"""Reference implementation probes for the AVP Evidence conformance profile."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from avp_ref.artifacts import (
    ArtifactDigestMismatch,
    ArtifactIntegrityError,
    ArtifactRef,
    InMemoryArtifactStore,
    sha256_digest,
)
from avp_ref.models import Evidence

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


class _FaultInjectableMemoryStore(InMemoryArtifactStore):
    """Reference-only store fixture used to exercise integrity failure paths.

    Portable TCK vectors never depend on this class. The adapter needs a
    controlled way to simulate bytes that no conforming public store API would
    allow to be published under a mismatched digest.
    """

    def inject_corruption(self, digest: str, content: bytes) -> None:
        self._objects[digest] = content


class ReferenceEvidenceTCKAdapter:
    """Evaluate Evidence TCK vectors against real reference Artifact behavior."""

    _SUPPORTED_CASES = frozenset(
        {
            "AVP-TCK-EVIDENCE-DIGEST-001",
            "AVP-TCK-EVIDENCE-LOCATOR-001",
            "AVP-TCK-EVIDENCE-REPRESENTATION-001",
            "AVP-TCK-EVIDENCE-IDENTITY-001",
            "AVP-TCK-EVIDENCE-METADATA-001",
            "AVP-TCK-EVIDENCE-INTEGRITY-001",
            "AVP-TCK-EVIDENCE-IMMUTABILITY-001",
        }
    )

    def __init__(
        self,
        *,
        store_factory: Callable[[], InMemoryArtifactStore] = InMemoryArtifactStore,
    ) -> None:
        self._store_factory = store_factory

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return self._SUPPORTED_CASES

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        dispatch = {
            "AVP-TCK-EVIDENCE-DIGEST-001": self._evaluate_digest,
            "AVP-TCK-EVIDENCE-LOCATOR-001": self._evaluate_locator,
            "AVP-TCK-EVIDENCE-REPRESENTATION-001": self._evaluate_representation,
            "AVP-TCK-EVIDENCE-IDENTITY-001": self._evaluate_identity,
            "AVP-TCK-EVIDENCE-METADATA-001": self._evaluate_metadata,
            "AVP-TCK-EVIDENCE-INTEGRITY-001": self._evaluate_integrity,
            "AVP-TCK-EVIDENCE-IMMUTABILITY-001": self._evaluate_immutability,
        }
        evaluator = dispatch.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(
                f"reference Evidence adapter does not implement TCK case {case_id}"
            )
        return evaluator(case)

    def _evaluate_digest(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        content = self._hex_bytes(vector.get("bytesHex"), f"{case_id} bytesHex")
        expected_size = self._integer(
            vector.get("expectedSize"),
            f"{case_id} expectedSize",
        )
        expected_digest = self._string(
            vector.get("expectedDigest"),
            f"{case_id} expectedDigest",
        )
        ref = self._store_factory().put_bytes(
            content,
            media_type="application/octet-stream",
        )
        if ref.size != expected_size or ref.digest != expected_digest:
            return self._fail(
                case_id,
                f"exact-byte identity mismatch: got size={ref.size} digest={ref.digest}",
            )
        if ref.digest != sha256_digest(content):
            return self._fail(
                case_id,
                "Artifact digest was not computed from exact bytes",
            )
        return self._pass(
            case_id,
            "exact bytes produce the required lowercase SHA-256 identity",
        )

    def _evaluate_locator(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        digest_value = self._string(vector.get("digest"), f"{case_id} digest")
        locators = self._string_list(
            vector.get("locators"),
            f"{case_id} locators",
        )
        refs = [
            ArtifactRef(
                digest_value,
                3,
                "application/octet-stream",
                uri=locator,
            )
            for locator in locators
        ]
        if len({item.digest for item in refs}) != 1:
            return self._fail(
                case_id,
                "changing locator changed Artifact content identity",
            )
        if len({item.uri for item in refs}) != len(locators):
            return self._fail(
                case_id,
                "distinct locators were not preserved as metadata",
            )
        return self._pass(
            case_id,
            "locator metadata is independent from content identity",
        )

    def _evaluate_representation(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        first = self._hex_bytes(
            vector.get("firstBytesHex"),
            f"{case_id} firstBytesHex",
        )
        second = self._hex_bytes(
            vector.get("secondBytesHex"),
            f"{case_id} secondBytesHex",
        )
        store = self._store_factory()
        first_ref = store.put_bytes(first, media_type="application/json")
        second_ref = store.put_bytes(second, media_type="application/json")
        if first_ref.digest == second_ref.digest:
            return self._fail(
                case_id,
                "different stored byte representations collapsed to one digest",
            )
        if store.get_bytes(first_ref) != first or store.get_bytes(second_ref) != second:
            return self._fail(
                case_id,
                "ArtifactStore transformed the supplied representation",
            )
        return self._pass(
            case_id,
            "storage preserves representation bytes without canonicalizing",
        )

    def _evaluate_identity(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        raw_evidence = vector.get("evidence")
        if not isinstance(raw_evidence, Mapping):
            raise TCKAdapterError(
                f"{case_id} evidence vector must be a mapping"
            )
        raw_artifact = raw_evidence.get("artifact")
        if not isinstance(raw_artifact, Mapping):
            raise TCKAdapterError(
                f"{case_id} artifact vector must be a mapping"
            )
        artifact = ArtifactRef(
            self._string(
                raw_artifact.get("digest"),
                f"{case_id} artifact.digest",
            ),
            self._integer(
                raw_artifact.get("size"),
                f"{case_id} artifact.size",
            ),
            self._string(
                raw_artifact.get("mediaType"),
                f"{case_id} artifact.mediaType",
            ),
        )
        evidence = Evidence(
            evidence_id=self._string(
                raw_evidence.get("evidenceId"),
                f"{case_id} evidenceId",
            ),
            evidence_type=self._string(
                raw_evidence.get("type"),
                f"{case_id} type",
            ),
            artifact=artifact,
            classification=self._string(
                raw_evidence.get("classification"),
                f"{case_id} classification",
            ),
        )
        if evidence.evidence_id == evidence.artifact.digest:
            return self._fail(
                case_id,
                "Evidence identity was collapsed into Artifact digest identity",
            )
        if evidence.artifact != artifact:
            return self._fail(
                case_id,
                "Evidence did not preserve its required Artifact reference",
            )
        return self._pass(
            case_id,
            "Evidence identity is stable and distinct from Artifact identity",
        )

    def _evaluate_metadata(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        expected_digest = self._string(
            vector.get("digest"),
            f"{case_id} digest",
        )
        variants = vector.get("metadataVariants")
        if not isinstance(variants, list) or len(variants) < 2:
            raise TCKAdapterError(
                f"{case_id} metadataVariants must contain at least two mappings"
            )
        artifact = ArtifactRef(
            expected_digest,
            3,
            "application/octet-stream",
        )
        observed_digests: set[str] = set()
        for index, raw in enumerate(variants):
            if not isinstance(raw, Mapping):
                raise TCKAdapterError(
                    f"{case_id} metadata variant {index} must be a mapping"
                )
            redaction = raw.get("redaction")
            if redaction is not None and not isinstance(redaction, Mapping):
                raise TCKAdapterError(
                    f"{case_id} redaction must be a mapping when present"
                )
            evidence = Evidence(
                evidence_id=f"ev_metadata_{index}",
                evidence_type="state_projection",
                artifact=artifact,
                classification=self._string(
                    raw.get("classification"),
                    f"{case_id} classification",
                ),
                producer=self._optional_string(
                    raw.get("producer"),
                    f"{case_id} producer",
                ),
                redaction=redaction,
            )
            observed_digests.add(evidence.artifact.digest)
        if observed_digests != {expected_digest}:
            return self._fail(
                case_id,
                "Evidence metadata altered Artifact content identity",
            )
        return self._pass(
            case_id,
            "classification/producer/redaction do not alter Artifact digest",
        )

    def _evaluate_integrity(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        declared = vector.get("declared")
        if not isinstance(declared, Mapping):
            raise TCKAdapterError(
                f"{case_id} declared vector must be a mapping"
            )
        declared_digest = self._string(
            declared.get("digest"),
            f"{case_id} declared.digest",
        )
        declared_size = self._integer(
            declared.get("size"),
            f"{case_id} declared.size",
        )
        ref = ArtifactRef(
            declared_digest,
            declared_size,
            "application/octet-stream",
        )
        for field in ("tamperedBytesHex", "truncatedBytesHex"):
            store = _FaultInjectableMemoryStore()
            store.inject_corruption(
                declared_digest,
                self._hex_bytes(vector.get(field), f"{case_id} {field}"),
            )
            try:
                store.get_bytes(ref)
            except ArtifactIntegrityError:
                continue
            return self._fail(case_id, f"{field} was silently accepted")
        return self._pass(
            case_id,
            "tampered and truncated Artifact bytes fail closed",
        )

    def _evaluate_immutability(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        published_digest = self._string(
            vector.get("publishedDigest"),
            f"{case_id} publishedDigest",
        )
        original = self._hex_bytes(
            vector.get("originalBytesHex"),
            f"{case_id} originalBytesHex",
        )
        replacement = self._hex_bytes(
            vector.get("replacementBytesHex"),
            f"{case_id} replacementBytesHex",
        )
        store = self._store_factory()
        ref = store.put_bytes(
            original,
            media_type="application/octet-stream",
            expected_digest=published_digest,
        )
        try:
            store.put_bytes(
                replacement,
                media_type="application/octet-stream",
                expected_digest=published_digest,
            )
        except ArtifactDigestMismatch:
            pass
        else:
            return self._fail(
                case_id,
                "replacement bytes were published under an existing digest",
            )
        if store.get_bytes(ref) != original:
            return self._fail(
                case_id,
                "failed replacement modified the original Artifact",
            )
        return self._pass(
            case_id,
            "published content identity is immutable",
        )

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        if not isinstance(metadata, Mapping) or not isinstance(
            metadata.get("id"), str
        ):
            raise TCKAdapterError("TCK case metadata.id is missing")
        return metadata["id"]

    @staticmethod
    def _vector(
        case: Mapping[str, Any],
        case_id: str,
    ) -> Mapping[str, Any]:
        vector = case.get("vector")
        if not isinstance(vector, Mapping):
            raise TCKAdapterError(f"{case_id} vector must be a mapping")
        return vector

    @staticmethod
    def _hex_bytes(value: object, context: str) -> bytes:
        if not isinstance(value, str) or not value:
            raise TCKAdapterError(
                f"{context} must be a non-empty hex string"
            )
        try:
            return bytes.fromhex(value)
        except ValueError as exc:
            raise TCKAdapterError(f"{context} is not valid hex") from exc

    @staticmethod
    def _string(value: object, context: str) -> str:
        if not isinstance(value, str) or not value:
            raise TCKAdapterError(
                f"{context} must be a non-empty string"
            )
        return value

    @classmethod
    def _optional_string(
        cls,
        value: object,
        context: str,
    ) -> str | None:
        if value is None:
            return None
        return cls._string(value, context)

    @staticmethod
    def _string_list(value: object, context: str) -> list[str]:
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(item, str) and item for item in value)
        ):
            raise TCKAdapterError(
                f"{context} must be a non-empty string list"
            )
        return list(value)

    @staticmethod
    def _integer(value: object, context: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise TCKAdapterError(
                f"{context} must be a non-negative integer"
            )
        return value

    @staticmethod
    def _pass(case_id: str, detail: str) -> TCKCaseResult:
        return TCKCaseResult(case_id, TCKStatus.PASS, detail)

    @staticmethod
    def _fail(case_id: str, detail: str) -> TCKCaseResult:
        return TCKCaseResult(case_id, TCKStatus.FAIL, detail)

"""Trusted Runtime-side publication of Evidence into an ArtifactStore."""

from __future__ import annotations

from collections.abc import Mapping

from avp_ref.artifacts import ArtifactStore
from avp_ref.canonical import canonical_json
from avp_ref.models import Evidence

JSON_MEDIA_TYPE = "application/json"


def canonical_json_bytes(value: object) -> bytes:
    """Encode one structured Evidence representation before storage.

    Canonicalization is intentionally outside ArtifactStore: callers choose the
    representation, and the store hashes exactly the resulting bytes.
    """

    return canonical_json(value).encode("utf-8")


class EvidencePublisher:
    """Publish exact Evidence representations and return stable Evidence refs."""

    def __init__(self, store: ArtifactStore) -> None:
        if not isinstance(store, ArtifactStore):
            raise TypeError("store must implement ArtifactStore")
        self._store = store

    def publish_bytes(
        self,
        *,
        evidence_id: str,
        evidence_type: str,
        content: bytes,
        media_type: str,
        classification: str = "evaluator-confidential",
        producer: str | None = None,
        redaction: Mapping[str, object] | None = None,
        extensions: Mapping[str, object] | None = None,
        expected_digest: str | None = None,
    ) -> Evidence:
        """Publish already-encoded bytes without changing their representation."""

        Evidence.validate_metadata(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            classification=classification,
            producer=producer,
        )
        if redaction is not None and not isinstance(redaction, Mapping):
            raise TypeError("redaction must be a mapping when present")
        if extensions is not None and not isinstance(extensions, Mapping):
            raise TypeError("extensions must be a mapping when present")
        artifact = self._store.put_bytes(
            content,
            media_type=media_type,
            expected_digest=expected_digest,
        )
        return Evidence(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            artifact=artifact,
            classification=classification,
            producer=producer,
            redaction=redaction,
            extensions=extensions,
        )

    def publish_json(
        self,
        *,
        evidence_id: str,
        evidence_type: str,
        value: object,
        classification: str = "evaluator-confidential",
        producer: str | None = None,
        redaction: Mapping[str, object] | None = None,
        extensions: Mapping[str, object] | None = None,
    ) -> Evidence:
        """Encode canonical JSON explicitly, then publish those exact bytes."""

        return self.publish_bytes(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            content=canonical_json_bytes(value),
            media_type=JSON_MEDIA_TYPE,
            classification=classification,
            producer=producer,
            redaction=redaction,
            extensions=extensions,
        )

    def read(self, evidence: Evidence) -> bytes:
        """Dereference Evidence through the store's integrity-checked read path."""

        return self._store.get_bytes(evidence.artifact)

    @property
    def store(self) -> ArtifactStore:
        """Return the configured store for implementation-level diagnostics/tests."""

        return self._store

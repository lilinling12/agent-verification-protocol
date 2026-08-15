"""Reference implementation probes for the AVP Artifact Trust profile."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from collections.abc import Mapping
from typing import Any, Iterable

from avp_ref.artifacts import ArtifactRef, InMemoryArtifactStore, sha256_digest
from avp_ref.trust import (
    ArtifactAttestation,
    ArtifactAttestationPublisher,
    ArtifactTrustOutcome,
    ArtifactTrustPolicy,
    ArtifactTrustVerifier,
    AuthenticatedAttestationObservation,
    MalformedAttestationError,
)

from .models import TCKAdapterError, TCKCaseResult, TCKStatus

_REFERENCE_BINDING = "avp-ref-auth-envelope-v1"
_STATEMENT_TYPE = "application/vnd.avp.ref.statement+json"
_DEFAULT_PREDICATE = "https://example.invalid/avp/reference-predicate/v1"
_SECRET = b"avp-reference-tck-authentication-key"


class _FaultInjectableMemoryStore(InMemoryArtifactStore):
    """Reference-only fixture for exercising attestation integrity failure."""

    def inject_corruption(self, digest: str, content: bytes) -> None:
        self._objects[digest] = content


class _ReferenceEnvelopeBinding:
    """Deterministic authenticated-envelope fixture used only by reference TCK.

    This is intentionally not a portable or production AVP signing format. It
    provides real byte-and-type authentication so the reference adapter can
    exercise AVP trust semantics without making a crypto algorithm normative.
    """

    @property
    def binding_profile(self) -> str:
        return _REFERENCE_BINDING

    @staticmethod
    def _authenticated_input(payload_type: str, payload: bytes) -> bytes:
        encoded_type = payload_type.encode("utf-8")
        return (
            b"AVP-REF-AUTH-v1 "
            + str(len(encoded_type)).encode("ascii")
            + b" "
            + encoded_type
            + b" "
            + str(len(payload)).encode("ascii")
            + b" "
            + payload
        )

    def issue(
        self,
        *,
        subject_digests: Iterable[str],
        signer_identity: str | None,
        predicate_type: str | None = _DEFAULT_PREDICATE,
        signer_hint: str = "lookup-hint",
        extra_claims: Iterable[str] = (),
    ) -> bytes:
        statement = {
            "subjects": list(subject_digests),
            "signerIdentity": signer_identity,
            "predicateType": predicate_type,
            "claims": list(extra_claims),
        }
        payload = json.dumps(
            statement,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        signature = hmac.new(
            _SECRET,
            self._authenticated_input(_STATEMENT_TYPE, payload),
            hashlib.sha256,
        ).hexdigest()
        return json.dumps(
            {
                "payloadType": _STATEMENT_TYPE,
                "payload": base64.b64encode(payload).decode("ascii"),
                "authenticator": signature,
                "signerHint": signer_hint,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def mutate(self, data: bytes, mutation: str) -> bytes:
        try:
            envelope = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AssertionError("reference fixture issued invalid envelope") from exc
        if mutation == "payload-bytes":
            payload = base64.b64decode(envelope["payload"], validate=True)
            envelope["payload"] = base64.b64encode(payload + b"!").decode("ascii")
        elif mutation == "authenticated-type":
            envelope["payloadType"] = _STATEMENT_TYPE + "+tampered"
        else:
            raise TCKAdapterError(f"unsupported reference mutation: {mutation}")
        return json.dumps(
            envelope,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def authenticate(self, data: bytes) -> AuthenticatedAttestationObservation:
        try:
            envelope = json.loads(data.decode("utf-8"))
            if not isinstance(envelope, dict):
                raise ValueError("envelope must be an object")
            payload_type = envelope["payloadType"]
            payload_b64 = envelope["payload"]
            signature = envelope["authenticator"]
            if not all(
                isinstance(item, str)
                for item in (payload_type, payload_b64, signature)
            ):
                raise ValueError("envelope authentication fields must be strings")
            payload = base64.b64decode(payload_b64, validate=True)
        except (
            KeyError,
            TypeError,
            ValueError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise MalformedAttestationError(
                "invalid reference attestation envelope"
            ) from exc

        expected = hmac.new(
            _SECRET,
            self._authenticated_input(payload_type, payload),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return AuthenticatedAttestationObservation(
                binding_profile=self.binding_profile,
                authenticated=False,
            )

        try:
            statement = json.loads(payload.decode("utf-8"))
            if not isinstance(statement, dict):
                raise ValueError("statement must be an object")
            subjects = statement["subjects"]
            signer_identity = statement.get("signerIdentity")
            predicate_type = statement.get("predicateType")
            if not isinstance(subjects, list) or not all(
                isinstance(item, str) for item in subjects
            ):
                raise ValueError("subjects must be a string list")
            if signer_identity is not None and not isinstance(signer_identity, str):
                raise ValueError("signer identity must be a string")
            if predicate_type is not None and not isinstance(predicate_type, str):
                raise ValueError("predicate type must be a string")
        except (
            KeyError,
            TypeError,
            ValueError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise MalformedAttestationError(
                "invalid authenticated reference statement"
            ) from exc

        return AuthenticatedAttestationObservation(
            binding_profile=self.binding_profile,
            authenticated=True,
            subject_digests=tuple(subjects),
            signer_identity=signer_identity,
            statement_type=payload_type,
            predicate_type=predicate_type,
            verified_properties=("reference.envelope-authentication",),
        )


class _ReferenceSigner:
    """Privileged signer fixture injected into the reference publisher."""

    def __init__(self, binding: _ReferenceEnvelopeBinding, identity: str) -> None:
        self._binding = binding
        self._identity = identity

    @property
    def binding_profile(self) -> str:
        return self._binding.binding_profile

    def create_attestation(
        self,
        artifact: ArtifactRef,
        *,
        predicate_type: str | None = None,
    ) -> bytes:
        return self._binding.issue(
            subject_digests=(artifact.digest,),
            signer_identity=self._identity,
            predicate_type=predicate_type or _DEFAULT_PREDICATE,
        )


class ReferenceArtifactTrustTCKAdapter:
    """Evaluate portable Artifact Trust cases against real reference behavior."""

    _SUPPORTED_CASES = frozenset(
        {
            "AVP-TCK-TRUST-IDENTITY-001",
            "AVP-TCK-TRUST-SUBJECT-BINDING-001",
            "AVP-TCK-TRUST-AUTHENTICATION-001",
            "AVP-TCK-TRUST-POLICY-001",
            "AVP-TCK-TRUST-FAIL-CLOSED-001",
            "AVP-TCK-TRUST-OUTCOME-001",
            "AVP-TCK-TRUST-PUBLICATION-AUTHORITY-001",
            "AVP-TCK-TRUST-CLAIM-HONESTY-001",
        }
    )

    def __init__(self, *, capabilities: Iterable[str] = ()) -> None:
        self._capabilities = frozenset(capabilities)
        self._binding = _ReferenceEnvelopeBinding()

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return self._SUPPORTED_CASES

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        applicability = case.get("applicability")
        when = case.get("when")
        if applicability == "conditional":
            if not isinstance(when, str) or not when:
                raise TCKAdapterError(f"{case_id} conditional case is missing when")
            if when not in self._capabilities:
                return TCKCaseResult(
                    case_id=case_id,
                    status=TCKStatus.SKIP,
                    detail=f"condition {when!r} is not declared",
                    skip_reason=f"condition-not-declared:{when}",
                )

        dispatch = {
            "AVP-TCK-TRUST-IDENTITY-001": self._evaluate_identity,
            "AVP-TCK-TRUST-SUBJECT-BINDING-001": self._evaluate_subject_binding,
            "AVP-TCK-TRUST-AUTHENTICATION-001": self._evaluate_authentication,
            "AVP-TCK-TRUST-POLICY-001": self._evaluate_policy,
            "AVP-TCK-TRUST-FAIL-CLOSED-001": self._evaluate_fail_closed,
            "AVP-TCK-TRUST-OUTCOME-001": self._evaluate_outcomes,
            "AVP-TCK-TRUST-PUBLICATION-AUTHORITY-001": self._evaluate_publication,
            "AVP-TCK-TRUST-CLAIM-HONESTY-001": self._evaluate_claim_honesty,
        }
        evaluator = dispatch.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(
                f"reference Artifact Trust adapter does not implement {case_id}"
            )
        return evaluator(case)

    def _evaluate_identity(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        content = self._hex_bytes(
            vector.get("artifactBytesHex"), f"{case_id} artifactBytesHex"
        )
        expected = self._string(
            vector.get("expectedArtifactDigest"),
            f"{case_id} expectedArtifactDigest",
        )
        store = InMemoryArtifactStore()
        artifact = store.put_bytes(content, media_type="application/octet-stream")
        if artifact.digest != expected or artifact.digest != sha256_digest(content):
            return self._fail(case_id, "target Artifact exact-byte identity is incorrect")
        original = artifact.digest
        variants = self._mapping_list(
            vector.get("attestationVariants"),
            f"{case_id} attestationVariants",
        )
        for index, variant in enumerate(variants):
            signer = self._string(
                variant.get("signerLabel"), f"{case_id} signerLabel[{index}]"
            )
            publisher = ArtifactAttestationPublisher(
                store,
                _ReferenceSigner(self._binding, signer),
            )
            published = publisher.publish(
                artifact,
                predicate_type=_DEFAULT_PREDICATE,
            )
            if published.artifact_digest != original or artifact.digest != original:
                return self._fail(
                    case_id,
                    "attestation metadata/publication changed target Artifact identity",
                )
        return self._pass(
            case_id,
            "attestation publication remains independent from Artifact content identity",
        )

    def _evaluate_subject_binding(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        target = self._string(
            vector.get("requestedArtifactDigest"),
            f"{case_id} requestedArtifactDigest",
        )
        matching = self._string_list(
            vector.get("authenticatedMatchingSubjects"),
            f"{case_id} authenticatedMatchingSubjects",
        )
        mismatching = self._string_list(
            vector.get("authenticatedMismatchingSubjects"),
            f"{case_id} authenticatedMismatchingSubjects",
        )
        policy = self._default_policy()
        accepted = self._verify_issued(
            target,
            matching,
            "identity:trusted-builder",
            policy,
        )
        rejected = self._verify_issued(
            target,
            mismatching,
            "identity:trusted-builder",
            policy,
        )
        if accepted.outcome is not ArtifactTrustOutcome.ACCEPTED:
            return self._fail(
                case_id,
                f"matching authenticated subject produced {accepted.outcome.value}",
            )
        if rejected.outcome is not ArtifactTrustOutcome.SUBJECT_MISMATCH:
            return self._fail(
                case_id,
                f"mismatched authenticated subject produced {rejected.outcome.value}",
            )
        return self._pass(
            case_id,
            "trust acceptance is bound to exact authenticated Artifact digest",
        )

    def _evaluate_authentication(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        mutations = self._string_list(
            vector.get("mutations"), f"{case_id} mutations"
        )
        target = "sha256:" + "1" * 64
        policy = self._default_policy()
        clean = self._binding.issue(
            subject_digests=(target,),
            signer_identity="identity:trusted-builder",
        )
        clean_result = self._verify_bytes(target, clean, policy)
        if clean_result.outcome is not ArtifactTrustOutcome.ACCEPTED:
            return self._fail(
                case_id,
                "unmodified authenticated envelope was not accepted",
            )
        for mutation in mutations:
            result = self._verify_bytes(
                target,
                self._binding.mutate(clean, mutation),
                policy,
            )
            if result.outcome is not ArtifactTrustOutcome.AUTHENTICATION_FAILED:
                return self._fail(
                    case_id,
                    f"{mutation} produced {result.outcome.value} instead of authentication-failed",
                )
        return self._pass(
            case_id,
            "reference binding authenticates both payload bytes and authenticated type",
        )

    def _evaluate_policy(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        raw_policy = vector.get("policy")
        if not isinstance(raw_policy, Mapping):
            raise TCKAdapterError(f"{case_id} policy must be a mapping")
        policy = ArtifactTrustPolicy(
            policy_id=self._string(
                raw_policy.get("policyId"), f"{case_id} policyId"
            ),
            allowed_signer_identities=tuple(
                self._string_list(
                    raw_policy.get("allowedSignerIdentities"),
                    f"{case_id} allowedSignerIdentities",
                )
            ),
        )
        target = "sha256:" + "2" * 64
        observations = self._mapping_list(
            vector.get("observations"), f"{case_id} observations"
        )
        for index, item in enumerate(observations):
            signer = self._string(
                item.get("signerIdentity"),
                f"{case_id} signerIdentity[{index}]",
            )
            hint = self._string(
                item.get("signerHint"), f"{case_id} signerHint[{index}]"
            )
            expected = self._string(
                item.get("expectedOutcome"),
                f"{case_id} expectedOutcome[{index}]",
            )
            data = self._binding.issue(
                subject_digests=(target,),
                signer_identity=signer,
                signer_hint=hint,
            )
            result = self._verify_bytes(target, data, policy)
            if result.outcome.value != expected:
                return self._fail(
                    case_id,
                    f"policy vector {index} produced {result.outcome.value}, expected {expected}",
                )
        return self._pass(
            case_id,
            "authenticated identity and trust policy govern acceptance; signer hints do not",
        )

    def _evaluate_fail_closed(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        failures = self._mapping_list(
            vector.get("failures"), f"{case_id} failures"
        )
        for item in failures:
            condition = self._string(item.get("condition"), f"{case_id} condition")
            expected = self._string(
                item.get("expectedOutcome"), f"{case_id} expectedOutcome"
            )
            result = self._failure_result(condition)
            if (
                result.outcome.value != expected
                or result.outcome is ArtifactTrustOutcome.ACCEPTED
            ):
                return self._fail(
                    case_id,
                    f"{condition} produced {result.outcome.value}, expected {expected}",
                )
        return self._pass(
            case_id,
            "all required trust failure gates terminate without acceptance",
        )

    def _evaluate_outcomes(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        required = set(
            self._string_list(
                vector.get("requiredOutcomes"),
                f"{case_id} requiredOutcomes",
            )
        )
        actual = {item.value for item in ArtifactTrustOutcome}
        if actual != required:
            return self._fail(
                case_id,
                f"portable outcome set mismatch: got {sorted(actual)}",
            )
        target = "sha256:" + "3" * 64
        accepted = self._verify_issued(
            target,
            (target,),
            "identity:trusted-builder",
            self._default_policy(),
        )
        if (
            accepted.outcome is not ArtifactTrustOutcome.ACCEPTED
            or accepted.signer_identity is None
        ):
            return self._fail(
                case_id,
                "accepted result did not preserve authenticated signer identity",
            )
        return self._pass(
            case_id,
            "all portable Artifact Trust outcomes are machine-distinct",
        )

    def _evaluate_publication(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        return self._fail(
            case_id,
            "reference in-process publication does not claim Subject credential-context isolation",
        )

    def _evaluate_claim_honesty(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        unsupported = set(
            self._string_list(
                vector.get("unsupportedClaims"),
                f"{case_id} unsupportedClaims",
            )
        )
        target = "sha256:" + "4" * 64
        data = self._binding.issue(
            subject_digests=(target,),
            signer_identity="identity:trusted-builder",
            extra_claims=unsupported,
        )
        result = self._verify_bytes(target, data, self._default_policy())
        if result.outcome is not ArtifactTrustOutcome.ACCEPTED:
            return self._fail(
                case_id,
                f"baseline trusted attestation produced {result.outcome.value}",
            )
        leaked = unsupported.intersection(result.verified_properties)
        if leaked:
            return self._fail(
                case_id,
                f"unverified claims were reported verified: {sorted(leaked)}",
            )
        return self._pass(
            case_id,
            "accepted trust does not imply unsupported assurance properties",
        )

    def _failure_result(self, condition: str) -> ArtifactTrustResult:
        target = "sha256:" + "5" * 64
        policy = self._default_policy()
        if condition == "attestation-integrity-failure":
            store = _FaultInjectableMemoryStore()
            good = self._binding.issue(
                subject_digests=(target,),
                signer_identity="identity:trusted-builder",
            )
            ref = store.put_bytes(good, media_type="application/octet-stream")
            store.inject_corruption(ref.digest, good + b"corrupt")
            return ArtifactTrustVerifier(store, (self._binding,)).verify(
                ArtifactAttestation(target, ref, _REFERENCE_BINDING),
                policy,
            )
        if condition == "malformed-attestation":
            return self._verify_bytes(target, b"{", policy)
        if condition == "unsupported-binding":
            store = InMemoryArtifactStore()
            ref = store.put_bytes(b"opaque", media_type="application/octet-stream")
            return ArtifactTrustVerifier(store, (self._binding,)).verify(
                ArtifactAttestation(target, ref, "unsupported-binding-v1"),
                policy,
            )
        if condition == "authentication-failure":
            clean = self._binding.issue(
                subject_digests=(target,),
                signer_identity="identity:trusted-builder",
            )
            return self._verify_bytes(
                target,
                self._binding.mutate(clean, "payload-bytes"),
                policy,
            )
        if condition == "subject-mismatch":
            return self._verify_issued(
                target,
                ("sha256:" + "6" * 64,),
                "identity:trusted-builder",
                policy,
            )
        if condition == "missing-authenticated-identity":
            return self._verify_issued(target, (target,), None, policy)
        if condition == "unauthorized-identity":
            return self._verify_issued(
                target,
                (target,),
                "identity:untrusted-builder",
                policy,
            )
        if condition == "required-policy-condition-fails":
            restrictive = ArtifactTrustPolicy(
                policy_id="reference-policy",
                allowed_signer_identities=("identity:trusted-builder",),
                allowed_predicate_types=(
                    "https://example.invalid/required-other-predicate/v1",
                ),
            )
            return self._verify_issued(
                target,
                (target,),
                "identity:trusted-builder",
                restrictive,
            )
        raise TCKAdapterError(f"unknown fail-closed condition: {condition}")

    def _verify_issued(
        self,
        target: str,
        subjects: Iterable[str],
        signer_identity: str | None,
        policy: ArtifactTrustPolicy,
    ) -> ArtifactTrustResult:
        data = self._binding.issue(
            subject_digests=subjects,
            signer_identity=signer_identity,
        )
        return self._verify_bytes(target, data, policy)

    def _verify_bytes(
        self,
        target: str,
        data: bytes,
        policy: ArtifactTrustPolicy,
    ) -> ArtifactTrustResult:
        store = InMemoryArtifactStore()
        ref = store.put_bytes(data, media_type="application/octet-stream")
        verifier = ArtifactTrustVerifier(store, (self._binding,))
        return verifier.verify(
            ArtifactAttestation(target, ref, _REFERENCE_BINDING),
            policy,
        )

    @staticmethod
    def _default_policy() -> ArtifactTrustPolicy:
        return ArtifactTrustPolicy(
            policy_id="reference-policy",
            allowed_signer_identities=("identity:trusted-builder",),
            allowed_binding_profiles=(_REFERENCE_BINDING,),
            allowed_predicate_types=(_DEFAULT_PREDICATE,),
        )

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("Artifact Trust TCK case metadata.id is missing")
        return case_id

    @staticmethod
    def _vector(case: Mapping[str, Any], case_id: str) -> Mapping[str, Any]:
        vector = case.get("vector")
        if not isinstance(vector, Mapping):
            raise TCKAdapterError(f"{case_id} vector must be a mapping")
        return vector

    @staticmethod
    def _string(value: Any, context: str) -> str:
        if not isinstance(value, str) or not value:
            raise TCKAdapterError(f"{context} must be a non-empty string")
        return value

    @classmethod
    def _string_list(cls, value: Any, context: str) -> list[str]:
        if not isinstance(value, list) or not value:
            raise TCKAdapterError(f"{context} must be a non-empty list")
        return [cls._string(item, context) for item in value]

    @staticmethod
    def _mapping_list(value: Any, context: str) -> list[Mapping[str, Any]]:
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(item, Mapping) for item in value)
        ):
            raise TCKAdapterError(
                f"{context} must be a non-empty list of mappings"
            )
        return list(value)

    @staticmethod
    def _hex_bytes(value: Any, context: str) -> bytes:
        if not isinstance(value, str):
            raise TCKAdapterError(f"{context} must be a hex string")
        try:
            return bytes.fromhex(value)
        except ValueError as exc:
            raise TCKAdapterError(f"{context} is not valid hex") from exc

    @staticmethod
    def _pass(case_id: str, detail: str) -> TCKCaseResult:
        return TCKCaseResult(case_id, TCKStatus.PASS, detail)

    @staticmethod
    def _fail(case_id: str, detail: str) -> TCKCaseResult:
        return TCKCaseResult(case_id, TCKStatus.FAIL, detail)

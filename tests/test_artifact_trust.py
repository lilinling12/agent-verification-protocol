from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

from avp_ref.artifacts import ArtifactRef, InMemoryArtifactStore, sha256_digest
from avp_ref.trust import (
    ArtifactAttestation,
    ArtifactAttestationPublisher,
    ArtifactTrustOutcome,
    ArtifactTrustPolicy,
    ArtifactTrustResult,
    ArtifactTrustVerifier,
    AuthenticatedAttestationObservation,
)

ROOT = Path(__file__).resolve().parents[1]
_BINDING = "test-binding-v1"
_SIGNER = "identity:test-signer"
_PREDICATE = "https://example.invalid/test-predicate/v1"


class _Binding:
    def __init__(self, observation: AuthenticatedAttestationObservation) -> None:
        self._observation = observation

    @property
    def binding_profile(self) -> str:
        return _BINDING

    def authenticate(self, data: bytes) -> AuthenticatedAttestationObservation:
        if data != b"attestation":
            raise AssertionError("unexpected test attestation bytes")
        return self._observation


class _UnsafeObservation:
    """Adversarial binding output that bypasses the reference value model."""

    binding_profile = _BINDING
    authenticated = False
    subject_digests = ("sha256:" + "0" * 64,)
    signer_identity = _SIGNER
    statement_type = "application/forged"
    predicate_type = _PREDICATE
    verified_properties = ("forged.authentication",)


class _UnsafeBinding:
    @property
    def binding_profile(self) -> str:
        return _BINDING

    def authenticate(self, data: bytes) -> _UnsafeObservation:
        if data != b"attestation":
            raise AssertionError("unexpected test attestation bytes")
        return _UnsafeObservation()


class _Signer:
    @property
    def binding_profile(self) -> str:
        return _BINDING

    def create_attestation(
        self,
        artifact: ArtifactRef,
        *,
        predicate_type: str | None = None,
    ) -> bytes:
        self.last_artifact_digest = artifact.digest
        self.last_predicate_type = predicate_type
        return b"attestation"


class _FaultStore(InMemoryArtifactStore):
    def corrupt(self, digest: str, data: bytes) -> None:
        self._objects[digest] = data


def _attestation_schema() -> dict[str, object]:
    schema = json.loads(
        (ROOT / "schemas/artifact-attestation.schema.json").read_text(encoding="utf-8")
    )
    artifact = json.loads(
        (ROOT / "schemas/artifact-ref.schema.json").read_text(encoding="utf-8")
    )
    schema["$defs"] = {"artifactRef": artifact}
    schema["properties"]["attestation"] = {"$ref": "#/$defs/artifactRef"}
    return schema


def _schema(name: str) -> dict[str, object]:
    return json.loads((ROOT / f"schemas/{name}").read_text(encoding="utf-8"))


class ArtifactTrustModelTest(unittest.TestCase):
    def test_portable_resources_validate_against_schemas(self) -> None:
        target = sha256_digest(b"artifact")
        attestation_ref = ArtifactRef(
            sha256_digest(b"attestation"),
            len(b"attestation"),
            "application/octet-stream",
        )
        attestation = ArtifactAttestation(target, attestation_ref, _BINDING)
        policy = ArtifactTrustPolicy(
            policy_id="policy:test",
            allowed_signer_identities=(_SIGNER,),
            allowed_binding_profiles=(_BINDING,),
            allowed_predicate_types=(_PREDICATE,),
        )
        result = ArtifactTrustResult(
            artifact_digest=target,
            attestation_digest=attestation_ref.digest,
            binding_profile=_BINDING,
            policy_id=policy.policy_id,
            outcome=ArtifactTrustOutcome.ACCEPTED,
            signer_identity=_SIGNER,
            verified_properties=("attestation.authentication",),
        )

        Draft202012Validator(_attestation_schema()).validate(attestation.to_dict())
        Draft202012Validator(_schema("artifact-trust-policy.schema.json")).validate(
            policy.to_dict()
        )
        Draft202012Validator(_schema("artifact-trust-result.schema.json")).validate(
            result.to_dict()
        )

    def test_accepted_result_requires_authenticated_signer_identity(self) -> None:
        digest = sha256_digest(b"artifact")
        with self.assertRaises(ValueError):
            ArtifactTrustResult(
                artifact_digest=digest,
                attestation_digest=sha256_digest(b"attestation"),
                binding_profile=_BINDING,
                policy_id="policy:test",
                outcome=ArtifactTrustOutcome.ACCEPTED,
            )

    def test_unauthenticated_observation_rejects_authenticated_claims(self) -> None:
        with self.assertRaises(ValueError):
            AuthenticatedAttestationObservation(
                binding_profile=_BINDING,
                authenticated=False,
                signer_identity=_SIGNER,
            )

    def test_authentication_failure_result_rejects_authenticated_claims(self) -> None:
        digest = sha256_digest(b"artifact")
        attestation_digest = sha256_digest(b"attestation")
        with self.assertRaises(ValueError):
            ArtifactTrustResult(
                artifact_digest=digest,
                attestation_digest=attestation_digest,
                binding_profile=_BINDING,
                policy_id="policy:test",
                outcome=ArtifactTrustOutcome.AUTHENTICATION_FAILED,
                signer_identity=_SIGNER,
            )

        invalid = {
            "artifactDigest": digest,
            "attestationDigest": attestation_digest,
            "bindingProfile": _BINDING,
            "policyId": "policy:test",
            "outcome": "authentication-failed",
            "signerIdentity": _SIGNER,
        }
        with self.assertRaises(ValidationError):
            Draft202012Validator(
                _schema("artifact-trust-result.schema.json")
            ).validate(invalid)


class ArtifactTrustVerifierTest(unittest.TestCase):
    def _verify(
        self,
        observation: AuthenticatedAttestationObservation,
        *,
        target: str | None = None,
        policy: ArtifactTrustPolicy | None = None,
    ) -> ArtifactTrustResult:
        target = target or sha256_digest(b"artifact")
        store = InMemoryArtifactStore()
        ref = store.put_bytes(b"attestation", media_type="application/octet-stream")
        verifier = ArtifactTrustVerifier(store, (_Binding(observation),))
        return verifier.verify(
            ArtifactAttestation(target, ref, _BINDING),
            policy
            or ArtifactTrustPolicy(
                policy_id="policy:test",
                allowed_signer_identities=(_SIGNER,),
                allowed_binding_profiles=(_BINDING,),
                allowed_predicate_types=(_PREDICATE,),
            ),
        )

    def test_authenticated_bound_authorized_attestation_is_accepted(self) -> None:
        target = sha256_digest(b"artifact")
        result = self._verify(
            AuthenticatedAttestationObservation(
                binding_profile=_BINDING,
                authenticated=True,
                subject_digests=(target,),
                signer_identity=_SIGNER,
                statement_type="application/example",
                predicate_type=_PREDICATE,
                verified_properties=("binding.native-check",),
            ),
            target=target,
        )
        self.assertIs(ArtifactTrustOutcome.ACCEPTED, result.outcome)
        self.assertEqual(_SIGNER, result.signer_identity)
        self.assertIn("binding.native-check", result.verified_properties)
        self.assertIn("policy.acceptance", result.verified_properties)

    def test_valid_authentication_does_not_bypass_signer_policy(self) -> None:
        target = sha256_digest(b"artifact")
        result = self._verify(
            AuthenticatedAttestationObservation(
                binding_profile=_BINDING,
                authenticated=True,
                subject_digests=(target,),
                signer_identity="identity:not-authorized",
                predicate_type=_PREDICATE,
            ),
            target=target,
        )
        self.assertIs(ArtifactTrustOutcome.IDENTITY_REJECTED, result.outcome)

    def test_authenticated_other_subject_is_rejected(self) -> None:
        result = self._verify(
            AuthenticatedAttestationObservation(
                binding_profile=_BINDING,
                authenticated=True,
                subject_digests=(sha256_digest(b"other"),),
                signer_identity=_SIGNER,
                predicate_type=_PREDICATE,
            )
        )
        self.assertIs(ArtifactTrustOutcome.SUBJECT_MISMATCH, result.outcome)

    def test_authentication_failure_sanitizes_untrusted_binding_claims(self) -> None:
        target = sha256_digest(b"artifact")
        store = InMemoryArtifactStore()
        ref = store.put_bytes(b"attestation", media_type="application/octet-stream")
        result = ArtifactTrustVerifier(store, (_UnsafeBinding(),)).verify(
            ArtifactAttestation(target, ref, _BINDING),
            ArtifactTrustPolicy("policy:test", (_SIGNER,)),
        )

        self.assertIs(ArtifactTrustOutcome.AUTHENTICATION_FAILED, result.outcome)
        self.assertIsNone(result.signer_identity)
        self.assertIsNone(result.statement_type)
        self.assertIsNone(result.predicate_type)
        self.assertEqual((), result.verified_properties)

    def test_unknown_binding_is_unsupported(self) -> None:
        store = InMemoryArtifactStore()
        ref = store.put_bytes(b"attestation", media_type="application/octet-stream")
        result = ArtifactTrustVerifier(store, ()).verify(
            ArtifactAttestation(sha256_digest(b"artifact"), ref, "unknown-binding"),
            ArtifactTrustPolicy("policy:test", (_SIGNER,)),
        )
        self.assertIs(ArtifactTrustOutcome.UNSUPPORTED, result.outcome)

    def test_attestation_artifact_integrity_failure_is_distinct(self) -> None:
        store = _FaultStore()
        ref = store.put_bytes(b"attestation", media_type="application/octet-stream")
        store.corrupt(ref.digest, b"tampered")
        verifier = ArtifactTrustVerifier(
            store,
            (
                _Binding(
                    AuthenticatedAttestationObservation(
                        binding_profile=_BINDING,
                        authenticated=True,
                    )
                ),
            ),
        )
        result = verifier.verify(
            ArtifactAttestation(sha256_digest(b"artifact"), ref, _BINDING),
            ArtifactTrustPolicy("policy:test", (_SIGNER,)),
        )
        self.assertIs(ArtifactTrustOutcome.INTEGRITY_FAILED, result.outcome)


class ArtifactAttestationPublisherTest(unittest.TestCase):
    def test_publication_preserves_target_identity_and_stores_attestation_separately(self) -> None:
        store = InMemoryArtifactStore()
        target = store.put_bytes(b"artifact", media_type="application/octet-stream")
        signer = _Signer()
        publisher = ArtifactAttestationPublisher(store, signer)

        published = publisher.publish(target, predicate_type=_PREDICATE)

        self.assertEqual(target.digest, published.artifact_digest)
        self.assertNotEqual(target.digest, published.attestation.digest)
        self.assertEqual(b"attestation", store.get_bytes(published.attestation))
        self.assertEqual(target.digest, signer.last_artifact_digest)
        self.assertEqual(_PREDICATE, signer.last_predicate_type)


if __name__ == "__main__":
    unittest.main()

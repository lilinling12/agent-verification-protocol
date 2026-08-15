"""Reference evaluator for AVP Artifact trust outcomes."""

from __future__ import annotations

from collections.abc import Iterable

from avp_ref.artifacts import ArtifactIntegrityError, ArtifactStore

from .models import (
    ArtifactAttestation,
    ArtifactTrustOutcome,
    ArtifactTrustPolicy,
    ArtifactTrustResult,
    AuthenticatedAttestationObservation,
)
from .protocol import (
    AttestationBinding,
    MalformedAttestationError,
    UnsupportedAttestationError,
)

_BASE_VERIFIED_PROPERTIES = (
    "attestation.authentication",
    "artifact.subject-binding",
    "signer.identity",
    "policy.acceptance",
)


class ArtifactTrustVerifier:
    """Evaluate immutable attestation bytes against a portable trust policy."""

    def __init__(
        self,
        store: ArtifactStore,
        bindings: Iterable[AttestationBinding],
    ) -> None:
        self._store = store
        indexed: dict[str, AttestationBinding] = {}
        for binding in bindings:
            profile = binding.binding_profile
            if not isinstance(profile, str) or not profile:
                raise ValueError("attestation binding profile must be non-empty")
            if profile in indexed:
                raise ValueError(f"duplicate attestation binding profile: {profile}")
            indexed[profile] = binding
        self._bindings = indexed

    @property
    def binding_profiles(self) -> frozenset[str]:
        return frozenset(self._bindings)

    def verify(
        self,
        attestation: ArtifactAttestation,
        policy: ArtifactTrustPolicy,
    ) -> ArtifactTrustResult:
        """Return one fail-closed trust result for the requested Artifact."""

        try:
            data = self._store.get_bytes(attestation.attestation)
        except ArtifactIntegrityError as exc:
            return self._result(
                attestation,
                policy,
                ArtifactTrustOutcome.INTEGRITY_FAILED,
                diagnostics={"reason": type(exc).__name__},
            )

        binding = self._bindings.get(attestation.binding_profile)
        if binding is None:
            return self._result(
                attestation,
                policy,
                ArtifactTrustOutcome.UNSUPPORTED,
                diagnostics={"reason": "binding-profile-not-supported"},
            )

        try:
            observation = binding.authenticate(data)
        except MalformedAttestationError as exc:
            return self._result(
                attestation,
                policy,
                ArtifactTrustOutcome.MALFORMED,
                diagnostics={"reason": str(exc) or type(exc).__name__},
            )
        except UnsupportedAttestationError as exc:
            return self._result(
                attestation,
                policy,
                ArtifactTrustOutcome.UNSUPPORTED,
                diagnostics={"reason": str(exc) or type(exc).__name__},
            )

        if observation.binding_profile != attestation.binding_profile:
            return self._result(
                attestation,
                policy,
                ArtifactTrustOutcome.MALFORMED,
                observation=observation,
                diagnostics={"reason": "binding-observation-profile-mismatch"},
            )
        if not observation.authenticated:
            return self._result(
                attestation,
                policy,
                ArtifactTrustOutcome.AUTHENTICATION_FAILED,
                diagnostics={"reason": "attestation-authentication-failed"},
            )
        if attestation.artifact_digest not in observation.subject_digests:
            return self._result(
                attestation,
                policy,
                ArtifactTrustOutcome.SUBJECT_MISMATCH,
                observation=observation,
                diagnostics={"reason": "authenticated-subject-does-not-match-artifact"},
            )
        if observation.signer_identity is None:
            return self._result(
                attestation,
                policy,
                ArtifactTrustOutcome.IDENTITY_REJECTED,
                observation=observation,
                diagnostics={"reason": "authenticated-signer-identity-unavailable"},
            )
        if observation.signer_identity not in policy.allowed_signer_identities:
            return self._result(
                attestation,
                policy,
                ArtifactTrustOutcome.IDENTITY_REJECTED,
                observation=observation,
                diagnostics={"reason": "authenticated-signer-identity-not-allowed"},
            )
        if (
            policy.allowed_binding_profiles is not None
            and attestation.binding_profile not in policy.allowed_binding_profiles
        ):
            return self._result(
                attestation,
                policy,
                ArtifactTrustOutcome.POLICY_REJECTED,
                observation=observation,
                diagnostics={"reason": "binding-profile-not-allowed"},
            )
        if policy.allowed_predicate_types is not None:
            if (
                observation.predicate_type is None
                or observation.predicate_type not in policy.allowed_predicate_types
            ):
                return self._result(
                    attestation,
                    policy,
                    ArtifactTrustOutcome.POLICY_REJECTED,
                    observation=observation,
                    diagnostics={"reason": "predicate-type-not-allowed"},
                )

        verified = tuple(
            dict.fromkeys((*observation.verified_properties, *_BASE_VERIFIED_PROPERTIES))
        )
        return self._result(
            attestation,
            policy,
            ArtifactTrustOutcome.ACCEPTED,
            observation=observation,
            verified_properties=verified,
        )

    @staticmethod
    def _result(
        attestation: ArtifactAttestation,
        policy: ArtifactTrustPolicy,
        outcome: ArtifactTrustOutcome,
        *,
        observation: AuthenticatedAttestationObservation | None = None,
        verified_properties: tuple[str, ...] = (),
        diagnostics: dict[str, object] | None = None,
    ) -> ArtifactTrustResult:
        authenticated_observation = (
            observation
            if observation is not None and observation.authenticated
            else None
        )
        return ArtifactTrustResult(
            artifact_digest=attestation.artifact_digest,
            attestation_digest=attestation.attestation.digest,
            binding_profile=attestation.binding_profile,
            policy_id=policy.policy_id,
            outcome=outcome,
            signer_identity=(
                authenticated_observation.signer_identity
                if authenticated_observation is not None
                else None
            ),
            statement_type=(
                authenticated_observation.statement_type
                if authenticated_observation is not None
                else None
            ),
            predicate_type=(
                authenticated_observation.predicate_type
                if authenticated_observation is not None
                else None
            ),
            verified_properties=verified_properties,
            diagnostics=diagnostics,
        )

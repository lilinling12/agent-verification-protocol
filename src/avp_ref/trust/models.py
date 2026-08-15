"""Reference value models for AVP Artifact trust semantics.

Normative authority lives in ``spec/trust``.  These Python types are one
implementation of the portable resources and must not define new semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from avp_ref.artifacts import ArtifactRef, validate_sha256_digest


def _non_empty(value: str, field: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    if len(value) > maximum:
        raise ValueError(f"{field} must not exceed {maximum} characters")
    return value


def _unique_non_empty(values: tuple[str, ...], field: str, *, maximum: int) -> None:
    if not isinstance(values, tuple) or not values:
        raise ValueError(f"{field} must be a non-empty tuple")
    if len(set(values)) != len(values):
        raise ValueError(f"{field} must not contain duplicates")
    for value in values:
        _non_empty(value, field, maximum=maximum)


def _optional_unique(values: tuple[str, ...] | None, field: str, *, maximum: int) -> None:
    if values is None:
        return
    _unique_non_empty(values, field, maximum=maximum)


class ArtifactTrustOutcome(str, Enum):
    """Portable terminal outcomes from the Artifact Trust contract."""

    ACCEPTED = "accepted"
    INTEGRITY_FAILED = "integrity-failed"
    MALFORMED = "malformed"
    UNSUPPORTED = "unsupported"
    AUTHENTICATION_FAILED = "authentication-failed"
    SUBJECT_MISMATCH = "subject-mismatch"
    IDENTITY_REJECTED = "identity-rejected"
    POLICY_REJECTED = "policy-rejected"


@dataclass(frozen=True, slots=True)
class ArtifactAttestation:
    """Reference to immutable attestation bytes for one requested Artifact."""

    artifact_digest: str
    attestation: ArtifactRef
    binding_profile: str

    def __post_init__(self) -> None:
        validate_sha256_digest(self.artifact_digest)
        _non_empty(self.binding_profile, "binding_profile", maximum=256)

    def to_dict(self) -> dict[str, object]:
        return {
            "artifactDigest": self.artifact_digest,
            "attestation": self.attestation.to_dict(),
            "bindingProfile": self.binding_profile,
        }


@dataclass(frozen=True, slots=True)
class ArtifactTrustPolicy:
    """Portable minimum evaluator-owned trust-policy surface."""

    policy_id: str
    allowed_signer_identities: tuple[str, ...]
    allowed_binding_profiles: tuple[str, ...] | None = None
    allowed_predicate_types: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        _non_empty(self.policy_id, "policy_id", maximum=256)
        _unique_non_empty(
            self.allowed_signer_identities,
            "allowed_signer_identities",
            maximum=512,
        )
        _optional_unique(
            self.allowed_binding_profiles,
            "allowed_binding_profiles",
            maximum=256,
        )
        _optional_unique(
            self.allowed_predicate_types,
            "allowed_predicate_types",
            maximum=2048,
        )

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "policyId": self.policy_id,
            "allowedSignerIdentities": list(self.allowed_signer_identities),
        }
        if self.allowed_binding_profiles is not None:
            result["allowedBindingProfiles"] = list(self.allowed_binding_profiles)
        if self.allowed_predicate_types is not None:
            result["allowedPredicateTypes"] = list(self.allowed_predicate_types)
        return result


@dataclass(frozen=True, slots=True)
class AuthenticatedAttestationObservation:
    """Binding-authoritative observations consumed by the trust evaluator.

    This is an internal reference-runtime boundary, not a portable AVP wire
    resource.  A binding implementation is responsible for ensuring that every
    populated field is derived from authenticated or binding-authoritative data.
    """

    binding_profile: str
    authenticated: bool
    subject_digests: tuple[str, ...] = ()
    signer_identity: str | None = None
    statement_type: str | None = None
    predicate_type: str | None = None
    verified_properties: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _non_empty(self.binding_profile, "binding_profile", maximum=256)
        if not isinstance(self.authenticated, bool):
            raise TypeError("authenticated must be a bool")
        if not self.authenticated and (
            self.subject_digests
            or self.signer_identity is not None
            or self.statement_type is not None
            or self.predicate_type is not None
            or self.verified_properties
        ):
            raise ValueError(
                "unauthenticated observation must not expose authenticated claims"
            )
        if len(set(self.subject_digests)) != len(self.subject_digests):
            raise ValueError("subject_digests must not contain duplicates")
        for digest in self.subject_digests:
            validate_sha256_digest(digest)
        if self.signer_identity is not None:
            _non_empty(self.signer_identity, "signer_identity", maximum=512)
        if self.statement_type is not None:
            _non_empty(self.statement_type, "statement_type", maximum=2048)
        if self.predicate_type is not None:
            _non_empty(self.predicate_type, "predicate_type", maximum=2048)
        if len(set(self.verified_properties)) != len(self.verified_properties):
            raise ValueError("verified_properties must not contain duplicates")
        for value in self.verified_properties:
            _non_empty(value, "verified_properties", maximum=256)


@dataclass(frozen=True, slots=True)
class ArtifactTrustResult:
    """Machine-readable terminal Artifact trust result."""

    artifact_digest: str
    attestation_digest: str
    binding_profile: str
    policy_id: str
    outcome: ArtifactTrustOutcome
    signer_identity: str | None = None
    statement_type: str | None = None
    predicate_type: str | None = None
    verified_properties: tuple[str, ...] = ()
    diagnostics: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        validate_sha256_digest(self.artifact_digest)
        validate_sha256_digest(self.attestation_digest)
        _non_empty(self.binding_profile, "binding_profile", maximum=256)
        _non_empty(self.policy_id, "policy_id", maximum=256)
        if not isinstance(self.outcome, ArtifactTrustOutcome):
            raise TypeError("outcome must be an ArtifactTrustOutcome")
        if self.signer_identity is not None:
            _non_empty(self.signer_identity, "signer_identity", maximum=512)
        if self.outcome is ArtifactTrustOutcome.ACCEPTED and self.signer_identity is None:
            raise ValueError("accepted trust result requires signer_identity")
        if self.outcome is ArtifactTrustOutcome.AUTHENTICATION_FAILED and (
            self.signer_identity is not None
            or self.statement_type is not None
            or self.predicate_type is not None
        ):
            raise ValueError(
                "authentication-failed result must not expose authenticated identity or type claims"
            )
        if self.statement_type is not None:
            _non_empty(self.statement_type, "statement_type", maximum=2048)
        if self.predicate_type is not None:
            _non_empty(self.predicate_type, "predicate_type", maximum=2048)
        if len(set(self.verified_properties)) != len(self.verified_properties):
            raise ValueError("verified_properties must not contain duplicates")
        for value in self.verified_properties:
            _non_empty(value, "verified_properties", maximum=256)
        if self.diagnostics is not None and not isinstance(self.diagnostics, dict):
            raise TypeError("diagnostics must be a dict when present")

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "artifactDigest": self.artifact_digest,
            "attestationDigest": self.attestation_digest,
            "bindingProfile": self.binding_profile,
            "policyId": self.policy_id,
            "outcome": self.outcome.value,
        }
        if self.signer_identity is not None:
            result["signerIdentity"] = self.signer_identity
        if self.statement_type is not None:
            result["statementType"] = self.statement_type
        if self.predicate_type is not None:
            result["predicateType"] = self.predicate_type
        if self.verified_properties:
            result["verifiedProperties"] = list(self.verified_properties)
        if self.diagnostics is not None:
            result["diagnostics"] = dict(self.diagnostics)
        return result

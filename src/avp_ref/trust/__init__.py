"""Artifact trust reference implementation.

Normative semantics originate in ``spec/trust``.  The Python API is reference
behavior only and is not independently normative.
"""

from .models import (
    ArtifactAttestation,
    ArtifactTrustOutcome,
    ArtifactTrustPolicy,
    ArtifactTrustResult,
    AuthenticatedAttestationObservation,
)
from .protocol import (
    AttestationBinding,
    AttestationBindingError,
    AttestationSigner,
    MalformedAttestationError,
    UnsupportedAttestationError,
)
from .publisher import ArtifactAttestationPublisher
from .verifier import ArtifactTrustVerifier

__all__ = [
    "ArtifactAttestation",
    "ArtifactAttestationPublisher",
    "ArtifactTrustOutcome",
    "ArtifactTrustPolicy",
    "ArtifactTrustResult",
    "ArtifactTrustVerifier",
    "AttestationBinding",
    "AttestationBindingError",
    "AttestationSigner",
    "AuthenticatedAttestationObservation",
    "MalformedAttestationError",
    "UnsupportedAttestationError",
]

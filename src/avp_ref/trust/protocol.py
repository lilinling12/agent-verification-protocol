"""Reference SPIs for Artifact attestation authentication and publication.

These interfaces are implementation boundaries only.  Normative semantics live
in ``spec/trust/artifact-trust-attestation-contract.md``.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from avp_ref.artifacts import ArtifactRef

from .models import AuthenticatedAttestationObservation


class AttestationBindingError(Exception):
    """Base error raised by an attestation binding implementation."""


class MalformedAttestationError(AttestationBindingError):
    """The selected binding cannot safely parse the supplied representation."""


class UnsupportedAttestationError(AttestationBindingError):
    """The binding encounters required semantics it does not support."""


@runtime_checkable
class AttestationBinding(Protocol):
    """Authenticate and interpret one immutable attestation representation."""

    @property
    def binding_profile(self) -> str: ...

    def authenticate(self, data: bytes) -> AuthenticatedAttestationObservation: ...


@runtime_checkable
class AttestationSigner(Protocol):
    """Privileged implementation-side signer used by an attestation publisher."""

    @property
    def binding_profile(self) -> str: ...

    def create_attestation(
        self,
        artifact: ArtifactRef,
        *,
        predicate_type: str | None = None,
    ) -> bytes: ...

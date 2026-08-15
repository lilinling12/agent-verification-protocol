"""Privileged reference publication path for immutable attestation bytes."""

from __future__ import annotations

from avp_ref.artifacts import ArtifactRef, ArtifactStore

from .models import ArtifactAttestation
from .protocol import AttestationSigner


class ArtifactAttestationPublisher:
    """Publish signer-produced attestation bytes without mutating target identity.

    The signer is evaluator/control-side authority.  This class deliberately
    exposes no signing credential accessor and is not a Subject capability.
    Deployment isolation remains governed by the Security contract.
    """

    def __init__(self, store: ArtifactStore, signer: AttestationSigner) -> None:
        if not isinstance(signer.binding_profile, str) or not signer.binding_profile:
            raise ValueError("attestation signer binding_profile must be non-empty")
        self._store = store
        self._signer = signer

    @property
    def binding_profile(self) -> str:
        return self._signer.binding_profile

    def publish(
        self,
        artifact: ArtifactRef,
        *,
        predicate_type: str | None = None,
        media_type: str = "application/octet-stream",
    ) -> ArtifactAttestation:
        """Create and store independent attestation bytes for ``artifact``."""

        original_digest = artifact.digest
        data = self._signer.create_attestation(
            artifact,
            predicate_type=predicate_type,
        )
        if not isinstance(data, bytes):
            raise TypeError("attestation signer must return bytes")
        attestation_ref = self._store.put_bytes(data, media_type=media_type)
        if artifact.digest != original_digest:
            raise RuntimeError("attestation publication mutated target Artifact identity")
        return ArtifactAttestation(
            artifact_digest=artifact.digest,
            attestation=attestation_ref,
            binding_profile=self.binding_profile,
        )

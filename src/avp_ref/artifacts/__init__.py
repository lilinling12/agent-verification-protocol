"""Content-addressed Artifact storage for the AVP reference implementation.

Protocol semantics originate in ``spec/evidence``. These classes are one
reference implementation of that contract and are not independently normative.
"""

from .errors import (
    ArtifactDigestMismatch,
    ArtifactIntegrityError,
    ArtifactNotFound,
    ArtifactSizeLimitExceeded,
    ArtifactStoreError,
)
from .filesystem import LocalFilesystemArtifactStore
from .memory import InMemoryArtifactStore
from .models import ArtifactRef, sha256_digest, validate_sha256_digest
from .protocol import ArtifactStore

__all__ = [
    "ArtifactDigestMismatch",
    "ArtifactIntegrityError",
    "ArtifactNotFound",
    "ArtifactRef",
    "ArtifactSizeLimitExceeded",
    "ArtifactStore",
    "ArtifactStoreError",
    "InMemoryArtifactStore",
    "LocalFilesystemArtifactStore",
    "sha256_digest",
    "validate_sha256_digest",
]

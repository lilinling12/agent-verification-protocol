"""Typed failures for content-addressed Artifact storage."""

from __future__ import annotations


class ArtifactStoreError(RuntimeError):
    """Base class for Artifact storage failures."""


class ArtifactNotFound(ArtifactStoreError):
    """Raised when a requested Artifact digest is not present."""


class ArtifactIntegrityError(ArtifactStoreError):
    """Raised when retained bytes do not match their declared identity."""


class ArtifactDigestMismatch(ArtifactStoreError):
    """Raised when caller-supplied expected identity differs from exact bytes."""

    def __init__(self, *, expected: str, actual: str) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(f"artifact digest mismatch: expected {expected}, got {actual}")


class ArtifactSizeLimitExceeded(ArtifactStoreError):
    """Raised before publishing an Artifact that exceeds the configured limit."""

    def __init__(self, *, limit: int, observed: int) -> None:
        self.limit = limit
        self.observed = observed
        super().__init__(
            f"artifact size limit exceeded: limit={limit} bytes, observed={observed} bytes"
        )

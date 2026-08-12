"""Immutable Artifact identity value objects."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Final

_SHA256_PATTERN: Final[re.Pattern[str]] = re.compile(r"^sha256:[0-9a-f]{64}$")


def validate_sha256_digest(value: str) -> str:
    """Validate and return the canonical AVP SHA-256 content identifier."""

    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError("artifact digest must match sha256:<64 lowercase hex characters>")
    return value


def validate_media_type(value: str) -> str:
    """Validate representation media-type metadata without normalizing it."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError("artifact media_type must be a non-empty string")
    if len(value) > 255:
        raise ValueError("artifact media_type must not exceed 255 characters")
    return value


def sha256_digest(data: bytes) -> str:
    """Return AVP Artifact identity for the exact supplied bytes."""

    if not isinstance(data, bytes):
        raise TypeError("artifact content must be bytes")
    return "sha256:" + hashlib.sha256(data).hexdigest()


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    """Reference to one immutable byte representation.

    ``digest`` is content identity. ``size``, ``media_type`` and ``uri`` are
    representation/locator metadata and never participate in the digest.
    """

    digest: str
    size: int
    media_type: str
    uri: str | None = None

    def __post_init__(self) -> None:
        validate_sha256_digest(self.digest)
        if isinstance(self.size, bool) or not isinstance(self.size, int) or self.size < 0:
            raise ValueError("artifact size must be a non-negative integer")
        validate_media_type(self.media_type)
        if self.uri is not None:
            if not isinstance(self.uri, str) or not self.uri:
                raise ValueError("artifact uri must be a non-empty string when present")
            if len(self.uri) > 4096:
                raise ValueError("artifact uri must not exceed 4096 characters")

    def to_dict(self) -> dict[str, object]:
        """Serialize to ``schemas/artifact-ref.schema.json`` shape."""

        result: dict[str, object] = {
            "digest": self.digest,
            "size": self.size,
            "mediaType": self.media_type,
        }
        if self.uri is not None:
            result["uri"] = self.uri
        return result

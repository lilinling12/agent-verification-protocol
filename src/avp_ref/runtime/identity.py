"""Episode identity relationships used by the reference implementation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

_SHA256_PATTERN: Final[re.Pattern[str]] = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class ReplaySourceIdentity:
    """Explicit immutable identity link from a replay to its source Episode.

    AVP Core v0.1 requires a replayed Episode to use a new Episode identifier
    while preserving an explicit source reference. The source manifest digest
    strengthens that link against accidental ID-only ambiguity without making
    any claim about replay equivalence or fidelity.
    """

    episode_id: str
    manifest_digest: str

    def __post_init__(self) -> None:
        if not self.episode_id or len(self.episode_id) > 256:
            raise ValueError("source episode_id must contain 1..256 characters")
        if _SHA256_PATTERN.fullmatch(self.manifest_digest) is None:
            raise ValueError("source manifest_digest must be a sha256 digest")

    def to_dict(self) -> dict[str, str]:
        """Serialize the source relationship for events and bindings."""

        return {
            "episodeId": self.episode_id,
            "manifestDigest": self.manifest_digest,
        }

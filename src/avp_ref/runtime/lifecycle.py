"""Immutable value objects for observable Episode lifecycle transitions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Final

from .state import EpisodeState

_CAUSE_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"
)


@dataclass(frozen=True, slots=True)
class TransitionCause:
    """Machine-readable cause attached to one lifecycle transition.

    Cause codes are implementation-observable values, not a standardized AVP
    taxonomy in v0.1. The representation intentionally matches the Core JSON
    Schema so records need no implementation-specific transformation.
    """

    code: str
    detail: str | None = None

    def __post_init__(self) -> None:
        if not self.code or len(self.code) > 128:
            raise ValueError("transition cause code must contain 1..128 characters")
        if _CAUSE_CODE_PATTERN.fullmatch(self.code) is None:
            raise ValueError(f"invalid transition cause code: {self.code!r}")
        if self.detail is not None and len(self.detail) > 2048:
            raise ValueError("transition cause detail must not exceed 2048 characters")

    def to_dict(self) -> dict[str, str]:
        """Serialize to the AVP Core transition-cause schema shape."""

        result = {"code": self.code}
        if self.detail is not None:
            result["detail"] = self.detail
        return result


@dataclass(frozen=True, slots=True)
class EpisodeTransition:
    """One canonical, Episode-local lifecycle transition record."""

    episode_id: str
    sequence: int
    previous_state: EpisodeState
    resulting_state: EpisodeState
    cause: TransitionCause

    def __post_init__(self) -> None:
        if not self.episode_id or len(self.episode_id) > 256:
            raise ValueError("episode_id must contain 1..256 characters")
        if self.sequence < 1:
            raise ValueError("transition sequence must be positive")
        if self.previous_state is self.resulting_state:
            raise ValueError("a lifecycle transition must change state")

    def to_dict(self) -> dict[str, Any]:
        """Serialize exactly to ``episode-lifecycle.schema.json`` shape."""

        return {
            "episodeId": self.episode_id,
            "sequence": self.sequence,
            "previousState": self.previous_state.value,
            "resultingState": self.resulting_state.value,
            "cause": self.cause.to_dict(),
        }


def default_transition_cause(
    previous: EpisodeState,
    resulting: EpisodeState,
) -> TransitionCause:
    """Return the reference runtime's deterministic default cause code.

    The Core specification requires a machine-readable cause but does not
    standardize a v0.1 cause taxonomy. Runtime methods may supply a more
    specific cause; otherwise a stable state-pair code keeps legacy execution
    paths conformant without inventing protocol-wide semantics.
    """

    return TransitionCause(
        f"runtime.lifecycle.{previous.value.lower()}.{resulting.value.lower()}"
    )

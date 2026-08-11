"""Episode lifecycle state machine."""

from __future__ import annotations

from enum import Enum


class EpisodeState(str, Enum):
    CREATED = "CREATED"
    PROVISIONING = "PROVISIONING"
    READY = "READY"
    RUNNING = "RUNNING"
    QUIESCING = "QUIESCING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"


_TRANSITIONS: dict[EpisodeState, frozenset[EpisodeState]] = {
    EpisodeState.CREATED: frozenset({EpisodeState.PROVISIONING}),
    EpisodeState.PROVISIONING: frozenset({EpisodeState.READY}),
    EpisodeState.READY: frozenset({EpisodeState.RUNNING}),
    EpisodeState.RUNNING: frozenset({EpisodeState.QUIESCING, EpisodeState.VERIFYING}),
    EpisodeState.QUIESCING: frozenset({EpisodeState.VERIFYING}),
    EpisodeState.VERIFYING: frozenset({EpisodeState.COMPLETED}),
    EpisodeState.COMPLETED: frozenset(),
}


class InvalidEpisodeTransition(Exception):
    """Raised when a runtime tries to bypass lifecycle guarantees."""


def assert_transition(current: EpisodeState, target: EpisodeState) -> None:
    """Validate lifecycle transitions.

    Explicit lifecycle prevents ambiguous evidence collection, for example
    verifying an Episode while tool execution is still active.
    """

    if target not in _TRANSITIONS[current]:
        raise InvalidEpisodeTransition(f"illegal transition {current.value} -> {target.value}")

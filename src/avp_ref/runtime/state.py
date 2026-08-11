"""Normative Episode lifecycle state machine for the reference runtime."""

from __future__ import annotations

from enum import Enum


class EpisodeState(str, Enum):
    """Lifecycle states shared by runtime, HTTP binding, TCK and reports."""

    CREATED = "CREATED"
    PROVISIONING = "PROVISIONING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    QUIESCING = "QUIESCING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    INVALID = "INVALID"
    INFRA_FAILED = "INFRA_FAILED"


_TERMINAL = frozenset({EpisodeState.COMPLETED, EpisodeState.ABORTED, EpisodeState.INVALID, EpisodeState.INFRA_FAILED})
_TRANSITIONS: dict[EpisodeState, frozenset[EpisodeState]] = {
    EpisodeState.CREATED: frozenset({EpisodeState.PROVISIONING, EpisodeState.ABORTED}),
    EpisodeState.PROVISIONING: frozenset({EpisodeState.READY, EpisodeState.INVALID, EpisodeState.INFRA_FAILED, EpisodeState.ABORTED}),
    EpisodeState.READY: frozenset({EpisodeState.RUNNING, EpisodeState.ABORTED}),
    EpisodeState.RUNNING: frozenset({EpisodeState.PAUSED, EpisodeState.QUIESCING, EpisodeState.ABORTED, EpisodeState.INFRA_FAILED}),
    EpisodeState.PAUSED: frozenset({EpisodeState.RUNNING, EpisodeState.ABORTED, EpisodeState.INFRA_FAILED}),
    EpisodeState.QUIESCING: frozenset({EpisodeState.VERIFYING, EpisodeState.ABORTED, EpisodeState.INFRA_FAILED}),
    EpisodeState.VERIFYING: frozenset({EpisodeState.COMPLETED, EpisodeState.INVALID, EpisodeState.INFRA_FAILED}),
    EpisodeState.COMPLETED: frozenset(),
    EpisodeState.ABORTED: frozenset(),
    EpisodeState.INVALID: frozenset(),
    EpisodeState.INFRA_FAILED: frozenset(),
}


class InvalidEpisodeTransition(RuntimeError):
    """Raised when execution attempts to bypass a lifecycle invariant."""


def assert_transition(current: EpisodeState, target: EpisodeState) -> None:
    """Reject transitions that could make execution/evidence ordering ambiguous."""

    if target not in _TRANSITIONS[current]:
        raise InvalidEpisodeTransition(f"illegal transition {current.value} -> {target.value}")


def is_terminal(state: EpisodeState) -> bool:
    """Return whether no further lifecycle transition is permitted."""

    return state in _TERMINAL

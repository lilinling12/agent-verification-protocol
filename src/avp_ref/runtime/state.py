"""Reference projection of the AVP Core Episode lifecycle.

The normative lifecycle is defined by ``spec/core/episode-lifecycle.md`` and
its TCK vectors. This module implements that contract; it does not define
protocol semantics independently.
"""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Final, Mapping


class EpisodeState(str, Enum):
    """Externally observable AVP Core lifecycle states."""

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


_TERMINAL: Final[frozenset[EpisodeState]] = frozenset(
    {
        EpisodeState.COMPLETED,
        EpisodeState.ABORTED,
        EpisodeState.INVALID,
        EpisodeState.INFRA_FAILED,
    }
)

_TRANSITIONS: Final[Mapping[EpisodeState, frozenset[EpisodeState]]] = MappingProxyType(
    {
        EpisodeState.CREATED: frozenset({EpisodeState.PROVISIONING, EpisodeState.ABORTED}),
        EpisodeState.PROVISIONING: frozenset(
            {
                EpisodeState.READY,
                EpisodeState.ABORTED,
                EpisodeState.INVALID,
                EpisodeState.INFRA_FAILED,
            }
        ),
        EpisodeState.READY: frozenset(
            {
                EpisodeState.RUNNING,
                EpisodeState.ABORTED,
                EpisodeState.INVALID,
                EpisodeState.INFRA_FAILED,
            }
        ),
        EpisodeState.RUNNING: frozenset(
            {
                EpisodeState.QUIESCING,
                EpisodeState.ABORTED,
                EpisodeState.INVALID,
                EpisodeState.INFRA_FAILED,
                EpisodeState.PAUSED,
            }
        ),
        EpisodeState.PAUSED: frozenset(
            {
                EpisodeState.RUNNING,
                EpisodeState.ABORTED,
                EpisodeState.INVALID,
                EpisodeState.INFRA_FAILED,
            }
        ),
        EpisodeState.QUIESCING: frozenset(
            {
                EpisodeState.VERIFYING,
                EpisodeState.ABORTED,
                EpisodeState.INVALID,
                EpisodeState.INFRA_FAILED,
            }
        ),
        EpisodeState.VERIFYING: frozenset(
            {
                EpisodeState.COMPLETED,
                EpisodeState.ABORTED,
                EpisodeState.INVALID,
                EpisodeState.INFRA_FAILED,
            }
        ),
        EpisodeState.COMPLETED: frozenset(),
        EpisodeState.ABORTED: frozenset(),
        EpisodeState.INVALID: frozenset(),
        EpisodeState.INFRA_FAILED: frozenset(),
    }
)


class InvalidEpisodeTransition(RuntimeError):
    """Raised when execution attempts to violate the Core lifecycle relation."""


def assert_transition(current: EpisodeState, target: EpisodeState) -> None:
    """Reject a transition outside the AVP Core relation implemented here."""

    if target not in _TRANSITIONS[current]:
        raise InvalidEpisodeTransition(
            f"illegal transition {current.value} -> {target.value}"
        )


def is_terminal(state: EpisodeState) -> bool:
    """Return whether Core forbids every outbound lifecycle transition."""

    return state in _TERMINAL

"""Runtime-neutral Subject authorization policy extension point."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SubjectCapabilityRequest:
    """One Subject attempt to exercise a named runtime capability."""

    episode_id: str
    actor_id: str
    capability: str


class SubjectExecutionDenied(RuntimeError):
    """Typed, audit-safe policy denial raised before downstream execution."""

    def __init__(
        self,
        code: str,
        *,
        actor_id: str,
        capability: str,
        policy_digest: str | None = None,
    ) -> None:
        if not code:
            raise ValueError("policy denial code must be non-empty")
        self.code = code
        self.actor_id = actor_id
        self.capability = capability
        self.policy_digest = policy_digest
        super().__init__(
            f"{code}: actor={actor_id!r} capability={capability!r}"
        )


class SubjectExecutionPolicy(Protocol):
    """Authorize Subject capabilities before MCP or Environment routing."""

    def authorize(self, request: SubjectCapabilityRequest) -> None:
        """Return for allow; raise SubjectExecutionDenied for deny."""

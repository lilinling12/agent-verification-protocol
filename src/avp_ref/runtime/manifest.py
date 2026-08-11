"""Immutable Episode identity manifest."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from avp_ref.canonical import digest

from .agent import AgentSystem


@dataclass(frozen=True, slots=True)
class EpisodeManifest:
    """Captures the immutable inputs required to reproduce an Episode."""

    scenario_digest: str
    agent_digest: str
    runtime_version: str
    environment_digest: str | None = None
    oracle_digest: str | None = None

    @classmethod
    def create(cls, scenario_digest: str, agent: AgentSystem, runtime_version: str, environment_digest: str | None = None, oracle_digest: str | None = None) -> "EpisodeManifest":
        return cls(
            scenario_digest=scenario_digest,
            agent_digest=digest(agent.to_dict()),
            runtime_version=runtime_version,
            environment_digest=environment_digest,
            oracle_digest=oracle_digest,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_digest": self.scenario_digest,
            "agent_digest": self.agent_digest,
            "environment_digest": self.environment_digest,
            "oracle_digest": self.oracle_digest,
            "runtime_version": self.runtime_version,
        }

    @property
    def digest(self) -> str:
        return digest(self.to_dict())

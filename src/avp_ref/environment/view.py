"""Capability-restricted evaluator view over a provisioned environment."""

from __future__ import annotations

from dataclasses import dataclass

from .adapter import EnvironmentAdapter
from .models import EnvironmentHandle, StateProjection


@dataclass(frozen=True, slots=True)
class ReadOnlyEvaluatorEnvironment:
    """Expose authoritative reads to Oracles without mutation capabilities."""

    adapter: EnvironmentAdapter
    handle: EnvironmentHandle

    def project(self, projection_id: str) -> StateProjection:
        return self.adapter.project(self.handle, projection_id)

    def digest(self, projection_id: str | None = None) -> str:
        return self.adapter.digest(self.handle, projection_id)

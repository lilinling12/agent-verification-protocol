"""Security capability policy implementation."""

from __future__ import annotations

from dataclasses import dataclass, field

from avp_ref.canonical import digest
from avp_ref.scenario.models import ScenarioInstance

from avp_ref.runtime.subject_policy import (
    SubjectCapabilityRequest,
    SubjectExecutionDenied,
)


@dataclass(slots=True)
class CapabilityGuardPolicy:
    """Scenario-bound capability deny-by-default policy."""

    _allowed: dict[str, dict[str, frozenset[str]]] = field(default_factory=dict)

    def bind(self, episode_id: str, scenario: ScenarioInstance) -> None:
        if episode_id in self._allowed:
            raise ValueError(f"policy already bound: {episode_id}")
        capabilities = scenario.document.get("capabilities", {})
        self._allowed[episode_id] = {
            str(actor): frozenset(
                str(item).rsplit("/", 1)[-1]
                for item in value.get("include", ())
                if str(item).startswith("mcp://") and "/" in str(item)
            )
            for actor, value in capabilities.items()
            if hasattr(value, "get")
        }

    def policy_digest(self, episode_id: str) -> str:
        return digest({
            "type": "capability-guard",
            "allowed": {
                actor: sorted(values)
                for actor, values in sorted(
                    self._allowed.get(episode_id, {}).items()
                )
            },
        })

    def authorize(self, request: SubjectCapabilityRequest) -> None:
        if request.episode_id not in self._allowed:
            raise SubjectExecutionDenied(
                "POLICY_UNAVAILABLE",
                actor_id=request.actor_id,
                capability=request.capability,
            )
        allowed = self._allowed[request.episode_id].get(
            request.actor_id,
            frozenset(),
        )
        if request.capability not in allowed:
            raise SubjectExecutionDenied(
                "CAPABILITY_DENIED",
                actor_id=request.actor_id,
                capability=request.capability,
                policy_digest=self.policy_digest(request.episode_id),
            )

    def release(self, episode_id: str) -> None:
        self._allowed.pop(episode_id, None)

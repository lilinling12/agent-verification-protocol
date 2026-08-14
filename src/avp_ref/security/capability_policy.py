"""Scenario-bound capability authorization for the Security profile."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from avp_ref.canonical import digest
from avp_ref.runtime.subject_policy import SubjectCapabilityRequest, SubjectExecutionDenied
from avp_ref.scenario.models import ScenarioInstance


@dataclass(frozen=True, slots=True)
class CapabilityDenialRecord:
    """Audit-safe record proving a request was denied before downstream routing."""

    episode_id: str
    actor_id: str
    capability: str
    code: str
    policy_digest: str | None


@dataclass(slots=True)
class CapabilityGuardPolicy:
    """Per-Episode, deny-by-default policy compiled from Scenario capabilities."""

    _allowed: dict[str, Mapping[str, frozenset[str]]] = field(default_factory=dict)
    _denials: dict[str, list[CapabilityDenialRecord]] = field(default_factory=dict)

    def bind(self, episode_id: str, scenario: ScenarioInstance) -> None:
        if not episode_id:
            raise ValueError("episode_id must be non-empty")
        if episode_id in self._allowed:
            raise ValueError(f"policy already bound for episode: {episode_id}")
        capabilities = scenario.document.get("capabilities", {})
        compiled: dict[str, frozenset[str]] = {}
        if hasattr(capabilities, "items"):
            for actor_id, raw in capabilities.items():
                include = raw.get("include", ()) if hasattr(raw, "get") else ()
                compiled[str(actor_id)] = frozenset(
                    self._tool_name(item) for item in include if self._is_mcp_tool(item)
                )
        self._allowed[episode_id] = compiled
        self._denials[episode_id] = []

    def authorize(self, request: SubjectCapabilityRequest) -> None:
        compiled = self._allowed.get(request.episode_id)
        if compiled is None:
            self._deny(request, "POLICY_UNAVAILABLE", None)
        policy_digest = self.policy_digest(request.episode_id)
        allowed = compiled.get(request.actor_id, frozenset())
        if request.capability not in allowed:
            self._deny(request, "CAPABILITY_DENIED", policy_digest)

    def release(self, episode_id: str) -> None:
        self._allowed.pop(episode_id, None)
        self._denials.pop(episode_id, None)

    def policy_digest(self, episode_id: str) -> str:
        compiled = self._allowed.get(episode_id)
        if compiled is None:
            raise KeyError(f"policy is not bound for episode: {episode_id}")
        return digest(
            {
                "type": "avp.security/capability-guard-v0.1",
                "allowed": {
                    actor: sorted(values)
                    for actor, values in sorted(compiled.items())
                },
            }
        )

    def denial_records(self, episode_id: str) -> tuple[CapabilityDenialRecord, ...]:
        return tuple(self._denials.get(episode_id, ()))

    def _deny(
        self,
        request: SubjectCapabilityRequest,
        code: str,
        policy_digest: str | None,
    ) -> None:
        record = CapabilityDenialRecord(
            request.episode_id,
            request.actor_id,
            request.capability,
            code,
            policy_digest,
        )
        self._denials.setdefault(request.episode_id, []).append(record)
        raise SubjectExecutionDenied(
            code,
            actor_id=request.actor_id,
            capability=request.capability,
            policy_digest=policy_digest,
        )

    @staticmethod
    def _is_mcp_tool(value: object) -> bool:
        text = str(value)
        return text.startswith("mcp://") and "/" in text

    @staticmethod
    def _tool_name(value: object) -> str:
        return str(value).rsplit("/", 1)[-1]

"""Subject Adapter decorator enforcing Security-profile capability policy."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from avp_ref.runtime.agent import AgentSystem
from avp_ref.runtime.subject_policy import SubjectCapabilityRequest, SubjectExecutionPolicy
from avp_ref.scenario.models import ScenarioInstance
from avp_ref.subject.adapter import SubjectAdapter, SubjectToolGateway
from avp_ref.subject.models import (
    SubjectDescription,
    SubjectHandle,
    SubjectInvocation,
    SubjectResult,
)


class ScenarioBoundSubjectExecutionPolicy(SubjectExecutionPolicy, Protocol):
    """Security policy whose immutable authorization state is Episode-scoped."""

    def bind(self, episode_id: str, scenario: ScenarioInstance) -> None: ...
    def release(self, episode_id: str) -> None: ...


@dataclass(slots=True)
class _BoundHandle:
    outer: SubjectHandle
    inner: SubjectHandle
    episode_id: str | None = None


class _GuardedGateway:
    __slots__ = ("_inner", "_policy", "_episode_id")

    def __init__(
        self,
        inner: SubjectToolGateway,
        policy: ScenarioBoundSubjectExecutionPolicy,
        episode_id: str,
    ) -> None:
        self._inner = inner
        self._policy = policy
        self._episode_id = episode_id

    def observe(self) -> Mapping[str, Any]:
        return self._inner.observe()

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Any:
        self._policy.authorize(
            SubjectCapabilityRequest(
                episode_id=self._episode_id,
                actor_id="subject",
                capability=name,
            )
        )
        return self._inner.call_tool(name, arguments)

    def trace_headers(self) -> Mapping[str, str]:
        return self._inner.trace_headers()


class CapabilityGuardedSubjectAdapter:
    """Decorate a SubjectAdapter with fail-closed Scenario capability enforcement.

    The decorator creates its own SubjectHandle so callers cannot accidentally
    couple lifecycle operations to the wrapped adapter's private handle identity.
    The wrapped adapter and Scenario digests are included in the description
    metadata, making the enforcement configuration part of Episode identity.
    """

    _VERSION = "0.1.0"

    def __init__(
        self,
        inner: SubjectAdapter,
        scenario: ScenarioInstance,
        policy: ScenarioBoundSubjectExecutionPolicy,
    ) -> None:
        self._inner = inner
        self._scenario = scenario
        self._policy = policy
        self._handles: dict[str, _BoundHandle] = {}
        inner_description = inner.describe()
        self._description = SubjectDescription(
            name=f"capability-guard({inner_description.name})",
            version=self._VERSION,
            adapter="capability-guard",
            transport=inner_description.transport,
            metadata={
                "innerSubjectAdapterDigest": inner_description.identity_digest,
                "scenarioInstanceDigest": scenario.instance_digest,
                "enforcement": "avp.security/capability-guard-v0.1",
            },
        )

    def describe(self) -> SubjectDescription:
        return self._description

    def open(self, agent_system: AgentSystem) -> SubjectHandle:
        inner_handle = self._inner.open(agent_system)
        outer = SubjectHandle(
            handle_id="subj_guard_" + uuid.uuid4().hex[:16],
            adapter_name=self._description.name,
            adapter_version=self._description.version,
            agent_system_digest=agent_system.identity_digest,
        )
        self._handles[outer.handle_id] = _BoundHandle(outer, inner_handle)
        return outer

    def invoke(
        self,
        handle: SubjectHandle,
        invocation: SubjectInvocation,
        gateway: SubjectToolGateway,
    ) -> SubjectResult:
        bound = self._bound(handle)
        if bound.episode_id is not None and bound.episode_id != invocation.episode_id:
            raise ValueError("subject handle cannot be reused across Episodes")
        if bound.episode_id is None:
            self._policy.bind(invocation.episode_id, self._scenario)
            bound.episode_id = invocation.episode_id
        return self._inner.invoke(
            bound.inner,
            invocation,
            _GuardedGateway(gateway, self._policy, invocation.episode_id),
        )

    def release(self, handle: SubjectHandle) -> None:
        bound = self._bound(handle)
        try:
            self._inner.release(bound.inner)
        finally:
            if bound.episode_id is not None:
                self._policy.release(bound.episode_id)
            self._handles.pop(handle.handle_id, None)

    def _bound(self, handle: SubjectHandle) -> _BoundHandle:
        bound = self._handles.get(handle.handle_id)
        if bound is None or bound.outer != handle:
            raise ValueError(f"unknown or mismatched guarded Subject handle: {handle.handle_id}")
        return bound

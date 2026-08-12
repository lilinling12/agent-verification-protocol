"""In-memory reference Environment Adapter backed by ``CommerceWorld``.

This adapter is a conformance fixture, not the generic Environment Fabric. It
exists to prove the SPI against deterministic authoritative state before real
PostgreSQL, browser, MCP, container, and VM adapters are introduced.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from typing import Any

from avp_ref.canonical import digest
from avp_ref.scenario.models import ScenarioInstance
from avp_ref.world import CommerceWorld

from .errors import (
    FaultInjectionError,
    SnapshotNotFoundError,
    ToolExecutionError,
    ToolPermissionDenied,
    UnknownEnvironmentHandle,
    UnsupportedEnvironmentError,
)
from .models import (
    EnvironmentCapability,
    EnvironmentDescription,
    EnvironmentHandle,
    FaultHandle,
    FaultObservation,
    FaultPhase,
    FaultSpec,
    ResetResult,
    ResetTarget,
    RestoreEquivalence,
    RestoreResult,
    SnapshotRef,
    StateDiff,
    StateProjection,
    ToolRequest,
    ToolResult,
)

_SUPPORTED_REF = "env://commerce-reference@0.2.0"


@dataclass(slots=True)
class _StoredSnapshot:
    ref: SnapshotRef
    state: dict[str, Any]


@dataclass(slots=True)
class _FaultRule:
    handle: FaultHandle
    spec: FaultSpec
    calls_seen: int = 0


@dataclass(slots=True)
class _Session:
    world: CommerceWorld
    scenario_digest: str
    initial_digest: str
    allowed_tools: dict[str, frozenset[str]]
    snapshots: dict[str, _StoredSnapshot] = field(default_factory=dict)
    faults: dict[str, _FaultRule] = field(default_factory=dict)


class InMemoryCommerceAdapter:
    """Deterministic adapter used by the AVP reference benchmark and TCK."""

    def __init__(self) -> None:
        self._sessions: dict[str, _Session] = {}
        self._description = EnvironmentDescription(
            name="commerce-reference",
            version="0.2.0",
            adapter="in-memory-commerce",
            capabilities=(
                EnvironmentCapability.OBSERVE,
                EnvironmentCapability.EXECUTE,
                EnvironmentCapability.STATE_PROJECTION,
                EnvironmentCapability.STATE_DIGEST,
                EnvironmentCapability.STATE_DIFF,
                EnvironmentCapability.SNAPSHOT,
                EnvironmentCapability.RESTORE,
                EnvironmentCapability.RESET,
                EnvironmentCapability.FAULT_INJECTION,
                EnvironmentCapability.RELEASE,
            ),
            isolation="in-process-reference",
            metadata={"supported_environment_refs": [_SUPPORTED_REF], "snapshot_fidelity": "state-equivalent"},
        )

    def describe(self) -> EnvironmentDescription:
        return self._description

    def provision(self, scenario: ScenarioInstance) -> EnvironmentHandle:
        environment = scenario.document.get("environment", {})
        environment_ref = environment.get("ref") if hasattr(environment, "get") else None
        if environment_ref != _SUPPORTED_REF:
            raise UnsupportedEnvironmentError(f"unsupported environment ref: {environment_ref!r}")
        handle = EnvironmentHandle(
            handle_id="env_" + uuid.uuid4().hex[:16],
            adapter_name=self._description.name,
            adapter_version=self._description.version,
            scenario_digest=scenario.instance_digest,
        )
        world = CommerceWorld()
        allowed_tools = self._resolve_allowed_tools(scenario)
        self._sessions[handle.handle_id] = _Session(
            world=world,
            scenario_digest=scenario.instance_digest,
            initial_digest=world.state_digest(),
            allowed_tools=allowed_tools,
        )
        return handle

    def reset(self, handle: EnvironmentHandle, target: ResetTarget = ResetTarget.INITIAL) -> ResetResult:
        if target is not ResetTarget.INITIAL:
            raise ValueError(f"unsupported reset target: {target}")
        session = self._session(handle)
        before = session.world.state_digest()
        session.world.reset()
        session.faults.clear()
        after = session.world.state_digest()
        return ResetResult(handle.handle_id, target, before, after, after == session.initial_digest)

    def release(self, handle: EnvironmentHandle) -> None:
        self._session(handle)
        del self._sessions[handle.handle_id]

    def logical_time(self, handle: EnvironmentHandle) -> int:
        return self._session(handle).world.logical_time

    def observe(self, handle: EnvironmentHandle, actor_id: str):
        session = self._session(handle)
        if actor_id not in session.allowed_tools:
            raise ToolPermissionDenied(f"unknown or unprovisioned actor: {actor_id}")
        return session.world.public_observation()

    def execute(self, handle: EnvironmentHandle, request: ToolRequest) -> ToolResult:
        session = self._session(handle)
        allowed = session.allowed_tools.get(request.actor_id)
        if allowed is None or request.name not in allowed:
            raise ToolPermissionDenied(f"actor '{request.actor_id}' cannot call tool '{request.name}'")
        self._apply_fault_if_due(session, request.name)
        before_digest = session.world.state_digest()
        result, before, after = session.world.call_tool(request.name, dict(request.arguments))
        after_digest = session.world.state_digest()
        changes = tuple(session.world.semantic_diff(before, after))
        state_diff = None
        if changes:
            state_diff = StateDiff(None, before_digest, after_digest, changes)
        return ToolResult(request, copy.deepcopy(result), before_digest, after_digest, state_diff)

    def project(self, handle: EnvironmentHandle, projection_id: str) -> StateProjection:
        session = self._session(handle)
        data = session.world.privileged_projection(projection_id)
        return StateProjection(projection_id, data, digest(data))

    def digest(self, handle: EnvironmentHandle, projection_id: str | None = None) -> str:
        session = self._session(handle)
        if projection_id is None:
            return session.world.state_digest()
        return self.project(handle, projection_id).digest

    def diff(self, handle: EnvironmentHandle, before: SnapshotRef, after: SnapshotRef, projection_id: str | None = None) -> StateDiff:
        session = self._session(handle)
        before_stored = self._snapshot(session, handle, before)
        after_stored = self._snapshot(session, handle, after)
        if projection_id is None:
            before_data = before_stored.state
            after_data = after_stored.state
            before_digest = before.state_digest
            after_digest = after.state_digest
            changes = tuple(session.world.semantic_diff(before_data, after_data))
        else:
            before_data = CommerceWorld.project_state(before_stored.state, projection_id)
            after_data = CommerceWorld.project_state(after_stored.state, projection_id)
            before_digest = digest(before_data)
            after_digest = digest(after_data)
            changes = () if before_data == after_data else ({"projection": projection_id, "before": before_data, "after": after_data},)
        return StateDiff(projection_id, before_digest, after_digest, changes)

    def snapshot(self, handle: EnvironmentHandle) -> SnapshotRef:
        session = self._session(handle)
        snapshot_id = f"snap_{len(session.snapshots) + 1}"
        ref = SnapshotRef(
            snapshot_id=snapshot_id,
            handle_id=handle.handle_id,
            state_digest=session.world.state_digest(),
            logical_time=session.world.logical_time,
            consistency="application-consistent",
            adapter_name=self._description.name,
        )
        session.snapshots[snapshot_id] = _StoredSnapshot(ref, session.world.snapshot_state())
        return ref

    def restore(self, handle: EnvironmentHandle, snapshot: SnapshotRef) -> RestoreResult:
        session = self._session(handle)
        stored = self._snapshot(session, handle, snapshot)
        before = session.world.state_digest()
        session.world.restore_state(stored.state, stored.ref.logical_time)
        after = session.world.state_digest()
        equivalence = RestoreEquivalence.STATE_EQUIVALENT if after == snapshot.state_digest else RestoreEquivalence.NON_EQUIVALENT
        return RestoreResult(snapshot.snapshot_id, before, after, equivalence)

    def inject_fault(self, handle: EnvironmentHandle, fault: FaultSpec) -> FaultHandle:
        session = self._session(handle)
        if fault.kind != "tool.error":
            raise FaultInjectionError(f"unsupported fault kind: {fault.kind}")
        if fault.target not in set().union(*session.allowed_tools.values()):
            raise FaultInjectionError(f"fault target is not a provisioned tool: {fault.target}")
        fault_handle = FaultHandle(
            fault_id="fault_" + uuid.uuid4().hex[:12],
            handle_id=handle.handle_id,
            kind=fault.kind,
            target=fault.target,
        )
        session.faults[fault_handle.fault_id] = _FaultRule(fault_handle, fault)
        return fault_handle

    def clear_fault(self, handle: EnvironmentHandle, fault: FaultHandle) -> None:
        session = self._session(handle)
        if fault.handle_id != handle.handle_id:
            raise FaultInjectionError("fault handle belongs to a different environment")
        session.faults.pop(fault.fault_id, None)

    def _session(self, handle: EnvironmentHandle) -> _Session:
        session = self._sessions.get(handle.handle_id)
        if session is None:
            raise UnknownEnvironmentHandle(f"unknown environment handle: {handle.handle_id}")
        if handle.adapter_name != self._description.name or handle.adapter_version != self._description.version:
            raise UnknownEnvironmentHandle("environment handle adapter identity does not match this adapter")
        if handle.scenario_digest != session.scenario_digest:
            raise UnknownEnvironmentHandle("environment handle scenario digest does not match provisioned session")
        return session

    @staticmethod
    def _snapshot(session: _Session, handle: EnvironmentHandle, ref: SnapshotRef) -> _StoredSnapshot:
        if ref.handle_id != handle.handle_id:
            raise SnapshotNotFoundError("snapshot belongs to a different environment handle")
        stored = session.snapshots.get(ref.snapshot_id)
        if stored is None or stored.ref != ref:
            raise SnapshotNotFoundError(f"unknown or mismatched snapshot: {ref.snapshot_id}")
        return stored

    @staticmethod
    def _resolve_allowed_tools(scenario: ScenarioInstance) -> dict[str, frozenset[str]]:
        capabilities = scenario.document.get("capabilities", {})
        actors = scenario.document.get("actors", ())
        resolved: dict[str, frozenset[str]] = {}
        for actor in actors:
            actor_id = str(actor.get("id"))
            actor_caps = capabilities.get(actor_id, {}) if hasattr(capabilities, "get") else {}
            includes = actor_caps.get("include", ()) if hasattr(actor_caps, "get") else ()
            tools = []
            for item in includes:
                value = str(item)
                if value.startswith("mcp://") and "/" in value:
                    tools.append(value.rsplit("/", 1)[-1])
            resolved[actor_id] = frozenset(tools)
        return resolved

    @staticmethod
    def _apply_fault_if_due(session: _Session, tool_name: str) -> None:
        for fault_id, rule in tuple(session.faults.items()):
            if rule.spec.target != tool_name:
                continue
            rule.calls_seen += 1
            if rule.calls_seen != rule.spec.occurrence:
                continue
            observations = (
                FaultObservation(rule.handle.fault_id, FaultPhase.ACTIVATED, rule.spec.kind, rule.spec.target),
                FaultObservation(rule.handle.fault_id, FaultPhase.OBSERVED, rule.spec.kind, rule.spec.target),
                FaultObservation(rule.handle.fault_id, FaultPhase.CLEARED, rule.spec.kind, rule.spec.target),
            )
            del session.faults[fault_id]
            error = str(rule.spec.parameters.get("error", "injected tool failure"))
            raise ToolExecutionError(error, observations)

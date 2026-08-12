"""Protocol contracts for AVP Environment Adapter implementations."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from avp_ref.scenario.models import ScenarioInstance

from .models import (
    EnvironmentDescription,
    EnvironmentHandle,
    FaultHandle,
    FaultSpec,
    ResetResult,
    ResetTarget,
    RestoreResult,
    SnapshotRef,
    StateDiff,
    StateProjection,
    ToolRequest,
    ToolResult,
)


@runtime_checkable
class EnvironmentAdapter(Protocol):
    """Environment lifecycle and authoritative-state SPI.

    Implementations own mutable environment resources. Callers interact through
    opaque handles so runtime code never depends on adapter-specific world,
    database connection, browser context, container, or VM objects.
    """

    def describe(self) -> EnvironmentDescription: ...

    def provision(self, scenario: ScenarioInstance) -> EnvironmentHandle: ...

    def reset(self, handle: EnvironmentHandle, target: ResetTarget = ResetTarget.INITIAL) -> ResetResult: ...

    def release(self, handle: EnvironmentHandle) -> None: ...

    def logical_time(self, handle: EnvironmentHandle) -> int: ...

    def observe(self, handle: EnvironmentHandle, actor_id: str) -> Mapping[str, Any]: ...

    def execute(self, handle: EnvironmentHandle, request: ToolRequest) -> ToolResult: ...

    def project(self, handle: EnvironmentHandle, projection_id: str) -> StateProjection: ...

    def digest(self, handle: EnvironmentHandle, projection_id: str | None = None) -> str: ...

    def diff(
        self,
        handle: EnvironmentHandle,
        before: SnapshotRef,
        after: SnapshotRef,
        projection_id: str | None = None,
    ) -> StateDiff: ...

    def snapshot(self, handle: EnvironmentHandle) -> SnapshotRef: ...

    def restore(self, handle: EnvironmentHandle, snapshot: SnapshotRef) -> RestoreResult: ...

    def inject_fault(self, handle: EnvironmentHandle, fault: FaultSpec) -> FaultHandle: ...

    def clear_fault(self, handle: EnvironmentHandle, fault: FaultHandle) -> None: ...


class EvaluatorEnvironment(Protocol):
    """Read-only evaluator surface intentionally narrower than EnvironmentAdapter."""

    def project(self, projection_id: str) -> StateProjection: ...

    def digest(self, projection_id: str | None = None) -> str: ...

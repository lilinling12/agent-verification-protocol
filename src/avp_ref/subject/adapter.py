"""Subject Adapter contracts."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from avp_ref.runtime.agent import AgentSystem

from .models import SubjectDescription, SubjectHandle, SubjectInvocation, SubjectResult


class SubjectToolGateway(Protocol):
    """Minimal Agent-facing gateway exposed by the Runtime."""

    def observe(self) -> Mapping[str, Any]: ...
    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Any: ...
    def trace_headers(self) -> Mapping[str, str]: ...


@runtime_checkable
class SubjectAdapter(Protocol):
    def describe(self) -> SubjectDescription: ...
    def open(self, agent_system: AgentSystem) -> SubjectHandle: ...
    def invoke(self, handle: SubjectHandle, invocation: SubjectInvocation, gateway: SubjectToolGateway) -> SubjectResult: ...
    def release(self, handle: SubjectHandle) -> None: ...

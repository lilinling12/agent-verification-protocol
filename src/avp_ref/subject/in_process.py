"""In-process Subject Adapter used by unit tests and reference benchmarks."""

from __future__ import annotations

import uuid
from typing import Any, Callable, Mapping

from avp_ref.runtime.agent import AgentSystem

from .errors import SubjectExecutionError, SubjectTransportError
from .models import SubjectDescription, SubjectHandle, SubjectInvocation, SubjectResult, SubjectStatus

SubjectCallable = Callable[[Any, Mapping[str, Any]], str]


class InProcessSubjectAdapter:
    """Reference-only adapter; not a process-isolation boundary."""

    def __init__(self, subject: SubjectCallable, *, name: str | None = None) -> None:
        self._subject = subject
        self._name = name or getattr(subject, "__name__", "in-process-subject")
        self._handles: dict[str, str] = {}
        self._description = SubjectDescription(
            name=self._name,
            version="0.1.0",
            adapter="in-process",
            transport="python-callable",
            metadata={"isolation": "none"},
        )

    def describe(self) -> SubjectDescription:
        return self._description

    def open(self, agent_system: AgentSystem) -> SubjectHandle:
        handle = SubjectHandle(
            handle_id="subj_" + uuid.uuid4().hex[:16],
            adapter_name=self._description.name,
            adapter_version=self._description.version,
            agent_system_digest=agent_system.identity_digest,
        )
        self._handles[handle.handle_id] = agent_system.identity_digest
        return handle

    def invoke(self, handle: SubjectHandle, invocation: SubjectInvocation, gateway) -> SubjectResult:
        self._assert_handle(handle)
        try:
            report = self._subject(gateway, invocation.task)
        except SubjectExecutionError:
            raise
        except Exception as exc:
            raise SubjectExecutionError(f"in-process subject failed: {type(exc).__name__}: {exc}") from exc
        return SubjectResult(SubjectStatus.COMPLETED, str(report), 1, {"adapter": "in-process"})

    def release(self, handle: SubjectHandle) -> None:
        self._assert_handle(handle)
        del self._handles[handle.handle_id]

    def _assert_handle(self, handle: SubjectHandle) -> None:
        digest = self._handles.get(handle.handle_id)
        if digest is None or digest != handle.agent_system_digest:
            raise SubjectTransportError(f"unknown subject handle: {handle.handle_id}")

"""Synchronous HTTP Subject Adapter for independently running Agents."""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, Mapping
from urllib.parse import urlsplit

from avp_ref.canonical import digest
from avp_ref.runtime.agent import AgentSystem

from .errors import (
    SubjectBudgetExceeded,
    SubjectExecutionError,
    SubjectProtocolError,
    SubjectTimeoutError,
    SubjectTransportError,
)
from .models import (
    SubjectDescription,
    SubjectHandle,
    SubjectInvocation,
    SubjectResult,
    SubjectStatus,
    ToolCall,
)

_RESERVED_TRACE_HEADERS = frozenset({"traceparent", "tracestate", "baggage"})
_TERMINAL_FIELDS = frozenset({"report", "error", "call"})


class HTTPSubjectAdapter:
    def __init__(
        self,
        base_url: str,
        *,
        endpoint: str = "/v1/avp/invoke",
        headers: Mapping[str, str] | None = None,
    ) -> None:
        normalized = base_url.rstrip("/")
        parsed = urlsplit(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("HTTP subject base_url must be an absolute http(s) URL")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("HTTP subject base_url must not contain userinfo credentials")
        if not endpoint.startswith("/"):
            raise ValueError("HTTP subject endpoint must be an absolute path")

        configured = {
            str(key): str(value) for key, value in (headers or {}).items()
        }
        forbidden = sorted(
            key for key in configured if key.lower() in _RESERVED_TRACE_HEADERS
        )
        if forbidden:
            raise ValueError(
                "HTTP subject trace propagation headers are Runtime-owned: "
                f"{forbidden}"
            )

        self._url = normalized + endpoint
        self._headers = configured
        self._handles: dict[str, AgentSystem] = {}
        target_digest = digest(
            {
                "base_url": normalized,
                "endpoint": endpoint,
            }
        )
        self._description = SubjectDescription(
            name="http-subject",
            version="0.1.0",
            adapter="http",
            transport="http-json",
            metadata={
                "endpoint": endpoint,
                "targetDigest": target_digest,
                "automatic_retry": False,
            },
        )

    def describe(self) -> SubjectDescription:
        return self._description

    def open(self, agent_system: AgentSystem) -> SubjectHandle:
        handle = SubjectHandle(
            "subj_" + uuid.uuid4().hex[:16],
            self._description.name,
            self._description.version,
            agent_system.identity_digest,
        )
        self._handles[handle.handle_id] = agent_system
        return handle

    def invoke(
        self,
        handle: SubjectHandle,
        invocation: SubjectInvocation,
        gateway: Any,
    ) -> SubjectResult:
        agent = self._agent(handle)
        started = time.monotonic()
        observation = gateway.observe()
        previous_tool_result: dict[str, Any] | None = None
        for step in range(1, invocation.max_steps + 1):
            remaining = invocation.timeout_seconds - (time.monotonic() - started)
            if remaining <= 0:
                raise SubjectTimeoutError("subject invocation deadline exceeded")
            payload = {
                "protocol_version": "avp.subject/v0.1",
                "episode_id": invocation.episode_id,
                "step": step,
                "agent_system": agent.to_dict(),
                "task": dict(invocation.task),
                "observation": observation,
                "previous_tool_result": previous_tool_result,
            }
            frame = self._post(
                payload,
                timeout=remaining,
                trace_headers=gateway.trace_headers(),
            )
            status = frame.get("status")
            self._validate_frame_shape(status, frame)
            if status == "completed":
                report = frame.get("report")
                if report is not None and not isinstance(report, str):
                    raise SubjectProtocolError(
                        "completed.report must be a string or null"
                    )
                return SubjectResult(
                    SubjectStatus.COMPLETED,
                    report,
                    step,
                    {"transport": "http"},
                )
            if status == "failed":
                error = frame.get("error")
                if not isinstance(error, str) or not error:
                    raise SubjectProtocolError(
                        "failed.error must be a non-empty string"
                    )
                raise SubjectExecutionError(error)
            if status != "tool_call":
                raise SubjectProtocolError(
                    "response status must be tool_call, completed, or failed"
                )
            call = self._parse_tool_call(frame.get("call"))
            result = gateway.call_tool(call.name, dict(call.arguments))
            previous_tool_result = {
                "call_id": call.call_id,
                "name": call.name,
                "result": result,
            }
            observation = gateway.observe()
        raise SubjectBudgetExceeded(
            f"subject exceeded max_steps={invocation.max_steps}"
        )

    def release(self, handle: SubjectHandle) -> None:
        self._agent(handle)
        del self._handles[handle.handle_id]

    def _agent(self, handle: SubjectHandle) -> AgentSystem:
        agent = self._handles.get(handle.handle_id)
        owner_matches = (
            handle.adapter_name == self._description.name
            and handle.adapter_version == self._description.version
        )
        if (
            agent is None
            or agent.identity_digest != handle.agent_system_digest
            or not owner_matches
        ):
            raise SubjectTransportError(
                f"unknown or mismatched subject handle: {handle.handle_id}"
            )
        return agent

    def _post(
        self,
        payload: Mapping[str, Any],
        *,
        timeout: float,
        trace_headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-AVP-Subject-Version": "avp.subject/v0.1",
            **self._headers,
        }
        existing = {item.lower() for item in headers}
        for key, value in (trace_headers or {}).items():
            if key.lower() in existing:
                raise SubjectProtocolError(
                    "trace propagation header collides with configured HTTP "
                    f"subject header: {key}"
                )
            headers[str(key)] = str(value)
            existing.add(key.lower())
        request = urllib.request.Request(
            self._url,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:2048]
            raise SubjectTransportError(
                f"subject endpoint returned HTTP {exc.code}: {detail}"
            ) from exc
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            if isinstance(getattr(exc, "reason", None), socket.timeout) or isinstance(
                exc,
                (socket.timeout, TimeoutError),
            ):
                raise SubjectTimeoutError("subject HTTP request timed out") from exc
            raise SubjectTransportError(
                f"subject endpoint unreachable: {exc}"
            ) from exc
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SubjectProtocolError(
                "subject response must be UTF-8 JSON"
            ) from exc
        if not isinstance(value, dict):
            raise SubjectProtocolError("subject response root must be an object")
        return value

    @staticmethod
    def _validate_frame_shape(status: Any, frame: Mapping[str, Any]) -> None:
        allowed_by_status = {
            "completed": frozenset({"report"}),
            "failed": frozenset({"error"}),
            "tool_call": frozenset({"call"}),
        }
        allowed_terminal = allowed_by_status.get(status)
        if allowed_terminal is None:
            return
        contradictory = sorted(
            key
            for key in _TERMINAL_FIELDS
            if key in frame and key not in allowed_terminal
        )
        if contradictory:
            raise SubjectProtocolError(
                f"{status} response contains contradictory terminal fields: "
                f"{contradictory}"
            )

    @staticmethod
    def _parse_tool_call(value: Any) -> ToolCall:
        if not isinstance(value, dict):
            raise SubjectProtocolError("tool_call.call must be an object")
        call_id = value.get("call_id")
        name = value.get("name")
        arguments = value.get("arguments", {})
        if (
            not isinstance(call_id, str)
            or not call_id
            or not isinstance(name, str)
            or not name
            or not isinstance(arguments, dict)
        ):
            raise SubjectProtocolError(
                "tool_call requires string call_id/name and object arguments"
            )
        return ToolCall(call_id, name, arguments)

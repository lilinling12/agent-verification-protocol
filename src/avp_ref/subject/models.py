"""Immutable Subject Adapter value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from avp_ref.canonical import digest


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


class SubjectStatus(str, Enum):
    """Successful SubjectResult terminal state.

    Material non-success outcomes are represented by the typed SubjectAdapterError
    taxonomy rather than by a second, ambiguous result channel.
    """

    COMPLETED = "COMPLETED"


@dataclass(frozen=True, slots=True)
class SubjectDescription:
    name: str
    version: str
    adapter: str
    transport: str
    protocol_version: str = "avp.subject/v0.1"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or not self.version or not self.adapter or not self.transport:
            raise ValueError("subject description identity fields must be non-empty")
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.protocol_version,
            "name": self.name,
            "version": self.version,
            "adapter": self.adapter,
            "transport": self.transport,
            "metadata": _thaw(self.metadata),
        }

    @property
    def identity_digest(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class SubjectHandle:
    handle_id: str
    adapter_name: str
    adapter_version: str
    agent_system_digest: str


@dataclass(frozen=True, slots=True)
class SubjectInvocation:
    episode_id: str
    task: Mapping[str, Any]
    max_steps: int
    timeout_seconds: float

    def __post_init__(self) -> None:
        if not self.episode_id:
            raise ValueError("episode_id must be non-empty")
        if self.max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        object.__setattr__(self, "task", _freeze(self.task))

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "task": _thaw(self.task),
            "max_steps": self.max_steps,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass(frozen=True, slots=True)
class ToolCall:
    call_id: str
    name: str
    arguments: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.call_id or not self.name:
            raise ValueError("tool call id and name must be non-empty")
        object.__setattr__(self, "arguments", _freeze(self.arguments))

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "name": self.name,
            "arguments": _thaw(self.arguments),
        }


@dataclass(frozen=True, slots=True)
class SubjectResult:
    """Successful completion produced by a Subject Adapter.

    Execution, transport, protocol, timeout and budget failures use typed
    SubjectAdapterError subclasses and therefore cannot be mistaken for a
    successful result object.
    """

    status: SubjectStatus
    report: str | None
    steps: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status is not SubjectStatus.COMPLETED:
            raise ValueError("SubjectResult status must be COMPLETED")
        if self.steps < 0:
            raise ValueError("steps must be >= 0")
        if self.report is not None and not isinstance(self.report, str):
            raise ValueError("SubjectResult report must be a string or null")
        object.__setattr__(self, "metadata", _freeze(self.metadata))

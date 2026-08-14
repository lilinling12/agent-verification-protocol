"""Immutable value objects shared by Environment Adapter implementations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from avp_ref.canonical import digest


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


class EnvironmentCapability(str, Enum):
    """Observable capabilities an adapter may advertise to the runtime."""

    OBSERVE = "observe"
    EXECUTE = "execute"
    STATE_PROJECTION = "state_projection"
    STATE_DIGEST = "state_digest"
    STATE_DIFF = "state_diff"
    SNAPSHOT = "snapshot"
    RESTORE = "restore"
    RESET = "reset"
    FAULT_INJECTION = "fault_injection"
    RELEASE = "release"


class ResetTarget(str, Enum):
    """Reset targets supported by the Alpha SPI."""

    INITIAL = "INITIAL"


class RestoreEquivalence(str, Enum):
    """Truthful restore-equivalence levels; adapters must not overclaim fidelity."""

    EXACT = "EXACT"
    STATE_EQUIVALENT = "STATE_EQUIVALENT"
    NON_EQUIVALENT = "NON_EQUIVALENT"


class FaultPhase(str, Enum):
    SCHEDULED = "SCHEDULED"
    ACTIVATED = "ACTIVATED"
    OBSERVED = "OBSERVED"
    CLEARED = "CLEARED"


@dataclass(frozen=True, slots=True)
class EnvironmentDescription:
    """Stable identity and declared semantics of one adapter implementation."""

    name: str
    version: str
    adapter: str
    capabilities: tuple[EnvironmentCapability, ...]
    isolation: str
    protocol_version: str = "avp.environment/v0.1"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or not self.version or not self.adapter:
            raise ValueError("environment description identity fields must be non-empty")
        ordered = tuple(sorted(set(self.capabilities), key=lambda item: item.value))
        object.__setattr__(self, "capabilities", ordered)
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    def supports(self, capability: EnvironmentCapability) -> bool:
        return capability in self.capabilities

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.protocol_version,
            "name": self.name,
            "version": self.version,
            "adapter": self.adapter,
            "capabilities": [item.value for item in self.capabilities],
            "isolation": self.isolation,
            "metadata": _thaw(self.metadata),
        }

    @property
    def identity_digest(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class EnvironmentHandle:
    """Opaque runtime identity for one provisioned environment instance."""

    handle_id: str
    adapter_name: str
    adapter_version: str
    scenario_digest: str


@dataclass(frozen=True, slots=True)
class StateProjection:
    """Evaluator-only authoritative projection plus content digest."""

    projection_id: str
    data: Any
    digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", _freeze(self.data))

    def to_dict(self) -> dict[str, Any]:
        return {"projection_id": self.projection_id, "data": _thaw(self.data), "digest": self.digest}


@dataclass(frozen=True, slots=True)
class StateDiff:
    """Semantic changes between two authoritative states or projections."""

    projection_id: str | None
    before_digest: str
    after_digest: str
    changes: tuple[Mapping[str, Any], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "changes", tuple(_freeze(item) for item in self.changes))

    def to_dict(self) -> dict[str, Any]:
        return {
            "projection_id": self.projection_id,
            "before_digest": self.before_digest,
            "after_digest": self.after_digest,
            "changes": [_thaw(item) for item in self.changes],
        }


@dataclass(frozen=True, slots=True)
class SnapshotRef:
    """Opaque snapshot identity; raw evaluator state never crosses this boundary."""

    snapshot_id: str
    handle_id: str
    state_digest: str
    logical_time: int
    consistency: str
    adapter_name: str


@dataclass(frozen=True, slots=True)
class ResetResult:
    handle_id: str
    target: ResetTarget
    before_digest: str
    after_digest: str
    equivalent_to_initial: bool


@dataclass(frozen=True, slots=True)
class RestoreResult:
    snapshot_id: str
    before_digest: str
    after_digest: str
    equivalence: RestoreEquivalence


@dataclass(frozen=True, slots=True)
class ToolRequest:
    actor_id: str
    name: str
    arguments: Mapping[str, Any]
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if not self.actor_id or not self.name:
            raise ValueError("tool request actor_id and name must be non-empty")
        object.__setattr__(self, "arguments", _freeze(self.arguments))

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "name": self.name,
            "arguments": _thaw(self.arguments),
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True, slots=True)
class ToolResult:
    request: ToolRequest
    result: Any
    before_digest: str
    after_digest: str
    diff: StateDiff | None = None


@dataclass(frozen=True, slots=True)
class FaultSpec:
    """Portable fault request. Adapter-specific knobs live under ``parameters``."""

    kind: str
    target: str
    occurrence: int = 1
    parameters: Mapping[str, Any] = field(default_factory=dict)
    visibility: str = "hidden"

    def __post_init__(self) -> None:
        if not self.kind or not self.target:
            raise ValueError("fault kind and target must be non-empty")
        if self.occurrence < 1:
            raise ValueError("fault occurrence must be >= 1")
        object.__setattr__(self, "parameters", _freeze(self.parameters))


@dataclass(frozen=True, slots=True)
class FaultHandle:
    fault_id: str
    handle_id: str
    kind: str
    target: str


@dataclass(frozen=True, slots=True)
class FaultObservation:
    fault_id: str
    phase: FaultPhase
    kind: str
    target: str

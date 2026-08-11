"""Environment Adapter SPI for AVP reference implementations.

The package defines protocol-level environment semantics and must remain
independent of any specific business domain. Concrete adapters may wrap local
fixtures, databases, browsers, MCP servers, containers, or remote systems.
"""

from .adapter import EnvironmentAdapter, EvaluatorEnvironment
from .errors import (
    EnvironmentAdapterError,
    FaultInjectionError,
    SnapshotNotFoundError,
    ToolExecutionError,
    ToolPermissionDenied,
    UnknownEnvironmentHandle,
    UnsupportedEnvironmentError,
)
from .in_memory import InMemoryCommerceAdapter
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
from .view import ReadOnlyEvaluatorEnvironment

__all__ = [
    "EnvironmentAdapter",
    "EnvironmentAdapterError",
    "EnvironmentCapability",
    "EnvironmentDescription",
    "EnvironmentHandle",
    "EvaluatorEnvironment",
    "FaultHandle",
    "FaultInjectionError",
    "FaultObservation",
    "FaultPhase",
    "FaultSpec",
    "InMemoryCommerceAdapter",
    "ReadOnlyEvaluatorEnvironment",
    "ResetResult",
    "ResetTarget",
    "RestoreEquivalence",
    "RestoreResult",
    "SnapshotNotFoundError",
    "SnapshotRef",
    "StateDiff",
    "StateProjection",
    "ToolExecutionError",
    "ToolPermissionDenied",
    "ToolRequest",
    "ToolResult",
    "UnknownEnvironmentHandle",
    "UnsupportedEnvironmentError",
]

"""Typed failures raised by Environment Adapter implementations."""

from __future__ import annotations

from typing import Iterable

from .models import FaultObservation


class EnvironmentAdapterError(RuntimeError):
    """Base class for evaluator-owned environment infrastructure failures."""


class UnknownEnvironmentHandle(EnvironmentAdapterError):
    """The adapter does not own the supplied EnvironmentHandle."""


class UnsupportedEnvironmentError(EnvironmentAdapterError):
    """The adapter cannot provision the ScenarioInstance environment reference."""


class ToolPermissionDenied(EnvironmentAdapterError):
    """The actor attempted to invoke a capability that was not granted by AVS."""


class SnapshotNotFoundError(EnvironmentAdapterError):
    """The referenced snapshot does not exist for the target handle."""


class FaultInjectionError(EnvironmentAdapterError):
    """The adapter cannot represent the requested fault semantics."""


class ToolExecutionError(EnvironmentAdapterError):
    """A tool call failed inside the environment.

    ``fault_observations`` is carried separately from the human-readable error
    so the runtime can emit deterministic fault lifecycle evidence without
    parsing exception strings.
    """

    def __init__(self, message: str, fault_observations: Iterable[FaultObservation] = ()) -> None:
        super().__init__(message)
        self.fault_observations = tuple(fault_observations)

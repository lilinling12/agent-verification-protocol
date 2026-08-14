"""Typed failures for Scenario parsing, compilation, identity, and visibility.

Scenario preparation failures belong to verification infrastructure. They MUST
NOT be reported as Subject-Agent task failures, so callers need stable typed
errors rather than generic exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DiagnosticSeverity(str, Enum):
    """Severity used by compiler diagnostics."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class CompileDiagnostic:
    """A stable, machine-readable AVS compiler diagnostic."""

    code: str
    message: str
    path: str = "$"
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR


class ScenarioCompileError(Exception):
    """Base class for deterministic Scenario preparation failures."""

    def __init__(self, message: str, diagnostics: tuple[CompileDiagnostic, ...] = ()) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics


class ScenarioParseError(ScenarioCompileError):
    """The source cannot be parsed as AVS YAML/JSON."""


class ScenarioValidationError(ScenarioCompileError):
    """A ScenarioTemplate or ScenarioInstance violates its schema contract."""


class ScenarioIdentityError(ValueError):
    """A ScenarioInstance declared identity is missing or inconsistent with content."""


class ParameterResolutionError(ScenarioCompileError):
    """A parameter cannot be deterministically resolved or validated."""


class ReferenceResolutionError(ScenarioCompileError):
    """A versioned AVS reference cannot be resolved under the active policy."""


class VisibilityViolationError(ScenarioCompileError):
    """Evaluator-confidential material would cross into the Subject view."""

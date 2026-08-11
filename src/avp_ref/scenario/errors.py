"""Compilation diagnostics and typed AVS failures.

Compilation failures belong to the verification infrastructure. They MUST NOT be
reported as subject-Agent failures, so callers need machine-readable error types
rather than generic ``ValueError`` exceptions.
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
    """Base class for deterministic AVS compilation failures."""

    def __init__(self, message: str, diagnostics: tuple[CompileDiagnostic, ...] = ()) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics


class ScenarioParseError(ScenarioCompileError):
    """The source cannot be parsed as AVS YAML/JSON."""


class ScenarioValidationError(ScenarioCompileError):
    """The parsed ScenarioTemplate violates the AVS schema."""


class ParameterResolutionError(ScenarioCompileError):
    """A parameter cannot be deterministically resolved or validated."""


class ReferenceResolutionError(ScenarioCompileError):
    """A versioned AVS reference cannot be resolved under the active policy."""


class VisibilityViolationError(ScenarioCompileError):
    """Evaluator-confidential material would cross into the Subject view."""

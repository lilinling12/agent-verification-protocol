"""Agent Verification Scenario (AVS) compiler API."""

from .compiler import CompileOptions, ScenarioCompiler
from .errors import (
    CompileDiagnostic,
    ParameterResolutionError,
    ReferenceResolutionError,
    ScenarioCompileError,
    ScenarioParseError,
    ScenarioValidationError,
    VisibilityViolationError,
)
from .loader import load_scenario, validate_template
from .models import ScenarioInstance, SeedBundle
from .references import StaticReferenceResolver, SymbolicReferenceResolver

__all__ = [
    "CompileDiagnostic",
    "CompileOptions",
    "ParameterResolutionError",
    "ReferenceResolutionError",
    "ScenarioCompileError",
    "ScenarioCompiler",
    "ScenarioInstance",
    "ScenarioParseError",
    "ScenarioValidationError",
    "SeedBundle",
    "StaticReferenceResolver",
    "SymbolicReferenceResolver",
    "VisibilityViolationError",
    "load_scenario",
    "validate_template",
]

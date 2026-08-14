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
from .identity import canonical_instance_bytes, identity_preimage, scenario_instance_digest
from .loader import load_scenario, validate_instance, validate_template
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
    "canonical_instance_bytes",
    "identity_preimage",
    "load_scenario",
    "scenario_instance_digest",
    "validate_instance",
    "validate_template",
]

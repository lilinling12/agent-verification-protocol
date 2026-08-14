"""Deterministic compiler from AVS ScenarioTemplate to ScenarioInstance."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from avp_ref.canonical import digest

from .errors import CompileDiagnostic, ParameterResolutionError, ReferenceResolutionError, ScenarioValidationError, VisibilityViolationError
from .generators import GeneratorRegistry
from .identity import scenario_instance_digest
from .loader import validate_template
from .models import GeneratorRecord, ScenarioInstance, deep_freeze
from .references import ReferenceResolver, SymbolicReferenceResolver
from .seed import derive_child_seed, resolve_seed_bundle

_COMPILER_NAME = "avp-reference-avs"
_COMPILER_VERSION = "0.2.0-alpha.1"
_PLACEHOLDER = re.compile(r"\$\{(?:parameters\.)?([A-Za-z_][A-Za-z0-9_.-]*)\}")
_REFERENCE = re.compile(r"^(?:env|oracle|mcp|simulator|artifact|agent|benchmark)://[^\s]+$")
_CONFIDENTIAL_CLASSIFICATIONS = {"evaluator-confidential", "secret", "regulated"}


@dataclass(frozen=True, slots=True)
class CompileOptions:
    """Deterministic inputs and policy for one compilation."""

    root_seed: int | None = 0
    parameter_overrides: Mapping[str, Any] = field(default_factory=dict)
    strict_references: bool = False


class ScenarioCompiler:
    """Compile a validated AVS template into an immutable ScenarioInstance.

    Compilation is part of the evaluator trust boundary. It materializes every
    supported source of nondeterminism before execution, binds reference
    identities and produces the AVP Scenario v0.1 content identity. Compilation
    failures are infrastructure/configuration failures and MUST NOT count as
    Agent FAIL.
    """

    def __init__(self, *, resolver: ReferenceResolver | None = None, generators: GeneratorRegistry | None = None, compiler_version: str = _COMPILER_VERSION) -> None:
        self._resolver = resolver or SymbolicReferenceResolver()
        self._generators = generators or GeneratorRegistry()
        self._compiler_version = compiler_version

    def compile(self, template: Mapping[str, Any], options: CompileOptions | None = None) -> ScenarioInstance:
        """Compile one ScenarioTemplate without mutating the input mapping."""

        active = options or CompileOptions()
        source = copy.deepcopy(dict(template))
        validate_template(source)
        self._validate_supported_semantics(source)
        template_digest = digest(source)
        seeds = resolve_seed_bundle(source.get("seeds"), active.root_seed)
        parameters, generator_records = self._resolve_parameters(source.get("parameters", {}), active, seeds.data)
        materialized = self._substitute(source, parameters)
        materialized.pop("parameters", None)
        materialized.pop("seeds", None)
        materialized.pop("generators", None)
        materialized["kind"] = "ScenarioInstance"
        references = self._resolve_references(materialized, active.strict_references)
        self._validate_subject_visibility(materialized)
        self._reject_unresolved_placeholders(materialized)

        if references:
            materialized["referenceBindings"] = [
                {
                    "location": reference.path,
                    "reference": reference.uri,
                    "identity": reference.digest,
                    "identityType": reference.mode,
                }
                for reference in references
            ]

        materialized["provenance"] = {
            "compiler": {"name": _COMPILER_NAME, "version": self._compiler_version},
            "template": {
                "name": source["metadata"]["name"],
                "version": source["metadata"]["version"],
                "digest": template_digest,
            },
            "seedBundle": seeds.to_dict(),
            "resolvedParameters": parameters,
            "generators": [record.to_dict() for record in generator_records],
        }
        instance_digest = scenario_instance_digest(materialized)
        materialized["instanceDigest"] = instance_digest
        return ScenarioInstance(
            template_digest=template_digest,
            instance_digest=instance_digest,
            document=deep_freeze(materialized),
        )

    def _validate_supported_semantics(self, template: Mapping[str, Any]) -> None:
        if template.get("generators"):
            raise ScenarioValidationError(
                "top-level AVS generators are not yet executable in this compiler",
                (CompileDiagnostic("AVS-SEM-001", "top-level generators require a registered generator stage; use parameter.generator for Alpha 2", "$.generators"),),
            )

    def _resolve_parameters(self, declarations: Mapping[str, Any], options: CompileOptions, data_seed: int) -> tuple[dict[str, Any], tuple[GeneratorRecord, ...]]:
        if not isinstance(declarations, Mapping):
            raise ParameterResolutionError("parameters must be an object", (CompileDiagnostic("AVS-PARAM-001", "parameters must be an object", "$.parameters"),))
        overrides = dict(options.parameter_overrides)
        unknown = sorted(set(overrides) - set(declarations))
        if unknown:
            name = unknown[0]
            raise ParameterResolutionError(f"unknown parameter override '{name}'", (CompileDiagnostic("AVS-PARAM-002", f"unknown parameter override '{name}'", f"$.parameters.{name}"),))
        values: dict[str, Any] = {}
        records: list[GeneratorRecord] = []
        for name in sorted(declarations):
            spec = declarations[name]
            if not isinstance(spec, Mapping):
                raise ParameterResolutionError(f"parameter '{name}' declaration must be an object", (CompileDiagnostic("AVS-PARAM-003", "parameter declaration must be an object", f"$.parameters.{name}"),))
            if name in overrides:
                value = overrides[name]
            elif "value" in spec:
                value = spec["value"]
            elif "default" in spec:
                value = spec["default"]
            elif "generator" in spec:
                generator_spec = spec["generator"]
                if not isinstance(generator_spec, Mapping):
                    raise ParameterResolutionError(f"parameter '{name}' generator must be an object", (CompileDiagnostic("AVS-PARAM-004", "generator must be an object", f"$.parameters.{name}.generator"),))
                child_seed = derive_child_seed(data_seed, f"parameter:{name}")
                value = self._generators.generate(name, generator_spec, child_seed)
                records.append(GeneratorRecord(parameter=name, generator_type=str(generator_spec.get("type", "")), generator_version=self._generators.version, seed=child_seed))
            elif spec.get("required", True):
                raise ParameterResolutionError(f"required parameter '{name}' has no value", (CompileDiagnostic("AVS-PARAM-005", "required parameter has no value", f"$.parameters.{name}"),))
            else:
                continue
            self._validate_parameter_value(name, value, spec)
            values[name] = copy.deepcopy(value)
        return values, tuple(records)

    def _validate_parameter_value(self, name: str, value: Any, spec: Mapping[str, Any]) -> None:
        expected = spec.get("type")
        validators = {
            "string": lambda item: isinstance(item, str),
            "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
            "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
            "boolean": lambda item: isinstance(item, bool),
            "array": lambda item: isinstance(item, list),
            "object": lambda item: isinstance(item, Mapping),
        }
        if expected is not None and expected not in validators:
            raise ParameterResolutionError(f"unsupported parameter type '{expected}'", (CompileDiagnostic("AVS-PARAM-006", f"unsupported parameter type '{expected}'", f"$.parameters.{name}.type"),))
        if expected is not None and not validators[expected](value):
            raise ParameterResolutionError(f"parameter '{name}' has invalid type", (CompileDiagnostic("AVS-PARAM-007", f"expected {expected}", f"$.parameters.{name}"),))
        enum = spec.get("enum")
        if enum is not None and value not in enum:
            raise ParameterResolutionError(f"parameter '{name}' is not in enum", (CompileDiagnostic("AVS-PARAM-008", f"value must be one of {enum!r}", f"$.parameters.{name}"),))
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            minimum = spec.get("minimum", spec.get("min"))
            maximum = spec.get("maximum", spec.get("max"))
            if minimum is not None and value < minimum:
                raise ParameterResolutionError(f"parameter '{name}' is below minimum", (CompileDiagnostic("AVS-PARAM-009", f"value must be >= {minimum}", f"$.parameters.{name}"),))
            if maximum is not None and value > maximum:
                raise ParameterResolutionError(f"parameter '{name}' is above maximum", (CompileDiagnostic("AVS-PARAM-010", f"value must be <= {maximum}", f"$.parameters.{name}"),))

    def _substitute(self, value: Any, parameters: Mapping[str, Any], path: str = "$") -> Any:
        if isinstance(value, Mapping):
            return {key: self._substitute(item, parameters, f"{path}.{key}") for key, item in value.items()}
        if isinstance(value, list):
            return [self._substitute(item, parameters, f"{path}[{index}]") for index, item in enumerate(value)]
        if not isinstance(value, str):
            return value
        full = _PLACEHOLDER.fullmatch(value)
        if full:
            return self._lookup_parameter(full.group(1), parameters, path)

        def replace(match: re.Match[str]) -> str:
            resolved = self._lookup_parameter(match.group(1), parameters, path)
            if isinstance(resolved, (dict, list)):
                raise ParameterResolutionError("structured parameter cannot be interpolated into a string", (CompileDiagnostic("AVS-PARAM-011", "object/array parameters must occupy the entire field value", path),))
            return str(resolved)

        return _PLACEHOLDER.sub(replace, value)

    @staticmethod
    def _lookup_parameter(name: str, parameters: Mapping[str, Any], path: str) -> Any:
        if name not in parameters:
            raise ParameterResolutionError(f"unresolved parameter '{name}'", (CompileDiagnostic("AVS-PARAM-012", f"unresolved parameter '{name}'", path),))
        return copy.deepcopy(parameters[name])

    def _resolve_references(self, document: Any, strict: bool) -> tuple[Any, ...]:
        records = []
        for path, uri in self._collect_references(document):
            resolved = self._resolver.resolve(path, uri)
            if strict and resolved.mode != "content":
                raise ReferenceResolutionError(f"strict compilation requires content resolution: {uri}", (CompileDiagnostic("AVS-REF-002", "strict compilation requires a content-backed reference digest", path),))
            records.append(resolved)
        records.sort(key=lambda item: (item.path, item.uri, item.digest))
        return tuple(records)

    def _collect_references(self, value: Any, path: str = "$") -> list[tuple[str, str]]:
        found: list[tuple[str, str]] = []
        if isinstance(value, Mapping):
            for key in sorted(value):
                found.extend(self._collect_references(value[key], f"{path}.{key}"))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                found.extend(self._collect_references(item, f"{path}[{index}]"))
        elif isinstance(value, str) and _REFERENCE.fullmatch(value):
            found.append((path, value))
        return found

    def _validate_subject_visibility(self, document: Mapping[str, Any]) -> None:
        violation = self._find_confidential(self._subject_candidate(document))
        if violation:
            path, classification = violation
            raise VisibilityViolationError("evaluator-confidential material is present in the Subject projection", (CompileDiagnostic("AVS-VIS-001", f"classification '{classification}' is not allowed in Agent-visible material", path),))

    @staticmethod
    def _subject_candidate(document: Mapping[str, Any]) -> dict[str, Any]:
        actors = [actor for actor in document.get("actors", []) if actor.get("id") == "subject"]
        capabilities = document.get("capabilities", {})
        return {"metadata": document.get("metadata", {}), "task": document.get("task", {}), "actors": actors, "capabilities": {"subject": capabilities.get("subject", {})} if isinstance(capabilities, Mapping) else {}, "budgets": document.get("budgets", {})}

    def _find_confidential(self, value: Any, path: str = "$.subject") -> tuple[str, str] | None:
        if isinstance(value, Mapping):
            classification = value.get("classification")
            if classification in _CONFIDENTIAL_CLASSIFICATIONS:
                return path, str(classification)
            for key, item in value.items():
                found = self._find_confidential(item, f"{path}.{key}")
                if found:
                    return found
        elif isinstance(value, list):
            for index, item in enumerate(value):
                found = self._find_confidential(item, f"{path}[{index}]")
                if found:
                    return found
        return None

    def _reject_unresolved_placeholders(self, value: Any, path: str = "$") -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                self._reject_unresolved_placeholders(item, f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                self._reject_unresolved_placeholders(item, f"{path}[{index}]")
        elif isinstance(value, str) and _PLACEHOLDER.search(value):
            raise ParameterResolutionError("unresolved parameter placeholder remains after compilation", (CompileDiagnostic("AVS-PARAM-013", "unresolved placeholder", path),))

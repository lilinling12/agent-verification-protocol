"""AVS YAML/JSON loading and schema validation."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any, Mapping

from .errors import CompileDiagnostic, ScenarioParseError, ScenarioValidationError


def load_scenario(path: str | Path) -> dict[str, Any]:
    """Load one ScenarioTemplate without applying compilation semantics."""

    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise ScenarioParseError(f"unable to read scenario: {source}") from exc

    try:
        if source.suffix.lower() == ".json":
            value = json.loads(text)
        else:
            import yaml

            value = yaml.safe_load(text)
    except Exception as exc:
        raise ScenarioParseError(
            f"unable to parse AVS resource: {source}",
            (CompileDiagnostic("AVS-PARSE-001", str(exc), "$"),),
        ) from exc

    if not isinstance(value, dict):
        raise ScenarioParseError(
            "ScenarioTemplate root must be an object",
            (CompileDiagnostic("AVS-PARSE-002", "root must be a mapping/object", "$"),),
        )
    return value


def load_default_template_schema() -> dict[str, Any]:
    """Load the schema shipped with the Python reference package.

    Packaging the schema with the runtime avoids a hidden dependency on the
    repository checkout layout when ``avp`` is installed from a wheel.
    """

    text = resources.files("avp_ref.resources").joinpath("scenario.schema.json").read_text(encoding="utf-8")
    return json.loads(text)


def validate_template(template: Mapping[str, Any], schema: Mapping[str, Any] | None = None) -> None:
    """Validate a ScenarioTemplate against JSON Schema Draft 2020-12."""

    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise RuntimeError("jsonschema is required by the AVS compiler") from exc

    active_schema = dict(schema) if schema is not None else load_default_template_schema()
    Draft202012Validator.check_schema(active_schema)
    validator = Draft202012Validator(active_schema)
    diagnostics: list[CompileDiagnostic] = []
    for error in sorted(validator.iter_errors(template), key=lambda item: list(item.absolute_path)):
        path = "$" + "".join(f"[{index}]" if isinstance(index, int) else f".{index}" for index in error.absolute_path)
        diagnostics.append(CompileDiagnostic("AVS-SCHEMA-001", error.message, path))

    if diagnostics:
        raise ScenarioValidationError(
            f"ScenarioTemplate failed schema validation ({len(diagnostics)} error(s))",
            tuple(diagnostics),
        )

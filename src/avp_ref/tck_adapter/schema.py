"""Schema and semantic validation for AVP ConformanceReport documents."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from avp_ref.canonical import digest

from .loader import TCKRepository
from .models import TCKAdapterError


REPORT_SCHEMA_NAME = "report.schema.json"


def load_report_schema(repository: TCKRepository) -> Mapping[str, Any]:
    """Load and validate the repository's Draft 2020-12 report schema."""

    path = repository.tck_root / "reports" / REPORT_SCHEMA_NAME
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TCKAdapterError(f"cannot load ConformanceReport schema {path}: {exc}") from exc
    if not isinstance(document, Mapping):
        raise TCKAdapterError("ConformanceReport schema root must be an object")
    try:
        Draft202012Validator.check_schema(document)
    except SchemaError as exc:
        raise TCKAdapterError(f"invalid ConformanceReport schema: {exc.message}") from exc
    return document


def validate_report(
    report: Mapping[str, Any],
    repository: TCKRepository,
    *,
    expected_profile: str | None = None,
) -> None:
    """Validate report shape plus cross-resource and counting invariants."""

    schema = load_report_schema(repository)
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(report),
        key=lambda item: (tuple(str(part) for part in item.absolute_path), item.message),
    )
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path) or "<root>"
        raise TCKAdapterError(f"ConformanceReport schema violation at {location}: {first.message}")

    profile = report["profile"]
    profile_name = profile["name"]
    if expected_profile is not None and profile_name != expected_profile:
        raise TCKAdapterError(
            f"ConformanceReport profile mismatch: expected {expected_profile!r}, got {profile_name!r}"
        )
    profile_document = repository.load_profile(profile_name)
    profile_metadata = profile_document.get("metadata")
    if not isinstance(profile_metadata, Mapping) or profile["version"] != profile_metadata.get("version"):
        raise TCKAdapterError("ConformanceReport profile version does not match profile resource")

    if report["tck"]["version"] != repository.version:
        raise TCKAdapterError("ConformanceReport TCK version does not match registry")
    actual_registry_digest = report["tck"]["registryDigest"]
    expected_registry_digest = repository.registry_digest
    if actual_registry_digest != expected_registry_digest:
        raise TCKAdapterError(
            "ConformanceReport registry digest does not match loaded registry: "
            f"expected {expected_registry_digest}, got {actual_registry_digest}"
        )

    implementation = report["implementation"]
    expected_identity = digest(
        {"name": implementation["name"], "version": implementation["version"]}
    )
    if implementation["identityDigest"] != expected_identity:
        raise TCKAdapterError("ConformanceReport implementation identity digest is invalid")

    cases = report["cases"]
    case_ids = [item["id"] for item in cases]
    if len(case_ids) != len(set(case_ids)):
        raise TCKAdapterError("ConformanceReport contains duplicate case ids")
    loaded_cases = {
        item.case_id: item
        for item in repository.load_cases(profile_name, selected_case_ids=case_ids)
    }
    declared_capabilities = set(report["declaredCapabilities"])
    for item in cases:
        loaded = loaded_cases[item["id"]]
        status = item["status"]
        if loaded.applicability in {"mandatory", "mixed"} and status == "SKIP":
            raise TCKAdapterError(f"mandatory TCK case {loaded.case_id} cannot be skipped")
        if loaded.applicability == "conditional":
            if loaded.when is None:
                raise TCKAdapterError(f"conditional TCK case {loaded.case_id} has no condition")
            applies = loaded.when in declared_capabilities
            if applies and status == "SKIP":
                raise TCKAdapterError(
                    f"applicable conditional TCK case {loaded.case_id} cannot be skipped"
                )
            if not applies and status != "SKIP":
                raise TCKAdapterError(
                    f"non-applicable conditional TCK case {loaded.case_id} must be skipped"
                )

    observed = Counter(item["status"] for item in cases)
    summary = report["summary"]
    expected_summary = {
        "total": len(cases),
        "passed": observed["PASS"],
        "failed": observed["FAIL"],
        "skipped": observed["SKIP"],
    }
    if summary != expected_summary:
        raise TCKAdapterError(
            f"ConformanceReport summary mismatch: expected {expected_summary}, got {summary}"
        )
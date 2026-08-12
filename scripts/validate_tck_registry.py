"""Validate the AVP TCK registry, profiles, cases, and report contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "spec/core/requirement-index.yaml"
REGISTRY_PATH = ROOT / "conformance/tck/registry.yaml"
PROFILE_PATH = ROOT / "conformance/tck/profiles/avp-core-v0.1.yaml"
CASE_ROOT = ROOT / "conformance/tck/cases"
REPORT_SCHEMA_PATH = ROOT / "conformance/tck/reports/report.schema.json"
PROFILE_NAME = "avp-core-v0.1"
MANDATORY_LEVELS = {"MUST", "MUST_NOT"}


def fail(message: str) -> None:
    raise SystemExit(f"TCK registry FAIL: {message}")


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"cannot parse {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must contain a mapping")
    return value


def as_string_set(value: Any, context: str) -> set[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        fail(f"{context} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        fail(f"{context} contains duplicates")
    return set(value)


def main() -> None:
    index = load_yaml(INDEX_PATH)
    requirement_records = index.get("requirements")
    if not isinstance(requirement_records, list) or not requirement_records:
        fail("requirement index is empty")
    requirements: dict[str, dict[str, Any]] = {}
    for record in requirement_records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            fail("invalid requirement record")
        requirement_id = record["id"]
        if requirement_id in requirements:
            fail(f"duplicate requirement {requirement_id}")
        requirements[requirement_id] = record

    expected_mandatory = {
        requirement_id
        for requirement_id, record in requirements.items()
        if record.get("level") in MANDATORY_LEVELS and not record.get("condition")
    }
    expected_conditional = {
        requirement_id: record.get("condition")
        for requirement_id, record in requirements.items()
        if record.get("level") in MANDATORY_LEVELS and record.get("condition")
    }

    profile = load_yaml(PROFILE_PATH)
    if profile.get("apiVersion") != "avp.tck/v0.1" or profile.get("kind") != "ConformanceProfile":
        fail("invalid profile resource identity")
    metadata = profile.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("name") != PROFILE_NAME:
        fail(f"profile metadata.name must be {PROFILE_NAME}")
    profile_requirements = profile.get("requirements")
    if not isinstance(profile_requirements, dict):
        fail("profile requirements must be a mapping")
    mandatory = as_string_set(profile_requirements.get("mandatory"), "profile mandatory requirements")
    if mandatory != expected_mandatory:
        fail(f"profile mandatory requirements differ from requirement index: expected {sorted(expected_mandatory)}, got {sorted(mandatory)}")
    conditional_records = profile_requirements.get("conditional")
    if not isinstance(conditional_records, list):
        fail("profile conditional requirements must be a list")
    conditional: dict[str, str] = {}
    for record in conditional_records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not isinstance(record.get("when"), str):
            fail("invalid profile conditional requirement")
        if record["id"] in conditional:
            fail(f"duplicate conditional requirement {record['id']}")
        conditional[record["id"]] = record["when"]
    if conditional != expected_conditional:
        fail(f"profile conditional requirements differ from requirement index: expected {expected_conditional}, got {conditional}")

    registry = load_yaml(REGISTRY_PATH)
    if registry.get("apiVersion") != "avp.tck/v0.1" or registry.get("kind") != "TCKRegistry":
        fail("invalid registry resource identity")
    registry_cases = registry.get("cases")
    if not isinstance(registry_cases, list) or not registry_cases:
        fail("registry cases must be a non-empty list")

    entries: dict[str, dict[str, Any]] = {}
    for entry in registry_cases:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            fail("invalid registry case entry")
        case_id = entry["id"]
        if case_id in entries:
            fail(f"duplicate registry case {case_id}")
        if entry.get("profile") != PROFILE_NAME:
            fail(f"{case_id} targets unexpected profile {entry.get('profile')!r}")
        path_value = entry.get("path")
        if not isinstance(path_value, str) or not path_value.startswith("conformance/tck/cases/"):
            fail(f"{case_id} has invalid case path")
        path = ROOT / path_value
        if not path.is_file():
            fail(f"{case_id} references missing case file {path_value}")
        if path.name != f"{case_id}.yaml":
            fail(f"{case_id} filename does not match its identity")
        entries[case_id] = entry

    actual_paths = set(CASE_ROOT.rglob("*.yaml"))
    registered_paths = {ROOT / entry["path"] for entry in entries.values()}
    if actual_paths != registered_paths:
        unregistered = sorted(str(path.relative_to(ROOT)) for path in actual_paths - registered_paths)
        missing = sorted(str(path.relative_to(ROOT)) for path in registered_paths - actual_paths)
        fail(f"case file/registry mismatch; unregistered={unregistered}, missing={missing}")

    covered_mandatory: set[str] = set()
    covered_conditional: dict[str, set[str]] = {requirement_id: set() for requirement_id in conditional}
    for case_id, entry in entries.items():
        case = load_yaml(ROOT / entry["path"])
        metadata = case.get("metadata")
        if case.get("apiVersion") != "avp.tck/v0.1" or case.get("kind") != "ConformanceCase":
            fail(f"{case_id} has invalid resource identity")
        if not isinstance(metadata, dict) or metadata.get("id") != case_id:
            fail(f"{case_id} metadata.id mismatch")
        if case.get("profile") != PROFILE_NAME:
            fail(f"{case_id} profile mismatch")
        case_requirements = as_string_set(case.get("requirements"), f"{case_id} requirements")
        entry_requirements = as_string_set(entry.get("requirements"), f"registry requirements for {case_id}")
        if case_requirements != entry_requirements:
            fail(f"{case_id} requirement mapping differs from registry")
        unknown = case_requirements - requirements.keys()
        if unknown:
            fail(f"{case_id} references unknown requirements {sorted(unknown)}")
        if case.get("applicability") != entry.get("applicability"):
            fail(f"{case_id} applicability differs from registry")
        if entry.get("applicability") == "conditional":
            when = entry.get("when")
            if not isinstance(when, str) or case.get("when") != when:
                fail(f"{case_id} conditional trigger mismatch")
        for requirement_id in case_requirements:
            if requirement_id in conditional:
                covered_conditional[requirement_id].add(case_id)
            else:
                covered_mandatory.add(requirement_id)

    missing_mandatory = expected_mandatory - covered_mandatory
    if missing_mandatory:
        fail(f"mandatory profile requirements without registered TCK coverage: {sorted(missing_mandatory)}")
    for requirement_id, condition in conditional.items():
        mapped = covered_conditional.get(requirement_id, set())
        if not mapped:
            fail(f"conditional requirement {requirement_id} has no TCK coverage")
        if not any(entries[case_id].get("when") == condition for case_id in mapped if entries[case_id].get("applicability") == "conditional"):
            fail(f"conditional requirement {requirement_id} has no case with trigger {condition!r}")

    for requirement_id, record in requirements.items():
        declared_cases = as_string_set(record.get("conformance"), f"{requirement_id} conformance mapping")
        for case_id in declared_cases:
            entry = entries.get(case_id)
            if entry is None:
                fail(f"{requirement_id} references unregistered TCK case {case_id}")
            if requirement_id not in entry["requirements"]:
                fail(f"registry case {case_id} does not map back to {requirement_id}")

    try:
        report_schema = json.loads(REPORT_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(report_schema)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse report schema: {exc}")
    except Exception as exc:  # jsonschema raises a hierarchy of schema errors.
        fail(f"invalid report schema: {exc}")

    print(
        "TCK registry OK: "
        f"{len(entries)} cases, {len(expected_mandatory)} mandatory requirements, "
        f"{len(expected_conditional)} conditional requirements"
    )


if __name__ == "__main__":
    main()

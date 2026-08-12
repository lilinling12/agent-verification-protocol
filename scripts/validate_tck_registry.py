"""Validate AVP TCK registry/profile/case consistency across profiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
TCK_ROOT = ROOT / "conformance/tck"
CASE_ROOT = TCK_ROOT / "cases"
PROFILE_ROOT = TCK_ROOT / "profiles"
REGISTRY_PATH = TCK_ROOT / "registry.yaml"
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


def string_set(value: Any, context: str, *, allow_empty: bool = False) -> set[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        fail(f"{context} must be a {'non-empty ' if not allow_empty else ''}list")
    if not all(isinstance(item, str) and item for item in value):
        fail(f"{context} must contain non-empty strings")
    if len(value) != len(set(value)):
        fail(f"{context} contains duplicates")
    return set(value)


def main() -> None:
    requirements: dict[str, dict[str, Any]] = {}
    requirement_profiles: dict[str, str] = {}
    expected_by_profile: dict[str, tuple[set[str], dict[str, str]]] = {}

    for path in sorted((ROOT / "spec").glob("**/requirement-index.yaml")):
        index = load_yaml(path)
        profile_name = index.get("profile")
        records = index.get("requirements")
        if not isinstance(profile_name, str) or not profile_name:
            fail(f"{path.relative_to(ROOT)} missing profile")
        if profile_name in expected_by_profile:
            fail(f"duplicate requirement index for profile {profile_name}")
        if not isinstance(records, list) or not records:
            fail(f"empty requirement index for profile {profile_name}")
        mandatory: set[str] = set()
        conditional: dict[str, str] = {}
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("id"), str):
                fail(f"invalid requirement record in {path.relative_to(ROOT)}")
            requirement_id = record["id"]
            if requirement_id in requirements:
                fail(f"duplicate requirement {requirement_id}")
            requirements[requirement_id] = record
            requirement_profiles[requirement_id] = profile_name
            if record.get("level") in MANDATORY_LEVELS:
                condition = record.get("condition")
                if condition is None:
                    mandatory.add(requirement_id)
                elif isinstance(condition, str) and condition:
                    conditional[requirement_id] = condition
                else:
                    fail(f"invalid condition for {requirement_id}")
        expected_by_profile[profile_name] = (mandatory, conditional)

    profiles: dict[str, dict[str, Any]] = {}
    for path in sorted(PROFILE_ROOT.glob("*.yaml")):
        profile = load_yaml(path)
        metadata = profile.get("metadata")
        name = metadata.get("name") if isinstance(metadata, dict) else None
        if profile.get("apiVersion") != "avp.tck/v0.1" or profile.get("kind") != "ConformanceProfile":
            fail(f"invalid profile resource {path.relative_to(ROOT)}")
        if not isinstance(name, str) or path.stem != name or name in profiles:
            fail(f"invalid or duplicate profile identity in {path.relative_to(ROOT)}")
        if name not in expected_by_profile:
            fail(f"profile {name} has no requirement index")
        requirements_doc = profile.get("requirements")
        if not isinstance(requirements_doc, dict):
            fail(f"profile {name} requirements must be a mapping")
        mandatory = string_set(requirements_doc.get("mandatory"), f"{name} mandatory requirements")
        conditional_records = requirements_doc.get("conditional")
        if not isinstance(conditional_records, list):
            fail(f"{name} conditional requirements must be a list")
        conditional: dict[str, str] = {}
        for record in conditional_records:
            if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not isinstance(record.get("when"), str):
                fail(f"invalid conditional requirement in {name}")
            if record["id"] in conditional:
                fail(f"duplicate conditional requirement {record['id']} in {name}")
            conditional[record["id"]] = record["when"]
        expected_mandatory, expected_conditional = expected_by_profile[name]
        if mandatory != expected_mandatory or conditional != expected_conditional:
            fail(f"profile {name} requirements differ from requirement index")
        profiles[name] = profile

    missing_profiles = expected_by_profile.keys() - profiles.keys()
    if missing_profiles:
        fail(f"requirement indexes without profiles: {sorted(missing_profiles)}")

    registry = load_yaml(REGISTRY_PATH)
    if registry.get("apiVersion") != "avp.tck/v0.1" or registry.get("kind") != "TCKRegistry":
        fail("invalid registry resource identity")
    registry_cases = registry.get("cases")
    if not isinstance(registry_cases, list) or not registry_cases:
        fail("registry cases must be a non-empty list")

    entries: dict[str, dict[str, Any]] = {}
    coverage: dict[str, set[str]] = {name: set() for name in profiles}
    for entry in registry_cases:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            fail("invalid registry case entry")
        case_id = entry["id"]
        if case_id in entries:
            fail(f"duplicate registry case {case_id}")
        profile_name = entry.get("profile")
        if profile_name not in profiles:
            fail(f"{case_id} references unknown profile {profile_name!r}")
        path_value = entry.get("path")
        if not isinstance(path_value, str) or not path_value.startswith("conformance/tck/cases/"):
            fail(f"{case_id} has invalid path")
        path = ROOT / path_value
        if not path.is_file() or path.name != f"{case_id}.yaml":
            fail(f"{case_id} references missing or mismatched case file")
        entry_requirements = string_set(entry.get("requirements"), f"registry requirements for {case_id}")
        for requirement_id in entry_requirements:
            if requirement_profiles.get(requirement_id) != profile_name:
                fail(f"{case_id} maps requirement outside profile: {requirement_id}")
        applicability = entry.get("applicability")
        if applicability not in {"mandatory", "conditional", "mixed"}:
            fail(f"{case_id} has invalid applicability {applicability!r}")
        case = load_yaml(path)
        metadata = case.get("metadata")
        if case.get("apiVersion") != "avp.tck/v0.1" or case.get("kind") != "ConformanceCase":
            fail(f"{case_id} has invalid resource identity")
        if not isinstance(metadata, dict) or metadata.get("id") != case_id:
            fail(f"{case_id} metadata.id mismatch")
        if case.get("profile") != profile_name or case.get("applicability") != applicability:
            fail(f"{case_id} profile/applicability differs from registry")
        if string_set(case.get("requirements"), f"{case_id} requirements") != entry_requirements:
            fail(f"{case_id} requirement mapping differs from registry")
        if applicability == "conditional":
            when = entry.get("when")
            if not isinstance(when, str) or case.get("when") != when:
                fail(f"{case_id} conditional trigger mismatch")
        entries[case_id] = entry
        coverage[profile_name].update(entry_requirements)

    actual_paths = set(CASE_ROOT.rglob("*.yaml"))
    registered_paths = {ROOT / entry["path"] for entry in entries.values()}
    if actual_paths != registered_paths:
        fail("case file/registry mismatch (orphan or missing registered case)")

    for profile_name, (mandatory, conditional) in expected_by_profile.items():
        required = mandatory | conditional.keys()
        missing = required - coverage[profile_name]
        if missing:
            fail(f"profile {profile_name} requirements without TCK coverage: {sorted(missing)}")
        for requirement_id, condition in conditional.items():
            mapped = [entry for entry in entries.values() if requirement_id in entry["requirements"]]
            if not any(entry.get("applicability") in {"conditional", "mixed"} and entry.get("when") == condition for entry in mapped):
                # Mixed lifecycle cases can cover a conditional relation without owning the trigger;
                # at least one dedicated conditional case must still carry it.
                if not any(entry.get("applicability") == "conditional" and entry.get("when") == condition for entry in mapped):
                    fail(f"conditional requirement {requirement_id} lacks trigger {condition!r}")

    for requirement_id, record in requirements.items():
        declared = string_set(record.get("conformance"), f"{requirement_id} conformance", allow_empty=True)
        for case_id in declared:
            entry = entries.get(case_id)
            if entry is None or requirement_id not in entry["requirements"]:
                fail(f"broken bidirectional mapping {requirement_id} <-> {case_id}")

    for schema_path in sorted((TCK_ROOT / "schemas").glob("*.json")):
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            fail(f"invalid TCK schema {schema_path.relative_to(ROOT)}: {exc}")

    print(
        f"TCK registry OK: {len(entries)} cases, {len(profiles)} profiles, "
        f"{len(requirements)} indexed requirements"
    )


if __name__ == "__main__":
    main()

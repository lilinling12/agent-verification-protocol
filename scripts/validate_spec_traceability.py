"""Validate normative AVP requirement-to-TCK traceability across profiles."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATHS = tuple(sorted((ROOT / "spec").glob("**/requirement-index.yaml")))
CASE_ROOT = ROOT / "conformance/tck/cases"
REQUIREMENT_ID = re.compile(r"AVP-[A-Z][A-Z0-9-]*-\d{3}")
ALLOWED_LEVELS = {"MUST", "MUST_NOT", "SHOULD", "SHOULD_NOT", "MAY"}
MANDATORY_LEVELS = {"MUST", "MUST_NOT"}


def fail(message: str) -> None:
    raise SystemExit(f"spec traceability FAIL: {message}")


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"cannot parse {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must contain a YAML mapping")
    return value


def main() -> None:
    if not INDEX_PATHS:
        fail("no normative requirement indexes found")

    requirements: dict[str, dict[str, Any]] = {}
    requirement_profiles: dict[str, str] = {}
    for index_path in INDEX_PATHS:
        index = load_yaml(index_path)
        profile = index.get("profile")
        records = index.get("requirements")
        if not isinstance(profile, str) or not profile:
            fail(f"{index_path.relative_to(ROOT)} missing profile")
        if not isinstance(records, list) or not records:
            fail(f"{index_path.relative_to(ROOT)} must contain non-empty requirements")
        for record in records:
            if not isinstance(record, dict):
                fail(f"invalid requirement in {index_path.relative_to(ROOT)}")
            requirement_id = record.get("id")
            level = record.get("level")
            if not isinstance(requirement_id, str) or not REQUIREMENT_ID.fullmatch(requirement_id):
                fail(f"invalid requirement id: {requirement_id!r}")
            if requirement_id in requirements:
                fail(f"duplicate requirement id: {requirement_id}")
            if level not in ALLOWED_LEVELS:
                fail(f"invalid requirement level for {requirement_id}: {level!r}")
            for field in ("area", "statement", "spec", "anchor"):
                if not isinstance(record.get(field), str) or not record[field]:
                    fail(f"{requirement_id} missing non-empty {field}")
            spec_path = ROOT / record["spec"]
            if not spec_path.is_file():
                fail(f"{requirement_id} references missing spec {record['spec']}")
            if f"### {requirement_id} " not in spec_path.read_text(encoding="utf-8"):
                fail(f"{requirement_id} has no normative heading in {record['spec']}")
            if record["anchor"] != requirement_id.lower():
                fail(f"{requirement_id} anchor must be {requirement_id.lower()!r}")
            schema = record.get("schema")
            if schema is not None and (not isinstance(schema, str) or not (ROOT / schema).is_file()):
                fail(f"{requirement_id} references missing schema {schema!r}")
            conformance = record.get("conformance")
            if not isinstance(conformance, list) or not all(isinstance(item, str) and item for item in conformance):
                fail(f"{requirement_id} conformance must be a list of case IDs")
            if level in MANDATORY_LEVELS and not conformance:
                fail(f"mandatory requirement {requirement_id} must declare conformance cases")
            if not conformance:
                rationale = record.get("conformance_rationale")
                if not isinstance(rationale, str) or not rationale:
                    fail(f"{requirement_id} without TCK coverage requires conformance_rationale")
            requirements[requirement_id] = record
            requirement_profiles[requirement_id] = profile

    cases: dict[str, dict[str, Any]] = {}
    covered: set[str] = set()
    for path in sorted(CASE_ROOT.rglob("*.yaml")):
        case = load_yaml(path)
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, dict) else None
        mapped = case.get("requirements")
        profile = case.get("profile")
        if case.get("apiVersion") != "avp.tck/v0.1" or case.get("kind") != "ConformanceCase":
            fail(f"invalid TCK resource identity in {path.relative_to(ROOT)}")
        if not isinstance(case_id, str) or not case_id.startswith("AVP-TCK-"):
            fail(f"invalid TCK id in {path.relative_to(ROOT)}")
        if path.name != f"{case_id}.yaml" or case_id in cases:
            fail(f"duplicate or filename-mismatched TCK id: {case_id}")
        if not isinstance(profile, str) or not profile:
            fail(f"{case_id} missing profile")
        if not isinstance(mapped, list) or not mapped:
            fail(f"{case_id} must map at least one requirement")
        for requirement_id in mapped:
            if requirement_id not in requirements:
                fail(f"{case_id} references unknown requirement {requirement_id}")
            if requirement_profiles[requirement_id] != profile:
                fail(f"{case_id} crosses profile boundary for {requirement_id}")
            covered.add(requirement_id)
        cases[case_id] = case

    for requirement_id, record in requirements.items():
        for case_id in record["conformance"]:
            case = cases.get(case_id)
            if case is None:
                fail(f"{requirement_id} references missing TCK case {case_id}")
            if requirement_id not in case["requirements"]:
                fail(f"{case_id} does not map back to {requirement_id}")

    missing = sorted(
        requirement_id
        for requirement_id, record in requirements.items()
        if record["level"] in MANDATORY_LEVELS and requirement_id not in covered
    )
    if missing:
        fail(f"mandatory requirements without TCK coverage: {missing}")

    print(
        f"spec traceability OK: {len(requirements)} requirements, "
        f"{len(cases)} TCK cases, {len(INDEX_PATHS)} profiles"
    )


if __name__ == "__main__":
    main()

"""Validate AVP normative requirement-to-TCK traceability."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "spec/core/requirement-index.yaml"
TCK_DIR = ROOT / "conformance/tck/cases/lifecycle"
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
    index = load_yaml(INDEX)
    records = index.get("requirements")
    if not isinstance(records, list) or not records:
        fail("requirement index must contain a non-empty requirements list")

    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            fail("each requirement must be a mapping")
        requirement_id = record.get("id")
        level = record.get("level")
        if not isinstance(requirement_id, str) or not REQUIREMENT_ID.fullmatch(requirement_id):
            fail(f"invalid requirement id: {requirement_id!r}")
        if requirement_id in by_id:
            fail(f"duplicate requirement id: {requirement_id}")
        if level not in ALLOWED_LEVELS:
            fail(f"invalid requirement level for {requirement_id}: {level!r}")
        for field in ("area", "statement", "spec", "anchor"):
            if not isinstance(record.get(field), str) or not record[field]:
                fail(f"{requirement_id} missing non-empty {field}")
        spec_path = ROOT / record["spec"]
        if not spec_path.is_file():
            fail(f"{requirement_id} references missing spec {record['spec']}")
        spec_text = spec_path.read_text(encoding="utf-8")
        if f"### {requirement_id} " not in spec_text:
            fail(f"{requirement_id} has no normative heading in {record['spec']}")
        if record["anchor"] != requirement_id.lower():
            fail(f"{requirement_id} anchor must be {requirement_id.lower()!r}")
        schema = record.get("schema")
        if schema is not None and (not isinstance(schema, str) or not (ROOT / schema).is_file()):
            fail(f"{requirement_id} references missing schema {schema!r}")
        conformance = record.get("conformance")
        if not isinstance(conformance, list) or not conformance or not all(isinstance(item, str) for item in conformance):
            fail(f"{requirement_id} must declare one or more conformance case IDs")
        by_id[requirement_id] = record

    cases: dict[str, dict[str, Any]] = {}
    covered: set[str] = set()
    for path in sorted(TCK_DIR.glob("*.yaml")):
        case = load_yaml(path)
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, dict) else None
        requirements = case.get("requirements")
        if case.get("apiVersion") != "avp.tck/v0.1" or case.get("kind") != "ConformanceCase":
            fail(f"invalid TCK resource identity in {path.relative_to(ROOT)}")
        if not isinstance(case_id, str) or not case_id.startswith("AVP-TCK-"):
            fail(f"invalid TCK id in {path.relative_to(ROOT)}")
        if path.name != f"{case_id}.yaml":
            fail(f"TCK filename must match case id: {path.relative_to(ROOT)}")
        if case_id in cases:
            fail(f"duplicate TCK id: {case_id}")
        if not isinstance(requirements, list) or not requirements:
            fail(f"{case_id} must map at least one requirement")
        for requirement_id in requirements:
            if requirement_id not in by_id:
                fail(f"{case_id} references unknown requirement {requirement_id}")
            covered.add(requirement_id)
        cases[case_id] = case

    for requirement_id, record in by_id.items():
        for case_id in record["conformance"]:
            case = cases.get(case_id)
            if case is None:
                fail(f"{requirement_id} references missing TCK case {case_id}")
            if requirement_id not in case["requirements"]:
                fail(f"{case_id} does not map back to {requirement_id}")

    missing = sorted(
        requirement_id
        for requirement_id, record in by_id.items()
        if record["level"] in MANDATORY_LEVELS and requirement_id not in covered
    )
    if missing:
        fail(f"mandatory requirements without TCK coverage: {missing}")

    print(f"spec traceability OK: {len(by_id)} requirements, {len(cases)} lifecycle TCK cases")


if __name__ == "__main__":
    main()

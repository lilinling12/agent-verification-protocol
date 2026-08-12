"""Validate AVP normative requirement and conformance traceability."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "spec/core/requirement-index.yaml"
SPEC = ROOT / "spec/core/episode-lifecycle.md"
TCK_DIR = ROOT / "conformance/lifecycle"
REQUIREMENT = re.compile(r"\bAVP-[A-Z][A-Z0-9-]*-\d{3}\b")


def fail(message: str) -> None:
    raise SystemExit(f"spec traceability FAIL: {message}")


def load_yaml(path: Path) -> dict:
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

    ids = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            fail("each requirement record must contain a string id")
        requirement_id = record["id"]
        if not REQUIREMENT.fullmatch(requirement_id):
            fail(f"invalid requirement id: {requirement_id}")
        ids.append(requirement_id)
    if len(ids) != len(set(ids)):
        fail("requirement IDs must be unique")

    spec_text = SPEC.read_text(encoding="utf-8")
    spec_ids = set(REQUIREMENT.findall(spec_text))
    indexed = set(ids)
    if spec_ids != indexed:
        fail(f"spec/index requirement mismatch; spec-only={sorted(spec_ids-indexed)}, index-only={sorted(indexed-spec_ids)}")

    covered: set[str] = set()
    case_ids: set[str] = set()
    for path in sorted(TCK_DIR.glob("*.yaml")):
        case = load_yaml(path)
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.startswith("AVP-TCK-"):
            fail(f"invalid TCK case id in {path.relative_to(ROOT)}")
        if case_id in case_ids:
            fail(f"duplicate TCK case id: {case_id}")
        case_ids.add(case_id)
        requirements = case.get("requirements")
        if not isinstance(requirements, list) or not requirements:
            fail(f"{case_id} must map at least one requirement")
        for requirement_id in requirements:
            if requirement_id not in indexed:
                fail(f"{case_id} references unknown requirement {requirement_id}")
            covered.add(requirement_id)

    required_for_tck = {r["id"] for r in records if r.get("level") in {"MUST", "MUST_NOT"}}
    missing = sorted(required_for_tck - covered)
    if missing:
        fail(f"mandatory requirements without TCK mapping: {missing}")

    print(f"spec traceability OK: {len(indexed)} requirements, {len(case_ids)} TCK cases")


if __name__ == "__main__":
    main()

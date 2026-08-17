"""Fail-closed validation for the Alpha 2 normative-surface closure audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "docs/reconciliation/v0.1/normative-surface-matrix.json"
SPEC_ROOT = ROOT / "spec"
SCHEMA_ROOT = ROOT / "schemas"
PROFILE_ROOT = ROOT / "conformance/tck/profiles"
ALLOWED_CLASSIFICATIONS = {
    "REQUIREMENT_OWNED",
    "UNOWNED_REQUIRES_GOVERNANCE",
    "ORPHAN_REQUIRES_GOVERNANCE",
    "ALIAS_REQUIRES_DISPOSITION",
}
ALLOWED_REQUIREMENT_INDEX_STATUSES = {
    "draft-normative-candidate",
    "normative",
}


def fail(message: str) -> None:
    raise SystemExit(f"normative surface FAIL: {message}")


def confined_file(value: Any, context: str) -> Path:
    if not isinstance(value, str) or not value or value.startswith("/"):
        fail(f"{context} must be a non-empty repository-relative path")
    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError:
        fail(f"{context} escapes repository root: {value!r}")
    if not path.is_file():
        fail(f"{context} references missing file: {value}")
    return path


def string_list(value: Any, context: str, *, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        fail(f"{context} must be a {'non-empty ' if nonempty else ''}list")
    if not all(isinstance(item, str) and item for item in value):
        fail(f"{context} must contain non-empty strings")
    if len(value) != len(set(value)):
        fail(f"{context} contains duplicates")
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"cannot parse {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must contain a mapping")
    return value


def main() -> None:
    try:
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse matrix: {exc}")
    if not isinstance(matrix, dict):
        fail("matrix root must be an object")
    if matrix.get("matrix_version") != "1.0":
        fail("matrix_version must be 1.0")
    if matrix.get("status") not in {"audit-candidate", "accepted"}:
        fail("invalid matrix status")
    if matrix.get("authority") != "non-normative-acceptance-evidence":
        fail("matrix must not claim normative authority")
    closure = matrix.get("closure_status")
    if closure not in {"BLOCKED", "READY"}:
        fail("closure_status must be BLOCKED or READY")

    blockers = matrix.get("blockers")
    if not isinstance(blockers, list):
        fail("blockers must be a list")
    blocker_ids: set[str] = set()
    for blocker in blockers:
        if not isinstance(blocker, dict):
            fail("each blocker must be an object")
        blocker_id = blocker.get("id")
        if not isinstance(blocker_id, str) or not blocker_id.startswith("NSC-") or blocker_id in blocker_ids:
            fail(f"invalid or duplicate blocker id: {blocker_id!r}")
        if blocker.get("decision_required") is not True:
            fail(f"{blocker_id} must explicitly require a decision")
        for field in ("surface", "category", "rationale"):
            if not isinstance(blocker.get(field), str) or not blocker[field]:
                fail(f"{blocker_id} missing {field}")
        blocker_ids.add(blocker_id)
    if blockers and closure != "BLOCKED":
        fail("READY is forbidden while blockers remain")
    if not blockers and closure != "READY":
        fail("zero blockers requires READY")

    expected_domains = {path.parent.name for path in SPEC_ROOT.glob("*/requirement-index.yaml")}
    domains = matrix.get("domains")
    if not isinstance(domains, list) or not domains:
        fail("domains must be a non-empty list")
    seen_domains: set[str] = set()
    seen_profiles: set[str] = set()
    schema_owners: dict[str, set[str]] = {}
    draft_status_seen = False
    for record in domains:
        if not isinstance(record, dict):
            fail("domain entry must be an object")
        domain = record.get("domain")
        if not isinstance(domain, str) or domain in seen_domains:
            fail(f"invalid or duplicate domain: {domain!r}")
        index_path = confined_file(record.get("requirement_index"), f"{domain}.requirement_index")
        if index_path != (SPEC_ROOT / domain / "requirement-index.yaml").resolve():
            fail(f"{domain} requirement index path is not canonical")
        index = load_yaml(index_path)
        index_status = index.get("status")
        if index_status not in ALLOWED_REQUIREMENT_INDEX_STATUSES:
            fail(f"{domain} has invalid requirement-index status {index_status!r}")
        if index_status == "draft-normative-candidate":
            draft_status_seen = True
        profile = record.get("profile")
        if not isinstance(profile, str) or index.get("profile") != profile:
            fail(f"{domain} profile differs from requirement index")
        if profile in seen_profiles or not (PROFILE_ROOT / f"{profile}.yaml").is_file():
            fail(f"{domain} references invalid or duplicate profile {profile!r}")
        seen_profiles.add(profile)
        specs = string_list(record.get("spec"), f"{domain}.spec")
        for spec in specs:
            confined_file(spec, f"{domain}.spec")
        lineage = record.get("lineage")
        if not isinstance(lineage, dict) or lineage.get("type") not in {"final-aep", "reconciliation"}:
            fail(f"{domain} has invalid lineage")
        lineage_path = confined_file(lineage.get("path"), f"{domain}.lineage.path")
        if lineage.get("type") == "final-aep" and "- Status: Final" not in lineage_path.read_text(encoding="utf-8"):
            fail(f"{domain} declares a Final AEP that is not Final")
        requirements = index.get("requirements")
        if not isinstance(requirements, list) or not requirements:
            fail(f"{domain} has empty requirement index")
        for requirement in requirements:
            if not isinstance(requirement, dict):
                fail(f"{domain} has invalid requirement record")
            schema = requirement.get("schema")
            if isinstance(schema, str):
                confined_file(schema, f"{domain} schema")
                schema_owners.setdefault(schema, set()).add(domain)
        seen_domains.add(domain)
    if seen_domains != expected_domains:
        fail(f"domain coverage mismatch: expected {sorted(expected_domains)}, got {sorted(seen_domains)}")
    actual_profiles = {path.stem for path in PROFILE_ROOT.glob("*.yaml")}
    if seen_profiles != actual_profiles:
        fail("matrix profile coverage differs from TCK profile inventory")
    if draft_status_seen and "NSC-005" not in blocker_ids:
        fail("draft requirement-index authority metadata requires NSC-005")
    if not draft_status_seen and "NSC-005" in blocker_ids:
        fail("NSC-005 is stale after all requirement indexes become normative")

    schema_entries = matrix.get("schemas")
    if not isinstance(schema_entries, list) or not schema_entries:
        fail("schemas must be a non-empty list")
    expected_schemas = {str(path.relative_to(ROOT)).replace("\\", "/") for path in SCHEMA_ROOT.glob("*.schema.json")}
    seen_schemas: set[str] = set()
    referenced_blockers: set[str] = set()
    for entry in schema_entries:
        if not isinstance(entry, dict):
            fail("schema entry must be an object")
        path_value = entry.get("path")
        path = confined_file(path_value, "schema.path")
        if not isinstance(path_value, str) or path_value in seen_schemas:
            fail(f"invalid or duplicate schema entry {path_value!r}")
        classification = entry.get("classification")
        if classification not in ALLOWED_CLASSIFICATIONS:
            fail(f"invalid schema classification for {path_value}")
        if classification == "REQUIREMENT_OWNED":
            owners = set(string_list(entry.get("owner_domains"), f"{path_value}.owner_domains"))
            if owners != schema_owners.get(path_value, set()):
                fail(f"{path_value} owner domains differ from requirement indexes")
        else:
            ids = set(string_list(entry.get("blocker_ids"), f"{path_value}.blocker_ids"))
            if not ids <= blocker_ids:
                fail(f"{path_value} references unknown blockers")
            referenced_blockers.update(ids)
            if path_value in schema_owners:
                fail(f"{path_value} is classified unresolved but has requirement ownership")
        if classification == "ALIAS_REQUIRES_DISPOSITION":
            target_value = entry.get("identical_to")
            target = confined_file(target_value, f"{path_value}.identical_to")
            if path.read_bytes() != target.read_bytes():
                fail(f"{path_value} declared alias bytes differ from {target_value}")
        seen_schemas.add(path_value)
    if seen_schemas != expected_schemas:
        fail("matrix schema coverage differs from root schema inventory")

    schema_blocker_ids = {item for item in blocker_ids if item in {"NSC-001", "NSC-002", "NSC-003", "NSC-004"}}
    if referenced_blockers != schema_blocker_ids:
        fail("schema blocker references are incomplete")

    print(
        f"normative surface audit OK: {len(seen_domains)} domains, "
        f"{len(seen_profiles)} profiles, {len(seen_schemas)} schemas, "
        f"closure={closure}, blockers={len(blockers)}"
    )


if __name__ == "__main__":
    main()

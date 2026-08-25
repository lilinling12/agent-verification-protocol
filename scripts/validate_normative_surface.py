"""Fail-closed validation for stable and active AVP normative surfaces.

The Alpha 2 normative-surface matrix remains the closed stable baseline. Future
protocol work is represented separately as complete, Accepted-AEP candidate
slices so an unfinished surface can never make the stable closure appear READY.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "docs/reconciliation/v0.1/normative-surface-matrix.json"
CANDIDATE_REGISTRY_PATH = ROOT / "docs/reconciliation/normative-candidates/registry.json"
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


def load_json(path: Path, context: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {context}: {exc}")
    if not isinstance(value, dict):
        fail(f"{context} root must be an object")
    return value


def candidate_inventory() -> tuple[list[dict[str, Any]], set[str], set[str], set[str]]:
    registry = load_json(CANDIDATE_REGISTRY_PATH, "normative candidate registry")
    if registry.get("registry_version") != "1.0":
        fail("candidate registry_version must be 1.0")
    if registry.get("authority") != "non-normative-governance-evidence":
        fail("candidate registry must not claim normative authority")
    records = registry.get("candidates")
    if not isinstance(records, list):
        fail("candidate registry candidates must be a list")

    domains: set[str] = set()
    profiles: set[str] = set()
    schemas: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            fail("candidate entry must be an object")
        domain = record.get("domain")
        profile = record.get("profile")
        if not isinstance(domain, str) or not domain or domain in domains:
            fail(f"invalid or duplicate candidate domain: {domain!r}")
        if not isinstance(profile, str) or not profile or profile in profiles:
            fail(f"invalid or duplicate candidate profile: {profile!r}")
        owned_schemas = set(string_list(record.get("owned_schemas"), f"candidate {domain}.owned_schemas", nonempty=False))
        duplicate_schemas = schemas & owned_schemas
        if duplicate_schemas:
            fail(f"candidate schemas have duplicate ownership: {sorted(duplicate_schemas)}")
        for schema in owned_schemas:
            if not schema.startswith("schemas/") or Path(schema).parent.as_posix() != "schemas" or not schema.endswith(".schema.json"):
                fail(f"candidate {domain} has non-canonical owned schema {schema!r}")
        domains.add(domain)
        profiles.add(profile)
        schemas.update(owned_schemas)
        normalized.append(record)
    return normalized, domains, profiles, schemas


def validate_candidate(
    record: dict[str, Any],
    *,
    stable_domains: set[str],
    stable_profiles: set[str],
    stable_schemas: set[str],
    all_candidate_domains: set[str],
    all_candidate_profiles: set[str],
    all_candidate_schemas: set[str],
) -> None:
    domain = record["domain"]
    profile = record["profile"]
    owned_schemas = set(string_list(record.get("owned_schemas"), f"candidate {domain}.owned_schemas", nonempty=False))

    if domain in stable_domains:
        fail(f"candidate domain overlaps stable domain: {domain}")
    if profile in stable_profiles:
        fail(f"candidate profile overlaps stable profile: {profile}")
    if owned_schemas & stable_schemas:
        fail(f"candidate {domain} claims stable schema ownership")

    lineage = record.get("lineage")
    if not isinstance(lineage, dict) or lineage.get("type") != "accepted-aep":
        fail(f"candidate {domain} lineage must be accepted-aep")
    lineage_path = confined_file(lineage.get("path"), f"candidate {domain}.lineage.path")
    lineage_text = lineage_path.read_text(encoding="utf-8")
    if "- Status: Accepted" not in lineage_text:
        fail(f"candidate {domain} Accepted AEP lineage is not Accepted")
    if "- Status: Final" in lineage_text:
        fail(f"candidate {domain} is Final and must be promoted out of the candidate registry")

    index_path = confined_file(record.get("requirement_index"), f"candidate {domain}.requirement_index")
    canonical_index = (SPEC_ROOT / domain / "requirement-index.yaml").resolve()
    if index_path != canonical_index:
        fail(f"candidate {domain} requirement index path is not canonical")
    index = load_yaml(index_path)
    if index.get("status") != "draft-normative-candidate":
        fail(f"candidate {domain} requirement-index status must be draft-normative-candidate")
    if index.get("profile") != profile:
        fail(f"candidate {domain} profile differs from requirement index")
    requirements = index.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        fail(f"candidate {domain} has empty requirement index")

    specs = string_list(record.get("spec"), f"candidate {domain}.spec")
    domain_root = (SPEC_ROOT / domain).resolve()
    for spec in specs:
        path = confined_file(spec, f"candidate {domain}.spec")
        try:
            path.relative_to(domain_root)
        except ValueError:
            fail(f"candidate {domain} spec is outside canonical domain: {spec}")
        if path == index_path:
            fail(f"candidate {domain} spec list must not contain requirement-index.yaml")

    profile_path = (PROFILE_ROOT / f"{profile}.yaml").resolve()
    if not profile_path.is_file():
        fail(f"candidate {domain} references missing TCK profile {profile!r}")
    profile_doc = load_yaml(profile_path)
    metadata = profile_doc.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("name") != profile:
        fail(f"candidate {domain} TCK profile identity mismatch")
    if metadata.get("status") != "draft":
        fail(f"candidate {domain} TCK profile status must be draft")

    referenced_schemas: set[str] = set()
    for requirement in requirements:
        if not isinstance(requirement, dict):
            fail(f"candidate {domain} has invalid requirement record")
        schema = requirement.get("schema")
        if schema is None:
            continue
        if not isinstance(schema, str):
            fail(f"candidate {domain} has non-string schema reference")
        confined_file(schema, f"candidate {domain} schema")
        referenced_schemas.add(schema)

    foreign_candidate_schemas = referenced_schemas & (all_candidate_schemas - owned_schemas)
    if foreign_candidate_schemas:
        fail(
            f"candidate {domain} references schema owned by another candidate: "
            f"{sorted(foreign_candidate_schemas)}"
        )
    unknown_schema_refs = referenced_schemas - stable_schemas - owned_schemas
    if unknown_schema_refs:
        fail(f"candidate {domain} references unowned schemas: {sorted(unknown_schema_refs)}")
    unreferenced_owned = owned_schemas - referenced_schemas
    if unreferenced_owned:
        fail(f"candidate {domain} owns schemas without requirement ownership: {sorted(unreferenced_owned)}")
    for schema in owned_schemas:
        confined_file(schema, f"candidate {domain}.owned_schema")

    # Defensive consistency checks make accidental record mutation fail locally.
    if domain not in all_candidate_domains or profile not in all_candidate_profiles:
        fail(f"candidate {domain} is absent from normalized candidate inventory")


def main() -> None:
    candidates, candidate_domains, candidate_profiles, candidate_schemas = candidate_inventory()

    matrix = load_json(MATRIX_PATH, "stable normative surface matrix")
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

    all_domains = {path.parent.name for path in SPEC_ROOT.glob("*/requirement-index.yaml")}
    expected_stable_domains = all_domains - candidate_domains
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
        if domain in candidate_domains:
            fail(f"stable matrix contains active candidate domain {domain}")
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
        if profile in candidate_profiles:
            fail(f"stable matrix contains active candidate profile {profile}")
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
    if seen_domains != expected_stable_domains:
        fail(
            f"stable domain coverage mismatch: expected {sorted(expected_stable_domains)}, "
            f"got {sorted(seen_domains)}"
        )

    actual_profiles = {path.stem for path in PROFILE_ROOT.glob("*.yaml")}
    expected_stable_profiles = actual_profiles - candidate_profiles
    if seen_profiles != expected_stable_profiles:
        fail("stable matrix profile coverage differs from non-candidate TCK profile inventory")
    if draft_status_seen and "NSC-005" not in blocker_ids:
        fail("draft stable requirement-index authority metadata requires NSC-005")
    if not draft_status_seen and "NSC-005" in blocker_ids:
        fail("NSC-005 is stale after all stable requirement indexes become normative")

    schema_entries = matrix.get("schemas")
    if not isinstance(schema_entries, list) or not schema_entries:
        fail("schemas must be a non-empty list")
    actual_schemas = {
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in SCHEMA_ROOT.glob("*.schema.json")
    }
    expected_stable_schemas = actual_schemas - candidate_schemas
    seen_schemas: set[str] = set()
    referenced_blockers: set[str] = set()
    for entry in schema_entries:
        if not isinstance(entry, dict):
            fail("schema entry must be an object")
        path_value = entry.get("path")
        path = confined_file(path_value, "schema.path")
        if not isinstance(path_value, str) or path_value in seen_schemas:
            fail(f"invalid or duplicate schema entry {path_value!r}")
        if path_value in candidate_schemas:
            fail(f"stable matrix contains active candidate schema {path_value}")
        classification = entry.get("classification")
        if classification not in ALLOWED_CLASSIFICATIONS:
            fail(f"invalid schema classification for {path_value}")
        if classification == "REQUIREMENT_OWNED":
            owners = set(string_list(entry.get("owner_domains"), f"{path_value}.owner_domains"))
            if owners != schema_owners.get(path_value, set()):
                fail(f"{path_value} owner domains differ from stable requirement indexes")
        else:
            ids = set(string_list(entry.get("blocker_ids"), f"{path_value}.blocker_ids"))
            if not ids <= blocker_ids:
                fail(f"{path_value} references unknown blockers")
            referenced_blockers.update(ids)
            if path_value in schema_owners:
                fail(f"{path_value} is classified unresolved but has stable requirement ownership")
        if classification == "ALIAS_REQUIRES_DISPOSITION":
            target_value = entry.get("identical_to")
            target = confined_file(target_value, f"{path_value}.identical_to")
            if path.read_bytes() != target.read_bytes():
                fail(f"{path_value} declared alias bytes differ from {target_value}")
        seen_schemas.add(path_value)
    if seen_schemas != expected_stable_schemas:
        fail("stable matrix schema coverage differs from non-candidate root schema inventory")

    schema_blocker_ids = {item for item in blocker_ids if item in {"NSC-001", "NSC-002", "NSC-003", "NSC-004"}}
    if referenced_blockers != schema_blocker_ids:
        fail("schema blocker references are incomplete")

    for candidate in candidates:
        validate_candidate(
            candidate,
            stable_domains=seen_domains,
            stable_profiles=seen_profiles,
            stable_schemas=seen_schemas,
            all_candidate_domains=candidate_domains,
            all_candidate_profiles=candidate_profiles,
            all_candidate_schemas=candidate_schemas,
        )

    # The subtraction-based stable checks plus candidate file validation make the
    # union exact. These explicit checks document the invariant and catch future
    # refactors that accidentally stop accounting for one inventory class.
    if seen_domains | candidate_domains != all_domains:
        fail("stable + candidate domains do not cover repository requirement-index inventory")
    if seen_profiles | candidate_profiles != actual_profiles:
        fail("stable + candidate profiles do not cover repository TCK profile inventory")
    if seen_schemas | candidate_schemas != actual_schemas:
        fail("stable + candidate schemas do not cover repository root schema inventory")

    print(
        f"normative surface audit OK: stable_domains={len(seen_domains)}, "
        f"stable_profiles={len(seen_profiles)}, stable_schemas={len(seen_schemas)}, "
        f"candidates={len(candidates)}, closure={closure}, blockers={len(blockers)}"
    )


if __name__ == "__main__":
    main()

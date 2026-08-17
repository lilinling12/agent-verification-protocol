#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "docs/reconciliation/v0.1/historical-disposition-ledger.json"
MANIFEST_PATH = ROOT / "docs/design/alpha-v0.1/SOURCE-MANIFEST.json"

EXPECTED_STATUS = "closure-candidate"
EXPECTED_AUTHORITY = "non-normative-reconciliation-evidence"
ALLOWED_DISPOSITIONS = {
    "PROMOTED",
    "SPLIT",
    "SUPERSEDED",
    "NON_NORMATIVE",
    "DEFERRED",
    "REJECTED",
}
EXPECTED_HISTORICAL_PROFILES = {
    "Core",
    "Environment",
    "Snapshot",
    "Verification",
    "Replay",
    "Chaos",
    "Telemetry",
}
ALLOWED_EVIDENCE_KEYS = {
    "aep",
    "normative_spec",
    "requirements",
    "schemas",
    "tck_profiles",
    "conformance",
    "governance",
    "runtime",
}
REQ_ID_RE = re.compile(r"^\s*-\s+id:\s+([A-Z0-9-]+)\s*$", re.MULTILINE)
REQ_RANGE_RE = re.compile(r"^(AVP-[A-Z0-9-]+-)(\d{3})\.\.(\d{3})$")


class ValidationError(Exception):
    """Raised when the historical disposition ledger violates closure invariants."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def _require_string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{where} must be a non-empty string")
    return value


def _manifest_targets(manifest: dict[str, Any]) -> set[str]:
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValidationError("historical source manifest must contain a non-empty files list")
    targets: set[str] = set()
    for index, entry in enumerate(files):
        if not isinstance(entry, dict):
            raise ValidationError(f"manifest files[{index}] must be an object")
        target = _require_string(entry.get("target_path"), f"manifest files[{index}].target_path")
        if target in targets:
            raise ValidationError(f"duplicate target_path in source manifest: {target}")
        targets.add(target)
    return targets


def _require_repo_path(path_text: str, where: str) -> None:
    path = Path(path_text)
    if path.is_absolute() or ".." in path.parts:
        raise ValidationError(f"{where} must be a repository-relative confined path: {path_text}")
    resolved = ROOT / path
    if not resolved.exists():
        raise ValidationError(f"{where} references missing repository path: {path_text}")


def _known_requirements() -> set[str]:
    result: set[str] = set()
    for index in (ROOT / "spec").glob("*/requirement-index.yaml"):
        result.update(REQ_ID_RE.findall(index.read_text(encoding="utf-8")))
    return result


def _expand_requirement_ref(ref: str) -> list[str]:
    match = REQ_RANGE_RE.fullmatch(ref)
    if match is None:
        return [ref]
    prefix, start_text, end_text = match.groups()
    start, end = int(start_text), int(end_text)
    if end < start:
        raise ValidationError(f"descending requirement range is forbidden: {ref}")
    return [f"{prefix}{number:03d}" for number in range(start, end + 1)]


def _validate_evidence(evidence: Any, where: str, known_requirements: set[str]) -> None:
    if not isinstance(evidence, dict):
        raise ValidationError(f"{where}.evidence must be an object")
    unknown_keys = set(evidence) - ALLOWED_EVIDENCE_KEYS
    if unknown_keys:
        raise ValidationError(f"{where}.evidence contains unsupported keys: {sorted(unknown_keys)}")

    for key, values in evidence.items():
        if not isinstance(values, list) or any(not isinstance(item, str) or not item for item in values):
            raise ValidationError(f"{where}.evidence.{key} must be a list of non-empty strings")
        if len(values) != len(set(values)):
            raise ValidationError(f"{where}.evidence.{key} contains duplicates")

        if key in {"aep", "normative_spec", "schemas", "conformance", "governance", "runtime"}:
            for item in values:
                _require_repo_path(item, f"{where}.evidence.{key}")
        elif key == "tck_profiles":
            for profile in values:
                _require_repo_path(
                    f"conformance/tck/profiles/{profile}.yaml",
                    f"{where}.evidence.tck_profiles",
                )
        elif key == "requirements":
            for ref in values:
                for requirement_id in _expand_requirement_ref(ref):
                    if requirement_id not in known_requirements:
                        raise ValidationError(
                            f"{where}.evidence.requirements references unknown requirement: "
                            f"{requirement_id} (from {ref})"
                        )


def validate() -> None:
    manifest = _load_json(MANIFEST_PATH)
    ledger = _load_json(LEDGER_PATH)

    if ledger.get("version") != "1.0":
        raise ValidationError("ledger version must be 1.0")
    if ledger.get("status") != EXPECTED_STATUS:
        raise ValidationError(f"ledger status must be {EXPECTED_STATUS}")
    if ledger.get("authority") != EXPECTED_AUTHORITY:
        raise ValidationError(f"ledger authority must be {EXPECTED_AUTHORITY}")

    declared_allowed = ledger.get("allowed_dispositions")
    if not isinstance(declared_allowed, list) or set(declared_allowed) != ALLOWED_DISPOSITIONS:
        raise ValidationError("ledger allowed_dispositions must exactly match the governed vocabulary")

    baseline = ledger.get("baseline")
    if not isinstance(baseline, dict):
        raise ValidationError("ledger baseline must be an object")
    if baseline.get("historical") != manifest.get("baseline_id"):
        raise ValidationError("ledger historical baseline id must match SOURCE-MANIFEST.json")
    if baseline.get("source_manifest") != "docs/design/alpha-v0.1/SOURCE-MANIFEST.json":
        raise ValidationError("ledger source_manifest must identify the immutable source manifest")
    _require_string(baseline.get("reconciled_against"), "ledger baseline.reconciled_against")

    documents = ledger.get("documents")
    if not isinstance(documents, list):
        raise ValidationError("ledger documents must be a list")

    expected_targets = _manifest_targets(manifest)
    seen_sources: set[str] = set()
    seen_ids: set[str] = set()
    known_requirements = _known_requirements()

    for index, document in enumerate(documents):
        where = f"documents[{index}]"
        if not isinstance(document, dict):
            raise ValidationError(f"{where} must be an object")
        doc_id = _require_string(document.get("id"), f"{where}.id")
        source = _require_string(document.get("source"), f"{where}.source")
        disposition = _require_string(document.get("disposition"), f"{where}.disposition")
        _require_string(document.get("rationale"), f"{where}.rationale")

        if doc_id in seen_ids:
            raise ValidationError(f"duplicate ledger document id: {doc_id}")
        if source in seen_sources:
            raise ValidationError(f"duplicate ledger historical source: {source}")
        if disposition not in ALLOWED_DISPOSITIONS:
            raise ValidationError(f"{where}.disposition is unsupported: {disposition}")
        if source not in expected_targets:
            raise ValidationError(f"{where}.source is not declared by SOURCE-MANIFEST.json: {source}")
        _require_repo_path(source, f"{where}.source")
        seen_ids.add(doc_id)
        seen_sources.add(source)

        areas = document.get("material_areas")
        if not isinstance(areas, list) or not areas:
            raise ValidationError(f"{where}.material_areas must be a non-empty list")
        if disposition == "SPLIT" and len(areas) < 2:
            raise ValidationError(f"{where} is SPLIT but does not contain multiple material areas")

        for area_index, material_area in enumerate(areas):
            area_where = f"{where}.material_areas[{area_index}]"
            if not isinstance(material_area, dict):
                raise ValidationError(f"{area_where} must be an object")
            _require_string(material_area.get("area"), f"{area_where}.area")
            area_disposition = _require_string(
                material_area.get("disposition"), f"{area_where}.disposition"
            )
            if area_disposition not in ALLOWED_DISPOSITIONS:
                raise ValidationError(
                    f"{area_where}.disposition is unsupported: {area_disposition}"
                )
            _validate_evidence(material_area.get("evidence"), area_where, known_requirements)
            if area_disposition == "PROMOTED":
                evidence = material_area["evidence"]
                for required_key in ("normative_spec", "requirements", "tck_profiles"):
                    if not evidence.get(required_key):
                        raise ValidationError(
                            f"{area_where} is PROMOTED but lacks {required_key} evidence"
                        )

    if seen_sources != expected_targets:
        missing = sorted(expected_targets - seen_sources)
        extra = sorted(seen_sources - expected_targets)
        raise ValidationError(
            f"ledger historical-source coverage mismatch; missing={missing}, extra={extra}"
        )

    mappings = ledger.get("historical_profile_mapping")
    if not isinstance(mappings, list):
        raise ValidationError("historical_profile_mapping must be a list")
    seen_profiles: set[str] = set()
    for index, mapping in enumerate(mappings):
        where = f"historical_profile_mapping[{index}]"
        if not isinstance(mapping, dict):
            raise ValidationError(f"{where} must be an object")
        name = _require_string(mapping.get("historical_profile"), f"{where}.historical_profile")
        disposition = _require_string(mapping.get("disposition"), f"{where}.disposition")
        _require_string(mapping.get("rationale"), f"{where}.rationale")
        if name in seen_profiles:
            raise ValidationError(f"duplicate historical profile mapping: {name}")
        if disposition not in ALLOWED_DISPOSITIONS:
            raise ValidationError(f"{where}.disposition is unsupported: {disposition}")
        current = mapping.get("current")
        if not isinstance(current, list) or not current:
            raise ValidationError(f"{where}.current must be a non-empty profile list")
        for profile in current:
            _require_string(profile, f"{where}.current")
            _require_repo_path(
                f"conformance/tck/profiles/{profile}.yaml",
                f"{where}.current",
            )
        seen_profiles.add(name)

    if seen_profiles != EXPECTED_HISTORICAL_PROFILES:
        raise ValidationError(
            "historical profile mapping must cover exactly "
            f"{sorted(EXPECTED_HISTORICAL_PROFILES)}"
        )

    _require_string(ledger.get("closure_statement"), "ledger closure_statement")


def main() -> int:
    try:
        validate()
    except ValidationError as exc:
        print(f"historical disposition ledger validation failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # fail closed on malformed/unexpected repository state
        print(
            f"historical disposition ledger validation failed unexpectedly: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2

    print("historical disposition ledger validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""Validate AVP monorepo authority and repository-boundary declarations."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "repository-boundaries.json"
REQUIRED_SURFACES = {
    "spec": "spec/README.md",
    "schemas": "schemas/README.md",
    "conformance": "conformance/README.md",
    "runtime": "runtime/README.md",
    "adapters": "adapters/README.md",
    "benchmarks": "benchmarks/README.md",
    "tests": "tests",
}
NORMATIVE = {"spec", "schemas"}
AUTHORITY_ORDER = ["spec", "schemas", "conformance", "reference-implementation"]
REQUIRED_POLICY_DOCUMENTS = {
    "governance": "GOVERNANCE.md",
    "architecture_boundaries": "docs/ARCHITECTURE_BOUNDARIES.md",
    "open_source_engineering": "docs/OPEN_SOURCE_ENGINEERING_STANDARD.md",
    "security": "SECURITY.md",
    "repository_settings": "docs/REPOSITORY_SETTINGS.md",
    "release_process": "docs/RELEASE_PROCESS.md",
}
REQUIRED_OPEN_SOURCE_INVARIANTS = {
    "independent_conformance_requires_public_semantics": True,
    "private_platform_must_not_define_conformance": True,
    "private_data_must_not_be_required_for_portable_tck": True,
    "reference_implementation_is_non_normative": True,
}
REQUIRED_EXCLUDED_SURFACES = {
    "commercial_platform",
    "production_sensitive_material",
    "private_evaluation_assets",
}


def fail(message: str) -> None:
    raise SystemExit(f"repository boundary FAIL: {message}")


def _require_file(relative: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.stat().st_size == 0:
        fail(f"required repository policy file missing or empty: {relative}")


def main() -> None:
    try:
        document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {MANIFEST.name}: {exc}")

    if document.get("schema_version") != "1.1":
        fail("repository-boundaries schema_version must be 1.1")

    if document.get("repository_phase") != "alpha-monorepo":
        fail("repository_phase must explicitly declare alpha-monorepo")

    policy_documents = document.get("policy_documents")
    if policy_documents != REQUIRED_POLICY_DOCUMENTS:
        fail(
            "policy_documents changed without an explicit boundary-policy update: "
            f"expected {REQUIRED_POLICY_DOCUMENTS}, got {policy_documents}"
        )
    for relative in REQUIRED_POLICY_DOCUMENTS.values():
        _require_file(relative)

    invariants = document.get("open_source_invariants")
    if invariants != REQUIRED_OPEN_SOURCE_INVARIANTS:
        fail(
            "open_source_invariants must preserve public independent conformance and "
            "non-normative private/reference implementation boundaries"
        )

    surfaces = document.get("surfaces")
    if not isinstance(surfaces, dict):
        fail("surfaces must be an object")
    if set(surfaces) != set(REQUIRED_SURFACES):
        fail(f"surface set mismatch: expected {sorted(REQUIRED_SURFACES)}, got {sorted(surfaces)}")

    for name, required_path in REQUIRED_SURFACES.items():
        entry = surfaces[name]
        if not isinstance(entry, dict):
            fail(f"surface {name!r} must be an object")
        if entry.get("path") != name:
            fail(f"surface {name!r} must own top-level path {name!r}")
        if not (ROOT / required_path).exists():
            fail(f"required boundary path missing: {required_path}")
        if bool(entry.get("normative")) != (name in NORMATIVE):
            fail(f"normative flag is incorrect for {name!r}")

    if document.get("authority_order") != AUTHORITY_ORDER:
        fail("authority_order changed without an explicit boundary-policy update")

    for surface in NORMATIVE:
        python_files = sorted((ROOT / surface).rglob("*.py"))
        if python_files:
            rendered = ", ".join(str(path.relative_to(ROOT)) for path in python_files)
            fail(f"Python implementation files are forbidden under {surface}/: {rendered}")

    excluded = document.get("excluded_surfaces")
    if not isinstance(excluded, dict):
        fail("excluded_surfaces must be an object")
    if not REQUIRED_EXCLUDED_SURFACES.issubset(excluded):
        missing = sorted(REQUIRED_EXCLUDED_SURFACES - set(excluded))
        fail(f"required excluded surfaces missing: {missing}")
    for name in REQUIRED_EXCLUDED_SURFACES:
        entry = excluded[name]
        if not isinstance(entry, dict) or entry.get("normative") is not False:
            fail(f"excluded surface {name!r} must be explicitly non-normative")

    print("repository boundaries OK")


if __name__ == "__main__":
    main()

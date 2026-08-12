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


def fail(message: str) -> None:
    raise SystemExit(f"repository boundary FAIL: {message}")


def main() -> None:
    try:
        document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {MANIFEST.name}: {exc}")

    if document.get("repository_phase") != "alpha-monorepo":
        fail("repository_phase must explicitly declare alpha-monorepo")

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

    if document.get("authority_order") != ["spec", "schemas", "conformance", "reference-implementation"]:
        fail("authority_order changed without an explicit boundary-policy update")

    for surface in NORMATIVE:
        python_files = sorted((ROOT / surface).rglob("*.py"))
        if python_files:
            rendered = ", ".join(str(path.relative_to(ROOT)) for path in python_files)
            fail(f"Python implementation files are forbidden under {surface}/: {rendered}")

    platform = document.get("excluded_surfaces", {}).get("commercial_platform")
    if not isinstance(platform, dict) or platform.get("normative") is not False:
        fail("commercial platform must be explicitly non-normative")

    print("repository boundaries OK")


if __name__ == "__main__":
    main()

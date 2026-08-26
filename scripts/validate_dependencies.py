"""Validate AVP dependency compatibility and reproducibility policy."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
CONSTRAINTS = ROOT / "constraints" / "ci.txt"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

_REQUIREMENT_NAME = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")
_EXACT_PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;]+)$")


def _fail(message: str) -> None:
    raise SystemExit(message)


def _canonical_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _requirement_name(requirement: str) -> str:
    match = _REQUIREMENT_NAME.match(requirement)
    if match is None:
        _fail(f"cannot parse dependency requirement: {requirement!r}")
    return _canonical_name(match.group(1))


def _exact_pin(requirement: str, context: str) -> tuple[str, str]:
    match = _EXACT_PIN.fullmatch(requirement)
    if match is None:
        _fail(f"{context} must be an exact NAME==VERSION pin: {requirement}")
    return _canonical_name(match.group(1)), match.group(2)


def _require_compatibility_window(requirement: str, context: str) -> None:
    if ">=" not in requirement:
        _fail(f"{context} dependency needs an explicit tested lower bound: {requirement}")
    if "<" not in requirement:
        _fail(f"{context} dependency needs an explicit breaking-version upper bound: {requirement}")
    if "==" in requirement:
        _fail(f"{context} dependency must expose a compatibility range, not an exact pin: {requirement}")


def _load_constraints() -> dict[str, str]:
    if not CONSTRAINTS.is_file():
        _fail("constraints/ci.txt is required")
    pins: dict[str, str] = {}
    previous: str | None = None
    for line_number, raw in enumerate(CONSTRAINTS.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _EXACT_PIN.fullmatch(line)
        if match is None:
            _fail(f"constraints/ci.txt:{line_number} must be an exact NAME==VERSION pin")
        name = _canonical_name(match.group(1))
        if name in pins:
            _fail(f"duplicate CI constraint for {name}")
        if previous is not None and name < previous:
            _fail("constraints/ci.txt pins must be sorted by normalized package name")
        previous = name
        pins[name] = match.group(2)
    if not pins:
        _fail("constraints/ci.txt must contain at least one exact pin")
    return pins


def main() -> None:
    document = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    build_requires = document.get("build-system", {}).get("requires", [])
    if not isinstance(build_requires, list) or len(build_requires) != 1:
        _fail("build-system.requires must contain exactly one reviewed build backend pin")
    build_backend_name, build_backend_version = _exact_pin(
        build_requires[0], "build-system.requires build backend"
    )
    if build_backend_name != "setuptools":
        _fail("build-system.requires must pin setuptools as the reviewed build backend")

    project = document.get("project", {})
    runtime = project.get("dependencies", [])
    optional = project.get("optional-dependencies", {})
    if not isinstance(runtime, list) or not isinstance(optional, dict):
        _fail("pyproject project dependency tables are malformed")

    for requirement in runtime:
        _require_compatibility_window(requirement, "runtime")
    for group_name, requirements in optional.items():
        if not isinstance(requirements, list):
            _fail(f"optional dependency group {group_name!r} must be a list")
        for requirement in requirements:
            _require_compatibility_window(requirement, f"optional group {group_name}")

    pins = _load_constraints()
    ci_optional_groups = ("dev", "postgresql")
    ci_direct_requirements = list(runtime)
    for group_name in ci_optional_groups:
        ci_direct_requirements.extend(optional.get(group_name, []))
    missing = sorted(
        name
        for name in {_requirement_name(item) for item in ci_direct_requirements}
        if name not in pins
    )
    if missing:
        _fail(f"CI constraints do not pin direct runtime/integration dependencies: {missing}")
    if pins.get(build_backend_name) != build_backend_version:
        _fail("CI constraints must pin the same setuptools version as build-system.requires")

    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    constrained_install = "python -m pip install -c constraints/ci.txt -e '.[dev]'"
    if workflow.count(constrained_install) < 2:
        _fail("CI quality and package build-tool installs must both use constraints/ci.txt")
    wheel_install = ".wheel-venv/bin/python -m pip install dist/*.whl"
    if wheel_install not in workflow:
        _fail("CI must retain an unconstrained clean-wheel consumer installation")
    if "-c constraints/ci.txt dist/*.whl" in workflow:
        _fail("clean-wheel consumer installation must not use repository constraints")
    if "[postgresql]" not in workflow or "AVP_POSTGRESQL_DSN" not in workflow:
        _fail("CI must retain a PostgreSQL optional-wheel integration path")

    print(
        "dependency policy OK: "
        f"build backend {build_backend_name}=={build_backend_version}, "
        f"{len(runtime)} runtime requirements, "
        f"{len(ci_direct_requirements)} CI direct requirements, "
        f"{len(pins)} exact CI pins"
    )


if __name__ == "__main__":
    main()

"""Validate release-facing identity, licensing, and built-wheel metadata."""

from __future__ import annotations

import argparse
import ast
import importlib.metadata
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
VERSION_FILE = ROOT / "src" / "avp_ref" / "_version.py"
LICENSE = ROOT / "LICENSE"
CHANGELOG = ROOT / "CHANGELOG.md"
CODE_OF_CONDUCT = ROOT / "CODE_OF_CONDUCT.md"
OBSOLETE_PUBLISHING = ROOT / "PUBLISHING.md"


def _fail(message: str) -> None:
    raise SystemExit(message)


def _source_version() -> str:
    tree = ast.parse(VERSION_FILE.read_text(encoding="utf-8"), filename=str(VERSION_FILE))
    values: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == "__version__":
            value = ast.literal_eval(node.value)
            if isinstance(value, str):
                values.append(value)
    if len(values) != 1 or not values[0]:
        _fail("src/avp_ref/_version.py must define exactly one non-empty __version__ string")
    return values[0]


def _validate_source_metadata(version: str) -> None:
    document = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = document.get("project", {})
    if project.get("version") is not None:
        _fail("project.version must not duplicate the single source version")
    if project.get("dynamic") != ["version"]:
        _fail("project.dynamic must contain only 'version'")
    if project.get("license") != "Apache-2.0":
        _fail("project.license must use the SPDX expression 'Apache-2.0'")
    if project.get("license-files") != ["LICENSE"]:
        _fail("project.license-files must explicitly include LICENSE")
    if project.get("readme") != "README.md":
        _fail("project.readme must identify README.md")

    dynamic = document.get("tool", {}).get("setuptools", {}).get("dynamic", {})
    if dynamic.get("version") != {"attr": "avp_ref._version.__version__"}:
        _fail("setuptools dynamic version must read avp_ref._version.__version__")

    from avp_ref import __version__
    from avp_ref.runtime import ReferenceRuntime

    if __version__ != version:
        _fail(f"package __version__ drift: source={version}, package={__version__}")
    installed = importlib.metadata.version("avp-reference")
    if installed != version:
        _fail(f"installed distribution version drift: source={version}, metadata={installed}")
    runtime_version = ReferenceRuntime().capabilities()["implementation"]["version"]
    if runtime_version != version:
        _fail(f"runtime implementation identity drift: source={version}, runtime={runtime_version}")


def _validate_repository_release_files() -> None:
    license_text = LICENSE.read_text(encoding="utf-8")
    required_license_markers = (
        "Apache License",
        "Version 2.0, January 2004",
        "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION",
        "END OF TERMS AND CONDITIONS",
    )
    if len(license_text) < 10_000 or any(
        marker not in license_text for marker in required_license_markers
    ):
        _fail("LICENSE must contain the complete Apache License 2.0 text")

    if OBSOLETE_PUBLISHING.exists():
        _fail("obsolete PUBLISHING.md bootstrap instructions must not be committed")

    changelog = CHANGELOG.read_text(encoding="utf-8")
    if "## Unreleased" not in changelog:
        _fail("CHANGELOG.md must retain an Unreleased development section")

    conduct = CODE_OF_CONDUCT.read_text(encoding="utf-8")
    required_conduct_sections = (
        "## Expected behavior",
        "## Unacceptable behavior",
        "## Reporting",
        "## Enforcement",
        "## No retaliation",
    )
    if any(section not in conduct for section in required_conduct_sections):
        _fail("CODE_OF_CONDUCT.md is missing required governance sections")


def _validate_wheel(path: Path, version: str) -> None:
    if not path.is_file() or path.suffix != ".whl":
        _fail(f"wheel path is invalid: {path}")
    with zipfile.ZipFile(path) as archive:
        metadata_members = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_members) != 1:
            _fail(f"wheel must contain exactly one METADATA file: {path}")
        message = BytesParser().parsebytes(archive.read(metadata_members[0]))
        if message.get("Name") != "avp-reference":
            _fail(f"wheel distribution name drift: {message.get('Name')!r}")
        if message.get("Version") != version:
            _fail(
                f"wheel version drift: source={version}, wheel={message.get('Version')!r}"
            )
        if message.get("License-Expression") != "Apache-2.0":
            _fail("wheel METADATA must contain License-Expression: Apache-2.0")
        if "LICENSE" not in message.get_all("License-File", []):
            _fail("wheel METADATA must declare License-File: LICENSE")
        if not any(
            name.endswith(".dist-info/licenses/LICENSE") for name in archive.namelist()
        ):
            _fail("wheel must contain the Apache-2.0 LICENSE file")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", nargs="*", type=Path, default=[])
    args = parser.parse_args()

    version = _source_version()
    _validate_source_metadata(version)
    _validate_repository_release_files()
    for wheel in args.wheel:
        _validate_wheel(wheel, version)

    suffix = f", {len(args.wheel)} wheel(s) validated" if args.wheel else ""
    print(f"release metadata OK: avp-reference {version}{suffix}")


if __name__ == "__main__":
    main()

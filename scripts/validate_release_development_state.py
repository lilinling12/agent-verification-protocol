"""Validate fail-closed development-version provenance after a published release."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from packaging.version import InvalidVersion, Version

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "docs" / "releases" / "release-development-state.json"
VERSION_FILE = ROOT / "src" / "avp_ref" / "_version.py"

SCHEMA_VERSION = "avp-release-development-state/v1"
DISTRIBUTION = "avp-reference"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")

# The already-published RC1 is immutable release evidence. Updating these anchors
# is a governed release transition, not ordinary development metadata maintenance.
IMMUTABLE_LATEST = {
    "version": "0.3.0rc1",
    "tag": "v0.3.0-rc.1",
    "commit": "ef199124017b0dcc8c4a966d00c4f407760f9a06",
}


class DevelopmentStateError(ValueError):
    """Raised when development/release identity is ambiguous or inconsistent."""


def _source_version(path: Path = VERSION_FILE) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == "__version__":
            value = ast.literal_eval(node.value)
            if isinstance(value, str) and value:
                values.append(value)
    if len(values) != 1:
        raise DevelopmentStateError("_version.py must define exactly one non-empty __version__")
    return values[0]


def _version(value: Any, field: str) -> Version:
    if not isinstance(value, str) or not value:
        raise DevelopmentStateError(f"{field} must be a non-empty version string")
    try:
        parsed = Version(value)
    except InvalidVersion as exc:
        raise DevelopmentStateError(f"{field} is not PEP 440 compliant: {value!r}") from exc
    if str(parsed) != value:
        raise DevelopmentStateError(
            f"{field} must use canonical PEP 440 form: expected {str(parsed)!r}, got {value!r}"
        )
    return parsed


def _expected_rc_tag(version: Version) -> str:
    if version.epoch != 0 or version.local is not None or version.post is not None or version.dev is not None:
        raise DevelopmentStateError("published RC tag version must not contain epoch/local/post/dev segments")
    if version.pre is None or version.pre[0] != "rc":
        raise DevelopmentStateError("published/next release strategy must use an RC prerelease")
    release = ".".join(str(part) for part in version.release)
    return f"v{release}-rc.{version.pre[1]}"


def validate_state(document: dict[str, Any], *, source_version: str) -> None:
    if set(document) != {"schemaVersion", "distribution", "mode", "latestPublished", "nextRelease", "sourceVersion"}:
        raise DevelopmentStateError("release development state has unexpected or missing top-level fields")
    if document["schemaVersion"] != SCHEMA_VERSION:
        raise DevelopmentStateError("release development state schemaVersion mismatch")
    if document["distribution"] != DISTRIBUTION:
        raise DevelopmentStateError("release development state distribution mismatch")
    if document["mode"] != "development":
        raise DevelopmentStateError("release development state must remain in development mode")

    latest = document["latestPublished"]
    next_release = document["nextRelease"]
    if latest != IMMUTABLE_LATEST:
        raise DevelopmentStateError("latestPublished must remain bound to immutable v0.3.0-rc.1 evidence")
    if not isinstance(next_release, dict) or set(next_release) != {"version", "tag"}:
        raise DevelopmentStateError("nextRelease must contain exactly version and tag")
    if not FULL_SHA.fullmatch(latest["commit"]):
        raise DevelopmentStateError("latestPublished.commit must be an exact lowercase 40-character SHA")

    latest_version = _version(latest["version"], "latestPublished.version")
    next_version = _version(next_release["version"], "nextRelease.version")
    declared_source = _version(document["sourceVersion"], "sourceVersion")
    actual_source = _version(source_version, "_version.py __version__")

    if latest["tag"] != _expected_rc_tag(latest_version):
        raise DevelopmentStateError("latestPublished.tag does not match latestPublished.version")
    if next_release["tag"] != _expected_rc_tag(next_version):
        raise DevelopmentStateError("nextRelease.tag does not match nextRelease.version")
    if declared_source != actual_source:
        raise DevelopmentStateError(
            f"sourceVersion drift: state={declared_source}, _version.py={actual_source}"
        )
    if declared_source == latest_version:
        raise DevelopmentStateError("development source must not reuse an already-published version")
    if not latest_version < declared_source < next_version:
        raise DevelopmentStateError(
            "development version ordering must satisfy latestPublished < sourceVersion < nextRelease"
        )

    # AVP's post-RC development policy deliberately uses a development release of
    # the *next* RC, e.g. rc2.dev0. This preserves monotonic ordering after rc1
    # without claiming that rc2 itself has been published.
    if next_version.pre is None or next_version.pre[0] != "rc":
        raise DevelopmentStateError("nextRelease.version must be an RC prerelease")
    if declared_source.pre != next_version.pre or declared_source.dev is None:
        raise DevelopmentStateError("sourceVersion must be a development release of nextRelease")
    if declared_source.release != next_version.release:
        raise DevelopmentStateError("sourceVersion and nextRelease must share the same release tuple")
    if declared_source.post is not None or declared_source.local is not None:
        raise DevelopmentStateError("sourceVersion must not contain post/local segments")


def main() -> None:
    try:
        document = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"unable to read release development state: {exc}") from exc
    if not isinstance(document, dict):
        raise SystemExit("release development state must be a JSON object")
    try:
        validate_state(document, source_version=_source_version())
    except DevelopmentStateError as exc:
        raise SystemExit(str(exc)) from exc
    print(
        "release development state OK: "
        f"{document['latestPublished']['version']} < {document['sourceVersion']} < "
        f"{document['nextRelease']['version']}"
    )


if __name__ == "__main__":
    main()

"""Validate fail-closed AVP release provenance and transition state."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from packaging.version import InvalidVersion, Version

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "docs" / "releases" / "release-development-state.json"
LEDGER_FILE = ROOT / "docs" / "releases" / "published-releases.json"
VERSION_FILE = ROOT / "src" / "avp_ref" / "_version.py"

STATE_SCHEMA_VERSION = "avp-release-development-state/v2"
LEDGER_SCHEMA_VERSION = "avp-published-release-ledger/v1"
DISTRIBUTION = "avp-reference"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")

# RC1 is the immutable seed for the published-release ledger. Future published
# releases are appended through governed release transitions; this seed may not
# be rewritten or removed.
IMMUTABLE_SEED = {
    "version": "0.3.0rc1",
    "tag": "v0.3.0-rc.1",
    "commit": "ef199124017b0dcc8c4a966d00c4f407760f9a06",
    "class": "prerelease",
}


class DevelopmentStateError(ValueError):
    """Raised when development or release identity is ambiguous or inconsistent."""


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
        raise DevelopmentStateError(
            "_version.py must define exactly one non-empty __version__"
        )
    return values[0]


def _version(value: Any, field: str) -> Version:
    if not isinstance(value, str) or not value:
        raise DevelopmentStateError(f"{field} must be a non-empty version string")
    try:
        parsed = Version(value)
    except InvalidVersion as exc:
        raise DevelopmentStateError(
            f"{field} is not PEP 440 compliant: {value!r}"
        ) from exc
    if str(parsed) != value:
        raise DevelopmentStateError(
            f"{field} must use canonical PEP 440 form: expected {str(parsed)!r}, got {value!r}"
        )
    return parsed


def _release_tag(version: Version) -> tuple[str, str]:
    """Return the only accepted public tag and class for a release version."""

    if (
        version.epoch != 0
        or version.local is not None
        or version.post is not None
        or version.dev is not None
    ):
        raise DevelopmentStateError(
            "public release version must not contain epoch/local/post/dev segments"
        )
    release = ".".join(str(part) for part in version.release)
    if version.pre is None:
        return f"v{release}", "stable"
    if version.pre[0] != "rc":
        raise DevelopmentStateError("AVP prerelease publication strategy must use RC releases")
    return f"v{release}-rc.{version.pre[1]}", "prerelease"


def validate_ledger(document: dict[str, Any]) -> list[dict[str, str]]:
    if set(document) != {"schemaVersion", "distribution", "releases"}:
        raise DevelopmentStateError(
            "published release ledger has unexpected or missing top-level fields"
        )
    if document["schemaVersion"] != LEDGER_SCHEMA_VERSION:
        raise DevelopmentStateError("published release ledger schemaVersion mismatch")
    if document["distribution"] != DISTRIBUTION:
        raise DevelopmentStateError("published release ledger distribution mismatch")

    releases = document["releases"]
    if not isinstance(releases, list) or not releases:
        raise DevelopmentStateError("published release ledger must contain releases")
    if releases[0] != IMMUTABLE_SEED:
        raise DevelopmentStateError("published release ledger immutable RC1 seed mismatch")

    normalized: list[dict[str, str]] = []
    previous_version: Version | None = None
    commits: set[str] = set()
    tags: set[str] = set()
    for index, item in enumerate(releases):
        if not isinstance(item, dict) or set(item) != {
            "version",
            "tag",
            "commit",
            "class",
        }:
            raise DevelopmentStateError(
                f"published release ledger entry {index} has invalid fields"
            )
        version = _version(item["version"], f"releases[{index}].version")
        expected_tag, expected_class = _release_tag(version)
        if item["tag"] != expected_tag:
            raise DevelopmentStateError(
                f"releases[{index}].tag does not match release version"
            )
        if item["class"] != expected_class:
            raise DevelopmentStateError(
                f"releases[{index}].class does not match release version"
            )
        commit = item["commit"]
        if not isinstance(commit, str) or not FULL_SHA.fullmatch(commit):
            raise DevelopmentStateError(
                f"releases[{index}].commit must be an exact lowercase 40-character SHA"
            )
        if previous_version is not None and version <= previous_version:
            raise DevelopmentStateError(
                "published release versions must be strictly monotonic"
            )
        if commit in commits:
            raise DevelopmentStateError("published release commits must be unique")
        if item["tag"] in tags:
            raise DevelopmentStateError("published release tags must be unique")
        previous_version = version
        commits.add(commit)
        tags.add(item["tag"])
        normalized.append(dict(item))
    return normalized


def validate_state(
    document: dict[str, Any],
    *,
    source_version: str,
    published_releases: list[dict[str, str]],
) -> None:
    if set(document) != {
        "schemaVersion",
        "distribution",
        "mode",
        "latestPublished",
        "nextRelease",
        "sourceVersion",
    }:
        raise DevelopmentStateError(
            "release state has unexpected or missing top-level fields"
        )
    if document["schemaVersion"] != STATE_SCHEMA_VERSION:
        raise DevelopmentStateError("release state schemaVersion mismatch")
    if document["distribution"] != DISTRIBUTION:
        raise DevelopmentStateError("release state distribution mismatch")
    if document["mode"] not in {"development", "release"}:
        raise DevelopmentStateError("release state mode must be development or release")
    if not published_releases:
        raise DevelopmentStateError("published release ledger must not be empty")

    latest = document["latestPublished"]
    latest_ledger = {
        key: published_releases[-1][key] for key in ("version", "tag", "commit")
    }
    if latest != latest_ledger:
        raise DevelopmentStateError(
            "latestPublished must equal the final published-release ledger entry"
        )

    next_release = document["nextRelease"]
    if not isinstance(next_release, dict) or set(next_release) != {"version", "tag"}:
        raise DevelopmentStateError("nextRelease must contain exactly version and tag")

    latest_version = _version(latest["version"], "latestPublished.version")
    next_version = _version(next_release["version"], "nextRelease.version")
    declared_source = _version(document["sourceVersion"], "sourceVersion")
    actual_source = _version(source_version, "_version.py __version__")
    expected_tag, _ = _release_tag(next_version)

    if next_release["tag"] != expected_tag:
        raise DevelopmentStateError("nextRelease.tag does not match nextRelease.version")
    if declared_source != actual_source:
        raise DevelopmentStateError(
            f"sourceVersion drift: state={declared_source}, _version.py={actual_source}"
        )
    if next_version <= latest_version:
        raise DevelopmentStateError("nextRelease must be newer than latestPublished")

    if document["mode"] == "development":
        if declared_source.dev is None:
            raise DevelopmentStateError(
                "development mode sourceVersion must be a PEP 440 development release"
            )
        if not latest_version < declared_source < next_version:
            raise DevelopmentStateError(
                "development ordering must satisfy latestPublished < sourceVersion < nextRelease"
            )
        if declared_source.post is not None or declared_source.local is not None:
            raise DevelopmentStateError(
                "development sourceVersion must not contain post/local segments"
            )
        return

    # Release mode is intentionally exact: selecting a release is a governed
    # transition, and the source identity must equal the planned public version.
    if declared_source != next_version:
        raise DevelopmentStateError(
            "release mode sourceVersion must equal nextRelease.version exactly"
        )
    if declared_source <= latest_version:
        raise DevelopmentStateError(
            "selected release must be newer than latestPublished"
        )


def main() -> None:
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        ledger = json.loads(LEDGER_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"unable to read release provenance state: {exc}") from exc
    if not isinstance(state, dict) or not isinstance(ledger, dict):
        raise SystemExit("release provenance documents must be JSON objects")
    try:
        releases = validate_ledger(ledger)
        validate_state(
            state,
            source_version=_source_version(),
            published_releases=releases,
        )
    except DevelopmentStateError as exc:
        raise SystemExit(str(exc)) from exc

    print(
        "release provenance state OK: "
        f"mode={state['mode']}, latest={state['latestPublished']['version']}, "
        f"source={state['sourceVersion']}, next={state['nextRelease']['version']}"
    )


if __name__ == "__main__":
    main()

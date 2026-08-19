"""Validate a published GitHub release against exact AVP release evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_DIGEST = re.compile(r"^sha256:([0-9a-f]{64})$")
# AVP's governed release-transition state currently permits exact RC and stable
# publication identities. Keep this subset deliberately narrower than arbitrary
# PEP 440 so release tags and artifact filenames can be derived unambiguously.
_RELEASE_VERSION = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:rc(0|[1-9][0-9]*))?$"
)
_SCHEMA_VERSION = "avp-release-evidence/v1"


class PublishedReleaseError(ValueError):
    """Raised when a published release is incomplete, inconsistent, or tampered with."""


def _expected_tag(version: str, *, prerelease: bool) -> str:
    match = _RELEASE_VERSION.fullmatch(version)
    if match is None:
        raise PublishedReleaseError(
            "distribution version must use the canonical AVP RC/stable PEP 440 subset"
        )

    major, minor, patch, rc_number = match.groups()
    release = f"{major}.{minor}.{patch}"
    if prerelease:
        if rc_number is None:
            raise PublishedReleaseError("prerelease validation requires an RC distribution version")
        return f"v{release}-rc.{rc_number}"
    if rc_number is not None:
        raise PublishedReleaseError("stable validation requires a stable distribution version")
    return f"v{release}"


def _validate_identity(
    repository: str,
    tag: str,
    commit: str,
    version: str,
    *,
    prerelease: bool,
) -> None:
    if not _REPOSITORY.fullmatch(repository):
        raise PublishedReleaseError(f"invalid repository identity: {repository!r}")
    if not _FULL_SHA.fullmatch(commit):
        raise PublishedReleaseError("release validation requires an exact lowercase 40-character commit SHA")

    expected_tag = _expected_tag(version, prerelease=prerelease)
    if tag != expected_tag:
        raise PublishedReleaseError(
            f"release tag/version/class mismatch: expected {expected_tag!r}, got {tag!r}"
        )


def _request_json(url: str, token: str | None) -> dict[str, Any]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            document = json.load(response)
    except (OSError, urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise PublishedReleaseError(f"unable to read GitHub release metadata from {url}: {exc}") from exc
    if not isinstance(document, dict):
        raise PublishedReleaseError(f"GitHub API response from {url} must be an object")
    return document


def _download(url: str, destination: Path, token: str | None) -> None:
    headers = {"Accept": "application/octet-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
    except (OSError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise PublishedReleaseError(f"unable to download release asset {url}: {exc}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _asset_records(release: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise PublishedReleaseError("release assets must be an array")
    records: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict) or not isinstance(asset.get("name"), str):
            raise PublishedReleaseError("release asset metadata is malformed")
        name = asset["name"]
        if name in records:
            raise PublishedReleaseError(f"duplicate release asset name: {name}")
        records[name] = asset
    return records


def validate_published_release(
    *,
    repository: str,
    tag: str,
    commit: str,
    version: str,
    output_dir: Path,
    token: str | None = None,
    prerelease: bool = True,
) -> dict[str, Any]:
    """Download and verify an exact GitHub release and its authoritative evidence assets."""

    _validate_identity(repository, tag, commit, version, prerelease=prerelease)
    api_root = f"https://api.github.com/repos/{repository}"
    release = _request_json(f"{api_root}/releases/tags/{tag}", token)
    ref = _request_json(f"{api_root}/git/ref/tags/{tag}", token)

    if release.get("tag_name") != tag:
        raise PublishedReleaseError("release tag name mismatch")
    if release.get("draft") is not False:
        raise PublishedReleaseError("release must be published, not draft")
    if release.get("prerelease") is not prerelease:
        raise PublishedReleaseError("release prerelease flag mismatch")
    if release.get("target_commitish") != commit:
        raise PublishedReleaseError("release target commit mismatch")

    ref_object = ref.get("object")
    if not isinstance(ref_object, dict) or ref_object.get("type") != "commit" or ref_object.get("sha") != commit:
        raise PublishedReleaseError("release tag does not resolve directly to the expected commit")

    wheel = f"avp_reference-{version}-py3-none-any.whl"
    sdist = f"avp_reference-{version}.tar.gz"
    expected_names = {wheel, sdist, "MANIFEST.json", "SHA256SUMS"}
    assets = _asset_records(release)
    if set(assets) != expected_names:
        raise PublishedReleaseError(
            f"release asset set mismatch: expected {sorted(expected_names)}, found {sorted(assets)}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    for name in sorted(expected_names):
        asset = assets[name]
        asset_url = asset.get("url")
        if not isinstance(asset_url, str):
            raise PublishedReleaseError(f"release asset {name} is missing its API URL")
        destination = output_dir / name
        _download(asset_url, destination, token)

        digest_match = _DIGEST.fullmatch(str(asset.get("digest", "")))
        if digest_match is None:
            raise PublishedReleaseError(f"release asset {name} is missing a SHA-256 digest")
        actual_digest = _sha256(destination)
        if actual_digest != digest_match.group(1):
            raise PublishedReleaseError(f"GitHub asset digest mismatch for {name}")
        size = asset.get("size")
        if not isinstance(size, int) or size != destination.stat().st_size:
            raise PublishedReleaseError(f"GitHub asset size mismatch for {name}")

    manifest_path = output_dir / "MANIFEST.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublishedReleaseError(f"unable to read published MANIFEST.json: {exc}") from exc
    if not isinstance(manifest, dict):
        raise PublishedReleaseError("published MANIFEST.json must be an object")
    if manifest.get("schemaVersion") != _SCHEMA_VERSION:
        raise PublishedReleaseError("published manifest schema version mismatch")
    if manifest.get("source") != {"commit": commit, "repository": repository}:
        raise PublishedReleaseError("published manifest source identity mismatch")
    if manifest.get("distribution") != {"name": "avp-reference", "version": version}:
        raise PublishedReleaseError("published manifest distribution identity mismatch")

    records = manifest.get("artifacts")
    if not isinstance(records, list) or len(records) != 2:
        raise PublishedReleaseError("published manifest must contain exactly two distribution artifacts")
    expected_manifest_records = []
    for kind, name in (("wheel", wheel), ("sdist", sdist)):
        path = output_dir / name
        expected_manifest_records.append(
            {"filename": name, "kind": kind, "sha256": _sha256(path), "size": path.stat().st_size}
        )
    if records != sorted(expected_manifest_records, key=lambda item: item["filename"]):
        raise PublishedReleaseError("published manifest artifact records do not match downloaded bytes")

    expected_checksums = [
        f"{record['sha256']}  {record['filename']}"
        for record in sorted(expected_manifest_records, key=lambda item: item["filename"])
    ]
    expected_checksums.append(f"{_sha256(manifest_path)}  MANIFEST.json")
    try:
        actual_checksums = (output_dir / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise PublishedReleaseError(f"unable to read published SHA256SUMS: {exc}") from exc
    if actual_checksums != expected_checksums:
        raise PublishedReleaseError("published SHA256SUMS does not match downloaded release bytes")

    return {"release": release, "manifest": manifest, "wheel": str(output_dir / wheel)}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--token")
    parser.add_argument("--stable", action="store_true", help="expect a non-prerelease GitHub release")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    try:
        result = validate_published_release(
            repository=args.repository,
            tag=args.tag,
            commit=args.commit,
            version=args.version,
            output_dir=args.output_dir,
            token=args.token,
            prerelease=not args.stable,
        )
    except PublishedReleaseError as exc:
        raise SystemExit(str(exc)) from exc
    print(
        "published release validation OK: "
        f"{args.repository}@{args.tag} -> {args.commit} "
        f"({len(result['release']['assets'])} verified assets)"
    )


if __name__ == "__main__":
    main()

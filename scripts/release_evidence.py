"""Build and verify deterministic release-evidence metadata for AVP distributions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "src" / "avp_ref" / "_version.py"
SCHEMA_VERSION = "avp-release-evidence/v1"
DISTRIBUTION_NAME = "avp-reference"
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_VERSION = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']\s*$', re.MULTILINE)


class EvidenceError(ValueError):
    """Raised when release evidence is incomplete, inconsistent, or tampered with."""


def _release_version() -> str:
    match = _VERSION.search(VERSION_FILE.read_text(encoding="utf-8"))
    if match is None:
        raise EvidenceError(f"unable to read release version from {VERSION_FILE.relative_to(ROOT)}")
    return match.group(1)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_source(repository: str, commit: str) -> None:
    if not _REPOSITORY.fullmatch(repository):
        raise EvidenceError(f"invalid repository identity: {repository!r}")
    if not _FULL_SHA.fullmatch(commit):
        raise EvidenceError("release evidence requires an exact lowercase 40-character commit SHA")


def _collect_distribution_artifacts(dist_dir: Path, version: str) -> list[dict[str, Any]]:
    if not dist_dir.is_dir():
        raise EvidenceError(f"distribution directory does not exist: {dist_dir}")

    wheels = sorted(path for path in dist_dir.glob("*.whl") if path.is_file())
    sdists = sorted(path for path in dist_dir.glob("*.tar.gz") if path.is_file())
    if len(wheels) != 1 or len(sdists) != 1:
        raise EvidenceError(
            "release evidence requires exactly one wheel and one source distribution; "
            f"found {len(wheels)} wheel(s) and {len(sdists)} sdist(s)"
        )

    expected_paths = {wheels[0], sdists[0]}
    unexpected = sorted(
        path.name for path in dist_dir.iterdir() if path.is_file() and path not in expected_paths
    )
    if unexpected:
        raise EvidenceError(f"unexpected files in distribution directory: {unexpected}")

    wheel, sdist = wheels[0], sdists[0]
    if f"-{version}-" not in wheel.name:
        raise EvidenceError(f"wheel filename does not bind release version {version!r}: {wheel.name}")
    if not sdist.name.endswith(f"-{version}.tar.gz"):
        raise EvidenceError(f"sdist filename does not bind release version {version!r}: {sdist.name}")

    records = []
    for kind, path in (("sdist", sdist), ("wheel", wheel)):
        records.append(
            {
                "filename": path.name,
                "kind": kind,
                "sha256": _sha256(path),
                "size": path.stat().st_size,
            }
        )
    return sorted(records, key=lambda item: item["filename"])


def build_evidence(*, dist_dir: Path, output_dir: Path, repository: str, commit: str) -> dict[str, Any]:
    """Create deterministic evidence files for exactly one wheel and one sdist."""

    _validate_source(repository, commit)
    version = _release_version()
    artifacts = _collect_distribution_artifacts(dist_dir, version)
    manifest = {
        "artifacts": artifacts,
        "distribution": {"name": DISTRIBUTION_NAME, "version": version},
        "schemaVersion": SCHEMA_VERSION,
        "source": {"commit": commit, "repository": repository},
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    checksum_lines = [
        f"{record['sha256']}  {record['filename']}" for record in artifacts
    ]
    checksum_lines.append(f"{_sha256(manifest_path)}  {manifest_path.name}")
    (output_dir / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return manifest


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"unable to read release evidence manifest: {exc}") from exc
    if not isinstance(document, dict):
        raise EvidenceError("release evidence manifest must be a JSON object")
    return document


def verify_evidence(*, dist_dir: Path, output_dir: Path, repository: str, commit: str) -> dict[str, Any]:
    """Verify source identity, artifact bytes, manifest metadata, and checksum file."""

    _validate_source(repository, commit)
    manifest_path = output_dir / "MANIFEST.json"
    checksums_path = output_dir / "SHA256SUMS"
    manifest = _load_manifest(manifest_path)
    version = _release_version()

    if manifest.get("schemaVersion") != SCHEMA_VERSION:
        raise EvidenceError("release evidence schema version mismatch")
    if manifest.get("source") != {"commit": commit, "repository": repository}:
        raise EvidenceError("release evidence source identity mismatch")
    if manifest.get("distribution") != {"name": DISTRIBUTION_NAME, "version": version}:
        raise EvidenceError("release evidence distribution identity mismatch")

    actual_records = _collect_distribution_artifacts(dist_dir, version)
    recorded = manifest.get("artifacts")
    if recorded != actual_records:
        raise EvidenceError("release evidence artifact digest/size metadata does not match distribution bytes")

    expected_checksum_lines = [
        f"{record['sha256']}  {record['filename']}" for record in actual_records
    ]
    expected_checksum_lines.append(f"{_sha256(manifest_path)}  {manifest_path.name}")
    try:
        actual_checksum_lines = checksums_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise EvidenceError(f"unable to read SHA256SUMS: {exc}") from exc
    if actual_checksum_lines != expected_checksum_lines:
        raise EvidenceError("SHA256SUMS does not match the release artifacts and manifest")

    return manifest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "verify"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--dist", type=Path, required=True)
        subparser.add_argument("--output-dir", type=Path, required=True)
        subparser.add_argument("--repository", required=True)
        subparser.add_argument("--commit", required=True)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    try:
        operation = build_evidence if args.command == "build" else verify_evidence
        manifest = operation(
            dist_dir=args.dist,
            output_dir=args.output_dir,
            repository=args.repository,
            commit=args.commit,
        )
    except EvidenceError as exc:
        raise SystemExit(str(exc)) from exc

    print(
        f"release evidence {args.command} OK: "
        f"{manifest['distribution']['name']} {manifest['distribution']['version']} "
        f"from {manifest['source']['commit']} ({len(manifest['artifacts'])} artifacts)"
    )


if __name__ == "__main__":
    main()

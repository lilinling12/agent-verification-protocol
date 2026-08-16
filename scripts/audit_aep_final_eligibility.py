#!/usr/bin/env python3
"""Audit Alpha 2 AEP technical finality evidence and lifecycle eligibility.

The audit intentionally separates two questions:

1. Did a published release contain the normative specification and required
   conformance assets for an AEP?
2. Does release policy make that publication a lifecycle-finality boundary?

A prerelease can therefore have complete technical evidence while still requiring
an explicit stable/finality decision. The script is standard-library only so it can
run in governance CI before project dependencies are installed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


EXPECTED_TAG = "v0.3.0-rc.1"
EXPECTED_RELEASE_COMMIT = "ef199124017b0dcc8c4a966d00c4f407760f9a06"
EXPECTED_REPOSITORY = "lilinling12/agent-verification-protocol"
GITHUB_API = "https://api.github.com"


@dataclass(frozen=True)
class AepEvidence:
    aep: str
    rfc: str
    normative_specs: tuple[str, ...]
    requirement_indexes: tuple[str, ...]
    schemas: tuple[str, ...]
    tck_profiles: tuple[str, ...]


AEP_EVIDENCE: tuple[AepEvidence, ...] = (
    AepEvidence(
        "AEP-0001",
        "rfcs/AEP-0001-oracle-evaluation-contract.md",
        ("spec/oracle/oracle-evaluation-contract.md",),
        ("spec/oracle/requirement-index.yaml",),
        ("schemas/oracle-evaluation.schema.json",),
        ("conformance/tck/profiles/avp-oracle-v0.1.yaml",),
    ),
    AepEvidence(
        "AEP-0002",
        "rfcs/AEP-0002-security-boundary-contract.md",
        ("spec/security/security-boundary-contract.md",),
        ("spec/security/requirement-index.yaml",),
        ("schemas/security-assurance.schema.json",),
        ("conformance/tck/profiles/avp-security-v0.1.yaml",),
    ),
    AepEvidence(
        "AEP-0003",
        "rfcs/AEP-0003-scenario-instance-contract.md",
        ("spec/scenario/scenario-contract.md",),
        ("spec/scenario/requirement-index.yaml",),
        (
            "schemas/scenario-template.schema.json",
            "schemas/scenario-instance.schema.json",
        ),
        ("conformance/tck/profiles/avp-scenario-v0.1.yaml",),
    ),
    AepEvidence(
        "AEP-0004",
        "rfcs/AEP-0004-environment-contract.md",
        ("spec/environment/environment-contract.md",),
        ("spec/environment/requirement-index.yaml",),
        (),
        ("conformance/tck/profiles/avp-environment-v0.1.yaml",),
    ),
    AepEvidence(
        "AEP-0005",
        "rfcs/AEP-0005-mcp-tools-interop-profile.md",
        ("spec/mcp/mcp-tools-interop-contract.md",),
        ("spec/mcp/requirement-index.yaml",),
        (),
        ("conformance/tck/profiles/avp-mcp-interop-v0.1.yaml",),
    ),
    AepEvidence(
        "AEP-0006",
        "rfcs/AEP-0006-opentelemetry-mapping-profile.md",
        ("spec/opentelemetry/opentelemetry-mapping-contract.md",),
        ("spec/opentelemetry/requirement-index.yaml",),
        (),
        ("conformance/tck/profiles/avp-otel-mapping-v0.1.yaml",),
    ),
    AepEvidence(
        "AEP-0007",
        "rfcs/AEP-0007-subject-adapter-contract.md",
        ("spec/subject/subject-adapter-contract.md",),
        ("spec/subject/requirement-index.yaml",),
        (),
        ("conformance/tck/profiles/avp-subject-v0.1.yaml",),
    ),
    AepEvidence(
        "AEP-0008",
        "rfcs/AEP-0008-artifact-trust-attestation.md",
        ("spec/trust/artifact-trust-attestation-contract.md",),
        ("spec/trust/requirement-index.yaml",),
        (
            "schemas/artifact-attestation.schema.json",
            "schemas/artifact-trust-policy.schema.json",
            "schemas/artifact-trust-result.schema.json",
        ),
        ("conformance/tck/profiles/avp-artifact-trust-v0.1.yaml",),
    ),
)


class AuditError(RuntimeError):
    """Raised when evidence is missing, ambiguous, or internally inconsistent."""


def _read_text(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        raise AuditError(f"required file missing: {relative}")
    return path.read_text(encoding="utf-8")


def _require_files(root: Path, paths: Iterable[str]) -> None:
    for relative in paths:
        if not (root / relative).is_file():
            raise AuditError(f"required released asset missing: {relative}")


def _aep_status(text: str, aep: str) -> str:
    matches = re.findall(r"(?mi)^-\s*Status:\s*([A-Za-z]+)\s*$", text)
    if len(matches) != 1:
        raise AuditError(f"{aep} must contain exactly one '- Status:' field")
    return matches[0]


def _load_release(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"invalid release metadata JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise AuditError("release metadata must be a JSON object")
    return payload


def _fetch_json(url: str, token: str) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "avp-aep-final-eligibility-audit",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise AuditError(f"GitHub API request failed for {url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise AuditError(f"GitHub API returned a non-object for {url}")
    return payload


def _bind_tag_resolution(release: dict[str, Any], tag_ref: dict[str, Any]) -> dict[str, Any]:
    expected_ref = f"refs/tags/{EXPECTED_TAG}"
    if tag_ref.get("ref") != expected_ref:
        raise AuditError("GitHub tag ref does not match the audited release tag")
    target = tag_ref.get("object")
    if not isinstance(target, dict):
        raise AuditError("GitHub tag ref is missing its target object")
    if target.get("type") != "commit":
        raise AuditError("audited RC tag must resolve directly to a commit")
    sha = target.get("sha")
    if not isinstance(sha, str):
        raise AuditError("GitHub tag target is missing a commit SHA")
    combined = dict(release)
    combined["resolved_tag_commit"] = sha
    return combined


def fetch_live_release_metadata(repository: str, tag: str, token: str) -> dict[str, Any]:
    if repository != EXPECTED_REPOSITORY or tag != EXPECTED_TAG:
        raise AuditError("this audit is pinned to the Alpha 2 RC1 repository and tag")
    encoded_tag = urllib.parse.quote(tag, safe="")
    release = _fetch_json(f"{GITHUB_API}/repos/{repository}/releases/tags/{encoded_tag}", token)
    tag_ref = _fetch_json(f"{GITHUB_API}/repos/{repository}/git/ref/tags/{encoded_tag}", token)
    return _bind_tag_resolution(release, tag_ref)


def _asset_names(release: dict[str, Any]) -> set[str]:
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise AuditError("release metadata assets must be an array")
    names: set[str] = set()
    for item in assets:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise AuditError("release asset must contain a string name")
        name = item["name"]
        if name in names:
            raise AuditError(f"duplicate release asset name: {name}")
        names.add(name)
    return names


def _validate_release(release: dict[str, Any]) -> str:
    if release.get("tag_name") != EXPECTED_TAG:
        raise AuditError("release tag does not match the audited RC")
    if release.get("resolved_tag_commit") != EXPECTED_RELEASE_COMMIT:
        raise AuditError("release tag does not resolve to the audited source commit")
    if release.get("target_commitish") != EXPECTED_RELEASE_COMMIT:
        raise AuditError("release target_commitish does not match the audited source commit")
    if release.get("draft") is not False:
        raise AuditError("audited release must be published, not draft")
    if release.get("prerelease") is not True:
        raise AuditError("v0.3.0-rc.1 must remain classified as a prerelease")

    expected_assets = {
        "avp_reference-0.3.0rc1-py3-none-any.whl",
        "avp_reference-0.3.0rc1.tar.gz",
        "MANIFEST.json",
        "SHA256SUMS",
    }
    actual_assets = _asset_names(release)
    if actual_assets != expected_assets:
        missing = sorted(expected_assets - actual_assets)
        extra = sorted(actual_assets - expected_assets)
        raise AuditError(f"release asset set mismatch: missing={missing}, extra={extra}")

    body = release.get("body")
    if not isinstance(body, str):
        raise AuditError("release body must be present")
    normalized = body.casefold()
    if "remain accepted" not in normalized or "not final" not in normalized:
        raise AuditError(
            "release body must explicitly preserve the Accepted/not-Final lifecycle boundary"
        )
    return "PUBLISHED_PRERELEASE_ACCEPTED_NOT_FINAL"


def _verify_profile_registration(release_root: Path, profiles: Iterable[str]) -> None:
    registry = _read_text(release_root, "conformance/tck/registry.yaml")
    for profile_path in profiles:
        profile_id = Path(profile_path).stem
        if not re.search(rf"(?m)^\s*profile:\s*{re.escape(profile_id)}\s*$", registry):
            raise AuditError(f"released TCK profile is not registered: {profile_id}")


def audit(current_root: Path, release_root: Path, release: dict[str, Any]) -> dict[str, Any]:
    governance = _read_text(current_root, "GOVERNANCE.md")
    release_process = _read_text(current_root, "docs/RELEASE_PROCESS.md")

    final_rule = "`Final` — normative text and required conformance coverage are merged and released"
    if final_rule not in governance:
        raise AuditError("GOVERNANCE.md Final definition changed; audit requires review")
    prerelease_rule = "A prerelease is not a stable conformance target unless release notes explicitly say otherwise."
    if prerelease_rule not in release_process:
        raise AuditError("release-candidate stability rule changed; audit requires review")

    release_classification = _validate_release(release)

    results: list[dict[str, Any]] = []
    for evidence in AEP_EVIDENCE:
        current_status = _aep_status(_read_text(current_root, evidence.rfc), evidence.aep)
        if current_status != "Accepted":
            raise AuditError(f"{evidence.aep} expected current status Accepted, got {current_status}")

        released_status = _aep_status(_read_text(release_root, evidence.rfc), evidence.aep)
        if released_status != "Accepted":
            raise AuditError(
                f"{evidence.aep} release-source status expected Accepted, got {released_status}"
            )

        released_paths = (
            *evidence.normative_specs,
            *evidence.requirement_indexes,
            *evidence.schemas,
            *evidence.tck_profiles,
        )
        _require_files(release_root, released_paths)
        _verify_profile_registration(release_root, evidence.tck_profiles)

        results.append(
            {
                "aep": evidence.aep,
                "currentStatus": current_status,
                "releasedStatus": released_status,
                "normativeSpecs": list(evidence.normative_specs),
                "requirementIndexes": list(evidence.requirement_indexes),
                "schemas": list(evidence.schemas),
                "tckProfiles": list(evidence.tck_profiles),
                "technicalFinalityEvidence": "PASS",
                "lifecycleEligibility": "REQUIRES_STABLE_FINALITY_DECISION",
                "reason": (
                    "Required normative/conformance assets are present and registered in the "
                    "published RC source, but the public release is a prerelease and explicitly "
                    "preserves Accepted/not-Final status."
                ),
            }
        )

    return {
        "schemaVersion": "avp-aep-final-eligibility/v1",
        "repository": EXPECTED_REPOSITORY,
        "auditedRelease": {
            "tag": EXPECTED_TAG,
            "commit": EXPECTED_RELEASE_COMMIT,
            "classification": release_classification,
        },
        "technicalFinalityEvidence": "PASS",
        "lifecycleEligibility": "REQUIRES_STABLE_FINALITY_DECISION",
        "aepResults": results,
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-root", type=Path, required=True)
    parser.add_argument("--release-root", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--release-json", type=Path)
    source.add_argument("--github-token")
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        release = (
            _load_release(args.release_json)
            if args.release_json
            else fetch_live_release_metadata(EXPECTED_REPOSITORY, EXPECTED_TAG, args.github_token)
        )
        result = audit(args.current_root.resolve(), args.release_root.resolve(), release)
    except AuditError as exc:
        print(f"AEP final eligibility audit failed: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

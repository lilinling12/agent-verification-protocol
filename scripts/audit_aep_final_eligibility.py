#!/usr/bin/env python3
"""Audit Alpha 2 AEP technical finality evidence and lifecycle eligibility.

This tool deliberately separates two questions that governance must not conflate:

1. Did a published release actually contain the normative specification and required
   conformance assets for an AEP?
2. Does the release policy make that publication a lifecycle-finality boundary?

The first question is evidence-driven. The second is governance-driven. A prerelease
can therefore have complete technical evidence while still requiring an explicit
stable/finality decision.

The script is intentionally standard-library only so it can run in governance CI
before project dependencies are installed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


EXPECTED_TAG = "v0.3.0-rc.1"
EXPECTED_RELEASE_COMMIT = "ef199124017b0dcc8c4a966d00c4f407760f9a06"
EXPECTED_REPOSITORY = "lilinling12/agent-verification-protocol"


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


def _validate_release(release: dict[str, Any]) -> tuple[bool, str]:
    if release.get("tag_name") != EXPECTED_TAG:
        raise AuditError("release tag does not match the audited RC")
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
    accepted_boundary = "remain accepted" in normalized and "not final" in normalized
    if not accepted_boundary:
        raise AuditError(
            "release body must explicitly preserve the Accepted/not-Final lifecycle boundary"
        )
    return True, "PUBLISHED_PRERELEASE_ACCEPTED_NOT_FINAL"


def audit(current_root: Path, release_root: Path, release: dict[str, Any]) -> dict[str, Any]:
    governance = _read_text(current_root, "GOVERNANCE.md")
    release_process = _read_text(current_root, "docs/RELEASE_PROCESS.md")

    if "`Final` — normative text and required conformance coverage are merged and released" not in governance:
        raise AuditError("GOVERNANCE.md Final definition changed; audit requires review")
    prerelease_rule = "A prerelease is not a stable conformance target unless release notes explicitly say otherwise."
    if prerelease_rule not in release_process:
        raise AuditError("release-candidate stability rule changed; audit requires review")

    _, release_classification = _validate_release(release)

    results: list[dict[str, Any]] = []
    for evidence in AEP_EVIDENCE:
        current_rfc = _read_text(current_root, evidence.rfc)
        current_status = _aep_status(current_rfc, evidence.aep)
        if current_status != "Accepted":
            raise AuditError(f"{evidence.aep} expected current status Accepted, got {current_status}")

        released_rfc = _read_text(release_root, evidence.rfc)
        released_status = _aep_status(released_rfc, evidence.aep)
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
                    "Required normative/conformance assets are present in the published RC source, "
                    "but the audited GitHub Release is a prerelease and explicitly preserves "
                    "Accepted/not-Final status."
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
    parser.add_argument("--release-json", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = audit(
            args.current_root.resolve(),
            args.release_root.resolve(),
            _load_release(args.release_json),
        )
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

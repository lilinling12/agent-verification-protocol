"""Validate the Alpha 2 AEP Final eligibility audit manifest fail-closed.

This validator does not decide protocol policy. It proves that the recorded audit
is internally consistent with repository state and prevents an undefined
prerelease policy from being represented as automatic AEP Final eligibility.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs/acceptance/alpha2-finalization-manifest.json"
EXPECTED_AEPS = {f"AEP-{index:04d}" for index in range(1, 9)}
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
STATUS_RE = re.compile(r"^- Status:\s*(\S+)\s*$", re.MULTILINE)
PROFILE_ID_RE = re.compile(r"^\s*(?:id|name):\s*([^#\s]+)", re.MULTILINE)


class ReadinessValidationError(ValueError):
    """Raised when the finalization-readiness evidence is inconsistent."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReadinessValidationError(message)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReadinessValidationError(f"cannot parse {path.relative_to(ROOT)}: {exc}") from exc
    _require(isinstance(value, dict), f"{path.relative_to(ROOT)} must contain an object")
    return value


def _repo_path(value: Any, field: str) -> Path:
    _require(isinstance(value, str) and value, f"{field} must be a non-empty repository path")
    path = Path(value)
    _require(not path.is_absolute() and ".." not in path.parts, f"{field} must stay inside the repository")
    resolved = ROOT / path
    _require(resolved.is_file(), f"{field} does not exist: {value}")
    return resolved


def _read_status(rfc_path: Path) -> str:
    text = rfc_path.read_text(encoding="utf-8")
    match = STATUS_RE.search(text)
    _require(match is not None, f"{rfc_path.relative_to(ROOT)} has no AEP Status metadata")
    return match.group(1)


def _profile_exists(profile_id: Any) -> None:
    _require(isinstance(profile_id, str) and profile_id, "tckProfile must be a non-empty string")
    profile_path = ROOT / "conformance/tck/profiles" / f"{profile_id}.yaml"
    _require(profile_path.is_file(), f"TCK profile does not exist: {profile_id}")


def validate_manifest(manifest: dict[str, Any]) -> None:
    _require(
        manifest.get("schemaVersion") == "avp-aep-finalization-readiness/v1",
        "unsupported finalization-readiness schemaVersion",
    )

    baseline = manifest.get("auditBaseline")
    _require(isinstance(baseline, dict), "auditBaseline must be an object")
    _require(baseline.get("repository") == "lilinling12/agent-verification-protocol", "unexpected repository identity")
    for field in ("mainCommit", "publishedSourceCommit"):
        value = baseline.get(field)
        _require(isinstance(value, str) and SHA40_RE.fullmatch(value) is not None, f"{field} must be exact lowercase SHA-40")
    _require(baseline.get("publishedTag") == "v0.3.0-rc.1", "unexpected publishedTag")
    _require(baseline.get("releaseClass") == "prerelease", "audit must remain bound to the published prerelease")
    release_acceptance = _repo_path(baseline.get("releaseAcceptance"), "auditBaseline.releaseAcceptance")
    acceptance_text = release_acceptance.read_text(encoding="utf-8")
    _require("Status: PASS" in acceptance_text, "release acceptance evidence is not PASS")
    _require(str(baseline["publishedSourceCommit"]) in acceptance_text, "release acceptance is not bound to publishedSourceCommit")

    policy = manifest.get("policy")
    _require(isinstance(policy, dict), "policy must be an object")
    _require(policy.get("governanceSource") == "GOVERNANCE.md", "governanceSource must be GOVERNANCE.md")
    _repo_path(policy.get("governanceSource"), "policy.governanceSource")
    _require(policy.get("prereleaseFinality") in {"UNDEFINED", "COUNTS_AS_RELEASED", "STABLE_RELEASE_REQUIRED"}, "invalid prereleaseFinality")
    _require(isinstance(policy.get("automaticFinalTransition"), bool), "automaticFinalTransition must be boolean")
    _require(policy.get("automaticFinalTransition") is False, "AEP Final transitions must never be automatic")

    prerelease_policy = policy["prereleaseFinality"]
    overall = manifest.get("overallConclusion")
    blockers = manifest.get("blockers")
    _require(isinstance(blockers, list) and all(isinstance(item, str) and item for item in blockers), "blockers must be a string list")
    if prerelease_policy == "UNDEFINED":
        _require(overall == "BLOCKED_ON_GOVERNANCE_CLARIFICATION", "undefined prerelease policy must block overall eligibility")
        _require("PRERELEASE_FINALITY_UNDEFINED" in blockers, "undefined prerelease policy must expose its blocker")
    else:
        _require("PRERELEASE_FINALITY_UNDEFINED" not in blockers, "resolved prerelease policy cannot retain undefined blocker")

    aeps = manifest.get("aeps")
    _require(isinstance(aeps, list), "aeps must be a list")
    ids = [item.get("id") for item in aeps if isinstance(item, dict)]
    _require(len(ids) == len(aeps), "every AEP entry must be an object with id")
    _require(len(ids) == len(set(ids)), "AEP ids must be unique")
    _require(set(ids) == EXPECTED_AEPS, "manifest must contain exactly AEP-0001 through AEP-0008")

    for entry in aeps:
        aep_id = entry["id"]
        _require(entry.get("expectedStatus") == "Accepted", f"{aep_id} expectedStatus must remain Accepted during audit")
        rfc_path = _repo_path(entry.get("rfc"), f"{aep_id}.rfc")
        _require(_read_status(rfc_path) == "Accepted", f"{aep_id} repository status is not Accepted")
        _repo_path(entry.get("spec"), f"{aep_id}.spec")
        _repo_path(entry.get("requirementIndex"), f"{aep_id}.requirementIndex")
        _repo_path(entry.get("reconciliation"), f"{aep_id}.reconciliation")
        _profile_exists(entry.get("tckProfile"))
        _require(entry.get("mechanicalReadiness") == "READY", f"{aep_id} mechanicalReadiness must be READY or the audit must be revised")

        eligibility = entry.get("finalEligibility")
        if prerelease_policy == "UNDEFINED":
            _require(
                eligibility == "BLOCKED_ON_GOVERNANCE_CLARIFICATION",
                f"{aep_id} cannot be Final-eligible while prerelease finality is undefined",
            )
        else:
            _require(
                eligibility in {"ELIGIBLE", "STABLE_RELEASE_REQUIRED", "BLOCKED"},
                f"{aep_id} has invalid finalEligibility for a resolved policy",
            )


def main() -> None:
    try:
        validate_manifest(_load_json(MANIFEST_PATH))
    except ReadinessValidationError as exc:
        raise SystemExit(f"AEP finalization readiness FAIL: {exc}") from exc
    print("AEP finalization readiness PASS")


if __name__ == "__main__":
    main()

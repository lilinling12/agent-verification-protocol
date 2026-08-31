#!/usr/bin/env python3
"""Plan installed-wheel TCK execution without conflating protocol candidates with runtime claims.

The stable normative surface is a release baseline: every stable profile MUST be
fully supported by the installed reference adapter. Active normative candidates
are different. Governance allows a complete Accepted-AEP authority slice to
exist before its reference implementation. A candidate is therefore either:

* fully supported by the installed reference adapter and executed; or
* completely unsupported and reported explicitly as implementation-pending.

Partial candidate support fails closed because it could make a half-implemented
profile look conformant. This script never changes TCK expectations and never
turns unsupported cases into PASS/SKIP results.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

import yaml

from avp_ref.tck_adapter.reference_composite import ReferenceConformanceAdapter


@dataclass(frozen=True, slots=True)
class ReferenceTCKPlan:
    """Profiles that must run and candidates that are not implemented yet."""

    run_profiles: tuple[str, ...]
    pending_candidate_profiles: tuple[str, ...]


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _profile_cases(profile_path: Path) -> frozenset[str]:
    document = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise ValueError(f"{profile_path} must contain a mapping")
    requirements = document.get("requirements")
    if not isinstance(requirements, Mapping):
        raise ValueError(f"{profile_path} is missing requirements")

    # Profile documents name requirements, while the global registry owns the
    # authoritative requirement -> case relation. This helper deliberately does
    # not infer case IDs from file names or provider/runtime behavior.
    mandatory = requirements.get("mandatory", [])
    conditional = requirements.get("conditional", [])
    if not isinstance(mandatory, list) or not isinstance(conditional, list):
        raise ValueError(f"{profile_path} requirement lists must be arrays")
    return frozenset(
        _require_string(item, f"{profile_path} requirement")
        for item in [*mandatory, *conditional]
    )


def _registry_case_ownership(registry_path: Path) -> dict[str, frozenset[str]]:
    document = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping) or not isinstance(document.get("cases"), list):
        raise ValueError(f"{registry_path} is missing cases")

    by_profile: dict[str, set[str]] = {}
    for item in document["cases"]:
        if not isinstance(item, Mapping):
            raise ValueError(f"{registry_path} case entry must be a mapping")
        profile = _require_string(item.get("profile"), "registry case profile")
        case_id = _require_string(item.get("id"), "registry case id")
        by_profile.setdefault(profile, set()).add(case_id)
    return {profile: frozenset(case_ids) for profile, case_ids in by_profile.items()}


def classify_profiles(
    *,
    stable_profiles: Iterable[str],
    candidate_profiles: Iterable[str],
    profile_case_ids: Mapping[str, frozenset[str]],
    supported_case_ids: frozenset[str],
) -> ReferenceTCKPlan:
    """Return a fail-closed reference-execution plan.

    Stable profiles must be fully implemented. Candidate profiles may be fully
    implemented or not implemented at all. Partial candidate support is an
    error because it is neither an honest pending state nor full conformance.
    """

    stable = frozenset(stable_profiles)
    candidates = frozenset(candidate_profiles)
    overlap = stable & candidates
    if overlap:
        raise ValueError(f"profiles cannot be both stable and candidate: {sorted(overlap)}")

    expected = stable | candidates
    actual = frozenset(profile_case_ids)
    if actual != expected:
        raise ValueError(
            "TCK profile ownership mismatch "
            f"missing={sorted(expected - actual)} extra={sorted(actual - expected)}"
        )

    run: list[str] = []
    pending: list[str] = []

    for profile in sorted(stable):
        required = profile_case_ids[profile]
        unsupported = required - supported_case_ids
        if unsupported:
            raise ValueError(
                f"stable profile {profile} is not fully supported by the reference adapter: "
                f"{sorted(unsupported)}"
            )
        run.append(profile)

    for profile in sorted(candidates):
        required = profile_case_ids[profile]
        supported = required & supported_case_ids
        if not supported:
            pending.append(profile)
            continue
        unsupported = required - supported_case_ids
        if unsupported:
            raise ValueError(
                f"candidate profile {profile} is only partially supported by the reference adapter: "
                f"supported={sorted(supported)} unsupported={sorted(unsupported)}"
            )
        run.append(profile)

    return ReferenceTCKPlan(tuple(run), tuple(pending))


def build_plan(repository_root: Path) -> ReferenceTCKPlan:
    """Build the plan from governed repository metadata and installed adapter support."""

    stable_matrix = json.loads(
        (repository_root / "docs/reconciliation/v0.1/normative-surface-matrix.json").read_text(
            encoding="utf-8"
        )
    )
    candidate_registry = json.loads(
        (repository_root / "docs/reconciliation/normative-candidates/registry.json").read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(stable_matrix.get("domains"), list):
        raise ValueError("stable normative matrix is missing domains")
    if not isinstance(candidate_registry.get("candidates"), list):
        raise ValueError("normative candidate registry is missing candidates")

    stable_profiles = [
        _require_string(item.get("profile"), "stable domain profile")
        for item in stable_matrix["domains"]
        if isinstance(item, Mapping)
    ]
    candidate_profiles = [
        _require_string(item.get("profile"), "candidate profile")
        for item in candidate_registry["candidates"]
        if isinstance(item, Mapping)
    ]

    profile_dir = repository_root / "conformance/tck/profiles"
    profile_paths = sorted(profile_dir.glob("*.yaml"))
    profile_names = {path.stem for path in profile_paths}
    expected_names = set(stable_profiles) | set(candidate_profiles)
    if profile_names != expected_names:
        raise ValueError(
            "profile file inventory mismatch "
            f"missing={sorted(expected_names - profile_names)} "
            f"extra={sorted(profile_names - expected_names)}"
        )

    # Validate that each profile document is structurally readable and that its
    # requirement list is non-empty. Requirement-to-case authority is then read
    # from the already-governed central TCK registry.
    for path in profile_paths:
        if not _profile_cases(path):
            raise ValueError(f"profile {path.stem} has no requirements")

    profile_case_ids = _registry_case_ownership(
        repository_root / "conformance/tck/registry.yaml"
    )
    adapter = ReferenceConformanceAdapter()
    return classify_profiles(
        stable_profiles=stable_profiles,
        candidate_profiles=candidate_profiles,
        profile_case_ids=profile_case_ids,
        supported_case_ids=adapter.supported_case_ids,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    plan = build_plan(args.repository_root.resolve())
    document = {
        "runProfiles": list(plan.run_profiles),
        "pendingCandidateProfiles": list(plan.pending_candidate_profiles),
    }
    rendered = json.dumps(document, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

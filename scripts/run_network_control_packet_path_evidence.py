#!/usr/bin/env python3
"""Run one qualified PTL-002 packet-path evidence case on native Linux."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from acceptance.network_control.evidence_core import ArtifactStore  # noqa: E402
from acceptance.network_control.packet_path.evidence_lane import (  # noqa: E402
    assert_expected_assessment,
    lane_case,
)
from acceptance.network_control.packet_path.github_qualification import (  # noqa: E402
    verify_github_qualification,
)
from acceptance.network_control.packet_path.live_evidence import (  # noqa: E402
    PacketPathLiveEvidenceLab,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description=(
            "Execute one concrete PTL-002 Linux packet-path evidence case after "
            "verifying the same trusted-main qualification binding."
        )
    )
    value.add_argument("--case", required=True)
    value.add_argument("--run-id", required=True)
    value.add_argument("--qualification-run-id", required=True)
    value.add_argument("--qualification", required=True, type=Path)
    value.add_argument("--semantic-baseline-commit", required=True)
    value.add_argument("--artifact-dir", required=True, type=Path)
    value.add_argument("--workspace", type=Path, default=ROOT)
    value.add_argument("--observation-budget-ms", type=int, default=1000)
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.observation_budget_ms <= 0:
        raise SystemExit("--observation-budget-ms must be positive")
    if not sys.platform.startswith("linux"):
        raise SystemExit("PTL-002 packet-path evidence requires native Linux")
    if os.geteuid() != 0:
        raise SystemExit(
            "PTL-002 packet-path evidence requires existing euid 0; "
            "this command never acquires privilege"
        )
    if not args.qualification.is_file():
        raise SystemExit("--qualification must name a retained same-run qualification file")

    case = lane_case(args.case)
    qualification = verify_github_qualification(
        args.qualification.read_bytes(),
        expected_semantic_baseline_commit=args.semantic_baseline_commit,
        expected_run_id=args.qualification_run_id,
    )
    store = ArtifactStore(args.artifact_dir)
    lab = PacketPathLiveEvidenceLab(
        workspace=args.workspace,
        artifact_store=store,
        run_id=args.run_id,
        semantic_baseline_commit=args.semantic_baseline_commit,
        observation_budget_ns=args.observation_budget_ms * 1_000_000,
        capture_assurance=qualification.capture_assurance,
        negative_mode=case.negative_mode,
    )
    result = lab.execute_evidence()
    assert_expected_assessment(
        case=case,
        classification=result.assessment.classification,
        primary_problem=result.assessment.primary_problem,
    )
    output = {
        "format": "avp-project-network-packet-path-case-result-v0.1",
        "case": case.slug,
        "runId": args.run_id,
        "qualificationRunId": qualification.run_id,
        "qualificationLocalSha256": qualification.local_qualification_sha256,
        "semanticBaselineCommit": args.semantic_baseline_commit,
        "negativeMode": None if case.negative_mode is None else case.negative_mode.value,
        "assessment": {
            "classification": result.assessment.classification.value,
            "primaryProblem": result.assessment.primary_problem,
            "secondaryProblems": list(result.assessment.secondary_problems),
        },
        "sealedPlan": {
            "sha256": result.sealed_plan_ref.sha256,
            "size": result.sealed_plan_ref.size,
            "logicalRole": result.sealed_plan_ref.logical_role,
        },
        "materializationProvenance": {
            "sha256": result.materialization_provenance_ref.sha256,
            "size": result.materialization_provenance_ref.size,
            "logicalRole": result.materialization_provenance_ref.logical_role,
        },
        "implementationRecord": {
            "sha256": result.implementation_record_ref.sha256,
            "size": result.implementation_record_ref.size,
            "logicalRole": result.implementation_record_ref.logical_role,
        },
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

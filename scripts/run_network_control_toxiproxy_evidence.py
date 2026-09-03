#!/usr/bin/env python3
"""Run one opt-in TEL-002 native-Linux Toxiproxy evidence matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from acceptance.network_control.evidence_core import ArtifactStore, ExchangeProgram  # noqa: E402
from acceptance.network_control.toxiproxy_evidence import NegativeMode  # noqa: E402
from acceptance.network_control.toxiproxy_live_execution import execute_live_matrix  # noqa: E402
from acceptance.network_control.toxiproxy_live_lab import ToxiproxyLiveLab  # noqa: E402
from acceptance.network_control.witness_evidence import CaptureAssurance  # noqa: E402


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description=(
            "Execute one controlled TEL-002 Toxiproxy evidence matrix. "
            "This command is opt-in and requires explicit reviewed capture-assurance assertions."
        )
    )
    value.add_argument("--run-id", required=True)
    value.add_argument("--semantic-baseline-commit", required=True)
    value.add_argument("--artifact-dir", required=True, type=Path)
    value.add_argument("--workspace", type=Path, default=ROOT)
    value.add_argument("--observation-budget-ms", type=int, default=1000)
    value.add_argument(
        "--negative-mode",
        choices=[mode.value for mode in NegativeMode],
        default=None,
    )
    value.add_argument("--assert-egress-coverage", action="store_true")
    value.add_argument("--assert-directionality", action="store_true")
    value.add_argument("--assert-offload-normalization", action="store_true")
    value.add_argument("--assert-pre-syn-gap-closed", action="store_true")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.observation_budget_ms <= 0:
        raise SystemExit("--observation-budget-ms must be positive")

    assertions = (
        args.assert_egress_coverage,
        args.assert_directionality,
        args.assert_offload_normalization,
        args.assert_pre_syn_gap_closed,
    )
    if not all(assertions):
        raise SystemExit(
            "live TEL-002 evidence requires all four explicit reviewed capture-assurance assertions"
        )

    assurance = CaptureAssurance(
        egress_coverage_verified=True,
        directionality_verified=True,
        offload_normalization_verified=True,
        pre_syn_connect_gap_closed=True,
    )
    program = ExchangeProgram(
        program_id="tel002-exact-byte-v0.1",
        request_prefix=b"AVP-TEL002-REQ\x00",
        request_suffix=b"\x00END",
        response_prefix=b"AVP-TEL002-RESP\x00",
        response_suffix=b"\x00END",
    )
    store = ArtifactStore(args.artifact_dir)
    lab = ToxiproxyLiveLab(
        workspace=args.workspace,
        artifact_store=store,
        run_id=args.run_id,
        semantic_baseline_commit=args.semantic_baseline_commit,
        exchange_program=program,
        observation_budget_ns=args.observation_budget_ms * 1_000_000,
        capture_assurance=assurance,
    )
    mode = None if args.negative_mode is None else NegativeMode(args.negative_mode)
    result = execute_live_matrix(lab, negative_mode=mode)
    output = {
        "runId": args.run_id,
        "negativeMode": args.negative_mode,
        "assessment": {
            "classification": result.assessment.classification.value,
            "primaryProblem": result.assessment.primary_problem,
            "secondaryProblems": list(result.assessment.secondary_problems),
        },
        "materializationProvenance": {
            "sha256": result.materialization_provenance_ref.sha256,
            "size": result.materialization_provenance_ref.size,
        },
        "implementationRecord": {
            "sha256": result.terminating_result.implementation_record_ref.sha256,
            "size": result.terminating_result.implementation_record_ref.size,
        },
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

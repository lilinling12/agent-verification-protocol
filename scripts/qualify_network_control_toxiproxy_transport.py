#!/usr/bin/env python3
"""Qualify the pinned Toxiproxy transport contract before TEL-003 matrix execution."""

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
from acceptance.network_control.toxiproxy_transport_qualification import (  # noqa: E402
    execute_toxiproxy_transport_qualification,
)
from acceptance.network_control.verified_live_labs import VerifiedToxiproxyLiveLab  # noqa: E402
from acceptance.network_control.witness_evidence import CaptureAssurance  # noqa: E402


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description=(
            "Qualify the exact pinned Toxiproxy transport behavior required by the "
            "project-local terminating evidence lab before executing the full matrix."
        )
    )
    value.add_argument("--run-id", required=True)
    value.add_argument("--semantic-baseline-commit", required=True)
    value.add_argument("--artifact-dir", required=True, type=Path)
    value.add_argument("--output", required=True, type=Path)
    value.add_argument("--workspace", type=Path, default=ROOT)
    value.add_argument("--observation-budget-ms", type=int, default=1000)
    value.add_argument("--assert-egress-coverage", action="store_true")
    value.add_argument("--assert-directionality", action="store_true")
    value.add_argument("--assert-offload-normalization", action="store_true")
    value.add_argument("--assert-pre-syn-gap-closed", action="store_true")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.observation_budget_ms <= 0:
        raise SystemExit("--observation-budget-ms must be positive")
    if not all(
        (
            args.assert_egress_coverage,
            args.assert_directionality,
            args.assert_offload_normalization,
            args.assert_pre_syn_gap_closed,
        )
    ):
        raise SystemExit(
            "Toxiproxy transport qualification requires all four reviewed capture-assurance assertions"
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
    lab = VerifiedToxiproxyLiveLab(
        workspace=args.workspace,
        artifact_store=ArtifactStore(args.artifact_dir),
        run_id=args.run_id,
        semantic_baseline_commit=args.semantic_baseline_commit,
        exchange_program=program,
        observation_budget_ns=args.observation_budget_ms * 1_000_000,
        capture_assurance=assurance,
    )
    result = execute_toxiproxy_transport_qualification(lab)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    exact = json.dumps(result.document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    args.output.write_bytes(exact)
    print(exact.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

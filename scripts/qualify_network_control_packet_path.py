#!/usr/bin/env python3
"""Run and bind one trusted-main PTL-002 packet-path qualification."""

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

from acceptance.network_control.packet_path.github_qualification import (  # noqa: E402
    build_github_qualification,
    verify_github_qualification,
)
from acceptance.network_control.packet_path.local_qualification import (  # noqa: E402
    PacketPathLocalQualification,
)
from acceptance.network_control.packet_path.process_environment import (  # noqa: E402
    sanitize_packet_path_process_environment,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description=(
            "Execute one native-Linux packet-path qualification and bind its exact "
            "result to the trusted repository commit used by PTL-002."
        )
    )
    value.add_argument("--run-id", required=True)
    value.add_argument("--semantic-baseline-commit", required=True)
    value.add_argument("--output", required=True, type=Path)
    value.add_argument("--workspace", type=Path, default=ROOT)
    value.add_argument("--observation-budget-ms", type=int, default=1000)
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.observation_budget_ms <= 0:
        raise SystemExit("--observation-budget-ms must be positive")
    if not sys.platform.startswith("linux"):
        raise SystemExit("PTL-002 packet-path qualification requires native Linux")
    if os.geteuid() != 0:
        raise SystemExit(
            "PTL-002 packet-path qualification requires existing euid 0; "
            "this command never acquires privilege"
        )

    sanitize_packet_path_process_environment(workspace=args.workspace)
    qualification = PacketPathLocalQualification(
        workspace=args.workspace,
        run_id=args.run_id,
        semantic_baseline_commit=args.semantic_baseline_commit,
        observation_budget_ns=args.observation_budget_ms * 1_000_000,
    )
    local_document = qualification.execute()
    exact = build_github_qualification(
        local_document=local_document,
        semantic_baseline_commit=args.semantic_baseline_commit,
    )
    # Re-verify before publication so the CLI cannot emit a document the matrix
    # runner would refuse for the same exact run/commit binding.
    verify_github_qualification(
        exact,
        expected_semantic_baseline_commit=args.semantic_baseline_commit,
        expected_run_id=args.run_id,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(exact)
    print(exact.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

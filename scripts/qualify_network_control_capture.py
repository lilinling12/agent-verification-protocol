#!/usr/bin/env python3
"""Qualify the exact Linux capture boundary before privileged TEL-003 execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from acceptance.network_control.verified_live_labs import VerifiedCaptureQualification  # noqa: E402


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Run the privileged Network Control AF_PACKET qualification canaries."
    )
    value.add_argument("--run-id", required=True)
    value.add_argument("--artifact-dir", required=True, type=Path)
    value.add_argument("--workspace", default=ROOT, type=Path)
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    result = VerifiedCaptureQualification(
        workspace=args.workspace,
        run_id=args.run_id,
    ).execute()

    raw_index: list[dict[str, object]] = []
    for filename, payload in result.raw_artifacts:
        path = args.artifact_dir / filename
        path.write_bytes(payload)
        raw_index.append(
            {
                "path": filename,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size": len(payload),
            }
        )

    document = dict(result.document)
    document["rawArtifacts"] = raw_index
    exact = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    output = args.artifact_dir / "qualification.json"
    output.write_bytes(exact)
    print(exact.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

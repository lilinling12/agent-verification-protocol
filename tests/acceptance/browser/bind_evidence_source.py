"""Bind non-normative Browser evidence to the exact checked-out source commit.

Pull-request workflows normally expose a synthetic merge commit as ``GITHUB_SHA``.
Acceptance evidence must instead identify the exact reviewed PR head.  This helper
verifies that the working tree was checked out at the expected source SHA before
stamping the evidence document.  A mismatch fails closed rather than silently
rewriting provenance.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def current_head_sha() -> str:
    """Return the exact Git commit checked out in the evidence workspace."""

    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def bind_evidence_source(path: Path, expected_sha: str) -> None:
    """Verify exact checkout identity and stamp one evidence JSON document."""

    expected_sha = expected_sha.strip().lower()
    if len(expected_sha) != 40 or any(character not in "0123456789abcdef" for character in expected_sha):
        raise ValueError("expected source SHA must be a full 40-character lowercase hexadecimal commit id")

    observed_sha = current_head_sha().lower()
    if observed_sha != expected_sha:
        raise RuntimeError(
            "Browser evidence checkout does not match the expected source head: "
            f"expected {expected_sha}, observed {observed_sha}"
        )

    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    existing = document.get("repositorySha")
    if existing not in (None, expected_sha):
        # A pull_request runner may initially record GitHub's synthetic merge SHA.
        # Rebinding is permitted only after exact checkout identity has been proven
        # above; other pre-existing values are retained in provenance diagnostics.
        document["preBindingRepositorySha"] = existing
    document["repositorySha"] = expected_sha
    document["sourceBinding"] = {
        "mode": "exact-checked-out-head",
        "verified": True,
    }
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args()
    bind_evidence_source(args.path, args.expected_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

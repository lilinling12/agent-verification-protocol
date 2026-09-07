#!/usr/bin/env python3
"""Build the retained NPR-011 cross-mechanism reassessment record.

The source ZIPs are independently adopted GitHub Actions artifacts. They are
inputs to this one evidence-construction command and are never copied into the
repository. The committed output retains the portable observations needed by the
current comparator plus exact source lineage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from acceptance.network_control.cross_mechanism import (
    SemanticBinding,
    SourceExpectation,
    build_reassessment_record,
    encode_reassessment_archive,
    verify_reassessment_record,
)

_REPOSITORY = "lilinling12/agent-verification-protocol"
_CANDIDATE_PARENT = "0ccac4339ed4c8f773b6413428e3df3b15f6b79e"
_AEP_PATH = "rfcs/AEP-0012-network-control-resource-profile.md"
_AEP_GIT_BLOB = "0b5ebdddb45533cf91a7bc264dcfe7548b54391c"
_COMPARATOR_PATH = "tests/acceptance/network_control/portable_comparator.py"
_COMPARATOR_GIT_BLOB = "39169f40083e204560606cd9db0d8f1a1dda57bd"

_TERMINATING = SourceExpectation(
    mechanism_class="terminating-intercepting",
    artifact_id="9926819468",
    zip_sha256="381f28d3357c210e813f3993c620b3404f9e205cb18cd88f2ad2ae67f1c37d02",
    source_commit="bb63d0859444d76e53743aae409f424e47178eab",
    workflow_run_id="33846543402",
    manifest_format="avp-project-tel003-github-evidence-manifest-v0.1",
    manifest_entries=452,
    historical_comparator_blob="05c4025f8ed839e367683f736d8822c13fe1bc92",
)
_PACKET_PATH = SourceExpectation(
    mechanism_class="packet-path",
    artifact_id="9987837192",
    zip_sha256="3beee7b92d728650c9cb22fa00702d8e963900eef8a4a6dec51e223ba42896d6",
    source_commit="f477afeeb780cb06cd4df90aa11a4b316887c981",
    workflow_run_id="34028504186",
    manifest_format="avp-project-network-packet-path-github-evidence-manifest-v0.1",
    manifest_entries=361,
    historical_comparator_blob="39169f40083e204560606cd9db0d8f1a1dda57bd",
)
_BINDING = SemanticBinding(
    aep_path=_AEP_PATH,
    aep_git_blob=_AEP_GIT_BLOB,
    current_comparator_path=_COMPARATOR_PATH,
    current_comparator_git_blob=_COMPARATOR_GIT_BLOB,
    candidate_parent_commit=_CANDIDATE_PARENT,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--terminating-zip", type=Path, required=True)
    parser.add_argument("--packet-path-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--skip-checkout-binding",
        action="store_true",
        help="Only for isolated fixture tests without a Git checkout.",
    )
    args = parser.parse_args()

    if not args.skip_checkout_binding:
        _verify_checkout_blob(_AEP_PATH, _AEP_GIT_BLOB)
        _verify_checkout_blob(_COMPARATOR_PATH, _COMPARATOR_GIT_BLOB)

    exact = build_reassessment_record(
        terminating_zip=args.terminating_zip,
        terminating_expectation=_TERMINATING,
        packet_path_zip=args.packet_path_zip,
        packet_path_expectation=_PACKET_PATH,
        semantic_binding=_BINDING,
    )
    verify_reassessment_record(exact, semantic_binding=_BINDING)
    archive = encode_reassessment_archive(exact)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(archive)

    print(
        json.dumps(
            {
                "repository": _REPOSITORY,
                "format": "avp-project-network-cross-mechanism-reassessment-v0.1",
                "jsonSize": len(exact),
                "jsonSha256": hashlib.sha256(exact).hexdigest(),
                "archiveSize": len(archive),
                "archiveSha256": hashlib.sha256(archive).hexdigest(),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


def _verify_checkout_blob(path: str, expected: str) -> None:
    completed = subprocess.run(
        ["git", "rev-parse", f"HEAD:{path}"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    actual = completed.stdout.strip()
    if actual != expected:
        raise RuntimeError(f"checkout Git blob drift for {path}: {actual} != {expected}")


if __name__ == "__main__":
    raise SystemExit(main())

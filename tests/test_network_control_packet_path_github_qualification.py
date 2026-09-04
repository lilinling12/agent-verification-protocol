"""Ordinary-CI coverage for the PTL-002 trusted-main qualification binding."""

from __future__ import annotations

import json
import unittest

from acceptance.network_control.evidence_core import EvidenceMaterializationError
from acceptance.network_control.packet_path.github_qualification import (
    build_github_qualification,
    verify_github_qualification,
)

_COMMIT = "5fef4b1844f071649fb326ed276c960f640df9b9"
_RUN_ID = "ptl002-qualification-test"


def _ready_local_document() -> dict[str, object]:
    return {
        "format": "avp-project-network-packet-path-local-qualification-v0.1",
        "runId": _RUN_ID,
        "ready": True,
        "problems": [],
        "captureAssurance": {
            "egressCoverageVerified": True,
            "directionalityVerified": True,
            "offloadNormalizationVerified": True,
            "preSynConnectGapClosed": True,
        },
        "facts": [
            {
                "property": "native-linux",
                "source": "evaluator-preflight",
                "verified": True,
                "detail": "test fixture",
            }
        ],
        "cleanup": {
            "problems": [],
            "residualResources": [],
        },
    }


class PacketPathGitHubQualificationTests(unittest.TestCase):
    def test_ready_local_qualification_is_bound_to_exact_commit_and_run(self) -> None:
        exact = build_github_qualification(
            local_document=_ready_local_document(),
            semantic_baseline_commit=_COMMIT,
        )

        verified = verify_github_qualification(
            exact,
            expected_semantic_baseline_commit=_COMMIT,
            expected_run_id=_RUN_ID,
        )

        self.assertEqual(verified.semantic_baseline_commit, _COMMIT)
        self.assertEqual(verified.run_id, _RUN_ID)
        self.assertEqual(verified.capture_assurance.problems(), ())
        self.assertEqual(len(verified.local_qualification_sha256), 64)

    def test_commit_or_run_drift_is_rejected(self) -> None:
        exact = build_github_qualification(
            local_document=_ready_local_document(),
            semantic_baseline_commit=_COMMIT,
        )

        with self.assertRaises(EvidenceMaterializationError):
            verify_github_qualification(
                exact,
                expected_semantic_baseline_commit="0" * 40,
                expected_run_id=_RUN_ID,
            )
        with self.assertRaises(EvidenceMaterializationError):
            verify_github_qualification(
                exact,
                expected_semantic_baseline_commit=_COMMIT,
                expected_run_id="different-run",
            )

    def test_unready_or_incomplete_capture_assurance_is_rejected(self) -> None:
        local = _ready_local_document()
        local["ready"] = False
        local["problems"] = ["qualification-failed"]
        exact = build_github_qualification(
            local_document=local,
            semantic_baseline_commit=_COMMIT,
        )
        with self.assertRaises(EvidenceMaterializationError):
            verify_github_qualification(
                exact,
                expected_semantic_baseline_commit=_COMMIT,
                expected_run_id=_RUN_ID,
            )

        local = _ready_local_document()
        assurance = dict(local["captureAssurance"])
        assurance["directionalityVerified"] = False
        local["captureAssurance"] = assurance
        exact = build_github_qualification(
            local_document=local,
            semantic_baseline_commit=_COMMIT,
        )
        with self.assertRaises(EvidenceMaterializationError):
            verify_github_qualification(
                exact,
                expected_semantic_baseline_commit=_COMMIT,
                expected_run_id=_RUN_ID,
            )

    def test_tampering_embedded_local_qualification_breaks_content_binding(self) -> None:
        exact = build_github_qualification(
            local_document=_ready_local_document(),
            semantic_baseline_commit=_COMMIT,
        )
        document = json.loads(exact)
        document["localQualification"]["facts"].append(
            {
                "property": "tampered",
                "source": "test",
                "verified": True,
                "detail": "must invalidate digest",
            }
        )
        tampered = json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        with self.assertRaises(EvidenceMaterializationError):
            verify_github_qualification(
                tampered,
                expected_semantic_baseline_commit=_COMMIT,
                expected_run_id=_RUN_ID,
            )

    def test_boolean_fields_do_not_accept_truthy_strings(self) -> None:
        local = _ready_local_document()
        local["ready"] = "true"
        with self.assertRaises(EvidenceMaterializationError):
            build_github_qualification(
                local_document=local,
                semantic_baseline_commit=_COMMIT,
            )

        local = _ready_local_document()
        assurance = dict(local["captureAssurance"])
        assurance["egressCoverageVerified"] = "true"
        local["captureAssurance"] = assurance
        with self.assertRaises(EvidenceMaterializationError):
            build_github_qualification(
                local_document=local,
                semantic_baseline_commit=_COMMIT,
            )


if __name__ == "__main__":
    unittest.main()

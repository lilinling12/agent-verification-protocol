"""Ordinary-CI coverage for the PTL-002 packet-path evidence-lane contract."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from acceptance.network_control.evidence_core import AssessmentClass, EvidenceMaterializationError
from acceptance.network_control.packet_path.evidence_lane import (
    assert_expected_assessment,
    build_execution_manifest,
    lane_case,
    packet_path_lane_cases,
    parse_front_initiations,
    verify_execution_manifest,
)
from acceptance.network_control.packet_path.negative_assemblies import PacketPathNegativeMode


class PacketPathEvidenceLaneTests(unittest.TestCase):
    def test_matrix_contains_positive_and_each_required_negative_exactly_once(self) -> None:
        cases = packet_path_lane_cases()

        self.assertEqual(cases[0].slug, "positive")
        self.assertIsNone(cases[0].negative_mode)
        self.assertEqual(
            {case.negative_mode for case in cases[1:]},
            set(PacketPathNegativeMode),
        )
        self.assertEqual(len({case.slug for case in cases}), len(cases))
        self.assertEqual(len(cases), 1 + len(PacketPathNegativeMode))

    def test_reviewed_expected_assessments_are_fixed_outside_negative_assemblies(self) -> None:
        assert_expected_assessment(
            case=lane_case("positive"),
            classification=AssessmentClass.SATISFIED,
            primary_problem=None,
        )
        assert_expected_assessment(
            case=lane_case("hidden-retry-fallback"),
            classification=AssessmentClass.SEMANTIC_VIOLATION,
            primary_problem="C10:front-initiation-cardinality",
        )

        with self.assertRaises(EvidenceMaterializationError):
            assert_expected_assessment(
                case=lane_case("collateral-target"),
                classification=AssessmentClass.SATISFIED,
                primary_problem=None,
            )

    def test_front_witness_parser_is_strict_and_keeps_capture_drop_as_validity_problem(self) -> None:
        facts = parse_front_initiations(
            {
                "channelFacts": [
                    {
                        "channel": "W-front",
                        "totalInitiations": 1,
                        "expectedTargetInitiations": 1,
                        "alternateTargetInitiations": 0,
                        "rawSynPackets": 2,
                        "retransmittedSynPackets": 1,
                    }
                ],
                "validityProblems": [],
                "captureDrops": 2,
            }
        )

        self.assertEqual(facts.channel, "W-front")
        self.assertEqual(facts.total_initiations, 1)
        self.assertEqual(facts.validity_problems, ("capture-drops:2",))

        with self.assertRaises(EvidenceMaterializationError):
            parse_front_initiations(
                {
                    "channelFacts": [
                        {
                            "channel": "W-front",
                            "totalInitiations": True,
                            "expectedTargetInitiations": 1,
                            "alternateTargetInitiations": 0,
                            "rawSynPackets": 1,
                            "retransmittedSynPackets": 0,
                        }
                    ],
                    "validityProblems": [],
                    "captureDrops": 0,
                }
            )

    def test_execution_manifest_is_exact_content_addressed_and_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "matrix" / "positive").mkdir(parents=True)
            result = root / "matrix" / "positive" / "result.json"
            result.write_text('{"assessment":"SATISFIED"}', encoding="utf-8")

            exact = build_execution_manifest(
                root=root,
                repository="lilinling12/agent-verification-protocol",
                commit="5fef4b1844f071649fb326ed276c960f640df9b9",
                run_id="123",
                run_attempt="1",
                workflow="Network Control Packet-Path Privileged Evidence",
            )
            document = json.loads(exact)
            self.assertEqual(
                document["format"],
                "avp-project-network-packet-path-github-evidence-manifest-v0.1",
            )
            self.assertEqual(document["files"][0]["path"], "matrix/positive/result.json")
            verify_execution_manifest(root=root, exact_bytes=exact)

            result.write_text('{"assessment":"changed"}', encoding="utf-8")
            with self.assertRaises(EvidenceMaterializationError):
                verify_execution_manifest(root=root, exact_bytes=exact)

    def test_manifest_rejects_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "evidence.txt").write_text("evidence", encoding="utf-8")
            exact = json.dumps(
                {
                    "format": "avp-project-network-packet-path-github-evidence-manifest-v0.1",
                    "files": [
                        {
                            "path": "../outside.txt",
                            "sha256": "0" * 64,
                            "size": 0,
                        }
                    ],
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")

            with self.assertRaises(EvidenceMaterializationError):
                verify_execution_manifest(root=root, exact_bytes=exact)


if __name__ == "__main__":
    unittest.main()

"""Unit checks for privileged Network Control capture qualification invariants."""

from __future__ import annotations

import unittest

from acceptance.network_control.capture_qualification import (
    QualificationTopology,
    _require_counts,
    _require_provisional_validity,
)
from acceptance.network_control.toxiproxy_binding import ToxiproxyPrerequisiteError


class QualificationTopologyTests(unittest.TestCase):
    def test_topology_is_deterministic_private_and_separate_from_tel002_pools(self) -> None:
        first = QualificationTopology.for_run("qualification-run")
        second = QualificationTopology.for_run("qualification-run")
        self.assertEqual(first, second)
        self.assertTrue(first.source.startswith("10."))
        second_octet = int(first.source.split(".")[1])
        self.assertGreaterEqual(second_octet, 192)
        self.assertLessEqual(second_octet, 223)
        self.assertNotEqual(first.source, first.expected_target)
        self.assertNotEqual(first.expected_target, first.alternate_target)
        self.assertTrue(first.subnet.endswith(".0/28"))

    def test_empty_run_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            QualificationTopology.for_run("")


class QualificationProvisionalValidityTests(unittest.TestCase):
    def test_exact_unverified_assurance_markers_are_accepted(self) -> None:
        _require_provisional_validity(
            [
                "egress-coverage-unverified",
                "directionality-unverified",
                "offload-normalization-unverified",
                "pre-syn-connect-gap-unclosed",
            ],
            scope="witness",
        )

    def test_additional_capture_problem_fails_closed(self) -> None:
        with self.assertRaises(ToxiproxyPrerequisiteError):
            _require_provisional_validity(
                [
                    "egress-coverage-unverified",
                    "directionality-unverified",
                    "offload-normalization-unverified",
                    "pre-syn-connect-gap-unclosed",
                    "capture-drops=1",
                ],
                scope="witness",
            )

    def test_missing_provisional_marker_fails_closed(self) -> None:
        with self.assertRaises(ToxiproxyPrerequisiteError):
            _require_provisional_validity(
                [
                    "egress-coverage-unverified",
                    "directionality-unverified",
                    "offload-normalization-unverified",
                ],
                scope="channel",
            )


class QualificationCountTests(unittest.TestCase):
    @staticmethod
    def document(*, total: int, expected: int, alternate: int, raw: int) -> dict[str, object]:
        return {
            "totalInitiations": total,
            "expectedTargetInitiations": expected,
            "alternateTargetInitiations": alternate,
            "rawSynPackets": raw,
        }

    def test_exact_expected_counts_are_accepted(self) -> None:
        _require_counts(
            self.document(total=2, expected=1, alternate=1, raw=2),
            total=2,
            expected=1,
            alternate=1,
        )

    def test_normalized_count_mismatch_fails_closed(self) -> None:
        with self.assertRaises(ToxiproxyPrerequisiteError):
            _require_counts(
                self.document(total=1, expected=1, alternate=0, raw=1),
                total=2,
                expected=2,
                alternate=0,
            )

    def test_raw_syn_count_below_normalized_count_fails_closed(self) -> None:
        with self.assertRaises(ToxiproxyPrerequisiteError):
            _require_counts(
                self.document(total=2, expected=2, alternate=0, raw=1),
                total=2,
                expected=2,
                alternate=0,
            )


if __name__ == "__main__":
    unittest.main()

"""Unit checks for same-run duplicate-SYN capture normalization qualification."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from acceptance.network_control.capture_qualification import (
    CaptureQualification,
    CaptureQualificationResult,
)
from acceptance.network_control.capture_qualification_retransmission import (
    RetransmissionQualifiedCaptureQualification,
    _require_duplicate_syn_normalization,
)
from acceptance.network_control.toxiproxy_binding import ToxiproxyPrerequisiteError


class DuplicateSynNormalizationTests(unittest.TestCase):
    @staticmethod
    def document(
        *,
        total: int = 1,
        expected: int = 1,
        alternate: int = 0,
        raw: int = 2,
        retransmitted: int = 1,
    ) -> dict[str, object]:
        return {
            "totalInitiations": total,
            "expectedTargetInitiations": expected,
            "alternateTargetInitiations": alternate,
            "rawSynPackets": raw,
            "retransmittedSynPackets": retransmitted,
        }

    def test_two_identical_raw_syns_normalize_to_one_initiation(self) -> None:
        _require_duplicate_syn_normalization(self.document())

    def test_extra_virtualized_duplicate_raw_syns_are_still_grouped(self) -> None:
        _require_duplicate_syn_normalization(self.document(raw=4, retransmitted=3))

    def test_second_normalized_initiation_fails_closed(self) -> None:
        with self.assertRaises(ToxiproxyPrerequisiteError):
            _require_duplicate_syn_normalization(
                self.document(total=2, expected=2, raw=2, retransmitted=0)
            )

    def test_missing_duplicate_observation_fails_closed(self) -> None:
        with self.assertRaises(ToxiproxyPrerequisiteError):
            _require_duplicate_syn_normalization(self.document(raw=1, retransmitted=0))

    def test_retransmission_accounting_mismatch_fails_closed(self) -> None:
        with self.assertRaises(ToxiproxyPrerequisiteError):
            _require_duplicate_syn_normalization(self.document(raw=3, retransmitted=1))


class DuplicateSynInjectorBoundaryTests(unittest.TestCase):
    def lab(self) -> RetransmissionQualifiedCaptureQualification:
        return RetransmissionQualifiedCaptureQualification(
            workspace=Path.cwd(),
            run_id="qualification-test",
        )

    def test_injector_is_same_namespace_capability_minimized_and_pinned(self) -> None:
        lab = self.lab()
        args = lab._duplicate_syn_injector_args()  # noqa: SLF001
        joined = " ".join(args)
        self.assertIn(f"container:{lab.source_name}", args)
        self.assertIn("--read-only", args)
        self.assertIn("--cap-drop=ALL", args)
        self.assertIn("--cap-add=NET_RAW", args)
        self.assertIn("--security-opt=no-new-privileges", args)
        self.assertIn(lab.helper.image_ref, args)
        self.assertNotIn("/var/run/docker.sock", joined)
        self.assertNotIn("NET_ADMIN", joined)
        self.assertNotIn("SYS_ADMIN", joined)

    def test_injector_script_binds_exact_source_and_target_identity(self) -> None:
        lab = self.lab()
        script = lab._duplicate_syn_script()  # noqa: SLF001
        self.assertIn(repr(lab.topology.source), script)
        self.assertIn(repr(lab.topology.expected_target), script)
        self.assertIn("sport=43123", script)
        self.assertIn("dport=43001", script)
        self.assertIn("seq=1247170609", script)
        self.assertEqual(script.count("sock.sendto(packet"), 2)

    def test_enhanced_document_is_emitted_only_after_duplicate_canary(self) -> None:
        lab = self.lab()
        base = CaptureQualificationResult(
            document={
                "format": "avp-project-network-capture-qualification-v0.2",
                "canaries": [{"label": "one-expected"}],
                "qualificationBasis": ["base"],
            },
            raw_artifacts=(("base.raw.json", b"base"),),
        )
        duplicate = {
            "totalInitiations": 1,
            "expectedTargetInitiations": 1,
            "alternateTargetInitiations": 0,
            "rawSynPackets": 2,
            "retransmittedSynPackets": 1,
            "label": "duplicate-syn-normalization",
            "rawBytes": b"duplicate",
        }
        with (
            patch.object(CaptureQualification, "_execute_materialized", return_value=base),
            patch.object(lab, "_observe", return_value=duplicate),
        ):
            result = lab._execute_materialized({})  # noqa: SLF001

        self.assertEqual(
            result.document["format"],
            "avp-project-network-capture-qualification-v0.3",
        )
        self.assertEqual(
            result.document["canaries"][-1]["label"],
            "duplicate-syn-normalization",
        )
        self.assertEqual(
            result.raw_artifacts[-1],
            ("duplicate-syn-normalization.raw.json", b"duplicate"),
        )
        self.assertFalse(lab._duplicate_syn_probe)  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()

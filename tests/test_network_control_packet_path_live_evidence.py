"""Ordinary-CI coverage for PTL-002 concrete packet-path live execution."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from acceptance.network_control.evidence_core import ArtifactStore, EvidenceMaterializationError
from acceptance.network_control.packet_path.live_evidence import (
    PacketPathLiveEvidenceLab,
    _exchange_from_document,
)
from acceptance.network_control.packet_path.negative_assemblies import PacketPathNegativeMode
from acceptance.network_control.witness_evidence import CaptureAssurance

_COMMIT = "5fef4b1844f071649fb326ed276c960f640df9b9"


def _assurance() -> CaptureAssurance:
    return CaptureAssurance(
        egress_coverage_verified=True,
        directionality_verified=True,
        offload_normalization_verified=True,
        pre_syn_connect_gap_closed=True,
    )


class PacketPathLiveEvidenceBoundaryTests(unittest.TestCase):
    def _lab(
        self,
        temporary: str,
        *,
        negative_mode: PacketPathNegativeMode | None = None,
    ) -> PacketPathLiveEvidenceLab:
        workspace = Path(__file__).resolve().parents[1]
        return PacketPathLiveEvidenceLab(
            workspace=workspace,
            artifact_store=ArtifactStore(Path(temporary) / "artifacts"),
            run_id="ptl002-live-boundary",
            semantic_baseline_commit=_COMMIT,
            observation_budget_ns=250_000_000,
            capture_assurance=_assurance(),
            negative_mode=negative_mode,
        )

    def test_constructor_does_not_materialize_network_resources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            lab = self._lab(temporary)

            self.assertFalse(lab.controller.topology_ready)
            self.assertFalse(lab.controller.fault_active)
            self.assertIsNone(lab.execution.negative_mode)

    def test_negative_case_is_bound_to_existing_single_mutation_assembly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            lab = self._lab(
                temporary,
                negative_mode=PacketPathNegativeMode.COLLATERAL_TARGET,
            )

            self.assertEqual(
                lab.execution.negative_mode,
                PacketPathNegativeMode.COLLATERAL_TARGET.value,
            )
            self.assertEqual(
                lab.plan.negative_mode,
                PacketPathNegativeMode.COLLATERAL_TARGET.value,
            )

    def test_incomplete_capture_assurance_is_rejected_before_execution(self) -> None:
        workspace = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(EvidenceMaterializationError):
                PacketPathLiveEvidenceLab(
                    workspace=workspace,
                    artifact_store=ArtifactStore(Path(temporary) / "artifacts"),
                    run_id="ptl002-live-assurance",
                    semantic_baseline_commit=_COMMIT,
                    observation_budget_ns=250_000_000,
                    capture_assurance=CaptureAssurance(
                        egress_coverage_verified=True,
                        directionality_verified=False,
                        offload_normalization_verified=True,
                        pre_syn_connect_gap_closed=True,
                    ),
                )

    def test_exchange_parser_rejects_truthy_strings(self) -> None:
        document = {
            "attemptId": "attempt-1",
            "completed": "false",
            "mismatchObserved": False,
            "observationBudgetExpired": True,
            "elapsedNs": 1,
            "responseSize": 0,
            "responseSha256": None,
            "nativeError": "ECONNREFUSED",
        }
        with self.assertRaises(EvidenceMaterializationError):
            _exchange_from_document(document)

    def test_native_error_remains_diagnostic_in_projected_exchange(self) -> None:
        observation = _exchange_from_document(
            {
                "attemptId": "attempt-1",
                "completed": False,
                "mismatchObserved": False,
                "observationBudgetExpired": False,
                "elapsedNs": 1,
                "responseSize": 0,
                "responseSha256": None,
                "nativeError": "ECONNREFUSED",
            }
        )

        self.assertFalse(observation.completed)
        self.assertFalse(observation.mismatch_observed)
        self.assertEqual(observation.native_error, "ECONNREFUSED")

    def test_source_keeps_mechanism_concrete_and_comparator_delegated(self) -> None:
        import acceptance.network_control.packet_path.live_evidence as module

        with open(module.__file__, "r", encoding="utf-8") as handle:
            source = handle.read()

        self.assertNotIn("class NetworkBackend", source)
        self.assertNotIn("class PacketPathBackend", source)
        self.assertNotIn("ProviderRegistry", source)
        self.assertNotIn("Toxiproxy", source)
        self.assertNotIn("compare_portable_evidence(", source)
        self.assertIn("PacketPathRunEvidence", source)
        self.assertIn("run_evidence.assess()", source)


if __name__ == "__main__":
    unittest.main()

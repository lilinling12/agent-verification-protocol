"""PTL-001 ordinary-CI tests for packet-path portable evidence projection."""

from __future__ import annotations

import unittest

from acceptance.network_control.attempt_client import ExchangeObservation
from acceptance.network_control.evidence_core import (
    AssessmentClass,
    AttemptFactory,
    ExchangeProgram,
    InitiationFacts,
)
from acceptance.network_control.packet_path.projection import (
    PacketPathAttemptEvidence,
    PacketPathRunEvidence,
)
from acceptance.network_control.packet_path.topology import PacketPathRunTopology

_BASELINE = "140ad041953ebea57a37273a63145258bba2a6ac"
_AEP_PATH = "rfcs/AEP-0012-network-control-resource-profile.md"


class PacketPathProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology = PacketPathRunTopology.for_run("packet-path-projection-tests")
        self.plan = self.topology.evidence_plan(
            design_revision="NPR-011-packet-path-v0.1",
            semantic_baseline_commit=_BASELINE,
            semantic_baseline_path=_AEP_PATH,
            path_id="selected-path",
            exchange_program=ExchangeProgram(
                program_id="exact-byte-v0.1",
                request_prefix=b"REQ",
                request_suffix=b"END",
                response_prefix=b"RESP",
                response_suffix=b"END",
            ),
            observation_budget_ns=1_000_000_000,
        )
        self.sealed = self.plan.seal()
        self.factory = AttemptFactory(private_run_root=b"p" * 32)

    def test_positive_packet_path_projects_no_upstream_initiation_channel(self) -> None:
        run = PacketPathRunEvidence(
            sealed_plan=self.sealed,
            attempts=tuple(
                self._evidence(phase, completed=phase not in {"activation-settlement", "subject-active-cut"})
                for phase in (
                    "baseline",
                    "pre-trigger",
                    "activation-settlement",
                    "subject-active-cut",
                    "non-target-control",
                    "recovery-1",
                    "recovery-2",
                    "stability",
                )
            ),
            cleanup_noninterference_ok=True,
            security_projection_ok=True,
        )

        observations = run.portable_observations()
        for item in (
            observations.baseline,
            observations.pre_trigger,
            observations.activation_settlement,
            observations.subject_active_cut,
            observations.non_target_control,
            observations.recovery_1,
            observations.recovery_2,
            observations.stability,
        ):
            self.assertIsNotNone(item)
            assert item is not None
            self.assertIsNone(item.upstream_initiations)

        self.assertEqual(run.assess().classification, AssessmentClass.SATISFIED)

    def test_missing_phase_is_not_fabricated_by_projection(self) -> None:
        run = PacketPathRunEvidence(
            sealed_plan=self.sealed,
            attempts=(self._evidence("baseline", completed=True),),
            cleanup_noninterference_ok=True,
            security_projection_ok=True,
        )

        observations = run.portable_observations()
        self.assertIsNone(observations.pre_trigger)
        self.assertEqual(run.assess().classification, AssessmentClass.EVIDENCE_INVALID)

    def test_hidden_fallback_is_rejected_by_unchanged_comparator(self) -> None:
        attempts = [
            self._evidence(phase, completed=phase not in {"activation-settlement", "subject-active-cut"})
            for phase in (
                "baseline",
                "pre-trigger",
                "activation-settlement",
                "subject-active-cut",
                "non-target-control",
                "recovery-1",
                "recovery-2",
                "stability",
            )
        ]
        cut_index = next(index for index, item in enumerate(attempts) if item.phase_id == "subject-active-cut")
        cut = attempts[cut_index]
        attempts[cut_index] = PacketPathAttemptEvidence(
            phase_id=cut.phase_id,
            attempt=cut.attempt,
            exchange=cut.exchange,
            front_initiations=InitiationFacts(
                channel="W-front",
                total_initiations=2,
                expected_target_initiations=1,
                alternate_target_initiations=1,
                raw_syn_packets=2,
                retransmitted_syn_packets=0,
            ),
        )
        run = PacketPathRunEvidence(
            sealed_plan=self.sealed,
            attempts=tuple(attempts),
            cleanup_noninterference_ok=True,
            security_projection_ok=True,
        )

        assessment = run.assess()
        self.assertEqual(assessment.classification, AssessmentClass.SEMANTIC_VIOLATION)
        self.assertIn("C10:subject-active-cut", assessment.primary_problem or "")

    def test_attempt_identity_drift_fails_before_comparator(self) -> None:
        evidence = self._evidence("baseline", completed=True)
        drifted_exchange = ExchangeObservation(
            attempt_id="0" * 64,
            completed=True,
            mismatch_observed=False,
            observation_budget_expired=False,
            elapsed_ns=1,
            response_size=len(evidence.attempt.expected_response_bytes),
            response_sha256=evidence.attempt.response_sha256,
            native_error=None,
        )

        with self.assertRaises(ValueError):
            PacketPathAttemptEvidence(
                phase_id="baseline",
                attempt=evidence.attempt,
                exchange=drifted_exchange,
                front_initiations=evidence.front_initiations,
            )

    def _evidence(self, phase: str, *, completed: bool) -> PacketPathAttemptEvidence:
        ordinal = (
            "baseline",
            "pre-trigger",
            "activation-settlement",
            "subject-active-cut",
            "non-target-control",
            "recovery-1",
            "recovery-2",
            "stability",
        ).index(phase)
        attempt = self.factory.issue(self.plan, phase_id=phase, ordinal=ordinal)
        exchange = ExchangeObservation(
            attempt_id=attempt.attempt_id,
            completed=completed,
            mismatch_observed=False,
            observation_budget_expired=not completed,
            elapsed_ns=1,
            response_size=len(attempt.expected_response_bytes) if completed else 0,
            response_sha256=attempt.response_sha256 if completed else None,
            native_error=None,
        )
        return PacketPathAttemptEvidence(
            phase_id=phase,
            attempt=attempt,
            exchange=exchange,
            front_initiations=InitiationFacts(
                channel="W-front",
                total_initiations=1,
                expected_target_initiations=1,
                alternate_target_initiations=0,
                raw_syn_packets=1,
                retransmitted_syn_packets=0,
            ),
        )


if __name__ == "__main__":
    unittest.main()

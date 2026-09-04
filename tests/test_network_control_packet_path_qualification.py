"""PTL-001 tests for the packet-path fail-closed qualification contract."""

from __future__ import annotations

import unittest

from acceptance.network_control.packet_path.qualification import (
    PacketPathQualificationPlan,
    PacketPathQualificationReport,
    QualificationFact,
    QualificationProperty,
    QualificationSource,
    expected_source,
)
from acceptance.network_control.packet_path.topology import PacketPathRunTopology
from acceptance.network_control.witness_evidence import CaptureAssurance


class PacketPathQualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology = PacketPathRunTopology.for_run("packet-path-qualification-tests")
        self.plan = PacketPathQualificationPlan.for_topology(self.topology)
        self.assurance = CaptureAssurance(
            egress_coverage_verified=True,
            directionality_verified=True,
            offload_normalization_verified=True,
            pre_syn_connect_gap_closed=True,
        )

    def _complete_facts(self) -> tuple[QualificationFact, ...]:
        return tuple(
            QualificationFact(
                property=requirement,
                source=expected_source(requirement),
                verified=True,
                detail=f"verified {requirement.value}",
            )
            for requirement in self.plan.required_properties
        )

    def test_complete_independently_sourced_qualification_is_ready(self) -> None:
        report = PacketPathQualificationReport.from_facts(
            plan=self.plan,
            facts=self._complete_facts(),
            capture_assurance=self.assurance,
        )
        self.assertTrue(report.ready)
        self.assertEqual(report.problems(), ())

    def test_missing_requirement_fails_closed(self) -> None:
        facts = self._complete_facts()[:-1]
        report = PacketPathQualificationReport.from_facts(
            plan=self.plan,
            facts=facts,
            capture_assurance=self.assurance,
        )
        self.assertFalse(report.ready)
        self.assertIn("missing:cleanup-residual-free", report.problems())

    def test_false_fact_fails_closed(self) -> None:
        facts = list(self._complete_facts())
        index = self.plan.required_properties.index(QualificationProperty.SELECTED_CUT)
        facts[index] = QualificationFact(
            property=QualificationProperty.SELECTED_CUT,
            source=QualificationSource.EXACT_EXCHANGE,
            verified=False,
            detail="selected exchange unexpectedly completed",
        )
        report = PacketPathQualificationReport.from_facts(
            plan=self.plan,
            facts=facts,
            capture_assurance=self.assurance,
        )
        self.assertIn("unverified:selected-cut", report.problems())

    def test_control_ack_cannot_substitute_for_route_or_exchange_evidence(self) -> None:
        facts = list(self._complete_facts())
        for requirement in (
            QualificationProperty.ROUTE_THROUGH_CONTROL,
            QualificationProperty.SELECTED_CUT,
        ):
            index = self.plan.required_properties.index(requirement)
            facts[index] = QualificationFact(
                property=requirement,
                source=QualificationSource.EVALUATOR_PREFLIGHT,
                verified=True,
                detail="command returned success",
            )
        report = PacketPathQualificationReport.from_facts(
            plan=self.plan,
            facts=facts,
            capture_assurance=self.assurance,
        )
        problems = report.problems()
        self.assertIn(
            "wrong-source:route-through-control:evaluator-preflight",
            problems,
        )
        self.assertIn(
            "wrong-source:selected-cut:evaluator-preflight",
            problems,
        )

    def test_duplicate_fact_is_ambiguous_and_fails_closed(self) -> None:
        facts = self._complete_facts() + (
            QualificationFact(
                property=QualificationProperty.RECOVERY_1,
                source=QualificationSource.EXACT_EXCHANGE,
                verified=True,
                detail="duplicate recovery observation",
            ),
        )
        report = PacketPathQualificationReport.from_facts(
            plan=self.plan,
            facts=facts,
            capture_assurance=self.assurance,
        )
        self.assertIn("duplicate:recovery-1", report.problems())

    def test_incomplete_capture_assurance_blocks_readiness(self) -> None:
        report = PacketPathQualificationReport.from_facts(
            plan=self.plan,
            facts=self._complete_facts(),
            capture_assurance=CaptureAssurance(
                egress_coverage_verified=True,
                directionality_verified=True,
                offload_normalization_verified=False,
                pre_syn_connect_gap_closed=True,
            ),
        )
        self.assertIn(
            "capture-assurance:offload-normalization-unverified",
            report.problems(),
        )

    def test_prerequisite_commands_are_read_only_discovery_commands(self) -> None:
        commands = self.plan.prerequisite_commands(python_executable="python3")
        self.assertEqual(commands[0], ("uname", "-srm"))
        self.assertIn(("id", "-u"), commands)
        self.assertIn(("ip", "-Version"), commands)
        self.assertIn(("nft", "--version"), commands)
        self.assertIn(("setpriv", "--version"), commands)
        self.assertIn(("python3", "--version"), commands)
        serialized = repr(commands)
        self.assertNotIn(" netns add ", serialized)
        self.assertNotIn(" add rule ", serialized)
        self.assertNotIn(" flush ", serialized)

    def test_source_ownership_matches_readiness_authority_boundaries(self) -> None:
        self.assertIs(
            expected_source(QualificationProperty.ROUTE_THROUGH_CONTROL),
            QualificationSource.ROUTE_OBSERVATION,
        )
        self.assertIs(
            expected_source(QualificationProperty.SUBJECT_CONTROL_ISOLATION),
            QualificationSource.SUBJECT_SECURITY_PROBE,
        )
        self.assertIs(
            expected_source(QualificationProperty.SELECTED_CUT),
            QualificationSource.EXACT_EXCHANGE,
        )
        self.assertIs(
            expected_source(QualificationProperty.WITNESS_ALTERNATE_VISIBILITY),
            QualificationSource.TRANSPORT_WITNESS,
        )
        self.assertIs(
            expected_source(QualificationProperty.CLEANUP_RESIDUAL_FREE),
            QualificationSource.CLEANUP_SENTINEL,
        )


if __name__ == "__main__":
    unittest.main()

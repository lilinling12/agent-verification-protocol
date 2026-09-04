"""PTL-001 tests for non-terminating Subject-egress witness binding."""

from __future__ import annotations

import unittest
from dataclasses import replace

from acceptance.network_control.evidence_core import (
    EvidenceMaterializationError,
    ExchangeProgram,
)
from acceptance.network_control.packet_path.controller import PacketPathController
from acceptance.network_control.packet_path.topology import PacketPathRunTopology
from acceptance.network_control.packet_path.witness_binding import PacketPathWitnessBinding
from acceptance.network_control.witness_evidence import CaptureAssurance


class PacketPathWitnessBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology = PacketPathRunTopology.for_run("packet-path-witness-tests")
        self.plan = self.topology.evidence_plan(
            design_revision="PTL-001-v0.1",
            semantic_baseline_commit="a" * 40,
            semantic_baseline_path="rfcs/AEP-0012-network-control-resource-profile.md",
            path_id="network-control-selected-path",
            exchange_program=ExchangeProgram(
                program_id="packet-path-test-exchange",
                request_prefix=b"req:",
                request_suffix=b";",
                response_prefix=b"resp:",
                response_suffix=b";",
            ),
            observation_budget_ns=1_000_000_000,
        )
        self.assurance = CaptureAssurance(
            egress_coverage_verified=True,
            directionality_verified=True,
            offload_normalization_verified=True,
            pre_syn_connect_gap_closed=True,
        )

    def test_selected_attempt_binds_only_subject_egress_channel(self) -> None:
        binding = PacketPathWitnessBinding.for_attempt(
            topology=self.topology,
            plan=self.plan,
            expected_target=self.plan.subject_destination,
            assurance=self.assurance,
        )

        self.assertEqual(binding.namespace_name, self.topology.subject_namespace)
        self.assertEqual(binding.interface_name, self.topology.subject_interface)
        self.assertEqual(binding.scope.channel, "W-front")
        self.assertEqual(binding.scope.role_id, "subject")
        self.assertEqual(binding.scope.source_addresses, (self.topology.subject_address,))
        self.assertEqual(binding.scope.expected_target, self.plan.subject_destination)

        witness = binding.build_witness()
        self.assertEqual(witness.scopes, (binding.scope,))
        self.assertEqual(witness.interface_name, self.topology.subject_interface)

    def test_control_attempt_uses_sealed_non_target_destination(self) -> None:
        control = self.plan.non_target_subject_destination
        assert control is not None
        binding = PacketPathWitnessBinding.for_attempt(
            topology=self.topology,
            plan=self.plan,
            expected_target=control,
            assurance=self.assurance,
        )
        self.assertEqual(binding.scope.expected_target, control)

    def test_privileged_probe_changes_role_not_capture_boundary(self) -> None:
        binding = PacketPathWitnessBinding.for_attempt(
            topology=self.topology,
            plan=self.plan,
            expected_target=self.plan.subject_destination,
            assurance=self.assurance,
            privileged_probe=True,
        )
        self.assertEqual(binding.scope.role_id, "privileged-probe")
        self.assertEqual(binding.namespace_name, self.topology.subject_namespace)
        self.assertEqual(binding.interface_name, self.topology.subject_interface)

    def test_evaluator_witness_and_subject_commands_have_distinct_authority(self) -> None:
        binding = PacketPathWitnessBinding.for_attempt(
            topology=self.topology,
            plan=self.plan,
            expected_target=self.plan.subject_destination,
            assurance=self.assurance,
        )
        evaluator = binding.evaluator_namespace_command(("python", "-m", "witness-worker"))
        subject = PacketPathController(topology=self.topology).subject_command(
            ("python", "-m", "attempt-worker")
        )

        self.assertEqual(evaluator[:4], ("ip", "netns", "exec", self.topology.subject_namespace))
        self.assertNotIn("setpriv", evaluator)
        self.assertIn("setpriv", subject)
        self.assertIn("--bounding-set=-all", subject)
        self.assertIn("--ambient-caps=-all", subject)
        self.assertIn("--no-new-privs", subject)

    def test_target_outside_sealed_plan_is_rejected(self) -> None:
        with self.assertRaises(EvidenceMaterializationError):
            PacketPathWitnessBinding.for_attempt(
                topology=self.topology,
                plan=self.plan,
                expected_target=replace(self.plan.subject_destination, port=49999),
                assurance=self.assurance,
            )

    def test_distinct_upstream_socket_is_rejected_for_packet_path(self) -> None:
        drifted = replace(
            self.plan,
            upstream_fixture=replace(self.plan.upstream_fixture, port=49998),
        )
        with self.assertRaisesRegex(EvidenceMaterializationError, "distinct selected upstream"):
            PacketPathWitnessBinding.for_attempt(
                topology=self.topology,
                plan=drifted,
                expected_target=drifted.subject_destination,
                assurance=self.assurance,
            )

    def test_run_identity_drift_is_rejected(self) -> None:
        other = PacketPathRunTopology.for_run("different-run")
        with self.assertRaisesRegex(EvidenceMaterializationError, "run identity drift"):
            PacketPathWitnessBinding.for_attempt(
                topology=other,
                plan=self.plan,
                expected_target=self.plan.subject_destination,
                assurance=self.assurance,
            )


if __name__ == "__main__":
    unittest.main()

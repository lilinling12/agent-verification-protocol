"""PTL-001 tests for the finite packet-path execution lifecycle."""

from __future__ import annotations

import unittest
from dataclasses import replace

from acceptance.network_control.evidence_core import (
    EvidenceMaterializationError,
    ExchangeProgram,
    MaterializedEndpoint,
)
from acceptance.network_control.packet_path.execution import (
    PacketPathActor,
    PacketPathExecutionPlan,
    PacketPathStepId,
)
from acceptance.network_control.packet_path.negative_assemblies import (
    PacketPathNegativeAssembly,
    PacketPathNegativeMode,
)
from acceptance.network_control.packet_path.topology import PacketPathRunTopology

_BASELINE = "140ad041953ebea57a37273a63145258bba2a6ac"
_AEP_PATH = "rfcs/AEP-0012-network-control-resource-profile.md"


class PacketPathExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology = PacketPathRunTopology.for_run("packet-path-execution-tests")
        self.plan = self.topology.evidence_plan(
            design_revision="NPR-011-packet-path-v0.1",
            semantic_baseline_commit=_BASELINE,
            semantic_baseline_path=_AEP_PATH,
            path_id="selected-path",
            exchange_program=ExchangeProgram(
                program_id="exact-byte-v0.1",
                request_prefix=b"REQ\x00",
                request_suffix=b"\x00END",
                response_prefix=b"RESP\x00",
                response_suffix=b"\x00END",
            ),
            observation_budget_ns=1_000_000_000,
        )

    def test_positive_lifecycle_binds_authorities_and_finite_attempts(self) -> None:
        execution = PacketPathExecutionPlan.build(
            topology=self.topology,
            evidence_plan=self.plan,
        )

        self.assertEqual(execution.steps[0].step_id, PacketPathStepId.SETUP)
        self.assertEqual(
            execution.step(PacketPathStepId.SUBJECT_ACTIVE_CUT).actor,
            PacketPathActor.SUBJECT,
        )
        self.assertEqual(
            execution.step(PacketPathStepId.ACTIVATION_SETTLEMENT).actor,
            PacketPathActor.PRIVILEGED_PROBE,
        )
        self.assertEqual(
            execution.step(PacketPathStepId.RECOVERY_1).actor,
            PacketPathActor.PRIVILEGED_PROBE,
        )
        self.assertEqual(
            execution.step(PacketPathStepId.RECOVERY_2).actor,
            PacketPathActor.PRIVILEGED_PROBE,
        )
        self.assertEqual(
            execution.step(PacketPathStepId.NON_TARGET_CONTROL).target,
            self.topology.control_endpoint,
        )
        self.assertEqual(
            execution.step(PacketPathStepId.SUBJECT_ACTIVE_CUT).connection_targets,
            (self.topology.selected_endpoint,),
        )
        self.assertEqual(len(execution.attempt_steps), 8)

        cleanup_index = execution.steps.index(execution.step(PacketPathStepId.CLEANUP))
        sentinel_index = execution.steps.index(
            execution.step(PacketPathStepId.CLEANUP_SENTINEL)
        )
        self.assertLess(cleanup_index, sentinel_index)

    def test_early_activation_moves_real_fault_before_pre_trigger(self) -> None:
        execution = self._negative(PacketPathNegativeMode.EARLY_ACTIVATION)
        install_index = execution.steps.index(
            execution.step(PacketPathStepId.INSTALL_FAULT)
        )
        pre_trigger_index = execution.steps.index(
            execution.step(PacketPathStepId.PRE_TRIGGER)
        )

        self.assertLess(install_index, pre_trigger_index)

    def test_false_settled_omits_independent_probe_only(self) -> None:
        execution = self._negative(PacketPathNegativeMode.FALSE_SETTLED)

        with self.assertRaises(KeyError):
            execution.step(PacketPathStepId.ACTIVATION_SETTLEMENT)
        self.assertEqual(len(execution.attempt_steps), 7)
        self.assertIsNotNone(execution.step(PacketPathStepId.SUBJECT_ACTIVE_CUT))

    def test_false_recovery_omits_second_probe_and_stability(self) -> None:
        execution = self._negative(PacketPathNegativeMode.FALSE_RECOVERY)

        self.assertIsNotNone(execution.step(PacketPathStepId.RECOVERY_1))
        with self.assertRaises(KeyError):
            execution.step(PacketPathStepId.RECOVERY_2)
        with self.assertRaises(KeyError):
            execution.step(PacketPathStepId.STABILITY)

    def test_hidden_fallback_executes_real_second_subject_connection(self) -> None:
        execution = self._negative(PacketPathNegativeMode.HIDDEN_RETRY_FALLBACK)
        cut = execution.step(PacketPathStepId.SUBJECT_ACTIVE_CUT)

        self.assertEqual(cut.actor, PacketPathActor.SUBJECT)
        self.assertEqual(
            cut.connection_targets,
            (self.topology.selected_endpoint, self.topology.control_endpoint),
        )
        self.assertNotIn("C10", repr(cut))
        self.assertNotIn("SEMANTIC_VIOLATION", repr(cut))

    def test_schedule_leak_changes_subject_projection_not_control_plane(self) -> None:
        execution = self._negative(PacketPathNegativeMode.SCHEDULE_LEAK)
        pre_trigger = execution.step(PacketPathStepId.PRE_TRIGGER)

        self.assertEqual(
            pre_trigger.subject_environment,
            (("AVP_FUTURE_FAULT_SCHEDULE", "deliberate-negative"),),
        )
        self.assertEqual(
            execution.step(PacketPathStepId.INSTALL_FAULT).subject_environment,
            (),
        )

    def test_residual_negative_runs_sentinel_before_best_effort_cleanup(self) -> None:
        execution = self._negative(
            PacketPathNegativeMode.RESIDUAL_STATE_CLEANUP_FAILURE
        )
        cleanup_index = execution.steps.index(execution.step(PacketPathStepId.CLEANUP))
        sentinel_index = execution.steps.index(
            execution.step(PacketPathStepId.CLEANUP_SENTINEL)
        )

        self.assertLess(sentinel_index, cleanup_index)
        self.assertEqual(
            execution.step(PacketPathStepId.CLEANUP_SENTINEL).actor,
            PacketPathActor.CLEANUP_SENTINEL,
        )

    def test_negative_plan_and_assembly_must_match_exactly(self) -> None:
        negative = PacketPathNegativeAssembly.for_mode(
            topology=self.topology,
            mode=PacketPathNegativeMode.BYPASS_FAULT,
        )

        with self.assertRaises(EvidenceMaterializationError):
            PacketPathExecutionPlan.build(
                topology=self.topology,
                evidence_plan=self.plan,
                negative=negative,
            )

    def test_execution_rejects_terminating_style_upstream_binding(self) -> None:
        terminating_upstream = MaterializedEndpoint(
            family="ipv4",
            address=self.topology.fixture_address,
            port=self.topology.unused_fault_port,
            role="upstream-fixture",
        )
        terminating_like = replace(
            self.plan,
            upstream_fixture=terminating_upstream,
        )

        with self.assertRaises(EvidenceMaterializationError):
            PacketPathExecutionPlan.build(
                topology=self.topology,
                evidence_plan=terminating_like,
            )

    def _negative(self, mode: PacketPathNegativeMode) -> PacketPathExecutionPlan:
        assembly = PacketPathNegativeAssembly.for_mode(
            topology=self.topology,
            mode=mode,
        )
        plan = replace(self.plan, negative_mode=mode.value)
        return PacketPathExecutionPlan.build(
            topology=self.topology,
            evidence_plan=plan,
            negative=assembly,
        )


if __name__ == "__main__":
    unittest.main()

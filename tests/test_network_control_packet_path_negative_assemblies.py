"""PTL-001 tests for concrete packet-path negative assemblies."""

from __future__ import annotations

import unittest

from acceptance.network_control.packet_path.controller import PacketPathFaultMode
from acceptance.network_control.packet_path.negative_assemblies import (
    ActivationTiming,
    CleanupBehavior,
    PacketPathNegativeAssembly,
    PacketPathNegativeMode,
    RecoveryBehavior,
    SettlementBehavior,
    SubjectAttemptBehavior,
    SubjectProjectionBehavior,
)
from acceptance.network_control.packet_path.topology import PacketPathRunTopology


class PacketPathNegativeAssemblyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology = PacketPathRunTopology.for_run("packet-path-negative-tests")

    def test_all_required_negative_modes_have_one_canonical_assembly(self) -> None:
        assemblies = {
            mode: PacketPathNegativeAssembly.for_mode(
                topology=self.topology,
                mode=mode,
            )
            for mode in PacketPathNegativeMode
        }

        self.assertEqual(set(assemblies), set(PacketPathNegativeMode))
        self.assertEqual(
            assemblies[PacketPathNegativeMode.BYPASS_FAULT].fault_mode,
            PacketPathFaultMode.BYPASS,
        )
        self.assertEqual(
            assemblies[PacketPathNegativeMode.EARLY_ACTIVATION].activation_timing,
            ActivationTiming.BEFORE_PRE_TRIGGER,
        )
        self.assertEqual(
            assemblies[PacketPathNegativeMode.FALSE_SETTLED].settlement_behavior,
            SettlementBehavior.OMIT_INDEPENDENT_PROBE,
        )
        self.assertEqual(
            assemblies[PacketPathNegativeMode.FALSE_RECOVERY].recovery_behavior,
            RecoveryBehavior.OMIT_SECOND_AND_STABILITY,
        )
        self.assertEqual(
            assemblies[PacketPathNegativeMode.SCHEDULE_LEAK].subject_projection_behavior,
            SubjectProjectionBehavior.LEAK_FUTURE_FAULT_SCHEDULE,
        )
        self.assertEqual(
            assemblies[
                PacketPathNegativeMode.HIDDEN_RETRY_FALLBACK
            ].subject_attempt_behavior,
            SubjectAttemptBehavior.SELECTED_THEN_CONTROL_FALLBACK,
        )
        self.assertEqual(
            assemblies[PacketPathNegativeMode.COLLATERAL_TARGET].fault_mode,
            PacketPathFaultMode.COLLATERAL,
        )
        self.assertEqual(
            assemblies[
                PacketPathNegativeMode.RESIDUAL_STATE_CLEANUP_FAILURE
            ].cleanup_behavior,
            CleanupBehavior.DEFER_RUN_OWNED_CLEANUP_UNTIL_SENTINEL,
        )

    def test_hidden_retry_uses_real_second_sealed_target(self) -> None:
        assembly = PacketPathNegativeAssembly.for_mode(
            topology=self.topology,
            mode=PacketPathNegativeMode.HIDDEN_RETRY_FALLBACK,
        )

        self.assertEqual(
            assembly.subject_active_cut_targets(),
            (self.topology.selected_endpoint, self.topology.control_endpoint),
        )

    def test_schedule_leak_is_a_subject_projection_mutation(self) -> None:
        assembly = PacketPathNegativeAssembly.for_mode(
            topology=self.topology,
            mode=PacketPathNegativeMode.SCHEDULE_LEAK,
        )

        self.assertEqual(
            assembly.subject_environment_overrides(),
            (("AVP_FUTURE_FAULT_SCHEDULE", "deliberate-negative"),),
        )

    def test_non_projection_negatives_do_not_leak_schedule(self) -> None:
        for mode in PacketPathNegativeMode:
            if mode is PacketPathNegativeMode.SCHEDULE_LEAK:
                continue
            assembly = PacketPathNegativeAssembly.for_mode(
                topology=self.topology,
                mode=mode,
            )
            self.assertEqual(assembly.subject_environment_overrides(), ())

    def test_negative_assemblies_do_not_encode_comparator_outcomes(self) -> None:
        for mode in PacketPathNegativeMode:
            assembly = PacketPathNegativeAssembly.for_mode(
                topology=self.topology,
                mode=mode,
            )
            rendered = repr(assembly)
            self.assertNotIn("SATISFIED", rendered)
            self.assertNotIn("SEMANTIC_VIOLATION", rendered)
            self.assertNotIn("EVIDENCE_INVALID", rendered)
            self.assertNotIn("C1", rendered)
            self.assertNotIn("C10", rendered)


if __name__ == "__main__":
    unittest.main()

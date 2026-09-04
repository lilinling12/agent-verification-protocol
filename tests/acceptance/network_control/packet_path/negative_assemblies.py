"""Real faulty-assembly descriptors for PTL-001 packet-path evidence.

Each required negative changes one concrete mechanism/lifecycle/security behavior
while leaving the provider-neutral comparator untouched. The descriptors are
mechanism-local execution inputs: they never encode an expected assessment,
portable verdict, or provider-specific success condition.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..evidence_core import EvidenceMaterializationError, MaterializedEndpoint
from .controller import PacketPathFaultMode
from .topology import PacketPathRunTopology


class PacketPathNegativeMode(str, Enum):
    """Required packet-path faulty assemblies from the NPR-011 readiness audit."""

    BYPASS_FAULT = "BypassFault"
    EARLY_ACTIVATION = "EarlyActivation"
    FALSE_SETTLED = "FalseSettled"
    FALSE_RECOVERY = "FalseRecovery"
    SCHEDULE_LEAK = "ScheduleLeak"
    HIDDEN_RETRY_FALLBACK = "HiddenRetry/Fallback"
    COLLATERAL_TARGET = "CollateralTarget"
    RESIDUAL_STATE_CLEANUP_FAILURE = "ResidualStateCleanupFailure"


class ActivationTiming(str, Enum):
    AFTER_TRIGGER = "after-trigger"
    BEFORE_PRE_TRIGGER = "before-pre-trigger"


class SettlementBehavior(str, Enum):
    INDEPENDENT_PROBE = "independent-probe"
    OMIT_INDEPENDENT_PROBE = "omit-independent-probe"


class RecoveryBehavior(str, Enum):
    TWO_PROBES_AND_STABILITY = "two-probes-and-stability"
    OMIT_SECOND_AND_STABILITY = "omit-second-and-stability"


class SubjectProjectionBehavior(str, Enum):
    SEALED_ONLY = "sealed-only"
    LEAK_FUTURE_FAULT_SCHEDULE = "leak-future-fault-schedule"


class SubjectAttemptBehavior(str, Enum):
    SINGLE_SELECTED = "single-selected"
    SELECTED_THEN_CONTROL_FALLBACK = "selected-then-control-fallback"


class CleanupBehavior(str, Enum):
    NORMAL = "normal"
    DEFER_RUN_OWNED_CLEANUP_UNTIL_SENTINEL = "defer-run-owned-cleanup-until-sentinel"


@dataclass(frozen=True, slots=True)
class PacketPathNegativeAssembly:
    """One canonical faulty packet-path assembly for a single evidence run."""

    mode: PacketPathNegativeMode
    topology: PacketPathRunTopology
    fault_mode: PacketPathFaultMode = PacketPathFaultMode.SELECTED
    activation_timing: ActivationTiming = ActivationTiming.AFTER_TRIGGER
    settlement_behavior: SettlementBehavior = SettlementBehavior.INDEPENDENT_PROBE
    recovery_behavior: RecoveryBehavior = RecoveryBehavior.TWO_PROBES_AND_STABILITY
    subject_projection_behavior: SubjectProjectionBehavior = SubjectProjectionBehavior.SEALED_ONLY
    subject_attempt_behavior: SubjectAttemptBehavior = SubjectAttemptBehavior.SINGLE_SELECTED
    cleanup_behavior: CleanupBehavior = CleanupBehavior.NORMAL

    def __post_init__(self) -> None:
        if not isinstance(self.mode, PacketPathNegativeMode):
            raise EvidenceMaterializationError("packet-path negative mode must be typed")
        marker = self._single_mutation_marker()
        expected = _EXPECTED_MUTATION[self.mode]
        if marker != expected:
            raise EvidenceMaterializationError(
                f"packet-path negative {self.mode.value!r} must realize exactly {expected!r}; "
                f"got {marker!r}"
            )

    @classmethod
    def for_mode(
        cls,
        *,
        topology: PacketPathRunTopology,
        mode: PacketPathNegativeMode,
    ) -> "PacketPathNegativeAssembly":
        """Materialize the reviewed single-fault assembly for ``mode``."""

        if mode is PacketPathNegativeMode.BYPASS_FAULT:
            return cls(mode=mode, topology=topology, fault_mode=PacketPathFaultMode.BYPASS)
        if mode is PacketPathNegativeMode.EARLY_ACTIVATION:
            return cls(
                mode=mode,
                topology=topology,
                activation_timing=ActivationTiming.BEFORE_PRE_TRIGGER,
            )
        if mode is PacketPathNegativeMode.FALSE_SETTLED:
            return cls(
                mode=mode,
                topology=topology,
                settlement_behavior=SettlementBehavior.OMIT_INDEPENDENT_PROBE,
            )
        if mode is PacketPathNegativeMode.FALSE_RECOVERY:
            return cls(
                mode=mode,
                topology=topology,
                recovery_behavior=RecoveryBehavior.OMIT_SECOND_AND_STABILITY,
            )
        if mode is PacketPathNegativeMode.SCHEDULE_LEAK:
            return cls(
                mode=mode,
                topology=topology,
                subject_projection_behavior=(
                    SubjectProjectionBehavior.LEAK_FUTURE_FAULT_SCHEDULE
                ),
            )
        if mode is PacketPathNegativeMode.HIDDEN_RETRY_FALLBACK:
            return cls(
                mode=mode,
                topology=topology,
                subject_attempt_behavior=(
                    SubjectAttemptBehavior.SELECTED_THEN_CONTROL_FALLBACK
                ),
            )
        if mode is PacketPathNegativeMode.COLLATERAL_TARGET:
            return cls(
                mode=mode,
                topology=topology,
                fault_mode=PacketPathFaultMode.COLLATERAL,
            )
        if mode is PacketPathNegativeMode.RESIDUAL_STATE_CLEANUP_FAILURE:
            return cls(
                mode=mode,
                topology=topology,
                cleanup_behavior=(
                    CleanupBehavior.DEFER_RUN_OWNED_CLEANUP_UNTIL_SENTINEL
                ),
            )
        raise EvidenceMaterializationError(f"unsupported packet-path negative mode: {mode!r}")

    def subject_active_cut_targets(self) -> tuple[MaterializedEndpoint, ...]:
        """Return real connection targets for the Subject active-cut attempt.

        The hidden retry/fallback negative executes a genuine second connection to
        the sealed non-target control endpoint. It is not represented by a
        fabricated initiation count.
        """

        if self.subject_attempt_behavior is SubjectAttemptBehavior.SELECTED_THEN_CONTROL_FALLBACK:
            return (self.topology.selected_endpoint, self.topology.control_endpoint)
        return (self.topology.selected_endpoint,)

    def subject_environment_overrides(self) -> tuple[tuple[str, str], ...]:
        """Return deliberate Subject-visible projection mutations for ScheduleLeak."""

        if self.subject_projection_behavior is SubjectProjectionBehavior.LEAK_FUTURE_FAULT_SCHEDULE:
            return (("AVP_FUTURE_FAULT_SCHEDULE", "deliberate-negative"),)
        return ()

    def _single_mutation_marker(self) -> str:
        mutations: list[str] = []
        if self.fault_mode is PacketPathFaultMode.BYPASS:
            mutations.append("fault:bypass")
        elif self.fault_mode is PacketPathFaultMode.COLLATERAL:
            mutations.append("fault:collateral")
        elif self.fault_mode is not PacketPathFaultMode.SELECTED:
            mutations.append(f"fault:unknown:{self.fault_mode!r}")

        if self.activation_timing is ActivationTiming.BEFORE_PRE_TRIGGER:
            mutations.append("activation:early")
        elif self.activation_timing is not ActivationTiming.AFTER_TRIGGER:
            mutations.append(f"activation:unknown:{self.activation_timing!r}")

        if self.settlement_behavior is SettlementBehavior.OMIT_INDEPENDENT_PROBE:
            mutations.append("settlement:omit")
        elif self.settlement_behavior is not SettlementBehavior.INDEPENDENT_PROBE:
            mutations.append(f"settlement:unknown:{self.settlement_behavior!r}")

        if self.recovery_behavior is RecoveryBehavior.OMIT_SECOND_AND_STABILITY:
            mutations.append("recovery:omit-second-and-stability")
        elif self.recovery_behavior is not RecoveryBehavior.TWO_PROBES_AND_STABILITY:
            mutations.append(f"recovery:unknown:{self.recovery_behavior!r}")

        if (
            self.subject_projection_behavior
            is SubjectProjectionBehavior.LEAK_FUTURE_FAULT_SCHEDULE
        ):
            mutations.append("projection:schedule-leak")
        elif self.subject_projection_behavior is not SubjectProjectionBehavior.SEALED_ONLY:
            mutations.append(f"projection:unknown:{self.subject_projection_behavior!r}")

        if (
            self.subject_attempt_behavior
            is SubjectAttemptBehavior.SELECTED_THEN_CONTROL_FALLBACK
        ):
            mutations.append("subject-attempt:selected-then-control-fallback")
        elif self.subject_attempt_behavior is not SubjectAttemptBehavior.SINGLE_SELECTED:
            mutations.append(f"subject-attempt:unknown:{self.subject_attempt_behavior!r}")

        if (
            self.cleanup_behavior
            is CleanupBehavior.DEFER_RUN_OWNED_CLEANUP_UNTIL_SENTINEL
        ):
            mutations.append("cleanup:defer-until-sentinel")
        elif self.cleanup_behavior is not CleanupBehavior.NORMAL:
            mutations.append(f"cleanup:unknown:{self.cleanup_behavior!r}")

        if len(mutations) != 1:
            raise EvidenceMaterializationError(
                "packet-path negative assembly must contain exactly one deliberate mutation"
            )
        return mutations[0]


_EXPECTED_MUTATION: dict[PacketPathNegativeMode, str] = {
    PacketPathNegativeMode.BYPASS_FAULT: "fault:bypass",
    PacketPathNegativeMode.EARLY_ACTIVATION: "activation:early",
    PacketPathNegativeMode.FALSE_SETTLED: "settlement:omit",
    PacketPathNegativeMode.FALSE_RECOVERY: "recovery:omit-second-and-stability",
    PacketPathNegativeMode.SCHEDULE_LEAK: "projection:schedule-leak",
    PacketPathNegativeMode.HIDDEN_RETRY_FALLBACK: (
        "subject-attempt:selected-then-control-fallback"
    ),
    PacketPathNegativeMode.COLLATERAL_TARGET: "fault:collateral",
    PacketPathNegativeMode.RESIDUAL_STATE_CLEANUP_FAILURE: "cleanup:defer-until-sentinel",
}

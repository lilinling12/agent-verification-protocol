"""Finite mechanism-local execution plan for Network Control PTL-001.

The plan binds the reviewed packet-path lifecycle to explicit actors and concrete
fault assemblies. It is not a generic lab runner and it does not assess C1-C12.
A future privileged lane may execute these steps, but may not redefine their
ordering, authority boundary, or negative mutation in workflow YAML.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from ..evidence_core import EvidenceMaterializationError, EvidencePlan, MaterializedEndpoint
from .controller import PacketPathFaultMode
from .negative_assemblies import (
    ActivationTiming,
    CleanupBehavior,
    PacketPathNegativeAssembly,
    RecoveryBehavior,
    SettlementBehavior,
    SubjectAttemptBehavior,
)
from .topology import PacketPathRunTopology


class PacketPathActor(str, Enum):
    """Concrete PTL-001 authorities; not reusable provider roles."""

    EVALUATOR_CONTROL = "evaluator-control"
    SUBJECT = "subject"
    PRIVILEGED_PROBE = "privileged-probe"
    CLEANUP_SENTINEL = "cleanup-sentinel"


class PacketPathStepId(str, Enum):
    SETUP = "setup"
    START_FIXTURES = "start-fixtures"
    BASELINE = "baseline"
    PRE_TRIGGER = "pre-trigger"
    TRIGGER = "trigger"
    INSTALL_FAULT = "install-fault"
    ACTIVATION_SETTLEMENT = "activation-settlement"
    SUBJECT_ACTIVE_CUT = "subject-active-cut"
    NON_TARGET_CONTROL = "non-target-control"
    CLEAR_FAULT = "clear-fault"
    RECOVERY_1 = "recovery-1"
    RECOVERY_2 = "recovery-2"
    STABILITY = "stability"
    STOP_FIXTURES = "stop-fixtures"
    CLEANUP = "cleanup"
    CLEANUP_SENTINEL = "cleanup-sentinel"


@dataclass(frozen=True, slots=True)
class PacketPathExecutionStep:
    """One finite execution action with enough data to prevent workflow drift."""

    step_id: PacketPathStepId
    actor: PacketPathActor
    attempt_phase: str | None = None
    target: MaterializedEndpoint | None = None
    connection_targets: tuple[MaterializedEndpoint, ...] = ()
    fault_mode: PacketPathFaultMode | None = None
    subject_environment: tuple[tuple[str, str], ...] = ()

    @property
    def is_attempt(self) -> bool:
        return self.attempt_phase is not None


@dataclass(frozen=True, slots=True)
class PacketPathExecutionPlan:
    """Reviewed positive or single-negative PTL-001 lifecycle."""

    topology: PacketPathRunTopology
    evidence_plan: EvidencePlan
    steps: tuple[PacketPathExecutionStep, ...]
    negative_mode: str | None = None

    @classmethod
    def build(
        cls,
        *,
        topology: PacketPathRunTopology,
        evidence_plan: EvidencePlan,
        negative: PacketPathNegativeAssembly | None = None,
    ) -> "PacketPathExecutionPlan":
        _validate_binding(topology=topology, plan=evidence_plan)
        if negative is not None:
            if negative.topology != topology:
                raise EvidenceMaterializationError(
                    "packet-path negative assembly topology does not match execution topology"
                )
            if evidence_plan.negative_mode != negative.mode.value:
                raise EvidenceMaterializationError(
                    "packet-path evidence-plan negative mode does not match assembly"
                )
        elif evidence_plan.negative_mode is not None:
            raise EvidenceMaterializationError(
                "packet-path negative evidence plan requires an explicit faulty assembly"
            )

        steps = list(_positive_steps(topology))
        if negative is not None:
            steps = _apply_negative(steps, negative)
        _validate_steps(steps=tuple(steps), plan=evidence_plan, negative=negative)
        return cls(
            topology=topology,
            evidence_plan=evidence_plan,
            steps=tuple(steps),
            negative_mode=None if negative is None else negative.mode.value,
        )

    def step(self, step_id: PacketPathStepId) -> PacketPathExecutionStep:
        matches = tuple(item for item in self.steps if item.step_id is step_id)
        if len(matches) != 1:
            raise KeyError(f"expected exactly one execution step {step_id.value!r}")
        return matches[0]

    @property
    def attempt_steps(self) -> tuple[PacketPathExecutionStep, ...]:
        return tuple(item for item in self.steps if item.is_attempt)


def _positive_steps(topology: PacketPathRunTopology) -> tuple[PacketPathExecutionStep, ...]:
    selected = topology.selected_endpoint
    control = topology.control_endpoint
    return (
        PacketPathExecutionStep(PacketPathStepId.SETUP, PacketPathActor.EVALUATOR_CONTROL),
        PacketPathExecutionStep(
            PacketPathStepId.START_FIXTURES,
            PacketPathActor.EVALUATOR_CONTROL,
        ),
        _attempt(PacketPathStepId.BASELINE, PacketPathActor.SUBJECT, "baseline", selected),
        _attempt(
            PacketPathStepId.PRE_TRIGGER,
            PacketPathActor.SUBJECT,
            "pre-trigger",
            selected,
        ),
        PacketPathExecutionStep(PacketPathStepId.TRIGGER, PacketPathActor.EVALUATOR_CONTROL),
        PacketPathExecutionStep(
            PacketPathStepId.INSTALL_FAULT,
            PacketPathActor.EVALUATOR_CONTROL,
            fault_mode=PacketPathFaultMode.SELECTED,
        ),
        _attempt(
            PacketPathStepId.ACTIVATION_SETTLEMENT,
            PacketPathActor.PRIVILEGED_PROBE,
            "activation-settlement",
            selected,
        ),
        _attempt(
            PacketPathStepId.SUBJECT_ACTIVE_CUT,
            PacketPathActor.SUBJECT,
            "subject-active-cut",
            selected,
        ),
        _attempt(
            PacketPathStepId.NON_TARGET_CONTROL,
            PacketPathActor.SUBJECT,
            "non-target-control",
            control,
        ),
        PacketPathExecutionStep(
            PacketPathStepId.CLEAR_FAULT,
            PacketPathActor.EVALUATOR_CONTROL,
        ),
        _attempt(
            PacketPathStepId.RECOVERY_1,
            PacketPathActor.PRIVILEGED_PROBE,
            "recovery-1",
            selected,
        ),
        _attempt(
            PacketPathStepId.RECOVERY_2,
            PacketPathActor.PRIVILEGED_PROBE,
            "recovery-2",
            selected,
        ),
        _attempt(
            PacketPathStepId.STABILITY,
            PacketPathActor.SUBJECT,
            "stability",
            selected,
        ),
        PacketPathExecutionStep(
            PacketPathStepId.STOP_FIXTURES,
            PacketPathActor.EVALUATOR_CONTROL,
        ),
        PacketPathExecutionStep(PacketPathStepId.CLEANUP, PacketPathActor.EVALUATOR_CONTROL),
        PacketPathExecutionStep(
            PacketPathStepId.CLEANUP_SENTINEL,
            PacketPathActor.CLEANUP_SENTINEL,
        ),
    )


def _attempt(
    step_id: PacketPathStepId,
    actor: PacketPathActor,
    phase: str,
    target: MaterializedEndpoint,
) -> PacketPathExecutionStep:
    return PacketPathExecutionStep(
        step_id=step_id,
        actor=actor,
        attempt_phase=phase,
        target=target,
        connection_targets=(target,),
    )


def _apply_negative(
    positive: list[PacketPathExecutionStep],
    negative: PacketPathNegativeAssembly,
) -> list[PacketPathExecutionStep]:
    steps = list(positive)

    if negative.fault_mode is not PacketPathFaultMode.SELECTED:
        index = _index(steps, PacketPathStepId.INSTALL_FAULT)
        steps[index] = replace(steps[index], fault_mode=negative.fault_mode)

    if negative.activation_timing is ActivationTiming.BEFORE_PRE_TRIGGER:
        install = steps.pop(_index(steps, PacketPathStepId.INSTALL_FAULT))
        pre_trigger_index = _index(steps, PacketPathStepId.PRE_TRIGGER)
        steps.insert(pre_trigger_index, install)

    if negative.settlement_behavior is SettlementBehavior.OMIT_INDEPENDENT_PROBE:
        steps.pop(_index(steps, PacketPathStepId.ACTIVATION_SETTLEMENT))

    if negative.recovery_behavior is RecoveryBehavior.OMIT_SECOND_AND_STABILITY:
        steps.pop(_index(steps, PacketPathStepId.RECOVERY_2))
        steps.pop(_index(steps, PacketPathStepId.STABILITY))

    environment = negative.subject_environment_overrides()
    if environment:
        index = _index(steps, PacketPathStepId.PRE_TRIGGER)
        steps[index] = replace(steps[index], subject_environment=environment)

    if (
        negative.subject_attempt_behavior
        is SubjectAttemptBehavior.SELECTED_THEN_CONTROL_FALLBACK
    ):
        index = _index(steps, PacketPathStepId.SUBJECT_ACTIVE_CUT)
        steps[index] = replace(
            steps[index],
            connection_targets=negative.subject_active_cut_targets(),
        )

    if negative.cleanup_behavior is CleanupBehavior.DEFER_RUN_OWNED_CLEANUP_UNTIL_SENTINEL:
        cleanup = steps.pop(_index(steps, PacketPathStepId.CLEANUP))
        sentinel_index = _index(steps, PacketPathStepId.CLEANUP_SENTINEL)
        steps.insert(sentinel_index + 1, cleanup)

    return steps


def _validate_binding(*, topology: PacketPathRunTopology, plan: EvidencePlan) -> None:
    if plan.run_id != topology.run_id:
        raise EvidenceMaterializationError("packet-path execution run identity drift")
    if plan.subject_destination != topology.selected_endpoint:
        raise EvidenceMaterializationError("packet-path execution selected endpoint drift")
    if plan.upstream_fixture != plan.subject_destination:
        raise EvidenceMaterializationError(
            "packet-path execution cannot materialize a terminating upstream socket"
        )
    if plan.non_target_subject_destination != topology.control_endpoint:
        raise EvidenceMaterializationError("packet-path execution control endpoint drift")
    if plan.non_target_upstream_fixture != plan.non_target_subject_destination:
        raise EvidenceMaterializationError(
            "packet-path execution cannot materialize a terminating control upstream socket"
        )


def _validate_steps(
    *,
    steps: tuple[PacketPathExecutionStep, ...],
    plan: EvidencePlan,
    negative: PacketPathNegativeAssembly | None,
) -> None:
    identities = tuple(item.step_id for item in steps)
    if len(set(identities)) != len(identities):
        raise EvidenceMaterializationError("packet-path execution step identities must be unique")
    if not steps or steps[0].step_id is not PacketPathStepId.SETUP:
        raise EvidenceMaterializationError("packet-path execution must begin with setup")

    expected_attempt_phases = {
        "baseline",
        "pre-trigger",
        "activation-settlement",
        "subject-active-cut",
        "non-target-control",
        "recovery-1",
        "recovery-2",
        "stability",
    }
    actual_attempt_phases = {
        item.attempt_phase for item in steps if item.attempt_phase is not None
    }
    allowed_missing: set[str] = set()
    if negative is not None:
        if negative.settlement_behavior is SettlementBehavior.OMIT_INDEPENDENT_PROBE:
            allowed_missing.add("activation-settlement")
        if negative.recovery_behavior is RecoveryBehavior.OMIT_SECOND_AND_STABILITY:
            allowed_missing.update(("recovery-2", "stability"))
    if actual_attempt_phases != expected_attempt_phases - allowed_missing:
        raise EvidenceMaterializationError("packet-path execution attempt phase set drift")

    if not actual_attempt_phases.issubset(set(plan.phase_program)):
        raise EvidenceMaterializationError(
            "packet-path execution contains attempt phase outside sealed phase program"
        )

    for item in steps:
        if item.is_attempt:
            if item.target is None or not item.connection_targets:
                raise EvidenceMaterializationError(
                    f"packet-path attempt {item.step_id.value!r} lacks literal target"
                )
            if item.connection_targets[0] != item.target:
                raise EvidenceMaterializationError(
                    f"packet-path attempt {item.step_id.value!r} primary connection target drift"
                )
        elif item.target is not None or item.connection_targets:
            raise EvidenceMaterializationError(
                f"non-attempt packet-path step {item.step_id.value!r} carries connection targets"
            )

    cleanup_index = _index(list(steps), PacketPathStepId.CLEANUP)
    sentinel_index = _index(list(steps), PacketPathStepId.CLEANUP_SENTINEL)
    residual_negative = (
        negative is not None
        and negative.cleanup_behavior
        is CleanupBehavior.DEFER_RUN_OWNED_CLEANUP_UNTIL_SENTINEL
    )
    if residual_negative and not sentinel_index < cleanup_index:
        raise EvidenceMaterializationError(
            "residual-state negative must observe run-owned state before final cleanup"
        )
    if not residual_negative and not cleanup_index < sentinel_index:
        raise EvidenceMaterializationError(
            "positive packet-path cleanup sentinel must run after cleanup"
        )


def _index(steps: list[PacketPathExecutionStep], step_id: PacketPathStepId) -> int:
    matches = [index for index, item in enumerate(steps) if item.step_id is step_id]
    if len(matches) != 1:
        raise EvidenceMaterializationError(
            f"expected exactly one packet-path execution step {step_id.value!r}"
        )
    return matches[0]

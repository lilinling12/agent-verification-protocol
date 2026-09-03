"""Provider-neutral comparator for the reviewed NPR-011 evidence predicates.

This module evaluates retained Network Control project evidence only. It is
non-normative, test-only, and deliberately contains no fault-provider or runtime
branching. Mechanism controllers may produce observations; they do not own the
portable assessment.
"""

from __future__ import annotations

from dataclasses import dataclass

from .evidence_core import (
    AssessmentClass,
    EvidenceAssessment,
    EvidenceMaterializationError,
    InitiationFacts,
    SealedPlan,
    assess_initiation_integrity,
)

_REQUIRED_ATTEMPT_PHASES = (
    "baseline",
    "pre-trigger",
    "activation-settlement",
    "subject-active-cut",
    "recovery-1",
    "recovery-2",
    "stability",
)


@dataclass(frozen=True, slots=True)
class AttemptObservation:
    """Normalized evidence for one certified fresh attempt.

    ``path_id`` binds the observation to the logical path already sealed in the
    evidence plan. ``completed`` is the provider-neutral exact-exchange predicate
    produced by the reviewed exact-byte client. Native socket errors and provider
    state are intentionally absent from this assessment surface.
    """

    phase_id: str
    path_id: str
    attempt_id: str
    completed: bool
    mismatch_observed: bool
    observation_budget_expired: bool
    front_initiations: InitiationFacts
    upstream_initiations: InitiationFacts
    validity_problems: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PortableEvidenceObservations:
    """Normalized C1-C12 evidence inputs for one sealed plan."""

    baseline: AttemptObservation | None
    pre_trigger: AttemptObservation | None
    activation_settlement: AttemptObservation | None
    subject_active_cut: AttemptObservation | None
    recovery_1: AttemptObservation | None
    recovery_2: AttemptObservation | None
    stability: AttemptObservation | None
    non_target_control: AttemptObservation | None = None
    cleanup_noninterference_ok: bool | None = None
    security_projection_ok: bool | None = None
    evidence_validity_problems: tuple[str, ...] = ()
    infrastructure_problems: tuple[str, ...] = ()
    unsupported_materialization_problems: tuple[str, ...] = ()


def compare_portable_evidence(
    sealed_plan: SealedPlan,
    observations: PortableEvidenceObservations,
) -> EvidenceAssessment:
    """Evaluate reviewed C1-C12 predicates without mechanism-specific logic.

    Evidence-integrity uncertainty is resolved before semantic conclusions.
    Once evidence is trustworthy, semantic failures are reported in predicate
    order so cleanup/security failures cannot overwrite an earlier root cause.
    """

    try:
        sealed_plan.verify()
    except EvidenceMaterializationError as exc:
        return _assessment(AssessmentClass.EVIDENCE_INVALID, f"C1:plan-integrity:{exc}")

    plan = sealed_plan.plan
    missing_phases = tuple(phase for phase in _REQUIRED_ATTEMPT_PHASES if phase not in plan.phase_program)
    if missing_phases:
        return _assessment(
            AssessmentClass.EVIDENCE_INVALID,
            f"C1:phase-program-missing:{missing_phases[0]}",
            *(f"C1:phase-program-missing:{phase}" for phase in missing_phases[1:]),
        )

    phase_observations = _phase_observations(observations)
    required = {phase: phase_observations.get(phase) for phase in _REQUIRED_ATTEMPT_PHASES}
    missing = tuple(phase for phase, item in required.items() if item is None)
    if missing:
        return _assessment(
            AssessmentClass.EVIDENCE_INVALID,
            f"C1:missing-observation:{missing[0]}",
            *(f"C1:missing-observation:{phase}" for phase in missing[1:]),
        )

    control = observations.non_target_control
    if plan.has_non_target_control and control is None:
        return _assessment(AssessmentClass.EVIDENCE_INVALID, "C6:missing-observation:non-target-control")
    if not plan.has_non_target_control and control is not None:
        return _assessment(AssessmentClass.EVIDENCE_INVALID, "C1:unexpected-observation:non-target-control")

    phase_binding_problems = tuple(
        f"C1:phase-binding:{expected}!={item.phase_id}"
        for expected, item in required.items()
        if item is not None and item.phase_id != expected
    )
    if control is not None and control.phase_id != "non-target-control":
        phase_binding_problems += (
            f"C1:phase-binding:non-target-control!={control.phase_id}",
        )
    if phase_binding_problems:
        return _assessment(
            AssessmentClass.EVIDENCE_INVALID,
            phase_binding_problems[0],
            *phase_binding_problems[1:],
        )

    path_binding_problems = tuple(
        f"C1:path-binding:{phase}:{plan.path_id}!={item.path_id}"
        for phase, item in required.items()
        if item is not None and item.path_id != plan.path_id
    )
    if control is not None:
        control_path_id = plan.non_target_path_id
        if control_path_id is None:
            path_binding_problems += ("C1:path-binding:non-target-control:unmaterialized",)
        elif control.path_id != control_path_id:
            path_binding_problems += (
                f"C1:path-binding:non-target-control:{control_path_id}!={control.path_id}",
            )
    if path_binding_problems:
        return _assessment(
            AssessmentClass.EVIDENCE_INVALID,
            path_binding_problems[0],
            *path_binding_problems[1:],
        )

    certified = [item for item in required.values() if item is not None]
    if control is not None:
        certified.append(control)

    structural_problems = _attempt_structure_problems(certified)
    validity_problems = tuple(observations.evidence_validity_problems) + tuple(
        f"{item.phase_id}:{problem}"
        for item in certified
        for problem in item.validity_problems
    )
    if structural_problems or validity_problems:
        problems = tuple(structural_problems) + tuple(
            f"evidence-invalid:{problem}" for problem in validity_problems
        )
        return _assessment(AssessmentClass.EVIDENCE_INVALID, problems[0], *problems[1:])

    # A witness ambiguity invalidates C10 evidence before any semantic verdict,
    # even if another retained observation would otherwise show a violation.
    initiation_assessments = tuple(
        (item.phase_id, assess_initiation_integrity(item.front_initiations, item.upstream_initiations))
        for item in certified
    )
    witness_invalid = tuple(
        f"C10:{phase}:{problem}"
        for phase, assessment in initiation_assessments
        if assessment.classification is AssessmentClass.EVIDENCE_INVALID
        for problem in _all_assessment_problems(assessment)
    )
    if witness_invalid:
        return _assessment(
            AssessmentClass.EVIDENCE_INVALID,
            witness_invalid[0],
            *witness_invalid[1:],
        )

    if observations.unsupported_materialization_problems:
        problems = tuple(
            f"materialization-unsupported:{problem}"
            for problem in observations.unsupported_materialization_problems
        )
        return _assessment(
            AssessmentClass.UNSUPPORTED_MATERIALIZATION,
            problems[0],
            *problems[1:],
        )

    if observations.infrastructure_problems:
        problems = tuple(
            f"infrastructure:{problem}" for problem in observations.infrastructure_problems
        )
        return _assessment(
            AssessmentClass.INFRASTRUCTURE_FAILURE,
            problems[0],
            *problems[1:],
        )

    semantic_problems: list[str] = []

    for phase, predicate in (("baseline", "C2"), ("pre-trigger", "C3")):
        item = required[phase]
        assert item is not None
        if not _successful_exchange(item):
            semantic_problems.append(f"{predicate}:{phase}:exact-exchange-not-completed")

    for phase, predicate in (("activation-settlement", "C4"), ("subject-active-cut", "C5")):
        item = required[phase]
        assert item is not None
        if item.completed:
            semantic_problems.append(f"{predicate}:{phase}:exact-exchange-completed")

    if control is not None and not _successful_exchange(control):
        semantic_problems.append("C6:non-target-control:exact-exchange-not-completed")

    for phase, predicate in (("recovery-1", "C7"), ("recovery-2", "C8"), ("stability", "C9")):
        item = required[phase]
        assert item is not None
        if not _successful_exchange(item):
            semantic_problems.append(f"{predicate}:{phase}:exact-exchange-not-completed")

    for phase, assessment in initiation_assessments:
        if assessment.classification is AssessmentClass.SEMANTIC_VIOLATION:
            semantic_problems.extend(
                f"C10:{phase}:{problem}" for problem in _all_assessment_problems(assessment)
            )

    if observations.cleanup_noninterference_ok is None:
        return _assessment(AssessmentClass.EVIDENCE_INVALID, "C11:cleanup-observation-missing")
    if not observations.cleanup_noninterference_ok:
        semantic_problems.append("C11:cleanup-noninterference-failed")

    if observations.security_projection_ok is None:
        return _assessment(AssessmentClass.EVIDENCE_INVALID, "C12:security-observation-missing")
    if not observations.security_projection_ok:
        semantic_problems.append("C12:security-projection-failed")

    if semantic_problems:
        return _assessment(
            AssessmentClass.SEMANTIC_VIOLATION,
            semantic_problems[0],
            *semantic_problems[1:],
        )
    return EvidenceAssessment(AssessmentClass.SATISFIED)


def _phase_observations(
    observations: PortableEvidenceObservations,
) -> dict[str, AttemptObservation | None]:
    return {
        "baseline": observations.baseline,
        "pre-trigger": observations.pre_trigger,
        "activation-settlement": observations.activation_settlement,
        "subject-active-cut": observations.subject_active_cut,
        "recovery-1": observations.recovery_1,
        "recovery-2": observations.recovery_2,
        "stability": observations.stability,
        "non-target-control": observations.non_target_control,
    }


def _attempt_structure_problems(observations: list[AttemptObservation]) -> tuple[str, ...]:
    problems: list[str] = []
    attempt_ids: set[str] = set()
    for item in observations:
        if not item.phase_id:
            problems.append("C1:attempt-phase-empty")
        if not item.path_id:
            problems.append(f"C1:{item.phase_id or 'unknown'}:path-id-empty")
        if not item.attempt_id:
            problems.append(f"C1:{item.phase_id or 'unknown'}:attempt-id-empty")
        elif item.attempt_id in attempt_ids:
            problems.append(f"C1:attempt-id-reused:{item.attempt_id}")
        else:
            attempt_ids.add(item.attempt_id)
        if item.completed and item.mismatch_observed:
            problems.append(f"C1:{item.phase_id}:completed-with-byte-mismatch")
        if item.completed and item.observation_budget_expired:
            problems.append(f"C1:{item.phase_id}:completed-after-budget-expiry")

    expected_phases = set(_REQUIRED_ATTEMPT_PHASES) | {"non-target-control"}
    for item in observations:
        if item.phase_id not in expected_phases:
            problems.append(f"C1:unexpected-attempt-phase:{item.phase_id}")
    return tuple(dict.fromkeys(problems))


def _successful_exchange(observation: AttemptObservation) -> bool:
    return (
        observation.completed
        and not observation.mismatch_observed
        and not observation.observation_budget_expired
    )


def _all_assessment_problems(assessment: EvidenceAssessment) -> tuple[str, ...]:
    if assessment.primary_problem is None:
        return assessment.secondary_problems
    return (assessment.primary_problem, *assessment.secondary_problems)


def _assessment(
    classification: AssessmentClass,
    primary: str,
    *secondary: str,
) -> EvidenceAssessment:
    return EvidenceAssessment(
        classification=classification,
        primary_problem=primary,
        secondary_problems=tuple(secondary),
    )

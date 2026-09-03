"""Provider-neutral C1-C12 comparator tests for Network Control evidence."""

from __future__ import annotations

import dataclasses
import unittest

from acceptance.network_control.evidence_core import (
    AssessmentClass,
    AttemptFactory,
    EvidenceMaterializationError,
    EvidencePlan,
    ExchangeProgram,
    InitiationFacts,
    MaterializedEndpoint,
)
from acceptance.network_control.portable_comparator import (
    AttemptObservation,
    PortableEvidenceObservations,
    compare_portable_evidence,
)

_BASELINE = "44f5e4884835fbb7e5c7d98960d7cbd6cce6f798"
_AEP_PATH = "rfcs/AEP-0012-network-control-resource-profile.md"
_SELECTED_PATH = "selected-path"
_CONTROL_PATH = "selected-path::non-target-control"


def endpoint(address: str, port: int, role: str) -> MaterializedEndpoint:
    return MaterializedEndpoint(
        family="ipv6" if ":" in address else "ipv4",
        address=address,
        port=port,
        role=role,
    )


def plan(*, with_control: bool = True) -> EvidencePlan:
    kwargs: dict[str, object] = {}
    if with_control:
        kwargs.update(
            non_target_subject_destination=endpoint("127.0.0.1", 42003, "control-subject-destination"),
            non_target_upstream_fixture=endpoint("127.0.0.1", 42004, "control-upstream-fixture"),
        )
    return EvidencePlan(
        design_revision="NPR-011-portable-comparator-v0.1",
        semantic_baseline_commit=_BASELINE,
        semantic_baseline_path=_AEP_PATH,
        run_id="run-comparator-001",
        path_id=_SELECTED_PATH,
        subject_destination=endpoint("127.0.0.1", 42001, "subject-destination"),
        upstream_fixture=endpoint("127.0.0.1", 42002, "upstream-fixture"),
        exchange_program=ExchangeProgram(
            program_id="exact-byte-v0.1",
            request_prefix=b"REQ\x00",
            request_suffix=b"\x00END",
            response_prefix=b"RESP\x00",
            response_suffix=b"\x00END",
        ),
        observation_budget_ns=1_000_000_000,
        **kwargs,
    )


def facts(
    channel: str,
    *,
    total: int = 1,
    expected: int = 1,
    alternate: int = 0,
    validity: tuple[str, ...] = (),
) -> InitiationFacts:
    return InitiationFacts(
        channel=channel,
        total_initiations=total,
        expected_target_initiations=expected,
        alternate_target_initiations=alternate,
        raw_syn_packets=max(1, total),
        retransmitted_syn_packets=0,
        validity_problems=validity,
    )


def attempt(phase: str, *, completed: bool, ordinal: int) -> AttemptObservation:
    path_id = _CONTROL_PATH if phase == "non-target-control" else _SELECTED_PATH
    return AttemptObservation(
        phase_id=phase,
        path_id=path_id,
        attempt_id=f"attempt-{ordinal}-{phase}",
        completed=completed,
        mismatch_observed=False,
        observation_budget_expired=not completed,
        front_initiations=facts("W-front"),
        upstream_initiations=facts("W-upstream"),
    )


def positive_observations(*, with_control: bool = True) -> PortableEvidenceObservations:
    return PortableEvidenceObservations(
        baseline=attempt("baseline", completed=True, ordinal=1),
        pre_trigger=attempt("pre-trigger", completed=True, ordinal=2),
        activation_settlement=attempt("activation-settlement", completed=False, ordinal=3),
        subject_active_cut=attempt("subject-active-cut", completed=False, ordinal=4),
        non_target_control=(
            attempt("non-target-control", completed=True, ordinal=5) if with_control else None
        ),
        recovery_1=attempt("recovery-1", completed=True, ordinal=6),
        recovery_2=attempt("recovery-2", completed=True, ordinal=7),
        stability=attempt("stability", completed=True, ordinal=8),
        cleanup_noninterference_ok=True,
        security_projection_ok=True,
    )


class EvidencePlanControlBindingTests(unittest.TestCase):
    def test_non_target_control_endpoints_are_an_atomic_pair(self) -> None:
        with self.assertRaises(EvidenceMaterializationError):
            dataclasses.replace(plan(), non_target_upstream_fixture=None)
        with self.assertRaises(EvidenceMaterializationError):
            dataclasses.replace(
                plan(),
                non_target_subject_destination=plan().subject_destination,
            )
        with self.assertRaises(EvidenceMaterializationError):
            dataclasses.replace(
                plan(),
                non_target_upstream_fixture=plan().upstream_fixture,
            )

    def test_control_binding_seals_distinct_logical_path_identity(self) -> None:
        without_control = plan(with_control=False).seal()
        with_control = plan(with_control=True).seal()
        self.assertIsNone(without_control.plan.non_target_path_id)
        self.assertEqual(with_control.plan.non_target_path_id, _CONTROL_PATH)
        self.assertNotEqual(without_control.ref.sha256, with_control.ref.sha256)
        self.assertNotIn(b"nonTargetControl", without_control.exact_bytes)
        self.assertIn(b'"pathId":"selected-path::non-target-control"', with_control.exact_bytes)

    def test_attempt_factory_binds_control_attempt_to_control_path(self) -> None:
        evidence_plan = plan()
        factory = AttemptFactory(b"P" * 32)
        selected = factory.issue(evidence_plan, phase_id="baseline", ordinal=1)
        control = factory.issue(evidence_plan, phase_id="non-target-control", ordinal=2)
        self.assertEqual(selected.path_id, _SELECTED_PATH)
        self.assertEqual(control.path_id, _CONTROL_PATH)
        self.assertNotEqual(selected.challenge, control.challenge)
        self.assertNotEqual(selected.attempt_id, control.attempt_id)

    def test_control_attempt_requires_materialized_control_path(self) -> None:
        factory = AttemptFactory(b"Q" * 32)
        with self.assertRaises(EvidenceMaterializationError):
            factory.issue(plan(with_control=False), phase_id="non-target-control", ordinal=1)


class PortableComparatorTests(unittest.TestCase):
    def test_complete_positive_evidence_satisfies_c1_through_c12(self) -> None:
        assessment = compare_portable_evidence(plan().seal(), positive_observations())
        self.assertEqual(assessment.classification, AssessmentClass.SATISFIED)
        self.assertIsNone(assessment.primary_problem)

    def test_optional_control_is_not_required_when_plan_does_not_bind_one(self) -> None:
        assessment = compare_portable_evidence(
            plan(with_control=False).seal(),
            positive_observations(with_control=False),
        )
        self.assertEqual(assessment.classification, AssessmentClass.SATISFIED)

    def test_missing_required_observation_fails_closed(self) -> None:
        evidence = dataclasses.replace(positive_observations(), baseline=None)
        assessment = compare_portable_evidence(plan().seal(), evidence)
        self.assertEqual(assessment.classification, AssessmentClass.EVIDENCE_INVALID)
        self.assertEqual(assessment.primary_problem, "C1:missing-observation:baseline")

    def test_phase_identity_drift_fails_closed(self) -> None:
        evidence = positive_observations()
        wrong = dataclasses.replace(evidence.baseline, phase_id="pre-trigger")
        assessment = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(evidence, baseline=wrong),
        )
        self.assertEqual(assessment.classification, AssessmentClass.EVIDENCE_INVALID)
        self.assertIn("phase-binding", assessment.primary_problem or "")

    def test_selected_path_identity_drift_fails_closed(self) -> None:
        evidence = positive_observations()
        wrong = dataclasses.replace(evidence.baseline, path_id="other-selected-path")
        assessment = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(evidence, baseline=wrong),
        )
        self.assertEqual(assessment.classification, AssessmentClass.EVIDENCE_INVALID)
        self.assertIn("path-binding:baseline", assessment.primary_problem or "")

    def test_control_path_identity_drift_fails_closed(self) -> None:
        evidence = positive_observations()
        wrong = dataclasses.replace(evidence.non_target_control, path_id=_SELECTED_PATH)
        assessment = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(evidence, non_target_control=wrong),
        )
        self.assertEqual(assessment.classification, AssessmentClass.EVIDENCE_INVALID)
        self.assertIn("path-binding:non-target-control", assessment.primary_problem or "")

    def test_attempt_identity_reuse_fails_closed(self) -> None:
        evidence = positive_observations()
        reused = dataclasses.replace(
            evidence.subject_active_cut,
            attempt_id=evidence.activation_settlement.attempt_id,
        )
        assessment = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(evidence, subject_active_cut=reused),
        )
        self.assertEqual(assessment.classification, AssessmentClass.EVIDENCE_INVALID)
        self.assertIn("attempt-id-reused", assessment.primary_problem or "")

    def test_invalid_witness_precedes_semantic_conclusion(self) -> None:
        evidence = positive_observations()
        invalid_front = facts("W-front", validity=("capture-drops=1",))
        invalid_baseline = dataclasses.replace(
            evidence.baseline,
            completed=False,
            observation_budget_expired=True,
            front_initiations=invalid_front,
        )
        assessment = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(evidence, baseline=invalid_baseline),
        )
        self.assertEqual(assessment.classification, AssessmentClass.EVIDENCE_INVALID)
        self.assertIn("C10:baseline:witness-invalid:capture-drops=1", assessment.primary_problem or "")

    def test_baseline_failure_localizes_c2(self) -> None:
        evidence = positive_observations()
        assessment = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(
                evidence,
                baseline=dataclasses.replace(
                    evidence.baseline,
                    completed=False,
                    observation_budget_expired=True,
                ),
            ),
        )
        self.assertEqual(assessment.classification, AssessmentClass.SEMANTIC_VIOLATION)
        self.assertEqual(assessment.primary_problem, "C2:baseline:exact-exchange-not-completed")

    def test_pre_trigger_effect_localizes_c3(self) -> None:
        evidence = positive_observations()
        assessment = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(
                evidence,
                pre_trigger=dataclasses.replace(
                    evidence.pre_trigger,
                    completed=False,
                    observation_budget_expired=True,
                ),
            ),
        )
        self.assertEqual(assessment.primary_problem, "C3:pre-trigger:exact-exchange-not-completed")

    def test_invalid_settlement_is_not_repaired_by_subject_cut(self) -> None:
        evidence = positive_observations()
        assessment = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(
                evidence,
                activation_settlement=dataclasses.replace(
                    evidence.activation_settlement,
                    completed=True,
                    observation_budget_expired=False,
                ),
            ),
        )
        self.assertEqual(assessment.primary_problem, "C4:activation-settlement:exact-exchange-completed")

    def test_subject_active_exchange_completion_localizes_c5(self) -> None:
        evidence = positive_observations()
        assessment = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(
                evidence,
                subject_active_cut=dataclasses.replace(
                    evidence.subject_active_cut,
                    completed=True,
                    observation_budget_expired=False,
                ),
            ),
        )
        self.assertEqual(assessment.primary_problem, "C5:subject-active-cut:exact-exchange-completed")

    def test_collateral_target_failure_localizes_c6(self) -> None:
        evidence = positive_observations()
        assessment = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(
                evidence,
                non_target_control=dataclasses.replace(
                    evidence.non_target_control,
                    completed=False,
                    observation_budget_expired=True,
                ),
            ),
        )
        self.assertEqual(assessment.primary_problem, "C6:non-target-control:exact-exchange-not-completed")

    def test_recovery_and_stability_are_independent_predicates(self) -> None:
        for field, predicate in (("recovery_1", "C7"), ("recovery_2", "C8"), ("stability", "C9")):
            with self.subTest(field=field):
                evidence = positive_observations()
                broken = dataclasses.replace(
                    getattr(evidence, field),
                    completed=False,
                    observation_budget_expired=True,
                )
                assessment = compare_portable_evidence(
                    plan().seal(),
                    dataclasses.replace(evidence, **{field: broken}),
                )
                self.assertEqual(assessment.classification, AssessmentClass.SEMANTIC_VIOLATION)
                self.assertTrue((assessment.primary_problem or "").startswith(f"{predicate}:"))

    def test_hidden_retry_localizes_c10(self) -> None:
        evidence = positive_observations()
        retry = facts("W-upstream", total=2, expected=2)
        assessment = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(
                evidence,
                subject_active_cut=dataclasses.replace(
                    evidence.subject_active_cut,
                    upstream_initiations=retry,
                ),
            ),
        )
        self.assertEqual(assessment.classification, AssessmentClass.SEMANTIC_VIOLATION)
        self.assertIn("C10:subject-active-cut", assessment.primary_problem or "")

    def test_cleanup_failure_is_primary_only_when_no_earlier_predicate_failed(self) -> None:
        evidence = positive_observations()
        cleanup_only = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(evidence, cleanup_noninterference_ok=False),
        )
        self.assertEqual(cleanup_only.primary_problem, "C11:cleanup-noninterference-failed")

        earlier = dataclasses.replace(
            evidence.baseline,
            completed=False,
            observation_budget_expired=True,
        )
        combined = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(
                evidence,
                baseline=earlier,
                cleanup_noninterference_ok=False,
            ),
        )
        self.assertEqual(combined.primary_problem, "C2:baseline:exact-exchange-not-completed")
        self.assertIn("C11:cleanup-noninterference-failed", combined.secondary_problems)

    def test_schedule_or_control_projection_failure_localizes_c12(self) -> None:
        assessment = compare_portable_evidence(
            plan().seal(),
            dataclasses.replace(positive_observations(), security_projection_ok=False),
        )
        self.assertEqual(assessment.classification, AssessmentClass.SEMANTIC_VIOLATION)
        self.assertEqual(assessment.primary_problem, "C12:security-projection-failed")

    def test_missing_cleanup_or_security_observation_fails_closed(self) -> None:
        for field, predicate in (("cleanup_noninterference_ok", "C11"), ("security_projection_ok", "C12")):
            with self.subTest(field=field):
                assessment = compare_portable_evidence(
                    plan().seal(),
                    dataclasses.replace(positive_observations(), **{field: None}),
                )
                self.assertEqual(assessment.classification, AssessmentClass.EVIDENCE_INVALID)
                self.assertTrue((assessment.primary_problem or "").startswith(f"{predicate}:"))


if __name__ == "__main__":
    unittest.main()

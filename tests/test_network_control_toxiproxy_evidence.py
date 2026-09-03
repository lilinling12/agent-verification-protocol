"""TEL-002 tests for finite Toxiproxy orchestration and negative-mode honesty."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from acceptance.network_control.evidence_core import (
    ArtifactStore,
    AssessmentClass,
    EvidencePlan,
    ExchangeProgram,
    InitiationFacts,
    MaterializedEndpoint,
)
from acceptance.network_control.portable_comparator import AttemptObservation
from acceptance.network_control.toxiproxy_binding import (
    ControlSnapshot,
    ProxyBinding,
    ToxiproxyArtifact,
    ToxiproxyRunTopology,
)
from acceptance.network_control.toxiproxy_evidence import (
    NegativeMode,
    PhaseExecution,
    ToxiproxyPhaseRunner,
)

_BASELINE = "883956784e57152537b11aaf65143209fc131429"
_AEP_PATH = "rfcs/AEP-0012-network-control-resource-profile.md"


def endpoint(address: str, port: int, role: str) -> MaterializedEndpoint:
    return MaterializedEndpoint(family="ipv4", address=address, port=port, role=role)


def evidence_plan() -> EvidencePlan:
    return EvidencePlan(
        design_revision="TEL-002-v0.1",
        semantic_baseline_commit=_BASELINE,
        semantic_baseline_path=_AEP_PATH,
        run_id="tel002-run",
        path_id="selected-path",
        subject_destination=endpoint("172.30.40.2", 41001, "subject-destination"),
        upstream_fixture=endpoint("172.30.40.3", 42001, "upstream-fixture"),
        non_target_subject_destination=endpoint(
            "172.30.40.2", 41002, "control-subject-destination"
        ),
        non_target_upstream_fixture=endpoint("172.30.40.4", 42002, "control-fixture"),
        exchange_program=ExchangeProgram(
            program_id="tel002-exact-byte-v0.1",
            request_prefix=b"REQ\x00",
            request_suffix=b"\x00END",
            response_prefix=b"RESP\x00",
            response_suffix=b"\x00END",
        ),
        observation_budget_ns=1_000_000_000,
    )


def facts(channel: str, *, total: int = 1) -> InitiationFacts:
    return InitiationFacts(
        channel=channel,
        total_initiations=total,
        expected_target_initiations=total,
        alternate_target_initiations=0,
        raw_syn_packets=total,
        retransmitted_syn_packets=0,
    )


class StatefulAdmin:
    def __init__(self) -> None:
        self.selected_active = False
        self.control_active = False
        self.operations: list[str] = []

    def create_proxy(self, binding: ProxyBinding) -> ControlSnapshot:
        self.operations.append(f"proxy:{binding.name}")
        return ControlSnapshot(f"POST proxy {binding.name}", 200, b"{}")

    def create_upstream_timeout_cut(self, proxy_name: str, *, toxic_name: str) -> ControlSnapshot:
        self.operations.append(f"cut:{proxy_name}:{toxic_name}")
        if proxy_name.startswith("selected-"):
            self.selected_active = True
        else:
            self.control_active = True
        return ControlSnapshot(f"POST toxic {proxy_name}/{toxic_name}", 200, b"{}")

    def delete_toxic(self, proxy_name: str, toxic_name: str) -> ControlSnapshot:
        self.operations.append(f"clear:{proxy_name}:{toxic_name}")
        if proxy_name.startswith("selected-"):
            self.selected_active = False
        else:
            self.control_active = False
        return ControlSnapshot(f"DELETE toxic {proxy_name}/{toxic_name}", 204, b"")


class RunnerHarness:
    def __init__(self, *, artifact_store: ArtifactStore | None = None) -> None:
        self.plan = evidence_plan()
        self.sealed = self.plan.seal()
        self.admin = StatefulAdmin()
        self.selected = ProxyBinding(
            "selected-tel002",
            self.plan.subject_destination,
            self.plan.upstream_fixture,
        )
        assert self.plan.non_target_subject_destination is not None
        assert self.plan.non_target_upstream_fixture is not None
        self.control = ProxyBinding(
            "control-tel002",
            self.plan.non_target_subject_destination,
            self.plan.non_target_upstream_fixture,
        )
        self.attempt_calls: list[tuple[str, bool, NegativeMode | None]] = []
        self.artifact_store = artifact_store

    def runner(self) -> ToxiproxyPhaseRunner:
        return ToxiproxyPhaseRunner(
            sealed_plan=self.sealed,
            admin=self.admin,  # type: ignore[arg-type]
            selected_binding=self.selected,
            control_binding=self.control,
            certified_attempt=self.certified_attempt,
            cleanup_sentinel=self.cleanup_sentinel,
            security_projection_check=self.security_check,
            artifact_store=self.artifact_store,
            artifact=ToxiproxyArtifact.reviewed("linux/amd64"),
            topology=ToxiproxyRunTopology.for_run(self.plan.run_id),
        )

    def certified_attempt(
        self,
        phase: str,
        privileged: bool,
        negative_mode: NegativeMode | None,
    ) -> PhaseExecution:
        self.attempt_calls.append((phase, privileged, negative_mode))
        control_phase = phase == "non-target-control"
        active = self.admin.control_active if control_phase else self.admin.selected_active
        completed = not active
        path_id = self.plan.non_target_path_id if control_phase else self.plan.path_id
        assert path_id is not None
        upstream_total = 2 if negative_mode is NegativeMode.HIDDEN_RETRY_FALLBACK else 1
        observation = AttemptObservation(
            phase_id=phase,
            path_id=path_id,
            attempt_id=f"attempt-{len(self.attempt_calls)}-{phase}",
            completed=completed,
            mismatch_observed=False,
            observation_budget_expired=not completed,
            front_initiations=facts("W-front"),
            upstream_initiations=facts("W-upstream", total=upstream_total),
        )
        return PhaseExecution(observation=observation)

    @staticmethod
    def cleanup_sentinel(intentional_residual: bool) -> tuple[bool, tuple[str, ...]]:
        return (not intentional_residual, ())

    @staticmethod
    def security_check(intentional_leak: bool) -> tuple[bool, tuple[str, ...]]:
        return (not intentional_leak, ())


class PositiveLifecycleTests(unittest.TestCase):
    def test_positive_matrix_is_satisfied_and_preserves_phase_privilege(self) -> None:
        harness = RunnerHarness()
        result = harness.runner().execute()
        self.assertEqual(result.assessment.classification, AssessmentClass.SATISFIED)
        self.assertEqual(
            [call[0] for call in harness.attempt_calls],
            [
                "baseline",
                "pre-trigger",
                "activation-settlement",
                "subject-active-cut",
                "non-target-control",
                "recovery-1",
                "recovery-2",
                "stability",
            ],
        )
        privilege = {phase: privileged for phase, privileged, _mode in harness.attempt_calls}
        self.assertTrue(privilege["activation-settlement"])
        self.assertFalse(privilege["subject-active-cut"])
        self.assertTrue(privilege["recovery-1"])
        self.assertTrue(privilege["recovery-2"])
        self.assertTrue(privilege["stability"])

    def test_provider_ack_does_not_replace_settlement_or_recovery_attempts(self) -> None:
        harness = RunnerHarness()
        harness.runner().execute()
        phases = [phase for phase, _privileged, _mode in harness.attempt_calls]
        self.assertIn("activation-settlement", phases)
        self.assertEqual(phases[-3:], ["recovery-1", "recovery-2", "stability"])
        self.assertTrue(any(operation.startswith("cut:selected-") for operation in harness.admin.operations))
        self.assertTrue(any(operation.startswith("clear:selected-") for operation in harness.admin.operations))

    def test_implementation_record_retains_provider_provenance_not_provider_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ArtifactStore(Path(temporary))
            harness = RunnerHarness(artifact_store=store)
            result = harness.runner().execute()
            assert result.implementation_record_ref is not None
            document = json.loads(store.read_verified(result.implementation_record_ref))
            self.assertEqual(document["format"], "avp-project-toxiproxy-terminating-evidence-v0.1")
            self.assertEqual(document["assessment"]["classification"], "SATISFIED")
            self.assertEqual(document["toxiproxy"]["version"], "2.12.0")
            self.assertIn("@sha256:", document["toxiproxy"]["imageRef"])
            self.assertEqual(document["comparatorRevision"], "npr011-portable-c1-c12-v0.1")
            self.assertNotIn("providerVerdict", document)


class NegativeMatrixTests(unittest.TestCase):
    def test_all_required_negative_directions_are_rejected(self) -> None:
        expectations = {
            NegativeMode.BYPASS_FAULT: (AssessmentClass.SEMANTIC_VIOLATION, "C4:"),
            NegativeMode.EARLY_ACTIVATION: (AssessmentClass.SEMANTIC_VIOLATION, "C3:"),
            NegativeMode.FALSE_SETTLED: (AssessmentClass.EVIDENCE_INVALID, "C1:missing-observation"),
            NegativeMode.FALSE_RECOVERY: (AssessmentClass.EVIDENCE_INVALID, "C1:missing-observation"),
            NegativeMode.SCHEDULE_LEAK: (AssessmentClass.SEMANTIC_VIOLATION, "C12:"),
            NegativeMode.HIDDEN_RETRY_FALLBACK: (AssessmentClass.SEMANTIC_VIOLATION, "C10:"),
            NegativeMode.COLLATERAL_TARGET: (AssessmentClass.SEMANTIC_VIOLATION, "C6:"),
            NegativeMode.RESIDUAL_STATE_CLEANUP_FAILURE: (
                AssessmentClass.SEMANTIC_VIOLATION,
                "C11:",
            ),
        }
        for mode, (classification, prefix) in expectations.items():
            with self.subTest(mode=mode.value):
                harness = RunnerHarness()
                result = harness.runner().execute(negative_mode=mode)
                self.assertEqual(result.assessment.classification, classification)
                self.assertTrue((result.assessment.primary_problem or "").startswith(prefix))

    def test_hidden_retry_is_requested_as_real_faulty_attempt_not_fabricated_afterward(self) -> None:
        harness = RunnerHarness()
        harness.runner().execute(negative_mode=NegativeMode.HIDDEN_RETRY_FALLBACK)
        calls = [call for call in harness.attempt_calls if call[2] is not None]
        self.assertEqual(calls, [("subject-active-cut", False, NegativeMode.HIDDEN_RETRY_FALLBACK)])

    def test_early_activation_occurs_after_clean_baseline_before_pre_trigger(self) -> None:
        harness = RunnerHarness()
        result = harness.runner().execute(negative_mode=NegativeMode.EARLY_ACTIVATION)
        self.assertTrue(result.observations.baseline and result.observations.baseline.completed)
        self.assertTrue(result.observations.pre_trigger and not result.observations.pre_trigger.completed)
        self.assertEqual(result.assessment.primary_problem, "C3:pre-trigger:exact-exchange-not-completed")


if __name__ == "__main__":
    unittest.main()

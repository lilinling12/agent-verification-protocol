"""Regression checks for both required HiddenRetry/Fallback faulty assemblies."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import MethodType, SimpleNamespace
from unittest.mock import patch

from acceptance.network_control.evidence_core import (
    ArtifactStore,
    AssessmentClass,
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
from acceptance.network_control.toxiproxy_binding import DockerCli, ToxiproxyRunTopology
from acceptance.network_control.toxiproxy_evidence import PhaseExecution
from acceptance.network_control.toxiproxy_live_lab import LabHelperArtifact, ToxiproxyLiveLab
from acceptance.network_control.toxiproxy_negative_assemblies import UpstreamHiddenRetryLiveLab

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_network_control_toxiproxy_evidence.py"
_BASELINE = "bc01bc028e8bd37dbff324fb98d4b980aecbf5be"


def endpoint(address: str, port: int) -> MaterializedEndpoint:
    return MaterializedEndpoint("ipv4", address, port, "upstream-fixture")


def initiation(channel: str, total: int = 1) -> InitiationFacts:
    return InitiationFacts(
        channel=channel,
        total_initiations=total,
        expected_target_initiations=total,
        alternate_target_initiations=0,
        raw_syn_packets=total,
        retransmitted_syn_packets=0,
    )


def attempt(phase: str, *, completed: bool, upstream_total: int = 1) -> AttemptObservation:
    return AttemptObservation(
        phase_id=phase,
        path_id="selected-path",
        attempt_id=f"attempt-{phase}",
        completed=completed,
        mismatch_observed=False,
        observation_budget_expired=not completed,
        front_initiations=initiation("W-front"),
        upstream_initiations=initiation("W-upstream", upstream_total),
    )


class UpstreamFaultCommandTests(unittest.TestCase):
    def lab(self) -> UpstreamHiddenRetryLiveLab:
        lab = object.__new__(UpstreamHiddenRetryLiveLab)
        lab.topology = ToxiproxyRunTopology.for_run("upstream-hidden-retry")  # type: ignore[attr-defined]
        lab.helper_artifact = LabHelperArtifact.reviewed_amd64()  # type: ignore[attr-defined]
        lab.docker = DockerCli(executable="docker")  # type: ignore[attr-defined]
        lab._upstream_negative_attempt = None  # type: ignore[attr-defined]
        return lab

    def test_helper_shares_toxiproxy_namespace_and_has_no_packet_capability(self) -> None:
        lab = self.lab()
        fixture = endpoint(lab.topology.data_address.rsplit(".", 1)[0] + ".3", 42001)
        command = lab._upstream_fault_command("negative-helper", fixture)  # noqa: SLF001

        self.assertIn(f"container:{lab.topology.container_name}", command)
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop=ALL", command)
        self.assertIn("--security-opt=no-new-privileges", command)
        self.assertNotIn("--cap-add=NET_RAW", command)
        self.assertNotIn("/var/run/docker.sock", " ".join(command))
        self.assertIn(lab.helper_artifact.image_ref, command)

        script = command[-1]
        self.assertIn(repr(lab.topology.data_address), script)
        self.assertIn(repr(fixture.address), script)
        self.assertIn(str(fixture.port), script)
        self.assertIn("s.bind", script)
        self.assertIn("connect_ex", script)

    def test_upstream_fault_executes_before_subject_exchange_and_suppresses_front_fault(self) -> None:
        lab = self.lab()
        fixture = endpoint(lab.topology.data_address.rsplit(".", 1)[0] + ".3", 42001)
        lab._materialization = SimpleNamespace(  # type: ignore[attr-defined]
            selected_binding=SimpleNamespace(upstream=fixture)
        )
        ordering: list[str] = []

        def run_bounded(self: UpstreamHiddenRetryLiveLab, command: list[str], **_kwargs: object) -> object:
            del self, command
            ordering.append("upstream-helper")
            return SimpleNamespace(stdout="", stderr="", returncode=0)

        def base_exchange(_self: ToxiproxyLiveLab, **kwargs: object) -> dict[str, object]:
            ordering.append("subject-exchange")
            self.assertFalse(bool(kwargs["extra_connect"]))
            return {"completed": False}

        lab._run_bounded = MethodType(run_bounded, lab)  # type: ignore[method-assign]
        attempt_document = {"attemptId": "attempt-1", "phaseId": "subject-active-cut"}
        visible = MaterializedEndpoint("ipv4", lab.topology.data_address, 41001, "subject-destination")

        with patch.object(ToxiproxyLiveLab, "_execute_role_exchange", new=base_exchange):
            result = lab._execute_role_exchange(  # noqa: SLF001
                container_name="subject",
                endpoint=visible,
                attempt_document=attempt_document,
                extra_connect=True,
            )

        self.assertEqual(result, {"completed": False})
        self.assertEqual(ordering, ["upstream-helper", "subject-exchange"])
        self.assertIsNotNone(lab._upstream_negative_attempt)  # noqa: SLF001
        assert lab._upstream_negative_attempt is not None  # noqa: SLF001
        self.assertEqual(
            lab._upstream_negative_attempt["variant"],  # noqa: SLF001
            "same-namespace-upstream-extra-connect",
        )

    def test_negative_assembly_marker_is_retained_as_phase_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            lab = self.lab()
            lab.artifact_store = ArtifactStore(Path(temporary))  # type: ignore[attr-defined]
            lab._upstream_negative_attempt = {  # type: ignore[attr-defined]
                "format": "avp-project-hidden-retry-upstream-negative-v0.1",
                "variant": "same-namespace-upstream-extra-connect",
                "attemptId": "attempt-1",
            }
            observation = attempt("subject-active-cut", completed=False, upstream_total=2)
            base = PhaseExecution(observation=observation)
            with patch.object(ToxiproxyLiveLab, "certified_attempt", return_value=base):
                result = lab.certified_attempt("subject-active-cut", False, None)

            self.assertEqual(len(result.evidence_refs), 1)
            payload = lab.artifact_store.read_verified(result.evidence_refs[0])
            self.assertIn(b"same-namespace-upstream-extra-connect", payload)
            self.assertIsNone(lab._upstream_negative_attempt)  # noqa: SLF001

    def test_failed_attempt_cannot_leak_variant_marker_into_next_attempt(self) -> None:
        lab = self.lab()
        lab._upstream_negative_attempt = {"attemptId": "stale"}  # type: ignore[attr-defined]
        with patch.object(ToxiproxyLiveLab, "certified_attempt", side_effect=RuntimeError("boom")):
            with self.assertRaisesRegex(RuntimeError, "boom"):
                lab.certified_attempt("subject-active-cut", False, None)
        self.assertIsNone(lab._upstream_negative_attempt)  # noqa: SLF001


class UpstreamComparatorRegressionTests(unittest.TestCase):
    def test_same_comparator_rejects_upstream_only_extra_initiation_as_c10(self) -> None:
        plan = EvidencePlan(
            design_revision="TEL-002-v0.1",
            semantic_baseline_commit=_BASELINE,
            semantic_baseline_path="rfcs/AEP-0012-network-control-resource-profile.md",
            run_id="hidden-retry-upstream-comparator",
            path_id="selected-path",
            subject_destination=MaterializedEndpoint(
                "ipv4", "172.30.80.2", 41001, "subject-destination"
            ),
            upstream_fixture=MaterializedEndpoint(
                "ipv4", "172.30.80.3", 42001, "upstream-fixture"
            ),
            exchange_program=ExchangeProgram(
                "hidden-retry-regression",
                b"REQ",
                b"END",
                b"RESP",
                b"END",
            ),
            observation_budget_ns=1_000_000_000,
        )
        observations = PortableEvidenceObservations(
            baseline=attempt("baseline", completed=True),
            pre_trigger=attempt("pre-trigger", completed=True),
            activation_settlement=attempt("activation-settlement", completed=False),
            subject_active_cut=attempt(
                "subject-active-cut",
                completed=False,
                upstream_total=2,
            ),
            recovery_1=attempt("recovery-1", completed=True),
            recovery_2=attempt("recovery-2", completed=True),
            stability=attempt("stability", completed=True),
            cleanup_noninterference_ok=True,
            security_projection_ok=True,
        )

        assessment = compare_portable_evidence(plan.seal(), observations)

        self.assertEqual(assessment.classification, AssessmentClass.SEMANTIC_VIOLATION)
        self.assertTrue((assessment.primary_problem or "").startswith("C10:subject-active-cut:"))


class HiddenRetryCliVariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("run_network_control_toxiproxy_evidence", SCRIPT)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load TEL-002 evidence runner")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.module = module

    def test_default_hidden_retry_variant_preserves_front_assembly(self) -> None:
        variant, lab_type = self.module._resolve_hidden_retry_variant(  # noqa: SLF001
            negative_mode="HiddenRetry/Fallback",
            requested=None,
        )
        self.assertEqual(variant, "front-extra-connect")
        self.assertIs(lab_type, ToxiproxyLiveLab)

    def test_upstream_variant_selects_same_namespace_faulty_lab(self) -> None:
        variant, lab_type = self.module._resolve_hidden_retry_variant(  # noqa: SLF001
            negative_mode="HiddenRetry/Fallback",
            requested="upstream-extra-connect",
        )
        self.assertEqual(variant, "upstream-extra-connect")
        self.assertIs(lab_type, UpstreamHiddenRetryLiveLab)

    def test_variant_is_rejected_for_unrelated_negative_mode(self) -> None:
        with self.assertRaises(ValueError):
            self.module._resolve_hidden_retry_variant(  # noqa: SLF001
                negative_mode="BypassFault",
                requested="upstream-extra-connect",
            )


if __name__ == "__main__":
    unittest.main()

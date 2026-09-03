"""TEL-002 tests for retained live materialization provenance and cleanup semantics."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from acceptance.network_control.evidence_core import (
    ArtifactStore,
    AssessmentClass,
    EvidenceAssessment,
    EvidencePlan,
    ExchangeProgram,
    MaterializedEndpoint,
)
from acceptance.network_control.portable_comparator import PortableEvidenceObservations
from acceptance.network_control.toxiproxy_binding import ProxyBinding, ToxiproxyArtifact, ToxiproxyRunTopology
from acceptance.network_control.toxiproxy_evidence import TerminatingRunResult
from acceptance.network_control.toxiproxy_live_execution import (
    _retain_materialization_provenance,
    execute_live_matrix,
)
from acceptance.network_control.toxiproxy_live_lab import LabHelperArtifact, LabRoleAddresses, LiveMaterialization
from acceptance.network_control.witness_evidence import CaptureAssurance

_BASELINE = "883956784e57152537b11aaf65143209fc131429"


def endpoint(address: str, port: int, role: str) -> MaterializedEndpoint:
    return MaterializedEndpoint(family="ipv4", address=address, port=port, role=role)


class _FakeRunner:
    def __init__(self, result: TerminatingRunResult | None = None, error: BaseException | None = None) -> None:
        self.result = result
        self.error = error

    def execute(self, *, negative_mode: object = None) -> TerminatingRunResult:
        del negative_mode
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


class _FakeLab:
    pass


def materialized_lab(root: Path) -> _FakeLab:
    topology = ToxiproxyRunTopology.for_run("live-provenance")
    addresses = LabRoleAddresses.from_topology(topology)
    selected = ProxyBinding(
        "selected",
        endpoint(topology.data_address, 41001, "subject-destination"),
        endpoint(addresses.selected_fixture, 42001, "upstream-fixture"),
    )
    control = ProxyBinding(
        "control",
        endpoint(topology.data_address, 41002, "control-subject-destination"),
        endpoint(addresses.control_fixture, 42002, "control-fixture"),
    )
    plan = EvidencePlan(
        design_revision="TEL-002-v0.1",
        semantic_baseline_commit=_BASELINE,
        semantic_baseline_path="rfcs/AEP-0012-network-control-resource-profile.md",
        run_id="live-provenance",
        path_id="selected-path",
        subject_destination=selected.listen,
        upstream_fixture=selected.upstream,
        non_target_subject_destination=control.listen,
        non_target_upstream_fixture=control.upstream,
        exchange_program=ExchangeProgram(
            program_id="provenance-test",
            request_prefix=b"REQ",
            request_suffix=b"END",
            response_prefix=b"RESP",
            response_suffix=b"END",
        ),
        observation_budget_ns=1_000_000,
    )

    lab = _FakeLab()
    lab.run_id = "live-provenance"
    lab.topology = topology
    lab.addresses = addresses
    lab.capture_assurance = CaptureAssurance(True, True, True, True)
    lab.toxiproxy_artifact = ToxiproxyArtifact.reviewed("linux/amd64")
    lab.helper_artifact = LabHelperArtifact.reviewed_amd64()
    lab.artifact_store = ArtifactStore(root)
    lab._admin_isolation_verified = True
    lab._materialization = LiveMaterialization(
        sealed_plan=plan.seal(),
        selected_binding=selected,
        control_binding=control,
        admin=object(),  # type: ignore[arg-type]
    )
    lab._require_materialization = lambda: lab._materialization
    return lab


class MaterializationProvenanceTests(unittest.TestCase):
    def test_observed_security_fact_is_separate_from_construction_invariants(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            lab = materialized_lab(Path(temporary))
            ref = _retain_materialization_provenance(lab)  # type: ignore[arg-type]
            document = json.loads(lab.artifact_store.read_verified(ref))

        self.assertEqual(document["helper"], lab.helper_artifact.provenance_document())
        self.assertTrue(document["captureAssurance"]["egressCoverageVerified"])
        security = document["securityEvidence"]
        self.assertTrue(security["subjectAdminIsolationVerified"])
        construction = security["constructionInvariants"]
        self.assertTrue(construction["networksInternalOnly"])
        self.assertFalse(construction["subjectDockerControlMounted"])
        self.assertFalse(construction["subjectNetRawGranted"])
        self.assertTrue(construction["witnessNetRawGranted"])
        self.assertNotIn("networksInternalOnly", security)


class LiveExecutionCleanupTests(unittest.TestCase):
    def test_primary_execution_failure_is_preserved_and_cleanup_problem_is_secondary_note(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            lab = materialized_lab(Path(temporary))
            primary = RuntimeError("primary-live-failure")
            lab.start = lambda: lab._materialization
            lab.phase_runner = lambda: _FakeRunner(error=primary)
            lab.close = lambda: ("cleanup:residual-role",)
            with self.assertRaisesRegex(RuntimeError, "primary-live-failure") as captured:
                execute_live_matrix(lab)  # type: ignore[arg-type]
        self.assertIs(captured.exception, primary)
        self.assertIn("cleanup:residual-role", getattr(primary, "__notes__", ()))

    def test_success_requires_retained_implementation_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            lab = materialized_lab(Path(temporary))
            lab.start = lambda: lab._materialization
            lab.close = lambda: ()
            empty = PortableEvidenceObservations(None, None, None, None, None, None, None)
            lab.phase_runner = lambda: _FakeRunner(
                result=TerminatingRunResult(
                    observations=empty,
                    assessment=EvidenceAssessment(AssessmentClass.SATISFIED),
                    control_snapshots=(),
                    implementation_record_ref=None,
                )
            )
            with self.assertRaisesRegex(RuntimeError, "did not retain implementation record"):
                execute_live_matrix(lab)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()

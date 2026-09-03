"""Controlled live-execution wrapper for Network Control TEL-002.

Materialization provenance is retained separately from portable C1-C12
observations so concrete helper/container facts remain auditable without gaining
portable verdict authority.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .evidence_core import ArtifactRef, EvidenceAssessment
from .toxiproxy_evidence import NegativeMode, TerminatingRunResult
from .toxiproxy_live_lab import ToxiproxyLiveLab

_MATERIALIZATION_FORMAT = "avp-project-toxiproxy-live-materialization-v0.1"


@dataclass(frozen=True, slots=True)
class LiveExecutionResult:
    materialization_provenance_ref: ArtifactRef
    terminating_result: TerminatingRunResult

    @property
    def assessment(self) -> EvidenceAssessment:
        return self.terminating_result.assessment


def execute_live_matrix(
    lab: ToxiproxyLiveLab,
    *,
    negative_mode: NegativeMode | None = None,
) -> LiveExecutionResult:
    """Materialize, retain concrete provenance, execute, and always clean up.

    Cleanup problems are attached to a raised primary failure rather than
    replacing it. Successful execution still closes any residual lab resources
    after the runner's cleanup/noninterference sentinel has executed.
    """

    primary: BaseException | None = None
    try:
        lab.start()
        provenance_ref = _retain_materialization_provenance(lab)
        result = lab.phase_runner().execute(negative_mode=negative_mode)
        if result.implementation_record_ref is None:
            raise RuntimeError("live TEL-002 execution did not retain implementation record")
        return LiveExecutionResult(
            materialization_provenance_ref=provenance_ref,
            terminating_result=result,
        )
    except BaseException as exc:
        primary = exc
        raise
    finally:
        cleanup_problems = lab.close()
        if primary is not None:
            for problem in cleanup_problems:
                primary.add_note(problem)


def _retain_materialization_provenance(lab: ToxiproxyLiveLab) -> ArtifactRef:
    """Retain observed preflight evidence separately from construction invariants."""

    materialization = lab._require_materialization()
    assurance = lab.capture_assurance
    document = {
        "format": _MATERIALIZATION_FORMAT,
        "runId": lab.run_id,
        "sealedPlan": {
            "sha256": materialization.sealed_plan.ref.sha256,
            "size": materialization.sealed_plan.ref.size,
            "logicalRole": materialization.sealed_plan.ref.logical_role,
        },
        "toxiproxy": lab.toxiproxy_artifact.provenance_document(),
        "helper": lab.helper_artifact.provenance_document(),
        "captureAssurance": {
            "egressCoverageVerified": assurance.egress_coverage_verified,
            "directionalityVerified": assurance.directionality_verified,
            "offloadNormalizationVerified": assurance.offload_normalization_verified,
            "preSynConnectGapClosed": assurance.pre_syn_connect_gap_closed,
        },
        "topology": {
            "runToken": lab.topology.run_token,
            "adminNetwork": lab.topology.admin_network,
            "dataNetwork": lab.topology.data_network,
            "toxiproxyContainer": lab.topology.container_name,
            "adminAddress": lab.topology.admin_address,
            "dataAddress": lab.topology.data_address,
            "selectedFixtureAddress": lab.addresses.selected_fixture,
            "controlFixtureAddress": lab.addresses.control_fixture,
            "subjectAddress": lab.addresses.subject,
            "privilegedProbeAddress": lab.addresses.privileged_probe,
        },
        "securityEvidence": {
            # This value is produced by an actual Subject-role reachability probe.
            "subjectAdminIsolationVerified": lab._admin_isolation_verified,
            # The remaining values describe the reviewed Docker construction
            # performed by this implementation. They are not presented as
            # independently observed runtime facts.
            "constructionInvariants": {
                "networksInternalOnly": True,
                "subjectDockerControlMounted": False,
                "subjectNetRawGranted": False,
                "witnessNetRawGranted": True,
            },
        },
    }
    payload = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return lab.artifact_store.put_bytes(
        payload,
        logical_role="toxiproxy-live-materialization-provenance",
    )

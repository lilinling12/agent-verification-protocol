"""TEL-002 finite Toxiproxy phase orchestration and retained implementation evidence.

The runner orders one concrete terminating mechanism. It deliberately delegates
portable verdict ownership to ``compare_portable_evidence`` and never converts a
Toxiproxy API acknowledgement into a portable PASS condition.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .evidence_core import (
    ArtifactRef,
    ArtifactStore,
    EvidenceAssessment,
    InitiationFacts,
    SealedPlan,
)
from .portable_comparator import (
    AttemptObservation,
    PortableEvidenceObservations,
    compare_portable_evidence,
)
from .toxiproxy_binding import (
    ControlSnapshot,
    ProxyBinding,
    ToxiproxyAdminClient,
    ToxiproxyArtifact,
    ToxiproxyRunTopology,
)

_RECORD_FORMAT = "avp-project-toxiproxy-terminating-evidence-v0.1"
_COMPARATOR_REVISION = "npr011-portable-c1-c12-v0.1"


class NegativeMode(str, Enum):
    """Required TEL-002 faulty assemblies; names are project-local evidence vocabulary."""

    BYPASS_FAULT = "BypassFault"
    EARLY_ACTIVATION = "EarlyActivation"
    FALSE_SETTLED = "FalseSettled"
    FALSE_RECOVERY = "FalseRecovery"
    SCHEDULE_LEAK = "ScheduleLeak"
    HIDDEN_RETRY_FALLBACK = "HiddenRetry/Fallback"
    COLLATERAL_TARGET = "CollateralTarget"
    RESIDUAL_STATE_CLEANUP_FAILURE = "ResidualStateCleanupFailure"


@dataclass(frozen=True, slots=True)
class PhaseExecution:
    """Result of one certified attempt plus its retained implementation evidence refs."""

    observation: AttemptObservation
    evidence_refs: tuple[ArtifactRef, ...] = ()


@dataclass(frozen=True, slots=True)
class TerminatingRunResult:
    """One finite TEL-002 run result; assessment remains provider-neutral."""

    observations: PortableEvidenceObservations
    assessment: EvidenceAssessment
    control_snapshots: tuple[ControlSnapshot, ...]
    implementation_record_ref: ArtifactRef | None


CertifiedAttempt = Callable[[str, bool, NegativeMode | None], PhaseExecution]
CleanupSentinel = Callable[[bool], tuple[bool, tuple[str, ...]]]
SecurityProjectionCheck = Callable[[bool], tuple[bool, tuple[str, ...]]]


class ToxiproxyPhaseRunner:
    """Execute the reviewed finite TEL-002 lifecycle against one concrete admin client.

    ``certified_attempt`` owns fixture/client/witness execution for a named phase.
    The boolean states whether the attempt is privileged evaluator traffic. A
    negative mode is passed only when that attempt must execute a real faulty
    assembly (for example an extra connect in HiddenRetry/Fallback). The callback
    returns already-normalized provider-neutral evidence; this runner sequences
    Toxiproxy control and delegates all portable assessment to the comparator.
    """

    def __init__(
        self,
        *,
        sealed_plan: SealedPlan,
        admin: ToxiproxyAdminClient,
        selected_binding: ProxyBinding,
        control_binding: ProxyBinding,
        certified_attempt: CertifiedAttempt,
        cleanup_sentinel: CleanupSentinel,
        security_projection_check: SecurityProjectionCheck,
        artifact_store: ArtifactStore | None = None,
        artifact: ToxiproxyArtifact | None = None,
        topology: ToxiproxyRunTopology | None = None,
    ) -> None:
        sealed_plan.verify()
        plan = sealed_plan.plan
        if not plan.has_non_target_control:
            raise ValueError("TEL-002 terminating matrix requires a materialized non-target control path")
        if selected_binding.listen != plan.subject_destination:
            raise ValueError("selected Toxiproxy listener does not match the sealed Subject destination")
        if selected_binding.upstream != plan.upstream_fixture:
            raise ValueError("selected Toxiproxy upstream does not match the sealed fixture endpoint")
        if control_binding.listen != plan.non_target_subject_destination:
            raise ValueError("control Toxiproxy listener does not match the sealed control destination")
        if control_binding.upstream != plan.non_target_upstream_fixture:
            raise ValueError("control Toxiproxy upstream does not match the sealed control fixture endpoint")
        self.sealed_plan = sealed_plan
        self.admin = admin
        self.selected_binding = selected_binding
        self.control_binding = control_binding
        self.certified_attempt = certified_attempt
        self.cleanup_sentinel = cleanup_sentinel
        self.security_projection_check = security_projection_check
        self.artifact_store = artifact_store
        self.artifact = artifact
        self.topology = topology

    def execute(self, *, negative_mode: NegativeMode | None = None) -> TerminatingRunResult:
        """Execute one bounded positive or intentionally faulty terminating matrix."""

        snapshots: list[ControlSnapshot] = []
        phase_refs: list[ArtifactRef] = []
        infrastructure: list[str] = []
        evidence_invalid: list[str] = []

        snapshots.append(self.admin.create_proxy(self.selected_binding))
        snapshots.append(self.admin.create_proxy(self.control_binding))

        baseline = self._attempt("baseline", privileged=False, refs=phase_refs)
        if negative_mode is NegativeMode.EARLY_ACTIVATION:
            snapshots.append(self._activate_selected())
        pre_trigger = self._attempt("pre-trigger", privileged=False, refs=phase_refs)

        if negative_mode not in {NegativeMode.BYPASS_FAULT, NegativeMode.EARLY_ACTIVATION}:
            snapshots.append(self._activate_selected())

        activation_settlement = (
            None
            if negative_mode is NegativeMode.FALSE_SETTLED
            else self._attempt("activation-settlement", privileged=True, refs=phase_refs)
        )
        subject_mode = (
            NegativeMode.HIDDEN_RETRY_FALLBACK
            if negative_mode is NegativeMode.HIDDEN_RETRY_FALLBACK
            else None
        )
        subject_active_cut = self._attempt(
            "subject-active-cut",
            privileged=False,
            refs=phase_refs,
            negative_mode=subject_mode,
        )

        if negative_mode is NegativeMode.COLLATERAL_TARGET:
            snapshots.append(
                self.admin.create_upstream_timeout_cut(
                    self.control_binding.name,
                    toxic_name=self._control_toxic_name,
                )
            )
        non_target_control = self._attempt("non-target-control", privileged=False, refs=phase_refs)

        # Provider acknowledgement is retained only as diagnostics. Recovery is
        # still decided by the two fresh probes + stability observation below.
        if negative_mode is not NegativeMode.BYPASS_FAULT:
            try:
                snapshots.append(
                    self.admin.delete_toxic(self.selected_binding.name, self._selected_toxic_name)
                )
            except RuntimeError as exc:
                infrastructure.append(f"clear-selected:{type(exc).__name__}")
        if negative_mode is NegativeMode.COLLATERAL_TARGET:
            try:
                snapshots.append(
                    self.admin.delete_toxic(self.control_binding.name, self._control_toxic_name)
                )
            except RuntimeError as exc:
                infrastructure.append(f"clear-control:{type(exc).__name__}")

        recovery_1 = self._attempt("recovery-1", privileged=True, refs=phase_refs)
        recovery_2 = (
            None
            if negative_mode is NegativeMode.FALSE_RECOVERY
            else self._attempt("recovery-2", privileged=True, refs=phase_refs)
        )
        stability = (
            None
            if negative_mode is NegativeMode.FALSE_RECOVERY
            else self._attempt("stability", privileged=True, refs=phase_refs)
        )

        security_ok, security_problems = self.security_projection_check(
            negative_mode is NegativeMode.SCHEDULE_LEAK
        )
        evidence_invalid.extend(security_problems)

        cleanup_ok, cleanup_problems = self.cleanup_sentinel(
            negative_mode is NegativeMode.RESIDUAL_STATE_CLEANUP_FAILURE
        )
        infrastructure.extend(cleanup_problems)

        observations = PortableEvidenceObservations(
            baseline=baseline,
            pre_trigger=pre_trigger,
            activation_settlement=activation_settlement,
            subject_active_cut=subject_active_cut,
            recovery_1=recovery_1,
            recovery_2=recovery_2,
            stability=stability,
            non_target_control=non_target_control,
            cleanup_noninterference_ok=cleanup_ok,
            security_projection_ok=security_ok,
            evidence_validity_problems=tuple(evidence_invalid),
            infrastructure_problems=tuple(infrastructure),
        )
        assessment = compare_portable_evidence(self.sealed_plan, observations)
        record_ref = self._retain_record(
            negative_mode=negative_mode,
            observations=observations,
            assessment=assessment,
            snapshots=tuple(snapshots),
            phase_refs=tuple(phase_refs),
        )
        return TerminatingRunResult(
            observations=observations,
            assessment=assessment,
            control_snapshots=tuple(snapshots),
            implementation_record_ref=record_ref,
        )

    @property
    def _selected_toxic_name(self) -> str:
        return f"cut-{self.sealed_plan.plan.run_id}"

    @property
    def _control_toxic_name(self) -> str:
        return f"collateral-cut-{self.sealed_plan.plan.run_id}"

    def _activate_selected(self) -> ControlSnapshot:
        return self.admin.create_upstream_timeout_cut(
            self.selected_binding.name,
            toxic_name=self._selected_toxic_name,
        )

    def _attempt(
        self,
        phase_id: str,
        *,
        privileged: bool,
        refs: list[ArtifactRef],
        negative_mode: NegativeMode | None = None,
    ) -> AttemptObservation:
        execution = self.certified_attempt(phase_id, privileged, negative_mode)
        if execution.observation.phase_id != phase_id:
            raise ValueError(
                f"certified attempt returned phase {execution.observation.phase_id!r} for {phase_id!r}"
            )
        refs.extend(execution.evidence_refs)
        return execution.observation

    def _retain_record(
        self,
        *,
        negative_mode: NegativeMode | None,
        observations: PortableEvidenceObservations,
        assessment: EvidenceAssessment,
        snapshots: tuple[ControlSnapshot, ...],
        phase_refs: tuple[ArtifactRef, ...],
    ) -> ArtifactRef | None:
        if self.artifact_store is None:
            return None
        document = {
            "format": _RECORD_FORMAT,
            "runId": self.sealed_plan.plan.run_id,
            "negativeMode": None if negative_mode is None else negative_mode.value,
            "sealedPlan": _artifact_document(self.sealed_plan.ref),
            "comparatorRevision": _COMPARATOR_REVISION,
            "assessment": {
                "classification": assessment.classification.value,
                "primaryProblem": assessment.primary_problem,
                "secondaryProblems": list(assessment.secondary_problems),
            },
            "portableObservationSnapshot": _observations_document(observations),
            "implementationEvidence": [_artifact_document(ref) for ref in phase_refs],
            "controlSnapshots": [
                {
                    "operation": item.operation,
                    "statusCode": item.status_code,
                    "responseUtf8": item.response_bytes.decode("utf-8", errors="replace"),
                }
                for item in snapshots
            ],
            "toxiproxy": None if self.artifact is None else self.artifact.provenance_document(),
            "topology": None if self.topology is None else _topology_document(self.topology),
        }
        payload = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return self.artifact_store.put_bytes(
            payload,
            logical_role="toxiproxy-terminating-evidence-record",
        )


def _observations_document(observations: PortableEvidenceObservations) -> dict[str, object]:
    return {
        "attempts": {
            "baseline": _attempt_document(observations.baseline),
            "preTrigger": _attempt_document(observations.pre_trigger),
            "activationSettlement": _attempt_document(observations.activation_settlement),
            "subjectActiveCut": _attempt_document(observations.subject_active_cut),
            "nonTargetControl": _attempt_document(observations.non_target_control),
            "recovery1": _attempt_document(observations.recovery_1),
            "recovery2": _attempt_document(observations.recovery_2),
            "stability": _attempt_document(observations.stability),
        },
        "cleanupNoninterferenceOk": observations.cleanup_noninterference_ok,
        "securityProjectionOk": observations.security_projection_ok,
        "evidenceValidityProblems": list(observations.evidence_validity_problems),
        "infrastructureProblems": list(observations.infrastructure_problems),
        "unsupportedMaterializationProblems": list(observations.unsupported_materialization_problems),
    }


def _attempt_document(item: AttemptObservation | None) -> dict[str, object] | None:
    if item is None:
        return None
    return {
        "phaseId": item.phase_id,
        "pathId": item.path_id,
        "attemptId": item.attempt_id,
        "completed": item.completed,
        "mismatchObserved": item.mismatch_observed,
        "observationBudgetExpired": item.observation_budget_expired,
        "frontInitiations": _initiation_document(item.front_initiations),
        "upstreamInitiations": _initiation_document(item.upstream_initiations),
        "validityProblems": list(item.validity_problems),
    }


def _initiation_document(item: InitiationFacts) -> dict[str, object]:
    return {
        "channel": item.channel,
        "totalInitiations": item.total_initiations,
        "expectedTargetInitiations": item.expected_target_initiations,
        "alternateTargetInitiations": item.alternate_target_initiations,
        "rawSynPackets": item.raw_syn_packets,
        "retransmittedSynPackets": item.retransmitted_syn_packets,
        "validityProblems": list(item.validity_problems),
    }


def _artifact_document(ref: ArtifactRef) -> dict[str, object]:
    return {"sha256": ref.sha256, "size": ref.size, "logicalRole": ref.logical_role}


def _topology_document(topology: ToxiproxyRunTopology) -> dict[str, str]:
    return {
        "runToken": topology.run_token,
        "adminNetwork": topology.admin_network,
        "dataNetwork": topology.data_network,
        "containerName": topology.container_name,
        "adminAddress": topology.admin_address,
        "dataAddress": topology.data_address,
    }

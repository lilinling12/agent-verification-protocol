"""Project-local pinned-Toxiproxy transport compatibility qualification.

This qualification is deliberately below the portable comparator. It proves that
the reviewed concrete Toxiproxy artifact can carry the already-reviewed exact-byte
fixture/client contract before the expensive TEL-003 positive/negative matrix is
attempted. It does not produce C1-C12 verdicts or provider-specific PASS semantics.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .evidence_core import InitiationFacts
from .portable_comparator import AttemptObservation
from .toxiproxy_binding import ControlSnapshot, ToxiproxyControlError
from .toxiproxy_evidence import PhaseExecution
from .verified_live_labs import VerifiedToxiproxyLiveLab

_FORMAT = "avp-project-toxiproxy-transport-qualification-v0.1"
_TOXIC_NAME = "transport-qualification-cut"


@dataclass(frozen=True, slots=True)
class ToxiproxyTransportQualificationResult:
    document: dict[str, object]


def execute_toxiproxy_transport_qualification(
    lab: VerifiedToxiproxyLiveLab,
) -> ToxiproxyTransportQualificationResult:
    """Qualify pass-through, timeout-cut, clear/recovery, and cleanup behavior."""

    materialization = lab.start()
    snapshots: list[ControlSnapshot] = []
    cleanup_done = False
    try:
        snapshots.append(materialization.admin.create_proxy(materialization.selected_binding))
        snapshots.append(materialization.admin.create_proxy(materialization.control_binding))

        baseline = lab.certified_attempt("baseline", False, None)
        _require_successful_exchange("baseline", baseline)

        snapshots.append(
            materialization.admin.create_upstream_timeout_cut(
                materialization.selected_binding.name,
                toxic_name=_TOXIC_NAME,
            )
        )
        active_cut = lab.certified_attempt("subject-active-cut", False, None)
        _require_timeout_cut("subject-active-cut", active_cut)

        snapshots.append(
            materialization.admin.delete_toxic(
                materialization.selected_binding.name,
                _TOXIC_NAME,
            )
        )
        recovery = lab.certified_attempt("recovery-1", True, None)
        _require_successful_exchange("recovery-1", recovery)

        cleanup_ok, cleanup_problems = lab.cleanup_sentinel(False)
        cleanup_done = True
        if not cleanup_ok or cleanup_problems:
            raise ToxiproxyControlError(
                f"transport qualification cleanup is not exact: {cleanup_problems!r}"
            )

        document: dict[str, object] = {
            "format": _FORMAT,
            "runId": materialization.sealed_plan.plan.run_id,
            "provider": "Toxiproxy",
            "artifact": lab.toxiproxy_artifact.provenance_document(),
            "helper": lab.helper_artifact.provenance_document(),
            "baseline": _execution_document(baseline),
            "activeCut": _execution_document(active_cut),
            "recovery": _execution_document(recovery),
            "controlSnapshots": [_snapshot_document(item) for item in snapshots],
            "cleanup": {"ok": True, "problems": []},
            "qualificationBasis": [
                "pass-through carries one exact request/response exchange without TCP half-close framing",
                "timeout toxic with timeout=0 suppresses application completion until evaluator observation budget expiry",
                "clear is followed by a fresh successful recovery exchange rather than provider acknowledgement alone",
                "each qualification attempt retains exactly one expected front and upstream initiation",
                "completed exchanges retain exact fixture integrity evidence and every exchange retains project-local diagnostics",
                "cleanup removes the concrete qualification resources before success is published",
            ],
        }
        return ToxiproxyTransportQualificationResult(document=document)
    finally:
        if not cleanup_done:
            lab.close()


def _require_successful_exchange(label: str, execution: PhaseExecution) -> None:
    observation = execution.observation
    if not observation.completed:
        raise ToxiproxyControlError(f"{label} transport qualification exchange did not complete")
    if observation.mismatch_observed or observation.observation_budget_expired:
        raise ToxiproxyControlError(f"{label} transport qualification exchange is not exact")
    _require_evidence_integrity(label, observation)
    _require_single_initiation(label, observation)
    _require_evidence_roles(
        label,
        execution,
        required={f"exchange-diagnostic-{observation.phase_id}", f"fixture-exchange-{observation.phase_id}"},
    )


def _require_timeout_cut(label: str, execution: PhaseExecution) -> None:
    observation = execution.observation
    if observation.completed or observation.mismatch_observed:
        raise ToxiproxyControlError(f"{label} timeout-cut qualification did not suppress completion")
    if not observation.observation_budget_expired:
        raise ToxiproxyControlError(
            f"{label} timeout-cut qualification ended before evaluator budget expiry"
        )
    _require_evidence_integrity(label, observation)
    _require_single_initiation(label, observation)
    _require_evidence_roles(
        label,
        execution,
        required={f"exchange-diagnostic-{observation.phase_id}"},
    )


def _require_evidence_integrity(label: str, observation: AttemptObservation) -> None:
    if observation.validity_problems:
        raise ToxiproxyControlError(
            f"{label} transport qualification evidence is invalid: {observation.validity_problems!r}"
        )


def _require_single_initiation(label: str, observation: AttemptObservation) -> None:
    for facts in (observation.front_initiations, observation.upstream_initiations):
        if (
            facts.total_initiations != 1
            or facts.expected_target_initiations != 1
            or facts.alternate_target_initiations != 0
            or facts.validity_problems
        ):
            raise ToxiproxyControlError(
                f"{label} transport qualification initiation evidence is not exact: {facts!r}"
            )


def _require_evidence_roles(
    label: str,
    execution: PhaseExecution,
    *,
    required: set[str],
) -> None:
    roles = {ref.logical_role for ref in execution.evidence_refs}
    missing = sorted(required - roles)
    if missing:
        raise ToxiproxyControlError(
            f"{label} transport qualification evidence refs are incomplete: {missing!r}"
        )


def _execution_document(execution: PhaseExecution) -> dict[str, object]:
    observation = execution.observation
    return {
        "phaseId": observation.phase_id,
        "attemptId": observation.attempt_id,
        "completed": observation.completed,
        "mismatchObserved": observation.mismatch_observed,
        "observationBudgetExpired": observation.observation_budget_expired,
        "frontInitiations": _initiation_document(observation.front_initiations),
        "upstreamInitiations": _initiation_document(observation.upstream_initiations),
        "validityProblems": list(observation.validity_problems),
        "evidenceRefs": [
            {"logicalRole": ref.logical_role, "sha256": ref.sha256, "size": ref.size}
            for ref in execution.evidence_refs
        ],
    }


def _initiation_document(facts: InitiationFacts) -> dict[str, object]:
    return {
        "channel": facts.channel,
        "totalInitiations": facts.total_initiations,
        "expectedTargetInitiations": facts.expected_target_initiations,
        "alternateTargetInitiations": facts.alternate_target_initiations,
        "rawSynPackets": facts.raw_syn_packets,
        "retransmittedSynPackets": facts.retransmitted_syn_packets,
        "validityProblems": list(facts.validity_problems),
    }


def _snapshot_document(snapshot: ControlSnapshot) -> dict[str, object]:
    return {
        "operation": snapshot.operation,
        "statusCode": snapshot.status_code,
        "responseSize": len(snapshot.response_bytes),
        "responseSha256": hashlib.sha256(snapshot.response_bytes).hexdigest(),
    }

"""Packet-path projection into the provider-neutral NPR-011 comparator surface.

This module is deliberately narrow: it converts already-observed packet-path
attempt evidence into ``AttemptObservation`` / ``PortableEvidenceObservations``
and delegates C1-C12 assessment unchanged to ``compare_portable_evidence``. It
does not own Linux control, qualification, or provider-specific verdict rules.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..attempt_client import ExchangeObservation
from ..evidence_core import (
    AttemptMaterial,
    EvidenceAssessment,
    EvidenceMaterializationError,
    InitiationFacts,
    SealedPlan,
)
from ..portable_comparator import (
    AttemptObservation,
    PortableEvidenceObservations,
    compare_portable_evidence,
)

_ALLOWED_PHASES = (
    "baseline",
    "pre-trigger",
    "activation-settlement",
    "subject-active-cut",
    "non-target-control",
    "recovery-1",
    "recovery-2",
    "stability",
)


@dataclass(frozen=True, slots=True)
class PacketPathAttemptEvidence:
    """One certified packet-path attempt before portable assessment."""

    phase_id: str
    attempt: AttemptMaterial
    exchange: ExchangeObservation
    front_initiations: InitiationFacts
    validity_problems: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.phase_id not in _ALLOWED_PHASES:
            raise EvidenceMaterializationError(
                f"packet-path attempt evidence phase is not reviewed: {self.phase_id!r}"
            )
        if self.attempt.phase_id != self.phase_id:
            raise EvidenceMaterializationError("packet-path attempt material phase drift")
        if self.exchange.attempt_id != self.attempt.attempt_id:
            raise EvidenceMaterializationError("packet-path exchange attempt identity drift")
        if self.front_initiations.channel != "W-front":
            raise EvidenceMaterializationError("packet-path attempt requires W-front initiation facts")

    def portable_observation(self, sealed_plan: SealedPlan) -> AttemptObservation:
        """Project one non-terminating attempt without fabricating upstream TCP evidence."""

        sealed_plan.verify()
        plan = sealed_plan.plan
        if self.attempt.run_id != plan.run_id:
            raise EvidenceMaterializationError("packet-path attempt run identity drift")
        if self.phase_id not in plan.phase_program:
            raise EvidenceMaterializationError("packet-path attempt phase is outside sealed plan")

        expected_path = plan.path_id
        if self.phase_id == "non-target-control":
            expected_path = plan.non_target_path_id or ""
            if not expected_path:
                raise EvidenceMaterializationError(
                    "packet-path non-target attempt requires a sealed control path"
                )
        if self.attempt.path_id != expected_path:
            raise EvidenceMaterializationError("packet-path attempt logical path identity drift")

        return AttemptObservation(
            phase_id=self.phase_id,
            path_id=self.attempt.path_id,
            attempt_id=self.attempt.attempt_id,
            completed=self.exchange.completed,
            mismatch_observed=self.exchange.mismatch_observed,
            observation_budget_expired=self.exchange.observation_budget_expired,
            front_initiations=self.front_initiations,
            # Non-terminating packet forwarding is not a second TCP initiation.
            upstream_initiations=None,
            validity_problems=self.validity_problems,
        )


@dataclass(frozen=True, slots=True)
class PacketPathRunEvidence:
    """Finite packet-path run evidence consumed by the unchanged comparator."""

    sealed_plan: SealedPlan
    attempts: tuple[PacketPathAttemptEvidence, ...]
    cleanup_noninterference_ok: bool | None
    security_projection_ok: bool | None
    evidence_validity_problems: tuple[str, ...] = ()
    infrastructure_problems: tuple[str, ...] = ()
    unsupported_materialization_problems: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self.sealed_plan.verify()
        phases = tuple(item.phase_id for item in self.attempts)
        if len(set(phases)) != len(phases):
            raise EvidenceMaterializationError("packet-path run contains duplicate attempt phases")

    def portable_observations(self) -> PortableEvidenceObservations:
        """Build the provider-neutral observation aggregate without filling omissions."""

        by_phase = {
            item.phase_id: item.portable_observation(self.sealed_plan)
            for item in self.attempts
        }
        return PortableEvidenceObservations(
            baseline=by_phase.get("baseline"),
            pre_trigger=by_phase.get("pre-trigger"),
            activation_settlement=by_phase.get("activation-settlement"),
            subject_active_cut=by_phase.get("subject-active-cut"),
            non_target_control=by_phase.get("non-target-control"),
            recovery_1=by_phase.get("recovery-1"),
            recovery_2=by_phase.get("recovery-2"),
            stability=by_phase.get("stability"),
            cleanup_noninterference_ok=self.cleanup_noninterference_ok,
            security_projection_ok=self.security_projection_ok,
            evidence_validity_problems=self.evidence_validity_problems,
            infrastructure_problems=self.infrastructure_problems,
            unsupported_materialization_problems=self.unsupported_materialization_problems,
        )

    def assess(self) -> EvidenceAssessment:
        """Delegate all C1-C12 semantics to the provider-neutral comparator."""

        return compare_portable_evidence(
            self.sealed_plan,
            self.portable_observations(),
        )

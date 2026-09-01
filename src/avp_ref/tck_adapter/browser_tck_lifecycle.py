"""Provider-neutral evaluator for Browser settlement and lifecycle semantics.

The evaluator composes the existing BrowserConformanceHarness rather than
re-implementing snapshot/reset/restore semantics. Positive settlement is owned by
the evaluator, and reset/restore success is accepted only after independent
post-operation reprojection. Concrete provider completion signals are never
sufficient settlement evidence here.

Temporal ineligibility is induced through an explicitly injected private control
callable. The portable evaluator therefore knows the required behavior, but not
a provider-specific fixture-control method name or parameter shape.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from avp_ref.environment.models import RestoreEquivalence, SnapshotRef

from .browser_harness import (
    BrowserConformanceHarness,
    BrowserHarnessError,
    BrowserSettlementLedger,
    BrowserSUT,
    BrowserVerificationError,
)
from .browser_tck_adapter import BROWSER_PROFILE
from .models import TCKAdapterError, TCKCaseResult, TCKStatus

CASE_ID = "AVP-TCK-BROWSER-SETTLEMENT-LIFECYCLE-001"
_NEGATIVE_CONTROLS = frozenset(
    {
        "sleep-only-settlement",
        "networkidle-only-settlement",
        "provider-command-success-only",
        "foreign-or-stale-snapshotref",
        "reset-without-independent-reprojection",
        "restore-without-independent-reprojection",
        "restore-reports-exact",
        "temporally-ineligible-cookie-restore-success",
    }
)


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TCKAdapterError(f"{label} must be an object")
    return value


def _strings(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise TCKAdapterError(f"{label} must be a non-empty array")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise TCKAdapterError(f"{label} must contain non-empty strings")
        result.append(item)
    return result


def _settled() -> BrowserSettlementLedger:
    ledger = BrowserSettlementLedger()
    ledger.close_subject_admission()
    return ledger


def _unresolved() -> BrowserSettlementLedger:
    ledger = BrowserSettlementLedger()
    ledger.accept_relevant_mutation("profile-relevant-work")
    ledger.close_subject_admission()
    return ledger


def _require_rejected(operation: Callable[[], object], label: str) -> None:
    try:
        operation()
    except BrowserHarnessError:
        return
    raise BrowserVerificationError(f"Browser lifecycle negative control accepted: {label}")


class BrowserSettlementLifecycleTCKEvaluator:
    """Execute positive settlement plus snapshot/reset/restore verification."""

    case_id = CASE_ID

    def __init__(
        self,
        harness: BrowserConformanceHarness,
        *,
        set_temporal_eligibility: Callable[[BrowserSUT, bool], None],
    ) -> None:
        if not callable(set_temporal_eligibility):
            raise TCKAdapterError("Browser temporal eligibility control must be callable")
        self._harness = harness
        self._set_temporal_eligibility = set_temporal_eligibility

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        vector, expect = self._case_parts(case)
        self._validate_contract(vector, expect)
        sut = self._harness.provision()
        try:
            self._execute_positive_path(sut)
            self._execute_negative_controls(sut)
        except BrowserHarnessError as exc:
            return TCKCaseResult(
                self.case_id,
                TCKStatus.FAIL,
                f"Browser settlement/lifecycle obligation failed: {exc}",
            )
        finally:
            sut.release()
        return TCKCaseResult(
            self.case_id,
            TCKStatus.PASS,
            "positive settlement, snapshot ownership, reset baseline reprojection, and STATE_EQUIVALENT restore verified",
        )

    def _case_parts(
        self,
        case: Mapping[str, Any],
    ) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
        metadata = _mapping(case.get("metadata"), f"{CASE_ID} metadata")
        if metadata.get("id") != CASE_ID or metadata.get("domain") != "browser":
            raise TCKAdapterError(f"{CASE_ID} case identity/domain mismatch")
        if case.get("profile") != BROWSER_PROFILE:
            raise TCKAdapterError(f"{CASE_ID} targets the wrong Browser profile")
        return (
            _mapping(case.get("vector"), f"{CASE_ID} vector"),
            _mapping(case.get("expect"), f"{CASE_ID} expect"),
        )

    def _validate_contract(
        self,
        vector: Mapping[str, Any],
        expect: Mapping[str, Any],
    ) -> None:
        witness = _mapping(vector.get("settlementWitness"), f"{CASE_ID} settlementWitness")
        expected_witness = {
            "subjectAdmissionClosed": True,
            "acceptedRelevantMutationsTerminal": True,
            "unresolvedRelevantMutations": 0,
            "projectionStartsAfterWitness": True,
        }
        if dict(witness) != expected_witness:
            raise TCKAdapterError(f"{CASE_ID} settlement witness contract changed")
        if _strings(vector.get("operations"), f"{CASE_ID} operations") != [
            "snapshot",
            "reset",
            "restore",
        ]:
            raise TCKAdapterError(f"{CASE_ID} lifecycle operation set changed")
        if vector.get("positiveRestoreFidelity") != "STATE_EQUIVALENT":
            raise TCKAdapterError(f"{CASE_ID} positive restore fidelity changed")
        controls = _strings(vector.get("negativeControls"), f"{CASE_ID} negativeControls")
        if len(controls) != len(set(controls)) or frozenset(controls) != _NEGATIVE_CONTROLS:
            raise TCKAdapterError(f"{CASE_ID} negative control set changed")
        expected_true = (
            "positiveSettlementWitnessRequired",
            "snapshotOwnershipRequired",
            "resetBaselineReprojectionRequired",
            "restoreSnapshotReprojectionRequired",
            "exactRestoreRejected",
            "negativeControlsRejected",
        )
        for key in expected_true:
            if expect.get(key) is not True:
                raise TCKAdapterError(f"{CASE_ID} expect.{key} must be true")
        if expect.get("successfulRestoreFidelity") != "STATE_EQUIVALENT":
            raise TCKAdapterError(f"{CASE_ID} successful restore fidelity changed")

    def _execute_positive_path(self, sut: BrowserSUT) -> None:
        baseline = self._harness.authoritative_projection(sut, _settled())
        snapshot = self._harness.verified_snapshot(sut, _settled())
        if snapshot.state_digest != baseline.digest:
            raise BrowserVerificationError("snapshot digest does not bind authoritative state")

        reset = self._harness.verified_reset(sut, _settled(), _settled())
        if not reset.equivalent_to_initial:
            raise BrowserVerificationError("reset did not re-establish baseline equivalence")

        restore = self._harness.verified_restore(
            sut,
            snapshot,
            _settled(),
            _settled(),
        )
        if restore.equivalence is not RestoreEquivalence.STATE_EQUIVALENT:
            raise BrowserVerificationError("restore fidelity is not STATE_EQUIVALENT")

    def _execute_negative_controls(self, sut: BrowserSUT) -> None:
        _require_rejected(
            lambda: self._harness.authoritative_projection(sut, _unresolved()),
            "sleep-only-settlement",
        )
        _require_rejected(
            lambda: self._harness.authoritative_projection(sut, _unresolved()),
            "networkidle-only-settlement",
        )

        snapshot = self._harness.verified_snapshot(sut, _settled())
        _require_rejected(
            lambda: self._harness.verified_reset(sut, _settled(), BrowserSettlementLedger()),
            "provider-command-success-only",
        )
        _require_rejected(
            lambda: self._harness.verified_reset(sut, _settled(), BrowserSettlementLedger()),
            "reset-without-independent-reprojection",
        )
        _require_rejected(
            lambda: self._harness.verified_restore(
                sut,
                snapshot,
                _settled(),
                BrowserSettlementLedger(),
            ),
            "restore-without-independent-reprojection",
        )

        foreign = SnapshotRef(
            snapshot_id=snapshot.snapshot_id,
            handle_id="foreign-browser-resource",
            state_digest=snapshot.state_digest,
            logical_time=snapshot.logical_time,
            consistency=snapshot.consistency,
            adapter_name=snapshot.adapter_name,
        )
        _require_rejected(
            lambda: self._harness.verified_restore(
                sut,
                foreign,
                _settled(),
                _settled(),
            ),
            "foreign-or-stale-snapshotref",
        )

        restore = self._harness.verified_restore(
            sut,
            snapshot,
            _settled(),
            _settled(),
        )
        if restore.equivalence is RestoreEquivalence.EXACT:
            raise BrowserVerificationError("EXACT Browser restore fidelity was accepted")

        self._set_temporal_eligibility(sut, False)
        try:
            _require_rejected(
                lambda: self._harness.verified_restore(
                    sut,
                    snapshot,
                    _settled(),
                    _settled(),
                ),
                "temporally-ineligible-cookie-restore-success",
            )
        finally:
            self._set_temporal_eligibility(sut, True)

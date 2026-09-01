"""Provider-neutral evaluator for executed Browser capability conformance.

The behavior oracle is the already-reviewed BrowserExecutedCapabilityEvaluator.
This case evaluator only binds the governed TCK vector to an exact set of
metadata-identical negative-control operations supplied by a private test-driver
seam. It contains no concrete browser/provider selection and cannot establish
conformance from metadata declarations alone.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from .browser_executed_capability import (
    BrowserExecutedCapabilityEvaluator,
    BrowserExecutedMetadata,
)
from .browser_harness import (
    BrowserConformanceHarness,
    BrowserHarnessError,
    BrowserSettlementLedger,
    BrowserSUT,
    BrowserVerificationError,
    MaterializedBrowserFixture,
)
from .browser_tck_adapter import BROWSER_PROFILE
from .models import TCKAdapterError, TCKCaseResult, TCKStatus

CASE_ID = "AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001"

_NEGATIVE_CONTROLS = frozenset(
    {
        "loses-hostonly-cookie-identity",
        "collapses-samesite-default",
        "admits-partitioned-state-as-unpartitioned",
        "corrupts-domstring-code-units",
        "uses-provider-enumeration-as-canonical-order",
        "reports-restore-success-without-reprojection",
        "bypasses-settlement-witness",
        "leaks-evaluator-private-state",
        "ignores-excluded-state-interference",
        "ignores-required-execution-input-drift",
    }
)


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TCKAdapterError(f"{label} must be an object")
    return value


def _strings(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise TCKAdapterError(f"{label} must be a non-empty array")
    values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise TCKAdapterError(f"{label} must contain non-empty strings")
        values.append(item)
    return values


def _settled() -> BrowserSettlementLedger:
    ledger = BrowserSettlementLedger()
    ledger.close_subject_admission()
    return ledger


@dataclass(frozen=True, slots=True)
class BrowserExecutedNegativeControlSet:
    """Exact private operations used to challenge one metadata-identical SUT.

    The operations themselves are implementation/test-driver details. Only their
    governed obligation names cross into this portable evaluator.
    """

    operations: Mapping[str, Callable[[], object]]
    candidate_metadata: BrowserExecutedMetadata

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "operations",
            MappingProxyType(dict(self.operations)),
        )


class BrowserExecutedCapabilityTCKEvaluator:
    """Require real behavior observation and rejection of all ten broken twins."""

    case_id = CASE_ID

    def __init__(
        self,
        *,
        harness: BrowserConformanceHarness,
        sut: BrowserSUT,
        fixture: MaterializedBrowserFixture,
        negative_controls: BrowserExecutedNegativeControlSet,
    ) -> None:
        self._harness = harness
        self._sut = sut
        self._fixture = fixture
        self._negative_controls = negative_controls
        self._behavior = BrowserExecutedCapabilityEvaluator()

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        vector, expect = self._case_parts(case)
        self._validate_contract(vector, expect)
        self._validate_control_set()
        reference_metadata = BrowserExecutedMetadata.from_fixture(self._fixture)
        try:
            self._behavior.require_metadata_identical(
                reference_metadata,
                self._negative_controls.candidate_metadata,
            )
            self._behavior.require_baseline_projection(
                self._harness,
                self._sut,
                _settled(),
                expected_digest=self._fixture.baseline_image_digest,
            )
            for obligation in sorted(_NEGATIVE_CONTROLS):
                self._behavior.require_rejected(
                    self._negative_controls.operations[obligation],
                    obligation=obligation,
                )
        except BrowserHarnessError as exc:
            return TCKCaseResult(
                self.case_id,
                TCKStatus.FAIL,
                f"executed Browser capability obligation failed: {exc}",
            )
        return TCKCaseResult(
            self.case_id,
            TCKStatus.PASS,
            "real Browser-bound baseline behavior and all metadata-identical broken controls were executed and rejected",
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
        positive = _mapping(vector.get("positivePath"), f"{CASE_ID} positivePath")
        if dict(positive) != {
            "requiresBehaviorObservationAtBrowserBoundary": True,
            "portableExpectationsProviderNeutral": True,
        }:
            raise TCKAdapterError(f"{CASE_ID} positive execution contract changed")

        controls = _strings(
            vector.get("metadataIdenticalNegativeControls"),
            f"{CASE_ID} metadataIdenticalNegativeControls",
        )
        if len(controls) != len(set(controls)) or frozenset(controls) != _NEGATIVE_CONTROLS:
            raise TCKAdapterError(f"{CASE_ID} metadata-identical control set changed")

        forbidden = _strings(
            vector.get("forbiddenPortableBranches"),
            f"{CASE_ID} forbiddenPortableBranches",
        )
        # The normative vector owns the concrete forbidden vocabulary. Portable
        # source code deliberately does not branch on those values; validating a
        # duplicate-free non-empty vector is sufficient here and avoids copying
        # provider/product names into executable branch logic.
        if len(forbidden) != len(set(forbidden)):
            raise TCKAdapterError(f"{CASE_ID} forbidden branch vector has duplicates")

        for key in (
            "metadataOnlyConformanceRejected",
            "brokenBehaviorRejected",
            "portableProviderBranchingRejected",
            "providerSpecificFixtureControlMayRemainPrivate",
        ):
            if expect.get(key) is not True:
                raise TCKAdapterError(f"{CASE_ID} expect.{key} must be true")

    def _validate_control_set(self) -> None:
        actual = set(self._negative_controls.operations)
        if actual != _NEGATIVE_CONTROLS:
            missing = sorted(_NEGATIVE_CONTROLS - actual)
            unexpected = sorted(actual - _NEGATIVE_CONTROLS)
            raise TCKAdapterError(
                "executed Browser negative-control set is incomplete: "
                f"missing={missing}, unexpected={unexpected}"
            )
        for obligation, operation in self._negative_controls.operations.items():
            if not callable(operation):
                raise TCKAdapterError(
                    f"executed Browser control {obligation} is not callable"
                )

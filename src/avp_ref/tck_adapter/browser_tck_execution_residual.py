"""Provider-neutral evaluator for Browser execution identity and residual state.

AVP-BROWSER-013/014 do not prescribe provider-specific execution-binding keys.
This evaluator therefore receives an explicit material-input plan from the
materialized test environment. Each material input must either map to an exact
immutable upstream execution binding or, for cookie temporal behavior, be
protected by the profile's fail-closed restore-eligibility proof. Excluded-state
surfaces require an explicit governed disposition and material interference is
behaviorally tested through the privileged fixture-control seam.

The plan is not conformance evidence by itself: execution-binding drift,
excluded-state interference, and temporal ineligibility are all induced and must
be rejected by the actual Browser harness path. Temporal test-driver mechanics
are injected as a semantic callable so portable code never names a private
provider-control API.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable

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

CASE_ID = "AVP-TCK-BROWSER-EXECUTION-RESIDUAL-001"

_MATERIAL_INPUTS = frozenset(
    {
        "browser-build-artifact",
        "storage-partition-isolation-policy",
        "cookie-temporal-policy",
    }
)
_EXCLUDED_SURFACES = frozenset(
    {
        "service-worker-state",
        "cache-storage-state",
        "indexeddb-state",
        "extension-or-preload-state",
    }
)
_ACCEPTED_DISPOSITIONS = frozenset(
    {
        "noninterfering-by-isolation",
        "immutable-policy-or-identity-bound",
        "fail-closed-insufficient",
    }
)
_NEGATIVE_CONTROLS = frozenset(
    {
        "product-label-only-as-execution-identity",
        "material-execution-input-unbound",
        "bound-execution-input-drift-ignored",
        "excluded-state-interference-silently-ignored",
    }
)
_TEMPORAL_FAIL_CLOSED = "fail-closed-restore-eligibility"


def _freeze_mapping(value: Mapping[str, str]) -> Mapping[str, str]:
    return MappingProxyType({str(key): str(item) for key, item in value.items()})


@dataclass(frozen=True, slots=True)
class BrowserExecutionResidualPlan:
    """Materialized wiring from normative input classes to execution evidence."""

    binding_references: Mapping[str, str]
    cookie_temporal_policy: str
    excluded_state_dispositions: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "binding_references",
            _freeze_mapping(self.binding_references),
        )
        object.__setattr__(
            self,
            "excluded_state_dispositions",
            _freeze_mapping(self.excluded_state_dispositions),
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


def _require_exact_set(value: object, expected: frozenset[str], label: str) -> None:
    values = _strings(value, label)
    if len(values) != len(set(values)) or frozenset(values) != expected:
        raise TCKAdapterError(f"{label} changed from the governed set")


def _settled() -> BrowserSettlementLedger:
    ledger = BrowserSettlementLedger()
    ledger.close_subject_admission()
    return ledger


def _require_rejected(operation: Callable[[], object], label: str) -> None:
    try:
        operation()
    except BrowserHarnessError:
        return
    raise BrowserVerificationError(
        f"Browser execution/residual negative control accepted: {label}"
    )


def _plain_bindings(value: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for reference, raw_binding in value.items():
        if not isinstance(reference, str) or not reference:
            raise TCKAdapterError("execution binding reference must be non-empty")
        binding = _mapping(raw_binding, f"executionBindings.{reference}")
        if set(binding) != {"identity", "identityType"}:
            raise TCKAdapterError(
                f"executionBindings.{reference} must contain identity and identityType only"
            )
        identity = binding.get("identity")
        identity_type = binding.get("identityType")
        if not isinstance(identity, str) or not identity:
            raise TCKAdapterError(
                f"executionBindings.{reference}.identity must be non-empty"
            )
        if identity_type not in {"content", "version", "symbolic"}:
            raise TCKAdapterError(
                f"executionBindings.{reference}.identityType is unsupported"
            )
        result[reference] = {
            "identity": identity,
            "identityType": str(identity_type),
        }
    return result


class BrowserExecutionResidualTCKEvaluator:
    """Execute immutable execution identity and excluded-state obligations."""

    case_id = CASE_ID

    def __init__(
        self,
        *,
        harness: BrowserConformanceHarness,
        fixture: MaterializedBrowserFixture,
        expected_execution_bindings: Mapping[str, Any],
        plan: BrowserExecutionResidualPlan,
        set_temporal_eligibility: Callable[[BrowserSUT, bool], None],
    ) -> None:
        if not callable(set_temporal_eligibility):
            raise TCKAdapterError("Browser temporal eligibility control must be callable")
        self._harness = harness
        self._fixture = fixture
        self._expected_bindings = _plain_bindings(expected_execution_bindings)
        self._plan = plan
        self._set_temporal_eligibility = set_temporal_eligibility

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        vector, expect = self._case_parts(case)
        self._validate_contract(vector, expect)
        self._validate_material_plan()
        sut = self._harness.provision()
        try:
            self._verify_bound_execution_identity()
            baseline = self._harness.authoritative_projection(sut, _settled())
            self._execute_binding_drift_controls(sut)
            self._execute_excluded_state_control(sut, baseline.digest)
            self._execute_temporal_policy_control(sut)
        except BrowserHarnessError as exc:
            return TCKCaseResult(
                self.case_id,
                TCKStatus.FAIL,
                f"Browser execution/residual obligation failed: {exc}",
            )
        finally:
            sut.release()
        return TCKCaseResult(
            self.case_id,
            TCKStatus.PASS,
            "material execution identity, excluded-state disposition, drift rejection, interference rejection, and temporal fail-closed behavior verified",
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
        _require_exact_set(
            vector.get("materialExecutionInputs"),
            _MATERIAL_INPUTS,
            f"{CASE_ID} materialExecutionInputs",
        )
        _require_exact_set(
            vector.get("excludedStateControls"),
            _EXCLUDED_SURFACES,
            f"{CASE_ID} excludedStateControls",
        )
        _require_exact_set(
            vector.get("acceptedDispositions"),
            _ACCEPTED_DISPOSITIONS,
            f"{CASE_ID} acceptedDispositions",
        )
        _require_exact_set(
            vector.get("negativeControls"),
            _NEGATIVE_CONTROLS,
            f"{CASE_ID} negativeControls",
        )
        for key in (
            "immutableExecutionIdentityRequired",
            "excludedStateDispositionRequired",
            "providerLabelInsufficient",
            "negativeControlsRejected",
        ):
            if expect.get(key) is not True:
                raise TCKAdapterError(f"{CASE_ID} expect.{key} must be true")

    def _validate_material_plan(self) -> None:
        required_bound = {
            "browser-build-artifact",
            "storage-partition-isolation-policy",
        }
        actual_bound = set(self._plan.binding_references)
        if actual_bound != required_bound:
            missing = sorted(required_bound - actual_bound)
            unexpected = sorted(actual_bound - required_bound)
            raise TCKAdapterError(
                "Browser material execution binding plan is incomplete: "
                f"missing={missing}, unexpected={unexpected}"
            )
        for material_input, reference in self._plan.binding_references.items():
            if not isinstance(reference, str) or not reference:
                raise TCKAdapterError(
                    f"material input {material_input} lacks execution binding reference"
                )
            if reference not in self._expected_bindings:
                raise TCKAdapterError(
                    f"material input {material_input} references unknown immutable binding"
                )

        if self._plan.cookie_temporal_policy != _TEMPORAL_FAIL_CLOSED:
            raise TCKAdapterError(
                "cookie temporal policy must use the governed fail-closed restore-eligibility proof"
            )

        dispositions = dict(self._plan.excluded_state_dispositions)
        if set(dispositions) != _EXCLUDED_SURFACES:
            missing = sorted(_EXCLUDED_SURFACES - set(dispositions))
            unexpected = sorted(set(dispositions) - _EXCLUDED_SURFACES)
            raise TCKAdapterError(
                "excluded-state disposition plan is incomplete: "
                f"missing={missing}, unexpected={unexpected}"
            )
        for surface, disposition in dispositions.items():
            if disposition not in _ACCEPTED_DISPOSITIONS:
                raise TCKAdapterError(
                    f"excluded surface {surface} uses an ungoverned disposition"
                )

    def _verify_bound_execution_identity(self) -> None:
        actual = _plain_bindings(
            _mapping(
                self._fixture.manifest.get("executionBindings"),
                "Browser Manifest executionBindings",
            )
        )
        for material_input, reference in self._plan.binding_references.items():
            expected = self._expected_bindings[reference]
            observed = actual.get(reference)
            if observed != expected:
                raise BrowserVerificationError(
                    f"material input {material_input} is not bound to exact upstream execution identity"
                )

    def _execute_binding_drift_controls(self, sut: BrowserSUT) -> None:
        reference = self._plan.binding_references["browser-build-artifact"]
        original = self._expected_bindings[reference]["identity"]
        self._harness.fixture_control.set_execution_binding(
            sut,
            reference,
            "synthetic-label-only-identity",
        )
        try:
            _require_rejected(
                lambda: self._harness.authoritative_projection(sut, _settled()),
                "product-label-only-as-execution-identity",
            )
            _require_rejected(
                lambda: self._harness.authoritative_projection(sut, _settled()),
                "bound-execution-input-drift-ignored",
            )
        finally:
            self._harness.fixture_control.set_execution_binding(
                sut,
                reference,
                original,
            )
        self._harness.authoritative_projection(sut, _settled())

    def _execute_excluded_state_control(
        self,
        sut: BrowserSUT,
        baseline_digest: str,
    ) -> None:
        self._harness.fixture_control.set_excluded_state_interference(
            sut,
            interfering=True,
        )
        try:
            _require_rejected(
                lambda: self._harness.authoritative_projection(sut, _settled()),
                "excluded-state-interference-silently-ignored",
            )
        finally:
            self._harness.fixture_control.set_excluded_state_interference(
                sut,
                interfering=False,
            )
        restored = self._harness.authoritative_projection(sut, _settled())
        if restored.digest != baseline_digest:
            raise BrowserVerificationError(
                "excluded-state control unexpectedly changed selected Browser identity"
            )

    def _execute_temporal_policy_control(self, sut: BrowserSUT) -> None:
        snapshot = self._harness.verified_snapshot(sut, _settled())
        self._set_temporal_eligibility(sut, False)
        try:
            _require_rejected(
                lambda: self._harness.verified_restore(
                    sut,
                    snapshot,
                    _settled(),
                    _settled(),
                ),
                "cookie-temporal-policy-fail-closed",
            )
        finally:
            self._set_temporal_eligibility(sut, True)

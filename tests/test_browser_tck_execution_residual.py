from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from avp_ref.environment.models import SnapshotRef
from avp_ref.tck_adapter.browser_harness import (
    BrowserCanonicalizationError,
    BrowserConformanceHarness,
    BrowserVerificationError,
    MaterializedBrowserFixture,
    canonical_state_image_digest,
    materialize_browser_fixture,
)
from avp_ref.tck_adapter.browser_tck_execution_residual import (
    BrowserExecutionResidualPlan,
    BrowserExecutionResidualTCKEvaluator,
)
from avp_ref.tck_adapter.models import TCKAdapterError, TCKStatus

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "conformance/fixtures/browser-state/v0.1/fixture-source.json"
CASE = ROOT / "conformance/tck/cases/browser/AVP-TCK-BROWSER-EXECUTION-RESIDUAL-001.yaml"


class _Verifier:
    def verify_canonical_origin(self, origin: str) -> None:
        if origin not in {"https://a.example", "https://b.example"}:
            raise BrowserCanonicalizationError(f"origin is not admitted: {origin}")

    def verify_canonical_cookie_domain(self, domain: str) -> None:
        if domain != "a.test":
            raise BrowserCanonicalizationError(f"domain is not admitted: {domain}")


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return copy.deepcopy(value)


class _SUT:
    _counter = 0

    def __init__(self, fixture: MaterializedBrowserFixture, verifier: _Verifier) -> None:
        type(self)._counter += 1
        self.handle_id = f"residual-browser-{type(self)._counter}"
        self.fixture = fixture
        self.verifier = verifier
        self.state = _plain(fixture.baseline_image)
        self.execution_bindings = _plain(fixture.manifest["executionBindings"])
        self.excluded_interference = False
        self.restore_eligible = True
        self.snapshots: dict[str, dict[str, Any]] = {}

    def snapshot(self) -> SnapshotRef:
        snapshot_id = f"{self.handle_id}-snapshot-{len(self.snapshots) + 1}"
        self.snapshots[snapshot_id] = _plain(self.state)
        return SnapshotRef(
            snapshot_id=snapshot_id,
            handle_id=self.handle_id,
            state_digest=canonical_state_image_digest(
                self.state,
                self.fixture.manifest,
                self.verifier,
            ),
            logical_time=len(self.snapshots),
            consistency="settled",
            adapter_name="memory-browser",
        )

    def reset(self) -> None:
        self.state = _plain(self.fixture.baseline_image)

    def restore(self, snapshot: SnapshotRef) -> None:
        self.state = _plain(self.snapshots[snapshot.snapshot_id])

    def release(self) -> None:
        return


class _Observer:
    def __init__(self, expected_bindings: Mapping[str, Any]) -> None:
        self.expected_bindings = _plain(expected_bindings)

    def verify_execution_conditions(
        self,
        sut: _SUT,
        fixture: MaterializedBrowserFixture,
    ) -> None:
        if sut.execution_bindings != self.expected_bindings:
            raise BrowserVerificationError("Browser execution-input identity drift")
        if _plain(fixture.manifest["executionBindings"]) != self.expected_bindings:
            raise BrowserVerificationError("materialized Browser execution identity mismatch")
        if sut.excluded_interference:
            raise BrowserVerificationError("material excluded Browser state interferes")

    def verify_restore_eligibility(
        self,
        sut: _SUT,
        fixture: MaterializedBrowserFixture,
        snapshot: SnapshotRef,
    ) -> None:
        del fixture, snapshot
        if not sut.restore_eligible:
            raise BrowserVerificationError("cookie temporal restore eligibility is unresolved")

    def project_selected_state(
        self,
        sut: _SUT,
        fixture: MaterializedBrowserFixture,
    ) -> Mapping[str, Any]:
        del fixture
        return _plain(sut.state)


class _Control:
    def seed_baseline(self, sut: _SUT, fixture: MaterializedBrowserFixture) -> None:
        sut.state = _plain(fixture.baseline_image)

    def seed_cookie(
        self,
        sut: _SUT,
        cookie: Mapping[str, Any],
        *,
        provenance: Mapping[str, Any] | None = None,
    ) -> None:
        del provenance
        sut.state["cookies"].append(dict(cookie))

    def seed_local_storage(
        self,
        sut: _SUT,
        origin: str,
        entries: Sequence[Mapping[str, str]],
    ) -> None:
        for origin_state in sut.state["origins"]:
            if origin_state["origin"] == origin:
                origin_state["localStorage"] = [dict(item) for item in entries]
                return
        raise BrowserVerificationError(f"unknown origin: {origin}")

    def seed_partitioned_cookie(self, sut: _SUT, cookie: Mapping[str, Any]) -> None:
        del sut, cookie

    def set_execution_binding(self, sut: _SUT, reference: str, identity: str) -> None:
        try:
            sut.execution_bindings[reference]["identity"] = identity
        except KeyError as exc:
            raise BrowserVerificationError(f"unknown execution binding: {reference}") from exc

    def set_excluded_state_interference(self, sut: _SUT, *, interfering: bool) -> None:
        sut.excluded_interference = interfering

    def seed_evaluator_private_state(self, sut: _SUT) -> None:
        del sut


class _Backend:
    def __init__(self, expected_bindings: Mapping[str, Any]) -> None:
        self._observer = _Observer(expected_bindings)
        self._control = _Control()

    @property
    def observer(self) -> _Observer:
        return self._observer

    @property
    def fixture_control(self) -> _Control:
        return self._control

    def provision(self, fixture: MaterializedBrowserFixture) -> _SUT:
        return _SUT(fixture, _Verifier())


def _fixture() -> tuple[MaterializedBrowserFixture, _Verifier]:
    verifier = _Verifier()
    source = json.loads(FIXTURE.read_text(encoding="utf-8"))
    fixture = materialize_browser_fixture(
        source,
        resolved_origins={
            "primary": "https://a.example",
            "secondary": "https://b.example",
        },
        verifier=verifier,
    )
    return fixture, verifier


def _case() -> dict[str, Any]:
    return yaml.safe_load(CASE.read_text(encoding="utf-8"))


def _plan() -> BrowserExecutionResidualPlan:
    return BrowserExecutionResidualPlan(
        binding_references={
            "browser-build-artifact": "browserBuild",
            "storage-partition-isolation-policy": "storageIsolationPolicy",
        },
        cookie_temporal_policy="fail-closed-restore-eligibility",
        excluded_state_dispositions={
            "service-worker-state": "noninterfering-by-isolation",
            "cache-storage-state": "noninterfering-by-isolation",
            "indexeddb-state": "noninterfering-by-isolation",
            "extension-or-preload-state": "immutable-policy-or-identity-bound",
        },
    )


def _set_temporal_eligibility(sut: _SUT, eligible: bool) -> None:
    sut.restore_eligible = eligible


def _evaluator(
    fixture: MaterializedBrowserFixture,
    verifier: _Verifier,
    plan: BrowserExecutionResidualPlan,
) -> BrowserExecutionResidualTCKEvaluator:
    expected = fixture.manifest["executionBindings"]
    harness = BrowserConformanceHarness(_Backend(expected), fixture, verifier)
    return BrowserExecutionResidualTCKEvaluator(
        harness=harness,
        fixture=fixture,
        expected_execution_bindings=expected,
        plan=plan,
        set_temporal_eligibility=_set_temporal_eligibility,
    )


class BrowserExecutionResidualTCKEvaluatorTest(unittest.TestCase):
    def test_executes_binding_drift_interference_and_temporal_controls(self) -> None:
        fixture, verifier = _fixture()
        result = _evaluator(fixture, verifier, _plan()).evaluate(_case())

        self.assertIs(TCKStatus.PASS, result.status, result.detail)

    def test_rejects_unbound_material_execution_input_before_execution(self) -> None:
        fixture, verifier = _fixture()
        plan = BrowserExecutionResidualPlan(
            binding_references={"browser-build-artifact": "browserBuild"},
            cookie_temporal_policy="fail-closed-restore-eligibility",
            excluded_state_dispositions=_plan().excluded_state_dispositions,
        )

        with self.assertRaisesRegex(TCKAdapterError, "binding plan is incomplete"):
            _evaluator(fixture, verifier, plan).evaluate(_case())

    def test_rejects_missing_excluded_state_disposition(self) -> None:
        fixture, verifier = _fixture()
        dispositions = dict(_plan().excluded_state_dispositions)
        dispositions.pop("indexeddb-state")
        plan = BrowserExecutionResidualPlan(
            binding_references=_plan().binding_references,
            cookie_temporal_policy="fail-closed-restore-eligibility",
            excluded_state_dispositions=dispositions,
        )

        with self.assertRaisesRegex(TCKAdapterError, "disposition plan is incomplete"):
            _evaluator(fixture, verifier, plan).evaluate(_case())


if __name__ == "__main__":
    unittest.main()

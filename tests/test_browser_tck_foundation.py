from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any, Mapping, Sequence

from avp_ref.environment.models import SnapshotRef
from avp_ref.tck_adapter.browser_harness import (
    BrowserCanonicalizationError,
    BrowserVerificationError,
    MaterializedBrowserFixture,
    canonical_state_image_digest,
    materialize_browser_fixture,
)
from avp_ref.tck_adapter.browser_tck_foundation import (
    BrowserIdentityTCKEvaluator,
    BrowserSelectionCanonicalTCKEvaluator,
    BrowserStateImageTCKEvaluator,
)
from avp_ref.tck_adapter.models import TCKStatus


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "conformance/fixtures/browser-state/v0.1/fixture-source.json"


class _Verifier:
    def __init__(self, origins: Sequence[str], domains: Sequence[str]) -> None:
        self._origins = frozenset(origins)
        self._domains = frozenset(domains)

    def verify_canonical_origin(self, origin: str) -> None:
        if origin not in self._origins:
            raise BrowserCanonicalizationError(f"origin is not admitted: {origin}")

    def verify_canonical_cookie_domain(self, domain: str) -> None:
        if domain not in self._domains:
            raise BrowserCanonicalizationError(f"domain is not admitted: {domain}")


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return copy.deepcopy(value)


class _SUT:
    _counter = 0

    def __init__(self, fixture: MaterializedBrowserFixture, verifier: _Verifier) -> None:
        type(self)._counter += 1
        self.handle_id = f"browser-{type(self)._counter}"
        self._fixture = fixture
        self._verifier = verifier
        self._state = _thaw(fixture.baseline_image)
        self._snapshots: dict[str, dict[str, Any]] = {}
        self._released = False

    def snapshot(self) -> SnapshotRef:
        snapshot_id = f"{self.handle_id}-snapshot"
        self._snapshots[snapshot_id] = _thaw(self._state)
        return SnapshotRef(
            snapshot_id=snapshot_id,
            handle_id=self.handle_id,
            state_digest=canonical_state_image_digest(
                self._state,
                self._fixture.manifest,
                self._verifier,
            ),
            logical_time=1,
            consistency="settled",
            adapter_name="memory-browser",
        )

    def reset(self) -> None:
        self._state = _thaw(self._fixture.baseline_image)

    def restore(self, snapshot: SnapshotRef) -> None:
        self._state = _thaw(self._snapshots[snapshot.snapshot_id])

    def release(self) -> None:
        self._released = True


class _Observer:
    def verify_execution_conditions(
        self,
        sut: _SUT,
        fixture: MaterializedBrowserFixture,
    ) -> None:
        del sut, fixture

    def verify_restore_eligibility(
        self,
        sut: _SUT,
        fixture: MaterializedBrowserFixture,
        snapshot: SnapshotRef,
    ) -> None:
        del sut, fixture, snapshot

    def project_selected_state(
        self,
        sut: _SUT,
        fixture: MaterializedBrowserFixture,
    ) -> Mapping[str, Any]:
        del fixture
        return _thaw(sut._state)


class _Control:
    def seed_baseline(self, sut: _SUT, fixture: MaterializedBrowserFixture) -> None:
        sut._state = _thaw(fixture.baseline_image)

    def seed_cookie(
        self,
        sut: _SUT,
        cookie: Mapping[str, Any],
        *,
        provenance: Mapping[str, Any] | None = None,
    ) -> None:
        del provenance
        sut._state["cookies"].append(dict(cookie))

    def seed_local_storage(
        self,
        sut: _SUT,
        origin: str,
        entries: Sequence[Mapping[str, str]],
    ) -> None:
        for state in sut._state["origins"]:
            if state["origin"] == origin:
                state["localStorage"] = [dict(item) for item in entries]
                return
        raise BrowserVerificationError(f"unknown localStorage origin: {origin}")

    def seed_partitioned_cookie(self, sut: _SUT, cookie: Mapping[str, Any]) -> None:
        del sut, cookie

    def set_execution_binding(self, sut: _SUT, reference: str, identity: str) -> None:
        del sut, reference, identity

    def set_excluded_state_interference(self, sut: _SUT, *, interfering: bool) -> None:
        del sut, interfering

    def seed_evaluator_private_state(self, sut: _SUT) -> None:
        del sut


class _Backend:
    def __init__(self, verifier: _Verifier) -> None:
        self._verifier = verifier
        self._observer = _Observer()
        self._control = _Control()

    @property
    def observer(self) -> _Observer:
        return self._observer

    @property
    def fixture_control(self) -> _Control:
        return self._control

    def provision(self, fixture: MaterializedBrowserFixture) -> _SUT:
        return _SUT(fixture, self._verifier)


def _load_yaml_case(name: str) -> dict[str, Any]:
    import yaml

    path = ROOT / "conformance/tck/cases/browser" / name
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _fixture() -> tuple[MaterializedBrowserFixture, _Verifier]:
    source = json.loads(FIXTURE.read_text(encoding="utf-8"))
    origins = ("https://a.example", "https://b.example")
    verifier = _Verifier(origins, ("a.example", "b.example"))
    fixture = materialize_browser_fixture(
        source,
        resolved_origins={"primary": origins[0], "secondary": origins[1]},
        verifier=verifier,
    )
    return fixture, verifier


class BrowserTCKFoundationTest(unittest.TestCase):
    def test_identity_executes_sibling_isolation_and_binding_reuse(self) -> None:
        fixture, verifier = _fixture()
        case = _load_yaml_case("AVP-TCK-BROWSER-IDENTITY-001.yaml")
        case["vector"]["manifestExecutionBindings"] = _thaw(
            fixture.manifest["executionBindings"]
        )
        case["vector"]["upstreamIdentityBindings"] = _thaw(
            fixture.manifest["executionBindings"]
        )
        evaluator = BrowserIdentityTCKEvaluator(
            backend=_Backend(verifier),
            fixture=fixture,
            verifier=verifier,
            upstream_execution_bindings=fixture.manifest["executionBindings"],
        )

        result = evaluator.evaluate(case)

        self.assertIs(TCKStatus.PASS, result.status)

    def test_identity_rejects_vector_binding_drift(self) -> None:
        fixture, verifier = _fixture()
        case = _load_yaml_case("AVP-TCK-BROWSER-IDENTITY-001.yaml")
        bindings = _thaw(fixture.manifest["executionBindings"])
        case["vector"]["manifestExecutionBindings"] = copy.deepcopy(bindings)
        case["vector"]["upstreamIdentityBindings"] = copy.deepcopy(bindings)
        case["vector"]["manifestExecutionBindings"]["browserBuild"][
            "identity"
        ] = "drift"
        evaluator = BrowserIdentityTCKEvaluator(
            backend=_Backend(verifier),
            fixture=fixture,
            verifier=verifier,
            upstream_execution_bindings=fixture.manifest["executionBindings"],
        )

        with self.assertRaisesRegex(Exception, "reuse exact upstream"):
            evaluator.evaluate(case)

    def test_selection_canonical_executes_governed_controls(self) -> None:
        fixture, verifier = _fixture()
        case = _load_yaml_case("AVP-TCK-BROWSER-SELECTION-CANONICAL-001.yaml")
        evaluator = BrowserSelectionCanonicalTCKEvaluator(
            fixture=fixture,
            verifier=verifier,
        )

        result = evaluator.evaluate(case)

        self.assertIs(TCKStatus.PASS, result.status)

    def test_selection_rejects_governed_control_set_drift(self) -> None:
        fixture, verifier = _fixture()
        case = _load_yaml_case("AVP-TCK-BROWSER-SELECTION-CANONICAL-001.yaml")
        case["vector"]["invalidControls"].pop()
        evaluator = BrowserSelectionCanonicalTCKEvaluator(
            fixture=fixture,
            verifier=verifier,
        )

        with self.assertRaisesRegex(Exception, "governed control set"):
            evaluator.evaluate(case)

    def test_state_image_executes_complete_binding_and_expiry_semantics(self) -> None:
        fixture, verifier = _fixture()
        case = _load_yaml_case("AVP-TCK-BROWSER-STATE-IMAGE-001.yaml")
        evaluator = BrowserStateImageTCKEvaluator(
            verifier=verifier,
            execution_bindings=fixture.manifest["executionBindings"],
        )

        result = evaluator.evaluate(case)

        self.assertIs(TCKStatus.PASS, result.status)

    def test_state_image_rejects_expectation_drift_before_execution(self) -> None:
        fixture, verifier = _fixture()
        case = _load_yaml_case("AVP-TCK-BROWSER-STATE-IMAGE-001.yaml")
        case["expect"]["closedSerializedShape"] = False
        evaluator = BrowserStateImageTCKEvaluator(
            verifier=verifier,
            execution_bindings=fixture.manifest["executionBindings"],
        )

        with self.assertRaisesRegex(Exception, "closedSerializedShape"):
            evaluator.evaluate(case)


if __name__ == "__main__":
    unittest.main()

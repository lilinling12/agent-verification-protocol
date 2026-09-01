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
from avp_ref.tck_adapter.browser_tck_cookie import BrowserCookieTCKEvaluator
from avp_ref.tck_adapter.models import TCKAdapterError, TCKStatus

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "conformance/fixtures/browser-state/v0.1/fixture-source.json"
CASE = ROOT / "conformance/tck/cases/browser/AVP-TCK-BROWSER-COOKIE-001.yaml"


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
        self.handle_id = f"cookie-browser-{type(self)._counter}"
        self.fixture = fixture
        self.verifier = verifier
        self.state = _plain(fixture.baseline_image)
        self.snapshots: dict[str, dict[str, Any]] = {}
        self.restore_eligible = True

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
        # Partitioned state is intentionally outside this profile's authoritative
        # projection. The memory backend records no portable state for this control.
        del sut, cookie

    def set_execution_binding(self, sut: _SUT, reference: str, identity: str) -> None:
        del sut, reference, identity

    def set_excluded_state_interference(self, sut: _SUT, *, interfering: bool) -> None:
        del sut, interfering

    def seed_evaluator_private_state(self, sut: _SUT) -> None:
        del sut

    def set_restore_temporal_eligibility(self, sut: _SUT, *, eligible: bool) -> None:
        sut.restore_eligible = eligible


class _Backend:
    def __init__(self) -> None:
        self._observer = _Observer()
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


class BrowserCookieTCKEvaluatorTest(unittest.TestCase):
    def test_executes_cookie_projection_and_negative_controls(self) -> None:
        fixture, verifier = _fixture()
        harness = BrowserConformanceHarness(_Backend(), fixture, verifier)
        evaluator = BrowserCookieTCKEvaluator(
            harness=harness,
            fixture=fixture,
            verifier=verifier,
        )

        result = evaluator.evaluate(_case())

        self.assertIs(TCKStatus.PASS, result.status, result.detail)

    def test_rejects_portable_identity_contract_drift(self) -> None:
        fixture, verifier = _fixture()
        harness = BrowserConformanceHarness(_Backend(), fixture, verifier)
        evaluator = BrowserCookieTCKEvaluator(
            harness=harness,
            fixture=fixture,
            verifier=verifier,
        )
        case = _case()
        case["vector"]["portableIdentity"] = ["name", "domain", "path"]

        with self.assertRaisesRegex(TCKAdapterError, "portable cookie identity changed"):
            evaluator.evaluate(case)

    def test_rejects_samesite_state_contract_drift(self) -> None:
        fixture, verifier = _fixture()
        harness = BrowserConformanceHarness(_Backend(), fixture, verifier)
        evaluator = BrowserCookieTCKEvaluator(
            harness=harness,
            fixture=fixture,
            verifier=verifier,
        )
        case = _case()
        case["vector"]["sameSiteStates"] = ["Strict", "Lax", "None"]

        with self.assertRaisesRegex(TCKAdapterError, "SameSite state set changed"):
            evaluator.evaluate(case)


if __name__ == "__main__":
    unittest.main()

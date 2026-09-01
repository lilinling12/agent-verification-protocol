from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from avp_ref.environment.models import SnapshotRef
from avp_ref.tck_adapter.browser_executed_capability import BrowserExecutedMetadata
from avp_ref.tck_adapter.browser_harness import (
    BrowserCanonicalizationError,
    BrowserConformanceHarness,
    BrowserSettlementLedger,
    BrowserVerificationError,
    MaterializedBrowserFixture,
    canonical_state_image_digest,
    materialize_browser_fixture,
)
from avp_ref.tck_adapter.browser_tck_executed_capability import (
    BrowserExecutedCapabilityTCKEvaluator,
    BrowserExecutedNegativeControlSet,
)
from avp_ref.tck_adapter.models import TCKAdapterError, TCKStatus

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "conformance/fixtures/browser-state/v0.1/fixture-source.json"
CASE = ROOT / "conformance/tck/cases/browser/AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001.yaml"


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
    def __init__(self, fixture: MaterializedBrowserFixture, verifier: _Verifier) -> None:
        self.handle_id = "executed-browser-1"
        self.fixture = fixture
        self.verifier = verifier
        self.state = _plain(fixture.baseline_image)

    def snapshot(self) -> SnapshotRef:
        return SnapshotRef(
            snapshot_id="snapshot-1",
            handle_id=self.handle_id,
            state_digest=canonical_state_image_digest(
                self.state,
                self.fixture.manifest,
                self.verifier,
            ),
            logical_time=1,
            consistency="settled",
            adapter_name="memory-browser",
        )

    def reset(self) -> None:
        self.state = _plain(self.fixture.baseline_image)

    def restore(self, snapshot: SnapshotRef) -> None:
        del snapshot

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
        del sut, fixture, snapshot

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
        del sut, origin, entries

    def seed_partitioned_cookie(self, sut: _SUT, cookie: Mapping[str, Any]) -> None:
        del sut, cookie

    def set_execution_binding(self, sut: _SUT, reference: str, identity: str) -> None:
        del sut, reference, identity

    def set_excluded_state_interference(self, sut: _SUT, *, interfering: bool) -> None:
        del sut, interfering

    def seed_evaluator_private_state(self, sut: _SUT) -> None:
        del sut


class _Backend:
    @property
    def observer(self) -> _Observer:
        return _Observer()

    @property
    def fixture_control(self) -> _Control:
        return _Control()

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


def _reject() -> object:
    raise BrowserVerificationError("synthetic broken implementation rejected")


def _controls(case: Mapping[str, Any]) -> dict[str, object]:
    return {
        name: _reject
        for name in case["vector"]["metadataIdenticalNegativeControls"]
    }


class BrowserExecutedCapabilityTCKEvaluatorTest(unittest.TestCase):
    def test_requires_all_metadata_identical_broken_controls_to_be_rejected(self) -> None:
        fixture, verifier = _fixture()
        backend = _Backend()
        harness = BrowserConformanceHarness(backend, fixture, verifier)
        sut = harness.provision()
        case = _case()
        evaluator = BrowserExecutedCapabilityTCKEvaluator(
            harness=harness,
            sut=sut,
            fixture=fixture,
            negative_controls=BrowserExecutedNegativeControlSet(
                operations=_controls(case),
                candidate_metadata=BrowserExecutedMetadata.from_fixture(fixture),
            ),
        )

        result = evaluator.evaluate(case)

        self.assertIs(TCKStatus.PASS, result.status, result.detail)

    def test_fails_when_one_broken_control_is_accepted(self) -> None:
        fixture, verifier = _fixture()
        backend = _Backend()
        harness = BrowserConformanceHarness(backend, fixture, verifier)
        sut = harness.provision()
        case = _case()
        controls = _controls(case)
        controls["corrupts-domstring-code-units"] = lambda: object()
        evaluator = BrowserExecutedCapabilityTCKEvaluator(
            harness=harness,
            sut=sut,
            fixture=fixture,
            negative_controls=BrowserExecutedNegativeControlSet(
                operations=controls,
                candidate_metadata=BrowserExecutedMetadata.from_fixture(fixture),
            ),
        )

        result = evaluator.evaluate(case)

        self.assertIs(TCKStatus.FAIL, result.status)
        self.assertIn("negative control was accepted", result.detail)

    def test_rejects_missing_negative_control_before_execution(self) -> None:
        fixture, verifier = _fixture()
        backend = _Backend()
        harness = BrowserConformanceHarness(backend, fixture, verifier)
        sut = harness.provision()
        case = _case()
        controls = _controls(case)
        controls.pop(next(iter(controls)))
        evaluator = BrowserExecutedCapabilityTCKEvaluator(
            harness=harness,
            sut=sut,
            fixture=fixture,
            negative_controls=BrowserExecutedNegativeControlSet(
                operations=controls,
                candidate_metadata=BrowserExecutedMetadata.from_fixture(fixture),
            ),
        )

        with self.assertRaisesRegex(TCKAdapterError, "control set is incomplete"):
            evaluator.evaluate(case)

    def test_rejects_metadata_drift_even_when_controls_all_reject(self) -> None:
        fixture, verifier = _fixture()
        backend = _Backend()
        harness = BrowserConformanceHarness(backend, fixture, verifier)
        sut = harness.provision()
        case = _case()
        metadata = BrowserExecutedMetadata.from_fixture(fixture)
        drifted = BrowserExecutedMetadata(
            profile=metadata.profile,
            revision=metadata.revision,
            canonical_representation=metadata.canonical_representation,
            manifest_digest="sha256:" + "f" * 64,
            execution_bindings=metadata.execution_bindings,
        )
        evaluator = BrowserExecutedCapabilityTCKEvaluator(
            harness=harness,
            sut=sut,
            fixture=fixture,
            negative_controls=BrowserExecutedNegativeControlSet(
                operations=_controls(case),
                candidate_metadata=drifted,
            ),
        )

        result = evaluator.evaluate(case)

        self.assertIs(TCKStatus.FAIL, result.status)
        self.assertIn("changed governed metadata", result.detail)


if __name__ == "__main__":
    unittest.main()

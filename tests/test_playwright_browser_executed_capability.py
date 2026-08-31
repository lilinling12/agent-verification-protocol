from __future__ import annotations

import copy
import json
import os
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator, Mapping

from avp_ref.environment.models import SnapshotRef
from avp_ref.tck_adapter.browser_executed_capability import (
    BrowserExecutedCapabilityEvaluator,
    BrowserExecutedMetadata,
)
from avp_ref.tck_adapter.browser_harness import (
    BrowserConformanceHarness,
    BrowserSettlementError,
    BrowserSettlementLedger,
    BrowserVerificationError,
    encode_dom_string_code_units,
)
from avp_ref.tck_adapter.playwright_browser import PlaywrightBrowserBackendHarness

ROOT = Path(__file__).resolve().parents[1]
_BROWSER = os.environ.get("AVP_PLAYWRIGHT_BROWSER")
_EXECUTION_FIXTURE = (
    ROOT / "conformance/fixtures/browser-state/v0.1/execution-fixture-source.json"
)


class _FixtureHandler(BaseHTTPRequestHandler):
    server_version = "AVPExecutedCapabilityFixture/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        payload = b"<!doctype html><meta charset=utf-8><title>AVP Browser</title>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        return


@contextmanager
def _fixture_server() -> Iterator[int]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield int(server.server_address[1])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _fixture_source() -> dict[str, Any]:
    return json.loads(_EXECUTION_FIXTURE.read_text(encoding="utf-8"))


def _settled() -> BrowserSettlementLedger:
    ledger = BrowserSettlementLedger()
    ledger.close_subject_admission()
    return ledger


class _ProjectionFaultObserver:
    """Test-driver seam that corrupts observation without changing metadata."""

    def __init__(self, delegate: Any, fault: str) -> None:
        self._delegate = delegate
        self._fault = fault

    def verify_execution_conditions(self, sut: Any, fixture: Any) -> None:
        if self._fault == "ignore-required-execution-input-drift":
            return
        if self._fault == "ignore-excluded-state-interference":
            resource = self._delegate._resource(sut)
            interfering = resource._excluded_state_interfering
            resource._excluded_state_interfering = False
            try:
                self._delegate.verify_execution_conditions(sut, fixture)
            finally:
                resource._excluded_state_interfering = interfering
            return
        self._delegate.verify_execution_conditions(sut, fixture)

    def verify_restore_eligibility(self, sut: Any, fixture: Any, snapshot: Any) -> None:
        self._delegate.verify_restore_eligibility(sut, fixture, snapshot)

    def project_selected_state(self, sut: Any, fixture: Any) -> Mapping[str, Any]:
        projected = copy.deepcopy(dict(self._delegate.project_selected_state(sut, fixture)))
        projected["cookies"] = [copy.deepcopy(dict(item)) for item in projected["cookies"]]
        projected["origins"] = [copy.deepcopy(dict(item)) for item in projected["origins"]]
        for origin in projected["origins"]:
            origin["localStorage"] = [
                copy.deepcopy(dict(item)) for item in origin["localStorage"]
            ]

        if self._fault == "loses-hostonly-cookie-identity":
            cookie = next(item for item in projected["cookies"] if item["name"] == "host_only")
            cookie["hostOnly"] = False
        elif self._fault == "collapses-samesite-default":
            cookie = next(item for item in projected["cookies"] if item["name"] == "host_only")
            cookie["sameSite"] = "Lax"
        elif self._fault == "admits-partitioned-state-as-unpartitioned":
            raw = next(
                item
                for item in sut._context.cookies()
                if item.get("name") == "partitioned_probe" and item.get("partitionKey")
            )
            projected["cookies"].append(
                {
                    "name": str(raw["name"]),
                    "value": str(raw["value"]),
                    "domain": str(raw["domain"]).lstrip("."),
                    "hostOnly": False,
                    "path": str(raw["path"]),
                    "persistent": False,
                    "secure": bool(raw["secure"]),
                    "httpOnly": bool(raw["httpOnly"]),
                    "sameSite": str(raw["sameSite"]),
                }
            )
        elif self._fault == "corrupts-domstring-code-units":
            entry = projected["origins"][0]["localStorage"][0]
            entry["value"] = encode_dom_string_code_units((50,))
        elif self._fault == "provider-enumeration-order":
            projected["cookies"].reverse()
            projected["origins"].reverse()
            for origin in projected["origins"]:
                origin["localStorage"].reverse()
        return projected


class _ObserverOverrideBackend:
    """Preserve one real backend while replacing only its evaluator observation seam."""

    def __init__(self, delegate: PlaywrightBrowserBackendHarness, observer: Any) -> None:
        self._delegate = delegate
        self._observer = observer

    @property
    def observer(self) -> Any:
        return self._observer

    @property
    def fixture_control(self) -> Any:
        return self._delegate.fixture_control

    def provision(self, fixture: Any) -> Any:
        return self._delegate.provision(fixture)


@unittest.skipUnless(
    _BROWSER == "chromium",
    "AVP_PLAYWRIGHT_BROWSER=chromium is required for executed capability evidence",
)
class PlaywrightBrowserExecutedCapabilityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = _fixture_server()
        self.port = self.server.__enter__()
        self.backend = PlaywrightBrowserBackendHarness(engine="chromium")
        self.origins = {
            "primary": f"http://a.test:{self.port}",
            "secondary": f"http://b.test:{self.port}",
        }
        self.fixture = self.backend.materialize_fixture(
            _fixture_source(),
            resolved_origins=self.origins,
        )
        self.reference_metadata = BrowserExecutedMetadata.from_fixture(self.fixture)
        self.evaluator = BrowserExecutedCapabilityEvaluator()

    def tearDown(self) -> None:
        try:
            self.backend.close()
        finally:
            self.server.__exit__(None, None, None)

    def _harness(self, observer: Any | None = None) -> BrowserConformanceHarness:
        if observer is None:
            backend: Any = self.backend
        else:
            backend = _ObserverOverrideBackend(self.backend, observer)
        return BrowserConformanceHarness(
            backend,
            self.fixture,
            self.backend.identity_verifier,
        )

    def _fault_harness(self, fault: str) -> BrowserConformanceHarness:
        # Provision once so the concrete backend creates its real observer.
        bootstrap = self._harness()
        sut = bootstrap.provision()
        sut.release()
        observer = _ProjectionFaultObserver(self.backend.observer, fault)
        return self._harness(observer)

    def _require_same_metadata(self) -> None:
        candidate = BrowserExecutedMetadata.from_fixture(self.fixture)
        self.evaluator.require_metadata_identical(self.reference_metadata, candidate)

    def test_positive_real_browser_path_is_accepted(self) -> None:
        harness = self._harness()
        sut = harness.provision()
        self._require_same_metadata()
        self.evaluator.require_baseline_projection(
            harness,
            sut,
            _settled(),
            expected_digest=self.fixture.baseline_image_digest,
        )

    def test_lost_hostonly_identity_is_rejected_with_identical_metadata(self) -> None:
        harness = self._fault_harness("loses-hostonly-cookie-identity")
        sut = harness.provision()
        self._require_same_metadata()
        self.evaluator.require_rejected(
            lambda: self.evaluator.require_baseline_projection(
                harness, sut, _settled(), expected_digest=self.fixture.baseline_image_digest
            ),
            obligation="preserve hostOnly cookie identity",
        )

    def test_collapsed_samesite_default_is_rejected_with_identical_metadata(self) -> None:
        harness = self._fault_harness("collapses-samesite-default")
        sut = harness.provision()
        self._require_same_metadata()
        self.evaluator.require_rejected(
            lambda: self.evaluator.require_baseline_projection(
                harness, sut, _settled(), expected_digest=self.fixture.baseline_image_digest
            ),
            obligation="preserve SameSite Default distinctly",
        )

    def test_partitioned_admission_is_rejected_with_identical_metadata(self) -> None:
        harness = self._fault_harness("admits-partitioned-state-as-unpartitioned")
        sut = harness.provision()
        harness.fixture_control.seed_partitioned_cookie(
            sut,
            {
                "name": "partitioned_probe",
                "value": "partitioned-value",
                "domain": "a.test",
                "path": "/",
                "topLevelSite": "https://b.test",
            },
        )
        self._require_same_metadata()
        self.evaluator.require_rejected(
            lambda: self.evaluator.require_baseline_projection(
                harness, sut, _settled(), expected_digest=self.fixture.baseline_image_digest
            ),
            obligation="exclude partitioned state from unpartitioned identity",
        )

    def test_domstring_corruption_is_rejected_with_identical_metadata(self) -> None:
        harness = self._fault_harness("corrupts-domstring-code-units")
        sut = harness.provision()
        self._require_same_metadata()
        self.evaluator.require_rejected(
            lambda: self.evaluator.require_baseline_projection(
                harness, sut, _settled(), expected_digest=self.fixture.baseline_image_digest
            ),
            obligation="preserve DOMString UTF-16 code units",
        )

    def test_provider_enumeration_order_does_not_change_canonical_identity(self) -> None:
        harness = self._fault_harness("provider-enumeration-order")
        sut = harness.provision()
        self._require_same_metadata()
        self.evaluator.require_baseline_projection(
            harness,
            sut,
            _settled(),
            expected_digest=self.fixture.baseline_image_digest,
        )

    def test_provider_order_snapshot_digest_claim_is_rejected(self) -> None:
        harness = self._harness()
        sut = harness.provision()
        original_snapshot = sut.snapshot

        def provider_order_snapshot() -> SnapshotRef:
            actual = original_snapshot()
            return SnapshotRef(
                snapshot_id=actual.snapshot_id,
                handle_id=actual.handle_id,
                state_digest="sha256:" + "0" * 64,
                logical_time=actual.logical_time,
                consistency=actual.consistency,
                adapter_name=actual.adapter_name,
            )

        sut.snapshot = provider_order_snapshot
        try:
            self._require_same_metadata()
            self.evaluator.require_rejected(
                lambda: harness.verified_snapshot(sut, _settled()),
                obligation="reject provider-order snapshot digest claim",
            )
        finally:
            sut.snapshot = original_snapshot

    def test_restore_success_without_reprojection_is_rejected(self) -> None:
        harness = self._harness()
        sut = harness.provision()
        snapshot = harness.verified_snapshot(sut, _settled())
        harness.fixture_control.seed_local_storage(
            sut,
            self.origins["secondary"],
            (
                {
                    "key": encode_dom_string_code_units((120,)),
                    "value": encode_dom_string_code_units((49,)),
                },
            ),
        )
        original_restore = sut.restore
        sut.restore = lambda ignored: None
        try:
            self._require_same_metadata()
            self.evaluator.require_rejected(
                lambda: harness.verified_restore(sut, snapshot, _settled(), _settled()),
                obligation="independently reproject restored target state",
            )
        finally:
            sut.restore = original_restore

    def test_unsettled_projection_is_rejected_before_provider_observation(self) -> None:
        harness = self._harness()
        sut = harness.provision()
        unsettled = BrowserSettlementLedger()
        unsettled.accept_relevant_mutation("pending-browser-write")
        self._require_same_metadata()
        with self.assertRaises(BrowserSettlementError):
            harness.authoritative_projection(sut, unsettled)

    def test_evaluator_private_leak_is_rejected_with_identical_metadata(self) -> None:
        harness = self._harness()
        sut = harness.provision()
        private_value = "evaluator-private-browser-value"
        harness.fixture_control.seed_local_storage(
            sut,
            self.origins["secondary"],
            (
                {
                    "key": encode_dom_string_code_units(tuple(map(ord, "private-key"))),
                    "value": encode_dom_string_code_units(tuple(map(ord, private_value))),
                },
            ),
        )
        page = sut._context.new_page()
        try:
            page.goto(self.origins["secondary"], wait_until="domcontentloaded")
            observed_private = str(page.evaluate("localStorage.getItem('private-key')"))
        finally:
            page.close()
        self.assertEqual(private_value, observed_private)
        self._require_same_metadata()
        self.evaluator.require_rejected(
            lambda: self.evaluator.require_subject_visibility(
                {"value": "public-observation", "leaked": observed_private},
                authorized_surface={"value": "public-observation"},
                evaluator_private_values=(private_value,),
            ),
            obligation="prevent evaluator-private state leakage to Subject surface",
        )

    def test_excluded_state_interference_cannot_be_ignored(self) -> None:
        harness = self._harness()
        sut = harness.provision()
        harness.fixture_control.set_excluded_state_interference(sut, interfering=True)
        self._require_same_metadata()
        self.evaluator.require_rejected(
            lambda: self.evaluator.require_baseline_projection(
                harness, sut, _settled(), expected_digest=self.fixture.baseline_image_digest
            ),
            obligation="fail closed on material excluded-state interference",
        )

    def test_required_execution_input_drift_cannot_be_ignored(self) -> None:
        harness = self._harness()
        sut = harness.provision()
        harness.fixture_control.set_execution_binding(
            sut,
            "storageIsolationPolicy",
            "drifted-storage-isolation-policy",
        )
        self._require_same_metadata()
        self.evaluator.require_rejected(
            lambda: self.evaluator.require_baseline_projection(
                harness, sut, _settled(), expected_digest=self.fixture.baseline_image_digest
            ),
            obligation="fail closed on required execution-input drift",
        )

    def test_broken_observer_that_ignores_execution_drift_is_detectably_wrong(self) -> None:
        harness = self._fault_harness("ignore-required-execution-input-drift")
        sut = harness.provision()
        harness.fixture_control.set_execution_binding(
            sut,
            "storageIsolationPolicy",
            "drifted-storage-isolation-policy",
        )
        self._require_same_metadata()
        with self.assertRaisesRegex(
            BrowserVerificationError,
            "negative control was accepted",
        ):
            self.evaluator.require_rejected(
                lambda: self.evaluator.require_baseline_projection(
                    harness, sut, _settled(), expected_digest=self.fixture.baseline_image_digest
                ),
                obligation="detect observer that ignores execution-input drift",
            )

    def test_broken_observer_that_ignores_excluded_interference_is_detectably_wrong(self) -> None:
        harness = self._fault_harness("ignore-excluded-state-interference")
        sut = harness.provision()
        harness.fixture_control.set_excluded_state_interference(sut, interfering=True)
        self._require_same_metadata()
        with self.assertRaisesRegex(
            BrowserVerificationError,
            "negative control was accepted",
        ):
            self.evaluator.require_rejected(
                lambda: self.evaluator.require_baseline_projection(
                    harness, sut, _settled(), expected_digest=self.fixture.baseline_image_digest
                ),
                obligation="detect observer that ignores excluded-state interference",
            )

    def test_evaluator_has_no_provider_name_branching(self) -> None:
        source = (
            ROOT / "src/avp_ref/tck_adapter/browser_executed_capability.py"
        ).read_text(encoding="utf-8").lower()
        forbidden = (
            "playwright",
            "selenium",
            "chromium",
            "firefox",
            "webkit",
            "cdp",
            "webdriver",
            "bidi",
        )
        for name in forbidden:
            with self.subTest(name=name):
                self.assertNotIn(name, source)


if __name__ == "__main__":
    unittest.main()

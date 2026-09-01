from __future__ import annotations

import copy
import hashlib
import json
import os
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator, Mapping

import rfc8785
import yaml

from avp_ref.environment.models import SnapshotRef
from avp_ref.tck_adapter.browser_executed_capability import (
    BrowserExecutedCapabilityEvaluator,
    BrowserExecutedMetadata,
)
from avp_ref.tck_adapter.browser_harness import (
    BrowserConformanceHarness,
    BrowserSettlementLedger,
    BrowserSUT,
    BrowserVerificationError,
    encode_dom_string_code_units,
)
from avp_ref.tck_adapter.browser_tck_adapter import (
    BROWSER_MANDATORY_CASE_IDS,
    BrowserTCKAdapter,
)
from avp_ref.tck_adapter.browser_tck_cookie import BrowserCookieTCKEvaluator
from avp_ref.tck_adapter.browser_tck_executed_capability import (
    BrowserExecutedCapabilityTCKEvaluator,
    BrowserExecutedNegativeControlSet,
)
from avp_ref.tck_adapter.browser_tck_execution_residual import (
    BrowserExecutionResidualPlan,
    BrowserExecutionResidualTCKEvaluator,
)
from avp_ref.tck_adapter.browser_tck_foundation import (
    BrowserIdentityTCKEvaluator,
    BrowserStateImageTCKEvaluator,
)
from avp_ref.tck_adapter.browser_tck_lifecycle import (
    BrowserSettlementLifecycleTCKEvaluator,
)
from avp_ref.tck_adapter.browser_tck_security import BrowserSecurityTCKEvaluator
from avp_ref.tck_adapter.browser_tck_selection import (
    BrowserSelectionCanonicalTCKEvaluator,
)
from avp_ref.tck_adapter.models import TCKStatus
from avp_ref.tck_adapter.playwright_browser import PlaywrightBrowserBackendHarness
from avp_ref.tck_adapter.reference_composite import ReferenceConformanceAdapter
from browser_playwright_tck_support import (
    ObserverOverrideBackend,
    PlaywrightBrowserSecurityEvidenceAdapter,
    ProjectionFaultObserver,
)

ROOT = Path(__file__).resolve().parents[1]
_BROWSER = os.environ.get("AVP_PLAYWRIGHT_BROWSER")
_FIXTURE_ROOT = ROOT / "conformance/fixtures/browser-state/v0.1"
_CASE_ROOT = ROOT / "conformance/tck/cases/browser"
_EXECUTION_FIXTURE = _FIXTURE_ROOT / "execution-fixture-source.json"
_SECURITY_FIXTURE = _FIXTURE_ROOT / "security-execution-fixture-source.json"
_PUBLIC_OBSERVATION = "public-observation"


class _ProfileFixtureHandler(BaseHTTPRequestHandler):
    server_version = "AVPBrowserTCKProfileFixture/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        path = self.path.split("?", 1)[0]
        if path == "/subject-observation":
            payload = _PUBLIC_OBSERVATION.encode("utf-8")
            content_type = "text/plain; charset=utf-8"
        else:
            payload = b"<!doctype html><meta charset=utf-8><title>AVP Browser TCK</title>"
            content_type = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        return


@contextmanager
def _fixture_server() -> Iterator[int]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ProfileFixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield int(server.server_address[1])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_case(case_id: str) -> dict[str, Any]:
    path = _CASE_ROOT / f"{case_id}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _settled() -> BrowserSettlementLedger:
    ledger = BrowserSettlementLedger()
    ledger.close_subject_admission()
    return ledger


def _sha256_jcs(value: Mapping[str, Any]) -> str:
    encoded = rfc8785.dumps(value)
    raw = encoded if isinstance(encoded, bytes) else encoded.encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


@unittest.skipUnless(
    _BROWSER == "chromium",
    "AVP_PLAYWRIGHT_BROWSER=chromium is required for complete Browser TCK execution",
)
class PlaywrightBrowserTCKProfileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = _fixture_server()
        self.port = self.server.__enter__()
        self.origins = {
            "primary": f"http://a.test:{self.port}",
            "secondary": f"http://b.test:{self.port}",
        }

        # One full-profile test owns one concrete Playwright runtime. Starting
        # multiple Sync API runtimes concurrently in the same thread is not a
        # supported Playwright lifecycle and would test the transport manager
        # rather than AVP's Browser semantics. Distinct TCK fixtures/resources
        # still remain independently materialized and isolated BrowserContexts.
        self.main_backend = PlaywrightBrowserBackendHarness(engine="chromium")

        main_source = _load_json(_EXECUTION_FIXTURE)
        security_source = _load_json(_SECURITY_FIXTURE)
        shared_bindings = copy.deepcopy(main_source["executionBindings"])
        shared_bindings["securityVisibilityPolicy"] = copy.deepcopy(
            security_source["executionBindings"]["securityVisibilityPolicy"]
        )
        main_source["executionBindings"] = copy.deepcopy(shared_bindings)

        self.main_fixture = self.main_backend.materialize_fixture(
            main_source,
            resolved_origins=self.origins,
        )
        self.main_harness = BrowserConformanceHarness(
            self.main_backend,
            self.main_fixture,
            self.main_backend.identity_verifier,
        )

        cookie_source = copy.deepcopy(main_source)
        persistent = next(
            item for item in cookie_source["baseline"]["cookies"] if item["persistent"]
        )
        persistent["expiry"]["nanoseconds"] = 123456000
        cookie_source["fixtureRevision"] = "browser-state-cookie-fidelity-v0.1"
        self.cookie_fixture = self.main_backend.materialize_fixture(
            cookie_source,
            resolved_origins=self.origins,
        )
        self.cookie_harness = BrowserConformanceHarness(
            self.main_backend,
            self.cookie_fixture,
            self.main_backend.identity_verifier,
        )

        self.security_backend = self.main_backend
        self.security_origins = {
            "subject": self.origins["primary"],
            "evaluatorPrivate": self.origins["secondary"],
        }
        security_source["executionBindings"] = copy.deepcopy(shared_bindings)
        self.security_fixture = self.security_backend.materialize_fixture(
            security_source,
            resolved_origins=self.security_origins,
        )
        self.security_harness = BrowserConformanceHarness(
            self.security_backend,
            self.security_fixture,
            self.security_backend.identity_verifier,
        )
        self.security_sut = self.security_harness.provision()
        self.security_evidence = PlaywrightBrowserSecurityEvidenceAdapter(
            subject_origin=self.security_origins["subject"],
            private_origin=self.security_origins["evaluatorPrivate"],
            private_cookie_domain="b.test",
            authorized_value=_PUBLIC_OBSERVATION,
        )

        self.executed_backend = self.main_backend
        executed_source = copy.deepcopy(main_source)
        self.executed_fixture = self.executed_backend.materialize_fixture(
            executed_source,
            resolved_origins=self.origins,
        )
        self.executed_harness = BrowserConformanceHarness(
            self.executed_backend,
            self.executed_fixture,
            self.executed_backend.identity_verifier,
        )
        self.executed_sut = self.executed_harness.provision()
        self.executed_behavior = BrowserExecutedCapabilityEvaluator()

    def tearDown(self) -> None:
        try:
            self.main_backend.close()
        finally:
            self.server.__exit__(None, None, None)

    def _set_main_temporal_eligibility(self, sut: BrowserSUT, eligible: bool) -> None:
        self.main_backend.fixture_control.set_restore_temporal_eligibility(
            sut,
            eligible=eligible,
        )

    def _seed_partitioned_control(self, sut: BrowserSUT) -> None:
        self.main_backend.fixture_control.seed_partitioned_cookie(
            sut,
            {
                "name": "partitioned_cookie_tck_probe",
                "value": "1",
                "domain": "a.test",
                "path": "/",
                "topLevelSite": "https://b.test",
            },
        )

    def _verify_security_private_state_authoritative(self, sut: BrowserSUT) -> None:
        projected = self.security_harness.authoritative_projection(sut, _settled())
        if projected.digest == self.security_fixture.baseline_image_digest:
            raise BrowserVerificationError(
                "evaluator-private selected Browser state was omitted from authoritative identity"
            )

    def _fault_harness(
        self,
        fault: str,
    ) -> tuple[BrowserConformanceHarness, ProjectionFaultObserver]:
        observer = ProjectionFaultObserver(self.executed_backend.observer, fault)
        backend = ObserverOverrideBackend(self.executed_backend, observer)
        return (
            BrowserConformanceHarness(
                backend,
                self.executed_fixture,
                self.executed_backend.identity_verifier,
            ),
            observer,
        )

    def _baseline_fault(self, fault: str) -> None:
        harness, _ = self._fault_harness(fault)
        sut = harness.provision()
        try:
            self.executed_behavior.require_baseline_projection(
                harness,
                sut,
                _settled(),
                expected_digest=self.executed_fixture.baseline_image_digest,
            )
        finally:
            sut.release()

    def _partitioned_admission_fault(self) -> None:
        harness, _ = self._fault_harness("admits-partitioned-state-as-unpartitioned")
        sut = harness.provision()
        try:
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
            self.executed_behavior.require_baseline_projection(
                harness,
                sut,
                _settled(),
                expected_digest=self.executed_fixture.baseline_image_digest,
            )
        finally:
            sut.release()

    def _provider_order_identity_fault(self) -> None:
        harness, observer = self._fault_harness("provider-enumeration-order")
        sut = harness.provision()
        original_snapshot = sut.snapshot
        try:
            raw_projection = observer.project_selected_state(sut, self.executed_fixture)
            raw_digest = _sha256_jcs(raw_projection)
            if raw_digest == self.executed_fixture.baseline_image_digest:
                raise BrowserVerificationError(
                    "provider-order control did not produce distinct raw identity bytes"
                )

            def raw_order_snapshot() -> SnapshotRef:
                actual = original_snapshot()
                return SnapshotRef(
                    snapshot_id=actual.snapshot_id,
                    handle_id=actual.handle_id,
                    state_digest=raw_digest,
                    logical_time=actual.logical_time,
                    consistency=actual.consistency,
                    adapter_name=actual.adapter_name,
                )

            sut.snapshot = raw_order_snapshot
            harness.verified_snapshot(sut, _settled())
        finally:
            sut.snapshot = original_snapshot
            sut.release()

    def _restore_without_reprojection_fault(self) -> None:
        harness = self.executed_harness
        sut = harness.provision()
        original_restore = sut.restore
        try:
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
            sut.restore = lambda ignored: None
            harness.verified_restore(sut, snapshot, _settled(), _settled())
        finally:
            sut.restore = original_restore
            sut.release()

    def _settlement_bypass_fault(self) -> None:
        sut = self.executed_harness.provision()
        try:
            ledger = BrowserSettlementLedger()
            ledger.accept_relevant_mutation("pending-browser-write")
            ledger.close_subject_admission()
            self.executed_harness.authoritative_projection(sut, ledger)
        finally:
            sut.release()

    def _private_state_leak_fault(self) -> None:
        sut = self.executed_harness.provision()
        private_value = "evaluator-private-browser-value"
        try:
            self.executed_harness.fixture_control.seed_local_storage(
                sut,
                self.origins["secondary"],
                (
                    {
                        "key": encode_dom_string_code_units(
                            tuple(map(ord, "private-key"))
                        ),
                        "value": encode_dom_string_code_units(
                            tuple(map(ord, private_value))
                        ),
                    },
                ),
            )
            page = sut._context.new_page()
            try:
                page.goto(self.origins["secondary"], wait_until="domcontentloaded")
                observed = str(page.evaluate("localStorage.getItem('private-key')"))
            finally:
                page.close()
            self.executed_behavior.require_subject_visibility(
                {"value": _PUBLIC_OBSERVATION, "leaked": observed},
                authorized_surface={"value": _PUBLIC_OBSERVATION},
                evaluator_private_values=(private_value,),
            )
        finally:
            sut.release()

    def _ignored_excluded_interference_fault(self) -> None:
        harness, _ = self._fault_harness("ignore-excluded-state-interference")
        sut = harness.provision()
        try:
            harness.fixture_control.set_excluded_state_interference(sut, interfering=True)
            self.executed_behavior.require_rejected(
                lambda: self.executed_behavior.require_baseline_projection(
                    harness,
                    sut,
                    _settled(),
                    expected_digest=self.executed_fixture.baseline_image_digest,
                ),
                obligation="detect observer that ignores excluded-state interference",
            )
        finally:
            sut.release()

    def _ignored_execution_drift_fault(self) -> None:
        harness, _ = self._fault_harness("ignore-required-execution-input-drift")
        sut = harness.provision()
        try:
            harness.fixture_control.set_execution_binding(
                sut,
                "storageIsolationPolicy",
                "drifted-storage-isolation-policy",
            )
            self.executed_behavior.require_rejected(
                lambda: self.executed_behavior.require_baseline_projection(
                    harness,
                    sut,
                    _settled(),
                    expected_digest=self.executed_fixture.baseline_image_digest,
                ),
                obligation="detect observer that ignores required execution drift",
            )
        finally:
            sut.release()

    def _executed_controls(self) -> BrowserExecutedNegativeControlSet:
        operations = {
            "loses-hostonly-cookie-identity": lambda: self._baseline_fault(
                "loses-hostonly-cookie-identity"
            ),
            "collapses-samesite-default": lambda: self._baseline_fault(
                "collapses-samesite-default"
            ),
            "admits-partitioned-state-as-unpartitioned": self._partitioned_admission_fault,
            "corrupts-domstring-code-units": lambda: self._baseline_fault(
                "corrupts-domstring-code-units"
            ),
            "uses-provider-enumeration-as-canonical-order": self._provider_order_identity_fault,
            "reports-restore-success-without-reprojection": self._restore_without_reprojection_fault,
            "bypasses-settlement-witness": self._settlement_bypass_fault,
            "leaks-evaluator-private-state": self._private_state_leak_fault,
            "ignores-excluded-state-interference": self._ignored_excluded_interference_fault,
            "ignores-required-execution-input-drift": self._ignored_execution_drift_fault,
        }
        return BrowserExecutedNegativeControlSet(
            operations=operations,
            candidate_metadata=BrowserExecutedMetadata.from_fixture(self.executed_fixture),
        )

    def _adapter(self) -> BrowserTCKAdapter:
        residual_plan = BrowserExecutionResidualPlan(
            binding_references={
                "browser-build-artifact": "browserBuild",
                "storage-partition-isolation-policy": "storageIsolationPolicy",
            },
            cookie_temporal_policy="fail-closed-restore-eligibility",
            excluded_state_dispositions={
                "service-worker-state": "fail-closed-insufficient",
                "cache-storage-state": "fail-closed-insufficient",
                "indexeddb-state": "fail-closed-insufficient",
                "extension-or-preload-state": "fail-closed-insufficient",
            },
        )
        return BrowserTCKAdapter(
            (
                BrowserIdentityTCKEvaluator(
                    backend=self.main_backend,
                    fixture=self.main_fixture,
                    verifier=self.main_backend.identity_verifier,
                    upstream_execution_bindings=self.main_fixture.manifest[
                        "executionBindings"
                    ],
                ),
                BrowserSelectionCanonicalTCKEvaluator(
                    fixture=self.main_fixture,
                    verifier=self.main_backend.identity_verifier,
                ),
                BrowserCookieTCKEvaluator(
                    harness=self.cookie_harness,
                    fixture=self.cookie_fixture,
                    verifier=self.main_backend.identity_verifier,
                    seed_partitioned_control=self._seed_partitioned_control,
                    set_temporal_eligibility=self._set_main_temporal_eligibility,
                ),
                BrowserStateImageTCKEvaluator(
                    verifier=self.main_backend.identity_verifier,
                    execution_bindings=self.main_fixture.manifest["executionBindings"],
                ),
                BrowserExecutionResidualTCKEvaluator(
                    harness=self.main_harness,
                    fixture=self.main_fixture,
                    expected_execution_bindings=self.main_fixture.manifest[
                        "executionBindings"
                    ],
                    plan=residual_plan,
                    set_temporal_eligibility=self._set_main_temporal_eligibility,
                ),
                BrowserSettlementLifecycleTCKEvaluator(
                    self.main_harness,
                    set_temporal_eligibility=self._set_main_temporal_eligibility,
                ),
                BrowserSecurityTCKEvaluator(
                    sut=self.security_sut,
                    evidence_control=self.security_evidence,
                    verify_private_state_authoritative=self._verify_security_private_state_authoritative,
                ),
                BrowserExecutedCapabilityTCKEvaluator(
                    harness=self.executed_harness,
                    sut=self.executed_sut,
                    fixture=self.executed_fixture,
                    negative_controls=self._executed_controls(),
                ),
            )
        )

    def test_complete_eight_case_profile_executes_through_composite_activation(self) -> None:
        browser_adapter = self._adapter()
        self.assertEqual(BROWSER_MANDATORY_CASE_IDS, browser_adapter.supported_case_ids)
        self.assertEqual(8, len(browser_adapter.supported_case_ids))

        default_case_ids = ReferenceConformanceAdapter().supported_case_ids
        composite = ReferenceConformanceAdapter(browser_adapter=browser_adapter)
        activated_case_ids = composite.supported_case_ids

        self.assertEqual(
            BROWSER_MANDATORY_CASE_IDS,
            activated_case_ids - default_case_ids,
            "real Browser activation must add exactly the mandatory eight cases",
        )
        self.assertEqual(
            default_case_ids,
            activated_case_ids - BROWSER_MANDATORY_CASE_IDS,
            "real Browser activation must preserve every non-Browser owner",
        )

        results = []
        for case_id in sorted(BROWSER_MANDATORY_CASE_IDS):
            result = composite.evaluate(_load_case(case_id))
            results.append(result)
            self.assertIs(TCKStatus.PASS, result.status, result.detail)

        self.assertEqual(BROWSER_MANDATORY_CASE_IDS, {item.case_id for item in results})


if __name__ == "__main__":
    unittest.main()

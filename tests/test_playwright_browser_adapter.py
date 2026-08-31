from __future__ import annotations

import copy
import json
import os
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator

from avp_ref.environment.models import RestoreEquivalence
from avp_ref.tck_adapter.browser_harness import (
    BrowserConformanceHarness,
    BrowserSettlementLedger,
    BrowserVerificationError,
    encode_dom_string_code_units,
)
from avp_ref.tck_adapter.playwright_browser import PlaywrightBrowserBackendHarness

ROOT = Path(__file__).resolve().parents[1]
_BROWSER = os.environ.get("AVP_PLAYWRIGHT_BROWSER")


class _FixtureHandler(BaseHTTPRequestHandler):
    server_version = "AVPPlaywrightBrowserFixture/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        payload = b"<!doctype html><meta charset=utf-8><title>AVP Browser Fixture</title>"
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


def _settled() -> BrowserSettlementLedger:
    ledger = BrowserSettlementLedger()
    ledger.close_subject_admission()
    return ledger


def _fixture_source() -> dict:
    path = ROOT / "conformance/fixtures/browser-state/v0.1/fixture-source.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _playwright_compatible_fixture_source() -> dict:
    """Use only provider-observable expiry precision for foundation lifecycle smoke.

    The shared portable fixture deliberately contains non-zero nanoseconds. Chromium's
    Playwright cookie transport is not assumed to preserve that precision. The provider
    must fail closed on the shared fixture; this derived source is intentionally limited
    to an exactly observable expiry and is not portable TCK authority.
    """

    source = copy.deepcopy(_fixture_source())
    for cookie in source["baseline"]["cookies"]:
        if cookie["persistent"]:
            cookie["expiry"]["nanoseconds"] = 0
    return source


@unittest.skipUnless(
    _BROWSER == "chromium",
    "AVP_PLAYWRIGHT_BROWSER=chromium is required for Playwright Browser integration",
)
class PlaywrightBrowserAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = _fixture_server()
        self.port = self.server.__enter__()
        self.backend = PlaywrightBrowserBackendHarness(engine="chromium")
        self.origins = {
            "primary": f"http://a.test:{self.port}",
            "secondary": f"http://b.test:{self.port}",
        }
        self.fixture = self.backend.materialize_fixture(
            _playwright_compatible_fixture_source(),
            resolved_origins=self.origins,
        )
        self.harness = BrowserConformanceHarness(
            self.backend,
            self.fixture,
            self.backend.identity_verifier,
        )

    def tearDown(self) -> None:
        try:
            self.backend.close()
        finally:
            self.server.__exit__(None, None, None)

    def test_shared_portable_fixture_fails_closed_when_expiry_precision_is_lossy(self) -> None:
        portable_fixture = self.backend.materialize_fixture(
            _fixture_source(),
            resolved_origins=self.origins,
        )
        with self.assertRaisesRegex(
            BrowserVerificationError,
            "expiry loses exact seconds/nanoseconds fidelity",
        ):
            self.backend.provision(portable_fixture)

    def test_materialized_fixture_binds_running_browser_identity(self) -> None:
        self.assertEqual(
            dict(self.backend.browser_build_binding),
            dict(self.fixture.manifest["executionBindings"]["browserBuild"]),
        )
        self.assertEqual(
            "version",
            self.fixture.manifest["executionBindings"]["browserBuild"]["identityType"],
        )

    def test_real_browser_baseline_projection_matches_compatible_canonical_identity(self) -> None:
        sut = self.harness.provision()
        observed = self.harness.authoritative_projection(sut, _settled())
        self.assertEqual(self.fixture.baseline_image_digest, observed.digest)

    def test_cookie_selection_is_independent_of_localstorage_selection(self) -> None:
        source = _playwright_compatible_fixture_source()
        source["selectedLocalStorageOriginSlots"] = ["secondary"]
        source["baseline"]["localStorageByOriginSlot"] = {
            "secondary": source["baseline"]["localStorageByOriginSlot"]["secondary"]
        }
        source["baseline"]["cookies"] = [
            cookie
            for cookie in source["baseline"]["cookies"]
            if not cookie["hostOnly"]
        ]
        fixture = self.backend.materialize_fixture(source, resolved_origins=self.origins)
        harness = BrowserConformanceHarness(
            self.backend,
            fixture,
            self.backend.identity_verifier,
        )
        sut = harness.provision()

        observed = harness.authoritative_projection(sut, _settled())

        self.assertEqual(fixture.baseline_image_digest, observed.digest)
        self.assertEqual(["a.test"], list(fixture.manifest["cookieDomains"]))
        self.assertEqual([self.origins["secondary"]], list(fixture.manifest["localStorageOrigins"]))

    def test_two_resources_do_not_share_selected_authoritative_state(self) -> None:
        first = self.harness.provision()
        second = self.harness.provision()
        baseline_second = self.harness.authoritative_projection(second, _settled())

        primary = self.fixture.manifest["localStorageOrigins"][0]
        self.harness.fixture_control.seed_local_storage(
            first,
            primary,
            (
                {
                    "key": encode_dom_string_code_units((0x0069, 0x0073, 0x006F)),
                    "value": encode_dom_string_code_units((0x0061,)),
                },
            ),
        )

        changed_first = self.harness.authoritative_projection(first, _settled())
        unchanged_second = self.harness.authoritative_projection(second, _settled())
        self.assertNotEqual(self.fixture.baseline_image_digest, changed_first.digest)
        self.assertEqual(baseline_second.digest, unchanged_second.digest)
        self.assertEqual(self.fixture.baseline_image_digest, unchanged_second.digest)

    def test_reset_preserves_excluded_cookie_state(self) -> None:
        sut = self.harness.provision()
        excluded = {
            "name": "excluded_cookie",
            "value": "keep-me",
            "url": self.origins["secondary"] + "/",
        }
        sut._context.add_cookies([excluded])  # concrete-provider acceptance probe

        self.harness.verified_reset(sut, _settled(), _settled())

        remaining = {
            (cookie["name"], cookie["value"], cookie["domain"])
            for cookie in sut._context.cookies()
        }
        self.assertTrue(
            any(name == "excluded_cookie" and value == "keep-me" for name, value, _ in remaining)
        )
        self.assertEqual(
            self.fixture.baseline_image_digest,
            self.harness.authoritative_projection(sut, _settled()).digest,
        )

    def test_snapshot_reset_restore_use_real_browser_state_and_independent_reprojection(self) -> None:
        sut = self.harness.provision()
        primary = self.fixture.manifest["localStorageOrigins"][0]
        self.harness.fixture_control.seed_local_storage(
            sut,
            primary,
            (
                {
                    "key": encode_dom_string_code_units((0x0073, 0x006E, 0x0061, 0x0070)),
                    "value": encode_dom_string_code_units((0x0032,)),
                },
            ),
        )
        snapshot = self.harness.verified_snapshot(sut, _settled())
        snapshot_digest = snapshot.state_digest

        reset = self.harness.verified_reset(sut, _settled(), _settled())
        self.assertTrue(reset.equivalent_to_initial)
        self.assertEqual(self.fixture.baseline_image_digest, reset.after_digest)

        restored = self.harness.verified_restore(
            sut,
            snapshot,
            _settled(),
            _settled(),
        )
        self.assertIs(restored.equivalence, RestoreEquivalence.STATE_EQUIVALENT)
        self.assertEqual(snapshot_digest, restored.after_digest)

    def test_execution_binding_and_temporal_controls_fail_closed(self) -> None:
        sut = self.harness.provision()
        snapshot = self.harness.verified_snapshot(sut, _settled())

        self.harness.fixture_control.set_execution_binding(
            sut,
            "browserBuild",
            "different-browser-build",
        )
        with self.assertRaisesRegex(Exception, "execution-input identity drift"):
            self.harness.authoritative_projection(sut, _settled())

        other = self.harness.provision()
        other_snapshot = self.harness.verified_snapshot(other, _settled())
        self.harness.fixture_control.set_restore_temporal_eligibility(
            other,
            eligible=False,
        )
        with self.assertRaisesRegex(Exception, "temporal restore eligibility"):
            self.harness.verified_restore(
                other,
                other_snapshot,
                _settled(),
                _settled(),
            )
        self.assertTrue(snapshot.snapshot_id)


if __name__ == "__main__":
    unittest.main()

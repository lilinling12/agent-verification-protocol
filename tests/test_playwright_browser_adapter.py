from __future__ import annotations

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


def _fixture_source():
    path = ROOT / "conformance/fixtures/browser-state/v0.1/fixture-source.json"
    return json.loads(path.read_text(encoding="utf-8"))


@unittest.skipUnless(
    _BROWSER == "chromium",
    "AVP_PLAYWRIGHT_BROWSER=chromium is required for Playwright Browser integration",
)
class PlaywrightBrowserAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = _fixture_server()
        self.port = self.server.__enter__()
        self.backend = PlaywrightBrowserBackendHarness(engine="chromium")
        origins = {
            "primary": f"http://a.test:{self.port}",
            "secondary": f"http://b.test:{self.port}",
        }
        self.fixture = self.backend.materialize_fixture(
            _fixture_source(),
            resolved_origins=origins,
        )
        self.harness = BrowserConformanceHarness(
            self.backend,
            self.fixture,
            self.backend.identity_verifier,
        )

    def tearDown(self) -> None:
        self.backend.close()
        self.server.__exit__(None, None, None)

    def test_materialized_fixture_binds_running_browser_identity(self) -> None:
        self.assertEqual(
            dict(self.backend.browser_build_binding),
            dict(self.fixture.manifest["executionBindings"]["browserBuild"]),
        )
        self.assertEqual("version", self.fixture.manifest["executionBindings"]["browserBuild"]["identityType"])

    def test_real_browser_baseline_projection_matches_shared_canonical_identity(self) -> None:
        sut = self.harness.provision()
        observed = self.harness.authoritative_projection(sut, _settled())
        self.assertEqual(self.fixture.baseline_image_digest, observed.digest)

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

        # Re-provision a clean resource so temporal eligibility is tested independently.
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

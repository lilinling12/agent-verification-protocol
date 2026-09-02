from __future__ import annotations

import json
import os
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator

from avp_ref.tck_adapter.browser_harness import (
    BrowserConformanceHarness,
    BrowserSettlementLedger,
    BrowserVerificationError,
)
from avp_ref.tck_adapter.playwright_browser import PlaywrightBrowserBackendHarness

ROOT = Path(__file__).resolve().parents[1]
_BROWSER = os.environ.get("AVP_PLAYWRIGHT_BROWSER")
_EXECUTION_FIXTURE = (
    ROOT / "conformance/fixtures/browser-state/v0.1/execution-fixture-source.json"
)


class _FixtureHandler(BaseHTTPRequestHandler):
    server_version = "AVPPlaywrightPartitionFixture/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        payload = b"<!doctype html><meta charset=utf-8><title>AVP Partition Fixture</title>"
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
    return json.loads(_EXECUTION_FIXTURE.read_text(encoding="utf-8"))


@unittest.skipUnless(
    _BROWSER == "chromium",
    "AVP_PLAYWRIGHT_BROWSER=chromium is required for partitioned-cookie integration",
)
class PlaywrightBrowserPartitionedCookieTest(unittest.TestCase):
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

    def _seed_partitioned(self, sut, *, name: str = "partitioned_probe") -> None:
        self.harness.fixture_control.seed_partitioned_cookie(
            sut,
            {
                "name": name,
                "value": "partitioned-value",
                "domain": "a.test",
                "path": "/",
                "topLevelSite": "https://b.test",
            },
        )

    @staticmethod
    def _partitioned_named(sut, name: str):
        return [
            cookie
            for cookie in sut._context.cookies()  # concrete-provider evidence only
            if cookie.get("name") == name and cookie.get("partitionKey")
        ]

    def test_control_shape_is_closed(self) -> None:
        sut = self.harness.provision()
        with self.assertRaisesRegex(BrowserVerificationError, "shape must be exactly"):
            self.harness.fixture_control.seed_partitioned_cookie(
                sut,
                {
                    "name": "partitioned_probe",
                    "value": "1",
                    "domain": "a.test",
                    "path": "/",
                    "topLevelSite": "https://b.test",
                    "providerOption": "forbidden",
                },
            )

    def test_partitioned_cookie_is_observed_but_not_admitted(self) -> None:
        sut = self.harness.provision()
        before = self.harness.authoritative_projection(sut, _settled())

        self._seed_partitioned(sut)

        raw = self._partitioned_named(sut, "partitioned_probe")
        self.assertEqual(1, len(raw))
        self.assertTrue(raw[0]["partitionKey"])

        projected = self.backend.observer.project_selected_state(sut, self.fixture)
        self.assertNotIn(
            "partitioned_probe",
            {cookie["name"] for cookie in projected["cookies"]},
        )
        after = self.harness.authoritative_projection(sut, _settled())
        self.assertEqual(before.digest, after.digest)
        self.assertEqual(self.fixture.baseline_image_digest, after.digest)

    def test_reset_preserves_partitioned_excluded_state(self) -> None:
        sut = self.harness.provision()
        self._seed_partitioned(sut)

        reset = self.harness.verified_reset(sut, _settled(), _settled())

        self.assertTrue(reset.equivalent_to_initial)
        self.assertEqual(1, len(self._partitioned_named(sut, "partitioned_probe")))
        self.assertEqual(
            self.fixture.baseline_image_digest,
            self.harness.authoritative_projection(sut, _settled()).digest,
        )

    def test_reset_preserves_partitioned_cookie_when_visible_tuple_collides(self) -> None:
        sut = self.harness.provision()
        self._seed_partitioned(sut, name="domain_scoped")

        colliding = self._partitioned_named(sut, "domain_scoped")
        self.assertEqual(1, len(colliding))

        reset = self.harness.verified_reset(sut, _settled(), _settled())

        self.assertTrue(reset.equivalent_to_initial)
        self.assertEqual(1, len(self._partitioned_named(sut, "domain_scoped")))
        self.assertEqual(
            self.fixture.baseline_image_digest,
            self.harness.authoritative_projection(sut, _settled()).digest,
        )


if __name__ == "__main__":
    unittest.main()

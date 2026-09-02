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
from avp_ref.tck_adapter.playwright_browser import (
    PlaywrightBrowserBackendHarness,
    PlaywrightBrowserExcludedStateControl,
)

ROOT = Path(__file__).resolve().parents[1]
_BROWSER = os.environ.get("AVP_PLAYWRIGHT_BROWSER")
_FIXTURE = (
    ROOT
    / "conformance/fixtures/browser-state/v0.1/"
    "excluded-state-execution-fixture-source.json"
)
_CACHE_NAME = "avp-excluded-state-v1"
_NETWORK_BODY = "network-origin"
_INTERFERING_BODY = "service-worker-cache"


class _FixtureHandler(BaseHTTPRequestHandler):
    server_version = "AVPPlaywrightExcludedStateFixture/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        path = self.path.split("?", 1)[0]
        if path == "/sw.js":
            payload = f"""
self.addEventListener('install', event => {{
  event.waitUntil(
    caches.open('{_CACHE_NAME}')
      .then(cache => cache.put(
        '/controlled-resource',
        new Response('{_INTERFERING_BODY}', {{headers: {{'Content-Type': 'text/plain'}}}})
      ))
      .then(() => self.skipWaiting())
  );
}});
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', event => {{
  const url = new URL(event.request.url);
  if (url.pathname === '/controlled-resource') {{
    event.respondWith(
      caches.match('/controlled-resource').then(response => response || fetch(event.request))
    );
  }}
}});
""".encode("utf-8")
            self._send(payload, content_type="text/javascript; charset=utf-8")
            return
        if path == "/controlled-resource":
            self._send(_NETWORK_BODY.encode("utf-8"))
            return
        self._send(
            b"<!doctype html><meta charset=utf-8><title>AVP Excluded State Fixture</title>",
            content_type="text/html; charset=utf-8",
        )

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, body: bytes, *, content_type: str = "text/plain; charset=utf-8") -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
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


def _fixture_source() -> dict[str, object]:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


@unittest.skipUnless(
    _BROWSER == "chromium",
    "AVP_PLAYWRIGHT_BROWSER=chromium is required for excluded-state integration",
)
class PlaywrightBrowserExcludedStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = _fixture_server()
        self.port = self.server.__enter__()
        self.origin = f"http://localhost:{self.port}"
        self.backend = PlaywrightBrowserBackendHarness(engine="chromium")
        self.fixture = self.backend.materialize_fixture(
            _fixture_source(),
            resolved_origins={"primary": self.origin},
        )
        self.harness = BrowserConformanceHarness(
            self.backend,
            self.fixture,
            self.backend.identity_verifier,
        )
        self.control = PlaywrightBrowserExcludedStateControl()

    def tearDown(self) -> None:
        try:
            self.backend.close()
        finally:
            self.server.__exit__(None, None, None)

    def test_material_interference_fails_closed_with_selected_digest_unchanged(self) -> None:
        sut = self.harness.provision()
        baseline = self.harness.authoritative_projection(sut, _settled())

        evidence = self.control.prove_service_worker_cache_interference(
            sut,
            origin=self.origin,
            service_worker_path="/sw.js",
            controlled_resource_path="/controlled-resource",
            expected_cache_name=_CACHE_NAME,
            expected_network_body=_NETWORK_BODY,
            expected_interfering_body=_INTERFERING_BODY,
        )

        self.assertEqual(baseline.digest, evidence.selected_digest_before)
        self.assertEqual(evidence.selected_digest_before, evidence.selected_digest_after)
        self.assertEqual(_NETWORK_BODY, evidence.baseline.response_body)
        self.assertEqual(_INTERFERING_BODY, evidence.residual.response_body)
        self.assertEqual(0, evidence.baseline.registration_count)
        self.assertGreaterEqual(evidence.residual.registration_count, 1)
        self.assertIn(_CACHE_NAME, evidence.residual.cache_names)
        self.assertTrue(evidence.residual.client_controlled)

        with self.assertRaisesRegex(
            BrowserVerificationError,
            "material excluded Browser state interferes",
        ):
            self.harness.authoritative_projection(sut, _settled())

    def test_excluded_state_isolation_is_resource_local(self) -> None:
        contaminated = self.harness.provision()
        clean = self.harness.provision()
        clean_before = self.harness.authoritative_projection(clean, _settled())

        self.control.prove_service_worker_cache_interference(
            contaminated,
            origin=self.origin,
            service_worker_path="/sw.js",
            controlled_resource_path="/controlled-resource",
            expected_cache_name=_CACHE_NAME,
            expected_network_body=_NETWORK_BODY,
            expected_interfering_body=_INTERFERING_BODY,
        )

        clean_observation = self.control.observe_service_worker_cache(
            clean,
            origin=self.origin,
            controlled_resource_path="/controlled-resource",
        )
        clean_after = self.harness.authoritative_projection(clean, _settled())

        self.assertEqual(clean_before.digest, clean_after.digest)
        self.assertEqual(0, clean_observation.registration_count)
        self.assertEqual((), clean_observation.cache_names)
        self.assertFalse(clean_observation.client_controlled)
        self.assertEqual(_NETWORK_BODY, clean_observation.response_body)

    def test_proof_rejects_unselected_origin(self) -> None:
        sut = self.harness.provision()
        with self.assertRaisesRegex(
            BrowserVerificationError,
            "outside Manifest localStorage selection",
        ):
            self.control.prove_service_worker_cache_interference(
                sut,
                origin=f"http://127.0.0.1:{self.port}",
                service_worker_path="/sw.js",
                controlled_resource_path="/controlled-resource",
                expected_cache_name=_CACHE_NAME,
                expected_network_body=_NETWORK_BODY,
                expected_interfering_body=_INTERFERING_BODY,
            )


if __name__ == "__main__":
    unittest.main()

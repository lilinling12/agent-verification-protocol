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
    PlaywrightBrowserIndexedDBControl,
)

ROOT = Path(__file__).resolve().parents[1]
_BROWSER = os.environ.get("AVP_PLAYWRIGHT_BROWSER")
_FIXTURE = (
    ROOT
    / "conformance/fixtures/browser-state/v0.1/"
    "excluded-state-execution-fixture-source.json"
)
_DB_NAME = "avp-indexeddb-interference-v1"
_STORE_NAME = "state"
_KEY = "mode"
_VALUE = "residual"
_CLEAN_BEHAVIOR = "network-mode"
_RESIDUAL_BEHAVIOR = "indexeddb-mode"


class _FixtureHandler(BaseHTTPRequestHandler):
    server_version = "AVPPlaywrightIndexedDBFixture/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        payload = b"<!doctype html><meta charset=utf-8><title>AVP IndexedDB Fixture</title>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except BrokenPipeError:
            return

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


def _fixture_source() -> dict[str, object]:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


@unittest.skipUnless(
    _BROWSER == "chromium",
    "AVP_PLAYWRIGHT_BROWSER=chromium is required for IndexedDB integration",
)
class PlaywrightBrowserIndexedDBTest(unittest.TestCase):
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
        self.control = PlaywrightBrowserIndexedDBControl()

    def tearDown(self) -> None:
        try:
            self.backend.close()
        finally:
            self.server.__exit__(None, None, None)

    def test_observation_does_not_create_missing_database(self) -> None:
        sut = self.harness.provision()

        first = self.control.observe(
            sut,
            origin=self.origin,
            database_name=_DB_NAME,
            store_name=_STORE_NAME,
            key=_KEY,
            clean_behavior=_CLEAN_BEHAVIOR,
            residual_behavior=_RESIDUAL_BEHAVIOR,
        )
        second = self.control.observe(
            sut,
            origin=self.origin,
            database_name=_DB_NAME,
            store_name=_STORE_NAME,
            key=_KEY,
            clean_behavior=_CLEAN_BEHAVIOR,
            residual_behavior=_RESIDUAL_BEHAVIOR,
        )

        self.assertFalse(first.database_exists)
        self.assertIsNone(first.stored_value)
        self.assertEqual(_CLEAN_BEHAVIOR, first.behavior_result)
        self.assertEqual(first, second)

    def test_material_interference_fails_closed_with_selected_digest_unchanged(self) -> None:
        sut = self.harness.provision()
        baseline = self.harness.authoritative_projection(sut, _settled())

        evidence = self.control.prove_interference(
            sut,
            origin=self.origin,
            database_name=_DB_NAME,
            store_name=_STORE_NAME,
            key=_KEY,
            stored_value=_VALUE,
            clean_behavior=_CLEAN_BEHAVIOR,
            residual_behavior=_RESIDUAL_BEHAVIOR,
        )

        self.assertEqual(baseline.digest, evidence.selected_digest_before)
        self.assertEqual(evidence.selected_digest_before, evidence.selected_digest_after)
        self.assertFalse(evidence.baseline.database_exists)
        self.assertIsNone(evidence.baseline.stored_value)
        self.assertEqual(_CLEAN_BEHAVIOR, evidence.baseline.behavior_result)
        self.assertTrue(evidence.residual.database_exists)
        self.assertEqual(_VALUE, evidence.residual.stored_value)
        self.assertEqual(_RESIDUAL_BEHAVIOR, evidence.residual.behavior_result)

        with self.assertRaisesRegex(
            BrowserVerificationError,
            "material excluded Browser state interferes",
        ):
            self.harness.authoritative_projection(sut, _settled())

    def test_indexeddb_residue_is_resource_local(self) -> None:
        contaminated = self.harness.provision()
        clean = self.harness.provision()
        clean_before = self.harness.authoritative_projection(clean, _settled())

        self.control.prove_interference(
            contaminated,
            origin=self.origin,
            database_name=_DB_NAME,
            store_name=_STORE_NAME,
            key=_KEY,
            stored_value=_VALUE,
            clean_behavior=_CLEAN_BEHAVIOR,
            residual_behavior=_RESIDUAL_BEHAVIOR,
        )

        clean_observation = self.control.observe(
            clean,
            origin=self.origin,
            database_name=_DB_NAME,
            store_name=_STORE_NAME,
            key=_KEY,
            clean_behavior=_CLEAN_BEHAVIOR,
            residual_behavior=_RESIDUAL_BEHAVIOR,
        )
        clean_after = self.harness.authoritative_projection(clean, _settled())

        self.assertEqual(clean_before.digest, clean_after.digest)
        self.assertFalse(clean_observation.database_exists)
        self.assertIsNone(clean_observation.stored_value)
        self.assertEqual(_CLEAN_BEHAVIOR, clean_observation.behavior_result)

    def test_proof_rejects_unselected_origin(self) -> None:
        sut = self.harness.provision()
        with self.assertRaisesRegex(
            BrowserVerificationError,
            "outside Manifest localStorage selection",
        ):
            self.control.prove_interference(
                sut,
                origin=f"http://127.0.0.1:{self.port}",
                database_name=_DB_NAME,
                store_name=_STORE_NAME,
                key=_KEY,
                stored_value=_VALUE,
                clean_behavior=_CLEAN_BEHAVIOR,
                residual_behavior=_RESIDUAL_BEHAVIOR,
            )


if __name__ == "__main__":
    unittest.main()

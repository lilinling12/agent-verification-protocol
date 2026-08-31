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
    BrowserSettlementError,
    BrowserSettlementLedger,
    BrowserVerificationError,
    encode_dom_string_code_units,
)
from avp_ref.tck_adapter.playwright_browser import (
    PlaywrightBrowserBackendHarness,
    PlaywrightBrowserMutationControl,
)

ROOT = Path(__file__).resolve().parents[1]
_BROWSER = os.environ.get("AVP_PLAYWRIGHT_BROWSER")
_EXECUTION_FIXTURE = (
    ROOT / "conformance/fixtures/browser-state/v0.1/execution-fixture-source.json"
)


class _FixtureHandler(BaseHTTPRequestHandler):
    server_version = "AVPPlaywrightSettlementFixture/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        payload = b"<!doctype html><meta charset=utf-8><title>AVP Settlement Fixture</title>"
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


def _fixture_source() -> dict:
    return json.loads(_EXECUTION_FIXTURE.read_text(encoding="utf-8"))


@unittest.skipUnless(
    _BROWSER == "chromium",
    "AVP_PLAYWRIGHT_BROWSER=chromium is required for settlement integration",
)
class PlaywrightBrowserSettlementTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = _fixture_server()
        self.port = self.server.__enter__()
        self.backend = PlaywrightBrowserBackendHarness(engine="chromium")
        self.fixture = self.backend.materialize_fixture(
            _fixture_source(),
            resolved_origins={
                "primary": f"http://a.test:{self.port}",
                "secondary": f"http://b.test:{self.port}",
            },
        )
        self.harness = BrowserConformanceHarness(
            self.backend,
            self.fixture,
            self.backend.identity_verifier,
        )
        self.mutations = PlaywrightBrowserMutationControl()

    def tearDown(self) -> None:
        try:
            self.mutations.close()
            self.backend.close()
        finally:
            self.server.__exit__(None, None, None)

    def test_network_idle_and_provider_terminal_cannot_self_certify_settlement(self) -> None:
        sut = self.harness.provision()
        mutation_id = "selected-localstorage-mutation"
        ledger = BrowserSettlementLedger()
        ledger.accept_relevant_mutation(mutation_id)

        self.mutations.start_delayed_local_storage_mutation(
            sut,
            mutation_id=mutation_id,
            origin=self.fixture.manifest["localStorageOrigins"][0],
            entry={
                "key": encode_dom_string_code_units(
                    (0x0073, 0x0065, 0x0074, 0x0074, 0x006C, 0x0065)
                ),
                "value": encode_dom_string_code_units(
                    (0x0074, 0x0065, 0x0072, 0x006D, 0x0069, 0x006E, 0x0061, 0x006C)
                ),
            },
            delay_ms=1500,
        )
        ledger.close_subject_admission()

        self.assertTrue(
            self.mutations.observe_network_idle_before_terminal(sut, mutation_id)
        )
        self.assertFalse(self.mutations.is_terminal(sut, mutation_id))
        with self.assertRaises(BrowserSettlementError):
            self.harness.authoritative_projection(sut, ledger)

        with self.assertRaises(BrowserSettlementError):
            ledger.accept_relevant_mutation("mutation-after-admission-close")

        self.mutations.wait_for_terminal(sut, mutation_id)
        self.assertTrue(self.mutations.is_terminal(sut, mutation_id))

        # A provider-observed terminal predicate is necessary evidence, but it does
        # not mutate the provider-neutral ledger and therefore cannot self-certify.
        with self.assertRaises(BrowserSettlementError):
            self.harness.authoritative_projection(sut, ledger)

        ledger.mark_terminal(mutation_id)
        accepted = self.harness.authoritative_projection(sut, ledger)
        self.assertNotEqual(self.fixture.baseline_image_digest, accepted.digest)

        projected = self.backend.observer.project_selected_state(sut, self.fixture)
        primary = next(
            origin_state
            for origin_state in projected["origins"]
            if origin_state["origin"] == self.fixture.manifest["localStorageOrigins"][0]
        )
        values = {
            entry["key"]: entry["value"] for entry in primary["localStorage"]
        }
        self.assertEqual(
            encode_dom_string_code_units(
                (0x0074, 0x0065, 0x0072, 0x006D, 0x0069, 0x006E, 0x0061, 0x006C)
            ),
            values[
                encode_dom_string_code_units(
                    (0x0073, 0x0065, 0x0074, 0x0074, 0x006C, 0x0065)
                )
            ],
        )

    def test_mutation_control_rejects_invalid_scope_and_delay(self) -> None:
        sut = self.harness.provision()
        entry = {
            "key": encode_dom_string_code_units((0x006B,)),
            "value": encode_dom_string_code_units((0x0076,)),
        }

        with self.assertRaisesRegex(BrowserVerificationError, "outside Manifest selection"):
            self.mutations.start_delayed_local_storage_mutation(
                sut,
                mutation_id="outside-origin",
                origin=f"http://sub.a.test:{self.port}",
                entry=entry,
                delay_ms=100,
            )

        with self.assertRaisesRegex(BrowserVerificationError, "delay_ms"):
            self.mutations.start_delayed_local_storage_mutation(
                sut,
                mutation_id="bad-delay",
                origin=self.fixture.manifest["localStorageOrigins"][0],
                entry=entry,
                delay_ms=0,
            )

    def test_mutation_control_is_resource_owned(self) -> None:
        first = self.harness.provision()
        second = self.harness.provision()
        mutation_id = "resource-owned-mutation"
        self.mutations.start_delayed_local_storage_mutation(
            first,
            mutation_id=mutation_id,
            origin=self.fixture.manifest["localStorageOrigins"][0],
            entry={
                "key": encode_dom_string_code_units((0x006B,)),
                "value": encode_dom_string_code_units((0x0076,)),
            },
            delay_ms=100,
        )

        with self.assertRaisesRegex(Exception, "unknown Browser mutation id"):
            self.mutations.is_terminal(second, mutation_id)

        self.mutations.wait_for_terminal(first, mutation_id)
        self.mutations.release_mutation(first, mutation_id)


if __name__ == "__main__":
    unittest.main()

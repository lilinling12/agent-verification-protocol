from __future__ import annotations

import json
import os
import threading
import unittest
from contextlib import contextmanager
from dataclasses import fields
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator

from avp_ref.tck_adapter.browser_harness import (
    BrowserConformanceHarness,
    BrowserSettlementLedger,
    BrowserVerificationError,
    encode_dom_string_code_units,
)
from avp_ref.tck_adapter.playwright_browser import (
    BrowserArtifactAuthorization,
    BrowserSubjectObservation,
    PlaywrightBrowserBackendHarness,
    PlaywrightBrowserSecurityControl,
)

ROOT = Path(__file__).resolve().parents[1]
_BROWSER = os.environ.get("AVP_PLAYWRIGHT_BROWSER")
_FIXTURE = ROOT / "conformance/fixtures/browser-state/v0.1/security-execution-fixture-source.json"
_PUBLIC_OBSERVATION = "public-observation"
_PRIVATE_COOKIE_NAME = "synthetic-secret-cookie"
_PRIVATE_COOKIE_VALUE = "private-cookie-value"
_PRIVATE_STORAGE_KEY = "synthetic-secret-key"
_PRIVATE_STORAGE_VALUE = "synthetic-secret-value"


class _SecurityFixtureHandler(BaseHTTPRequestHandler):
    server_version = "AVPPlaywrightBrowserSecurityFixture/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        path = self.path.split("?", 1)[0]
        if path == "/subject-observation":
            payload = _PUBLIC_OBSERVATION.encode("utf-8")
            content_type = "text/plain; charset=utf-8"
        else:
            payload = b"<!doctype html><meta charset=utf-8><title>AVP Browser Security</title>"
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
    server = ThreadingHTTPServer(("127.0.0.1", 0), _SecurityFixtureHandler)
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
    "AVP_PLAYWRIGHT_BROWSER=chromium is required for Browser security integration",
)
class PlaywrightBrowserSecurityVisibilityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = _fixture_server()
        self.port = self.server.__enter__()
        self.backend = PlaywrightBrowserBackendHarness(engine="chromium")
        self.origins = {
            "subject": f"http://a.test:{self.port}",
            "evaluatorPrivate": f"http://b.test:{self.port}",
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
        self.security = PlaywrightBrowserSecurityControl()

    def tearDown(self) -> None:
        try:
            self.backend.close()
        finally:
            self.server.__exit__(None, None, None)

    def _provision_private_state(self):
        sut = self.harness.provision()
        private_origin = self.origins["evaluatorPrivate"]
        self.security.seed_evaluator_private_state(
            sut,
            origin=private_origin,
            cookie={
                "name": _PRIVATE_COOKIE_NAME,
                "value": _PRIVATE_COOKIE_VALUE,
                "domain": "b.test",
                "hostOnly": True,
                "path": "/",
                "persistent": False,
                "secure": False,
                "httpOnly": False,
                "sameSite": "Lax",
            },
            local_storage=(
                {
                    "key": encode_dom_string_code_units(tuple(map(ord, _PRIVATE_STORAGE_KEY))),
                    "value": encode_dom_string_code_units(tuple(map(ord, _PRIVATE_STORAGE_VALUE))),
                },
            ),
        )
        return sut

    def test_real_private_state_exists_but_subject_receives_only_authorized_value(self) -> None:
        sut = self._provision_private_state()
        cookie_value, storage_value = self.security.observe_evaluator_private_state(
            sut,
            origin=self.origins["evaluatorPrivate"],
            cookie_name=_PRIVATE_COOKIE_NAME,
            local_storage_key=_PRIVATE_STORAGE_KEY,
        )
        self.assertEqual(_PRIVATE_COOKIE_VALUE, cookie_value)
        self.assertEqual(_PRIVATE_STORAGE_VALUE, storage_value)

        subject = self.security.observe_subject_surface(
            sut,
            subject_origin=self.origins["subject"],
            path="/subject-observation",
            expected_authorized_value=_PUBLIC_OBSERVATION,
        )

        self.assertEqual(BrowserSubjectObservation(value=_PUBLIC_OBSERVATION), subject)
        self.assertEqual(["value"], [field.name for field in fields(subject)])
        self.assertFalse(hasattr(subject, "__dict__"))
        rendered = repr(subject)
        self.assertNotIn(_PRIVATE_COOKIE_VALUE, rendered)
        self.assertNotIn(_PRIVATE_STORAGE_VALUE, rendered)

        # Private authoritative state remains part of the evaluator projection;
        # secrecy is a visibility boundary, not omission from state identity.
        projected = self.harness.authoritative_projection(sut, _settled())
        self.assertNotEqual(self.fixture.baseline_image_digest, projected.digest)

    def test_subject_surface_exposes_no_privileged_browser_or_lifecycle_handle(self) -> None:
        sut = self._provision_private_state()
        subject = self.security.observe_subject_surface(
            sut,
            subject_origin=self.origins["subject"],
            path="/subject-observation",
            expected_authorized_value=_PUBLIC_OBSERVATION,
        )

        forbidden = {
            "page",
            "context",
            "browser",
            "resource",
            "handle_id",
            "snapshot",
            "restore",
            "reset",
            "release",
            "evaluate",
            "goto",
            "fixture_control",
        }
        for name in forbidden:
            with self.subTest(name=name):
                self.assertFalse(hasattr(subject, name))

    def test_private_state_on_evaluator_origin_is_not_visible_at_subject_origin(self) -> None:
        sut = self._provision_private_state()
        page = sut._context.new_page()  # evaluator-only implementation evidence probe
        try:
            page.goto(self.origins["subject"] + "/state", wait_until="domcontentloaded")
            visible_cookie = str(page.evaluate("document.cookie"))
            visible_storage = page.evaluate(
                """() => Object.fromEntries(
                  Array.from({length: localStorage.length}, (_, index) => localStorage.key(index))
                    .map(key => [key, localStorage.getItem(key)])
                )"""
            )
        finally:
            page.close()

        self.assertNotIn(_PRIVATE_COOKIE_NAME, visible_cookie)
        self.assertNotIn(_PRIVATE_COOKIE_VALUE, visible_cookie)
        self.assertNotIn(_PRIVATE_STORAGE_KEY, visible_storage)
        self.assertNotIn(_PRIVATE_STORAGE_VALUE, tuple(visible_storage.values()))

    def test_subject_observation_refuses_unselected_origin(self) -> None:
        sut = self._provision_private_state()
        with self.assertRaisesRegex(
            BrowserVerificationError,
            "outside Manifest localStorage selection",
        ):
            self.security.observe_subject_surface(
                sut,
                subject_origin=f"http://sub.a.test:{self.port}",
                path="/subject-observation",
                expected_authorized_value=_PUBLIC_OBSERVATION,
            )


class BrowserArtifactAuthoritySeparationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.security = PlaywrightBrowserSecurityControl()

    def test_artifact_digest_is_identity_not_retrieval_authorization(self) -> None:
        retained = self.security.retain_evaluator_artifact(b"evaluator-private-browser-state")
        self.assertTrue(retained.locator.digest.startswith("sha256:"))
        self.assertEqual(
            b"evaluator-private-browser-state",
            self.security.retrieve_evaluator_artifact(
                retained.locator,
                retained.authorization,
            ),
        )

        with self.assertRaisesRegex(
            BrowserVerificationError,
            "digest identity is not retrieval authorization",
        ):
            self.security.retrieve_evaluator_artifact(
                retained.locator,
                retained.locator.digest,  # type: ignore[arg-type]
            )

        other = self.security.retain_evaluator_artifact(b"different-private-artifact")
        with self.assertRaisesRegex(BrowserVerificationError, "authorization is invalid"):
            self.security.retrieve_evaluator_artifact(
                retained.locator,
                other.authorization,
            )

    def test_redacted_bytes_receive_distinct_artifact_identity(self) -> None:
        unredacted, redacted = self.security.retain_redacted_artifact(
            b"public-prefix:secret-value",
            redacted_content=b"public-prefix:[REDACTED]",
        )
        self.assertNotEqual(unredacted.locator.digest, redacted.locator.digest)
        self.assertEqual(
            b"public-prefix:[REDACTED]",
            self.security.retrieve_evaluator_artifact(
                redacted.locator,
                redacted.authorization,
            ),
        )
        self.assertIsInstance(redacted.authorization, BrowserArtifactAuthorization)


if __name__ == "__main__":
    unittest.main()

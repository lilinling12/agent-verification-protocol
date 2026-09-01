from __future__ import annotations

import copy
import json
import os
import threading
import unittest
from contextlib import contextmanager
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator, Mapping

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
_SERIALIZATION_FIXTURE = (
    ROOT / "conformance/fixtures/browser-state/v0.1/fixture-source.json"
)
_EXECUTION_FIXTURE = (
    ROOT / "conformance/fixtures/browser-state/v0.1/execution-fixture-source.json"
)


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


def _load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _serialization_fixture_source() -> dict[str, Any]:
    return _load_fixture(_SERIALIZATION_FIXTURE)


def _execution_fixture_source() -> dict[str, Any]:
    return _load_fixture(_EXECUTION_FIXTURE)


def _persistent_cookie(source: Mapping[str, Any]) -> dict[str, Any]:
    cookies = source["baseline"]["cookies"]
    matches = [cookie for cookie in cookies if cookie["persistent"]]
    if len(matches) != 1:
        raise AssertionError("fixture must contain exactly one persistent baseline cookie")
    return matches[0]


def _with_persistent_expiry_nanoseconds(
    source: Mapping[str, Any], nanoseconds: int
) -> dict[str, Any]:
    mutated = copy.deepcopy(source)
    _persistent_cookie(mutated)["expiry"]["nanoseconds"] = nanoseconds
    return mutated


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
            _execution_fixture_source(),
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

    def _materialize(self, source: Mapping[str, Any]):
        return self.backend.materialize_fixture(
            source,
            resolved_origins=self.origins,
        )

    def test_serialization_fixture_keeps_arbitrary_nanosecond_vector(self) -> None:
        source = _serialization_fixture_source()
        expiry = _persistent_cookie(source)["expiry"]
        self.assertEqual("1800000000", expiry["unixSeconds"])
        self.assertEqual(123456789, expiry["nanoseconds"])

    def test_execution_fixture_uses_explicit_browser_representable_expiry(self) -> None:
        source = _execution_fixture_source()
        expiry = _persistent_cookie(source)["expiry"]
        self.assertEqual("1800000000", expiry["unixSeconds"])
        self.assertEqual(0, expiry["nanoseconds"])
        self.assertNotEqual(
            source["fixtureRevision"],
            _serialization_fixture_source()["fixtureRevision"],
        )

    def test_nonrepresentable_nanosecond_seed_fails_closed(self) -> None:
        portable_fixture = self._materialize(_serialization_fixture_source())
        with self.assertRaisesRegex(
            BrowserVerificationError,
            "expiry loses exact seconds/nanoseconds fidelity",
        ):
            self.backend.provision(portable_fixture)

    def test_whole_second_expiry_round_trips_exactly(self) -> None:
        sut = self.harness.provision()
        observed = self.harness.authoritative_projection(sut, _settled())
        self.assertEqual(self.fixture.baseline_image_digest, observed.digest)

    def test_nonzero_microsecond_expiry_round_trips_exactly(self) -> None:
        source = _with_persistent_expiry_nanoseconds(
            _execution_fixture_source(),
            123456000,
        )
        fixture = self._materialize(source)
        harness = BrowserConformanceHarness(
            self.backend,
            fixture,
            self.backend.identity_verifier,
        )
        sut = harness.provision()

        observed = harness.authoritative_projection(sut, _settled())

        self.assertEqual(fixture.baseline_image_digest, observed.digest)
        persistent = [cookie for cookie in fixture.baseline_image["cookies"] if cookie["persistent"]]
        self.assertEqual(123456000, persistent[0]["expiry"]["nanoseconds"])

    def test_integer_truncation_of_actual_expiry_is_rejected(self) -> None:
        source = _with_persistent_expiry_nanoseconds(
            _execution_fixture_source(),
            123456000,
        )
        fixture = self._materialize(source)
        harness = BrowserConformanceHarness(
            self.backend,
            fixture,
            self.backend.identity_verifier,
        )
        sut = harness.provision()
        record = next(item for item in sut._provenance.values() if item.persistent)

        sut._context.add_cookies(
            [
                {
                    "name": record.name,
                    "value": record.value,
                    "domain": "." + record.domain,
                    "path": record.path,
                    "secure": record.secure,
                    "httpOnly": record.http_only,
                    "sameSite": record.same_site,
                    "expires": int(record.expiry_seconds),
                }
            ]
        )

        with self.assertRaisesRegex(
            BrowserVerificationError,
            "expiry loses exact seconds/nanoseconds fidelity",
        ):
            harness.authoritative_projection(sut, _settled())

    def test_provenance_cannot_manufacture_fractional_expiry(self) -> None:
        sut = self.harness.provision()
        identity, record = next(
            (identity, item)
            for identity, item in sut._provenance.items()
            if item.persistent
        )
        sut._provenance[identity] = replace(record, expiry_nanoseconds=123456000)

        with self.assertRaisesRegex(
            BrowserVerificationError,
            "expiry loses exact seconds/nanoseconds fidelity",
        ):
            self.harness.authoritative_projection(sut, _settled())

    def test_session_and_persistent_cookie_state_remain_distinct(self) -> None:
        sut = self.harness.provision()
        image = self.backend.observer.project_selected_state(sut, self.fixture)
        cookies = {cookie["name"]: cookie for cookie in image["cookies"]}

        session = cookies["host_only"]
        persistent = cookies["domain_scoped"]
        self.assertFalse(session["persistent"])
        self.assertNotIn("expiry", session)
        self.assertTrue(persistent["persistent"])
        self.assertEqual(
            {"unixSeconds": "1800000000", "nanoseconds": 0},
            persistent["expiry"],
        )

    def test_materialized_fixture_binds_running_browser_identity(self) -> None:
        self.assertEqual(
            dict(self.backend.browser_build_binding),
            dict(self.fixture.manifest["executionBindings"]["browserBuild"]),
        )
        self.assertEqual(
            "version",
            self.fixture.manifest["executionBindings"]["browserBuild"]["identityType"],
        )

    def test_cookie_selection_is_independent_of_localstorage_selection(self) -> None:
        source = _execution_fixture_source()
        source["selectedLocalStorageOriginSlots"] = ["secondary"]
        source["baseline"]["localStorageByOriginSlot"] = {
            "secondary": source["baseline"]["localStorageByOriginSlot"]["secondary"]
        }
        source["baseline"]["cookies"] = [
            cookie
            for cookie in source["baseline"]["cookies"]
            if not cookie["hostOnly"]
        ]
        fixture = self._materialize(source)
        harness = BrowserConformanceHarness(
            self.backend,
            fixture,
            self.backend.identity_verifier,
        )
        sut = harness.provision()

        observed = harness.authoritative_projection(sut, _settled())

        self.assertEqual(fixture.baseline_image_digest, observed.digest)
        self.assertEqual(["a.test"], list(fixture.manifest["cookieDomains"]))
        self.assertEqual(
            [self.origins["secondary"]],
            list(fixture.manifest["localStorageOrigins"]),
        )

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
            any(
                name == "excluded_cookie" and value == "keep-me"
                for name, value, _ in remaining
            )
        )
        self.assertEqual(
            self.fixture.baseline_image_digest,
            self.harness.authoritative_projection(sut, _settled()).digest,
        )

    def test_snapshot_reset_restore_use_real_browser_state_and_independent_reprojection(
        self,
    ) -> None:
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

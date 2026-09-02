"""Execute non-normative Browser acceptance evidence across engine families.

This module is deliberately test-only. Playwright is transport, not protocol
authority; expected behavior is expressed through browser-observable HTTP/Web
Storage effects and AEP-0011 decisions. If the transport cannot expose an
AVP-required field, the result records that insufficiency instead of inferring a
portable value from vendor serialization.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import platform
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any, Iterator

_FIXTURE_REVISION = "browser-acceptance-evidence-v0.1"
_TEST_HOST = "a.test"
_SUBDOMAIN_HOST = "sub.a.test"
_SECOND_HOST = "b.test"


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    status: str
    details: dict[str, Any]


@dataclass(frozen=True, slots=True)
class EngineResult:
    engine_family: str
    browser_version: str
    cases: tuple[CaseResult, ...]


class _FixtureHandler(BaseHTTPRequestHandler):
    server_version = "AVPBrowserEvidence/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        path = self.path.split("?", 1)[0]
        if path == "/set-host-only":
            self._send_text(
                "host-only seeded",
                extra_headers=(
                    ("Set-Cookie", "host_only=1; Path=/; SameSite=Lax"),
                ),
            )
            return
        if path == "/set-domain":
            self._send_text(
                "domain seeded",
                extra_headers=(
                    ("Set-Cookie", "domain_scoped=1; Domain=a.test; Path=/; SameSite=Lax"),
                ),
            )
            return
        if path == "/echo-cookies":
            self._send_text(self.headers.get("Cookie", ""))
            return
        self._send_text(
            "<!doctype html><meta charset=utf-8><title>AVP Browser Evidence</title>",
            content_type="text/html; charset=utf-8",
        )

    def log_message(self, format: str, *args: object) -> None:
        # Fixture traffic is intentionally quiet; evidence is retained in JSON.
        return

    def _send_text(
        self,
        body: str,
        *,
        content_type: str = "text/plain; charset=utf-8",
        extra_headers: tuple[tuple[str, str], ...] = (),
    ) -> None:
        payload = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        for name, value in extra_headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)


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


def encode_domstring_code_units(code_units: list[int]) -> str:
    """Encode exact unsigned UTF-16 code units per the Proposed AEP decision."""

    if any(unit < 0 or unit > 0xFFFF for unit in code_units):
        raise ValueError("DOMString code units must be unsigned 16-bit integers")
    raw = bytearray()
    for unit in code_units:
        raw.extend(((unit >> 8) & 0xFF, unit & 0xFF))
    return base64.urlsafe_b64encode(bytes(raw)).rstrip(b"=").decode("ascii")


def decode_domstring_code_units(encoded: str) -> list[int]:
    """Decode the evidence representation without Unicode repair/normalization."""

    padding = "=" * ((4 - len(encoded) % 4) % 4)
    raw = base64.urlsafe_b64decode((encoded + padding).encode("ascii"))
    if len(raw) % 2:
        raise ValueError("encoded DOMString evidence must decode to whole UTF-16 code units")
    return [(raw[index] << 8) | raw[index + 1] for index in range(0, len(raw), 2)]


def _url(host: str, port: int, path: str = "/") -> str:
    return f"http://{host}:{port}{path}"


def _case_bae_001(browser: Any, port: int) -> CaseResult:
    context = browser.new_context()
    try:
        page = context.new_page()
        page.goto(_url(_TEST_HOST, port, "/set-host-only"))
        page.goto(_url(_TEST_HOST, port, "/set-domain"))
        page.goto(_url(_SUBDOMAIN_HOST, port, "/echo-cookies"))
        echoed = page.text_content("body") or ""

        if "host_only=1" in echoed:
            raise AssertionError("host-only cookie leaked to subdomain")
        if "domain_scoped=1" not in echoed:
            raise AssertionError("domain-scoped cookie was not sent to matching subdomain")

        cookies = context.cookies([_url(_TEST_HOST, port), _url(_SUBDOMAIN_HOST, port)])
        host_only_field_exposed = any("hostOnly" in cookie for cookie in cookies)
        return CaseResult(
            case_id="BAE-001",
            status="partial" if not host_only_field_exposed else "pass",
            details={
                "behavioral_distinction_proven": True,
                "transport_exposes_hostOnly": host_only_field_exposed,
                "projection_disposition": (
                    "transport field available; AVP projection still requires independent review"
                    if host_only_field_exposed
                    else "fail-closed required for a projector relying only on this cookie serialization"
                ),
                "cookie_object_keys": sorted({key for cookie in cookies for key in cookie}),
            },
        )
    finally:
        context.close()


def _case_bae_005(browser: Any, port: int) -> CaseResult:
    context = browser.new_context()
    try:
        page = context.new_page()
        page.goto(_url(_TEST_HOST, port, "/one?query=1#fragment"))
        page.evaluate("localStorage.clear(); localStorage.setItem('scope', 'origin-a')")

        page.goto(_url(_TEST_HOST, port, "/two?query=2#other"))
        same_origin = page.evaluate("localStorage.getItem('scope')")
        if same_origin != "origin-a":
            raise AssertionError("path/query/fragment changed localStorage origin identity")

        page.goto(_url(_SECOND_HOST, port))
        second_before = page.evaluate("localStorage.getItem('scope')")
        if second_before is not None:
            raise AssertionError("localStorage leaked across tuple origins")
        page.evaluate("localStorage.setItem('scope', 'origin-b')")

        page.goto(_url(_TEST_HOST, port))
        first_after = page.evaluate("localStorage.getItem('scope')")
        if first_after != "origin-a":
            raise AssertionError("first origin localStorage changed after second-origin mutation")

        return CaseResult(
            case_id="BAE-005",
            status="pass",
            details={
                "tuple_origin_separation": True,
                "path_query_fragment_non_identity": True,
                "first_origin_value": first_after,
                "second_origin_initial_value": second_before,
            },
        )
    finally:
        context.close()


def _case_bae_007(browser: Any, port: int) -> CaseResult:
    samples = {
        "empty": [],
        "nul": [0x0000],
        "ascii": [0x0041, 0x0056, 0x0050],
        "bmp": [0x4E2D, 0x6587],
        "surrogate-pair": [0xD83D, 0xDE80],
        "lone-high": [0xD800],
        "lone-low": [0xDC00],
        "composed": [0x00E9],
        "decomposed": [0x0065, 0x0301],
    }

    context = browser.new_context()
    try:
        page = context.new_page()
        page.goto(_url(_TEST_HOST, port))
        observed: dict[str, dict[str, Any]] = {}
        for label, code_units in samples.items():
            result = page.evaluate(
                """
                ([keyUnits, valueUnits]) => {
                  localStorage.clear();
                  const key = String.fromCharCode(...keyUnits);
                  const value = String.fromCharCode(...valueUnits);
                  localStorage.setItem(key, value);
                  const storedKey = localStorage.key(0);
                  const storedValue = localStorage.getItem(storedKey);
                  const units = text => Array.from(
                    {length: text.length},
                    (_, index) => text.charCodeAt(index)
                  );
                  return {key: units(storedKey), value: units(storedValue)};
                }
                """,
                [code_units, code_units],
            )
            key_units = [int(unit) for unit in result["key"]]
            value_units = [int(unit) for unit in result["value"]]
            if key_units != code_units or value_units != code_units:
                raise AssertionError(f"DOMString code units changed for sample {label}")

            encoded = encode_domstring_code_units(code_units)
            decoded = decode_domstring_code_units(encoded)
            if decoded != code_units:
                raise AssertionError(f"AVP evidence encoding failed round trip for {label}")
            observed[label] = {"code_units": code_units, "encoded": encoded}

        return CaseResult(
            case_id="BAE-007",
            status="pass",
            details={
                "lossless_code_unit_round_trip": True,
                "samples": observed,
            },
        )
    finally:
        context.close()


def _run_engine(browser_type: Any, port: int) -> EngineResult:
    browser = browser_type.launch(headless=True)
    try:
        cases: list[CaseResult] = []
        for case in (_case_bae_001, _case_bae_005, _case_bae_007):
            try:
                cases.append(case(browser, port))
            except Exception as exc:  # evidence must retain the exact failed case
                cases.append(
                    CaseResult(
                        case_id=case.__name__.replace("_case_bae_", "BAE-").replace("_", "-"),
                        status="fail",
                        details={"error_type": type(exc).__name__, "error": str(exc)},
                    )
                )
        return EngineResult(
            engine_family=browser_type.name,
            browser_version=browser.version,
            cases=tuple(cases),
        )
    finally:
        browser.close()


def run(output: Path) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # dedicated evidence dependency, never base dependency
        raise RuntimeError(
            "Playwright is required only for Browser acceptance evidence; "
            "install the dedicated evidence dependency before running this module"
        ) from exc

    with _fixture_server() as port, sync_playwright() as playwright:
        engines = tuple(
            _run_engine(browser_type, port)
            for browser_type in (playwright.chromium, playwright.firefox, playwright.webkit)
        )

    document = {
        "schema": "avp-browser-acceptance-evidence-v0.1",
        "fixtureRevision": _FIXTURE_REVISION,
        "repositorySha": os.environ.get("GITHUB_SHA"),
        "transport": {
            "name": "playwright-python",
            "version": package_version("playwright"),
            "authority": "test-transport-only",
        },
        "execution": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "headless": True,
            "hosts": [_TEST_HOST, _SUBDOMAIN_HOST, _SECOND_HOST],
        },
        "engines": [asdict(engine) for engine in engines],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")

    failures = [
        (engine.engine_family, case.case_id)
        for engine in engines
        for case in engine.cases
        if case.status == "fail"
    ]
    if failures:
        print(json.dumps({"failures": failures}, indent=2))
        return 1

    partials = [
        (engine.engine_family, case.case_id)
        for engine in engines
        for case in engine.cases
        if case.status == "partial"
    ]
    print(
        json.dumps(
            {
                "output": str(output),
                "engines": [engine.engine_family for engine in engines],
                "partials": partials,
            },
            indent=2,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("browser-evidence/browser-evidence.json"),
    )
    args = parser.parse_args()
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())

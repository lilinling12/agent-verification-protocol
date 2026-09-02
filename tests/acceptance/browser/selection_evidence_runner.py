"""Execute non-normative evidence for Browser v0.1 cookie selection semantics.

This runner tests only the exact stored-domain complete-set rule from AEP-0011.
It deliberately does not claim that Playwright provides a lossless AVP cookie
projection: hostOnly and SameSite Default remain independently gated evidence.
"""

from __future__ import annotations

import argparse
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

_FIXTURE_REVISION = "browser-cookie-selection-evidence-v0.1"
_SELECTED_HOST = "a.test"
_OUTSIDE_HOST = "b.test"


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
    server_version = "AVPBrowserSelectionEvidence/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        host = self.headers.get("Host", "").split(":", 1)[0].lower()
        path = self.path.split("?", 1)[0]
        if host == _SELECTED_HOST and path == "/seed":
            self._send(
                b"selected cookies seeded",
                headers=(
                    ("Set-Cookie", "fixed=one; Path=/; SameSite=Lax"),
                    ("Set-Cookie", "dynamic_7f3a=two; Path=/; SameSite=Lax"),
                    ("Set-Cookie", "deep=three; Path=/deep; SameSite=Lax"),
                    (
                        "Set-Cookie",
                        "domain_dynamic=four; Domain=a.test; Path=/; SameSite=Lax",
                    ),
                ),
            )
            return
        if host == _OUTSIDE_HOST and path == "/seed":
            self._send(
                b"outside cookie seeded",
                headers=(("Set-Cookie", "outside=five; Path=/; SameSite=Lax"),),
            )
            return
        self._send(b"fixture")

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(
        self,
        body: bytes,
        *,
        headers: tuple[tuple[str, str], ...] = (),
    ) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)


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


def _url(host: str, port: int, path: str = "/") -> str:
    return f"http://{host}:{port}{path}"


def _canonical_fixture_domain(serialized_domain: str) -> str:
    """Canonicalize only the controlled ASCII `.test` fixture domain syntax.

    The AEP owns general host/domain canonicalization. This test helper handles
    only the known fixture's optional presentation leading dot so a provider's
    display choice does not become selection semantics.
    """

    return serialized_domain.removeprefix(".").lower()


def _selected_cookie_projection(
    serialized_cookies: list[dict[str, Any]], selected_domains: frozenset[str]
) -> list[dict[str, Any]]:
    selected = [
        cookie
        for cookie in serialized_cookies
        if _canonical_fixture_domain(str(cookie["domain"])) in selected_domains
    ]
    return sorted(
        selected,
        key=lambda cookie: (
            str(cookie["name"]),
            _canonical_fixture_domain(str(cookie["domain"])),
            str(cookie["path"]),
        ),
    )


def _identity_view(cookie: dict[str, Any]) -> tuple[str, str, str]:
    """Return only fields needed to test selection completeness in this slice."""

    return (
        str(cookie["name"]),
        _canonical_fixture_domain(str(cookie["domain"])),
        str(cookie["path"]),
    )


def _case_bae_004(browser: Any, port: int) -> CaseResult:
    context = browser.new_context()
    try:
        page = context.new_page()
        page.goto(_url(_SELECTED_HOST, port, "/seed"))
        page.goto(_url(_OUTSIDE_HOST, port, "/seed"))

        serialized = context.cookies(
            [
                _url(_SELECTED_HOST, port),
                _url(_SELECTED_HOST, port, "/deep/page"),
                _url(_OUTSIDE_HOST, port),
            ]
        )
        selected_domains = frozenset({_SELECTED_HOST})
        selected = _selected_cookie_projection(serialized, selected_domains)
        identities = [_identity_view(cookie) for cookie in selected]

        expected = {
            ("fixed", _SELECTED_HOST, "/"),
            ("dynamic_7f3a", _SELECTED_HOST, "/"),
            ("deep", _SELECTED_HOST, "/deep"),
            ("domain_dynamic", _SELECTED_HOST, "/"),
        }
        if set(identities) != expected:
            raise AssertionError(
                f"exact-domain complete-set selection mismatch: {identities!r}"
            )
        if any(identity[0] == "outside" for identity in identities):
            raise AssertionError("cookie from non-selected exact domain entered projection")

        # Dynamic names prove selection is domain-complete rather than a cookie
        # name allowlist. An additional in-scope cookie must change the complete
        # selected set even though its name did not exist in the authored fixture.
        await_name = "runtime_91c2"
        page.goto(_url(_SELECTED_HOST, port))
        page.evaluate(
            "name => { document.cookie = `${name}=late; Path=/; SameSite=Lax`; }",
            await_name,
        )
        after = _selected_cookie_projection(
            context.cookies(
                [_url(_SELECTED_HOST, port), _url(_SELECTED_HOST, port, "/deep/page")]
            ),
            selected_domains,
        )
        after_identities = [_identity_view(cookie) for cookie in after]
        if (await_name, _SELECTED_HOST, "/") not in after_identities:
            raise AssertionError("new in-scope dynamic cookie was silently omitted")
        if set(after_identities) == set(identities):
            raise AssertionError("extra in-scope state did not change complete selected set")

        return CaseResult(
            case_id="BAE-004",
            status="pass",
            details={
                "selection_rule": "exact canonical stored-domain complete set",
                "selected_domains": sorted(selected_domains),
                "baseline_selected_identities": [list(item) for item in identities],
                "post_mutation_selected_identities": [list(item) for item in after_identities],
                "dynamic_cookie_name_captured": True,
                "outside_exact_domain_excluded": True,
                "extra_in_scope_state_changes_projection": True,
                "hostOnly_projection_claimed": False,
                "sameSite_default_projection_claimed": False,
            },
        )
    finally:
        context.close()


def _run_engine(browser_type: Any, port: int) -> EngineResult:
    browser = browser_type.launch(headless=True)
    try:
        try:
            result = _case_bae_004(browser, port)
        except Exception as exc:
            result = CaseResult(
                case_id="BAE-004",
                status="fail",
                details={"error_type": type(exc).__name__, "error": str(exc)},
            )
        return EngineResult(
            engine_family=browser_type.name,
            browser_version=browser.version,
            cases=(result,),
        )
    finally:
        browser.close()


def run(output: Path) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is required only for Browser acceptance evidence; install the dedicated evidence transport before running this module"
        ) from exc

    with _fixture_server() as port, sync_playwright() as playwright:
        engines = tuple(
            _run_engine(browser_type, port)
            for browser_type in (playwright.chromium, playwright.firefox, playwright.webkit)
        )

    document = {
        "schema": "avp-browser-cookie-selection-evidence-v0.1",
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
            "hosts": [_SELECTED_HOST, _OUTSIDE_HOST],
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
    print(json.dumps({"failures": failures}, indent=2))
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("browser-evidence/browser-cookie-selection-evidence.json"),
    )
    args = parser.parse_args()
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())

"""Execute non-normative Browser snapshot/restore/reset acceptance evidence.

This runner exercises the lifecycle shape required by BAE-008 and BAE-009
without pretending that the current Playwright transport provides a lossless
BrowserStateImage cookie projector.  Restore/reset control uses ordinary HTTP
Set-Cookie semantics and same-origin Web Storage operations; success is judged
only by a separate behavioral reprojection path after a positive test-only
settlement witness.

The result is intentionally PARTIAL while BPR-003/BPR-004 prevent a complete
cookie-state fidelity claim.  Nothing in this module is packaged runtime or
portable TCK authority.
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

_FIXTURE_REVISION = "browser-recovery-evidence-v0.1"
_SELECTED_HOST = "a.test"
_SUBDOMAIN_HOST = "sub.a.test"
_CROSS_SITE_HOST = "b.test"
_COOKIE_NAME = "avp_lifecycle"
_EXTRA_COOKIE_NAME = "avp_runtime_extra"
_BASELINE_COOKIE_VALUE = "baseline"
_MUTATED_COOKIE_VALUE = "mutated"
_BASELINE_STORAGE = {"alpha": "1", "beta": "2"}
_MUTATED_STORAGE = {"alpha": "mutated", "runtime": "extra"}


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


class _MutationLedger:
    """Test-only positive settlement witness for one controlled recovery phase.

    The ledger is deliberately local to this evidence runner.  It is not a
    candidate Browser runtime abstraction: it only proves that projection starts
    after admission closes and after every accepted selected-state mutation has
    reached a known terminal outcome.
    """

    def __init__(self) -> None:
        self._admission_open = True
        self._states: dict[str, str] = {}

    def accept(self, mutation_id: str) -> None:
        if not self._admission_open:
            raise RuntimeError("selected-state mutation admission is closed")
        if mutation_id in self._states:
            raise RuntimeError(f"duplicate mutation id: {mutation_id}")
        self._states[mutation_id] = "accepted"

    def terminal(self, mutation_id: str) -> None:
        if self._states.get(mutation_id) != "accepted":
            raise RuntimeError(f"mutation is not unresolved accepted work: {mutation_id}")
        self._states[mutation_id] = "terminal"

    def close_admission(self) -> None:
        self._admission_open = False

    def assert_settled(self) -> None:
        if self._admission_open:
            raise RuntimeError("projection attempted before mutation admission closed")
        unresolved = sorted(
            mutation_id
            for mutation_id, state in self._states.items()
            if state == "accepted"
        )
        if unresolved:
            raise RuntimeError(f"projection attempted with unresolved mutations: {unresolved}")


class _FixtureHandler(BaseHTTPRequestHandler):
    server_version = "AVPBrowserRecoveryEvidence/0.1"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        host = self.headers.get("Host", "").split(":", 1)[0].lower()
        path = self.path.split("?", 1)[0]

        if host == _SELECTED_HOST and path == "/control/baseline-cookie":
            self._send(
                b"baseline cookie seeded",
                headers=(("Set-Cookie", self._cookie(_COOKIE_NAME, _BASELINE_COOKIE_VALUE)),),
            )
            return
        if host == _SELECTED_HOST and path == "/control/mutated-cookie":
            self._send(
                b"mutated cookie seeded",
                headers=(("Set-Cookie", self._cookie(_COOKIE_NAME, _MUTATED_COOKIE_VALUE)),),
            )
            return
        if host == _SELECTED_HOST and path == "/control/extra-cookie":
            self._send(
                b"extra cookie seeded",
                headers=(("Set-Cookie", self._cookie(_EXTRA_COOKIE_NAME, "extra")),),
            )
            return
        if host == _SELECTED_HOST and path == "/control/clear-extra-cookie":
            self._send(
                b"extra cookie cleared",
                headers=(("Set-Cookie", self._expired_cookie(_EXTRA_COOKIE_NAME)),),
            )
            return
        if path == "/probe/cookies":
            self._send(self.headers.get("Cookie", "").encode("utf-8"))
            return
        if host == _CROSS_SITE_HOST and path == "/probe/cross-site-get":
            port = self.server.server_address[1]
            html = (
                "<!doctype html><meta charset=utf-8>"
                f"<script>location.href='http://{_SELECTED_HOST}:{port}/probe/cookies'</script>"
            ).encode("utf-8")
            self._send(html, content_type="text/html; charset=utf-8")
            return
        if host == _CROSS_SITE_HOST and path == "/probe/cross-site-post":
            port = self.server.server_address[1]
            html = f"""<!doctype html>
<meta charset=utf-8>
<form id=post method=post action=http://{_SELECTED_HOST}:{port}/probe/post-cookies></form>
<script>document.getElementById('post').submit()</script>
""".encode("utf-8")
            self._send(html, content_type="text/html; charset=utf-8")
            return

        self._send(
            b"<!doctype html><meta charset=utf-8><title>AVP Browser Recovery Evidence</title>",
            content_type="text/html; charset=utf-8",
        )

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        path = self.path.split("?", 1)[0]
        if path == "/probe/post-cookies":
            self._send(self.headers.get("Cookie", "").encode("utf-8"))
            return
        self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        return

    @staticmethod
    def _cookie(name: str, value: str) -> str:
        # No Domain => host-only. No Expires/Max-Age => session semantics.
        # Explicit Lax avoids creation-time-sensitive SameSite Default behavior.
        return f"{name}={value}; Path=/; SameSite=Lax"

    @staticmethod
    def _expired_cookie(name: str) -> str:
        return f"{name}=; Path=/; SameSite=Lax; Max-Age=0"

    def _send(
        self,
        body: bytes,
        *,
        content_type: str = "text/plain; charset=utf-8",
        headers: tuple[tuple[str, str], ...] = (),
    ) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
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


def _cookie_map(header: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for field in header.split(";"):
        field = field.strip()
        if not field:
            continue
        name, separator, value = field.partition("=")
        if not separator:
            raise AssertionError(f"malformed controlled Cookie header: {field!r}")
        result[name] = value
    return result


def _storage_map(page: Any) -> dict[str, str]:
    return page.evaluate(
        """() => Object.fromEntries(
          Array.from({length: localStorage.length}, (_, index) => localStorage.key(index))
            .sort()
            .map(key => [key, localStorage.getItem(key)])
        )"""
    )


def _set_storage(page: Any, values: dict[str, str]) -> None:
    page.evaluate(
        """values => {
          localStorage.clear();
          for (const [key, value] of Object.entries(values)) localStorage.setItem(key, value);
        }""",
        values,
    )


def _apply_baseline(context: Any, port: int, ledger: _MutationLedger) -> None:
    page = context.new_page()
    try:
        ledger.accept("baseline-cookie")
        page.goto(_url(_SELECTED_HOST, port, "/control/baseline-cookie"))
        ledger.terminal("baseline-cookie")

        ledger.accept("clear-extra-cookie")
        page.goto(_url(_SELECTED_HOST, port, "/control/clear-extra-cookie"))
        ledger.terminal("clear-extra-cookie")

        ledger.accept("baseline-localstorage")
        page.goto(_url(_SELECTED_HOST, port, "/state"))
        _set_storage(page, _BASELINE_STORAGE)
        ledger.terminal("baseline-localstorage")
    finally:
        page.close()


def _apply_mutation(context: Any, port: int, ledger: _MutationLedger) -> None:
    page = context.new_page()
    try:
        ledger.accept("mutated-cookie")
        page.goto(_url(_SELECTED_HOST, port, "/control/mutated-cookie"))
        ledger.terminal("mutated-cookie")

        ledger.accept("extra-cookie")
        page.goto(_url(_SELECTED_HOST, port, "/control/extra-cookie"))
        ledger.terminal("extra-cookie")

        ledger.accept("mutated-localstorage")
        page.goto(_url(_SELECTED_HOST, port, "/state"))
        _set_storage(page, _MUTATED_STORAGE)
        ledger.terminal("mutated-localstorage")
    finally:
        page.close()


def _project_selected_behavior(context: Any, port: int, ledger: _MutationLedger) -> dict[str, Any]:
    """Independently observe the controlled selected surface after settlement.

    The projection deliberately avoids Playwright ``storageState`` and cookie
    export objects.  HTTP transmission, subdomain behavior, document.cookie,
    cross-site navigation behavior, and direct Web Storage reads are separate
    observations from the control path that performed restore/reset.

    The observations still cannot prove every required canonical cookie field
    (notably persistence metadata) for a general AVP projector, so lifecycle
    evidence remains PARTIAL rather than manufacturing a fidelity claim.
    """

    ledger.close_admission()
    ledger.assert_settled()

    page = context.new_page()
    try:
        root = page.goto(_url(_SELECTED_HOST, port, "/probe/cookies"))
        if root is None:
            raise AssertionError("cookie root probe produced no response")
        root_cookies = _cookie_map(root.text())

        child = page.goto(_url(_SUBDOMAIN_HOST, port, "/probe/cookies"))
        if child is None:
            raise AssertionError("cookie subdomain probe produced no response")
        child_cookies = _cookie_map(child.text())

        page.goto(_url(_SELECTED_HOST, port, "/state"))
        storage = _storage_map(page)
        document_cookie = _cookie_map(str(page.evaluate("document.cookie")))

        page.goto(_url(_CROSS_SITE_HOST, port, "/probe/cross-site-get"))
        page.wait_for_url(_url(_SELECTED_HOST, port, "/probe/cookies"))
        cross_site_get = _cookie_map(page.text_content("body") or "")

        page.goto(_url(_CROSS_SITE_HOST, port, "/probe/cross-site-post"))
        page.wait_for_url(_url(_SELECTED_HOST, port, "/probe/post-cookies"))
        cross_site_post = _cookie_map(page.text_content("body") or "")

        selected_names = {_COOKIE_NAME, _EXTRA_COOKIE_NAME}
        return {
            "cookieBehavior": {
                "rootSelected": {
                    name: root_cookies[name]
                    for name in sorted(selected_names & root_cookies.keys())
                },
                "subdomainSelected": {
                    name: child_cookies[name]
                    for name in sorted(selected_names & child_cookies.keys())
                },
                "documentCookieSelected": {
                    name: document_cookie[name]
                    for name in sorted(selected_names & document_cookie.keys())
                },
                "crossSiteGetSelected": {
                    name: cross_site_get[name]
                    for name in sorted(selected_names & cross_site_get.keys())
                },
                "crossSitePostSelected": {
                    name: cross_site_post[name]
                    for name in sorted(selected_names & cross_site_post.keys())
                },
            },
            "localStorage": storage,
        }
    finally:
        page.close()


def _require_baseline_projection(document: dict[str, Any]) -> None:
    cookies = document["cookieBehavior"]
    expected_cookie = {_COOKIE_NAME: _BASELINE_COOKIE_VALUE}
    if cookies["rootSelected"] != expected_cookie:
        raise AssertionError(f"baseline root cookie mismatch: {cookies['rootSelected']!r}")
    if cookies["subdomainSelected"]:
        raise AssertionError("host-only baseline cookie leaked to subdomain")
    if cookies["documentCookieSelected"] != expected_cookie:
        raise AssertionError("non-HttpOnly baseline cookie was not independently observable")
    if cookies["crossSiteGetSelected"] != expected_cookie:
        raise AssertionError("explicit Lax baseline cookie missing from cross-site top-level GET")
    if cookies["crossSitePostSelected"]:
        raise AssertionError("explicit Lax baseline cookie sent on cross-site unsafe POST")
    if document["localStorage"] != _BASELINE_STORAGE:
        raise AssertionError(f"baseline localStorage mismatch: {document['localStorage']!r}")


def _case_bae_008(browser: Any, port: int) -> CaseResult:
    context = browser.new_context()
    try:
        baseline_ledger = _MutationLedger()
        _apply_baseline(context, port, baseline_ledger)
        snapshot = _project_selected_behavior(context, port, baseline_ledger)
        _require_baseline_projection(snapshot)

        mutation_ledger = _MutationLedger()
        _apply_mutation(context, port, mutation_ledger)
        mutated = _project_selected_behavior(context, port, mutation_ledger)
        if mutated == snapshot:
            raise AssertionError("selected-state mutation did not change independent projection")

        restore_ledger = _MutationLedger()
        _apply_baseline(context, port, restore_ledger)
        restored = _project_selected_behavior(context, port, restore_ledger)
        _require_baseline_projection(restored)
        if restored != snapshot:
            raise AssertionError("restore reprojection did not reproduce snapshot observation")

        return CaseResult(
            case_id="BAE-008",
            status="partial",
            details={
                "snapshot_established_after_positive_settlement": True,
                "mutation_changed_selected_projection": True,
                "restore_control_completed": True,
                "independent_reprojection_matches_snapshot": True,
                "required_absence_restored": _EXTRA_COOKIE_NAME
                not in restored["cookieBehavior"]["rootSelected"],
                "temporal_fixture": "explicit SameSite=Lax session cookie; Default SameSite not used",
                "provider_storage_state_used_as_oracle": False,
                "candidate_success_fidelity": "STATE_EQUIVALENT",
                "fidelity_claimed": False,
                "closure": (
                    "lifecycle/reprojection shape proven, but complete lossless cookie-state "
                    "projection remains blocked by BPR-003/BPR-004; no full fidelity claim"
                ),
            },
        )
    finally:
        context.close()


def _case_bae_009(browser: Any, port: int) -> CaseResult:
    context = browser.new_context()
    try:
        baseline_ledger = _MutationLedger()
        _apply_baseline(context, port, baseline_ledger)
        immutable_baseline = _project_selected_behavior(context, port, baseline_ledger)
        _require_baseline_projection(immutable_baseline)

        mutation_ledger = _MutationLedger()
        _apply_mutation(context, port, mutation_ledger)
        mutated = _project_selected_behavior(context, port, mutation_ledger)
        if mutated == immutable_baseline:
            raise AssertionError("reset fixture mutation did not change selected projection")

        reset_ledger = _MutationLedger()
        _apply_baseline(context, port, reset_ledger)
        reset = _project_selected_behavior(context, port, reset_ledger)
        _require_baseline_projection(reset)
        if reset != immutable_baseline:
            raise AssertionError("reset reprojection did not reproduce immutable baseline")

        return CaseResult(
            case_id="BAE-009",
            status="partial",
            details={
                "immutable_baseline_projected": True,
                "mutation_changed_selected_projection": True,
                "reset_control_completed": True,
                "independent_reprojection_matches_baseline": True,
                "required_absence_restored": _EXTRA_COOKIE_NAME
                not in reset["cookieBehavior"]["rootSelected"],
                "provider_storage_state_used_as_oracle": False,
                "candidate_success_fidelity": "STATE_EQUIVALENT",
                "fidelity_claimed": False,
                "closure": (
                    "reset/reprojection shape proven, but complete lossless cookie-state "
                    "projection remains blocked by BPR-003/BPR-004; no full fidelity claim"
                ),
            },
        )
    finally:
        context.close()


def _run_engine(browser_type: Any, port: int) -> EngineResult:
    browser = browser_type.launch(headless=True)
    try:
        cases: list[CaseResult] = []
        for case in (_case_bae_008, _case_bae_009):
            try:
                cases.append(case(browser, port))
            except Exception as exc:
                cases.append(
                    CaseResult(
                        case_id="BAE-008" if case is _case_bae_008 else "BAE-009",
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
        "schema": "avp-browser-recovery-evidence-v0.1",
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
            "selectedHost": _SELECTED_HOST,
            "subdomainHost": _SUBDOMAIN_HOST,
            "crossSiteHost": _CROSS_SITE_HOST,
            "cookieTemporalPolicy": "explicit SameSite=Lax only; no Default-SameSite fidelity claim",
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
        default=Path("browser-evidence/browser-recovery-evidence.json"),
    )
    args = parser.parse_args()
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())

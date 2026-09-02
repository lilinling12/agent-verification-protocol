"""Execute Browser acceptance evidence for SameSite and storage partitioning.

This is non-normative test infrastructure. Browser products and Playwright are
observed as evidence inputs; their serialization formats do not define AEP-0011.
The runner therefore records transport lossiness and engine-policy variation as
explicit dispositions rather than normalizing them into a false common model.
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

_FIXTURE_REVISION = "browser-cookie-partition-evidence-v0.1"
_FIRST_PARTY = "a.test"
_TOP_LEVEL_ONE = "b.test"
_TOP_LEVEL_TWO = "c.test"


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
    server_version = "AVPBrowserCookiePartitionEvidence/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        path = self.path.split("?", 1)[0]
        if path == "/set-samesite":
            self._send(
                b"same-site cookies seeded",
                headers=(
                    ("Set-Cookie", "default_site=1; Path=/"),
                    ("Set-Cookie", "explicit_lax=1; Path=/; SameSite=Lax"),
                ),
            )
            return
        if path == "/cross-site-post":
            port = self.server.server_address[1]
            html = f"""<!doctype html>
<meta charset=utf-8>
<form id=post method=post action=http://{_FIRST_PARTY}:{port}/echo-post></form>
<script>document.getElementById('post').submit()</script>
""".encode("utf-8")
            self._send(html, content_type="text/html; charset=utf-8")
            return
        self._send(
            b"<!doctype html><meta charset=utf-8><title>AVP Browser Evidence</title>",
            content_type="text/html; charset=utf-8",
        )

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler contract
        path = self.path.split("?", 1)[0]
        if path == "/echo-post":
            self._send(self.headers.get("Cookie", "").encode("utf-8"))
            return
        self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        return

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


def _case_bae_002(browser: Any, port: int) -> CaseResult:
    context = browser.new_context()
    try:
        page = context.new_page()
        page.goto(_url(_FIRST_PARTY, port, "/set-samesite"))
        cookies = {
            cookie["name"]: cookie
            for cookie in context.cookies([_url(_FIRST_PARTY, port)])
            if cookie["name"] in {"default_site", "explicit_lax"}
        }
        if set(cookies) != {"default_site", "explicit_lax"}:
            raise AssertionError(f"expected SameSite fixture cookies, got {sorted(cookies)}")

        reported = {
            name: cookie.get("sameSite")
            for name, cookie in sorted(cookies.items())
        }
        distinguishable = reported["default_site"] != reported["explicit_lax"]
        return CaseResult(
            case_id="BAE-002",
            status="pass" if distinguishable else "partial",
            details={
                "transport_reported_sameSite": reported,
                "transport_distinguishes_default_from_explicit_lax": distinguishable,
                "projection_disposition": (
                    "transport exposes distinguishable stored-state evidence; independent review still required"
                    if distinguishable
                    else "transport serialization cannot prove Default versus explicit Lax; AVP projection must fail closed if no independent evidence path exists"
                ),
            },
        )
    finally:
        context.close()


def _case_bae_003(browser: Any, port: int) -> CaseResult:
    context = browser.new_context()
    try:
        page = context.new_page()
        page.goto(_url(_FIRST_PARTY, port, "/set-samesite"))
        page.goto(_url(_TOP_LEVEL_ONE, port, "/cross-site-post"))
        page.wait_for_url(f"http://{_FIRST_PARTY}:{port}/echo-post")
        echoed = page.text_content("body") or ""

        default_sent = "default_site=1" in echoed
        explicit_lax_sent = "explicit_lax=1" in echoed
        if explicit_lax_sent:
            raise AssertionError(
                "explicit SameSite=Lax cookie was sent on controlled cross-site unsafe POST"
            )

        return CaseResult(
            case_id="BAE-003",
            status="partial",
            details={
                "fresh_default_sent_on_cross_site_unsafe_post": default_sent,
                "explicit_lax_sent_on_cross_site_unsafe_post": explicit_lax_sent,
                "optional_recent_cookie_behavior_observed": default_sent,
                "temporal_restore_disposition": (
                    "fresh Default behavior differs from explicit Lax in this bound engine/build; historical creation-time preservation/equivalence remains required before relying on this behavior"
                    if default_sent
                    else "no fresh-cookie compatibility behavior observed in this case; absence does not prove creation time is globally irrelevant"
                ),
                "closure": "diagnostic only; historical-age comparison or another independently reviewable temporal proof remains required",
            },
        )
    finally:
        context.close()


def _third_party_storage(frame: Any, operation: str, value: str | None = None) -> Any:
    script = """
    ([operation, value]) => {
      try {
        if (operation === 'write') {
          localStorage.setItem('partition_probe', value);
          return {kind: 'ok', value: localStorage.getItem('partition_probe')};
        }
        return {kind: 'ok', value: localStorage.getItem('partition_probe')};
      } catch (error) {
        return {kind: 'blocked', name: error.name, message: String(error.message)};
      }
    }
    """
    return frame.evaluate(script, [operation, value])


def _attach_third_party_frame(page: Any, port: int) -> Any:
    page.evaluate(
        """
        url => new Promise((resolve, reject) => {
          const frame = document.createElement('iframe');
          frame.src = url;
          frame.onload = () => resolve(true);
          frame.onerror = () => reject(new Error('third-party iframe failed to load'));
          document.body.appendChild(frame);
        })
        """,
        _url(_FIRST_PARTY, port),
    )
    frames = [frame for frame in page.frames if frame.url.startswith(_url(_FIRST_PARTY, port))]
    if len(frames) != 1:
        raise AssertionError(f"expected one third-party frame, got {len(frames)}")
    return frames[0]


def _case_bae_006(browser: Any, port: int) -> CaseResult:
    context = browser.new_context()
    try:
        page = context.new_page()
        page.goto(_url(_TOP_LEVEL_ONE, port))
        first_frame = _attach_third_party_frame(page, port)
        first = _third_party_storage(first_frame, "write", "under-b")

        page.goto(_url(_TOP_LEVEL_TWO, port))
        second_frame = _attach_third_party_frame(page, port)
        second = _third_party_storage(second_frame, "read")

        if first["kind"] == "blocked" or second["kind"] == "blocked":
            model = "blocked"
            status = "pass"
            disposition = (
                "third-party storage is unavailable in at least one controlled context; Browser v0.1 must not invent tuple-origin state and must treat the dependency as unsupported/insufficient unless separately governed"
            )
        elif second.get("value") != "under-b":
            model = "partitioned"
            status = "pass"
            disposition = (
                "same third-party tuple origin does not expose one shared bucket across top-level sites; base-profile projection must not flatten these contexts into ordinary tuple-origin state"
            )
        else:
            model = "shared-unpartitioned"
            status = "partial"
            disposition = (
                "this bound engine/build exposed shared unpartitioned third-party localStorage; the run does not demonstrate a partitioned bucket, and any admission into Browser v0.1 still requires explicit proof that tuple origin is the complete selected storage identity"
            )

        return CaseResult(
            case_id="BAE-006",
            status=status,
            details={
                "observed_storage_model": model,
                "top_level_b_result": first,
                "top_level_c_result": second,
                "base_profile_disposition": disposition,
                "vendor_partition_key_used_as_avp_identity": False,
            },
        )
    finally:
        context.close()


def _run_engine(browser_type: Any, port: int) -> EngineResult:
    browser = browser_type.launch(headless=True)
    try:
        results: list[CaseResult] = []
        for case in (_case_bae_002, _case_bae_003, _case_bae_006):
            case_id = case.__name__.replace("_case_bae_", "BAE-").replace("_", "-")
            try:
                results.append(case(browser, port))
            except Exception as exc:
                results.append(
                    CaseResult(
                        case_id=case_id,
                        status="fail",
                        details={"error_type": type(exc).__name__, "error": str(exc)},
                    )
                )
        return EngineResult(
            engine_family=browser_type.name,
            browser_version=browser.version,
            cases=tuple(results),
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
        "schema": "avp-browser-cookie-partition-evidence-v0.1",
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
            "hosts": [_FIRST_PARTY, _TOP_LEVEL_ONE, _TOP_LEVEL_TWO],
            "nonDefaultBrowserFlags": [],
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
    partials = [
        (engine.engine_family, case.case_id)
        for engine in engines
        for case in engine.cases
        if case.status == "partial"
    ]
    print(json.dumps({"failures": failures, "partials": partials}, indent=2))
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("browser-evidence/browser-cookie-partition-evidence.json"),
    )
    args = parser.parse_args()
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())

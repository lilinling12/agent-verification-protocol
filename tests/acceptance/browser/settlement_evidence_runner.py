"""Execute non-normative evidence for the AEP-0011 settlement witness.

The test deliberately creates a profile-relevant mutation that remains pending
after the browser reaches network-idle. Correctness is determined by explicit
Evaluator/Control mutation state, never by sleeping or by a provider idle flag.
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

_FIXTURE_REVISION = "browser-settlement-evidence-v0.1"
_HOST = "a.test"


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
    """Test-only evaluator ledger for accepted profile-relevant mutations.

    This is intentionally not a reusable runtime abstraction. It models only the
    acceptance invariant needed by BAE-010: after admission closes, no new
    Subject mutation is accepted, and projection is forbidden while an already
    accepted profile-relevant mutation remains unresolved.
    """

    def __init__(self) -> None:
        self._admission_open = True
        self._states: dict[str, str] = {}

    def accept(self, mutation_id: str) -> None:
        if not self._admission_open:
            raise RuntimeError("subject side-effect admission is closed")
        if mutation_id in self._states:
            raise RuntimeError(f"duplicate mutation id: {mutation_id}")
        self._states[mutation_id] = "accepted"

    def close_admission(self) -> None:
        self._admission_open = False

    def mark_terminal(self, mutation_id: str) -> None:
        if self._states.get(mutation_id) != "accepted":
            raise RuntimeError(f"mutation is not unresolved accepted work: {mutation_id}")
        self._states[mutation_id] = "terminal"

    def unresolved(self) -> tuple[str, ...]:
        return tuple(
            mutation_id
            for mutation_id, state in sorted(self._states.items())
            if state == "accepted"
        )

    @property
    def admission_open(self) -> bool:
        return self._admission_open


class _FixtureHandler(BaseHTTPRequestHandler):
    server_version = "AVPBrowserSettlementEvidence/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        payload = b"""<!doctype html>
<meta charset=utf-8>
<title>AVP Settlement Evidence</title>
<script>
window.__mutationDone = false;
window.startDelayedMutation = () => {
  setTimeout(() => {
    localStorage.setItem('settlement_probe', 'terminal-value');
    window.__mutationDone = true;
  }, 1500);
};
</script>
"""
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


def _url(port: int) -> str:
    return f"http://{_HOST}:{port}/"


def _project_selected_state(page: Any, ledger: _MutationLedger) -> dict[str, Any]:
    unresolved = ledger.unresolved()
    if unresolved:
        return {
            "accepted": False,
            "condition": "unsettled",
            "unresolved": list(unresolved),
        }
    return {
        "accepted": True,
        "condition": "settled",
        "localStorage": {
            "settlement_probe": page.evaluate(
                "localStorage.getItem('settlement_probe')"
            )
        },
    }


def _case_bae_010(browser: Any, port: int) -> CaseResult:
    context = browser.new_context()
    try:
        page = context.new_page()
        page.goto(_url(port))
        page.evaluate("localStorage.clear()")

        ledger = _MutationLedger()
        ledger.accept("mutation-1")
        page.evaluate("window.startDelayedMutation()")
        ledger.close_admission()

        # Playwright's network-idle condition can become true while the accepted
        # timer-based storage mutation is still unresolved. The result is
        # recorded as evidence, but it has no authority over settlement.
        page.wait_for_load_state("networkidle")
        mutation_done_at_network_idle = bool(page.evaluate("window.__mutationDone"))
        if mutation_done_at_network_idle:
            raise AssertionError(
                "fixture mutation completed before the intended network-idle observation"
            )

        pre_terminal_projection = _project_selected_state(page, ledger)
        if pre_terminal_projection["accepted"]:
            raise AssertionError("projection was accepted while mutation remained unresolved")
        if pre_terminal_projection["condition"] != "unsettled":
            raise AssertionError("unresolved mutation did not produce unsettled condition")

        rejected_after_close = False
        try:
            ledger.accept("mutation-after-close")
        except RuntimeError:
            rejected_after_close = True
        if not rejected_after_close:
            raise AssertionError("new Subject mutation was admitted after admission closed")

        # Wait on an explicit terminal predicate rather than a correctness sleep.
        page.wait_for_function("window.__mutationDone === true")
        ledger.mark_terminal("mutation-1")

        post_terminal_projection = _project_selected_state(page, ledger)
        if not post_terminal_projection["accepted"]:
            raise AssertionError("projection remained rejected after all accepted work terminated")
        if (
            post_terminal_projection["localStorage"]["settlement_probe"]
            != "terminal-value"
        ):
            raise AssertionError("accepted terminal mutation was not reflected in projection")

        return CaseResult(
            case_id="BAE-010",
            status="pass",
            details={
                "network_idle_observed_before_terminal": True,
                "network_idle_proved_settlement": False,
                "pre_terminal_projection": pre_terminal_projection,
                "new_subject_mutation_after_close_rejected": rejected_after_close,
                "post_terminal_projection": post_terminal_projection,
                "terminal_wait": "explicit browser predicate observed by evaluator/control",
            },
        )
    finally:
        context.close()


def _run_engine(browser_type: Any, port: int) -> EngineResult:
    browser = browser_type.launch(headless=True)
    try:
        try:
            result = _case_bae_010(browser, port)
        except Exception as exc:
            result = CaseResult(
                case_id="BAE-010",
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
        "schema": "avp-browser-settlement-evidence-v0.1",
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
            "host": _HOST,
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
        default=Path("browser-evidence/browser-settlement-evidence.json"),
    )
    args = parser.parse_args()
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())

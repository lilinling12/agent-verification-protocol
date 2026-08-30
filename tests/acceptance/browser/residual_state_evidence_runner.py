"""Execute non-normative residual-state noninterference evidence for AEP-0011.

BAE-011 proves that equal selected Browser v0.1 state does not imply equal
behavior when excluded browser state differs. The fixture exercises two
independent excluded-state surfaces: Service Worker/Cache Storage and IndexedDB.
It then proves one admissible isolation policy: destroy the contaminated isolated
context, create a fresh context, and materialize only the selected base-profile
state.

The runner uses ``http://localhost`` because Service Worker registration requires
a secure context and localhost is the web-platform loopback exception for a
potentially trustworthy origin.

Playwright is evidence transport only. In particular, Playwright documents its
Service Worker support as Chromium-only. A non-Chromium managed build that
cannot demonstrate the Service Worker fetch-interception subproof is therefore
recorded as transport-insufficient, not as a protocol failure and never as a
protocol pass. An independently observed interception remains useful evidence,
but an unsupported transport cannot close engine-family evidence.

This module is acceptance evidence only. It is not Browser runtime, portable
TCK, or protocol authority.
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

_FIXTURE_REVISION = "browser-residual-state-evidence-v0.6"
_HOST = "localhost"
_SELECTED_COOKIE = "avp_selected=baseline; Path=/; SameSite=Lax"
_SELECTED_STORAGE = {"selected": "baseline"}
_DB_NAME = "avp-residual-db"
_DB_STORE = "state"
_DB_KEY = "probe"
_DB_VALUE = "residual-value"
_CACHE_NAME = "avp-residual-v1"
_PLAYWRIGHT_SERVICE_WORKER_DOC = "https://playwright.dev/docs/service-workers"


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
    server_version = "AVPBrowserResidualEvidence/0.6"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = self.path.split("?", 1)[0]
        if path == "/seed-cookie":
            self._send(b"seeded", headers=(("Set-Cookie", _SELECTED_COOKIE),))
            return
        if path == "/sw.js":
            body = f"""
self.addEventListener('install', event => {{
  event.waitUntil(caches.open('{_CACHE_NAME}').then(cache =>
    cache.put('/controlled-resource', new Response('service-worker-cache'))
  ).then(() => self.skipWaiting()));
}});
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', event => {{
  const url = new URL(event.request.url);
  if (url.pathname === '/controlled-resource') {{
    event.respondWith(caches.match('/controlled-resource').then(response =>
      response || fetch(event.request)
    ));
  }}
}});
""".encode("utf-8")
            self._send(body, content_type="text/javascript; charset=utf-8")
            return
        if path == "/controlled-resource":
            self._send(b"network-origin")
            return
        if path == "/probe-cookie":
            self._send(self.headers.get("Cookie", "").encode("utf-8"))
            return
        self._send(
            b"<!doctype html><meta charset=utf-8><title>AVP Residual Evidence</title>",
            content_type="text/html; charset=utf-8",
        )

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
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            # Navigations may abandon a response after enough bytes arrive.
            # That transport close is not Browser-state evidence.
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


def _url(port: int, path: str = "/") -> str:
    return f"http://{_HOST}:{port}{path}"


def _set_selected_state(context: Any, port: int) -> None:
    page = context.new_page()
    try:
        page.goto(_url(port, "/seed-cookie"))
        page.goto(_url(port, "/state"))
        page.evaluate(
            """state => {
              localStorage.clear();
              for (const [key, value] of Object.entries(state)) {
                localStorage.setItem(key, value);
              }
            }""",
            _SELECTED_STORAGE,
        )
    finally:
        page.close()


def _project_selected_state(context: Any, port: int) -> dict[str, Any]:
    page = context.new_page()
    try:
        cookie_response = page.goto(_url(port, "/probe-cookie"))
        if cookie_response is None:
            raise AssertionError("selected cookie probe produced no response")
        cookie_header = cookie_response.text()
        page.goto(_url(port, "/state"))
        storage = page.evaluate(
            """() => Object.fromEntries(
              Array.from({length: localStorage.length}, (_, index) => localStorage.key(index))
                .sort()
                .map(key => [key, localStorage.getItem(key)])
            )"""
        )
        return {
            "selectedCookiePresent": "avp_selected=baseline" in cookie_header,
            "localStorage": storage,
        }
    finally:
        page.close()


def _assert_service_worker_capability(page: Any) -> None:
    capability = page.evaluate(
        """() => ({
          secureContext: window.isSecureContext,
          serviceWorkerAvailable: 'serviceWorker' in navigator,
        })"""
    )
    if capability != {"secureContext": True, "serviceWorkerAvailable": True}:
        raise AssertionError(
            "residual fixture lacks the required trustworthy Service Worker context: "
            f"{capability!r}"
        )


def _install_service_worker_and_cache(context: Any, port: int) -> None:
    """Install residue without making client-controller timing an oracle."""

    page = context.new_page()
    try:
        page.goto(_url(port, "/state"))
        _assert_service_worker_capability(page)
        state = page.evaluate(
            """async () => {
              const registration = await navigator.serviceWorker.register('/sw.js');
              const ready = await navigator.serviceWorker.ready;
              return {
                scope: registration.scope,
                active: ready.active !== null,
              };
            }"""
        )
        if not state.get("active"):
            raise AssertionError(f"Service Worker did not reach ready active registration: {state!r}")
    finally:
        page.close()


def _service_worker_registration_count(context: Any, port: int) -> int:
    page = context.new_page()
    try:
        page.goto(_url(port, "/state"))
        _assert_service_worker_capability(page)
        return int(
            page.evaluate(
                "navigator.serviceWorker.getRegistrations().then(registrations => registrations.length)"
            )
        )
    finally:
        page.close()


def _cache_names(context: Any, port: int) -> tuple[str, ...]:
    page = context.new_page()
    try:
        page.goto(_url(port, "/state"))
        names = page.evaluate("caches.keys()")
        return tuple(sorted(str(name) for name in names))
    finally:
        page.close()


def _seed_indexed_db(context: Any, port: int) -> None:
    page = context.new_page()
    try:
        page.goto(_url(port, "/state"))
        page.evaluate(
            """([dbName, storeName, key, value]) => new Promise((resolve, reject) => {
              const request = indexedDB.open(dbName, 1);
              request.onupgradeneeded = () => request.result.createObjectStore(storeName);
              request.onerror = () => reject(request.error);
              request.onsuccess = () => {
                const db = request.result;
                const tx = db.transaction(storeName, 'readwrite');
                tx.objectStore(storeName).put(value, key);
                tx.oncomplete = () => { db.close(); resolve(true); };
                tx.onerror = () => reject(tx.error);
              };
            })""",
            [_DB_NAME, _DB_STORE, _DB_KEY, _DB_VALUE],
        )
    finally:
        page.close()


def _read_indexed_db(context: Any, port: int) -> str | None:
    """Read controlled IndexedDB state without creating a missing database."""

    page = context.new_page()
    try:
        page.goto(_url(port, "/state"))
        return page.evaluate(
            """([dbName, storeName, key]) => new Promise(async (resolve, reject) => {
              if (typeof indexedDB.databases !== 'function') {
                reject(new Error('indexedDB.databases() unavailable for side-effect-free residue probe'));
                return;
              }
              let databases;
              try {
                databases = await indexedDB.databases();
              } catch (error) {
                reject(error);
                return;
              }
              if (!databases.some(database => database.name === dbName)) {
                resolve(null);
                return;
              }
              const request = indexedDB.open(dbName);
              request.onerror = () => reject(request.error);
              request.onsuccess = () => {
                const db = request.result;
                if (!db.objectStoreNames.contains(storeName)) {
                  db.close();
                  resolve(null);
                  return;
                }
                const tx = db.transaction(storeName, 'readonly');
                const get = tx.objectStore(storeName).get(key);
                get.onsuccess = () => {
                  const value = get.result ?? null;
                  db.close();
                  resolve(value);
                };
                get.onerror = () => reject(get.error);
              };
            })""",
            [_DB_NAME, _DB_STORE, _DB_KEY],
        )
    finally:
        page.close()


def _indexed_db_behavior(context: Any, port: int) -> str:
    """Project an IndexedDB behavior state using a side-effect-free existence probe."""

    value = _read_indexed_db(context, port)
    if value is None:
        return "indexeddb-clean"
    if value == _DB_VALUE:
        return "indexeddb-residual"
    raise AssertionError(f"unexpected controlled IndexedDB value: {value!r}")


def _read_controlled_resource(context: Any, port: int) -> str:
    page = context.new_page()
    try:
        page.goto(_url(port, "/state"))
        return str(
            page.evaluate(
                "url => fetch(url, {cache: 'no-store'}).then(response => response.text())",
                _url(port, "/controlled-resource"),
            )
        )
    finally:
        page.close()


def _assert_clean_excluded_state(context: Any, port: int) -> None:
    registrations = _service_worker_registration_count(context, port)
    if registrations != 0:
        raise AssertionError(
            f"clean isolated context unexpectedly had Service Worker registrations: {registrations}"
        )
    cache_names = _cache_names(context, port)
    if cache_names:
        raise AssertionError(
            f"clean isolated context unexpectedly had Cache residue: {cache_names!r}"
        )
    indexed_db = _read_indexed_db(context, port)
    if indexed_db is not None:
        raise AssertionError(
            f"clean isolated context unexpectedly had IndexedDB residue: {indexed_db!r}"
        )


def _playwright_service_worker_support(engine_family: str) -> str:
    """Classify Playwright transport support, never browser-engine semantics."""

    if engine_family == "chromium":
        return "documented-supported"
    return "documented-nonchromium-insufficient"


def _case_bae_011(browser: Any, port: int, engine_family: str) -> CaseResult:
    clean = browser.new_context()
    residual = browser.new_context()
    recreated = None
    try:
        _set_selected_state(clean, port)
        _set_selected_state(residual, port)

        clean_selected = _project_selected_state(clean, port)
        residual_selected_before = _project_selected_state(residual, port)
        if clean_selected != residual_selected_before:
            raise AssertionError("contexts did not begin with identical selected state")
        _assert_clean_excluded_state(clean, port)

        clean_idb_before = _indexed_db_behavior(clean, port)
        residual_idb_before = _indexed_db_behavior(residual, port)
        if clean_idb_before != "indexeddb-clean" or residual_idb_before != "indexeddb-clean":
            raise AssertionError(
                "contexts did not begin with clean IndexedDB behavior: "
                f"clean={clean_idb_before!r}, residual={residual_idb_before!r}"
            )

        _install_service_worker_and_cache(residual, port)
        _seed_indexed_db(residual, port)

        residual_selected_after = _project_selected_state(residual, port)
        if residual_selected_after != clean_selected:
            raise AssertionError("excluded-state setup unexpectedly changed selected state")

        clean_idb_after = _indexed_db_behavior(clean, port)
        residual_idb_after = _indexed_db_behavior(residual, port)
        if clean_idb_after != "indexeddb-clean":
            raise AssertionError(
                f"clean context IndexedDB behavior unexpectedly changed: {clean_idb_after!r}"
            )
        if residual_idb_after != "indexeddb-residual":
            raise AssertionError(
                "controlled IndexedDB residue did not materially change behavior: "
                f"{residual_idb_after!r}"
            )

        registrations = _service_worker_registration_count(residual, port)
        if registrations < 1:
            raise AssertionError("Service Worker registration residue was not observable")
        cache_names = _cache_names(residual, port)
        if _CACHE_NAME not in cache_names:
            raise AssertionError(
                f"controlled Cache residue was not observable: {cache_names!r}"
            )

        clean_resource = _read_controlled_resource(clean, port)
        residual_resource = _read_controlled_resource(residual, port)
        if clean_resource != "network-origin":
            raise AssertionError(f"clean context resource unexpectedly changed: {clean_resource!r}")

        transport_support = _playwright_service_worker_support(engine_family)
        if residual_resource == "service-worker-cache":
            service_worker_outcome = (
                "pass"
                if transport_support == "documented-supported"
                else "observed-unsupported-transport"
            )
        elif residual_resource == "network-origin" and transport_support != "documented-supported":
            # Playwright documents SW support as Chromium-only. This branch is a
            # transport limitation classification, not a Gecko/WebKit semantic
            # claim and not a portable-protocol success.
            service_worker_outcome = "transport-insufficient"
        else:
            raise AssertionError(
                "Service Worker/Cache behavior was inconsistent with the observed transport capability: "
                f"support={transport_support!r}, response={residual_resource!r}"
            )

        # One admissible noninterference strategy: discard the contaminated
        # isolated session, create a fresh session, then materialize only the
        # selected Browser-v0.1 state. Excluded residue must not cross the
        # isolation boundary.
        residual.close()
        recreated = browser.new_context()
        _set_selected_state(recreated, port)
        recreated_selected = _project_selected_state(recreated, port)
        if recreated_selected != clean_selected:
            raise AssertionError("fresh isolated context changed selected baseline")
        _assert_clean_excluded_state(recreated, port)

        recreated_idb = _indexed_db_behavior(recreated, port)
        if recreated_idb != "indexeddb-clean":
            raise AssertionError(
                f"IndexedDB residue crossed fresh isolation boundary: {recreated_idb!r}"
            )
        recreated_resource = _read_controlled_resource(recreated, port)
        if recreated_resource != "network-origin":
            raise AssertionError("Service Worker/Cache residue crossed fresh isolation boundary")

        status = "pass" if service_worker_outcome == "pass" else "partial"
        closure_required = None
        if status == "partial":
            closure_required = (
                "obtain the Service Worker/cache behavior subproof from a documented shipping/native "
                "transport for this engine family; any Playwright non-Chromium observation remains "
                "diagnostic and does not close engine-family evidence"
            )

        return CaseResult(
            case_id="BAE-011",
            status=status,
            details={
                "fixture_origin_is_potentially_trustworthy": True,
                "service_worker_controller_timing_used_as_oracle": False,
                "selected_state_equal_before_excluded_mutation": True,
                "selected_state_equal_after_excluded_mutation": True,
                "indexeddb_behavior_before_clean": clean_idb_before,
                "indexeddb_behavior_before_residual": residual_idb_before,
                "indexeddb_behavior_after_clean": clean_idb_after,
                "indexeddb_behavior_after_residual": residual_idb_after,
                "indexeddb_behavior_changed": True,
                "fresh_isolated_context_indexeddb_behavior": recreated_idb,
                "service_worker_registration_observed": True,
                "cache_storage_residue_observed": True,
                "service_worker_expected_intercept": "service-worker-cache",
                "service_worker_observed_response": residual_resource,
                "service_worker_behavior_outcome": service_worker_outcome,
                "service_worker_transport_support": transport_support,
                "service_worker_transport_documentation": _PLAYWRIGHT_SERVICE_WORKER_DOC,
                "service_worker_transport_authority": "test-transport-only",
                "selected_state_equality_proved_excluded_equivalence": False,
                "fresh_isolated_context_removed_service_worker_cache_residue": True,
                "fresh_isolated_context_removed_indexeddb_residue": True,
                "full_bae011_engine_family_evidence_proven": status == "pass",
                "closure_required": closure_required,
                "noninterference_strategy_proven": (
                    "destroy contaminated isolated context; recreate fresh context; "
                    "materialize selected base state only"
                ),
                "protocol_disposition": (
                    "base restore must bind/establish an isolation policy equivalent to the proven "
                    "boundary, or fail closed when Scenario behavior materially depends on excluded state"
                ),
            },
        )
    finally:
        clean.close()
        if recreated is not None:
            recreated.close()
        try:
            residual.close()
        except Exception:
            pass


def _run_engine(browser_type: Any, port: int) -> EngineResult:
    browser = browser_type.launch(headless=True)
    try:
        try:
            result = _case_bae_011(browser, port, browser_type.name)
        except Exception as exc:
            result = CaseResult(
                case_id="BAE-011",
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
        "schema": "avp-browser-residual-state-evidence-v0.1",
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
            "originTrustPolicy": "http localhost potentially-trustworthy loopback exception",
            "excludedSurfaces": ["service-worker", "cache-storage", "indexeddb"],
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
        default=Path("browser-evidence/browser-residual-state-evidence.json"),
    )
    args = parser.parse_args()
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())

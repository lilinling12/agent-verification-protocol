"""Execute non-normative residual-state noninterference evidence for AEP-0011.

BAE-011 proves that equal selected Browser v0.1 state does not imply equal
behavior when excluded browser state differs.  The fixture exercises two
material excluded surfaces: Service Worker/Cache Storage and IndexedDB.

The acceptance conclusion is not that AVP should restore those surfaces.  It is
that Browser v0.1 must bind an isolation/policy condition or fail closed when a
Scenario materially depends on them.  This module is test-only evidence, not a
portable Browser runtime or TCK implementation.
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

_FIXTURE_REVISION = "browser-residual-state-evidence-v0.1"
_HOST = "a.test"
_SELECTED_COOKIE = "avp_selected=baseline; Path=/; SameSite=Lax"
_SELECTED_STORAGE = {"selected": "baseline"}
_DB_NAME = "avp-residual-db"
_DB_STORE = "state"
_DB_KEY = "probe"
_DB_VALUE = "residual-value"
_CACHE_NAME = "avp-residual-v1"


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
    server_version = "AVPBrowserResidualEvidence/0.1"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = self.path.split("?", 1)[0]
        if path == "/seed-cookie":
            self._send(
                b"seeded",
                headers=(("Set-Cookie", _SELECTED_COOKIE),),
            )
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
              for (const [key, value] of Object.entries(state)) localStorage.setItem(key, value);
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


def _install_service_worker_and_cache(context: Any, port: int) -> None:
    page = context.new_page()
    try:
        page.goto(_url(port, "/state"))
        page.evaluate(
            """async () => {
              await navigator.serviceWorker.register('/sw.js');
              await navigator.serviceWorker.ready;
              if (!navigator.serviceWorker.controller) {
                location.reload();
                await new Promise(resolve => {
                  if (navigator.serviceWorker.controller) { resolve(true); return; }
                  navigator.serviceWorker.addEventListener('controllerchange', () => resolve(true), {once: true});
                });
              }
              return true;
            }"""
        )
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
    """Read the controlled IndexedDB value without creating a missing database."""

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
                if (!db.objectStoreNames.contains(storeName)) { db.close(); resolve(null); return; }
                const tx = db.transaction(storeName, 'readonly');
                const get = tx.objectStore(storeName).get(key);
                get.onsuccess = () => { const value = get.result ?? null; db.close(); resolve(value); };
                get.onerror = () => reject(get.error);
              };
            })""",
            [_DB_NAME, _DB_STORE, _DB_KEY],
        )
    finally:
        page.close()


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


def _case_bae_011(browser: Any, port: int) -> CaseResult:
    clean = browser.new_context()
    residual = browser.new_context()
    clean_recreated = None
    try:
        _set_selected_state(clean, port)
        _set_selected_state(residual, port)

        clean_selected = _project_selected_state(clean, port)
        residual_selected_before = _project_selected_state(residual, port)
        if clean_selected != residual_selected_before:
            raise AssertionError("contexts did not begin with identical selected state")

        clean_idb_before = _read_indexed_db(clean, port)
        if clean_idb_before is not None:
            raise AssertionError(f"clean context unexpectedly had IndexedDB residue: {clean_idb_before!r}")

        _install_service_worker_and_cache(residual, port)
        _seed_indexed_db(residual, port)

        residual_selected_after = _project_selected_state(residual, port)
        if residual_selected_after != clean_selected:
            raise AssertionError("excluded-state setup unexpectedly changed selected state")

        clean_resource = _read_controlled_resource(clean, port)
        residual_resource = _read_controlled_resource(residual, port)
        if clean_resource != "network-origin":
            raise AssertionError(f"clean context resource unexpectedly changed: {clean_resource!r}")
        if residual_resource != "service-worker-cache":
            raise AssertionError(
                f"Service Worker/Cache residual state did not affect behavior: {residual_resource!r}"
            )

        residual_idb = _read_indexed_db(residual, port)
        if residual_idb != _DB_VALUE:
            raise AssertionError(f"IndexedDB residual state not observed: {residual_idb!r}")

        # Prove one admissible noninterference strategy: destroy the contaminated
        # isolated context and create a fresh independently isolated context,
        # then materialize only the selected Browser-v0.1 state.  The excluded
        # Service Worker/Cache/IndexedDB residue must not survive that boundary.
        residual.close()
        clean_recreated = browser.new_context()
        _set_selected_state(clean_recreated, port)
        recreated_selected = _project_selected_state(clean_recreated, port)
        recreated_resource = _read_controlled_resource(clean_recreated, port)
        recreated_idb = _read_indexed_db(clean_recreated, port)

        if recreated_selected != clean_selected:
            raise AssertionError("fresh isolated context changed selected baseline")
        if recreated_resource != "network-origin":
            raise AssertionError("Service Worker/Cache residue crossed fresh isolation boundary")
        if recreated_idb is not None:
            raise AssertionError("IndexedDB residue crossed fresh isolation boundary")

        return CaseResult(
            case_id="BAE-011",
            status="pass",
            details={
                "selected_state_equal_before_excluded_mutation": True,
                "selected_state_equal_after_excluded_mutation": True,
                "service_worker_cache_changed_behavior": True,
                "indexeddb_residual_value_observed": True,
                "selected_state_equality_proved_excluded_equivalence": False,
                "fresh_isolated_context_removed_service_worker_cache_residue": True,
                "fresh_isolated_context_removed_indexeddb_residue": True,
                "noninterference_strategy_proven": "destroy contaminated isolated context; recreate fresh context; materialize selected base state only",
                "protocol_disposition": (
                    "base restore must bind/establish an isolation policy equivalent to the proven boundary, "
                    "or fail closed when Scenario behavior materially depends on excluded state"
                ),
            },
        )
    finally:
        clean.close()
        if clean_recreated is not None:
            clean_recreated.close()
        try:
            residual.close()
        except Exception:
            pass


def _run_engine(browser_type: Any, port: int) -> EngineResult:
    browser = browser_type.launch(headless=True)
    try:
        try:
            result = _case_bae_011(browser, port)
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

"""Execute BAE-011 residual-state evidence in shipping browser products.

This Alpha 3 runner is non-normative acceptance infrastructure. It uses native
W3C WebDriver transports for branded/shipping browsers and proves one concrete
BPR-008 isolation strategy across independent WebDriver sessions:

1. establish selected Browser-v0.1 state in a clean session;
2. establish the same selected state in a second session and add excluded
   Service Worker/Cache Storage plus IndexedDB residue;
3. prove the excluded residue materially changes behavior while selected state
   remains equal;
4. destroy the contaminated session, create a third fresh session, materialize
   only selected state, and prove the excluded residue did not cross the session
   isolation boundary.

Browser/driver/session details are evidence identity only. They do not become
portable AVP state or normative Browser semantics.

For Safari, each WebDriver session owns one explicitly managed SafariDriver
service generation. The runner starts the service, creates exactly one session,
destroys that session, and then positively stops the service process before the
next generation starts. This mirrors Safari's one-active-session-at-a-time
constraint without treating provider-daemon lifetime as Browser protocol state.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any, Iterator

_FIXTURE_REVISION = "browser-shipping-residual-evidence-v0.1"
_HOST = "localhost"
_SELECTED_COOKIE = "avp_selected=baseline; Path=/; SameSite=Lax"
_SELECTED_STORAGE = {"selected": "baseline"}
_DB_NAME = "avp-shipping-residual-db"
_DB_STORE = "state"
_DB_KEY = "probe"
_DB_VALUE = "shipping-residual-value"
_CACHE_NAME = "avp-shipping-residual-v1"
_SAFARI_DRIVER = "/usr/bin/safaridriver"
_DIAGNOSTIC_TAIL_LIMIT = 4096


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    status: str
    details: dict[str, Any]


@dataclass(frozen=True, slots=True)
class BrowserIdentity:
    engine_family: str
    product: str
    browser_version: str
    driver_version: str | None
    platform_name: str | None
    runner_os: str | None
    runner_arch: str | None
    runner_image_os: str | None
    runner_image_version: str | None


@dataclass(slots=True)
class _ExecutionProgress:
    """Retain transport/session progress without changing the BAE-011 oracle."""

    current_stage: str = "initializing"
    failure_stage: str | None = None
    created_session_count: int = 0
    completed_session_count: int = 0
    browser_identity: BrowserIdentity | None = None
    cleanup_errors: list[dict[str, str]] = field(default_factory=list)
    safari_service_generations_started: int = 0
    safari_service_generations_stopped: int = 0
    safari_diagnostic_logs: dict[str, Path] = field(default_factory=dict)

    def enter(self, stage: str) -> None:
        self.current_stage = stage

    def capture_failure(self) -> None:
        if self.failure_stage is None:
            self.failure_stage = self.current_stage

    def record_cleanup_error(self, stage: str, exc: BaseException) -> None:
        self.cleanup_errors.append(
            {
                "stage": stage,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )

    def transport_evidence(self) -> dict[str, Any]:
        return {
            "createdSessionCount": self.created_session_count,
            "completedSessionCount": self.completed_session_count,
            "safariDriverServiceGenerationsStarted": self.safari_service_generations_started,
            "safariDriverServiceGenerationsStopped": self.safari_service_generations_stopped,
            "cleanupErrors": list(self.cleanup_errors),
        }


class _FixtureHandler(BaseHTTPRequestHandler):
    server_version = "AVPBrowserShippingResidualEvidence/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        path = self.path.split("?", 1)[0]
        if path == "/seed-cookie":
            self._send(b"seeded", headers=(("Set-Cookie", _SELECTED_COOKIE),))
            return
        if path == "/probe-cookie":
            self._send(self.headers.get("Cookie", "").encode("utf-8"))
            return
        if path == "/controlled-resource":
            self._send(b"network-origin")
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
        self._send(
            b"<!doctype html><meta charset=utf-8><title>AVP Shipping Residual Evidence</title>",
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


def _resolve_driver_binary(command: str, env_name: str) -> str | None:
    on_path = shutil.which(command)
    if on_path:
        return on_path
    configured = os.environ.get(env_name)
    if not configured:
        return None
    candidate = Path(configured)
    if candidate.is_dir():
        candidate = candidate / command
    return str(candidate) if candidate.exists() else None


def _command_version(*command: str) -> str | None:
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = (completed.stdout or completed.stderr).strip()
    return value or None


def _new_safari_service(diagnostic_log: Path) -> Any:
    """Create one explicitly caller-owned SafariDriver service generation."""

    from selenium.webdriver.safari.service import Service

    if not Path(_SAFARI_DRIVER).exists():
        raise RuntimeError(f"{_SAFARI_DRIVER} is unavailable on this runner")

    diagnostic_log.parent.mkdir(parents=True, exist_ok=True)
    return Service(
        executable_path=_SAFARI_DRIVER,
        reuse_service=True,
        enable_logging=True,
        log_output=str(diagnostic_log),
    )


def _create_driver(engine: str, *, safari_service: Any | None = None) -> Any:
    from selenium import webdriver

    if engine == "chrome":
        from selenium.webdriver.chrome.service import Service

        executable = _resolve_driver_binary("chromedriver", "CHROMEWEBDRIVER")
        if not executable:
            raise RuntimeError("ChromeDriver was not found in PATH or CHROMEWEBDRIVER")
        options = webdriver.ChromeOptions()
        return webdriver.Chrome(service=Service(executable_path=executable), options=options)

    if engine == "firefox":
        from selenium.webdriver.firefox.service import Service

        executable = _resolve_driver_binary("geckodriver", "GECKOWEBDRIVER")
        if not executable:
            raise RuntimeError("geckodriver was not found in PATH or GECKOWEBDRIVER")
        options = webdriver.FirefoxOptions()
        return webdriver.Firefox(service=Service(executable_path=executable), options=options)

    if engine == "safari":
        if safari_service is None:
            raise RuntimeError("Safari shipping evidence requires a caller-owned SafariDriver service")
        return webdriver.Safari(service=safari_service)

    raise ValueError(f"unsupported engine: {engine}")


class _DriverTransport:
    """Own provider transport generations without owning Browser semantics."""

    def __init__(
        self,
        engine: str,
        progress: _ExecutionProgress,
        *,
        safari_diagnostic_dir: Path,
    ) -> None:
        self._engine = engine
        self._progress = progress
        self._safari_diagnostic_dir = safari_diagnostic_dir

    def _safari_log(self, role: str) -> Path:
        return self._safari_diagnostic_dir / f"safaridriver-{role}.log"

    def create(self, role: str) -> tuple[Any, Any | None]:
        safari_service: Any | None = None
        if self._engine == "safari":
            diagnostic_log = self._safari_log(role)
            self._progress.safari_diagnostic_logs[role] = diagnostic_log
            self._progress.enter(f"{role}:safaridriver-service-create")
            safari_service = _new_safari_service(diagnostic_log)
            self._progress.enter(f"{role}:safaridriver-service-start")
            safari_service.start()
            self._progress.safari_service_generations_started += 1
            self._progress.enter(f"{role}:safaridriver-service-ready")

        self._progress.enter(f"{role}:session-create")
        try:
            driver = _create_driver(self._engine, safari_service=safari_service)
        except BaseException:
            self._progress.capture_failure()
            if safari_service is not None:
                self._stop_safari_service(role, safari_service, primary_failure=True)
            raise

        self._progress.created_session_count += 1
        return driver, safari_service

    def cleanup(
        self,
        role: str,
        driver: Any,
        safari_service: Any | None,
        *,
        primary_failure: bool,
    ) -> None:
        session_stage = (
            f"{role}:session-quit-after-failure" if primary_failure else f"{role}:session-quit"
        )
        self._progress.enter(session_stage)
        try:
            driver.quit()
        except Exception as cleanup_exc:
            self._progress.record_cleanup_error(session_stage, cleanup_exc)
            if not primary_failure:
                self._progress.capture_failure()
                raise

        if safari_service is not None:
            self._stop_safari_service(role, safari_service, primary_failure=primary_failure)

        if not primary_failure:
            self._progress.completed_session_count += 1

    def _stop_safari_service(
        self,
        role: str,
        service: Any,
        *,
        primary_failure: bool,
    ) -> None:
        stage = f"{role}:safaridriver-service-stop"
        self._progress.enter(stage)
        try:
            service.stop()
            process = getattr(service, "process", None)
            if process is not None and process.poll() is None:
                raise RuntimeError("SafariDriver service process remained alive after stop()")
        except Exception as cleanup_exc:
            self._progress.record_cleanup_error(stage, cleanup_exc)
            if not primary_failure:
                self._progress.capture_failure()
                raise
        else:
            self._progress.safari_service_generations_stopped += 1


@contextmanager
def _browser_session(
    transport: _DriverTransport,
    role: str,
    progress: _ExecutionProgress,
) -> Iterator[Any]:
    """Create one session and preserve the primary failure across cleanup."""

    driver, safari_service = transport.create(role)
    try:
        yield driver
    except BaseException:
        progress.capture_failure()
        transport.cleanup(
            role,
            driver,
            safari_service,
            primary_failure=True,
        )
        raise
    else:
        transport.cleanup(
            role,
            driver,
            safari_service,
            primary_failure=False,
        )


def _engine_family(engine: str) -> str:
    return {"chrome": "chromium", "firefox": "gecko", "safari": "webkit"}[engine]


def _product_name(engine: str) -> str:
    return {
        "chrome": "Google Chrome",
        "firefox": "Mozilla Firefox",
        "safari": "Safari",
    }[engine]


def _driver_version(engine: str) -> str | None:
    if engine == "chrome":
        executable = _resolve_driver_binary("chromedriver", "CHROMEWEBDRIVER")
        return _command_version(executable, "--version") if executable else None
    if engine == "firefox":
        executable = _resolve_driver_binary("geckodriver", "GECKOWEBDRIVER")
        return _command_version(executable, "--version") if executable else None
    return _command_version(_SAFARI_DRIVER, "--version")


def _browser_identity(engine: str, driver: Any) -> BrowserIdentity:
    capabilities = driver.capabilities
    return BrowserIdentity(
        engine_family=_engine_family(engine),
        product=_product_name(engine),
        browser_version=str(capabilities.get("browserVersion", "unknown")),
        driver_version=_driver_version(engine),
        platform_name=capabilities.get("platformName"),
        runner_os=os.environ.get("RUNNER_OS"),
        runner_arch=os.environ.get("RUNNER_ARCH"),
        runner_image_os=os.environ.get("ImageOS"),
        runner_image_version=os.environ.get("ImageVersion"),
    )


def _configure_driver(driver: Any) -> None:
    driver.set_page_load_timeout(20)
    driver.set_script_timeout(20)


def _set_selected_state(driver: Any, port: int) -> None:
    driver.get(_url(port, "/seed-cookie"))
    driver.get(_url(port, "/state"))
    driver.execute_script(
        """
        const state = arguments[0];
        localStorage.clear();
        for (const [key, value] of Object.entries(state)) localStorage.setItem(key, value);
        """,
        _SELECTED_STORAGE,
    )


def _project_selected_state(driver: Any, port: int) -> dict[str, Any]:
    driver.get(_url(port, "/probe-cookie"))
    cookie_header = driver.execute_script("return document.body.textContent || '';")
    driver.get(_url(port, "/state"))
    storage = driver.execute_script(
        """
        const keys = Array.from({length: localStorage.length}, (_, i) => localStorage.key(i)).sort();
        return Object.fromEntries(keys.map(key => [key, localStorage.getItem(key)]));
        """
    )
    return {
        "selectedCookiePresent": "avp_selected=baseline" in str(cookie_header),
        "localStorage": storage,
    }


def _service_worker_capability(driver: Any, port: int) -> dict[str, Any]:
    driver.get(_url(port, "/state"))
    return driver.execute_script(
        """
        return {
          secureContext: window.isSecureContext,
          serviceWorkerAvailable: 'serviceWorker' in navigator,
        };
        """
    )


def _assert_service_worker_capability(driver: Any, port: int) -> None:
    capability = _service_worker_capability(driver, port)
    if capability != {"secureContext": True, "serviceWorkerAvailable": True}:
        raise AssertionError(f"shipping fixture lacks Service Worker capability: {capability!r}")


def _install_service_worker_and_cache(driver: Any, port: int) -> None:
    driver.get(_url(port, "/state"))
    _assert_service_worker_capability(driver, port)
    state = driver.execute_async_script(
        """
        const done = arguments[arguments.length - 1];
        (async () => {
          const registration = await navigator.serviceWorker.register('/sw.js');
          const ready = await navigator.serviceWorker.ready;
          return {scope: registration.scope, active: ready.active !== null};
        })().then(done).catch(error => done({error: String(error)}));
        """
    )
    if state.get("error"):
        raise AssertionError(f"Service Worker registration failed: {state['error']}")
    if not state.get("active"):
        raise AssertionError(f"Service Worker did not reach ready active registration: {state!r}")
    # A fresh document removes reliance on controller-exposure timing. The
    # subsequent fetch behavior remains the actual acceptance oracle.
    driver.get(_url(port, "/controlled-client"))


def _service_worker_registration_count(driver: Any, port: int) -> int:
    driver.get(_url(port, "/state"))
    _assert_service_worker_capability(driver, port)
    result = driver.execute_async_script(
        """
        const done = arguments[arguments.length - 1];
        navigator.serviceWorker.getRegistrations()
          .then(registrations => done({count: registrations.length}))
          .catch(error => done({error: String(error)}));
        """
    )
    if result.get("error"):
        raise AssertionError(f"Service Worker registration probe failed: {result['error']}")
    return int(result["count"])


def _cache_names(driver: Any, port: int) -> tuple[str, ...]:
    driver.get(_url(port, "/state"))
    result = driver.execute_async_script(
        """
        const done = arguments[arguments.length - 1];
        caches.keys()
          .then(names => done({names}))
          .catch(error => done({error: String(error)}));
        """
    )
    if result.get("error"):
        raise AssertionError(f"Cache Storage probe failed: {result['error']}")
    return tuple(sorted(str(name) for name in result["names"]))


def _seed_indexed_db(driver: Any, port: int) -> None:
    driver.get(_url(port, "/state"))
    result = driver.execute_async_script(
        """
        const [dbName, storeName, key, value, done] = arguments;
        const request = indexedDB.open(dbName, 1);
        request.onupgradeneeded = () => request.result.createObjectStore(storeName);
        request.onerror = () => done({error: String(request.error)});
        request.onsuccess = () => {
          const db = request.result;
          const tx = db.transaction(storeName, 'readwrite');
          tx.objectStore(storeName).put(value, key);
          tx.oncomplete = () => { db.close(); done({ok: true}); };
          tx.onerror = () => done({error: String(tx.error)});
        };
        """,
        _DB_NAME,
        _DB_STORE,
        _DB_KEY,
        _DB_VALUE,
    )
    if result.get("error"):
        raise AssertionError(f"IndexedDB seed failed: {result['error']}")


def _read_indexed_db(driver: Any, port: int) -> str | None:
    driver.get(_url(port, "/state"))
    result = driver.execute_async_script(
        """
        const [dbName, storeName, key, done] = arguments;
        (async () => {
          if (typeof indexedDB.databases !== 'function') {
            return {error: 'indexedDB.databases() unavailable for side-effect-free residue probe'};
          }
          const databases = await indexedDB.databases();
          if (!databases.some(database => database.name === dbName)) return {value: null};
          return await new Promise(resolve => {
            const request = indexedDB.open(dbName);
            request.onerror = () => resolve({error: String(request.error)});
            request.onsuccess = () => {
              const db = request.result;
              if (!db.objectStoreNames.contains(storeName)) {
                db.close();
                resolve({value: null});
                return;
              }
              const tx = db.transaction(storeName, 'readonly');
              const get = tx.objectStore(storeName).get(key);
              get.onsuccess = () => {
                const value = get.result ?? null;
                db.close();
                resolve({value});
              };
              get.onerror = () => resolve({error: String(get.error)});
            };
          });
        })().then(done).catch(error => done({error: String(error)}));
        """,
        _DB_NAME,
        _DB_STORE,
        _DB_KEY,
    )
    if result.get("error"):
        raise AssertionError(f"IndexedDB residue probe failed: {result['error']}")
    return result.get("value")


def _read_controlled_resource(driver: Any, port: int) -> str:
    driver.get(_url(port, "/state"))
    result = driver.execute_async_script(
        """
        const [url, done] = arguments;
        fetch(url, {cache: 'no-store'})
          .then(response => response.text())
          .then(value => done({value}))
          .catch(error => done({error: String(error)}));
        """,
        _url(port, "/controlled-resource"),
    )
    if result.get("error"):
        raise AssertionError(f"controlled resource probe failed: {result['error']}")
    return str(result["value"])


def _assert_clean_excluded_state(driver: Any, port: int) -> dict[str, Any]:
    registrations = _service_worker_registration_count(driver, port)
    caches = _cache_names(driver, port)
    indexed_db = _read_indexed_db(driver, port)
    if registrations != 0:
        raise AssertionError(f"fresh session unexpectedly had Service Worker residue: {registrations}")
    if caches:
        raise AssertionError(f"fresh session unexpectedly had Cache residue: {caches!r}")
    if indexed_db is not None:
        raise AssertionError(f"fresh session unexpectedly had IndexedDB residue: {indexed_db!r}")
    return {
        "serviceWorkerRegistrations": registrations,
        "cacheNames": caches,
        "indexedDb": indexed_db,
    }


def _session_profile_marker(engine: str, driver: Any) -> str | None:
    if engine != "firefox":
        return None
    profile = driver.capabilities.get("moz:profile")
    return str(profile) if profile else None


def _run_case(
    engine: str,
    port: int,
    transport: _DriverTransport,
    progress: _ExecutionProgress,
) -> tuple[BrowserIdentity, CaseResult, dict[str, Any]]:
    session_ids: list[str] = []
    firefox_profiles: list[str] = []

    with _browser_session(transport, "clean", progress) as clean:
        progress.enter("clean:configure")
        _configure_driver(clean)
        progress.enter("clean:browser-identity")
        identity = _browser_identity(engine, clean)
        progress.browser_identity = identity
        session_ids.append(str(clean.session_id))
        marker = _session_profile_marker(engine, clean)
        if marker:
            firefox_profiles.append(marker)
        progress.enter("clean:set-selected-state")
        _set_selected_state(clean, port)
        progress.enter("clean:project-selected-state")
        baseline = _project_selected_state(clean, port)
        progress.enter("clean:assert-excluded-state")
        clean_excluded = _assert_clean_excluded_state(clean, port)
        progress.enter("clean:read-controlled-resource")
        clean_resource = _read_controlled_resource(clean, port)
        if clean_resource != "network-origin":
            raise AssertionError(f"clean session resource unexpectedly changed: {clean_resource!r}")

    with _browser_session(transport, "residual", progress) as residual:
        progress.enter("residual:configure")
        _configure_driver(residual)
        session_ids.append(str(residual.session_id))
        marker = _session_profile_marker(engine, residual)
        if marker:
            firefox_profiles.append(marker)
        progress.enter("residual:set-selected-state")
        _set_selected_state(residual, port)
        progress.enter("residual:project-selected-before")
        residual_selected_before = _project_selected_state(residual, port)
        if residual_selected_before != baseline:
            raise AssertionError("second session did not begin with identical selected state")
        progress.enter("residual:assert-excluded-state-before")
        residual_clean_before = _assert_clean_excluded_state(residual, port)

        progress.enter("residual:install-service-worker-cache")
        _install_service_worker_and_cache(residual, port)
        progress.enter("residual:seed-indexeddb")
        _seed_indexed_db(residual, port)

        progress.enter("residual:project-selected-after")
        residual_selected_after = _project_selected_state(residual, port)
        if residual_selected_after != baseline:
            raise AssertionError("excluded-state setup unexpectedly changed selected state")
        progress.enter("residual:observe-service-worker")
        residual_registrations = _service_worker_registration_count(residual, port)
        progress.enter("residual:observe-cache")
        residual_caches = _cache_names(residual, port)
        progress.enter("residual:observe-indexeddb")
        residual_idb = _read_indexed_db(residual, port)
        progress.enter("residual:read-controlled-resource")
        residual_resource = _read_controlled_resource(residual, port)

        if residual_registrations < 1:
            raise AssertionError("Service Worker registration residue was not observable")
        if _CACHE_NAME not in residual_caches:
            raise AssertionError(f"controlled Cache residue was not observable: {residual_caches!r}")
        if residual_idb != _DB_VALUE:
            raise AssertionError(f"IndexedDB residual value not observed: {residual_idb!r}")
        if residual_resource != "service-worker-cache":
            raise AssertionError(
                "shipping Service Worker/Cache residue did not materially affect behavior: "
                f"{residual_resource!r}"
            )

    with _browser_session(transport, "recreated", progress) as recreated:
        progress.enter("recreated:configure")
        _configure_driver(recreated)
        session_ids.append(str(recreated.session_id))
        marker = _session_profile_marker(engine, recreated)
        if marker:
            firefox_profiles.append(marker)
        progress.enter("recreated:set-selected-state")
        _set_selected_state(recreated, port)
        progress.enter("recreated:project-selected-state")
        recreated_selected = _project_selected_state(recreated, port)
        if recreated_selected != baseline:
            raise AssertionError("recreated session changed selected baseline")
        progress.enter("recreated:assert-excluded-state")
        recreated_excluded = _assert_clean_excluded_state(recreated, port)
        progress.enter("recreated:read-controlled-resource")
        recreated_resource = _read_controlled_resource(recreated, port)
        if recreated_resource != "network-origin":
            raise AssertionError("Service Worker/Cache residue crossed the fresh session boundary")

    progress.enter("verify:distinct-webdriver-sessions")
    distinct_sessions = len(set(session_ids)) == 3
    if not distinct_sessions:
        raise AssertionError(f"expected three distinct WebDriver sessions, got {session_ids!r}")

    firefox_profiles_distinct: bool | None = None
    if engine == "firefox":
        progress.enter("verify:distinct-firefox-profiles")
        firefox_profiles_distinct = len(firefox_profiles) == 3 and len(set(firefox_profiles)) == 3
        if not firefox_profiles_distinct:
            raise AssertionError("geckodriver did not expose three distinct temporary profile paths")

    progress.enter("complete")
    details = {
        "evidenceScope": "shipping-product-native-webdriver",
        "selectedStateBaseline": baseline,
        "selectedStateEqualBeforeExcludedMutation": True,
        "selectedStateEqualAfterExcludedMutation": True,
        "cleanSessionExcludedState": clean_excluded,
        "residualSessionCleanBeforeMutation": residual_clean_before,
        "residualServiceWorkerRegistrations": residual_registrations,
        "residualCacheNames": residual_caches,
        "residualIndexedDbValue": residual_idb,
        "residualControlledResource": residual_resource,
        "recreatedSessionExcludedState": recreated_excluded,
        "recreatedControlledResource": recreated_resource,
        "webDriverSessionsDistinct": distinct_sessions,
        "firefoxTemporaryProfilesDistinct": firefox_profiles_distinct,
        "noninterferenceStrategyProven": (
            "quit contaminated native WebDriver session; create a new browser automation session; "
            "materialize selected Browser-v0.1 state only"
        ),
        "selectedStateEqualityProvedExcludedEquivalence": False,
        "fullBae011EngineFamilyEvidenceProven": True,
        "closureRequired": None,
        "protocolDisposition": (
            "Browser v0.1 restore must establish an equivalent isolation boundary or fail closed when "
            "Scenario behavior materially depends on excluded browser state"
        ),
    }
    return identity, CaseResult(case_id="BAE-011", status="pass", details=details), {
        "sessionCount": 3,
        "distinctSessionIds": distinct_sessions,
        "firefoxTemporaryProfilesDistinct": firefox_profiles_distinct,
    }


def _fallback_identity(engine: str) -> BrowserIdentity:
    return BrowserIdentity(
        engine_family=_engine_family(engine),
        product=_product_name(engine),
        browser_version="unknown",
        driver_version=_driver_version(engine),
        platform_name=None,
        runner_os=os.environ.get("RUNNER_OS"),
        runner_arch=os.environ.get("RUNNER_ARCH"),
        runner_image_os=os.environ.get("ImageOS"),
        runner_image_version=os.environ.get("ImageVersion"),
    )


def _diagnostic_tail(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    try:
        value = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return value[-_DIAGNOSTIC_TAIL_LIMIT:] or None


def _safari_diagnostic_tails(progress: _ExecutionProgress) -> dict[str, str]:
    tails: dict[str, str] = {}
    for role, path in progress.safari_diagnostic_logs.items():
        tail = _diagnostic_tail(path)
        if tail:
            tails[role] = tail
    return tails


def run(engine: str, output: Path) -> int:
    try:
        import selenium  # noqa: F401 - dependency availability check
    except ImportError as exc:
        raise RuntimeError(
            "Selenium is required only for shipping/native Browser acceptance evidence"
        ) from exc

    progress = _ExecutionProgress()
    safari_diagnostic_dir = output.parent / f"{output.stem}-safaridriver"

    with _fixture_server() as port:
        try:
            transport = _DriverTransport(
                engine,
                progress,
                safari_diagnostic_dir=safari_diagnostic_dir,
            )
            identity, case, semantic_session_evidence = _run_case(
                engine,
                port,
                transport,
                progress,
            )
            session_evidence = {
                **semantic_session_evidence,
                **progress.transport_evidence(),
            }
        except Exception as exc:
            progress.capture_failure()
            identity = progress.browser_identity or _fallback_identity(engine)
            details: dict[str, Any] = {
                "error_type": type(exc).__name__,
                "error": str(exc),
                "failureStage": progress.failure_stage or progress.current_stage,
                **progress.transport_evidence(),
            }
            diagnostic_tails = _safari_diagnostic_tails(progress)
            if diagnostic_tails:
                details["safariDriverDiagnosticTails"] = diagnostic_tails
            case = CaseResult(
                case_id="BAE-011",
                status="fail",
                details=details,
            )
            session_evidence = progress.transport_evidence()

    document = {
        "schema": "avp-browser-shipping-residual-evidence-v0.1",
        "fixtureRevision": _FIXTURE_REVISION,
        "repositorySha": os.environ.get("GITHUB_SHA"),
        "transport": {
            "name": "selenium-python",
            "version": package_version("selenium"),
            "protocol": "W3C WebDriver",
            "authority": "test-transport-only",
        },
        "browserIdentity": asdict(identity),
        "execution": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "requestedEngine": engine,
            "host": _HOST,
            "nonDefaultPrivacyFlagsOrPrefsAddedByAvp": [],
            "headlessRequestedByAvp": False,
            "sessionIsolation": session_evidence,
            "safariNativeAutomationIsolation": engine == "safari",
            "safariDriverServiceStrategy": (
                "one-service-generation-per-session" if engine == "safari" else None
            ),
        },
        "cases": [asdict(case)],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")

    print(
        json.dumps(
            {
                "engine": identity.engine_family,
                "product": identity.product,
                "browserVersion": identity.browser_version,
                "case": {"id": case.case_id, "status": case.status},
            },
            indent=2,
        )
    )
    return 1 if case.status == "fail" else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=("chrome", "firefox", "safari"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return run(args.engine, args.output)


if __name__ == "__main__":
    raise SystemExit(main())

"""Execute BAE-006 against shipping browser products through native WebDriver.

This runner is non-normative Alpha 3 acceptance infrastructure. It observes the
same third-party localStorage relationship as ``cookie_partition_evidence_runner``
but deliberately changes the transport/build under test:

- branded Google Chrome + ChromeDriver;
- shipping Mozilla Firefox + geckodriver;
- Safari + Apple's safaridriver.

The browser product, driver, runner image, automation profile, and observed
storage model are evidence metadata. None of them become AVP state identity.
The portable disposition remains: if tuple origin is not proven to be the
complete selected unpartitioned storage identity, Browser v0.1 projection must
not flatten additional partition dimensions into tuple-origin state.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any, Iterator

_FIXTURE_REVISION = "browser-shipping-partition-evidence-v0.1"
_FIRST_PARTY = "a.test"
_TOP_LEVEL_ONE = "b.test"
_TOP_LEVEL_TWO = "c.test"
_FIREFOX_PARTITION_PREF = "network.cookie.cookieBehavior"


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


class _FixtureHandler(BaseHTTPRequestHandler):
    server_version = "AVPBrowserShippingPartitionEvidence/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        self._send(
            b"<!doctype html><meta charset=utf-8><title>AVP Shipping Partition Evidence</title>",
            content_type="text/html; charset=utf-8",
        )

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, body: bytes, *, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
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


def _url(host: str, port: int) -> str:
    return f"http://{host}:{port}/"


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


def _create_driver(engine: str) -> Any:
    from selenium import webdriver

    if engine == "chrome":
        from selenium.webdriver.chrome.service import Service

        executable = _resolve_driver_binary("chromedriver", "CHROMEWEBDRIVER")
        if not executable:
            raise RuntimeError("ChromeDriver was not found in PATH or CHROMEWEBDRIVER")
        options = webdriver.ChromeOptions()
        # Do not inject privacy/storage feature flags. Xvfb supplies the display,
        # so the branded browser is not forced into headless mode either.
        return webdriver.Chrome(service=Service(executable_path=executable), options=options)

    if engine == "firefox":
        from selenium.webdriver.firefox.service import Service

        executable = _resolve_driver_binary("geckodriver", "GECKOWEBDRIVER")
        if not executable:
            raise RuntimeError("geckodriver was not found in PATH or GECKOWEBDRIVER")
        options = webdriver.FirefoxOptions()
        # Do not override network.cookie.cookieBehavior or related privacy prefs.
        return webdriver.Firefox(service=Service(executable_path=executable), options=options)

    if engine == "safari":
        from selenium.webdriver.safari.service import Service

        executable = "/usr/bin/safaridriver"
        if not Path(executable).exists():
            raise RuntimeError("/usr/bin/safaridriver is unavailable on this runner")
        return webdriver.Safari(service=Service(executable_path=executable))

    raise ValueError(f"unsupported engine: {engine}")


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
    return _command_version("/usr/bin/safaridriver", "--version")


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


def _firefox_partition_pref_evidence(driver: Any) -> dict[str, Any]:
    profile = driver.capabilities.get("moz:profile")
    result: dict[str, Any] = {
        "profilePathExposed": bool(profile),
        "controlledPreference": _FIREFOX_PARTITION_PREF,
        "observedValues": [],
        "forcedSharedUnpartitionedValueObserved": False,
    }
    if not profile:
        return result

    pattern = re.compile(
        rf'user_pref\("{re.escape(_FIREFOX_PARTITION_PREF)}",\s*([^\)]+)\);'
    )
    values: list[str] = []
    for filename in ("user.js", "prefs.js"):
        path = Path(profile) / filename
        if not path.exists():
            continue
        for match in pattern.finditer(path.read_text(encoding="utf-8", errors="replace")):
            values.append(match.group(1).strip())
    result["observedValues"] = sorted(set(values))
    result["forcedSharedUnpartitionedValueObserved"] = "4" in values
    return result


def _attach_third_party_frame(driver: Any, port: int) -> None:
    from selenium.webdriver.common.by import By

    driver.execute_async_script(
        """
        const [url, done] = arguments;
        const frame = document.createElement('iframe');
        frame.src = url;
        frame.onload = () => done(true);
        frame.onerror = () => done(false);
        document.body.appendChild(frame);
        """,
        _url(_FIRST_PARTY, port),
    )
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    if len(frames) != 1:
        raise AssertionError(f"expected one third-party frame, got {len(frames)}")
    driver.switch_to.frame(frames[0])


def _third_party_storage(driver: Any, operation: str, value: str | None = None) -> dict[str, Any]:
    try:
        return driver.execute_script(
            """
            const [operation, value] = arguments;
            try {
              if (operation === 'write') {
                localStorage.setItem('partition_probe', value);
                return {kind: 'ok', value: localStorage.getItem('partition_probe')};
              }
              return {kind: 'ok', value: localStorage.getItem('partition_probe')};
            } catch (error) {
              return {kind: 'blocked', name: error.name, message: String(error.message)};
            }
            """,
            operation,
            value,
        )
    finally:
        driver.switch_to.default_content()


def _case_bae_006(engine: str, driver: Any, port: int) -> CaseResult:
    driver.get(_url(_TOP_LEVEL_ONE, port))
    _attach_third_party_frame(driver, port)
    first = _third_party_storage(driver, "write", "under-b")

    driver.get(_url(_TOP_LEVEL_TWO, port))
    _attach_third_party_frame(driver, port)
    second = _third_party_storage(driver, "read")

    if first["kind"] == "blocked" or second["kind"] == "blocked":
        model = "blocked"
        base_status = "pass"
        disposition = (
            "shipping automation context restricts third-party storage; Browser v0.1 must not invent "
            "tuple-origin state for the unavailable dependency"
        )
    elif second.get("value") != "under-b":
        model = "partitioned"
        base_status = "pass"
        disposition = (
            "same third-party tuple origin does not expose one shared bucket across top-level sites; "
            "Browser v0.1 must not flatten the observed partition dimension"
        )
    else:
        model = "shared-unpartitioned"
        base_status = "partial"
        disposition = (
            "this exact shipping automation execution exposed shared unpartitioned third-party "
            "localStorage; that observation does not prove tuple origin is universally complete"
        )

    transport_policy: dict[str, Any] = {
        "customPrivacyFlagsOrPrefsInjectedByAvp": False,
        "headlessRequestedByAvp": False,
    }
    status = base_status
    closure_required: str | None = None

    if engine == "firefox":
        firefox_prefs = _firefox_partition_pref_evidence(driver)
        transport_policy["firefoxAutomationProfile"] = firefox_prefs
        if firefox_prefs["forcedSharedUnpartitionedValueObserved"]:
            status = "partial"
            closure_required = (
                "geckodriver automation profile explicitly forced network.cookie.cookieBehavior=4; "
                "this execution cannot close shipping partition-policy evidence"
            )

    if status == "partial" and closure_required is None:
        closure_required = (
            "shipping/default partition identity remains unproven for this exact execution; retain "
            "Browser v0.1 fail-closed admission unless another independently reviewable proof closes it"
        )

    return CaseResult(
        case_id="BAE-006",
        status=status,
        details={
            "evidenceScope": "shipping-product-native-webdriver",
            "observed_storage_model": model,
            "top_level_b_result": first,
            "top_level_c_result": second,
            "transportPolicy": transport_policy,
            "base_profile_disposition": disposition,
            "closure_required": closure_required,
            "vendor_partition_key_used_as_avp_identity": False,
        },
    )


def run(engine: str, output: Path) -> int:
    try:
        import selenium  # noqa: F401 - dependency availability check
    except ImportError as exc:
        raise RuntimeError(
            "Selenium is required only for shipping/native Browser acceptance evidence"
        ) from exc

    with _fixture_server() as port:
        driver = _create_driver(engine)
        try:
            driver.set_page_load_timeout(20)
            identity = _browser_identity(engine, driver)
            try:
                case = _case_bae_006(engine, driver, port)
            except Exception as exc:
                case = CaseResult(
                    case_id="BAE-006",
                    status="fail",
                    details={"error_type": type(exc).__name__, "error": str(exc)},
                )
            capabilities = {
                key: value
                for key, value in driver.capabilities.items()
                if key
                in {
                    "browserName",
                    "browserVersion",
                    "platformName",
                    "acceptInsecureCerts",
                    "moz:geckodriverVersion",
                    "moz:headless",
                    "safari:automaticInspection",
                    "safari:automaticProfiling",
                }
            }
        finally:
            driver.quit()

    document = {
        "schema": "avp-browser-shipping-partition-evidence-v0.1",
        "fixtureRevision": _FIXTURE_REVISION,
        "repositorySha": os.environ.get("GITHUB_SHA"),
        "transport": {
            "name": "selenium-python",
            "version": package_version("selenium"),
            "protocol": "W3C WebDriver",
            "authority": "test-transport-only",
        },
        "browserIdentity": asdict(identity),
        "capabilities": capabilities,
        "execution": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "requestedEngine": engine,
            "hosts": [_FIRST_PARTY, _TOP_LEVEL_ONE, _TOP_LEVEL_TWO],
            "nonDefaultPrivacyFlagsOrPrefsAddedByAvp": [],
            "headlessRequestedByAvp": False,
            "safariNativeAutomationIsolation": engine == "safari",
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

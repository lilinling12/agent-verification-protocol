"""Execute shipping cookie-fidelity boundary evidence for AEP-0011.

This Alpha 3 runner is non-normative acceptance infrastructure. It deliberately
separates three questions that must not be collapsed into one provider result:

1. browser-observable HTTP behavior (host-only/domain and SameSite delivery);
2. state fields exposed by the native W3C WebDriver cookie transport; and
3. the AVP decision at a lossless projection / temporal restore boundary.

A shipping browser behaving correctly does not make a lossy WebDriver cookie
object lossless. Conversely, transport insufficiency is not a browser failure:
the AVP evidence decision must fail closed rather than infer ``hostOnly``,
normalize ``SameSite=Default`` to Lax, or manufacture historical creation time.
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
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any, Iterator

_FIXTURE_REVISION = "browser-shipping-cookie-fidelity-evidence-v0.1"
_HOST = "a.test"
_SUBDOMAIN = "sub.a.test"
_CROSS_SITE = "b.test"
_REQUIRED_COOKIE_IDENTITY_FIELDS = ("name", "domain", "hostOnly", "path")
_TEMPORAL_SCENARIO_POLICY = "creation-time-sensitive-cookie-behavior-material"


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
    server_version = "AVPBrowserShippingCookieFidelityEvidence/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        path = self.path.split("?", 1)[0]
        if path == "/set-host-only":
            self._send(
                b"host-only seeded",
                headers=(("Set-Cookie", "host_only=1; Path=/; SameSite=Lax"),),
            )
            return
        if path == "/set-domain":
            self._send(
                b"domain seeded",
                headers=(("Set-Cookie", "domain_scoped=1; Domain=a.test; Path=/; SameSite=Lax"),),
            )
            return
        if path == "/set-samesite":
            self._send(
                b"samesite seeded",
                headers=(
                    ("Set-Cookie", "default_site=1; Path=/"),
                    ("Set-Cookie", "explicit_lax=1; Path=/; SameSite=Lax"),
                ),
            )
            return
        if path == "/cross-site-post":
            port = self.server.server_address[1]
            body = f"""<!doctype html><meta charset=utf-8>
<form id=p method=post action=http://{_HOST}:{port}/echo-post></form>
<script>document.getElementById('p').submit()</script>
""".encode("utf-8")
            self._send(body, content_type="text/html; charset=utf-8")
            return
        if path == "/echo-cookies":
            self._send(self.headers.get("Cookie", "").encode("utf-8"))
            return
        self._send(
            b"<!doctype html><meta charset=utf-8><title>AVP Cookie Fidelity Evidence</title>",
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


def _url(host: str, port: int, path: str = "/") -> str:
    return f"http://{host}:{port}{path}"


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
        return webdriver.Chrome(service=Service(executable_path=executable), options=webdriver.ChromeOptions())

    if engine == "firefox":
        from selenium.webdriver.firefox.service import Service

        executable = _resolve_driver_binary("geckodriver", "GECKOWEBDRIVER")
        if not executable:
            raise RuntimeError("geckodriver was not found in PATH or GECKOWEBDRIVER")
        return webdriver.Firefox(service=Service(executable_path=executable), options=webdriver.FirefoxOptions())

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
    return {"chrome": "Google Chrome", "firefox": "Mozilla Firefox", "safari": "Safari"}[engine]


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


def _configure_driver(driver: Any) -> None:
    driver.set_page_load_timeout(20)
    driver.set_script_timeout(20)


def _clear_cookies(driver: Any, port: int) -> None:
    driver.get(_url(_HOST, port))
    driver.delete_all_cookies()


def _cookie_map(driver: Any) -> dict[str, dict[str, Any]]:
    return {str(cookie.get("name")): cookie for cookie in driver.get_cookies()}


def _transport_cookie_field_summary(cookies: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keys = sorted({key for cookie in cookies.values() for key in cookie})
    return {
        "cookieObjectKeys": keys,
        "hostOnlyFieldExposed": "hostOnly" in keys,
        "creationTimeFieldExposed": any(key in keys for key in ("creationTime", "creation-time")),
        "requiredIdentityFields": list(_REQUIRED_COOKIE_IDENTITY_FIELDS),
    }


def _case_bae_001(driver: Any, port: int) -> CaseResult:
    _clear_cookies(driver, port)
    driver.get(_url(_HOST, port, "/set-host-only"))
    driver.get(_url(_HOST, port, "/set-domain"))

    cookies = _cookie_map(driver)
    selected = {
        name: cookies[name]
        for name in ("host_only", "domain_scoped")
        if name in cookies
    }
    if set(selected) != {"host_only", "domain_scoped"}:
        raise AssertionError(f"expected controlled cookies, got {sorted(selected)}")

    driver.get(_url(_SUBDOMAIN, port, "/echo-cookies"))
    echoed = str(driver.execute_script("return document.body.textContent || '';"))
    if "host_only=1" in echoed:
        raise AssertionError("host-only cookie leaked to qualifying subdomain")
    if "domain_scoped=1" not in echoed:
        raise AssertionError("domain-scoped cookie was not sent to qualifying subdomain")

    field_summary = _transport_cookie_field_summary(selected)
    host_only_exposed = bool(field_summary["hostOnlyFieldExposed"])
    positive_projection_available = host_only_exposed and all(
        isinstance(selected[name].get("hostOnly"), bool)
        for name in ("host_only", "domain_scoped")
    )

    # Domain presentation is diagnostic only. Leading dots, exact host text, or
    # another convenience serialization MUST NOT stand in for hostOnly.
    projection_accepted = positive_projection_available
    fail_closed_enforced = not positive_projection_available and not projection_accepted

    return CaseResult(
        case_id="BAE-001",
        status="pass" if positive_projection_available else "partial",
        details={
            "behavioralDistinctionProven": True,
            "subdomainCookieHeader": echoed,
            "transportCookieFields": field_summary,
            "transportCookieObjects": selected,
            "domainTextUsedToInferHostOnly": False,
            "positiveLosslessProjectionAvailable": positive_projection_available,
            "projectionAccepted": projection_accepted,
            "failClosedOnMissingHostOnly": fail_closed_enforced,
            "closureRequired": (
                None
                if positive_projection_available
                else "an independently reviewable positive hostOnly projection mechanism remains required before selected cookies can be positively projected through this transport"
            ),
        },
    )


def _case_bae_002(driver: Any, port: int) -> CaseResult:
    _clear_cookies(driver, port)
    driver.get(_url(_HOST, port, "/set-samesite"))
    cookies = _cookie_map(driver)
    selected = {
        name: cookies[name]
        for name in ("default_site", "explicit_lax")
        if name in cookies
    }
    if set(selected) != {"default_site", "explicit_lax"}:
        raise AssertionError(f"expected SameSite fixture cookies, got {sorted(selected)}")

    default_reported = selected["default_site"].get("sameSite")
    lax_reported = selected["explicit_lax"].get("sameSite")
    default_token_exposed = str(default_reported).lower() == "default"
    explicit_lax_exposed = str(lax_reported).lower() == "lax"
    stored_state_distinguished = default_token_exposed and explicit_lax_exposed

    projection_accepted = stored_state_distinguished
    fail_closed_enforced = not stored_state_distinguished and not projection_accepted

    return CaseResult(
        case_id="BAE-002",
        status="pass" if stored_state_distinguished else "partial",
        details={
            "transportReportedSameSite": {
                "default_site": default_reported,
                "explicit_lax": lax_reported,
            },
            "transportExposesStoredDefaultToken": default_token_exposed,
            "transportExposesExplicitLaxToken": explicit_lax_exposed,
            "storedDefaultVersusLaxDistinguished": stored_state_distinguished,
            "defaultNormalizedToLaxByAvp": False,
            "projectionAccepted": projection_accepted,
            "failClosedOnUnprovenStoredSameSite": fail_closed_enforced,
            "closureRequired": (
                None
                if stored_state_distinguished
                else "a positive stored SameSite=Default evidence path remains required for selected Default cookies; AVP must not normalize the transport result to Lax"
            ),
        },
    )


def _case_bae_003(driver: Any, port: int) -> CaseResult:
    from selenium.webdriver.support.ui import WebDriverWait

    _clear_cookies(driver, port)
    driver.get(_url(_HOST, port, "/set-samesite"))
    cookies = _cookie_map(driver)
    selected = {
        name: cookies[name]
        for name in ("default_site", "explicit_lax")
        if name in cookies
    }
    if set(selected) != {"default_site", "explicit_lax"}:
        raise AssertionError(f"expected temporal fixture cookies, got {sorted(selected)}")

    field_summary = _transport_cookie_field_summary(selected)
    creation_time_exposed = bool(field_summary["creationTimeFieldExposed"])
    default_state_exposed = str(selected["default_site"].get("sameSite")).lower() == "default"

    driver.get(_url(_CROSS_SITE, port, "/cross-site-post"))
    expected_fragment = f"{_HOST}:{port}/echo-post"
    WebDriverWait(driver, 10).until(lambda current: expected_fragment in current.current_url)
    echoed = str(driver.execute_script("return document.body.textContent || '';"))

    default_sent = "default_site=1" in echoed
    explicit_lax_sent = "explicit_lax=1" in echoed
    if explicit_lax_sent:
        raise AssertionError("explicit SameSite=Lax cookie was sent on controlled cross-site unsafe POST")

    # The materialized acceptance fixture explicitly declares historical
    # creation-time-sensitive behavior material. If creation time is absent, a
    # field-equal fresh cookie can never self-certify STATE_EQUIVALENT restore.
    temporal_behavior_material = True
    eligibility = not temporal_behavior_material or (
        creation_time_exposed and default_state_exposed
    )
    if eligibility:
        # This runner has no positive historical creation-time restoration
        # mechanism. A true result here would overstate the evidence boundary.
        raise AssertionError("temporal-sensitive restore was incorrectly considered eligible")

    return CaseResult(
        case_id="BAE-003",
        status="pass",
        details={
            "freshDefaultSentOnCrossSiteUnsafePost": default_sent,
            "explicitLaxSentOnCrossSiteUnsafePost": explicit_lax_sent,
            "optionalRecentCookieBehaviorObserved": default_sent,
            "scenarioTemporalPolicy": _TEMPORAL_SCENARIO_POLICY,
            "creationTimeExposedByTransport": creation_time_exposed,
            "storedDefaultTokenExposedByTransport": default_state_exposed,
            "historicalCreationTimePreservedOrProvenEquivalent": False,
            "freshFieldEqualCookieSelfCertifiesEquivalent": False,
            "restoreEligible": False,
            "failClosedTemporalEligibilityProven": True,
            "disposition": (
                "controlled temporal-sensitive restore is rejected because historical creation-time behavior is not preserved/proven; fresh Default behavior is diagnostic only"
            ),
        },
    )


def run(engine: str, output: Path) -> int:
    try:
        import selenium  # noqa: F401 - dependency availability check
    except ImportError as exc:
        raise RuntimeError("Selenium is required only for shipping cookie evidence") from exc

    with _fixture_server() as port:
        driver = _create_driver(engine)
        try:
            _configure_driver(driver)
            identity = _browser_identity(engine, driver)
            cases: list[CaseResult] = []
            for case in (_case_bae_001, _case_bae_002, _case_bae_003):
                try:
                    cases.append(case(driver, port))
                except Exception as exc:
                    cases.append(
                        CaseResult(
                            case_id=case.__name__.replace("_case_bae_", "BAE-").replace("_", "-"),
                            status="fail",
                            details={"error_type": type(exc).__name__, "error": str(exc)},
                        )
                    )
        finally:
            driver.quit()

    document = {
        "schema": "avp-browser-shipping-cookie-fidelity-evidence-v0.1",
        "fixtureRevision": _FIXTURE_REVISION,
        "repositorySha": os.environ.get("GITHUB_SHA"),
        "transport": {
            "name": "selenium-python",
            "version": package_version("selenium"),
            "protocol": "W3C WebDriver Classic cookie commands",
            "authority": "test-transport-only",
            "knownStandardBoundary": {
                "hostOnlyInClassicCookieType": False,
                "creationTimeInClassicCookieType": False,
                "sameSiteDefaultPortablyGuaranteedByClassic": False,
            },
        },
        "browserIdentity": asdict(identity),
        "execution": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "requestedEngine": engine,
            "hosts": [_HOST, _SUBDOMAIN, _CROSS_SITE],
            "nonDefaultCookiePolicyFlagsOrPrefsAddedByAvp": [],
            "headlessRequestedByAvp": False,
        },
        "cases": [asdict(case) for case in cases],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")

    failures = [case.case_id for case in cases if case.status == "fail"]
    partials = [case.case_id for case in cases if case.status == "partial"]
    print(
        json.dumps(
            {
                "product": identity.product,
                "browserVersion": identity.browser_version,
                "failures": failures,
                "partials": partials,
            },
            indent=2,
        )
    )
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=("chrome", "firefox", "safari"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return run(args.engine, args.output)


if __name__ == "__main__":
    raise SystemExit(main())

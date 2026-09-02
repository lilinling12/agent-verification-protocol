"""Shipping provenance-complete cookie evidence for AEP-0011.

Non-normative Alpha 3 acceptance infrastructure. Native WebDriver observes
current state only; evaluator/control-owned provenance establishes required
cookie fields that lossy transports omit. Missing, stale, ambiguous, or
inconsistent provenance fails closed. Provenance is Evidence, not portable
BrowserStateImage identity and not provider serialization.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

_FIXTURE_REVISION = "browser-shipping-cookie-provenance-evidence-v0.1"
_HOST = "a.test"
_SUBDOMAIN = "sub.a.test"
_BASE_STORAGE = {"alpha": "1", "beta": "2"}
_ALLOWED_SAMESITE = {"Default", "Lax", "Strict", "None"}


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    status: str
    details: dict[str, Any]


@dataclass(frozen=True, slots=True)
class CookieProvenance:
    name: str
    value: str
    domain: str
    host_only: bool
    path: str
    secure: bool
    http_only: bool
    same_site: str
    persistent: bool
    expiry: int | None
    source: str
    revision: int


def _record(name: str, value: str, *, host_only: bool = True, same_site: str = "Lax", revision: int = 1, source: str = "controlled Set-Cookie") -> CookieProvenance:
    return CookieProvenance(
        name=name,
        value=value,
        domain=_HOST,
        host_only=host_only,
        path="/",
        secure=False,
        http_only=False,
        same_site=same_site,
        persistent=False,
        expiry=None,
        source=source,
        revision=revision,
    )


class _Handler(BaseHTTPRequestHandler):
    server_version = "AVPBrowserShippingCookieProvenanceEvidence/0.1"

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        headers: tuple[tuple[str, str], ...] = ()
        if path == "/seed-identity":
            headers = (
                ("Set-Cookie", "host_only=1; Path=/; SameSite=Lax"),
                ("Set-Cookie", "domain_scoped=1; Domain=a.test; Path=/; SameSite=Lax"),
            )
        elif path == "/seed-samesite":
            headers = (
                ("Set-Cookie", "default_site=1; Path=/"),
                ("Set-Cookie", "explicit_lax=1; Path=/; SameSite=Lax"),
            )
        elif path == "/seed-lifecycle":
            headers = (("Set-Cookie", "lifecycle=baseline; Path=/; SameSite=Lax"),)
        elif path == "/mutate-lifecycle":
            headers = (
                ("Set-Cookie", "lifecycle=mutated; Path=/; SameSite=Lax"),
                ("Set-Cookie", "extra=1; Path=/; SameSite=Lax"),
            )
        elif path == "/restore-lifecycle":
            headers = (
                ("Set-Cookie", "lifecycle=baseline; Path=/; SameSite=Lax"),
                ("Set-Cookie", "extra=; Path=/; Max-Age=0; SameSite=Lax"),
            )
        elif path == "/seed-untracked":
            headers = (("Set-Cookie", "untracked=1; Path=/; SameSite=Lax"),)
        elif path == "/echo-cookies":
            self._send(self.headers.get("Cookie", "").encode())
            return
        self._send(b"ok", headers=headers)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, body: bytes, headers: tuple[tuple[str, str], ...] = ()) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass


@contextmanager
def _server() -> Iterator[int]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
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


def _binary(command: str, env_name: str) -> str | None:
    found = shutil.which(command)
    if found:
        return found
    configured = os.environ.get(env_name)
    if not configured:
        return None
    path = Path(configured)
    if path.is_dir():
        path /= command
    return str(path) if path.exists() else None


def _version(*command: str) -> str | None:
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return (result.stdout or result.stderr).strip() or None


def _driver(engine: str) -> Any:
    from selenium import webdriver
    if engine == "chrome":
        from selenium.webdriver.chrome.service import Service
        executable = _binary("chromedriver", "CHROMEWEBDRIVER")
        if not executable:
            raise RuntimeError("chromedriver unavailable")
        return webdriver.Chrome(service=Service(executable), options=webdriver.ChromeOptions())
    if engine == "firefox":
        from selenium.webdriver.firefox.service import Service
        executable = _binary("geckodriver", "GECKOWEBDRIVER")
        if not executable:
            raise RuntimeError("geckodriver unavailable")
        return webdriver.Firefox(service=Service(executable), options=webdriver.FirefoxOptions())
    from selenium.webdriver.safari.service import Service
    if not Path("/usr/bin/safaridriver").exists():
        raise RuntimeError("safaridriver unavailable")
    return webdriver.Safari(service=Service("/usr/bin/safaridriver"))


def _identity(engine: str, driver: Any) -> dict[str, Any]:
    family = {"chrome": "chromium", "firefox": "gecko", "safari": "webkit"}[engine]
    product = {"chrome": "Google Chrome", "firefox": "Mozilla Firefox", "safari": "Safari"}[engine]
    if engine == "chrome":
        executable = _binary("chromedriver", "CHROMEWEBDRIVER")
        driver_version = _version(executable, "--version") if executable else None
    elif engine == "firefox":
        executable = _binary("geckodriver", "GECKOWEBDRIVER")
        driver_version = _version(executable, "--version") if executable else None
    else:
        driver_version = _version("/usr/bin/safaridriver", "--version")
    return {
        "engine_family": family,
        "product": product,
        "browser_version": str(driver.capabilities.get("browserVersion", "unknown")),
        "driver_version": driver_version,
        "platform_name": driver.capabilities.get("platformName"),
        "runner_os": os.environ.get("RUNNER_OS"),
        "runner_arch": os.environ.get("RUNNER_ARCH"),
        "runner_image_os": os.environ.get("ImageOS"),
        "runner_image_version": os.environ.get("ImageVersion"),
    }


def _reset(driver: Any, port: int) -> None:
    driver.get(_url(_HOST, port, "/state"))
    driver.delete_all_cookies()
    driver.execute_script("localStorage.clear();")


def _cookies(driver: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in driver.get_cookies()]


def _digest(records: Sequence[CookieProvenance]) -> str:
    raw = json.dumps([asdict(r) for r in sorted(records, key=lambda r: r.name)], sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _project(cookies: Sequence[Mapping[str, Any]], records: Sequence[CookieProvenance]) -> dict[str, Any]:
    for record in records:
        if not record.domain or not record.path.startswith("/") or record.same_site not in _ALLOWED_SAMESITE:
            raise ValueError(f"incomplete provenance for {record.name}")
        if record.persistent != (record.expiry is not None):
            raise ValueError(f"persistence provenance mismatch for {record.name}")
    by_name = {record.name: record for record in records}
    names = [str(cookie.get("name")) for cookie in cookies]
    if len(by_name) != len(records) or len(set(names)) != len(names):
        raise ValueError("ambiguous provenance/current state")
    if set(names) != set(by_name):
        raise ValueError("provenance/current complete-set mismatch")
    result = []
    for cookie in cookies:
        record = by_name[str(cookie.get("name"))]
        observable = (
            cookie.get("value") == record.value
            and cookie.get("path") == record.path
            and bool(cookie.get("secure", False)) == record.secure
            and bool(cookie.get("httpOnly", False)) == record.http_only
        )
        if not observable:
            raise ValueError(f"current state contradicts provenance for {record.name}")
        result.append({
            "name": record.name,
            "value": record.value,
            "domain": record.domain,
            "hostOnly": record.host_only,
            "path": record.path,
            "secure": record.secure,
            "httpOnly": record.http_only,
            "sameSite": record.same_site,
            "persistent": record.persistent,
            "expiry": record.expiry,
        })
    result.sort(key=lambda item: (item["domain"], item["path"], item["name"], item["hostOnly"]))
    return {"cookies": result, "provenanceDigest": _digest(records)}


def _storage(driver: Any) -> dict[str, str]:
    return dict(driver.execute_script("return Object.fromEntries(Array.from({length:localStorage.length},(_,i)=>localStorage.key(i)).sort().map(k=>[k,localStorage.getItem(k)]));"))


def _set_storage(driver: Any, state: Mapping[str, str]) -> None:
    driver.execute_script("localStorage.clear(); for (const [k,v] of Object.entries(arguments[0])) localStorage.setItem(k,v);", dict(state))


def _image(driver: Any, port: int, records: Sequence[CookieProvenance]) -> dict[str, Any]:
    driver.get(_url(_HOST, port, "/state"))
    projected = _project(_cookies(driver), records)
    return {"cookies": projected["cookies"], "localStorage": _storage(driver), "provenanceDigest": projected["provenanceDigest"]}


def _bae_001(driver: Any, port: int) -> CaseResult:
    _reset(driver, port)
    driver.get(_url(_HOST, port, "/seed-identity"))
    records = (
        _record("host_only", "1", source="Set-Cookie without Domain"),
        _record("domain_scoped", "1", host_only=False, source="Set-Cookie Domain=a.test"),
    )
    projected = _project(_cookies(driver), records)
    identities = {item["name"]: [item["domain"], item["hostOnly"], item["path"]] for item in projected["cookies"]}
    driver.get(_url(_SUBDOMAIN, port, "/echo-cookies"))
    echoed = str(driver.execute_script("return document.body.textContent || '';"))
    if "host_only=1" in echoed or "domain_scoped=1" not in echoed:
        raise AssertionError(f"host-only/domain witness failed: {echoed!r}")
    driver.get(_url(_HOST, port, "/seed-untracked"))
    rejected = False
    try:
        _project(_cookies(driver), records)
    except ValueError:
        rejected = True
    if not rejected:
        raise AssertionError("missing provenance did not fail closed")
    return CaseResult("BAE-001", "pass", {
        "behavioralDistinctionProven": True,
        "positiveHostOnlyProjectionProven": True,
        "projectedIdentities": identities,
        "domainPresentationUsedToInferHostOnly": False,
        "missingProvenanceRejected": True,
        "provenanceDigest": projected["provenanceDigest"],
        "admittedClass": "complete evaluator/control-owned current cookie provenance",
        "outsideAdmittedClassDisposition": "fail-closed",
    })


def _bae_002(driver: Any, port: int) -> CaseResult:
    _reset(driver, port)
    driver.get(_url(_HOST, port, "/seed-samesite"))
    records = (
        _record("default_site", "1", same_site="Default", source="Set-Cookie SameSite omitted"),
        _record("explicit_lax", "1", same_site="Lax", source="Set-Cookie SameSite=Lax"),
    )
    projected = _project(_cookies(driver), records)
    values = {item["name"]: item["sameSite"] for item in projected["cookies"]}
    if values != {"default_site": "Default", "explicit_lax": "Lax"}:
        raise AssertionError(f"stored SameSite provenance changed: {values!r}")
    rejected = False
    try:
        _project(_cookies(driver), (replace(records[0], same_site=""), records[1]))
    except ValueError:
        rejected = True
    if not rejected:
        raise AssertionError("unknown stored SameSite did not fail closed")
    return CaseResult("BAE-002", "pass", {
        "positiveStoredDefaultProjectionProven": True,
        "storedDefaultVersusExplicitLax": values,
        "transportSameSiteUsedAsAuthority": False,
        "defaultNormalizedToLaxByAvp": False,
        "unknownStoredSameSiteRejected": True,
        "provenanceDigest": projected["provenanceDigest"],
    })


def _lifecycle(value: str, revision: int) -> tuple[CookieProvenance, ...]:
    return (_record("lifecycle", value, revision=revision, source="controlled lifecycle Set-Cookie"),)


def _mutated(revision: int) -> tuple[CookieProvenance, ...]:
    return (
        _record("lifecycle", "mutated", revision=revision, source="controlled lifecycle mutation"),
        _record("extra", "1", revision=revision, source="controlled lifecycle mutation"),
    )


def _authoritative(image: Mapping[str, Any]) -> dict[str, Any]:
    return {"cookies": image["cookies"], "localStorage": image["localStorage"]}


def _bae_008_009(driver: Any, port: int) -> tuple[CaseResult, CaseResult]:
    _reset(driver, port)
    driver.get(_url(_HOST, port, "/seed-lifecycle"))
    _set_storage(driver, _BASE_STORAGE)
    baseline = _image(driver, port, _lifecycle("baseline", 1))

    driver.get(_url(_HOST, port, "/mutate-lifecycle"))
    _set_storage(driver, {"alpha": "mutated", "gamma": "3"})
    if _authoritative(_image(driver, port, _mutated(2))) == _authoritative(baseline):
        raise AssertionError("mutation did not change selected state")

    driver.get(_url(_HOST, port, "/restore-lifecycle"))
    _set_storage(driver, _BASE_STORAGE)
    restored = _image(driver, port, _lifecycle("baseline", 3))
    if _authoritative(restored) != _authoritative(baseline):
        raise AssertionError("post-restore independent reprojection mismatch")

    driver.get(_url(_HOST, port, "/mutate-lifecycle"))
    _set_storage(driver, {"alpha": "mutated-again"})
    _image(driver, port, _mutated(4))
    driver.get(_url(_HOST, port, "/restore-lifecycle"))
    _set_storage(driver, _BASE_STORAGE)
    reset = _image(driver, port, _lifecycle("baseline", 5))
    if _authoritative(reset) != _authoritative(baseline):
        raise AssertionError("post-reset independent reprojection mismatch")

    policy = {
        "creationTimeSensitiveBehaviorMaterial": False,
        "cookieHeaderOrderingMaterial": False,
        "selectedCookieSameSite": "Lax",
        "selectedCookieNamesUniqueWithinFixture": True,
    }
    common = {
        "fidelityClaimed": "STATE_EQUIVALENT",
        "exactFidelityClaimed": False,
        "temporalEligibilityPolicy": policy,
        "backendCommandSuccessUsedAsOracle": False,
        "provenanceIsBrowserStateImageIdentity": False,
        "outsideProvenanceCompleteClassDisposition": "fail-closed",
    }
    return (
        CaseResult("BAE-008", "pass", {**common, "independentReprojectionMatched": True, "snapshotProvenanceDigest": baseline["provenanceDigest"], "restoredProvenanceDigest": restored["provenanceDigest"]}),
        CaseResult("BAE-009", "pass", {**common, "immutableBaselineReprojectionMatched": True, "resetProvenanceDigest": reset["provenanceDigest"]}),
    )


def run(engine: str, output: Path) -> int:
    cases: list[CaseResult] = []
    identity: dict[str, Any] = {
        "engine_family": {"chrome": "chromium", "firefox": "gecko", "safari": "webkit"}[engine],
        "product": {"chrome": "Google Chrome", "firefox": "Mozilla Firefox", "safari": "Safari"}[engine],
        "browser_version": "unknown",
    }
    driver = None
    try:
        with _server() as port:
            driver = _driver(engine)
            driver.set_page_load_timeout(20)
            driver.set_script_timeout(20)
            identity = _identity(engine, driver)
            for case in (_bae_001, _bae_002):
                try:
                    cases.append(case(driver, port))
                except Exception as exc:
                    cases.append(CaseResult(case.__name__.replace("_bae_", "BAE-").replace("_", "-"), "fail", {"error_type": type(exc).__name__, "error": str(exc)}))
            try:
                cases.extend(_bae_008_009(driver, port))
            except Exception as exc:
                details = {"error_type": type(exc).__name__, "error": str(exc)}
                cases.extend((CaseResult("BAE-008", "fail", details), CaseResult("BAE-009", "fail", details)))
    except Exception as exc:
        cases = [CaseResult("INFRASTRUCTURE", "fail", {"error_type": type(exc).__name__, "error": str(exc)})]
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

    document = {
        "schema": "avp-browser-shipping-cookie-provenance-evidence-v0.1",
        "fixtureRevision": _FIXTURE_REVISION,
        "repositorySha": os.environ.get("GITHUB_SHA"),
        "browserIdentity": identity,
        "transport": {"name": "selenium-python", "version": package_version("selenium"), "protocol": "W3C WebDriver", "authority": "current-state-observation-only"},
        "provenance": {"authority": "evaluator-control-owned-evidence", "portableStateIdentity": False, "providerSerialization": False, "missingOrAmbiguousDisposition": "fail-closed"},
        "execution": {"platform": platform.platform(), "python": platform.python_version(), "requestedEngine": engine, "headlessRequestedByAvp": False, "nonDefaultPrivacyFlagsOrPrefsAddedByAvp": [], "hosts": [_HOST, _SUBDOMAIN]},
        "cases": [asdict(case) for case in cases],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")
    failures = [case.case_id for case in cases if case.status == "fail"]
    print(json.dumps({"product": identity.get("product"), "browserVersion": identity.get("browser_version"), "cases": {case.case_id: case.status for case in cases}, "failures": failures}, indent=2))
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=("chrome", "firefox", "safari"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return run(args.engine, args.output)


if __name__ == "__main__":
    raise SystemExit(main())

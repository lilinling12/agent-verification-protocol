"""Playwright-backed Browser v0.1 implementation foundation.

Playwright is a concrete implementation transport only. This module keeps
BrowserContext/Page objects private, binds the actual browser build into the
materialized execution identity before provisioning, and reconstructs selected
portable cookie state from current browser observation plus evaluator-owned
provenance when the provider transport is lossy.
"""

from __future__ import annotations

import copy
import itertools
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from avp_ref.environment.models import SnapshotRef
from avp_ref.tck_adapter.browser_harness import (
    BrowserCanonicalizationError,
    BrowserHarnessError,
    BrowserIdentityVerifier,
    BrowserVerificationError,
    MaterializedBrowserFixture,
    canonical_state_image_digest,
    decode_dom_string_code_units,
    encode_dom_string_code_units,
    materialize_browser_fixture,
)

from .driver import sync_playwright_runtime


@dataclass(frozen=True, slots=True)
class CookieProvenance:
    """Evaluator/control evidence for portable cookie facts Playwright may omit."""

    name: str
    value: str
    domain: str
    host_only: bool
    path: str
    persistent: bool
    secure: bool
    http_only: bool
    same_site: str
    expiry_seconds: str | None = None
    expiry_nanoseconds: int | None = None
    source: str = "controlled-playwright-fixture"
    revision: int = 1

    @property
    def identity(self) -> tuple[str, str, bool, str]:
        return self.name, self.domain, self.host_only, self.path

    def portable(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "name": self.name,
            "value": self.value,
            "domain": self.domain,
            "hostOnly": self.host_only,
            "path": self.path,
            "persistent": self.persistent,
            "secure": self.secure,
            "httpOnly": self.http_only,
            "sameSite": self.same_site,
        }
        if self.persistent:
            if self.expiry_seconds is None or self.expiry_nanoseconds is None:
                raise BrowserVerificationError("persistent cookie provenance lacks expiry")
            value["expiry"] = {
                "unixSeconds": self.expiry_seconds,
                "nanoseconds": self.expiry_nanoseconds,
            }
        return value


@dataclass(frozen=True, slots=True)
class _StoredSnapshot:
    image: Mapping[str, Any]
    provenance: tuple[CookieProvenance, ...]


class PlaywrightBrowserIdentityVerifier(BrowserIdentityVerifier):
    """Validate canonical origin/host text with the browser WHATWG URL parser."""

    def __init__(self, browser: Any) -> None:
        self._browser = browser

    def _url_field(self, value: str, field: str) -> str:
        context = self._browser.new_context()
        try:
            page = context.new_page()
            result = page.evaluate(
                "([value, field]) => { const u = new URL(value); return u[field]; }",
                [value, field],
            )
        finally:
            context.close()
        if not isinstance(result, str) or not result:
            raise BrowserCanonicalizationError("browser URL canonicalization returned no value")
        return result

    def verify_canonical_origin(self, origin: str) -> None:
        try:
            canonical = self._url_field(origin, "origin")
        except Exception as exc:
            raise BrowserCanonicalizationError(f"invalid Browser origin: {origin!r}") from exc
        if canonical != origin:
            raise BrowserCanonicalizationError(
                f"origin is not exact WHATWG canonical serialization: {origin!r}"
            )

    def verify_canonical_cookie_domain(self, domain: str) -> None:
        if not domain or domain.startswith("."):
            raise BrowserCanonicalizationError(
                "stored cookie domain must be canonical text without a leading dot"
            )
        try:
            canonical = self._url_field(f"http://{domain}/", "hostname")
        except Exception as exc:
            raise BrowserCanonicalizationError(f"invalid cookie domain: {domain!r}") from exc
        if canonical != domain:
            raise BrowserCanonicalizationError(
                f"cookie domain is not canonical hostname text: {domain!r}"
            )


class PlaywrightBrowserResource:
    """One independently isolated Browser resource backed by one BrowserContext."""

    def __init__(
        self,
        *,
        handle_id: str,
        context: Any,
        fixture: MaterializedBrowserFixture,
        verifier: BrowserIdentityVerifier,
    ) -> None:
        self.handle_id = handle_id
        self._context = context
        self._fixture = fixture
        self._verifier = verifier
        self._provenance: dict[tuple[str, str, bool, str], CookieProvenance] = {}
        self._snapshots: dict[str, _StoredSnapshot] = {}
        self._snapshot_counter = itertools.count(1)
        self._released = False
        self._execution_bindings = _plain_bindings(fixture.manifest["executionBindings"])
        self._excluded_state_interfering = False
        self._restore_temporally_eligible = True
        self._evaluator_private_marker: str | None = None

    def _ensure_live(self) -> None:
        if self._released:
            raise BrowserHarnessError("Playwright Browser resource is released")

    def snapshot(self) -> SnapshotRef:
        self._ensure_live()
        image = _project_selected_state(self, self._fixture)
        state_digest = canonical_state_image_digest(
            image, self._fixture.manifest, self._verifier
        )
        sequence = next(self._snapshot_counter)
        snapshot_id = f"{self.handle_id}-snapshot-{sequence}"
        self._snapshots[snapshot_id] = _StoredSnapshot(
            image=copy.deepcopy(image),
            provenance=tuple(self._provenance.values()),
        )
        return SnapshotRef(
            snapshot_id=snapshot_id,
            handle_id=self.handle_id,
            state_digest=state_digest,
            logical_time=sequence,
            consistency="settled",
            adapter_name="playwright-browser",
        )

    def reset(self) -> None:
        self._ensure_live()
        _replace_selected_state(self, self._fixture.baseline_image, provenance=None)

    def restore(self, snapshot: SnapshotRef) -> None:
        self._ensure_live()
        if snapshot.handle_id != self.handle_id:
            raise BrowserVerificationError("foreign Browser SnapshotRef")
        try:
            stored = self._snapshots[snapshot.snapshot_id]
        except KeyError as exc:
            raise BrowserVerificationError("unknown or stale Browser SnapshotRef") from exc
        _replace_selected_state(
            self,
            stored.image,
            provenance={item.identity: item for item in stored.provenance},
        )

    def release(self) -> None:
        if self._released:
            return
        self._context.close()
        self._released = True


class PlaywrightBrowserObserver:
    """Evaluator-only authoritative observation path for Playwright resources."""

    def __init__(self, expected_bindings: Mapping[str, Mapping[str, str]]) -> None:
        self._expected_bindings = _plain_bindings(expected_bindings)

    @staticmethod
    def _resource(sut: Any) -> PlaywrightBrowserResource:
        if not isinstance(sut, PlaywrightBrowserResource):
            raise TypeError("Playwright observer received a foreign Browser SUT")
        sut._ensure_live()
        return sut

    def verify_execution_conditions(
        self, sut: Any, fixture: MaterializedBrowserFixture
    ) -> None:
        resource = self._resource(sut)
        if resource._execution_bindings != self._expected_bindings:
            raise BrowserVerificationError("Browser execution-input identity drift")
        if _plain_bindings(fixture.manifest["executionBindings"]) != self._expected_bindings:
            raise BrowserVerificationError("materialized Browser execution identity mismatch")
        if resource._excluded_state_interfering:
            raise BrowserVerificationError("material excluded Browser state interferes")

    def verify_restore_eligibility(
        self,
        sut: Any,
        fixture: MaterializedBrowserFixture,
        snapshot: SnapshotRef,
    ) -> None:
        del fixture, snapshot
        if not self._resource(sut)._restore_temporally_eligible:
            raise BrowserVerificationError("cookie temporal restore eligibility is unresolved")

    def project_selected_state(
        self, sut: Any, fixture: MaterializedBrowserFixture
    ) -> Mapping[str, Any]:
        return _project_selected_state(self._resource(sut), fixture)


class PlaywrightBrowserFixtureControl:
    """Privileged test/control operations deliberately absent from BrowserSUT."""

    @staticmethod
    def _resource(sut: Any) -> PlaywrightBrowserResource:
        if not isinstance(sut, PlaywrightBrowserResource):
            raise TypeError("Playwright fixture control received a foreign Browser SUT")
        sut._ensure_live()
        return sut

    def seed_baseline(self, sut: Any, fixture: MaterializedBrowserFixture) -> None:
        _replace_selected_state(self._resource(sut), fixture.baseline_image, provenance=None)

    def seed_cookie(
        self,
        sut: Any,
        cookie: Mapping[str, Any],
        *,
        provenance: Mapping[str, Any] | None = None,
    ) -> None:
        resource = self._resource(sut)
        record = _cookie_provenance(cookie, provenance)
        _seed_cookie(resource, record)

    def seed_local_storage(
        self,
        sut: Any,
        origin: str,
        entries: Sequence[Mapping[str, str]],
    ) -> None:
        _set_local_storage(self._resource(sut), origin, entries)

    def seed_partitioned_cookie(self, sut: Any, cookie: Mapping[str, Any]) -> None:
        del sut, cookie
        raise BrowserVerificationError(
            "partitioned-cookie control is reserved for the executed-TCK provider slice"
        )

    def set_execution_binding(self, sut: Any, reference: str, identity: str) -> None:
        resource = self._resource(sut)
        try:
            resource._execution_bindings[reference]["identity"] = identity
        except KeyError as exc:
            raise BrowserVerificationError(
                f"unknown Browser execution binding: {reference}"
            ) from exc

    def set_excluded_state_interference(self, sut: Any, *, interfering: bool) -> None:
        self._resource(sut)._excluded_state_interfering = interfering

    def seed_evaluator_private_state(self, sut: Any) -> None:
        self._resource(sut)._evaluator_private_marker = "synthetic-private-state"

    def set_restore_temporal_eligibility(self, sut: Any, *, eligible: bool) -> None:
        self._resource(sut)._restore_temporally_eligible = eligible


class PlaywrightBrowserBackendHarness:
    """Chromium-first Playwright implementation of the shared Browser harness."""

    def __init__(self, *, engine: str = "chromium", headless: bool = True) -> None:
        if engine != "chromium":
            raise ValueError("the first Playwright reference backend supports chromium only")
        self._manager = sync_playwright_runtime()
        self._playwright = self._manager.start()
        self._browser = getattr(self._playwright, engine).launch(headless=headless)
        self.engine = engine
        self.browser_version = str(self._browser.version)
        self.identity_verifier = PlaywrightBrowserIdentityVerifier(self._browser)
        self._control = PlaywrightBrowserFixtureControl()
        self._observer: PlaywrightBrowserObserver | None = None
        self._resources: list[PlaywrightBrowserResource] = []
        self._counter = itertools.count(1)

    @property
    def browser_build_binding(self) -> Mapping[str, str]:
        # A product/version tuple is a version identity, not a content digest.
        return {
            "identity": f"playwright/{self.engine}/{self.browser_version}",
            "identityType": "version",
        }

    def materialize_fixture(
        self,
        source: Mapping[str, Any],
        *,
        resolved_origins: Mapping[str, str],
    ) -> MaterializedBrowserFixture:
        materialized_source = copy.deepcopy(dict(source))
        bindings = copy.deepcopy(dict(materialized_source.get("executionBindings", {})))
        if "browserBuild" not in bindings:
            raise BrowserVerificationError("Browser fixture lacks browserBuild execution binding")
        bindings["browserBuild"] = dict(self.browser_build_binding)
        materialized_source["executionBindings"] = bindings
        return materialize_browser_fixture(
            materialized_source,
            resolved_origins=resolved_origins,
            verifier=self.identity_verifier,
        )

    @property
    def observer(self) -> PlaywrightBrowserObserver:
        if self._observer is None:
            raise BrowserHarnessError("provision a Browser fixture before observer use")
        return self._observer

    @property
    def fixture_control(self) -> PlaywrightBrowserFixtureControl:
        return self._control

    def provision(self, fixture: MaterializedBrowserFixture) -> PlaywrightBrowserResource:
        expected = _plain_bindings(fixture.manifest["executionBindings"])
        if expected.get("browserBuild") != dict(self.browser_build_binding):
            raise BrowserVerificationError(
                "materialized browserBuild identity does not match running provider"
            )
        if self._observer is None:
            self._observer = PlaywrightBrowserObserver(expected)
        elif self._observer._expected_bindings != expected:
            raise BrowserVerificationError(
                "one Playwright backend cannot mix execution-binding identities"
            )
        resource = PlaywrightBrowserResource(
            handle_id=f"playwright-browser-{next(self._counter)}",
            context=self._browser.new_context(),
            fixture=fixture,
            verifier=self.identity_verifier,
        )
        self._resources.append(resource)
        try:
            self._control.seed_baseline(resource, fixture)
        except Exception:
            resource.release()
            raise
        return resource

    def close(self) -> None:
        for resource in reversed(self._resources):
            resource.release()
        self._browser.close()
        self._manager.stop()


def _plain_bindings(value: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    return {
        str(reference): {
            "identity": str(binding["identity"]),
            "identityType": str(binding["identityType"]),
        }
        for reference, binding in value.items()
    }


def _cookie_provenance(
    cookie: Mapping[str, Any], provenance: Mapping[str, Any] | None
) -> CookieProvenance:
    persistent = cookie.get("persistent")
    required = {
        "name", "value", "domain", "hostOnly", "path", "persistent",
        "secure", "httpOnly", "sameSite",
    }
    if persistent is True:
        required.add("expiry")
    if set(cookie) != required:
        raise BrowserVerificationError("cookie seed is not the closed portable shape")
    source = "controlled-playwright-fixture"
    revision = 1
    if provenance is not None:
        if set(provenance) != {"source", "revision"}:
            raise BrowserVerificationError("cookie provenance shape is not closed")
        source = provenance["source"]
        revision = provenance["revision"]
    if not isinstance(source, str) or not source:
        raise BrowserVerificationError("cookie provenance source must be non-empty")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise BrowserVerificationError("cookie provenance revision must be positive")
    expiry_seconds = None
    expiry_nanoseconds = None
    if persistent is True:
        expiry = cookie["expiry"]
        expiry_seconds = str(expiry["unixSeconds"])
        expiry_nanoseconds = int(expiry["nanoseconds"])
    return CookieProvenance(
        name=str(cookie["name"]), value=str(cookie["value"]),
        domain=str(cookie["domain"]), host_only=bool(cookie["hostOnly"]),
        path=str(cookie["path"]), persistent=bool(persistent),
        secure=bool(cookie["secure"]), http_only=bool(cookie["httpOnly"]),
        same_site=str(cookie["sameSite"]), expiry_seconds=expiry_seconds,
        expiry_nanoseconds=expiry_nanoseconds, source=source, revision=revision,
    )


def _cookie_for_playwright(
    record: CookieProvenance, fixture: MaterializedBrowserFixture
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "name": record.name,
        "value": record.value,
        "path": record.path,
        "secure": record.secure,
        "httpOnly": record.http_only,
    }
    if record.host_only:
        matches = [
            origin for origin in fixture.manifest["localStorageOrigins"]
            if origin.split("://", 1)[1].split(":", 1)[0] == record.domain
        ]
        if len(matches) != 1:
            raise BrowserVerificationError(
                "host-only cookie needs exactly one selected origin with its stored domain"
            )
        value["url"] = matches[0] + record.path
    else:
        value["domain"] = record.domain
    if record.same_site != "Default":
        value["sameSite"] = record.same_site
    if record.persistent:
        assert record.expiry_seconds is not None
        assert record.expiry_nanoseconds is not None
        value["expires"] = int(record.expiry_seconds) + (
            record.expiry_nanoseconds / 1_000_000_000
        )
    return value


def _seed_cookie(resource: PlaywrightBrowserResource, record: CookieProvenance) -> None:
    resource._context.add_cookies([_cookie_for_playwright(record, resource._fixture)])
    resource._provenance[record.identity] = record


def _set_local_storage(
    resource: PlaywrightBrowserResource,
    origin: str,
    entries: Sequence[Mapping[str, str]],
) -> None:
    if origin not in set(resource._fixture.manifest["localStorageOrigins"]):
        raise BrowserVerificationError("localStorage seed is outside Manifest selection")
    payload = []
    for entry in entries:
        if set(entry) != {"key", "value"}:
            raise BrowserVerificationError("localStorage seed entry shape is not closed")
        payload.append(
            {
                "key": list(decode_dom_string_code_units(entry["key"])),
                "value": list(decode_dom_string_code_units(entry["value"])),
            }
        )
    page = resource._context.new_page()
    try:
        page.goto(origin + "/", wait_until="domcontentloaded")
        page.evaluate("localStorage.clear()")
        page.evaluate(
            "entries => {"
            " const s = units => String.fromCharCode(...units);"
            " for (const e of entries) localStorage.setItem(s(e.key), s(e.value));"
            "}",
            payload,
        )
    finally:
        page.close()


def _clear_selected_state(resource: PlaywrightBrowserResource) -> None:
    resource._context.clear_cookies()
    resource._provenance.clear()
    for origin in resource._fixture.manifest["localStorageOrigins"]:
        page = resource._context.new_page()
        try:
            page.goto(origin + "/", wait_until="domcontentloaded")
            page.evaluate("localStorage.clear()")
        finally:
            page.close()


def _replace_selected_state(
    resource: PlaywrightBrowserResource,
    image: Mapping[str, Any],
    *,
    provenance: Mapping[tuple[str, str, bool, str], CookieProvenance] | None,
) -> None:
    _clear_selected_state(resource)
    for origin_state in image["origins"]:
        _set_local_storage(resource, origin_state["origin"], origin_state["localStorage"])
    for cookie in image["cookies"]:
        identity = (
            cookie["name"], cookie["domain"], cookie["hostOnly"], cookie["path"]
        )
        record = provenance.get(identity) if provenance is not None else None
        if record is None:
            record = _cookie_provenance(cookie, None)
        if record.portable() != dict(cookie):
            raise BrowserVerificationError("cookie provenance conflicts with portable state")
        _seed_cookie(resource, record)


def _visible_cookie_key(cookie: Mapping[str, Any]) -> tuple[str, str, str]:
    domain = str(cookie.get("domain", ""))
    if domain.startswith("."):
        # Correlation normalization only. Never infer hostOnly from this syntax.
        domain = domain[1:]
    return str(cookie.get("name", "")), domain, str(cookie.get("path", ""))


def _project_cookies(
    resource: PlaywrightBrowserResource, fixture: MaterializedBrowserFixture
) -> list[dict[str, Any]]:
    observed = resource._context.cookies(list(fixture.manifest["localStorageOrigins"]))
    visible: dict[tuple[str, str, str], list[Mapping[str, Any]]] = {}
    for cookie in observed:
        visible.setdefault(_visible_cookie_key(cookie), []).append(cookie)

    selected_domains = set(fixture.manifest["cookieDomains"])
    projected: list[dict[str, Any]] = []
    expected_visible: set[tuple[str, str, str]] = set()
    for record in resource._provenance.values():
        if record.domain not in selected_domains:
            continue
        key = (record.name, record.domain, record.path)
        expected_visible.add(key)
        matches = visible.get(key, [])
        if len(matches) != 1:
            raise BrowserVerificationError(
                "selected cookie is missing or ambiguous against evaluator provenance"
            )
        current = matches[0]
        if str(current.get("value")) != record.value:
            raise BrowserVerificationError("cookie value conflicts with provenance")
        if bool(current.get("secure")) != record.secure:
            raise BrowserVerificationError("cookie secure flag conflicts with provenance")
        if bool(current.get("httpOnly")) != record.http_only:
            raise BrowserVerificationError("cookie httpOnly flag conflicts with provenance")
        if record.same_site != "Default" and current.get("sameSite") != record.same_site:
            raise BrowserVerificationError("cookie SameSite conflicts with provenance")
        if record.persistent:
            observed_expiry = current.get("expires")
            if not isinstance(observed_expiry, (int, float)) or observed_expiry <= 0:
                raise BrowserVerificationError("persistent cookie expiry is not observable")
            assert record.expiry_seconds is not None
            if int(observed_expiry) != int(record.expiry_seconds):
                raise BrowserVerificationError("persistent cookie expiry second conflicts")
        projected.append(record.portable())

    extras = [
        key for key in visible
        if key[1] in selected_domains and key not in expected_visible
    ]
    if extras:
        raise BrowserVerificationError(
            "selected browser cookie exists without evaluator/control provenance"
        )
    return projected


def _project_local_storage(
    resource: PlaywrightBrowserResource, fixture: MaterializedBrowserFixture
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for origin in fixture.manifest["localStorageOrigins"]:
        page = resource._context.new_page()
        try:
            page.goto(origin + "/", wait_until="domcontentloaded")
            entries = page.evaluate(
                "() => {"
                " const units = text => { const out = [];"
                "   for (let i = 0; i < text.length; i++) out.push(text.charCodeAt(i));"
                "   return out; };"
                " const out = [];"
                " for (let i = 0; i < localStorage.length; i++) {"
                "   const key = localStorage.key(i);"
                "   out.push({key: units(key), value: units(localStorage.getItem(key))});"
                " }"
                " return out;"
                "}"
            )
        finally:
            page.close()
        if not isinstance(entries, list):
            raise BrowserVerificationError("localStorage observation is malformed")
        encoded = []
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise BrowserVerificationError("localStorage observation entry is malformed")
            encoded.append(
                {
                    "key": encode_dom_string_code_units(entry["key"]),
                    "value": encode_dom_string_code_units(entry["value"]),
                }
            )
        result.append({"origin": origin, "localStorage": encoded})
    return result


def _project_selected_state(
    resource: PlaywrightBrowserResource, fixture: MaterializedBrowserFixture
) -> dict[str, Any]:
    resource._ensure_live()
    return {
        "apiVersion": "avp.browser/v0.1",
        "kind": "BrowserStateImage",
        "manifestDigest": fixture.manifest_digest,
        "cookies": _project_cookies(resource, fixture),
        "origins": _project_local_storage(resource, fixture),
    }

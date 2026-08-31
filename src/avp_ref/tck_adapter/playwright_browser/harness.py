"""Concrete Playwright implementation of the Browser conformance harness.

This module implements Browser v0.1 through Playwright without promoting
Playwright concepts into portable AVP semantics. Browser contexts, pages,
launch options, and provider cookie serialization remain private implementation
mechanics. Required cookie facts that the provider transport does not expose
losslessly are established by evaluator/control-owned provenance and fail closed
when provenance is missing or inconsistent.
"""

from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass
from threading import RLock
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
)

from .driver import sync_playwright_runtime


@dataclass(frozen=True, slots=True)
class _CookieProvenance:
    name: str
    value: str
    domain: str
    host_only: bool
    path: str
    persistent: bool
    secure: bool
    http_only: bool
    same_site: str
    expiry_unix_seconds: str | None
    expiry_nanoseconds: int | None
    source: str
    revision: int

    @property
    def portable_identity(self) -> tuple[str, str, bool, str]:
        return self.name, self.domain, self.host_only, self.path

    def to_portable_cookie(self) -> dict[str, Any]:
        cookie: dict[str, Any] = {
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
            if self.expiry_unix_seconds is None or self.expiry_nanoseconds is None:
                raise BrowserVerificationError(
                    "persistent cookie provenance is missing exact expiry"
                )
            cookie["expiry"] = {
                "unixSeconds": self.expiry_unix_seconds,
                "nanoseconds": self.expiry_nanoseconds,
            }
        return cookie


@dataclass(frozen=True, slots=True)
class _StoredSnapshot:
    image: Mapping[str, Any]
    provenance: tuple[_CookieProvenance, ...]


class PlaywrightBrowserIdentityVerifier(BrowserIdentityVerifier):
    """Use the actual browser WHATWG URL implementation for origin admission."""

    def __init__(self, browser: Any) -> None:
        self._browser = browser

    def _canonical_url_field(self, value: str, expression: str) -> str:
        context = self._browser.new_context()
        try:
            page = context.new_page()
            result = page.evaluate(
                "([value, expression]) => {"
                " const url = new URL(value);"
                " return expression === 'origin' ? url.origin : url.hostname;"
                "}",
                [value, expression],
            )
        finally:
            context.close()
        if not isinstance(result, str) or not result:
            raise BrowserCanonicalizationError("browser URL canonicalization failed")
        return result

    def verify_canonical_origin(self, origin: str) -> None:
        try:
            canonical = self._canonical_url_field(origin, "origin")
        except Exception as exc:
            raise BrowserCanonicalizationError(
                f"invalid Browser tuple origin: {origin!r}"
            ) from exc
        if canonical != origin:
            raise BrowserCanonicalizationError(
                f"Browser origin is not exact WHATWG canonical serialization: {origin!r}"
            )

    def verify_canonical_cookie_domain(self, domain: str) -> None:
        if not domain or domain.startswith("."):
            raise BrowserCanonicalizationError(
                "stored cookie domain must be canonical text without a presentation leading dot"
            )
        try:
            canonical = self._canonical_url_field(f"http://{domain}/", "hostname")
        except Exception as exc:
            raise BrowserCanonicalizationError(
                f"invalid stored cookie domain: {domain!r}"
            ) from exc
        if canonical != domain:
            raise BrowserCanonicalizationError(
                f"stored cookie domain is not canonical hostname text: {domain!r}"
            )


class PlaywrightBrowserResource:
    """One independently isolated Playwright BrowserContext-backed resource."""

    def __init__(
        self,
        *,
        handle_id: str,
        context: Any,
        fixture: MaterializedBrowserFixture,
        verifier: BrowserIdentityVerifier,
        adapter_name: str,
    ) -> None:
        self.handle_id = handle_id
        self._context = context
        self._fixture = fixture
        self._verifier = verifier
        self._adapter_name = adapter_name
        self._provenance: dict[tuple[str, str, bool, str], _CookieProvenance] = {}
        self._snapshots: dict[str, _StoredSnapshot] = {}
        self._snapshot_counter = itertools.count(1)
        self._released = False
        self._execution_bindings = {
            reference: dict(binding)
            for reference, binding in fixture.manifest["executionBindings"].items()
        }
        self._excluded_state_interfering = False
        self._restore_temporally_eligible = True
        self._lock = RLock()

    def _ensure_live(self) -> None:
        if self._released:
            raise BrowserHarnessError("Browser resource has been released")

    def snapshot(self) -> SnapshotRef:
        self._ensure_live()
        with self._lock:
            image = _project_selected_state(self, self._fixture)
            digest = canonical_state_image_digest(image, self._fixture.manifest, self._verifier)
            sequence = next(self._snapshot_counter)
            snapshot_id = f"{self.handle_id}-snapshot-{sequence}"
            self._snapshots[snapshot_id] = _StoredSnapshot(
                image=image,
                provenance=tuple(self._provenance.values()),
            )
            return SnapshotRef(
                snapshot_id=snapshot_id,
                handle_id=self.handle_id,
                state_digest=digest,
                logical_time=sequence,
                consistency="settled",
                adapter_name=self._adapter_name,
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
            provenance={item.portable_identity: item for item in stored.provenance},
        )

    def release(self) -> None:
        if self._released:
            return
        self._context.close()
        self._released = True


class PlaywrightBrowserObserver:
    """Evaluator-owned observation of selected Browser state."""

    def __init__(self, expected_execution_bindings: Mapping[str, Mapping[str, str]]) -> None:
        self._expected_execution_bindings = {
            reference: dict(binding)
            for reference, binding in expected_execution_bindings.items()
        }

    @staticmethod
    def _resource(sut: Any) -> PlaywrightBrowserResource:
        if not isinstance(sut, PlaywrightBrowserResource):
            raise TypeError("Playwright observer received a foreign Browser SUT")
        sut._ensure_live()
        return sut

    def verify_execution_conditions(
        self,
        sut: Any,
        fixture: MaterializedBrowserFixture,
    ) -> None:
        resource = self._resource(sut)
        if resource._execution_bindings != self._expected_execution_bindings:
            raise BrowserVerificationError("material Browser execution-input identity drift")
        if resource._excluded_state_interfering:
            raise BrowserVerificationError(
                "material excluded Browser state interference is unresolved"
            )
        if dict(fixture.manifest["executionBindings"]) != self._expected_execution_bindings:
            raise BrowserVerificationError("materialized Browser fixture binding mismatch")

    def verify_restore_eligibility(
        self,
        sut: Any,
        fixture: MaterializedBrowserFixture,
        snapshot: SnapshotRef,
    ) -> None:
        del fixture, snapshot
        resource = self._resource(sut)
        if not resource._restore_temporally_eligible:
            raise BrowserVerificationError(
                "selected cookie temporal restore eligibility is unresolved"
            )

    def project_selected_state(
        self,
        sut: Any,
        fixture: MaterializedBrowserFixture,
    ) -> Mapping[str, Any]:
        resource = self._resource(sut)
        return _project_selected_state(resource, fixture)


class PlaywrightBrowserFixtureControl:
    """Privileged Browser controls not exposed through ``BrowserSUT``."""

    @staticmethod
    def _resource(sut: Any) -> PlaywrightBrowserResource:
        if not isinstance(sut, PlaywrightBrowserResource):
            raise TypeError("Playwright fixture control received a foreign Browser SUT")
        sut._ensure_live()
        return sut

    def seed_baseline(
        self,
        sut: Any,
        fixture: MaterializedBrowserFixture,
    ) -> None:
        resource = self._resource(sut)
        _replace_selected_state(resource, fixture.baseline_image, provenance=None)

    def seed_cookie(
        self,
        sut: Any,
        cookie: Mapping[str, Any],
        *,
        provenance: Mapping[str, Any] | None = None,
    ) -> None:
        resource = self._resource(sut)
        record = _provenance_from_cookie(cookie, provenance=provenance)
        _seed_cookie(resource, record)

    def seed_local_storage(
        self,
        sut: Any,
        origin: str,
        entries: Sequence[Mapping[str, str]],
    ) -> None:
        resource = self._resource(sut)
        _set_local_storage(resource, origin, entries)

    def seed_partitioned_cookie(
        self,
        sut: Any,
        cookie: Mapping[str, Any],
    ) -> None:
        # Partitioned-state controls are implemented in the executed-TCK slice.
        # Failing here is safer than silently admitting a non-partitioned cookie.
        del sut, cookie
        raise BrowserVerificationError(
            "partitioned cookie control is not implemented by the provider foundation"
        )

    def set_execution_binding(
        self,
        sut: Any,
        reference: str,
        identity: str,
    ) -> None:
        resource = self._resource(sut)
        try:
            binding = resource._execution_bindings[reference]
        except KeyError as exc:
            raise BrowserVerificationError(
                f"unknown Browser execution binding: {reference}"
            ) from exc
        binding["identity"] = identity

    def set_excluded_state_interference(
        self,
        sut: Any,
        *,
        interfering: bool,
    ) -> None:
        resource = self._resource(sut)
        resource._excluded_state_interfering = interfering

    def seed_evaluator_private_state(self, sut: Any) -> None:
        resource = self._resource(sut)
        # The concrete secrecy probe is added with the executed Security case.
        # This private marker cannot be observed through the BrowserSUT seam.
        resource._evaluator_private_marker = "synthetic-evaluator-private-browser-state"

    def set_restore_temporal_eligibility(self, sut: Any, *, eligible: bool) -> None:
        self._resource(sut)._restore_temporally_eligible = eligible


class PlaywrightBrowserBackendHarness:
    """Concrete Chromium-first Playwright implementation of Browser backend roles."""

    adapter_name = "playwright-browser"

    def __init__(
        self,
        *,
        engine: str = "chromium",
        headless: bool = True,
    ) -> None:
        if engine != "chromium":
            raise ValueError(
                "the first Playwright reference implementation currently admits only chromium"
            )
        self._manager = sync_playwright_runtime()
        self._playwright = self._manager.start()
        browser_type = getattr(self._playwright, engine)
        self._browser = browser_type.launch(headless=headless)
        self.engine = engine
        self.browser_version = str(self._browser.version)
        self.identity_verifier = PlaywrightBrowserIdentityVerifier(self._browser)
        self._control = PlaywrightBrowserFixtureControl()
        self._observer: PlaywrightBrowserObserver | None = None
        self._counter = itertools.count(1)
        self._resources: list[PlaywrightBrowserResource] = []

    @property
    def browser_build_identity(self) -> str:
        """Content-like immutable identity for this installed browser build.

        The implementation cannot portably expose the browser executable bytes
        through Playwright, so the first provider slice binds the exact provider
        engine/version tuple as a symbolic execution identity. It must not be
        substituted for BrowserState identity or represented as a content hash.
        """

        payload = f"playwright:{self.engine}:{self.browser_version}".encode("utf-8")
        return "playwright-build-sha256:" + hashlib.sha256(payload).hexdigest()

    @property
    def observer(self) -> PlaywrightBrowserObserver:
        if self._observer is None:
            raise BrowserHarnessError("Browser fixture must be provisioned before observer use")
        return self._observer

    @property
    def fixture_control(self) -> PlaywrightBrowserFixtureControl:
        return self._control

    def provision(self, fixture: MaterializedBrowserFixture) -> PlaywrightBrowserResource:
        expected = {
            reference: dict(binding)
            for reference, binding in fixture.manifest["executionBindings"].items()
        }
        if self._observer is None:
            self._observer = PlaywrightBrowserObserver(expected)
        elif self._observer._expected_execution_bindings != expected:
            raise BrowserVerificationError(
                "one Playwright backend cannot mix materially different execution bindings"
            )
        context = self._browser.new_context()
        resource = PlaywrightBrowserResource(
            handle_id=f"playwright-browser-{next(self._counter)}",
            context=context,
            fixture=fixture,
            verifier=self.identity_verifier,
            adapter_name=self.adapter_name,
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


def _provenance_from_cookie(
    cookie: Mapping[str, Any],
    *,
    provenance: Mapping[str, Any] | None,
) -> _CookieProvenance:
    required = {
        "name",
        "value",
        "domain",
        "hostOnly",
        "path",
        "persistent",
        "secure",
        "httpOnly",
        "sameSite",
    }
    if bool(cookie.get("persistent")):
        required.add("expiry")
    if set(cookie) != required:
        raise BrowserVerificationError("cookie seed must use the closed portable cookie shape")

    if provenance is not None:
        if set(provenance) != {"source", "revision"}:
            raise BrowserVerificationError("cookie provenance shape is not closed")
        source = provenance["source"]
        revision = provenance["revision"]
    else:
        source = "controlled-playwright-fixture"
        revision = 1
    if not isinstance(source, str) or not source:
        raise BrowserVerificationError("cookie provenance source must be non-empty")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise BrowserVerificationError("cookie provenance revision must be positive")

    expiry_seconds: str | None = None
    expiry_nanos: int | None = None
    if cookie["persistent"]:
        expiry = cookie["expiry"]
        expiry_seconds = str(expiry["unixSeconds"])
        expiry_nanos = int(expiry["nanoseconds"])

    return _CookieProvenance(
        name=str(cookie["name"]),
        value=str(cookie["value"]),
        domain=str(cookie["domain"]),
        host_only=bool(cookie["hostOnly"]),
        path=str(cookie["path"]),
        persistent=bool(cookie["persistent"]),
        secure=bool(cookie["secure"]),
        http_only=bool(cookie["httpOnly"]),
        same_site=str(cookie["sameSite"]),
        expiry_unix_seconds=expiry_seconds,
        expiry_nanoseconds=expiry_nanos,
        source=source,
        revision=revision,
    )


def _playwright_cookie(record: _CookieProvenance, fixture: MaterializedBrowserFixture) -> dict[str, Any]:
    cookie: dict[str, Any] = {
        "name": record.name,
        "value": record.value,
        "path": record.path,
        "secure": record.secure,
        "httpOnly": record.http_only,
    }
    if record.host_only:
        origins = tuple(fixture.manifest["localStorageOrigins"])
        matching = [origin for origin in origins if f"://{record.domain}" in origin]
        if not matching:
            raise BrowserVerificationError(
                "host-only cookie has no selected exact origin for controlled seeding"
            )
        cookie["url"] = matching[0]
    else:
        cookie["domain"] = record.domain
    if record.same_site != "Default":
        cookie["sameSite"] = record.same_site
    if record.persistent:
        assert record.expiry_unix_seconds is not None
        assert record.expiry_nanoseconds is not None
        cookie["expires"] = int(record.expiry_unix_seconds) + (
            record.expiry_nanoseconds / 1_000_000_000
        )
    return cookie


def _seed_cookie(resource: PlaywrightBrowserResource, record: _CookieProvenance) -> None:
    resource._fixture.manifest  # keep fixture ownership explicit
    resource._context.add_cookies([_playwright_cookie(record, resource._fixture)])
    resource._provenance[record.portable_identity] = record


def _set_local_storage(
    resource: PlaywrightBrowserResource,
    origin: str,
    entries: Sequence[Mapping[str, str]],
) -> None:
    if origin not in set(resource._fixture.manifest["localStorageOrigins"]):
        raise BrowserVerificationError("cannot seed localStorage outside exact Manifest selection")
    code_unit_entries = []
    for entry in entries:
        if set(entry) != {"key", "value"}:
            raise BrowserVerificationError("localStorage seed entry shape is not closed")
        code_unit_entries.append(
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
            " const text = units => String.fromCharCode(...units);"
            " for (const entry of entries) localStorage.setItem(text(entry.key), text(entry.value));"
            "}",
            code_unit_entries,
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
    provenance: Mapping[tuple[str, str, bool, str], _CookieProvenance] | None,
) -> None:
    resource._ensure_live()
    _clear_selected_state(resource)
    for origin_state in image["origins"]:
        _set_local_storage(resource, origin_state["origin"], origin_state["localStorage"])
    for cookie in image["cookies"]:
        identity = (
            cookie["name"],
            cookie["domain"],
            cookie["hostOnly"],
            cookie["path"],
        )
        record = provenance.get(identity) if provenance is not None else None
        if record is None:
            record = _provenance_from_cookie(cookie, provenance=None)
        if record.to_portable_cookie() != dict(cookie):
            raise BrowserVerificationError(
                "cookie provenance conflicts with selected portable cookie state"
            )
        _seed_cookie(resource, record)


def _observed_cookie_key(cookie: Mapping[str, Any]) -> tuple[str, str, str]:
    domain = str(cookie.get("domain", ""))
    if domain.startswith("."):
        # This normalization is used only to correlate a lossy provider record
        # with evaluator provenance. It is never used to infer hostOnly.
        domain = domain[1:]
    return str(cookie.get("name", "")), domain, str(cookie.get("path", ""))


def _project_cookies(
    resource: PlaywrightBrowserResource,
    fixture: MaterializedBrowserFixture,
) -> list[dict[str, Any]]:
    origins = list(fixture.manifest["localStorageOrigins"])
    observed = resource._context.cookies(origins)
    by_visible_key: dict[tuple[str, str, str], list[Mapping[str, Any]]] = {}
    for item in observed:
        by_visible_key.setdefault(_observed_cookie_key(item), []).append(item)

    projected: list[dict[str, Any]] = []
    selected_domains = set(fixture.manifest["cookieDomains"])
    for provenance in resource._provenance.values():
        if provenance.domain not in selected_domains:
            continue
        visible_key = (provenance.name, provenance.domain, provenance.path)
        matches = by_visible_key.get(visible_key, [])
        if len(matches) != 1:
            raise BrowserVerificationError(
                "selected cookie observation is missing or ambiguous for evaluator provenance"
            )
        current = matches[0]
        if str(current.get("value")) != provenance.value:
            raise BrowserVerificationError("selected cookie value conflicts with provenance")
        if bool(current.get("secure")) != provenance.secure:
            raise BrowserVerificationError("selected cookie secure flag conflicts with provenance")
        if bool(current.get("httpOnly")) != provenance.http_only:
            raise BrowserVerificationError("selected cookie httpOnly flag conflicts with provenance")
        projected.append(provenance.to_portable_cookie())

    provenance_visible_keys = {
        (item.name, item.domain, item.path)
        for item in resource._provenance.values()
        if item.domain in selected_domains
    }
    extra_selected = [
        key
        for key in by_visible_key
        if key[1] in selected_domains and key not in provenance_visible_keys
    ]
    if extra_selected:
        raise BrowserVerificationError(
            "browser contains selected cookie state without evaluator provenance"
        )
    return projected


def _project_local_storage(
    resource: PlaywrightBrowserResource,
    fixture: MaterializedBrowserFixture,
) -> list[dict[str, Any]]:
    origins: list[dict[str, Any]] = []
    for origin in fixture.manifest["localStorageOrigins"]:
        page = resource._context.new_page()
        try:
            page.goto(origin + "/", wait_until="domcontentloaded")
            entries = page.evaluate(
                "() => Array.from({length: localStorage.length}, (_, i) => {"
                " const key = localStorage.key(i);"
                " const value = localStorage.getItem(key);"
                " const units = text => Array.from(text, (_, j) => text.charCodeAt(j));"
                " return {key: units(key), value: units(value)};"
                "})"
            )
        finally:
            page.close()
        if not isinstance(entries, list):
            raise BrowserVerificationError("Playwright localStorage observation is malformed")
        encoded = []
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise BrowserVerificationError("Playwright localStorage entry is malformed")
            encoded.append(
                {
                    "key": encode_dom_string_code_units(entry["key"]),
                    "value": encode_dom_string_code_units(entry["value"]),
                }
            )
        origins.append({"origin": origin, "localStorage": encoded})
    return origins


def _project_selected_state(
    resource: PlaywrightBrowserResource,
    fixture: MaterializedBrowserFixture,
) -> dict[str, Any]:
    return {
        "apiVersion": "avp.browser/v0.1",
        "kind": "BrowserStateImage",
        "manifestDigest": fixture.manifest_digest,
        "cookies": _project_cookies(resource, fixture),
        "origins": _project_local_storage(resource, fixture),
    }

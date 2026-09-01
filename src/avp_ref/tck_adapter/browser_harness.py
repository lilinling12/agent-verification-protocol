"""Backend-neutral Browser v0.1 conformance infrastructure.

This module is implementation infrastructure, not protocol authority. It is
intentionally narrower than a browser-automation API: portable conformance sees
only Browser resource lifecycle, evaluator-owned state observation, fixture
control, canonical identity, and settlement. Provider page/context/session
handles and automation commands stay behind concrete implementations.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable

import rfc8785

from avp_ref.environment.models import (
    ResetResult,
    ResetTarget,
    RestoreEquivalence,
    RestoreResult,
    SnapshotRef,
    StateProjection,
)

_BROWSER_API_VERSION = "avp.browser/v0.1"
_BROWSER_PROFILE = "avp-browser-unpartitioned-cookie-localstorage-v0.1"
_BROWSER_REVISION = "0.1"
_BROWSER_REPRESENTATION = "avp-browser-v0.1-rfc8785-jcs"
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_UNIX_SECONDS_RE = re.compile(r"^(?:0|-?[1-9][0-9]*)$")
_SAME_SITE = frozenset({"Default", "Strict", "Lax", "None"})


class BrowserHarnessError(RuntimeError):
    """Base error for fail-closed Browser conformance infrastructure."""


class BrowserCanonicalizationError(BrowserHarnessError):
    """Raised when Browser profile identity cannot be established canonically."""


class BrowserSettlementError(BrowserHarnessError):
    """Raised when an authoritative observation is attempted while unsettled."""


class BrowserVerificationError(BrowserHarnessError):
    """Raised when independently observed state contradicts a lifecycle claim."""


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _require_exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise BrowserCanonicalizationError(
            f"{label} fields are not closed: missing={missing}, extra={extra}"
        )


def _jcs_bytes(value: Any) -> bytes:
    encoded = rfc8785.dumps(value)
    return encoded if isinstance(encoded, bytes) else encoded.encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def encode_dom_string_code_units(code_units: Sequence[int]) -> str:
    """Encode exact Web IDL DOMString UTF-16 code units for Browser v0.1.

    Callers pass code units rather than a Python ``str`` so unmatched surrogate
    values are never repaired by the host language before canonicalization.
    """

    raw = bytearray()
    for code_unit in code_units:
        if isinstance(code_unit, bool) or not isinstance(code_unit, int):
            raise BrowserCanonicalizationError("DOMString code units must be integers")
        if code_unit < 0 or code_unit > 0xFFFF:
            raise BrowserCanonicalizationError(
                f"DOMString code unit outside unsigned 16-bit range: {code_unit}"
            )
        raw.extend(code_unit.to_bytes(2, "big"))
    return base64.urlsafe_b64encode(bytes(raw)).decode("ascii").rstrip("=")


def decode_dom_string_code_units(encoded: str) -> tuple[int, ...]:
    """Decode and validate canonical unpadded Browser DOMString bytes."""

    if not isinstance(encoded, str):
        raise BrowserCanonicalizationError("DOMString encoding must be a string")
    if "=" in encoded:
        raise BrowserCanonicalizationError("DOMString base64url must be unpadded")
    if any(
        not (char.isascii() and (char.isalnum() or char in "-_"))
        for char in encoded
    ):
        raise BrowserCanonicalizationError("DOMString contains non-base64url characters")

    padding = "=" * ((4 - len(encoded) % 4) % 4)
    try:
        raw = base64.b64decode(
            (encoded + padding).encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, binascii.Error) as exc:
        raise BrowserCanonicalizationError("invalid DOMString base64url encoding") from exc

    if len(raw) % 2:
        raise BrowserCanonicalizationError(
            "DOMString decoded bytes must contain whole UTF-16 code units"
        )
    if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != encoded:
        raise BrowserCanonicalizationError(
            "DOMString base64url must use canonical zero pad bits"
        )
    return tuple(
        int.from_bytes(raw[offset : offset + 2], "big")
        for offset in range(0, len(raw), 2)
    )


@runtime_checkable
class BrowserIdentityVerifier(Protocol):
    """Standards-aware admission boundary for already canonical Browser ids.

    The shared harness deliberately does not approximate WHATWG URL/origin
    parsing with Python's RFC-oriented standard-library URL parser. A concrete
    observer/runtime must provide a reviewed verifier for canonical tuple origins
    and stored-cookie domains.
    """

    def verify_canonical_origin(self, origin: str) -> None: ...

    def verify_canonical_cookie_domain(self, domain: str) -> None: ...


def _origin_sort_key(origin: str) -> bytes:
    return origin.encode("utf-8")


def _domain_sort_key(domain: str) -> bytes:
    return domain.encode("utf-8")


def _cookie_octets(value: Any, label: str) -> bytes:
    if not isinstance(value, str):
        raise BrowserCanonicalizationError(f"{label} must be a string")
    try:
        raw = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise BrowserCanonicalizationError(
            f"{label} must preserve ASCII cookie octets"
        ) from exc
    if any(byte < 0x20 or byte > 0x7E for byte in raw):
        raise BrowserCanonicalizationError(f"{label} contains unsupported cookie octets")
    return raw


def canonicalize_manifest(
    manifest: Mapping[str, Any],
    verifier: BrowserIdentityVerifier,
) -> dict[str, Any]:
    """Validate and profile-order a BrowserStateManifest before JCS."""

    _require_exact_keys(
        manifest,
        {
            "apiVersion",
            "kind",
            "profile",
            "revision",
            "canonicalRepresentation",
            "localStorageOrigins",
            "cookieDomains",
            "executionBindings",
        },
        "BrowserStateManifest",
    )
    constants = {
        "apiVersion": _BROWSER_API_VERSION,
        "kind": "BrowserStateManifest",
        "profile": _BROWSER_PROFILE,
        "revision": _BROWSER_REVISION,
        "canonicalRepresentation": _BROWSER_REPRESENTATION,
    }
    for key, expected in constants.items():
        if manifest[key] != expected:
            raise BrowserCanonicalizationError(
                f"BrowserStateManifest {key} must equal {expected!r}"
            )

    origins_value = manifest["localStorageOrigins"]
    domains_value = manifest["cookieDomains"]
    bindings_value = manifest["executionBindings"]
    if not isinstance(origins_value, (list, tuple)):
        raise BrowserCanonicalizationError("localStorageOrigins must be an array")
    if not isinstance(domains_value, (list, tuple)):
        raise BrowserCanonicalizationError("cookieDomains must be an array")
    if not isinstance(bindings_value, Mapping):
        raise BrowserCanonicalizationError("executionBindings must be an object")

    origins: list[str] = []
    for origin in origins_value:
        if not isinstance(origin, str) or not origin:
            raise BrowserCanonicalizationError("selected origin must be a non-empty string")
        verifier.verify_canonical_origin(origin)
        origins.append(origin)
    if len(origins) != len(set(origins)):
        raise BrowserCanonicalizationError("duplicate localStorage origin selection")

    domains: list[str] = []
    for domain in domains_value:
        if not isinstance(domain, str) or not domain:
            raise BrowserCanonicalizationError("selected cookie domain must be non-empty")
        verifier.verify_canonical_cookie_domain(domain)
        domains.append(domain)
    if len(domains) != len(set(domains)):
        raise BrowserCanonicalizationError("duplicate cookie domain selection")

    bindings: dict[str, dict[str, str]] = {}
    for reference, binding in bindings_value.items():
        if not isinstance(reference, str) or not reference:
            raise BrowserCanonicalizationError("execution binding reference must be non-empty")
        if not isinstance(binding, Mapping):
            raise BrowserCanonicalizationError("execution binding must be an object")
        _require_exact_keys(binding, {"identity", "identityType"}, "execution binding")
        identity = binding["identity"]
        identity_type = binding["identityType"]
        if not isinstance(identity, str) or not identity:
            raise BrowserCanonicalizationError("execution binding identity must be non-empty")
        if identity_type not in {"content", "version", "symbolic"}:
            raise BrowserCanonicalizationError("unsupported execution binding identityType")
        bindings[reference] = {"identity": identity, "identityType": identity_type}

    return {
        **constants,
        "localStorageOrigins": sorted(origins, key=_origin_sort_key),
        "cookieDomains": sorted(domains, key=_domain_sort_key),
        "executionBindings": bindings,
    }


def canonical_manifest_bytes(
    manifest: Mapping[str, Any],
    verifier: BrowserIdentityVerifier,
) -> bytes:
    return _jcs_bytes(canonicalize_manifest(manifest, verifier))


def canonical_manifest_digest(
    manifest: Mapping[str, Any],
    verifier: BrowserIdentityVerifier,
) -> str:
    return _sha256_bytes(canonical_manifest_bytes(manifest, verifier))


def _canonical_local_storage(entries: Any) -> list[dict[str, str]]:
    if not isinstance(entries, (list, tuple)):
        raise BrowserCanonicalizationError("localStorage must be an array")
    result: list[tuple[tuple[int, ...], dict[str, str]]] = []
    seen: set[tuple[int, ...]] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise BrowserCanonicalizationError("localStorage entry must be an object")
        _require_exact_keys(entry, {"key", "value"}, "localStorage entry")
        key = entry["key"]
        value = entry["value"]
        if not isinstance(key, str) or not isinstance(value, str):
            raise BrowserCanonicalizationError("localStorage key/value must be strings")
        key_units = decode_dom_string_code_units(key)
        decode_dom_string_code_units(value)
        if key_units in seen:
            raise BrowserCanonicalizationError("duplicate localStorage key identity")
        seen.add(key_units)
        result.append((key_units, {"key": key, "value": value}))
    result.sort(key=lambda item: item[0])
    return [entry for _, entry in result]


def _canonical_cookie(
    cookie: Mapping[str, Any],
    verifier: BrowserIdentityVerifier,
) -> dict[str, Any]:
    persistent = cookie.get("persistent")
    if not isinstance(persistent, bool):
        raise BrowserCanonicalizationError("cookie persistent must be boolean")
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
    if persistent:
        required.add("expiry")
    _require_exact_keys(cookie, required, "cookie")

    name = cookie["name"]
    value = cookie["value"]
    path = cookie["path"]
    _cookie_octets(name, "cookie name")
    _cookie_octets(value, "cookie value")
    _cookie_octets(path, "cookie path")

    domain = cookie["domain"]
    if not isinstance(domain, str) or not domain:
        raise BrowserCanonicalizationError("cookie domain must be non-empty")
    verifier.verify_canonical_cookie_domain(domain)

    for field in ("hostOnly", "secure", "httpOnly"):
        if not isinstance(cookie[field], bool):
            raise BrowserCanonicalizationError(f"cookie {field} must be boolean")
    if cookie["sameSite"] not in _SAME_SITE:
        raise BrowserCanonicalizationError("cookie sameSite is outside Browser v0.1")

    result = {
        "name": name,
        "value": value,
        "domain": domain,
        "hostOnly": cookie["hostOnly"],
        "path": path,
        "persistent": persistent,
        "secure": cookie["secure"],
        "httpOnly": cookie["httpOnly"],
        "sameSite": cookie["sameSite"],
    }
    if persistent:
        expiry = cookie["expiry"]
        if not isinstance(expiry, Mapping):
            raise BrowserCanonicalizationError("persistent cookie expiry must be an object")
        _require_exact_keys(expiry, {"unixSeconds", "nanoseconds"}, "cookie expiry")
        unix_seconds = expiry["unixSeconds"]
        nanoseconds = expiry["nanoseconds"]
        if not isinstance(unix_seconds, str) or not _UNIX_SECONDS_RE.fullmatch(unix_seconds):
            raise BrowserCanonicalizationError("cookie unixSeconds is not canonical")
        if (
            isinstance(nanoseconds, bool)
            or not isinstance(nanoseconds, int)
            or nanoseconds < 0
            or nanoseconds > 999_999_999
        ):
            raise BrowserCanonicalizationError("cookie nanoseconds is outside canonical range")
        result["expiry"] = {"unixSeconds": unix_seconds, "nanoseconds": nanoseconds}
    return result


def _cookie_identity(cookie: Mapping[str, Any]) -> tuple[bytes, bytes, bool, bytes]:
    return (
        _cookie_octets(cookie["name"], "cookie name"),
        _domain_sort_key(cookie["domain"]),
        bool(cookie["hostOnly"]),
        _cookie_octets(cookie["path"], "cookie path"),
    )


def canonicalize_state_image(
    image: Mapping[str, Any],
    manifest: Mapping[str, Any],
    verifier: BrowserIdentityVerifier,
) -> dict[str, Any]:
    """Validate completeness and profile-order one BrowserStateImage."""

    canonical_manifest = canonicalize_manifest(manifest, verifier)
    manifest_digest = _sha256_bytes(_jcs_bytes(canonical_manifest))

    _require_exact_keys(
        image,
        {"apiVersion", "kind", "manifestDigest", "cookies", "origins"},
        "BrowserStateImage",
    )
    if image["apiVersion"] != _BROWSER_API_VERSION:
        raise BrowserCanonicalizationError("BrowserStateImage apiVersion mismatch")
    if image["kind"] != "BrowserStateImage":
        raise BrowserCanonicalizationError("BrowserStateImage kind mismatch")
    if image["manifestDigest"] != manifest_digest:
        raise BrowserCanonicalizationError(
            "BrowserStateImage does not bind exact Manifest digest"
        )
    if not _DIGEST_RE.fullmatch(str(image["manifestDigest"])):
        raise BrowserCanonicalizationError("BrowserStateImage manifestDigest is malformed")

    origins_value = image["origins"]
    cookies_value = image["cookies"]
    if not isinstance(origins_value, (list, tuple)):
        raise BrowserCanonicalizationError("BrowserStateImage origins must be an array")
    if not isinstance(cookies_value, (list, tuple)):
        raise BrowserCanonicalizationError("BrowserStateImage cookies must be an array")

    selected_origins = set(canonical_manifest["localStorageOrigins"])
    origins: list[dict[str, Any]] = []
    seen_origins: set[str] = set()
    for origin_state in origins_value:
        if not isinstance(origin_state, Mapping):
            raise BrowserCanonicalizationError("origin state must be an object")
        _require_exact_keys(origin_state, {"origin", "localStorage"}, "origin state")
        origin = origin_state["origin"]
        if not isinstance(origin, str) or not origin:
            raise BrowserCanonicalizationError("origin state identity must be non-empty")
        verifier.verify_canonical_origin(origin)
        if origin not in selected_origins:
            raise BrowserCanonicalizationError("StateImage contains an unselected origin")
        if origin in seen_origins:
            raise BrowserCanonicalizationError("duplicate StateImage origin identity")
        seen_origins.add(origin)
        origins.append(
            {
                "origin": origin,
                "localStorage": _canonical_local_storage(origin_state["localStorage"]),
            }
        )
    if seen_origins != selected_origins:
        raise BrowserCanonicalizationError(
            "StateImage does not contain every selected origin exactly once"
        )
    origins.sort(key=lambda item: _origin_sort_key(item["origin"]))

    selected_domains = set(canonical_manifest["cookieDomains"])
    cookies: list[dict[str, Any]] = []
    seen_cookie_ids: set[tuple[bytes, bytes, bool, bytes]] = set()
    for raw_cookie in cookies_value:
        if not isinstance(raw_cookie, Mapping):
            raise BrowserCanonicalizationError("cookie must be an object")
        cookie = _canonical_cookie(raw_cookie, verifier)
        if cookie["domain"] not in selected_domains:
            raise BrowserCanonicalizationError(
                "StateImage contains a cookie outside Manifest selection"
            )
        identity = _cookie_identity(cookie)
        if identity in seen_cookie_ids:
            raise BrowserCanonicalizationError("duplicate portable cookie identity")
        seen_cookie_ids.add(identity)
        cookies.append(cookie)
    cookies.sort(key=_cookie_identity)

    return {
        "apiVersion": _BROWSER_API_VERSION,
        "kind": "BrowserStateImage",
        "manifestDigest": manifest_digest,
        "cookies": cookies,
        "origins": origins,
    }


def canonical_state_image_bytes(
    image: Mapping[str, Any],
    manifest: Mapping[str, Any],
    verifier: BrowserIdentityVerifier,
) -> bytes:
    return _jcs_bytes(canonicalize_state_image(image, manifest, verifier))


def canonical_state_image_digest(
    image: Mapping[str, Any],
    manifest: Mapping[str, Any],
    verifier: BrowserIdentityVerifier,
) -> str:
    return _sha256_bytes(canonical_state_image_bytes(image, manifest, verifier))


@dataclass(frozen=True, slots=True)
class MaterializedBrowserFixture:
    """Immutable Browser fixture after exact execution origins are resolved."""

    fixture_revision: str
    manifest: Mapping[str, Any]
    baseline_image: Mapping[str, Any]
    manifest_bytes: bytes
    baseline_image_bytes: bytes
    manifest_digest: str
    baseline_image_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "manifest", _freeze(self.manifest))
        object.__setattr__(self, "baseline_image", _freeze(self.baseline_image))


def materialize_browser_fixture(
    source: Mapping[str, Any],
    *,
    resolved_origins: Mapping[str, str],
    verifier: BrowserIdentityVerifier,
) -> MaterializedBrowserFixture:
    """Resolve every origin slot before provisioning and freeze canonical identity."""

    _require_exact_keys(
        source,
        {
            "fixtureRevision",
            "originSlots",
            "selectedLocalStorageOriginSlots",
            "cookieDomains",
            "executionBindings",
            "baseline",
        },
        "Browser fixture source",
    )
    revision = source["fixtureRevision"]
    origin_slots = source["originSlots"]
    selected_slots = source["selectedLocalStorageOriginSlots"]
    if not isinstance(revision, str) or not revision:
        raise BrowserCanonicalizationError("fixtureRevision must be non-empty")
    if not isinstance(origin_slots, (list, tuple)) or not all(
        isinstance(slot, str) and slot for slot in origin_slots
    ):
        raise BrowserCanonicalizationError("originSlots must contain non-empty strings")
    if len(origin_slots) != len(set(origin_slots)):
        raise BrowserCanonicalizationError("originSlots must be duplicate-free")
    if set(resolved_origins) != set(origin_slots):
        raise BrowserCanonicalizationError("every origin slot must be resolved exactly once")
    if not isinstance(selected_slots, (list, tuple)) or not all(
        isinstance(slot, str) and slot for slot in selected_slots
    ):
        raise BrowserCanonicalizationError("selected origin slots must be strings")
    if len(selected_slots) != len(set(selected_slots)):
        raise BrowserCanonicalizationError("selected origin slots must be duplicate-free")
    if not set(selected_slots).issubset(set(origin_slots)):
        raise BrowserCanonicalizationError("selected origin slot is not declared")

    exact_origins: dict[str, str] = {}
    for slot in origin_slots:
        origin = resolved_origins[slot]
        if not isinstance(origin, str) or not origin:
            raise BrowserCanonicalizationError("resolved origin must be non-empty")
        verifier.verify_canonical_origin(origin)
        exact_origins[slot] = origin
    if len(set(exact_origins.values())) != len(exact_origins):
        raise BrowserCanonicalizationError("two origin slots resolved to the same tuple origin")

    cookie_domains = source["cookieDomains"]
    execution_bindings = source["executionBindings"]
    if not isinstance(cookie_domains, (list, tuple)):
        raise BrowserCanonicalizationError("fixture cookieDomains must be an array")
    if not isinstance(execution_bindings, Mapping):
        raise BrowserCanonicalizationError("fixture executionBindings must be an object")

    manifest = {
        "apiVersion": _BROWSER_API_VERSION,
        "kind": "BrowserStateManifest",
        "profile": _BROWSER_PROFILE,
        "revision": _BROWSER_REVISION,
        "canonicalRepresentation": _BROWSER_REPRESENTATION,
        "localStorageOrigins": [exact_origins[slot] for slot in selected_slots],
        "cookieDomains": list(cookie_domains),
        "executionBindings": _thaw(execution_bindings),
    }
    manifest = canonicalize_manifest(manifest, verifier)
    manifest_bytes = _jcs_bytes(manifest)
    manifest_digest = _sha256_bytes(manifest_bytes)

    baseline = source["baseline"]
    if not isinstance(baseline, Mapping):
        raise BrowserCanonicalizationError("fixture baseline must be an object")
    _require_exact_keys(
        baseline,
        {"localStorageByOriginSlot", "cookies"},
        "fixture baseline",
    )
    local_storage_by_slot = baseline["localStorageByOriginSlot"]
    cookies = baseline["cookies"]
    if not isinstance(local_storage_by_slot, Mapping):
        raise BrowserCanonicalizationError("localStorageByOriginSlot must be an object")
    if not isinstance(cookies, (list, tuple)):
        raise BrowserCanonicalizationError("fixture cookies must be an array")
    if set(local_storage_by_slot) != set(selected_slots):
        raise BrowserCanonicalizationError(
            "baseline localStorage must define every selected origin slot exactly once"
        )

    origins: list[dict[str, Any]] = []
    for slot in selected_slots:
        entries = local_storage_by_slot[slot]
        if not isinstance(entries, (list, tuple)):
            raise BrowserCanonicalizationError("fixture localStorage entries must be an array")
        encoded_entries: list[dict[str, str]] = []
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise BrowserCanonicalizationError("fixture localStorage entry must be an object")
            _require_exact_keys(
                entry,
                {"keyCodeUnits", "valueCodeUnits"},
                "fixture localStorage entry",
            )
            key_units = entry["keyCodeUnits"]
            value_units = entry["valueCodeUnits"]
            if not isinstance(key_units, (list, tuple)) or not isinstance(
                value_units, (list, tuple)
            ):
                raise BrowserCanonicalizationError(
                    "fixture DOMString code units must be arrays"
                )
            encoded_entries.append(
                {
                    "key": encode_dom_string_code_units(key_units),
                    "value": encode_dom_string_code_units(value_units),
                }
            )
        origins.append(
            {"origin": exact_origins[slot], "localStorage": encoded_entries}
        )

    image = {
        "apiVersion": _BROWSER_API_VERSION,
        "kind": "BrowserStateImage",
        "manifestDigest": manifest_digest,
        "cookies": _thaw(cookies),
        "origins": origins,
    }
    image = canonicalize_state_image(image, manifest, verifier)
    image_bytes = _jcs_bytes(image)
    image_digest = _sha256_bytes(image_bytes)
    return MaterializedBrowserFixture(
        fixture_revision=revision,
        manifest=manifest,
        baseline_image=image,
        manifest_bytes=manifest_bytes,
        baseline_image_bytes=image_bytes,
        manifest_digest=manifest_digest,
        baseline_image_digest=image_digest,
    )


class BrowserSettlementLedger:
    """Evaluator-owned positive settlement witness for one observation boundary."""

    def __init__(self) -> None:
        self._admission_open = True
        self._mutations: dict[str, bool] = {}

    @property
    def admission_open(self) -> bool:
        return self._admission_open

    @property
    def unresolved_mutations(self) -> tuple[str, ...]:
        return tuple(
            sorted(label for label, terminal in self._mutations.items() if not terminal)
        )

    def accept_relevant_mutation(self, label: str) -> None:
        if not self._admission_open:
            raise BrowserSettlementError("Subject side-effect admission is closed")
        if not label or label in self._mutations:
            raise BrowserSettlementError("mutation label must be unique and non-empty")
        self._mutations[label] = False

    def close_subject_admission(self) -> None:
        self._admission_open = False

    def mark_terminal(self, label: str) -> None:
        if label not in self._mutations or self._mutations[label]:
            raise BrowserSettlementError("mutation is not unresolved accepted work")
        self._mutations[label] = True

    def require_positive_witness(self) -> None:
        if self._admission_open:
            raise BrowserSettlementError("Subject side-effect admission is still open")
        unresolved = self.unresolved_mutations
        if unresolved:
            raise BrowserSettlementError(
                "accepted profile-relevant mutations remain unresolved: "
                f"{list(unresolved)}"
            )


@runtime_checkable
class BrowserSUT(Protocol):
    """Narrow Browser resource lifecycle visible to the conformance harness."""

    handle_id: str

    def snapshot(self) -> SnapshotRef: ...

    def reset(self) -> None: ...

    def restore(self, snapshot: SnapshotRef) -> None: ...

    def release(self) -> None: ...


@runtime_checkable
class BrowserAuthoritativeObserver(Protocol):
    """Evaluator-authorized observation path independent of SUT success claims."""

    def verify_execution_conditions(
        self,
        sut: BrowserSUT,
        fixture: MaterializedBrowserFixture,
    ) -> None: ...

    def verify_restore_eligibility(
        self,
        sut: BrowserSUT,
        fixture: MaterializedBrowserFixture,
        snapshot: SnapshotRef,
    ) -> None: ...

    def project_selected_state(
        self,
        sut: BrowserSUT,
        fixture: MaterializedBrowserFixture,
    ) -> Mapping[str, Any]: ...


@runtime_checkable
class BrowserFixtureControl(Protocol):
    """Privileged logical controls deliberately absent from ``BrowserSUT``."""

    def seed_baseline(
        self,
        sut: BrowserSUT,
        fixture: MaterializedBrowserFixture,
    ) -> None: ...

    def seed_cookie(
        self,
        sut: BrowserSUT,
        cookie: Mapping[str, Any],
        *,
        provenance: Mapping[str, Any] | None = None,
    ) -> None: ...

    def seed_local_storage(
        self,
        sut: BrowserSUT,
        origin: str,
        entries: Sequence[Mapping[str, str]],
    ) -> None: ...

    def seed_partitioned_cookie(
        self,
        sut: BrowserSUT,
        cookie: Mapping[str, Any],
    ) -> None: ...

    def set_execution_binding(
        self,
        sut: BrowserSUT,
        reference: str,
        identity: str,
    ) -> None: ...

    def set_excluded_state_interference(
        self,
        sut: BrowserSUT,
        *,
        interfering: bool,
    ) -> None: ...

    def seed_evaluator_private_state(self, sut: BrowserSUT) -> None: ...


@runtime_checkable
class BrowserBackendHarness(Protocol):
    """Provider-independent factory/observer/control composition for Browser TCK."""

    @property
    def observer(self) -> BrowserAuthoritativeObserver: ...

    @property
    def fixture_control(self) -> BrowserFixtureControl: ...

    def provision(self, fixture: MaterializedBrowserFixture) -> BrowserSUT: ...


class BrowserConformanceHarness:
    """Shared fail-closed lifecycle verifier for Browser backend implementations."""

    def __init__(
        self,
        backend: BrowserBackendHarness,
        fixture: MaterializedBrowserFixture,
        verifier: BrowserIdentityVerifier,
    ) -> None:
        self._backend = backend
        self._fixture = fixture
        self._verifier = verifier
        self._snapshot_targets: dict[str, tuple[str, str]] = {}

    @property
    def fixture_control(self) -> BrowserFixtureControl:
        return self._backend.fixture_control

    def provision(self) -> BrowserSUT:
        return self._backend.provision(self._fixture)

    def authoritative_projection(
        self,
        sut: BrowserSUT,
        settlement: BrowserSettlementLedger,
    ) -> StateProjection:
        settlement.require_positive_witness()
        self._backend.observer.verify_execution_conditions(sut, self._fixture)
        raw = self._backend.observer.project_selected_state(sut, self._fixture)
        canonical = canonicalize_state_image(
            raw,
            self._fixture.manifest,
            self._verifier,
        )
        digest = _sha256_bytes(_jcs_bytes(canonical))
        return StateProjection(
            projection_id="browser.authoritative",
            data=canonical,
            digest=digest,
        )

    def verified_snapshot(
        self,
        sut: BrowserSUT,
        settlement: BrowserSettlementLedger,
    ) -> SnapshotRef:
        observed = self.authoritative_projection(sut, settlement)
        snapshot = sut.snapshot()
        if snapshot.handle_id != sut.handle_id:
            raise BrowserVerificationError(
                "snapshot is not owned by the Browser resource handle"
            )
        if snapshot.state_digest != observed.digest:
            raise BrowserVerificationError(
                "snapshot state digest does not match independent authoritative projection"
            )
        previous = self._snapshot_targets.get(snapshot.snapshot_id)
        target = (snapshot.handle_id, observed.digest)
        if previous is not None and previous != target:
            raise BrowserVerificationError(
                "snapshot id was reused for different Browser state"
            )
        self._snapshot_targets[snapshot.snapshot_id] = target
        return snapshot

    def verified_reset(
        self,
        sut: BrowserSUT,
        before_settlement: BrowserSettlementLedger,
        after_settlement: BrowserSettlementLedger,
    ) -> ResetResult:
        before = self.authoritative_projection(sut, before_settlement)
        sut.reset()
        after = self.authoritative_projection(sut, after_settlement)
        if after.digest != self._fixture.baseline_image_digest:
            raise BrowserVerificationError(
                "reset command completed without re-establishing canonical baseline state"
            )
        return ResetResult(
            handle_id=sut.handle_id,
            target=ResetTarget.INITIAL,
            before_digest=before.digest,
            after_digest=after.digest,
            equivalent_to_initial=True,
        )

    def verified_restore(
        self,
        sut: BrowserSUT,
        snapshot: SnapshotRef,
        before_settlement: BrowserSettlementLedger,
        after_settlement: BrowserSettlementLedger,
    ) -> RestoreResult:
        if snapshot.handle_id != sut.handle_id:
            raise BrowserVerificationError("foreign Browser SnapshotRef")
        expected = self._snapshot_targets.get(snapshot.snapshot_id)
        if expected is None:
            raise BrowserVerificationError("stale or unknown Browser SnapshotRef")
        expected_handle, expected_digest = expected
        if expected_handle != sut.handle_id or expected_digest != snapshot.state_digest:
            raise BrowserVerificationError(
                "Browser SnapshotRef ownership/state binding changed"
            )

        before = self.authoritative_projection(sut, before_settlement)
        self._backend.observer.verify_restore_eligibility(
            sut,
            self._fixture,
            snapshot,
        )
        sut.restore(snapshot)
        after = self.authoritative_projection(sut, after_settlement)
        if after.digest != expected_digest:
            raise BrowserVerificationError(
                "restore command completed without independently reprojecting target state"
            )
        return RestoreResult(
            snapshot_id=snapshot.snapshot_id,
            before_digest=before.digest,
            after_digest=after.digest,
            equivalence=RestoreEquivalence.STATE_EQUIVALENT,
        )

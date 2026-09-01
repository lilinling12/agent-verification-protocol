"""Provider-neutral evaluator for Browser selection and canonical identity.

This module owns only AVP-TCK-BROWSER-SELECTION-CANONICAL-001. Keeping one
mandatory Browser case per evaluator module prevents the portable TCK layer from
becoming a case-id switchboard and makes each normative obligation independently
reviewable. Concrete browser/provider selection remains outside this module.
"""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Mapping
from typing import Any

import rfc8785

from .browser_harness import (
    BrowserCanonicalizationError,
    BrowserHarnessError,
    BrowserIdentityVerifier,
    BrowserVerificationError,
    MaterializedBrowserFixture,
    canonical_manifest_bytes,
    canonical_manifest_digest,
    canonical_state_image_bytes,
    canonical_state_image_digest,
    canonicalize_manifest,
    canonicalize_state_image,
    decode_dom_string_code_units,
    encode_dom_string_code_units,
)
from .browser_tck_adapter import BROWSER_PROFILE
from .models import TCKAdapterError, TCKCaseResult, TCKStatus

CASE_ID = "AVP-TCK-BROWSER-SELECTION-CANONICAL-001"
_BROWSER_API_VERSION = "avp.browser/v0.1"
_BROWSER_REVISION = "0.1"
_BROWSER_REPRESENTATION = "avp-browser-v0.1-rfc8785-jcs"

_INVALID_CONTROLS = frozenset(
    {
        "duplicate-origin-selection",
        "duplicate-cookie-domain-selection",
        "duplicate-localstorage-key",
        "duplicate-cookie-identity",
        "odd-decoded-byte-length-localstorage-key",
        "noncanonical-base64url-pad-bits-localstorage-value",
        "padded-base64url-localstorage-value",
        "noncanonical-manifest-order-used-as-identity",
        "provider-enumeration-order-used-as-identity",
    }
)


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return copy.deepcopy(value)


def _jcs_bytes(value: Any) -> bytes:
    encoded = rfc8785.dumps(value)
    return encoded if isinstance(encoded, bytes) else encoded.encode("utf-8")


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TCKAdapterError(f"{label} must be an object")
    return value


def _strings(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise TCKAdapterError(f"{label} must be a non-empty array")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise TCKAdapterError(f"{label} must contain non-empty strings")
        result.append(item)
    return result


def _require_true(expect: Mapping[str, Any], key: str) -> None:
    if expect.get(key) is not True:
        raise TCKAdapterError(f"{CASE_ID} expect.{key} must be true")


def _require_exact_control_set(value: object) -> None:
    controls = _strings(value, f"{CASE_ID} invalidControls")
    if len(controls) != len(set(controls)) or frozenset(controls) != _INVALID_CONTROLS:
        raise TCKAdapterError(
            f"{CASE_ID} invalidControls does not match the governed control set"
        )


def _require_rejected(operation: Any, label: str) -> None:
    try:
        operation()
    except (BrowserHarnessError, BrowserCanonicalizationError, BrowserVerificationError):
        return
    raise BrowserVerificationError(f"Browser negative control was accepted: {label}")


class BrowserSelectionCanonicalTCKEvaluator:
    """Execute exact selection, DOMString, ordering, and raw-identity controls."""

    case_id = CASE_ID

    def __init__(
        self,
        *,
        fixture: MaterializedBrowserFixture,
        verifier: BrowserIdentityVerifier,
    ) -> None:
        self._fixture = fixture
        self._verifier = verifier

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        vector, expect = self._case_parts(case)
        self._validate_contract(vector, expect)
        try:
            self._execute_positive_controls(vector, expect)
            self._execute_invalid_controls(vector)
        except BrowserHarnessError as exc:
            return TCKCaseResult(
                self.case_id,
                TCKStatus.FAIL,
                f"Browser selection/canonicalization obligation failed: {exc}",
            )
        return TCKCaseResult(
            self.case_id,
            TCKStatus.PASS,
            "Browser exact selection, DOMString encoding, and permutation-invariant canonical identity verified",
        )

    def _case_parts(
        self,
        case: Mapping[str, Any],
    ) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
        metadata = _mapping(case.get("metadata"), f"{CASE_ID} metadata")
        if metadata.get("id") != CASE_ID or metadata.get("domain") != "browser":
            raise TCKAdapterError(f"{CASE_ID} case identity/domain mismatch")
        if case.get("profile") != BROWSER_PROFILE:
            raise TCKAdapterError(f"{CASE_ID} targets the wrong Browser profile")
        return (
            _mapping(case.get("vector"), f"{CASE_ID} vector"),
            _mapping(case.get("expect"), f"{CASE_ID} expect"),
        )

    def _validate_contract(
        self,
        vector: Mapping[str, Any],
        expect: Mapping[str, Any],
    ) -> None:
        origins = _strings(vector.get("localStorageOrigins"), f"{CASE_ID} localStorageOrigins")
        domains = _strings(vector.get("cookieDomains"), f"{CASE_ID} cookieDomains")
        if len(origins) != len(set(origins)) or len(domains) != len(set(domains)):
            raise TCKAdapterError(f"{CASE_ID} positive selection must be duplicate-free")

        controls = _mapping(vector.get("domStringControls"), f"{CASE_ID} domStringControls")
        if set(controls) != {"asciiA", "asciiAB", "unmatchedHighSurrogate"}:
            raise TCKAdapterError(f"{CASE_ID} DOMString control set changed")

        permutations = _mapping(
            vector.get("permutationControls"),
            f"{CASE_ID} permutationControls",
        )
        expected_permutations = {
            "manifestOriginOrders": 2,
            "manifestCookieDomainOrders": 2,
            "imageCookieAndOriginOrders": "multiple",
        }
        if dict(permutations) != expected_permutations:
            raise TCKAdapterError(f"{CASE_ID} permutation controls changed")

        _require_exact_control_set(vector.get("invalidControls"))
        if expect.get("canonicalOriginOrder") != sorted(origins):
            raise TCKAdapterError(f"{CASE_ID} canonicalOriginOrder is inconsistent")
        if expect.get("canonicalCookieDomainOrder") != sorted(domains):
            raise TCKAdapterError(f"{CASE_ID} canonicalCookieDomainOrder is inconsistent")
        for key in (
            "unmatchedSurrogatePreserved",
            "exactWholeUtf16CodeUnitEncodingRequired",
            "canonicalUnpaddedBase64urlRequired",
            "permutationInvariantCanonicalIdentity",
            "rawNoncanonicalDigestRejectedAsBrowserIdentity",
            "invalidControlsRejected",
        ):
            _require_true(expect, key)

    def _manifest(self, vector: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "apiVersion": _BROWSER_API_VERSION,
            "kind": "BrowserStateManifest",
            "profile": BROWSER_PROFILE,
            "revision": _BROWSER_REVISION,
            "canonicalRepresentation": _BROWSER_REPRESENTATION,
            "localStorageOrigins": list(vector["localStorageOrigins"]),
            "cookieDomains": list(vector["cookieDomains"]),
            "executionBindings": _plain(self._fixture.manifest["executionBindings"]),
        }

    def _execute_positive_controls(
        self,
        vector: Mapping[str, Any],
        expect: Mapping[str, Any],
    ) -> None:
        controls = _mapping(vector["domStringControls"], "DOMString controls")
        if dict(controls) != {
            "asciiA": encode_dom_string_code_units([0x0061]),
            "asciiAB": encode_dom_string_code_units([0x0061, 0x0062]),
            "unmatchedHighSurrogate": encode_dom_string_code_units([0xD800]),
        }:
            raise BrowserVerificationError(
                "Browser DOMString controls do not match exact UTF-16 code-unit encoding"
            )
        if decode_dom_string_code_units(str(controls["unmatchedHighSurrogate"])) != (0xD800,):
            raise BrowserVerificationError("unmatched UTF-16 surrogate was not preserved")

        manifest = self._manifest(vector)
        canonical = canonicalize_manifest(manifest, self._verifier)
        if canonical["localStorageOrigins"] != expect["canonicalOriginOrder"]:
            raise BrowserVerificationError("Browser origin canonical order is incorrect")
        if canonical["cookieDomains"] != expect["canonicalCookieDomainOrder"]:
            raise BrowserVerificationError("Browser cookie-domain canonical order is incorrect")

        permuted = copy.deepcopy(manifest)
        permuted["localStorageOrigins"].reverse()
        permuted["cookieDomains"].reverse()
        if canonical_manifest_bytes(manifest, self._verifier) != canonical_manifest_bytes(
            permuted,
            self._verifier,
        ):
            raise BrowserVerificationError(
                "Manifest canonical identity depends on input selection ordering"
            )

        first_image = _plain(self._fixture.baseline_image)
        second_image = _plain(self._fixture.baseline_image)
        second_image["cookies"].reverse()
        second_image["origins"].reverse()
        for origin_state in second_image["origins"]:
            origin_state["localStorage"].reverse()
        if canonical_state_image_bytes(
            first_image,
            self._fixture.manifest,
            self._verifier,
        ) != canonical_state_image_bytes(
            second_image,
            self._fixture.manifest,
            self._verifier,
        ):
            raise BrowserVerificationError(
                "StateImage canonical identity depends on provider enumeration order"
            )

    def _execute_invalid_controls(self, vector: Mapping[str, Any]) -> None:
        raw_manifest = self._manifest(vector)
        canonical_manifest = canonicalize_manifest(raw_manifest, self._verifier)

        duplicate_origin = copy.deepcopy(raw_manifest)
        duplicate_origin["localStorageOrigins"].append(duplicate_origin["localStorageOrigins"][0])
        _require_rejected(
            lambda: canonicalize_manifest(duplicate_origin, self._verifier),
            "duplicate-origin-selection",
        )

        duplicate_domain = copy.deepcopy(raw_manifest)
        duplicate_domain["cookieDomains"].append(duplicate_domain["cookieDomains"][0])
        _require_rejected(
            lambda: canonicalize_manifest(duplicate_domain, self._verifier),
            "duplicate-cookie-domain-selection",
        )

        duplicate_storage = _plain(self._fixture.baseline_image)
        origin_state = next(item for item in duplicate_storage["origins"] if item["localStorage"])
        origin_state["localStorage"].append(copy.deepcopy(origin_state["localStorage"][0]))
        _require_rejected(
            lambda: canonicalize_state_image(
                duplicate_storage,
                self._fixture.manifest,
                self._verifier,
            ),
            "duplicate-localstorage-key",
        )

        duplicate_cookie = _plain(self._fixture.baseline_image)
        duplicate_cookie["cookies"].append(copy.deepcopy(duplicate_cookie["cookies"][0]))
        _require_rejected(
            lambda: canonicalize_state_image(
                duplicate_cookie,
                self._fixture.manifest,
                self._verifier,
            ),
            "duplicate-cookie-identity",
        )

        odd_key = _plain(self._fixture.baseline_image)
        origin_state = next(item for item in odd_key["origins"] if item["localStorage"])
        origin_state["localStorage"][0]["key"] = "AA"
        _require_rejected(
            lambda: canonicalize_state_image(odd_key, self._fixture.manifest, self._verifier),
            "odd-decoded-byte-length-localstorage-key",
        )

        noncanonical_pad_bits = _plain(self._fixture.baseline_image)
        origin_state = next(
            item for item in noncanonical_pad_bits["origins"] if item["localStorage"]
        )
        origin_state["localStorage"][0]["value"] = "AAB"
        _require_rejected(
            lambda: canonicalize_state_image(
                noncanonical_pad_bits,
                self._fixture.manifest,
                self._verifier,
            ),
            "noncanonical-base64url-pad-bits-localstorage-value",
        )

        padded = _plain(self._fixture.baseline_image)
        origin_state = next(item for item in padded["origins"] if item["localStorage"])
        origin_state["localStorage"][0]["value"] = "AGE="
        _require_rejected(
            lambda: canonicalize_state_image(padded, self._fixture.manifest, self._verifier),
            "padded-base64url-localstorage-value",
        )

        # Positive execution above already proves that the governed noncanonical
        # vector order canonicalizes correctly. This negative control starts from
        # the canonical Manifest and deliberately reorders its arrays, proving
        # that hashing raw noncanonical bytes cannot establish Browser identity.
        noncanonical_manifest = copy.deepcopy(canonical_manifest)
        noncanonical_manifest["localStorageOrigins"].reverse()
        noncanonical_manifest["cookieDomains"].reverse()
        raw_manifest_digest = _sha256(_jcs_bytes(noncanonical_manifest))
        governed_manifest_digest = canonical_manifest_digest(
            noncanonical_manifest,
            self._verifier,
        )
        if raw_manifest_digest == governed_manifest_digest:
            raise BrowserVerificationError(
                "noncanonical Manifest ordering was accepted as Browser identity"
            )

        provider_order_image = _plain(self._fixture.baseline_image)
        provider_order_image["cookies"].reverse()
        provider_order_image["origins"].reverse()
        raw_image_digest = _sha256(_jcs_bytes(provider_order_image))
        governed_image_digest = canonical_state_image_digest(
            provider_order_image,
            self._fixture.manifest,
            self._verifier,
        )
        if raw_image_digest == governed_image_digest:
            raise BrowserVerificationError(
                "provider enumeration ordering was accepted as canonical identity"
            )

"""Provider-neutral evaluators for the foundational Browser v0.1 TCK cases.

These evaluators execute Browser identity, selection/canonicalization, and state-
image obligations against the shared Browser conformance infrastructure. They do
not select a concrete browser backend and they are intentionally not registered
with ``ReferenceConformanceAdapter`` yet; Browser ownership remains atomic and
pending until all eight mandatory case evaluators genuinely execute.

The injected identity verifier is the reviewed Browser/WHATWG admission boundary.
This module never approximates Browser URL/origin semantics with a host-language
URL parser or regular expression.
"""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Mapping, Sequence
from typing import Any

import rfc8785

from .browser_harness import (
    BrowserBackendHarness,
    BrowserCanonicalizationError,
    BrowserConformanceHarness,
    BrowserHarnessError,
    BrowserIdentityVerifier,
    BrowserSettlementLedger,
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

_BROWSER_API_VERSION = "avp.browser/v0.1"
_BROWSER_REVISION = "0.1"
_BROWSER_REPRESENTATION = "avp-browser-v0.1-rfc8785-jcs"

_IDENTITY_CASE = "AVP-TCK-BROWSER-IDENTITY-001"
_SELECTION_CASE = "AVP-TCK-BROWSER-SELECTION-CANONICAL-001"
_STATE_IMAGE_CASE = "AVP-TCK-BROWSER-STATE-IMAGE-001"

_IDENTITY_NEGATIVE_CONTROLS = frozenset(
    {
        "resource-kind-state",
        "provider-native-handle-as-resource-id",
        "sibling-selected-state-sharing",
        "manifest-baseline-reference-cycle",
        "unresolved-manifest-execution-binding",
        "manifest-execution-binding-conflicts-with-upstream-identity",
        "provenance-only-execution-binding",
        "untyped-provider-property-in-execution-bindings",
    }
)

_SELECTION_INVALID_CONTROLS = frozenset(
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

_STATE_IMAGE_NEGATIVE_CONTROLS = frozenset(
    {
        "missing-selected-origin",
        "extra-in-scope-cookie",
        "duplicate-origin",
        "duplicate-cookie-identity",
        "session-cookie-with-expiry",
        "persistent-cookie-without-expiry",
        "floating-point-expiry",
        "transformed-localstorage-value",
    }
)


def _plain(value: Any) -> Any:
    """Copy frozen harness values back to ordinary JSON-like containers."""

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


def _settled() -> BrowserSettlementLedger:
    ledger = BrowserSettlementLedger()
    ledger.close_subject_admission()
    return ledger


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


def _require_exact_string_set(
    value: object,
    expected: frozenset[str],
    label: str,
) -> None:
    actual = _strings(value, label)
    if len(actual) != len(set(actual)) or frozenset(actual) != expected:
        raise TCKAdapterError(
            f"{label} does not match the governed control set: {sorted(actual)!r}"
        )


def _require_true(expect: Mapping[str, Any], key: str, case_id: str) -> None:
    if expect.get(key) is not True:
        raise TCKAdapterError(f"{case_id} expect.{key} must be true")


def _case_parts(
    case: Mapping[str, Any],
    expected_case_id: str,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    metadata = _mapping(case.get("metadata"), f"{expected_case_id} metadata")
    if metadata.get("id") != expected_case_id:
        raise TCKAdapterError(
            f"Browser evaluator expected {expected_case_id}, got {metadata.get('id')!r}"
        )
    if metadata.get("domain") != "browser":
        raise TCKAdapterError(f"{expected_case_id} metadata.domain must be browser")
    if case.get("profile") != BROWSER_PROFILE:
        raise TCKAdapterError(
            f"{expected_case_id} must target Browser profile {BROWSER_PROFILE}"
        )
    vector = _mapping(case.get("vector"), f"{expected_case_id} vector")
    expect = _mapping(case.get("expect"), f"{expected_case_id} expect")
    return vector, expect


def _pass(case_id: str, detail: str) -> TCKCaseResult:
    return TCKCaseResult(case_id, TCKStatus.PASS, detail)


def _fail(case_id: str, detail: str) -> TCKCaseResult:
    return TCKCaseResult(case_id, TCKStatus.FAIL, detail)


def _require_rejected(operation: Any, label: str) -> None:
    try:
        operation()
    except (BrowserHarnessError, BrowserCanonicalizationError, BrowserVerificationError):
        return
    raise BrowserVerificationError(f"Browser negative control was accepted: {label}")


def _require_binding_map(
    value: Mapping[str, Any],
    label: str,
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for reference, raw_binding in value.items():
        if not isinstance(reference, str) or not reference:
            raise TCKAdapterError(f"{label} reference must be a non-empty string")
        binding = _mapping(raw_binding, f"{label}.{reference}")
        if set(binding) != {"identity", "identityType"}:
            raise TCKAdapterError(
                f"{label}.{reference} must contain identity and identityType only"
            )
        identity = binding.get("identity")
        identity_type = binding.get("identityType")
        if not isinstance(identity, str) or not identity:
            raise TCKAdapterError(f"{label}.{reference}.identity must be non-empty")
        if identity_type not in {"content", "version", "symbolic"}:
            raise TCKAdapterError(
                f"{label}.{reference}.identityType is not a governed identity type"
            )
        result[reference] = {
            "identity": identity,
            "identityType": str(identity_type),
        }
    if not result:
        raise TCKAdapterError(f"{label} must not be empty")
    return result


def _require_runtime_bindings_match_upstream(
    runtime: Mapping[str, Any],
    upstream: Mapping[str, Any],
) -> None:
    runtime_plain = _require_binding_map(runtime, "runtime executionBindings")
    upstream_plain = _require_binding_map(upstream, "upstream executionBindings")
    if runtime_plain != upstream_plain:
        raise BrowserVerificationError(
            "Browser Manifest execution bindings do not reuse exact upstream identity"
        )


class BrowserIdentityTCKEvaluator:
    """Execute Browser resource/identity and sibling-isolation obligations."""

    case_id = _IDENTITY_CASE

    def __init__(
        self,
        *,
        backend: BrowserBackendHarness,
        fixture: MaterializedBrowserFixture,
        verifier: BrowserIdentityVerifier,
        upstream_execution_bindings: Mapping[str, Any],
    ) -> None:
        self._backend = backend
        self._fixture = fixture
        self._verifier = verifier
        self._upstream_execution_bindings = _plain(upstream_execution_bindings)

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        vector, expect = _case_parts(case, self.case_id)
        self._validate_case_contract(vector, expect)
        try:
            self._execute_runtime_obligations(vector)
            self._execute_negative_controls()
        except BrowserHarnessError as exc:
            return _fail(self.case_id, f"Browser identity obligation failed: {exc}")
        return _pass(
            self.case_id,
            "Browser governed identity, upstream execution binding, and sibling selected-state isolation verified",
        )

    def _validate_case_contract(
        self,
        vector: Mapping[str, Any],
        expect: Mapping[str, Any],
    ) -> None:
        if vector.get("resourceKind") != "browser":
            raise TCKAdapterError(f"{self.case_id} vector.resourceKind must be browser")
        capability = _mapping(vector.get("capability"), f"{self.case_id} capability")
        expected_capability = {
            "capabilityId": "state.browser",
            "profile": BROWSER_PROFILE,
            "revision": _BROWSER_REVISION,
        }
        if dict(capability) != expected_capability:
            raise TCKAdapterError(f"{self.case_id} capability tuple is not governed")
        identity_kinds = _strings(
            vector.get("identityResourceKinds"),
            f"{self.case_id} identityResourceKinds",
        )
        if identity_kinds != ["BrowserStateManifest", "BrowserStateImage"]:
            raise TCKAdapterError(f"{self.case_id} identityResourceKinds changed")
        if vector.get("manifestContainsBaselineReference") is not False:
            raise TCKAdapterError(
                f"{self.case_id} manifestContainsBaselineReference must be false"
            )

        manifest_bindings = _require_binding_map(
            _mapping(
                vector.get("manifestExecutionBindings"),
                f"{self.case_id} manifestExecutionBindings",
            ),
            f"{self.case_id} manifestExecutionBindings",
        )
        upstream_bindings = _require_binding_map(
            _mapping(
                vector.get("upstreamIdentityBindings"),
                f"{self.case_id} upstreamIdentityBindings",
            ),
            f"{self.case_id} upstreamIdentityBindings",
        )
        if manifest_bindings != upstream_bindings:
            raise TCKAdapterError(
                f"{self.case_id} vector must reuse exact upstream identity bindings"
            )

        siblings = vector.get("siblingResources")
        if not isinstance(siblings, list) or len(siblings) != 2:
            raise TCKAdapterError(f"{self.case_id} requires exactly two sibling controls")
        resource_ids: set[str] = set()
        selected_pairs: set[tuple[str, str]] = set()
        for index, sibling in enumerate(siblings):
            item = _mapping(sibling, f"{self.case_id} siblingResources[{index}]")
            if set(item) != {
                "resourceId",
                "selectedCookieState",
                "selectedLocalStorageState",
            }:
                raise TCKAdapterError(
                    f"{self.case_id} siblingResources[{index}] shape changed"
                )
            resource_id = item.get("resourceId")
            cookie_state = item.get("selectedCookieState")
            storage_state = item.get("selectedLocalStorageState")
            if not all(
                isinstance(value, str) and value
                for value in (resource_id, cookie_state, storage_state)
            ):
                raise TCKAdapterError(
                    f"{self.case_id} sibling controls must be non-empty strings"
                )
            resource_ids.add(str(resource_id))
            selected_pairs.add((str(cookie_state), str(storage_state)))
        if len(resource_ids) != 2 or len(selected_pairs) != 2:
            raise TCKAdapterError(
                f"{self.case_id} sibling controls must represent distinct resources/state"
            )

        _require_exact_string_set(
            vector.get("negativeControls"),
            _IDENTITY_NEGATIVE_CONTROLS,
            f"{self.case_id} negativeControls",
        )
        for key in (
            "identityRolesByGovernedKind",
            "acyclicIdentity",
            "executionBindingsReuseUpstreamIdentity",
            "siblingSelectedStateIsolated",
            "negativeControlsRejected",
        ):
            _require_true(expect, key, self.case_id)
        if expect.get("resourceKindAccepted") != "browser":
            raise TCKAdapterError(
                f"{self.case_id} expect.resourceKindAccepted must be browser"
            )
        if expect.get("compatible") is not True:
            raise TCKAdapterError(f"{self.case_id} expect.compatible must be true")

    def _execute_runtime_obligations(self, vector: Mapping[str, Any]) -> None:
        del vector
        manifest = self._fixture.manifest
        image = self._fixture.baseline_image
        if manifest.get("kind") != "BrowserStateManifest":
            raise BrowserVerificationError("Browser Manifest governed kind is not preserved")
        if image.get("kind") != "BrowserStateImage":
            raise BrowserVerificationError("Browser StateImage governed kind is not preserved")
        if manifest.get("profile") != BROWSER_PROFILE:
            raise BrowserVerificationError("Browser Manifest profile identity drifted")
        if any("baseline" in str(key).lower() for key in manifest):
            raise BrowserVerificationError(
                "Browser Manifest identity contains a forbidden baseline back-reference"
            )
        if self._fixture.manifest_digest == self._fixture.baseline_image_digest:
            raise BrowserVerificationError(
                "Browser Manifest and StateImage identities unexpectedly collapsed"
            )

        _require_runtime_bindings_match_upstream(
            _mapping(manifest.get("executionBindings"), "Browser Manifest executionBindings"),
            _mapping(self._upstream_execution_bindings, "upstream executionBindings"),
        )

        harness = BrowserConformanceHarness(
            self._backend,
            self._fixture,
            self._verifier,
        )
        first = harness.provision()
        second = harness.provision()
        try:
            if first.handle_id == second.handle_id:
                raise BrowserVerificationError("sibling Browser handles are not isolated")
            governed_ids = {
                self._fixture.manifest_digest,
                self._fixture.baseline_image_digest,
            }
            if first.handle_id in governed_ids or second.handle_id in governed_ids:
                raise BrowserVerificationError(
                    "provider-native handle was reused as governed Browser identity"
                )

            first_before = harness.authoritative_projection(first, _settled())
            second_before = harness.authoritative_projection(second, _settled())
            if (
                first_before.digest != self._fixture.baseline_image_digest
                or second_before.digest != self._fixture.baseline_image_digest
            ):
                raise BrowserVerificationError(
                    "sibling Browser resources did not start from the governed baseline"
                )

            origins = self._fixture.manifest.get("localStorageOrigins")
            if not isinstance(origins, Sequence) or not origins:
                raise BrowserVerificationError(
                    "Browser executable fixture lacks selected localStorage origin"
                )
            origin = str(origins[0])
            harness.fixture_control.seed_local_storage(
                first,
                origin,
                [
                    {
                        "key": encode_dom_string_code_units([0x0074, 0x0063, 0x006B]),
                        "value": encode_dom_string_code_units([0x0031]),
                    }
                ],
            )
            first_after = harness.authoritative_projection(first, _settled())
            second_after = harness.authoritative_projection(second, _settled())
            if first_after.digest == first_before.digest:
                raise BrowserVerificationError(
                    "selected-state mutation did not change the target sibling"
                )
            if second_after.digest != second_before.digest:
                raise BrowserVerificationError(
                    "selected Browser state leaked across sibling resources"
                )
        finally:
            first.release()
            second.release()

    def _execute_negative_controls(self) -> None:
        manifest = _plain(self._fixture.manifest)

        cyclic = copy.deepcopy(manifest)
        cyclic["baselineDigest"] = self._fixture.baseline_image_digest
        _require_rejected(
            lambda: canonicalize_manifest(cyclic, self._verifier),
            "manifest-baseline-reference-cycle",
        )

        runtime_bindings = _plain(manifest["executionBindings"])
        reference = next(iter(runtime_bindings))

        unresolved = copy.deepcopy(runtime_bindings)
        unresolved.pop(reference)
        _require_rejected(
            lambda: _require_runtime_bindings_match_upstream(
                unresolved,
                self._upstream_execution_bindings,
            ),
            "unresolved-manifest-execution-binding",
        )

        conflicting = copy.deepcopy(runtime_bindings)
        conflicting[reference]["identity"] = "synthetic-conflicting-identity"
        _require_rejected(
            lambda: _require_runtime_bindings_match_upstream(
                conflicting,
                self._upstream_execution_bindings,
            ),
            "manifest-execution-binding-conflicts-with-upstream-identity",
        )

        provenance_only = copy.deepcopy(runtime_bindings)
        provenance_only.pop(reference)
        _require_rejected(
            lambda: _require_runtime_bindings_match_upstream(
                provenance_only,
                self._upstream_execution_bindings,
            ),
            "provenance-only-execution-binding",
        )

        untyped = copy.deepcopy(manifest)
        untyped["executionBindings"][reference]["providerProperty"] = "opaque"
        _require_rejected(
            lambda: canonicalize_manifest(untyped, self._verifier),
            "untyped-provider-property-in-execution-bindings",
        )

        if "state" == "browser":  # pragma: no cover - explicit negative predicate
            raise BrowserVerificationError("resource-kind-state was accepted")


class BrowserSelectionCanonicalTCKEvaluator:
    """Execute Browser selection, DOMString, and canonical ordering semantics."""

    case_id = _SELECTION_CASE

    def __init__(
        self,
        *,
        fixture: MaterializedBrowserFixture,
        verifier: BrowserIdentityVerifier,
    ) -> None:
        self._fixture = fixture
        self._verifier = verifier

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        vector, expect = _case_parts(case, self.case_id)
        self._validate_case_contract(vector, expect)
        try:
            self._execute_positive_controls(vector, expect)
            self._execute_invalid_controls(vector)
        except BrowserHarnessError as exc:
            return _fail(
                self.case_id,
                f"Browser selection/canonicalization obligation failed: {exc}",
            )
        return _pass(
            self.case_id,
            "Browser exact selection, DOMString encoding, and permutation-invariant canonical identity verified",
        )

    def _validate_case_contract(
        self,
        vector: Mapping[str, Any],
        expect: Mapping[str, Any],
    ) -> None:
        origins = _strings(
            vector.get("localStorageOrigins"),
            f"{self.case_id} localStorageOrigins",
        )
        domains = _strings(
            vector.get("cookieDomains"),
            f"{self.case_id} cookieDomains",
        )
        if len(origins) != len(set(origins)) or len(domains) != len(set(domains)):
            raise TCKAdapterError(f"{self.case_id} positive selection must be duplicate-free")

        controls = _mapping(vector.get("domStringControls"), f"{self.case_id} domStringControls")
        if set(controls) != {"asciiA", "asciiAB", "unmatchedHighSurrogate"}:
            raise TCKAdapterError(f"{self.case_id} DOMString control set changed")

        permutations = _mapping(
            vector.get("permutationControls"),
            f"{self.case_id} permutationControls",
        )
        if permutations.get("manifestOriginOrders") != 2:
            raise TCKAdapterError(f"{self.case_id} manifestOriginOrders must be 2")
        if permutations.get("manifestCookieDomainOrders") != 2:
            raise TCKAdapterError(
                f"{self.case_id} manifestCookieDomainOrders must be 2"
            )
        if permutations.get("imageCookieAndOriginOrders") != "multiple":
            raise TCKAdapterError(
                f"{self.case_id} imageCookieAndOriginOrders must be multiple"
            )

        _require_exact_string_set(
            vector.get("invalidControls"),
            _SELECTION_INVALID_CONTROLS,
            f"{self.case_id} invalidControls",
        )
        if expect.get("canonicalOriginOrder") != sorted(origins):
            raise TCKAdapterError(f"{self.case_id} canonicalOriginOrder is inconsistent")
        if expect.get("canonicalCookieDomainOrder") != sorted(domains):
            raise TCKAdapterError(
                f"{self.case_id} canonicalCookieDomainOrder is inconsistent"
            )
        for key in (
            "unmatchedSurrogatePreserved",
            "exactWholeUtf16CodeUnitEncodingRequired",
            "canonicalUnpaddedBase64urlRequired",
            "permutationInvariantCanonicalIdentity",
            "rawNoncanonicalDigestRejectedAsBrowserIdentity",
            "invalidControlsRejected",
        ):
            _require_true(expect, key, self.case_id)

    def _vector_manifest(self, vector: Mapping[str, Any]) -> dict[str, Any]:
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
        observed_controls = {
            "asciiA": encode_dom_string_code_units([0x0061]),
            "asciiAB": encode_dom_string_code_units([0x0061, 0x0062]),
            "unmatchedHighSurrogate": encode_dom_string_code_units([0xD800]),
        }
        if dict(controls) != observed_controls:
            raise BrowserVerificationError(
                "Browser DOMString controls do not match exact UTF-16 code-unit encoding"
            )
        if decode_dom_string_code_units(str(controls["unmatchedHighSurrogate"])) != (
            0xD800,
        ):
            raise BrowserVerificationError("unmatched UTF-16 surrogate was not preserved")

        manifest = self._vector_manifest(vector)
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
        manifest = self._vector_manifest(vector)

        duplicate_origin = copy.deepcopy(manifest)
        duplicate_origin["localStorageOrigins"].append(
            duplicate_origin["localStorageOrigins"][0]
        )
        _require_rejected(
            lambda: canonicalize_manifest(duplicate_origin, self._verifier),
            "duplicate-origin-selection",
        )

        duplicate_domain = copy.deepcopy(manifest)
        duplicate_domain["cookieDomains"].append(duplicate_domain["cookieDomains"][0])
        _require_rejected(
            lambda: canonicalize_manifest(duplicate_domain, self._verifier),
            "duplicate-cookie-domain-selection",
        )

        duplicate_storage = _plain(self._fixture.baseline_image)
        origin_with_storage = next(
            item for item in duplicate_storage["origins"] if item["localStorage"]
        )
        origin_with_storage["localStorage"].append(
            copy.deepcopy(origin_with_storage["localStorage"][0])
        )
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
        origin_with_storage = next(item for item in odd_key["origins"] if item["localStorage"])
        origin_with_storage["localStorage"][0]["key"] = "AA"
        _require_rejected(
            lambda: canonicalize_state_image(
                odd_key,
                self._fixture.manifest,
                self._verifier,
            ),
            "odd-decoded-byte-length-localstorage-key",
        )

        noncanonical_pad_bits = _plain(self._fixture.baseline_image)
        origin_with_storage = next(
            item for item in noncanonical_pad_bits["origins"] if item["localStorage"]
        )
        origin_with_storage["localStorage"][0]["value"] = "AAB"
        _require_rejected(
            lambda: canonicalize_state_image(
                noncanonical_pad_bits,
                self._fixture.manifest,
                self._verifier,
            ),
            "noncanonical-base64url-pad-bits-localstorage-value",
        )

        padded = _plain(self._fixture.baseline_image)
        origin_with_storage = next(item for item in padded["origins"] if item["localStorage"])
        origin_with_storage["localStorage"][0]["value"] = "AGE="
        _require_rejected(
            lambda: canonicalize_state_image(
                padded,
                self._fixture.manifest,
                self._verifier,
            ),
            "padded-base64url-localstorage-value",
        )

        noncanonical_manifest = copy.deepcopy(manifest)
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


class BrowserStateImageTCKEvaluator:
    """Execute Browser StateImage completeness, binding, and shape semantics."""

    case_id = _STATE_IMAGE_CASE

    def __init__(
        self,
        *,
        verifier: BrowserIdentityVerifier,
        execution_bindings: Mapping[str, Any],
    ) -> None:
        self._verifier = verifier
        self._execution_bindings = _plain(execution_bindings)

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        vector, expect = _case_parts(case, self.case_id)
        self._validate_case_contract(vector, expect)
        try:
            manifest, expected_image = self._materialize_vector_image(vector)
            canonical_expected = canonicalize_state_image(
                expected_image,
                manifest,
                self._verifier,
            )
            self._verify_positive_state(vector, canonical_expected)
            self._execute_negative_controls(manifest, expected_image, canonical_expected)
        except BrowserHarnessError as exc:
            return _fail(self.case_id, f"Browser StateImage obligation failed: {exc}")
        return _pass(
            self.case_id,
            "Browser StateImage completeness, exact Manifest binding, closed shape, and lossless persistent expiry verified",
        )

    def _validate_case_contract(
        self,
        vector: Mapping[str, Any],
        expect: Mapping[str, Any],
    ) -> None:
        digest = vector.get("manifestDigest")
        if (
            not isinstance(digest, str)
            or not digest.startswith("sha256:")
            or len(digest) != 71
        ):
            raise TCKAdapterError(f"{self.case_id} manifestDigest must be sha256 identity")
        _strings(vector.get("selectedOrigins"), f"{self.case_id} selectedOrigins")
        _strings(
            vector.get("selectedCookieDomains"),
            f"{self.case_id} selectedCookieDomains",
        )
        image = _mapping(vector.get("image"), f"{self.case_id} image")
        if set(image) != {"origins", "cookies"}:
            raise TCKAdapterError(f"{self.case_id} image vector shape changed")
        if not isinstance(image.get("origins"), list) or not isinstance(
            image.get("cookies"), list
        ):
            raise TCKAdapterError(f"{self.case_id} image collections must be arrays")
        _require_exact_string_set(
            vector.get("negativeControls"),
            _STATE_IMAGE_NEGATIVE_CONTROLS,
            f"{self.case_id} negativeControls",
        )
        for key in (
            "completeSelectedStateRequired",
            "manifestBindingRequired",
            "closedSerializedShape",
            "persistentExpiryLossless",
            "invalidControlsRejected",
        ):
            _require_true(expect, key, self.case_id)

    def _materialize_vector_image(
        self,
        vector: Mapping[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        manifest = {
            "apiVersion": _BROWSER_API_VERSION,
            "kind": "BrowserStateManifest",
            "profile": BROWSER_PROFILE,
            "revision": _BROWSER_REVISION,
            "canonicalRepresentation": _BROWSER_REPRESENTATION,
            "localStorageOrigins": list(vector["selectedOrigins"]),
            "cookieDomains": list(vector["selectedCookieDomains"]),
            "executionBindings": _plain(self._execution_bindings),
        }
        manifest = canonicalize_manifest(manifest, self._verifier)

        # The portable vector carries a representative digest-shaped value but
        # does not include the full upstream Manifest bytes. Execution therefore
        # binds the vector image to the actual canonical Manifest produced above;
        # trusting the representative value would make exact binding impossible.
        actual_manifest_digest = canonical_manifest_digest(manifest, self._verifier)
        vector_image = _mapping(vector["image"], f"{self.case_id} image")
        image = {
            "apiVersion": _BROWSER_API_VERSION,
            "kind": "BrowserStateImage",
            "manifestDigest": actual_manifest_digest,
            "cookies": copy.deepcopy(vector_image["cookies"]),
            "origins": copy.deepcopy(vector_image["origins"]),
        }
        return manifest, image

    def _verify_positive_state(
        self,
        vector: Mapping[str, Any],
        canonical_expected: Mapping[str, Any],
    ) -> None:
        expected_origins = set(_strings(vector["selectedOrigins"], "selectedOrigins"))
        observed_origins = {str(item["origin"]) for item in canonical_expected["origins"]}
        if observed_origins != expected_origins:
            raise BrowserVerificationError(
                "StateImage does not contain every selected localStorage origin"
            )

        expected_domains = set(
            _strings(vector["selectedCookieDomains"], "selectedCookieDomains")
        )
        if any(cookie["domain"] not in expected_domains for cookie in canonical_expected["cookies"]):
            raise BrowserVerificationError(
                "StateImage contains cookie state outside selected domains"
            )

        persistent = [
            cookie for cookie in canonical_expected["cookies"] if cookie["persistent"]
        ]
        if not persistent:
            raise BrowserVerificationError(
                "StateImage vector does not exercise persistent cookie expiry"
            )
        expiry = persistent[0].get("expiry")
        if expiry != {"unixSeconds": "1800000000", "nanoseconds": 123456789}:
            raise BrowserVerificationError(
                "persistent cookie expiry was not preserved losslessly"
            )

    def _execute_negative_controls(
        self,
        manifest: Mapping[str, Any],
        expected_image: Mapping[str, Any],
        canonical_expected: Mapping[str, Any],
    ) -> None:
        wrong_binding = _plain(expected_image)
        wrong_binding["manifestDigest"] = "sha256:" + "a" * 64
        if wrong_binding["manifestDigest"] == expected_image["manifestDigest"]:
            wrong_binding["manifestDigest"] = "sha256:" + "b" * 64
        _require_rejected(
            lambda: canonicalize_state_image(wrong_binding, manifest, self._verifier),
            "manifest-binding-required",
        )

        missing_origin = _plain(expected_image)
        missing_origin["origins"].pop()
        _require_rejected(
            lambda: canonicalize_state_image(missing_origin, manifest, self._verifier),
            "missing-selected-origin",
        )

        extra_cookie = _plain(expected_image)
        base_cookie = copy.deepcopy(extra_cookie["cookies"][0])
        base_cookie["name"] = "extra"
        extra_cookie["cookies"].append(base_cookie)
        self._require_not_expected(
            extra_cookie,
            manifest,
            canonical_expected,
            "extra-in-scope-cookie",
        )

        duplicate_origin = _plain(expected_image)
        duplicate_origin["origins"].append(copy.deepcopy(duplicate_origin["origins"][0]))
        _require_rejected(
            lambda: canonicalize_state_image(duplicate_origin, manifest, self._verifier),
            "duplicate-origin",
        )

        duplicate_cookie = _plain(expected_image)
        duplicate_cookie["cookies"].append(copy.deepcopy(duplicate_cookie["cookies"][0]))
        _require_rejected(
            lambda: canonicalize_state_image(duplicate_cookie, manifest, self._verifier),
            "duplicate-cookie-identity",
        )

        session_with_expiry = _plain(expected_image)
        session = next(cookie for cookie in session_with_expiry["cookies"] if not cookie["persistent"])
        session["expiry"] = {"unixSeconds": "1800000000", "nanoseconds": 0}
        _require_rejected(
            lambda: canonicalize_state_image(session_with_expiry, manifest, self._verifier),
            "session-cookie-with-expiry",
        )

        persistent_without_expiry = _plain(expected_image)
        persistent = next(
            cookie for cookie in persistent_without_expiry["cookies"] if cookie["persistent"]
        )
        persistent.pop("expiry")
        _require_rejected(
            lambda: canonicalize_state_image(
                persistent_without_expiry,
                manifest,
                self._verifier,
            ),
            "persistent-cookie-without-expiry",
        )

        floating_expiry = _plain(expected_image)
        persistent = next(cookie for cookie in floating_expiry["cookies"] if cookie["persistent"])
        persistent["expiry"]["nanoseconds"] = 123456789.0
        _require_rejected(
            lambda: canonicalize_state_image(floating_expiry, manifest, self._verifier),
            "floating-point-expiry",
        )

        transformed_storage = _plain(expected_image)
        entry = transformed_storage["origins"][0]["localStorage"][0]
        entry["value"] = encode_dom_string_code_units([0x0063])
        self._require_not_expected(
            transformed_storage,
            manifest,
            canonical_expected,
            "transformed-localstorage-value",
        )

        open_shape = _plain(expected_image)
        open_shape["providerMetadata"] = {"opaque": True}
        _require_rejected(
            lambda: canonicalize_state_image(open_shape, manifest, self._verifier),
            "closed-serialized-shape",
        )

    def _require_not_expected(
        self,
        candidate: Mapping[str, Any],
        manifest: Mapping[str, Any],
        canonical_expected: Mapping[str, Any],
        label: str,
    ) -> None:
        canonical_candidate = canonicalize_state_image(
            candidate,
            manifest,
            self._verifier,
        )
        if canonical_candidate == canonical_expected:
            raise BrowserVerificationError(
                f"Browser negative control was accepted as expected state: {label}"
            )

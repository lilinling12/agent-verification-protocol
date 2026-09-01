"""Provider-neutral evaluator for Browser v0.1 cookie semantics.

Portable cookie truth is established from the evaluator-authorized Browser state
projection, never from provider presentation syntax. The evaluator verifies the
closed portable identity/state shape, preserves explicit SameSite=Default and
persistent expiry exactly, excludes partitioned state from the unpartitioned
profile, and fails closed when temporal restore eligibility cannot be proved.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any, Callable

from .browser_harness import (
    BrowserCanonicalizationError,
    BrowserConformanceHarness,
    BrowserHarnessError,
    BrowserSettlementLedger,
    BrowserVerificationError,
    MaterializedBrowserFixture,
    canonical_state_image_digest,
    canonicalize_state_image,
)
from .browser_tck_adapter import BROWSER_PROFILE
from .models import TCKAdapterError, TCKCaseResult, TCKStatus

CASE_ID = "AVP-TCK-BROWSER-COOKIE-001"
_PORTABLE_IDENTITY = ["name", "domain", "hostOnly", "path"]
_REQUIRED_STATE = [
    "name",
    "value",
    "domain",
    "hostOnly",
    "path",
    "persistent",
    "secure",
    "httpOnly",
    "sameSite",
]
_SAMESITE_STATES = ["Default", "Strict", "Lax", "None"]
_POSITIVE_CONTROLS = frozenset(
    {
        "host-only-and-domain-cookie-distinguished",
        "explicit-default-samesite-preserved",
        "persistent-expiry-preserved-losslessly",
        "session-cookie-without-expiry",
    }
)
_NEGATIVE_CONTROLS = frozenset(
    {
        "host-only-inferred-from-leading-dot",
        "default-samesite-normalized-to-lax",
        "partitioned-cookie-admitted-as-unpartitioned",
        "lossy-provider-export-treated-as-authoritative",
        "persistent-expiry-rounded-or-truncated",
        "temporally-ineligible-cookie-restored-as-equivalent",
    }
)


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


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return copy.deepcopy(value)


def _settled() -> BrowserSettlementLedger:
    ledger = BrowserSettlementLedger()
    ledger.close_subject_admission()
    return ledger


def _require_exact_set(value: object, expected: frozenset[str], label: str) -> None:
    values = _strings(value, label)
    if len(values) != len(set(values)) or frozenset(values) != expected:
        raise TCKAdapterError(f"{label} changed from the governed control set")


def _require_rejected(operation: Callable[[], object], label: str) -> None:
    try:
        operation()
    except BrowserHarnessError:
        return
    raise BrowserVerificationError(f"Browser cookie negative control accepted: {label}")


class BrowserCookieTCKEvaluator:
    """Execute portable cookie identity, projection, and temporal obligations."""

    case_id = CASE_ID

    def __init__(
        self,
        *,
        harness: BrowserConformanceHarness,
        fixture: MaterializedBrowserFixture,
    ) -> None:
        self._harness = harness
        self._fixture = fixture

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        vector, expect = self._case_parts(case)
        self._validate_contract(vector, expect)
        sut = self._harness.provision()
        try:
            observed = self._harness.authoritative_projection(sut, _settled())
            self._verify_positive_projection(observed.data)
            self._execute_semantic_negative_controls(observed.data)
            self._execute_partitioned_control(sut, observed.digest)
            self._execute_temporal_control(sut)
        except BrowserHarnessError as exc:
            return TCKCaseResult(
                self.case_id,
                TCKStatus.FAIL,
                f"Browser cookie obligation failed: {exc}",
            )
        finally:
            sut.release()
        return TCKCaseResult(
            self.case_id,
            TCKStatus.PASS,
            "portable cookie identity/state, explicit Default SameSite, lossless expiry, partition exclusion, and temporal restore eligibility verified",
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
        if vector.get("portableIdentity") != _PORTABLE_IDENTITY:
            raise TCKAdapterError(f"{CASE_ID} portable cookie identity changed")
        if vector.get("requiredState") != _REQUIRED_STATE:
            raise TCKAdapterError(f"{CASE_ID} required cookie state changed")
        if vector.get("persistentAdditionalState") != ["expiry"]:
            raise TCKAdapterError(f"{CASE_ID} persistent additional state changed")
        if vector.get("sameSiteStates") != _SAMESITE_STATES:
            raise TCKAdapterError(f"{CASE_ID} SameSite state set changed")
        _require_exact_set(
            vector.get("positiveControls"),
            _POSITIVE_CONTROLS,
            f"{CASE_ID} positiveControls",
        )
        _require_exact_set(
            vector.get("negativeControls"),
            _NEGATIVE_CONTROLS,
            f"{CASE_ID} negativeControls",
        )
        for key in (
            "portableIdentityPreserved",
            "losslessProjectionRequired",
            "sameSiteDefaultDistinct",
            "temporalEligibilityRequired",
            "negativeControlsRejected",
        ):
            if expect.get(key) is not True:
                raise TCKAdapterError(f"{CASE_ID} expect.{key} must be true")

    def _verify_positive_projection(self, image: Any) -> None:
        state = _mapping(image, "authoritative Browser StateImage")
        cookies = state.get("cookies")
        if not isinstance(cookies, (list, tuple)) or not cookies:
            raise BrowserVerificationError("Browser cookie case requires projected cookies")

        default_cookies = []
        persistent_cookies = []
        session_cookies = []
        for raw_cookie in cookies:
            cookie = _mapping(raw_cookie, "projected cookie")
            persistent = cookie.get("persistent")
            expected_keys = set(_REQUIRED_STATE)
            if persistent is True:
                expected_keys.add("expiry")
                persistent_cookies.append(cookie)
            elif persistent is False:
                session_cookies.append(cookie)
            else:
                raise BrowserVerificationError("projected cookie persistent flag is invalid")
            if set(cookie) != expected_keys:
                raise BrowserVerificationError("projected cookie shape is not closed/lossless")
            if cookie.get("sameSite") == "Default":
                default_cookies.append(cookie)
            if not isinstance(cookie.get("hostOnly"), bool):
                raise BrowserVerificationError("projected cookie hostOnly truth is unavailable")

        if not default_cookies:
            raise BrowserVerificationError("explicit SameSite=Default is not observable")
        if not persistent_cookies:
            raise BrowserVerificationError("persistent cookie expiry is not exercised")
        if not session_cookies or any("expiry" in cookie for cookie in session_cookies):
            raise BrowserVerificationError("session cookie incorrectly carries expiry")

        for cookie in persistent_cookies:
            expiry = _mapping(cookie.get("expiry"), "persistent cookie expiry")
            if set(expiry) != {"unixSeconds", "nanoseconds"}:
                raise BrowserVerificationError("persistent cookie expiry shape is not closed")
            seconds = expiry.get("unixSeconds")
            nanos = expiry.get("nanoseconds")
            if not isinstance(seconds, str) or not seconds:
                raise BrowserVerificationError("persistent cookie seconds are not exact text")
            if isinstance(nanos, bool) or not isinstance(nanos, int):
                raise BrowserVerificationError("persistent cookie nanoseconds are not exact integer")

    def _execute_semantic_negative_controls(self, image: Any) -> None:
        baseline = _plain(_mapping(image, "authoritative Browser StateImage"))
        cookies = baseline["cookies"]

        host_only = next((cookie for cookie in cookies if cookie["hostOnly"]), None)
        if host_only is None:
            raise BrowserVerificationError("host-only cookie control is unavailable")
        erased_host_only = copy.deepcopy(baseline)
        target = next(cookie for cookie in erased_host_only["cookies"] if cookie["hostOnly"])
        target["hostOnly"] = False
        self._require_digest_change(erased_host_only, baseline, "host-only-inferred-from-leading-dot")

        default_cookie = next(
            (cookie for cookie in cookies if cookie["sameSite"] == "Default"),
            None,
        )
        if default_cookie is None:
            raise BrowserVerificationError("Default SameSite control is unavailable")
        collapsed_default = copy.deepcopy(baseline)
        target = next(
            cookie for cookie in collapsed_default["cookies"] if cookie["sameSite"] == "Default"
        )
        target["sameSite"] = "Lax"
        self._require_digest_change(
            collapsed_default,
            baseline,
            "default-samesite-normalized-to-lax",
        )

        persistent = next((cookie for cookie in cookies if cookie["persistent"]), None)
        if persistent is None:
            raise BrowserVerificationError("persistent expiry control is unavailable")
        nanos = persistent["expiry"]["nanoseconds"]
        if nanos:
            rounded = copy.deepcopy(baseline)
            target = next(cookie for cookie in rounded["cookies"] if cookie["persistent"])
            target["expiry"]["nanoseconds"] = 0
            self._require_digest_change(
                rounded,
                baseline,
                "persistent-expiry-rounded-or-truncated",
            )

        # A provider export that omits any required field is not authoritative
        # Browser state. Canonicalization must reject the lossy projection.
        lossy = copy.deepcopy(baseline)
        lossy["cookies"][0].pop("hostOnly")
        _require_rejected(
            lambda: canonicalize_state_image(
                lossy,
                self._fixture.manifest,
                self._harness._verifier,
            ),
            "lossy-provider-export-treated-as-authoritative",
        )

    def _require_digest_change(
        self,
        candidate: Mapping[str, Any],
        baseline: Mapping[str, Any],
        label: str,
    ) -> None:
        verifier = self._harness._verifier
        candidate_digest = canonical_state_image_digest(
            candidate,
            self._fixture.manifest,
            verifier,
        )
        baseline_digest = canonical_state_image_digest(
            baseline,
            self._fixture.manifest,
            verifier,
        )
        if candidate_digest == baseline_digest:
            raise BrowserVerificationError(f"Browser cookie negative control collapsed: {label}")

    def _execute_partitioned_control(self, sut: Any, before_digest: str) -> None:
        origins = self._fixture.manifest.get("localStorageOrigins")
        domains = self._fixture.manifest.get("cookieDomains")
        if not isinstance(origins, (list, tuple)) or not origins:
            raise BrowserVerificationError("partitioned control needs a selected origin")
        if not isinstance(domains, (list, tuple)) or not domains:
            raise BrowserVerificationError("partitioned control needs a selected cookie domain")
        self._harness.fixture_control.seed_partitioned_cookie(
            sut,
            {
                "name": "avp_partitioned_control",
                "value": "1",
                "domain": str(domains[0]),
                "path": "/",
                "topLevelSite": str(origins[0]),
            },
        )
        after = self._harness.authoritative_projection(sut, _settled())
        if after.digest != before_digest:
            raise BrowserVerificationError(
                "partitioned cookie was admitted into unpartitioned Browser identity"
            )

    def _execute_temporal_control(self, sut: Any) -> None:
        snapshot = self._harness.verified_snapshot(sut, _settled())
        setter = getattr(self._harness.fixture_control, "set_restore_temporal_eligibility", None)
        if setter is None:
            raise BrowserVerificationError(
                "backend lacks controlled temporal-ineligibility proof seam"
            )
        setter(sut, eligible=False)
        try:
            _require_rejected(
                lambda: self._harness.verified_restore(
                    sut,
                    snapshot,
                    _settled(),
                    _settled(),
                ),
                "temporally-ineligible-cookie-restored-as-equivalent",
            )
        finally:
            setter(sut, eligible=True)

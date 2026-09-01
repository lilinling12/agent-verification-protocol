"""Private Playwright test-driver support for Browser TCK execution.

Nothing in this module is portable TCK authority. It exists only under ``tests``
to induce controlled concrete-provider faults and adapt the already-reviewed
Playwright Browser security control to provider-neutral evaluator seams.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

from avp_ref.tck_adapter.browser_harness import encode_dom_string_code_units
from avp_ref.tck_adapter.browser_tck_security import BrowserSecurityArtifact
from avp_ref.tck_adapter.playwright_browser import (
    PlaywrightBrowserBackendHarness,
    PlaywrightBrowserSecurityControl,
)


class ProjectionFaultObserver:
    """Corrupt concrete observation while preserving governed fixture metadata."""

    def __init__(self, delegate: Any, fault: str) -> None:
        self._delegate = delegate
        self._fault = fault

    def verify_execution_conditions(self, sut: Any, fixture: Any) -> None:
        if self._fault == "ignore-required-execution-input-drift":
            return
        if self._fault == "ignore-excluded-state-interference":
            resource = self._delegate._resource(sut)
            interfering = resource._excluded_state_interfering
            resource._excluded_state_interfering = False
            try:
                self._delegate.verify_execution_conditions(sut, fixture)
            finally:
                resource._excluded_state_interfering = interfering
            return
        self._delegate.verify_execution_conditions(sut, fixture)

    def verify_restore_eligibility(self, sut: Any, fixture: Any, snapshot: Any) -> None:
        self._delegate.verify_restore_eligibility(sut, fixture, snapshot)

    def project_selected_state(self, sut: Any, fixture: Any) -> Mapping[str, Any]:
        projected = copy.deepcopy(dict(self._delegate.project_selected_state(sut, fixture)))
        projected["cookies"] = [copy.deepcopy(dict(item)) for item in projected["cookies"]]
        projected["origins"] = [copy.deepcopy(dict(item)) for item in projected["origins"]]
        for origin in projected["origins"]:
            origin["localStorage"] = [
                copy.deepcopy(dict(item)) for item in origin["localStorage"]
            ]

        if self._fault == "loses-hostonly-cookie-identity":
            cookie = next(
                item for item in projected["cookies"] if item["name"] == "host_only"
            )
            cookie["hostOnly"] = False
        elif self._fault == "collapses-samesite-default":
            cookie = next(
                item for item in projected["cookies"] if item["name"] == "host_only"
            )
            cookie["sameSite"] = "Lax"
        elif self._fault == "admits-partitioned-state-as-unpartitioned":
            raw = next(
                item
                for item in sut._context.cookies()
                if item.get("name") == "partitioned_probe" and item.get("partitionKey")
            )
            projected["cookies"].append(
                {
                    "name": str(raw["name"]),
                    "value": str(raw["value"]),
                    "domain": str(raw["domain"]).lstrip("."),
                    "hostOnly": False,
                    "path": str(raw["path"]),
                    "persistent": False,
                    "secure": bool(raw["secure"]),
                    "httpOnly": bool(raw["httpOnly"]),
                    "sameSite": str(raw["sameSite"]),
                }
            )
        elif self._fault == "corrupts-domstring-code-units":
            entry = projected["origins"][0]["localStorage"][0]
            entry["value"] = encode_dom_string_code_units((50,))
        elif self._fault == "provider-enumeration-order":
            projected["cookies"].reverse()
            projected["origins"].reverse()
            for origin in projected["origins"]:
                origin["localStorage"].reverse()
        return projected


class ObserverOverrideBackend:
    """Compose one real backend with an evaluator-observer test double only."""

    def __init__(
        self,
        delegate: PlaywrightBrowserBackendHarness,
        observer: Any,
    ) -> None:
        self._delegate = delegate
        self._observer = observer

    @property
    def observer(self) -> Any:
        return self._observer

    @property
    def fixture_control(self) -> Any:
        return self._delegate.fixture_control

    def provision(self, fixture: Any) -> Any:
        return self._delegate.provision(fixture)


class PlaywrightBrowserSecurityEvidenceAdapter:
    """Adapt concrete Playwright security evidence to the portable TCK seam."""

    _PRIVATE_COOKIE_NAME = "avp-evaluator-private-cookie"
    _PRIVATE_STORAGE_KEY = "avp-evaluator-private-storage"

    def __init__(
        self,
        *,
        subject_origin: str,
        private_origin: str,
        private_cookie_domain: str,
        authorized_value: str,
    ) -> None:
        self._subject_origin = subject_origin
        self._private_origin = private_origin
        self._private_cookie_domain = private_cookie_domain
        self._authorized_value = authorized_value
        self._control = PlaywrightBrowserSecurityControl()

    def seed_evaluator_private_state(
        self,
        sut: Any,
        *,
        cookie_value: str,
        local_storage_value: str,
    ) -> None:
        self._control.seed_evaluator_private_state(
            sut,
            origin=self._private_origin,
            cookie={
                "name": self._PRIVATE_COOKIE_NAME,
                "value": cookie_value,
                "domain": self._private_cookie_domain,
                "hostOnly": True,
                "path": "/",
                "persistent": False,
                "secure": False,
                "httpOnly": False,
                "sameSite": "Lax",
            },
            local_storage=(
                {
                    "key": encode_dom_string_code_units(
                        tuple(map(ord, self._PRIVATE_STORAGE_KEY))
                    ),
                    "value": encode_dom_string_code_units(
                        tuple(map(ord, local_storage_value))
                    ),
                },
            ),
        )

    def observe_subject_surface(self, sut: Any) -> Mapping[str, Any]:
        observation = self._control.observe_subject_surface(
            sut,
            subject_origin=self._subject_origin,
            path="/subject-observation",
            expected_authorized_value=self._authorized_value,
        )
        return {"value": observation.value}

    def observe_evaluator_private_state(self, sut: Any) -> Mapping[str, str]:
        cookie, storage = self._control.observe_evaluator_private_state(
            sut,
            origin=self._private_origin,
            cookie_name=self._PRIVATE_COOKIE_NAME,
            local_storage_key=self._PRIVATE_STORAGE_KEY,
        )
        if cookie is None or storage is None:
            return {}
        return {"cookie": cookie, "localStorage": storage}

    def retain_artifact(self, content: bytes) -> BrowserSecurityArtifact:
        retained = self._control.retain_evaluator_artifact(content)
        return BrowserSecurityArtifact(
            identity=retained.locator.digest,
            locator=retained.locator,
            authorization=retained.authorization,
        )

    def retrieve_artifact(self, locator: object, authorization: object) -> bytes:
        return self._control.retrieve_evaluator_artifact(locator, authorization)  # type: ignore[arg-type]

    def retain_redacted_artifacts(
        self,
        content: bytes,
        *,
        redacted_content: bytes,
    ) -> tuple[BrowserSecurityArtifact, BrowserSecurityArtifact]:
        unredacted, redacted = self._control.retain_redacted_artifact(
            content,
            redacted_content=redacted_content,
        )
        return (
            BrowserSecurityArtifact(
                identity=unredacted.locator.digest,
                locator=unredacted.locator,
                authorization=unredacted.authorization,
            ),
            BrowserSecurityArtifact(
                identity=redacted.locator.digest,
                locator=redacted.locator,
                authorization=redacted.authorization,
            ),
        )

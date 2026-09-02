"""Evaluator-only Playwright proof for material excluded Browser state.

Browser v0.1 selects unpartitioned cookies and localStorage only. Service Worker
registrations and Cache Storage are therefore excluded state. Their mere presence
is not automatically a protocol failure: this control first proves, in the real
browser resource, that the excluded state changes execution behavior while the
canonical selected-state digest remains unchanged. Only then is the resource
marked as materially interfering so the existing evaluator verification path
fails closed.

The module is a concrete Chromium/Playwright implementation control. It does not
extend BrowserStateImage, define portable Service Worker semantics, or make
provider observations protocol authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from avp_ref.tck_adapter.browser_harness import (
    BrowserVerificationError,
    canonical_state_image_digest,
)

from .backend import PlaywrightBrowserResource, _project_selected_state


@dataclass(frozen=True, slots=True)
class ServiceWorkerCacheObservation:
    """Concrete evaluator observation of one excluded-state surface."""

    registration_count: int
    cache_names: tuple[str, ...]
    client_controlled: bool
    response_body: str


@dataclass(frozen=True, slots=True)
class ExcludedStateInterferenceEvidence:
    """Evidence that excluded state changed behavior without changing selected state."""

    resource_handle_id: str
    origin: str
    surface: str
    selected_digest_before: str
    selected_digest_after: str
    baseline: ServiceWorkerCacheObservation
    residual: ServiceWorkerCacheObservation


class PlaywrightBrowserExcludedStateControl:
    """Privileged control for Service Worker + Cache Storage interference proof."""

    _SURFACE = "service-worker-cache-storage"

    @staticmethod
    def _resource(sut: Any) -> PlaywrightBrowserResource:
        if not isinstance(sut, PlaywrightBrowserResource):
            raise TypeError("Playwright excluded-state control received a foreign Browser SUT")
        sut._ensure_live()
        return sut

    @staticmethod
    def _require_selected_origin(resource: PlaywrightBrowserResource, origin: str) -> None:
        if not isinstance(origin, str) or not origin:
            raise BrowserVerificationError("excluded-state origin must be a non-empty string")
        resource._verifier.verify_canonical_origin(origin)
        if origin not in set(resource._fixture.manifest["localStorageOrigins"]):
            raise BrowserVerificationError(
                "excluded-state proof origin is outside Manifest localStorage selection"
            )

    @staticmethod
    def _require_path(value: str, field: str) -> None:
        if not isinstance(value, str) or not value.startswith("/"):
            raise BrowserVerificationError(f"{field} must be an absolute-path reference")

    @staticmethod
    def _selected_digest(resource: PlaywrightBrowserResource) -> str:
        image = _project_selected_state(resource, resource._fixture)
        return canonical_state_image_digest(
            image,
            resource._fixture.manifest,
            resource._verifier,
        )

    def observe_service_worker_cache(
        self,
        sut: Any,
        *,
        origin: str,
        controlled_resource_path: str,
    ) -> ServiceWorkerCacheObservation:
        """Observe excluded state and one behavior probe without mutating selected state."""

        resource = self._resource(sut)
        self._require_selected_origin(resource, origin)
        self._require_path(controlled_resource_path, "controlled_resource_path")

        page = resource._context.new_page()
        try:
            page.goto(origin + "/state", wait_until="domcontentloaded")
            capability = page.evaluate(
                """() => ({
                  secureContext: window.isSecureContext,
                  serviceWorkerAvailable: 'serviceWorker' in navigator,
                  cacheStorageAvailable: 'caches' in window,
                })"""
            )
            if capability != {
                "secureContext": True,
                "serviceWorkerAvailable": True,
                "cacheStorageAvailable": True,
            }:
                raise BrowserVerificationError(
                    "excluded-state fixture lacks required Service Worker/Cache Storage capability"
                )

            registration_count = int(
                page.evaluate(
                    "navigator.serviceWorker.getRegistrations().then(items => items.length)"
                )
            )
            cache_names_value = page.evaluate("caches.keys()")
            if not isinstance(cache_names_value, list):
                raise BrowserVerificationError("Cache Storage observation is malformed")
            cache_names = tuple(sorted(str(name) for name in cache_names_value))
            client_controlled = bool(
                page.evaluate("navigator.serviceWorker.controller !== null")
            )
            response_body = str(
                page.evaluate(
                    "path => fetch(path, {cache: 'no-store'}).then(response => response.text())",
                    controlled_resource_path,
                )
            )
            return ServiceWorkerCacheObservation(
                registration_count=registration_count,
                cache_names=cache_names,
                client_controlled=client_controlled,
                response_body=response_body,
            )
        finally:
            page.close()

    def prove_service_worker_cache_interference(
        self,
        sut: Any,
        *,
        origin: str,
        service_worker_path: str,
        controlled_resource_path: str,
        expected_cache_name: str,
        expected_network_body: str,
        expected_interfering_body: str,
    ) -> ExcludedStateInterferenceEvidence:
        """Prove material excluded-state interference and bind fail-closed evidence.

        The proof is accepted only when all of the following hold:
        - the resource begins clean for this controlled excluded-state surface;
        - the selected BrowserStateImage digest is unchanged by excluded-state setup;
        - a Service Worker registration and the expected Cache Storage entry exist;
        - a newly created client is controlled by that worker;
        - the controlled resource behavior changes from the network baseline to the
          expected excluded-state result.

        No provider-idle signal, timer, or arbitrary sleep is used as evidence.
        """

        resource = self._resource(sut)
        self._require_selected_origin(resource, origin)
        self._require_path(service_worker_path, "service_worker_path")
        self._require_path(controlled_resource_path, "controlled_resource_path")
        for field, value in (
            ("expected_cache_name", expected_cache_name),
            ("expected_network_body", expected_network_body),
            ("expected_interfering_body", expected_interfering_body),
        ):
            if not isinstance(value, str) or not value:
                raise BrowserVerificationError(f"{field} must be a non-empty string")
        if expected_network_body == expected_interfering_body:
            raise BrowserVerificationError(
                "excluded-state behavior proof requires distinct baseline and interfering results"
            )

        selected_before = self._selected_digest(resource)
        baseline = self.observe_service_worker_cache(
            resource,
            origin=origin,
            controlled_resource_path=controlled_resource_path,
        )
        if baseline.registration_count != 0 or baseline.cache_names or baseline.client_controlled:
            raise BrowserVerificationError(
                "excluded-state proof requires a clean isolated Browser resource"
            )
        if baseline.response_body != expected_network_body:
            raise BrowserVerificationError(
                "controlled resource did not establish the expected clean network baseline"
            )

        page = resource._context.new_page()
        try:
            page.goto(origin + "/state", wait_until="domcontentloaded")
            installed = page.evaluate(
                """async path => {
                  const registration = await navigator.serviceWorker.register(path);
                  const ready = await navigator.serviceWorker.ready;
                  return {
                    scope: registration.scope,
                    active: ready.active !== null,
                  };
                }""",
                service_worker_path,
            )
            if not isinstance(installed, dict) or installed.get("active") is not True:
                raise BrowserVerificationError(
                    "controlled Service Worker did not reach an active ready registration"
                )
        finally:
            page.close()

        residual = self.observe_service_worker_cache(
            resource,
            origin=origin,
            controlled_resource_path=controlled_resource_path,
        )
        selected_after = self._selected_digest(resource)

        if selected_after != selected_before:
            raise BrowserVerificationError(
                "excluded-state setup changed selected Browser authoritative state"
            )
        if residual.registration_count < 1:
            raise BrowserVerificationError(
                "controlled Service Worker registration is not independently observable"
            )
        if expected_cache_name not in residual.cache_names:
            raise BrowserVerificationError(
                "controlled Cache Storage residue is not independently observable"
            )
        if not residual.client_controlled:
            raise BrowserVerificationError(
                "fresh controlled client is not under the expected Service Worker"
            )
        if residual.response_body != expected_interfering_body:
            raise BrowserVerificationError(
                "excluded Service Worker/Cache state did not produce expected interference"
            )
        if residual.response_body == baseline.response_body:
            raise BrowserVerificationError(
                "excluded-state behavior remained equivalent to the clean baseline"
            )

        # This private marker is evaluator evidence only. The ordinary observer
        # remains responsible for failing execution-condition verification.
        resource._excluded_state_interfering = True
        return ExcludedStateInterferenceEvidence(
            resource_handle_id=resource.handle_id,
            origin=origin,
            surface=self._SURFACE,
            selected_digest_before=selected_before,
            selected_digest_after=selected_after,
            baseline=baseline,
            residual=residual,
        )

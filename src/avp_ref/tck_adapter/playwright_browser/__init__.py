"""Concrete Playwright Browser backend for AVP conformance integration."""

from .backend import (
    CookieProvenance,
    PlaywrightBrowserBackendHarness,
    PlaywrightBrowserFixtureControl,
    PlaywrightBrowserIdentityVerifier,
    PlaywrightBrowserObserver,
    PlaywrightBrowserResource,
)

__all__ = [
    "CookieProvenance",
    "PlaywrightBrowserBackendHarness",
    "PlaywrightBrowserFixtureControl",
    "PlaywrightBrowserIdentityVerifier",
    "PlaywrightBrowserObserver",
    "PlaywrightBrowserResource",
]

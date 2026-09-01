"""Lazy Playwright loading for the concrete Browser reference backend.

Playwright is an optional implementation dependency. Importing AVP's base wheel
must not import or require Playwright, and Playwright objects never cross the
portable Browser harness boundary.
"""

from __future__ import annotations

from typing import Any


def sync_playwright_runtime() -> Any:
    """Return Playwright's sync runtime or fail with an implementation error."""

    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        if exc.name == "playwright":
            raise RuntimeError(
                "Playwright Browser support requires the optional 'browser' dependency"
            ) from exc
        raise
    return sync_playwright()

"""Cross-engine Browser acceptance evidence for AEP-0011.

These tests are intentionally non-normative.  They exercise real browser behavior
through one pinned transport while keeping the expected outcomes browser- and
transport-neutral.  The future portable Browser TCK must be specified separately.
"""

from __future__ import annotations

import os
import unittest
from typing import Any, Final

from .evidence_support import (
    EvidenceHTTPServer,
    canonical_domstring_order,
    decode_domstring_code_units,
    encode_domstring_code_units,
    parse_cookie_header,
)

try:
    from playwright.sync_api import Browser, BrowserType, sync_playwright
except ImportError:  # Optional evidence dependency; base CI must remain browser-free.
    Browser = Any  # type: ignore[assignment,misc]
    BrowserType = Any  # type: ignore[assignment,misc]
    sync_playwright = None


_BROWSER_FAMILIES: Final[tuple[str, ...]] = ("chromium", "firefox", "webkit")
_SELECTED_BROWSER = os.environ.get("AVP_BROWSER_EVIDENCE_ENGINE")


def _selected_families() -> tuple[str, ...]:
    if _SELECTED_BROWSER is None:
        return _BROWSER_FAMILIES
    if _SELECTED_BROWSER not in _BROWSER_FAMILIES:
        raise RuntimeError(
            "AVP_BROWSER_EVIDENCE_ENGINE must be chromium, firefox, or webkit"
        )
    return (_SELECTED_BROWSER,)


@unittest.skipIf(sync_playwright is None, "Playwright is optional Browser acceptance evidence transport")
class BrowserPlatformEvidenceTest(unittest.TestCase):
    """Execute the same browser-observable evidence cases across engine families."""

    def test_bae_001_host_only_and_domain_cookie_behavior(self) -> None:
        with EvidenceHTTPServer() as fixture, sync_playwright() as playwright:
            for family in _selected_families():
                with self.subTest(engine=family):
                    browser = self._launch(getattr(playwright, family))
                    try:
                        context = browser.new_context()
                        page = context.new_page()
                        page.goto(fixture.url("avp.test", "/cookie/seed"))

                        parent = page.goto(fixture.url("avp.test", "/cookie/echo"))
                        self.assertIsNotNone(parent)
                        parent_document = parent.json()
                        parent_cookies = parse_cookie_header(parent_document["cookie"])
                        self.assertEqual("host", parent_cookies["avp_host_only"])
                        self.assertEqual("domain", parent_cookies["avp_domain"])

                        child = page.goto(fixture.url("sub.avp.test", "/cookie/echo"))
                        self.assertIsNotNone(child)
                        child_document = child.json()
                        child_cookies = parse_cookie_header(child_document["cookie"])
                        self.assertNotIn("avp_host_only", child_cookies)
                        self.assertEqual("domain", child_cookies["avp_domain"])

                        # This is deliberately a transport-capability observation, not
                        # an AVP identity inference.  If the provider omits hostOnly,
                        # AEP-0011 requires projection to fail closed rather than derive
                        # it from the domain string.
                        exported = context.cookies()
                        self.assertTrue(exported)
                        self.assertTrue(
                            all("domain" in cookie and "path" in cookie for cookie in exported)
                        )
                        self.assertTrue(
                            all("hostOnly" not in cookie for cookie in exported),
                            "Pinned Playwright transport unexpectedly exposes hostOnly; review the evidence boundary before changing this assertion",
                        )
                    finally:
                        browser.close()

    def test_bae_005_unpartitioned_localstorage_tuple_origin_complete_map(self) -> None:
        with EvidenceHTTPServer() as fixture, sync_playwright() as playwright:
            for family in _selected_families():
                with self.subTest(engine=family):
                    browser = self._launch(getattr(playwright, family))
                    try:
                        context = browser.new_context()
                        page = context.new_page()

                        page.goto(fixture.url("avp.test", "/storage?seed=parent#one"))
                        page.evaluate(
                            """() => {
                                localStorage.clear();
                                localStorage.setItem('alpha', '1');
                                localStorage.setItem('beta', '2');
                            }"""
                        )

                        # Path/query/fragment changes do not change tuple-origin identity.
                        page.goto(fixture.url("avp.test", "/storage?other=value#two"))
                        parent_map = self._storage_map(page)
                        self.assertEqual({"alpha": "1", "beta": "2"}, parent_map)

                        # A distinct tuple origin owns a distinct complete map.
                        page.goto(fixture.url("other.test", "/storage"))
                        self.assertEqual({}, self._storage_map(page))
                        page.evaluate("() => localStorage.setItem('gamma', '3')")
                        self.assertEqual({"gamma": "3"}, self._storage_map(page))

                        page.goto(fixture.url("avp.test", "/storage"))
                        self.assertEqual({"alpha": "1", "beta": "2"}, self._storage_map(page))
                    finally:
                        browser.close()

    def test_bae_007_domstring_code_unit_round_trip(self) -> None:
        cases: dict[str, tuple[int, ...]] = {
            "empty": (),
            "nul": (0x0000,),
            "ascii": tuple(ord(char) for char in "AVP"),
            "bmp": (0x4E2D, 0x6587),
            "pair": (0xD83D, 0xDE80),
            "lone-high": (0xD800,),
            "lone-low": (0xDC00,),
            "composed": (0x00E9,),
            "decomposed": (0x0065, 0x0301),
        }
        for label, units in cases.items():
            with self.subTest(codec_case=label):
                encoded = encode_domstring_code_units(units)
                self.assertEqual(units, decode_domstring_code_units(encoded))

        unordered = (
            cases["decomposed"],
            cases["lone-low"],
            cases["ascii"],
            cases["empty"],
            cases["lone-high"],
        )
        self.assertEqual(tuple(sorted(unordered)), canonical_domstring_order(unordered))

        with EvidenceHTTPServer() as fixture, sync_playwright() as playwright:
            for family in _selected_families():
                with self.subTest(engine=family):
                    browser = self._launch(getattr(playwright, family))
                    try:
                        context = browser.new_context()
                        page = context.new_page()
                        page.goto(fixture.url("avp.test", "/storage"))

                        observed = page.evaluate(
                            """() => {
                                const values = {
                                    empty: '',
                                    nul: '\\u0000',
                                    ascii: 'AVP',
                                    bmp: '\\u4e2d\\u6587',
                                    pair: '\\ud83d\\ude80',
                                    'lone-high': '\\ud800',
                                    'lone-low': '\\udc00',
                                    composed: '\\u00e9',
                                    decomposed: 'e\\u0301',
                                };
                                localStorage.clear();
                                for (const [key, value] of Object.entries(values)) {
                                    localStorage.setItem(key, value);
                                }
                                const result = {};
                                for (const key of Object.keys(values)) {
                                    const value = localStorage.getItem(key);
                                    const units = [];
                                    for (let index = 0; index < value.length; index += 1) {
                                        units.push(value.charCodeAt(index));
                                    }
                                    result[key] = units;
                                }
                                return result;
                            }"""
                        )
                        normalized = {key: tuple(value) for key, value in observed.items()}
                        self.assertEqual(cases, normalized)
                        for label, units in normalized.items():
                            encoded = encode_domstring_code_units(units)
                            self.assertEqual(units, decode_domstring_code_units(encoded), label)
                    finally:
                        browser.close()

    @staticmethod
    def _launch(browser_type: BrowserType) -> Browser:
        return browser_type.launch(headless=True)

    @staticmethod
    def _storage_map(page: Any) -> dict[str, str]:
        return page.evaluate(
            """() => Object.fromEntries(
                Array.from({length: localStorage.length}, (_, index) => localStorage.key(index))
                    .sort()
                    .map(key => [key, localStorage.getItem(key)])
            )"""
        )


if __name__ == "__main__":
    unittest.main()

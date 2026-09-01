from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_ROOT = ROOT / "src/avp_ref/tck_adapter"


class BrowserTCKPortabilityTest(unittest.TestCase):
    def test_portable_browser_tck_modules_contain_no_concrete_provider_branches(self) -> None:
        modules = sorted(ADAPTER_ROOT.glob("browser_tck_*.py"))
        self.assertGreaterEqual(len(modules), 8)

        forbidden_products = (
            "playwright",
            "selenium",
            "chromium",
            "firefox",
            "webkit",
            "cdp",
            "webdriver",
            "bidi",
        )
        for path in modules:
            source = path.read_text(encoding="utf-8").lower()
            for token in forbidden_products:
                with self.subTest(module=path.name, token=token):
                    self.assertNotIn(token, source)

    def test_portable_browser_tck_modules_do_not_encode_private_driver_shapes(self) -> None:
        modules = sorted(ADAPTER_ROOT.glob("browser_tck_*.py"))
        forbidden_driver_details = (
            "toplevelsite",
            "set_restore_temporal_eligibility",
            "_context",
            "partitionkey",
        )
        for path in modules:
            source = path.read_text(encoding="utf-8").lower()
            for token in forbidden_driver_details:
                with self.subTest(module=path.name, token=token):
                    self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()

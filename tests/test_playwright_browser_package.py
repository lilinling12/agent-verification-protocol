from __future__ import annotations

import subprocess
import sys
import unittest


class PlaywrightBrowserPackageTest(unittest.TestCase):
    """Keep the base AVP package independent from the optional Browser provider."""

    def test_import_does_not_eagerly_load_playwright(self) -> None:
        script = (
            "import sys; "
            "import avp_ref.tck_adapter.playwright_browser; "
            "assert 'playwright' not in sys.modules; "
            "assert not any(name.startswith('playwright.') for name in sys.modules)"
        )
        completed = subprocess.run(
            [sys.executable, "-c", script],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.validate_release_development_state import validate_ledger, validate_state

ROOT = Path(__file__).resolve().parents[1]


class PostStableReleaseStateTests(unittest.TestCase):
    def test_post_stable_reconciliation_state_is_valid(self) -> None:
        ledger = json.loads(
            (ROOT / "docs/releases/published-releases.json").read_text(encoding="utf-8")
        )
        state = json.loads(
            (ROOT / "docs/releases/release-development-state.json").read_text(encoding="utf-8")
        )

        releases = validate_ledger(ledger)
        self.assertEqual(
            releases[-1],
            {
                "version": "0.3.0",
                "tag": "v0.3.0",
                "commit": "7be045f47f59b259b32865be8b30005e4caa40f6",
                "class": "stable",
            },
        )
        self.assertEqual(state["mode"], "development")
        self.assertEqual(state["latestPublished"]["version"], "0.3.0")
        self.assertEqual(state["sourceVersion"], "0.3.1.dev0")
        self.assertEqual(state["nextRelease"], {"version": "0.3.1", "tag": "v0.3.1"})

        validate_state(
            state,
            source_version="0.3.1.dev0",
            published_releases=releases,
        )

    def test_post_stable_development_identity_is_strictly_between_boundaries(self) -> None:
        from packaging.version import Version

        self.assertLess(Version("0.3.0"), Version("0.3.1.dev0"))
        self.assertLess(Version("0.3.1.dev0"), Version("0.3.1"))


if __name__ == "__main__":
    unittest.main()

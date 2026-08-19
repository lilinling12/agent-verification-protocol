from __future__ import annotations

import copy
import unittest

from scripts.validate_release_development_state import DevelopmentStateError, validate_state


VALID_STATE = {
    "schemaVersion": "avp-release-development-state/v1",
    "distribution": "avp-reference",
    "mode": "development",
    "latestPublished": {
        "version": "0.3.0rc1",
        "tag": "v0.3.0-rc.1",
        "commit": "ef199124017b0dcc8c4a966d00c4f407760f9a06",
    },
    "nextRelease": {"version": "0.3.0rc2", "tag": "v0.3.0-rc.2"},
    "sourceVersion": "0.3.0rc2.dev0",
}


class ReleaseDevelopmentStateTests(unittest.TestCase):
    def test_accepts_monotonic_post_rc_development_identity(self) -> None:
        validate_state(copy.deepcopy(VALID_STATE), source_version="0.3.0rc2.dev0")

    def test_rejects_reuse_of_published_rc1(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["sourceVersion"] = "0.3.0rc1"
        with self.assertRaisesRegex(DevelopmentStateError, "already-published|ordering"):
            validate_state(state, source_version="0.3.0rc1")

    def test_rejects_dev_version_that_orders_before_rc1(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["sourceVersion"] = "0.3.0.dev99"
        with self.assertRaisesRegex(DevelopmentStateError, "ordering"):
            validate_state(state, source_version="0.3.0.dev99")

    def test_rejects_rc1_dev_build_because_it_orders_before_rc1(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["sourceVersion"] = "0.3.0rc1.dev1"
        with self.assertRaisesRegex(DevelopmentStateError, "ordering"):
            validate_state(state, source_version="0.3.0rc1.dev1")

    def test_rejects_source_and_state_drift(self) -> None:
        with self.assertRaisesRegex(DevelopmentStateError, "sourceVersion drift"):
            validate_state(copy.deepcopy(VALID_STATE), source_version="0.3.0rc2.dev1")

    def test_rejects_noncanonical_pep440_form(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["sourceVersion"] = "0.3.0-rc2.dev0"
        with self.assertRaisesRegex(DevelopmentStateError, "canonical PEP 440"):
            validate_state(state, source_version="0.3.0-rc2.dev0")

    def test_rejects_next_release_tag_drift(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["nextRelease"]["tag"] = "v0.3.0-rc.3"
        with self.assertRaisesRegex(DevelopmentStateError, "nextRelease.tag"):
            validate_state(state, source_version="0.3.0rc2.dev0")

    def test_rejects_immutable_published_anchor_substitution(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["latestPublished"]["commit"] = "0" * 40
        with self.assertRaisesRegex(DevelopmentStateError, "immutable"):
            validate_state(state, source_version="0.3.0rc2.dev0")

    def test_rejects_plain_next_rc_as_development_source(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["sourceVersion"] = "0.3.0rc2"
        with self.assertRaisesRegex(DevelopmentStateError, "ordering|development release"):
            validate_state(state, source_version="0.3.0rc2")


if __name__ == "__main__":
    unittest.main()

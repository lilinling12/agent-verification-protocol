from __future__ import annotations

import copy
import unittest

from scripts.validate_release_development_state import (
    DevelopmentStateError,
    validate_ledger,
    validate_state,
)


RC1 = {
    "version": "0.3.0rc1",
    "tag": "v0.3.0-rc.1",
    "commit": "ef199124017b0dcc8c4a966d00c4f407760f9a06",
    "class": "prerelease",
}

VALID_LEDGER = {
    "schemaVersion": "avp-published-release-ledger/v1",
    "distribution": "avp-reference",
    "releases": [RC1],
}

VALID_STATE = {
    "schemaVersion": "avp-release-development-state/v2",
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
    def releases(self, ledger=None):
        return validate_ledger(copy.deepcopy(ledger or VALID_LEDGER))

    def validate(self, state=None, *, source_version="0.3.0rc2.dev0", ledger=None):
        validate_state(
            copy.deepcopy(state or VALID_STATE),
            source_version=source_version,
            published_releases=self.releases(ledger),
        )

    def test_accepts_current_monotonic_development_identity(self) -> None:
        self.validate()

    def test_accepts_exact_rc_release_transition(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["mode"] = "release"
        state["sourceVersion"] = "0.3.0rc2"
        self.validate(state, source_version="0.3.0rc2")

    def test_accepts_exact_stable_release_transition(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["mode"] = "release"
        state["nextRelease"] = {"version": "0.3.0", "tag": "v0.3.0"}
        state["sourceVersion"] = "0.3.0"
        self.validate(state, source_version="0.3.0")

    def test_rejects_release_mode_version_drift(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["mode"] = "release"
        with self.assertRaisesRegex(DevelopmentStateError, "must equal"):
            self.validate(state)

    def test_rejects_development_source_without_dev_segment(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["sourceVersion"] = "0.3.0rc2"
        with self.assertRaisesRegex(DevelopmentStateError, "development release"):
            self.validate(state, source_version="0.3.0rc2")

    def test_rejects_reuse_of_published_rc1(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["sourceVersion"] = "0.3.0rc1"
        with self.assertRaisesRegex(DevelopmentStateError, "development release|ordering"):
            self.validate(state, source_version="0.3.0rc1")

    def test_rejects_source_and_state_drift(self) -> None:
        with self.assertRaisesRegex(DevelopmentStateError, "sourceVersion drift"):
            self.validate(source_version="0.3.0rc2.dev1")

    def test_rejects_noncanonical_pep440_form(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["sourceVersion"] = "0.3.0-rc2.dev0"
        with self.assertRaisesRegex(DevelopmentStateError, "canonical PEP 440"):
            self.validate(state, source_version="0.3.0-rc2.dev0")

    def test_rejects_next_release_tag_drift(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["nextRelease"]["tag"] = "v0.3.0-rc.3"
        with self.assertRaisesRegex(DevelopmentStateError, "nextRelease.tag"):
            self.validate(state)

    def test_rejects_latest_published_not_equal_to_ledger_tail(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["latestPublished"]["commit"] = "0" * 40
        with self.assertRaisesRegex(DevelopmentStateError, "final published-release ledger"):
            self.validate(state)

    def test_rejects_immutable_rc1_seed_substitution(self) -> None:
        ledger = copy.deepcopy(VALID_LEDGER)
        ledger["releases"][0]["commit"] = "0" * 40
        with self.assertRaisesRegex(DevelopmentStateError, "immutable RC1 seed"):
            self.releases(ledger)

    def test_accepts_governed_published_ledger_advancement(self) -> None:
        ledger = copy.deepcopy(VALID_LEDGER)
        ledger["releases"].append(
            {
                "version": "0.3.0rc2",
                "tag": "v0.3.0-rc.2",
                "commit": "1" * 40,
                "class": "prerelease",
            }
        )
        releases = self.releases(ledger)
        self.assertEqual(releases[-1]["version"], "0.3.0rc2")

    def test_rejects_non_monotonic_published_ledger(self) -> None:
        ledger = copy.deepcopy(VALID_LEDGER)
        ledger["releases"].append(
            {
                "version": "0.3.0rc1",
                "tag": "v0.3.0-rc.1",
                "commit": "1" * 40,
                "class": "prerelease",
            }
        )
        with self.assertRaisesRegex(DevelopmentStateError, "strictly monotonic|unique"):
            self.releases(ledger)

    def test_rejects_published_release_class_drift(self) -> None:
        ledger = copy.deepcopy(VALID_LEDGER)
        ledger["releases"][0]["class"] = "stable"
        with self.assertRaisesRegex(DevelopmentStateError, "immutable RC1 seed"):
            self.releases(ledger)

    def test_rejects_beta_as_next_public_prerelease(self) -> None:
        state = copy.deepcopy(VALID_STATE)
        state["nextRelease"] = {"version": "0.3.0b2", "tag": "v0.3.0-beta.2"}
        state["sourceVersion"] = "0.3.0b2.dev0"
        with self.assertRaisesRegex(DevelopmentStateError, "must use RC"):
            self.validate(state, source_version="0.3.0b2.dev0")


if __name__ == "__main__":
    unittest.main()

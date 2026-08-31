"""Tests for fail-closed stable/candidate installed-wheel TCK planning."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "plan_reference_tck_profiles.py"
_SPEC = importlib.util.spec_from_file_location("plan_reference_tck_profiles", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)
classify_profiles = _MODULE.classify_profiles


class ReferenceTCKPlanTests(unittest.TestCase):
    def test_runs_stable_and_fully_supported_candidate(self) -> None:
        plan = classify_profiles(
            stable_profiles=["stable"],
            candidate_profiles=["candidate"],
            profile_case_ids={
                "stable": frozenset({"S-1"}),
                "candidate": frozenset({"C-1", "C-2"}),
            },
            supported_case_ids=frozenset({"S-1", "C-1", "C-2"}),
        )
        self.assertEqual(plan.run_profiles, ("candidate", "stable"))
        self.assertEqual(plan.pending_candidate_profiles, ())

    def test_allows_completely_unimplemented_candidate_as_explicit_pending(self) -> None:
        plan = classify_profiles(
            stable_profiles=["stable"],
            candidate_profiles=["candidate"],
            profile_case_ids={
                "stable": frozenset({"S-1"}),
                "candidate": frozenset({"C-1", "C-2"}),
            },
            supported_case_ids=frozenset({"S-1"}),
        )
        self.assertEqual(plan.run_profiles, ("stable",))
        self.assertEqual(plan.pending_candidate_profiles, ("candidate",))

    def test_rejects_partial_candidate_support(self) -> None:
        with self.assertRaisesRegex(ValueError, "only partially supported"):
            classify_profiles(
                stable_profiles=["stable"],
                candidate_profiles=["candidate"],
                profile_case_ids={
                    "stable": frozenset({"S-1"}),
                    "candidate": frozenset({"C-1", "C-2"}),
                },
                supported_case_ids=frozenset({"S-1", "C-1"}),
            )

    def test_rejects_missing_stable_support(self) -> None:
        with self.assertRaisesRegex(ValueError, "stable profile stable is not fully supported"):
            classify_profiles(
                stable_profiles=["stable"],
                candidate_profiles=[],
                profile_case_ids={"stable": frozenset({"S-1", "S-2"})},
                supported_case_ids=frozenset({"S-1"}),
            )

    def test_rejects_unowned_profile_inventory(self) -> None:
        with self.assertRaisesRegex(ValueError, "TCK profile ownership mismatch"):
            classify_profiles(
                stable_profiles=["stable"],
                candidate_profiles=[],
                profile_case_ids={
                    "stable": frozenset({"S-1"}),
                    "orphan": frozenset({"O-1"}),
                },
                supported_case_ids=frozenset({"S-1", "O-1"}),
            )

    def test_rejects_stable_candidate_overlap(self) -> None:
        with self.assertRaisesRegex(ValueError, "both stable and candidate"):
            classify_profiles(
                stable_profiles=["same"],
                candidate_profiles=["same"],
                profile_case_ids={"same": frozenset({"X-1"})},
                supported_case_ids=frozenset({"X-1"}),
            )


if __name__ == "__main__":
    unittest.main()

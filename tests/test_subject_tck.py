from __future__ import annotations

import unittest
from pathlib import Path

from avp_ref.tck_adapter import TCKRepository, TCKRunner, TCKStatus

ROOT = Path(__file__).resolve().parents[1]
_SUBJECT_CASES = (
    "AVP-TCK-SUBJECT-LIFECYCLE-001",
    "AVP-TCK-SUBJECT-PROJECTION-001",
    "AVP-TCK-SUBJECT-BUDGET-001",
    "AVP-TCK-SUBJECT-CAPABILITY-001",
    "AVP-TCK-SUBJECT-OUTCOME-001",
    "AVP-TCK-SUBJECT-RESULT-001",
    "AVP-TCK-SUBJECT-ASSURANCE-001",
)


class ReferenceSubjectTCKTest(unittest.TestCase):
    def test_reference_passes_all_registered_subject_cases(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(
            profile="avp-subject-v0.1",
            selected_case_ids=_SUBJECT_CASES,
        )

        self.assertTrue(result.conformant)
        self.assertEqual(7, result.report["summary"]["total"])
        self.assertEqual(7, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])
        self.assertEqual(
            set(_SUBJECT_CASES),
            {item.case_id for item in result.case_results},
        )
        self.assertTrue(
            all(item.status is TCKStatus.PASS for item in result.case_results)
        )

    def test_full_subject_profile_is_conformant(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(profile="avp-subject-v0.1")

        self.assertTrue(result.conformant)
        self.assertEqual(7, result.report["summary"]["total"])
        self.assertEqual(7, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])


if __name__ == "__main__":
    unittest.main()

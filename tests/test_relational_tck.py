from __future__ import annotations

import unittest
from pathlib import Path

from avp_ref.tck_adapter import TCKRepository, TCKRunner, TCKStatus

ROOT = Path(__file__).resolve().parents[1]
_RELATIONAL_CASES = (
    "AVP-TCK-RELATIONAL-IDENTITY-001",
    "AVP-TCK-RELATIONAL-CANONICAL-001",
    "AVP-TCK-RELATIONAL-PROJECTION-001",
    "AVP-TCK-RELATIONAL-QUIESCING-001",
    "AVP-TCK-RELATIONAL-DRIFT-001",
    "AVP-TCK-RELATIONAL-SNAPSHOT-RESET-001",
    "AVP-TCK-RELATIONAL-RESTORE-001",
    "AVP-TCK-RELATIONAL-DIFF-001",
    "AVP-TCK-RELATIONAL-SECURITY-001",
    "AVP-TCK-RELATIONAL-EXECUTED-CAPABILITY-001",
)


class ReferenceRelationalTCKTest(unittest.TestCase):
    def test_reference_passes_all_registered_relational_cases(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(
            profile="avp-relational-state-v0.1",
            selected_case_ids=_RELATIONAL_CASES,
        )

        self.assertTrue(result.conformant)
        self.assertEqual(10, result.report["summary"]["total"])
        self.assertEqual(10, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])
        self.assertEqual(
            set(_RELATIONAL_CASES),
            {item.case_id for item in result.case_results},
        )
        self.assertTrue(all(item.status is TCKStatus.PASS for item in result.case_results))

    def test_full_relational_profile_is_conformant(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(profile="avp-relational-state-v0.1")

        self.assertTrue(result.conformant)
        self.assertEqual(10, result.report["summary"]["total"])
        self.assertEqual(10, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])


if __name__ == "__main__":
    unittest.main()

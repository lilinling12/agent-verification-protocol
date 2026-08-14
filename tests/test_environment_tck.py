from __future__ import annotations

import unittest
from pathlib import Path

from avp_ref.tck_adapter import TCKRepository, TCKRunner, TCKStatus

ROOT = Path(__file__).resolve().parents[1]
_ENVIRONMENT_CASES = (
    "AVP-TCK-ENVIRONMENT-LIFECYCLE-001",
    "AVP-TCK-ENVIRONMENT-RESET-TIME-001",
    "AVP-TCK-ENVIRONMENT-OBSERVATION-001",
    "AVP-TCK-ENVIRONMENT-PROJECTION-001",
    "AVP-TCK-ENVIRONMENT-SNAPSHOT-RESTORE-001",
    "AVP-TCK-ENVIRONMENT-DIFF-001",
    "AVP-TCK-ENVIRONMENT-FAULT-001",
)


class ReferenceEnvironmentTCKTest(unittest.TestCase):
    def test_reference_passes_all_registered_environment_cases(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(
            profile="avp-environment-v0.1",
            selected_case_ids=_ENVIRONMENT_CASES,
        )

        self.assertTrue(result.conformant)
        self.assertEqual(7, result.report["summary"]["total"])
        self.assertEqual(7, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])
        self.assertEqual(
            set(_ENVIRONMENT_CASES),
            {item.case_id for item in result.case_results},
        )
        self.assertTrue(all(item.status is TCKStatus.PASS for item in result.case_results))

    def test_full_environment_profile_is_conformant(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(profile="avp-environment-v0.1")

        self.assertTrue(result.conformant)
        self.assertEqual(7, result.report["summary"]["total"])
        self.assertEqual(7, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])


if __name__ == "__main__":
    unittest.main()

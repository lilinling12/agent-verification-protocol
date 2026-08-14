from __future__ import annotations

import unittest
from pathlib import Path

from avp_ref.tck_adapter import TCKRepository, TCKRunner, TCKStatus

ROOT = Path(__file__).resolve().parents[1]
_SECURITY_CASES = (
    "AVP-TCK-SECURITY-CAPABILITY-SEPARATION-001",
    "AVP-TCK-SECURITY-CAPABILITY-DENY-001",
    "AVP-TCK-SECURITY-CREDENTIAL-CONTEXT-001",
    "AVP-TCK-SECURITY-HIDDEN-MATERIAL-001",
    "AVP-TCK-SECURITY-FAULT-SECRECY-001",
    "AVP-TCK-SECURITY-ASSURANCE-HONESTY-001",
)


class ReferenceSecurityTCKTest(unittest.TestCase):
    def test_reference_passes_all_registered_security_cases(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(
            profile="avp-security-v0.1",
            selected_case_ids=_SECURITY_CASES,
        )

        self.assertTrue(result.conformant)
        self.assertEqual(6, result.report["summary"]["total"])
        self.assertEqual(6, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])
        self.assertEqual(
            set(_SECURITY_CASES),
            {item.case_id for item in result.case_results},
        )
        self.assertTrue(
            all(item.status is TCKStatus.PASS for item in result.case_results)
        )

    def test_full_security_profile_is_conformant(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(profile="avp-security-v0.1")

        self.assertTrue(result.conformant)
        self.assertEqual(6, result.report["summary"]["total"])
        self.assertEqual(6, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])
        self.assertEqual(
            set(_SECURITY_CASES),
            {item.case_id for item in result.case_results},
        )


if __name__ == "__main__":
    unittest.main()

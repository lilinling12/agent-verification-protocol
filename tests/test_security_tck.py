from __future__ import annotations

import unittest
from pathlib import Path

from avp_ref.tck_adapter import (
    TCKAdapterError,
    TCKRepository,
    TCKRunner,
    TCKStatus,
)

ROOT = Path(__file__).resolve().parents[1]
_SECURITY_IMPLEMENTED_CASES = (
    "AVP-TCK-SECURITY-CAPABILITY-SEPARATION-001",
    "AVP-TCK-SECURITY-CAPABILITY-DENY-001",
    "AVP-TCK-SECURITY-CREDENTIAL-CONTEXT-001",
)


class ReferenceSecurityTCKTest(unittest.TestCase):
    def test_reference_passes_implemented_security_slice(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(
            profile="avp-security-v0.1",
            selected_case_ids=_SECURITY_IMPLEMENTED_CASES,
        )

        self.assertTrue(result.conformant)
        self.assertEqual(3, result.report["summary"]["total"])
        self.assertEqual(3, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])
        self.assertTrue(
            all(item.status is TCKStatus.PASS for item in result.case_results)
        )

    def test_full_security_profile_fails_closed_until_all_cases_are_supported(self) -> None:
        repository = TCKRepository(ROOT)

        with self.assertRaises(TCKAdapterError) as error:
            TCKRunner.for_reference(repository).run(profile="avp-security-v0.1")

        message = str(error.exception)
        self.assertIn("does not support registered TCK cases", message)
        self.assertNotIn("AVP-TCK-SECURITY-CREDENTIAL-CONTEXT-001", message)
        self.assertIn("AVP-TCK-SECURITY-HIDDEN-MATERIAL-001", message)
        self.assertIn("AVP-TCK-SECURITY-FAULT-SECRECY-001", message)
        self.assertIn("AVP-TCK-SECURITY-ASSURANCE-HONESTY-001", message)


if __name__ == "__main__":
    unittest.main()

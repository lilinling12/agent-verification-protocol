from __future__ import annotations

import unittest
from pathlib import Path

from avp_ref.tck_adapter import TCKRepository, TCKRunner, TCKStatus

ROOT = Path(__file__).resolve().parents[1]


class ReferenceEvidenceTCKTest(unittest.TestCase):
    def test_reference_implementation_passes_evidence_profile(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(
            profile="avp-evidence-v0.1"
        )
        self.assertTrue(result.conformant)
        self.assertEqual(7, result.report["summary"]["total"])
        self.assertEqual(7, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])
        self.assertTrue(
            all(item.status is TCKStatus.PASS for item in result.case_results)
        )

    def test_reference_composite_preserves_core_profile(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(profile="avp-core-v0.1")
        self.assertTrue(result.conformant)
        self.assertEqual(9, result.report["summary"]["total"])
        self.assertEqual(8, result.report["summary"]["passed"])
        self.assertEqual(1, result.report["summary"]["skipped"])


if __name__ == "__main__":
    unittest.main()

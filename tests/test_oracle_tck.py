from __future__ import annotations

import unittest
from pathlib import Path

from avp_ref.models import ValidityDetail
from avp_ref.tck_adapter import TCKRepository, TCKRunner, TCKStatus

ROOT = Path(__file__).resolve().parents[1]


class ReferenceOracleTCKTest(unittest.TestCase):
    def test_reference_implementation_passes_oracle_profile(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(profile="avp-oracle-v0.1")
        self.assertTrue(result.conformant)
        self.assertEqual(4, result.report["summary"]["total"])
        self.assertEqual(4, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])
        self.assertTrue(
            all(item.status is TCKStatus.PASS for item in result.case_results)
        )

    def test_validity_detail_is_structured_and_immutable(self) -> None:
        detail = ValidityDetail(
            "ORACLE_PROTOCOL_ERROR",
            "Oracle output violated the declared contract",
            ("ev_1", "ev_2"),
        )
        self.assertEqual(
            {
                "code": "ORACLE_PROTOCOL_ERROR",
                "message": "Oracle output violated the declared contract",
                "evidenceIds": ["ev_1", "ev_2"],
            },
            detail.to_dict(),
        )
        with self.assertRaises(AttributeError):
            detail.code = "ORACLE_CRASH"  # type: ignore[misc]

    def test_validity_detail_rejects_invalid_shape(self) -> None:
        with self.assertRaises(ValueError):
            ValidityDetail("oracle_crash")
        with self.assertRaises(ValueError):
            ValidityDetail("ORACLE_CRASH", evidence_ids=("ev_1", "ev_1"))
        with self.assertRaises(ValueError):
            ValidityDetail("ORACLE_CRASH", message="x" * 513)


if __name__ == "__main__":
    unittest.main()

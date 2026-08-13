from __future__ import annotations

import json
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from jsonschema import Draft202012Validator

from avp_ref.artifacts import sha256_digest
from avp_ref.models import TaskVerdict, Validity, ValidityDetail, VerificationResult
from avp_ref.oracle_runner import OracleEvaluationRecord
from avp_ref.tck_adapter import TCKRepository, TCKRunner, TCKStatus

ROOT = Path(__file__).resolve().parents[1]


class ReferenceOracleTCKTest(unittest.TestCase):
    def test_reference_implementation_passes_oracle_profile(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(profile="avp-oracle-v0.1")
        self.assertTrue(result.conformant)
        self.assertEqual(5, result.report["summary"]["total"])
        self.assertEqual(5, result.report["summary"]["passed"])
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

    def test_oracle_evaluation_record_is_schema_valid_and_immutable(self) -> None:
        result = VerificationResult(
            "oracle.audit.bound",
            "state.postcondition",
            "PASS",
            "critical",
            "oracle_tck",
            "0.1.0",
            ("ev_execution",),
        )
        record = OracleEvaluationRecord(
            oracle_id="refund-state",
            oracle_version="1.2.0",
            package_digest=sha256_digest(b"package"),
            input_digest=sha256_digest(b"input"),
            execution_record_digest=sha256_digest(b"execution"),
            evaluation_validity=Validity.VALID,
            task_verdict=TaskVerdict.PASS,
            accepted_results=(result,),
            evidence_ids=("ev_execution",),
        )
        schema = json.loads(
            (ROOT / "schemas" / "oracle-evaluation.schema.json").read_text(
                encoding="utf-8"
            )
        )
        Draft202012Validator(schema).validate(record.to_dict())
        with self.assertRaises(FrozenInstanceError):
            record.oracle_id = "tampered"  # type: ignore[misc]

    def test_oracle_failure_record_cannot_accept_results(self) -> None:
        result = VerificationResult(
            "oracle.audit.bound",
            "state.postcondition",
            "PASS",
            "critical",
            "oracle_tck",
            "0.1.0",
        )
        with self.assertRaises(ValueError):
            OracleEvaluationRecord(
                oracle_id="refund-state",
                oracle_version="1.2.0",
                package_digest=sha256_digest(b"package"),
                input_digest=sha256_digest(b"input"),
                execution_record_digest=None,
                evaluation_validity=Validity.ORACLE_FAILURE,
                task_verdict=TaskVerdict.INCONCLUSIVE,
                accepted_results=(result,),
                validity_detail=ValidityDetail("ORACLE_CRASH"),
            )

    def test_valid_oracle_record_requires_execution_and_forbids_detail(self) -> None:
        with self.assertRaises(ValueError):
            OracleEvaluationRecord(
                oracle_id="refund-state",
                oracle_version="1.2.0",
                package_digest=sha256_digest(b"package"),
                input_digest=sha256_digest(b"input"),
                execution_record_digest=None,
                evaluation_validity=Validity.VALID,
                task_verdict=TaskVerdict.PASS,
            )
        with self.assertRaises(ValueError):
            OracleEvaluationRecord(
                oracle_id="refund-state",
                oracle_version="1.2.0",
                package_digest=sha256_digest(b"package"),
                input_digest=sha256_digest(b"input"),
                execution_record_digest=sha256_digest(b"execution"),
                evaluation_validity=Validity.VALID,
                task_verdict=TaskVerdict.PASS,
                validity_detail=ValidityDetail("ORACLE_PROTOCOL_ERROR"),
            )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from pathlib import Path

from avp_ref.tck_adapter import TCKRepository, TCKRunner, TCKStatus

ROOT = Path(__file__).resolve().parents[1]
_OTEL_CASES = (
    "AVP-TCK-OTEL-ROOT-CORRELATION-001",
    "AVP-TCK-OTEL-EVENT-CORRELATION-001",
    "AVP-TCK-OTEL-TOOL-CORRELATION-001",
    "AVP-TCK-OTEL-OUTCOME-PRESERVATION-001",
    "AVP-TCK-OTEL-PROPAGATION-001",
    "AVP-TCK-OTEL-DATA-MINIMIZATION-001",
    "AVP-TCK-OTEL-COMPLETENESS-001",
    "AVP-TCK-OTEL-EVIDENCE-BINDING-001",
)


class ReferenceOpenTelemetryTCKTest(unittest.TestCase):
    def test_reference_passes_all_registered_otel_cases(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(
            profile="avp-otel-mapping-v0.1",
            selected_case_ids=_OTEL_CASES,
        )

        self.assertTrue(result.conformant)
        self.assertEqual(8, result.report["summary"]["total"])
        self.assertEqual(8, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])
        self.assertEqual(
            set(_OTEL_CASES),
            {item.case_id for item in result.case_results},
        )
        self.assertTrue(
            all(item.status is TCKStatus.PASS for item in result.case_results)
        )

    def test_full_otel_profile_is_conformant(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(
            profile="avp-otel-mapping-v0.1"
        )

        self.assertTrue(result.conformant)
        self.assertEqual(8, result.report["summary"]["total"])
        self.assertEqual(8, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])


if __name__ == "__main__":
    unittest.main()

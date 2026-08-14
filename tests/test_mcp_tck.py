from __future__ import annotations

import unittest
from pathlib import Path

from avp_ref.tck_adapter import TCKRepository, TCKRunner, TCKStatus

ROOT = Path(__file__).resolve().parents[1]
_MCP_CASES = (
    "AVP-TCK-MCP-REVISION-001",
    "AVP-TCK-MCP-CAPABILITY-DENY-001",
    "AVP-TCK-MCP-BASELINE-IDENTITY-001",
    "AVP-TCK-MCP-SCHEMA-DRIFT-001",
    "AVP-TCK-MCP-CALL-BINDING-001",
    "AVP-TCK-MCP-UPSTREAM-FAILURE-001",
    "AVP-TCK-MCP-FEATURE-HONESTY-001",
)


class ReferenceMCPTCKTest(unittest.TestCase):
    def test_reference_passes_all_registered_mcp_cases(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(
            profile="avp-mcp-interop-v0.1",
            selected_case_ids=_MCP_CASES,
        )

        self.assertTrue(result.conformant)
        self.assertEqual(7, result.report["summary"]["total"])
        self.assertEqual(7, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])
        self.assertEqual(
            set(_MCP_CASES),
            {item.case_id for item in result.case_results},
        )
        self.assertTrue(
            all(item.status is TCKStatus.PASS for item in result.case_results)
        )

    def test_full_mcp_profile_is_conformant(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(
            profile="avp-mcp-interop-v0.1"
        )

        self.assertTrue(result.conformant)
        self.assertEqual(7, result.report["summary"]["total"])
        self.assertEqual(7, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import unittest
from importlib import resources
from pathlib import Path

from avp_ref.tck_adapter import TCKRepository, TCKRunner, TCKStatus

ROOT = Path(__file__).resolve().parents[1]
_SCENARIO_CASES = (
    "AVP-TCK-SCENARIO-MATERIALIZATION-001",
    "AVP-TCK-SCENARIO-UNRESOLVED-001",
    "AVP-TCK-SCENARIO-IDENTITY-001",
    "AVP-TCK-SCENARIO-IMMUTABILITY-001",
    "AVP-TCK-SCENARIO-PROJECTION-001",
    "AVP-TCK-SCENARIO-REFERENCE-001",
)


class ReferenceScenarioTCKTest(unittest.TestCase):
    def test_reference_passes_all_registered_scenario_cases(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(
            profile="avp-scenario-v0.1",
            selected_case_ids=_SCENARIO_CASES,
        )

        self.assertTrue(result.conformant)
        self.assertEqual(6, result.report["summary"]["total"])
        self.assertEqual(6, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])
        self.assertEqual(
            set(_SCENARIO_CASES),
            {item.case_id for item in result.case_results},
        )
        self.assertTrue(
            all(item.status is TCKStatus.PASS for item in result.case_results)
        )

    def test_full_scenario_profile_is_conformant(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(profile="avp-scenario-v0.1")

        self.assertTrue(result.conformant)
        self.assertEqual(6, result.report["summary"]["total"])
        self.assertEqual(6, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(0, result.report["summary"]["skipped"])

    def test_packaged_schemas_match_normative_repository_schemas(self) -> None:
        for name in ("scenario-template.schema.json", "scenario-instance.schema.json"):
            normative = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
            packaged = json.loads(
                resources.files("avp_ref.resources").joinpath(name).read_text(encoding="utf-8")
            )
            self.assertEqual(normative, packaged, name)


if __name__ == "__main__":
    unittest.main()

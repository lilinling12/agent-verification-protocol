from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate_normative_surface as validator


class NormativeSurfaceValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = json.loads(validator.MATRIX_PATH.read_text(encoding="utf-8"))

    def validate(self, matrix: dict) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matrix.json"
            path.write_text(json.dumps(matrix), encoding="utf-8")
            with patch.object(validator, "MATRIX_PATH", path):
                validator.main()

    def assert_rejected(self, matrix: dict) -> None:
        with self.assertRaises(SystemExit):
            self.validate(matrix)

    def test_current_blocked_audit_is_valid(self) -> None:
        self.validate(copy.deepcopy(self.matrix))

    def test_ready_is_rejected_while_blockers_remain(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        matrix["closure_status"] = "READY"
        self.assert_rejected(matrix)

    def test_missing_domain_is_rejected(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        matrix["domains"] = matrix["domains"][1:]
        self.assert_rejected(matrix)

    def test_missing_schema_is_rejected(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        matrix["schemas"] = matrix["schemas"][1:]
        self.assert_rejected(matrix)

    def test_requirement_owned_schema_cannot_invent_owner(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        entry = next(item for item in matrix["schemas"] if item["path"] == "schemas/artifact-ref.schema.json")
        entry["owner_domains"] = ["evidence", "trust"]
        self.assert_rejected(matrix)

    def test_unresolved_schema_requires_known_blocker(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        entry = next(item for item in matrix["schemas"] if item["path"] == "schemas/avp-event.schema.json")
        entry["blocker_ids"] = ["NSC-999"]
        self.assert_rejected(matrix)

    def test_alias_bytes_must_match(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        entry = next(item for item in matrix["schemas"] if item["path"] == "schemas/scenario.schema.json")
        entry["identical_to"] = "schemas/scenario-instance.schema.json"
        self.assert_rejected(matrix)

    def test_draft_requirement_metadata_requires_explicit_blocker(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        matrix["blockers"] = [item for item in matrix["blockers"] if item["id"] != "NSC-005"]
        self.assert_rejected(matrix)

    def test_final_aep_lineage_must_actually_be_final(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        oracle = next(item for item in matrix["domains"] if item["domain"] == "oracle")
        oracle["lineage"] = {
            "type": "final-aep",
            "path": "docs/reconciliation/v0.1/decisions/episode-lifecycle-001.md",
        }
        self.assert_rejected(matrix)

    def test_repository_path_traversal_is_rejected(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        matrix["domains"][0]["spec"] = ["../outside.md"]
        self.assert_rejected(matrix)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import yaml

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

    def test_current_ready_audit_is_valid(self) -> None:
        self.assertEqual("READY", self.matrix["closure_status"])
        self.assertEqual([], self.matrix["blockers"])
        self.validate(copy.deepcopy(self.matrix))

    def test_blocked_is_rejected_when_zero_blockers_remain(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        matrix["closure_status"] = "BLOCKED"
        self.assert_rejected(matrix)

    def test_ready_is_rejected_when_a_blocker_is_added(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        matrix["blockers"].append(
            {
                "id": "NSC-999",
                "surface": "synthetic",
                "category": "synthetic-regression",
                "decision_required": True,
                "rationale": "Synthetic blocker used to verify fail-closed READY semantics.",
            }
        )
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
        entry = next(item for item in matrix["schemas"] if item["path"] == "schemas/artifact-ref.schema.json")
        entry["classification"] = "UNOWNED_REQUIRES_GOVERNANCE"
        entry.pop("owner_domains")
        entry["blocker_ids"] = ["NSC-999"]
        self.assert_rejected(matrix)

    def test_retired_avp_core_schema_is_absent(self) -> None:
        schema_paths = {item["path"] for item in self.matrix["schemas"]}
        self.assertNotIn("schemas/avp-core.schema.json", schema_paths)
        self.assertFalse((validator.ROOT / "schemas/avp-core.schema.json").exists())
        blocker_ids = {item["id"] for item in self.matrix["blockers"]}
        self.assertNotIn("NSC-003", blocker_ids)

    def test_retired_scenario_alias_is_absent(self) -> None:
        schema_paths = {item["path"] for item in self.matrix["schemas"]}
        self.assertNotIn("schemas/scenario.schema.json", schema_paths)
        self.assertFalse((validator.ROOT / "schemas/scenario.schema.json").exists())
        self.assertFalse((validator.ROOT / "src/avp_ref/resources/scenario.schema.json").exists())

    def test_retired_reliability_schema_is_absent(self) -> None:
        schema_paths = {item["path"] for item in self.matrix["schemas"]}
        self.assertNotIn("schemas/reliability-report.schema.json", schema_paths)
        self.assertFalse((validator.ROOT / "schemas/reliability-report.schema.json").exists())
        blocker_ids = {item["id"] for item in self.matrix["blockers"]}
        self.assertNotIn("NSC-001", blocker_ids)

    def test_retired_event_schema_is_absent(self) -> None:
        schema_paths = {item["path"] for item in self.matrix["schemas"]}
        self.assertNotIn("schemas/avp-event.schema.json", schema_paths)
        self.assertFalse((validator.ROOT / "schemas/avp-event.schema.json").exists())
        blocker_ids = {item["id"] for item in self.matrix["blockers"]}
        self.assertNotIn("NSC-002", blocker_ids)

    def test_unknown_requirement_index_status_is_rejected(self) -> None:
        original_load_yaml = validator.load_yaml

        def load_with_invalid_status(path: Path) -> dict:
            value = original_load_yaml(path)
            if path.name == "requirement-index.yaml" and path.parent.name == "core":
                value = copy.deepcopy(value)
                value["status"] = "Final"
            return value

        with patch.object(validator, "load_yaml", side_effect=load_with_invalid_status):
            self.assert_rejected(copy.deepcopy(self.matrix))

    def test_draft_requirement_metadata_requires_explicit_blocker(self) -> None:
        original_load_yaml = validator.load_yaml

        def load_with_draft_status(path: Path) -> dict:
            value = original_load_yaml(path)
            if path.name == "requirement-index.yaml" and path.parent.name == "core":
                value = copy.deepcopy(value)
                value["status"] = "draft-normative-candidate"
            return value

        with patch.object(validator, "load_yaml", side_effect=load_with_draft_status):
            self.assert_rejected(copy.deepcopy(self.matrix))

    def test_nsc005_is_rejected_when_all_indexes_are_normative(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        matrix["closure_status"] = "BLOCKED"
        matrix["blockers"].append(
            {
                "id": "NSC-005",
                "surface": "spec/*/requirement-index.yaml#status",
                "category": "authority-metadata-drift",
                "decision_required": True,
                "rationale": "Synthetic stale blocker used to verify fail-closed status linkage.",
            }
        )
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


class NormativeCandidateValidationTests(unittest.TestCase):
    def write_yaml(self, path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")

    def build_repository(self, root: Path) -> tuple[Path, Path]:
        spec_root = root / "spec"
        schema_root = root / "schemas"
        profile_root = root / "conformance/tck/profiles"
        matrix_path = root / "docs/reconciliation/v0.1/normative-surface-matrix.json"
        registry_path = root / "docs/reconciliation/normative-candidates/registry.json"

        (spec_root / "stable").mkdir(parents=True)
        (spec_root / "candidate").mkdir(parents=True)
        schema_root.mkdir(parents=True)
        profile_root.mkdir(parents=True)
        matrix_path.parent.mkdir(parents=True)
        registry_path.parent.mkdir(parents=True)
        (root / "rfcs").mkdir(parents=True)

        (root / "rfcs/AEP-0001-stable.md").write_text("- Status: Final\n", encoding="utf-8")
        (root / "rfcs/AEP-0099-candidate.md").write_text("- Status: Accepted\n", encoding="utf-8")
        (spec_root / "stable/contract.md").write_text("# Stable\n", encoding="utf-8")
        (spec_root / "candidate/contract.md").write_text("# Candidate\n", encoding="utf-8")
        (schema_root / "stable.schema.json").write_text("{}\n", encoding="utf-8")
        (schema_root / "candidate.schema.json").write_text("{}\n", encoding="utf-8")

        self.write_yaml(
            spec_root / "stable/requirement-index.yaml",
            {
                "status": "normative",
                "profile": "avp-stable-v0.1",
                "requirements": [{"id": "AVP-STABLE-001", "schema": "schemas/stable.schema.json"}],
            },
        )
        self.write_yaml(
            spec_root / "candidate/requirement-index.yaml",
            {
                "status": "draft-normative-candidate",
                "profile": "avp-candidate-v0.1",
                "requirements": [{"id": "AVP-CANDIDATE-001", "schema": "schemas/candidate.schema.json"}],
            },
        )
        self.write_yaml(
            profile_root / "avp-stable-v0.1.yaml",
            {"metadata": {"name": "avp-stable-v0.1", "status": "active"}},
        )
        self.write_yaml(
            profile_root / "avp-candidate-v0.1.yaml",
            {"metadata": {"name": "avp-candidate-v0.1", "status": "draft"}},
        )

        matrix = {
            "matrix_version": "1.0",
            "status": "accepted",
            "authority": "non-normative-acceptance-evidence",
            "closure_status": "READY",
            "domains": [
                {
                    "domain": "stable",
                    "lineage": {"type": "final-aep", "path": "rfcs/AEP-0001-stable.md"},
                    "spec": ["spec/stable/contract.md"],
                    "requirement_index": "spec/stable/requirement-index.yaml",
                    "profile": "avp-stable-v0.1",
                }
            ],
            "schemas": [
                {
                    "path": "schemas/stable.schema.json",
                    "classification": "REQUIREMENT_OWNED",
                    "owner_domains": ["stable"],
                }
            ],
            "blockers": [],
        }
        registry = {
            "registry_version": "1.0",
            "authority": "non-normative-governance-evidence",
            "candidates": [
                {
                    "domain": "candidate",
                    "lineage": {"type": "accepted-aep", "path": "rfcs/AEP-0099-candidate.md"},
                    "spec": ["spec/candidate/contract.md"],
                    "requirement_index": "spec/candidate/requirement-index.yaml",
                    "profile": "avp-candidate-v0.1",
                    "owned_schemas": ["schemas/candidate.schema.json"],
                }
            ],
        }
        matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
        return matrix_path, registry_path

    def run_fixture(self, root: Path, *, rejected: bool = False) -> None:
        matrix_path = root / "docs/reconciliation/v0.1/normative-surface-matrix.json"
        registry_path = root / "docs/reconciliation/normative-candidates/registry.json"
        with ExitStack() as stack:
            stack.enter_context(patch.object(validator, "ROOT", root))
            stack.enter_context(patch.object(validator, "MATRIX_PATH", matrix_path))
            stack.enter_context(patch.object(validator, "CANDIDATE_REGISTRY_PATH", registry_path))
            stack.enter_context(patch.object(validator, "SPEC_ROOT", root / "spec"))
            stack.enter_context(patch.object(validator, "SCHEMA_ROOT", root / "schemas"))
            stack.enter_context(patch.object(validator, "PROFILE_ROOT", root / "conformance/tck/profiles"))
            if rejected:
                with self.assertRaises(SystemExit):
                    validator.main()
            else:
                validator.main()

    def test_complete_accepted_candidate_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_repository(root)
            self.run_fixture(root)

    def test_candidate_aep_must_be_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_repository(root)
            (root / "rfcs/AEP-0099-candidate.md").write_text("- Status: Proposed\n", encoding="utf-8")
            self.run_fixture(root, rejected=True)

    def test_final_candidate_requires_explicit_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_repository(root)
            (root / "rfcs/AEP-0099-candidate.md").write_text("- Status: Final\n", encoding="utf-8")
            self.run_fixture(root, rejected=True)

    def test_candidate_requirement_index_must_remain_draft(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_repository(root)
            index_path = root / "spec/candidate/requirement-index.yaml"
            index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
            index["status"] = "normative"
            self.write_yaml(index_path, index)
            self.run_fixture(root, rejected=True)

    def test_candidate_tck_profile_must_remain_draft(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_repository(root)
            profile_path = root / "conformance/tck/profiles/avp-candidate-v0.1.yaml"
            profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
            profile["metadata"]["status"] = "active"
            self.write_yaml(profile_path, profile)
            self.run_fixture(root, rejected=True)

    def test_candidate_owned_schema_requires_requirement_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_repository(root)
            index_path = root / "spec/candidate/requirement-index.yaml"
            index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
            index["requirements"][0].pop("schema")
            self.write_yaml(index_path, index)
            self.run_fixture(root, rejected=True)

    def test_unregistered_candidate_domain_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_repository(root)
            registry_path = root / "docs/reconciliation/normative-candidates/registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["candidates"] = []
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            self.run_fixture(root, rejected=True)

    def test_candidate_spec_must_stay_inside_canonical_domain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_repository(root)
            registry_path = root / "docs/reconciliation/normative-candidates/registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["candidates"][0]["spec"] = ["spec/stable/contract.md"]
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            self.run_fixture(root, rejected=True)

    def test_candidate_cannot_overlap_stable_domain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_repository(root)
            registry_path = root / "docs/reconciliation/normative-candidates/registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["candidates"][0]["domain"] = "stable"
            registry["candidates"][0]["requirement_index"] = "spec/stable/requirement-index.yaml"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            self.run_fixture(root, rejected=True)


if __name__ == "__main__":
    unittest.main()

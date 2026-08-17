from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_historical_disposition.py"
SPEC = importlib.util.spec_from_file_location("validate_historical_disposition", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class HistoricalDispositionValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / "docs/design/alpha-v0.1").mkdir(parents=True)
        (self.root / "docs/reconciliation/v0.1").mkdir(parents=True)
        (self.root / "spec/core").mkdir(parents=True)
        (self.root / "conformance/tck/profiles").mkdir(parents=True)

        self.sources = []
        for index in range(20):
            name = f"docs/design/alpha-v0.1/source-{index:02d}.md"
            (self.root / name).write_text(f"source {index}\n", encoding="utf-8")
            self.sources.append(name)

        manifest = {
            "baseline_id": "avp-design-alpha-v0.1",
            "files": [{"target_path": source} for source in self.sources],
        }
        (self.root / "docs/design/alpha-v0.1/SOURCE-MANIFEST.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        (self.root / "spec/core/requirement-index.yaml").write_text(
            "requirements:\n  - id: AVP-CORE-001\n", encoding="utf-8"
        )
        (self.root / "spec/core/contract.md").write_text("contract\n", encoding="utf-8")
        (self.root / "conformance/tck/profiles/avp-core-v0.1.yaml").write_text(
            "profile: avp-core-v0.1\n", encoding="utf-8"
        )

        documents = []
        for index, source in enumerate(self.sources):
            documents.append(
                {
                    "id": str(index),
                    "source": source,
                    "disposition": "PROMOTED",
                    "rationale": "governed test disposition",
                    "material_areas": [
                        {
                            "area": "test area",
                            "disposition": "PROMOTED",
                            "evidence": {
                                "normative_spec": ["spec/core/contract.md"],
                                "requirements": ["AVP-CORE-001"],
                                "tck_profiles": ["avp-core-v0.1"],
                            },
                        }
                    ],
                }
            )

        profiles = [
            {
                "historical_profile": name,
                "disposition": "PROMOTED",
                "current": ["avp-core-v0.1"],
                "rationale": "test mapping",
            }
            for name in sorted(validator.EXPECTED_HISTORICAL_PROFILES)
        ]
        self.ledger = {
            "version": "1.0",
            "status": validator.EXPECTED_STATUS,
            "authority": validator.EXPECTED_AUTHORITY,
            "baseline": {
                "historical": "avp-design-alpha-v0.1",
                "source_manifest": "docs/design/alpha-v0.1/SOURCE-MANIFEST.json",
                "reconciled_against": "main@test",
            },
            "allowed_dispositions": sorted(validator.ALLOWED_DISPOSITIONS),
            "documents": documents,
            "historical_profile_mapping": profiles,
            "closure_statement": "test closure",
        }
        self._write_ledger()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_ledger(self) -> None:
        (self.root / "docs/reconciliation/v0.1/historical-disposition-ledger.json").write_text(
            json.dumps(self.ledger), encoding="utf-8"
        )

    def _validate(self) -> None:
        with (
            patch.object(validator, "ROOT", self.root),
            patch.object(
                validator,
                "LEDGER_PATH",
                self.root / "docs/reconciliation/v0.1/historical-disposition-ledger.json",
            ),
            patch.object(
                validator,
                "MANIFEST_PATH",
                self.root / "docs/design/alpha-v0.1/SOURCE-MANIFEST.json",
            ),
        ):
            validator.validate()

    def test_valid_complete_ledger_is_accepted(self) -> None:
        self._validate()

    def test_missing_historical_source_is_rejected(self) -> None:
        self.ledger["documents"].pop()
        self._write_ledger()
        with self.assertRaisesRegex(validator.ValidationError, "coverage mismatch"):
            self._validate()

    def test_duplicate_historical_source_is_rejected(self) -> None:
        self.ledger["documents"][1]["source"] = self.ledger["documents"][0]["source"]
        self._write_ledger()
        with self.assertRaisesRegex(validator.ValidationError, "duplicate ledger historical source"):
            self._validate()

    def test_invalid_disposition_is_rejected(self) -> None:
        self.ledger["documents"][0]["disposition"] = "MAYBE"
        self._write_ledger()
        with self.assertRaisesRegex(validator.ValidationError, "unsupported"):
            self._validate()

    def test_promoted_area_requires_normative_and_tck_evidence(self) -> None:
        del self.ledger["documents"][0]["material_areas"][0]["evidence"]["tck_profiles"]
        self._write_ledger()
        with self.assertRaisesRegex(validator.ValidationError, "lacks tck_profiles evidence"):
            self._validate()

    def test_unknown_requirement_is_rejected(self) -> None:
        self.ledger["documents"][0]["material_areas"][0]["evidence"]["requirements"] = [
            "AVP-CORE-999"
        ]
        self._write_ledger()
        with self.assertRaisesRegex(validator.ValidationError, "unknown requirement"):
            self._validate()

    def test_missing_historical_profile_mapping_is_rejected(self) -> None:
        self.ledger["historical_profile_mapping"].pop()
        self._write_ledger()
        with self.assertRaisesRegex(validator.ValidationError, "must cover exactly"):
            self._validate()

    def test_missing_repository_reference_is_rejected(self) -> None:
        self.ledger["documents"][0]["material_areas"][0]["evidence"]["normative_spec"] = [
            "spec/core/missing.md"
        ]
        self._write_ledger()
        with self.assertRaisesRegex(validator.ValidationError, "missing repository path"):
            self._validate()

    def test_repository_path_escape_is_rejected(self) -> None:
        self.ledger["documents"][0]["material_areas"][0]["evidence"]["normative_spec"] = [
            "../outside.md"
        ]
        self._write_ledger()
        with self.assertRaisesRegex(validator.ValidationError, "confined path"):
            self._validate()

    def test_split_document_requires_multiple_material_areas(self) -> None:
        self.ledger["documents"][0]["disposition"] = "SPLIT"
        self._write_ledger()
        with self.assertRaisesRegex(validator.ValidationError, "does not contain multiple"):
            self._validate()


if __name__ == "__main__":
    unittest.main()

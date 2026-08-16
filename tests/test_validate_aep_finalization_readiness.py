from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/validate_aep_finalization_readiness.py"
SPEC = importlib.util.spec_from_file_location("validate_aep_finalization_readiness", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class FinalizationReadinessValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(
            (ROOT / "docs/acceptance/alpha2-finalization-manifest.json").read_text(encoding="utf-8")
        )

    def assert_invalid(self, manifest: dict, expected: str) -> None:
        with self.assertRaisesRegex(validator.ReadinessValidationError, expected):
            validator.validate_manifest(manifest)

    def test_repository_manifest_is_valid_blocked_audit(self) -> None:
        validator.validate_manifest(copy.deepcopy(self.manifest))

    def test_rejects_missing_aep(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["aeps"].pop()
        self.assert_invalid(manifest, "exactly AEP-0001 through AEP-0008")

    def test_rejects_duplicate_aep(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["aeps"][-1]["id"] = "AEP-0001"
        self.assert_invalid(manifest, "AEP ids must be unique")

    def test_rejects_non_exact_commit(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["auditBaseline"]["mainCommit"] = "ABC123"
        self.assert_invalid(manifest, "mainCommit must be exact lowercase SHA-40")

    def test_rejects_wrong_release_class(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["auditBaseline"]["releaseClass"] = "stable"
        self.assert_invalid(manifest, "published prerelease")

    def test_rejects_automatic_final_transition(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["policy"]["automaticFinalTransition"] = True
        self.assert_invalid(manifest, "must never be automatic")

    def test_rejects_eligibility_while_prerelease_policy_is_undefined(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["aeps"][0]["finalEligibility"] = "ELIGIBLE"
        self.assert_invalid(manifest, "cannot be Final-eligible")

    def test_rejects_missing_undefined_policy_blocker(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["blockers"] = []
        self.assert_invalid(manifest, "must expose its blocker")

    def test_rejects_repository_rfc_status_substitution(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        original = validator._read_status

        def substituted(path: Path) -> str:
            if path.name.startswith("AEP-0001-"):
                return "Final"
            return original(path)

        with mock.patch.object(validator, "_read_status", side_effect=substituted):
            self.assert_invalid(manifest, "AEP-0001 repository status is not Accepted")

    def test_rejects_unknown_profile(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["aeps"][0]["tckProfile"] = "avp-does-not-exist-v0.1"
        self.assert_invalid(manifest, "TCK profile does not exist")

    def test_rejects_repository_path_escape(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["aeps"][0]["spec"] = "../outside.md"
        self.assert_invalid(manifest, "must stay inside the repository")

    def test_release_acceptance_must_bind_published_source_commit(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["auditBaseline"]["publishedSourceCommit"] = "0" * 40
        self.assert_invalid(manifest, "not bound to publishedSourceCommit")


if __name__ == "__main__":
    unittest.main()

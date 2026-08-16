from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_aep_final_eligibility import (
    AEP_EVIDENCE,
    AuditError,
    EXPECTED_RELEASE_COMMIT,
    EXPECTED_TAG,
    _bind_tag_resolution,
    audit,
)


FINAL_RULE = "`Final` — normative text and required conformance coverage are merged and released"
PRERELEASE_RULE = (
    "A prerelease is not a stable conformance target unless release notes explicitly say otherwise."
)


class AepFinalEligibilityAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.current_root = self.root / "current"
        self.release_root = self.root / "release"
        self.current_root.mkdir()
        self.release_root.mkdir()
        self._populate_roots()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write(self, root: Path, relative: str, text: str = "fixture\n") -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _populate_roots(self) -> None:
        self._write(self.current_root, "GOVERNANCE.md", FINAL_RULE + "\n")
        self._write(self.current_root, "docs/RELEASE_PROCESS.md", PRERELEASE_RULE + "\n")

        registry_lines = ["cases:"]
        case_number = 0
        for evidence in AEP_EVIDENCE:
            rfc = f"# {evidence.aep}\n\n- Status: Accepted\n"
            self._write(self.current_root, evidence.rfc, rfc)
            self._write(self.release_root, evidence.rfc, rfc)
            for relative in (
                *evidence.normative_specs,
                *evidence.requirement_indexes,
                *evidence.schemas,
                *evidence.tck_profiles,
            ):
                self._write(self.release_root, relative)
            for profile in evidence.tck_profiles:
                case_number += 1
                registry_lines.extend(
                    (
                        f"  - id: FIXTURE-{case_number:03d}",
                        f"    profile: {Path(profile).stem}",
                    )
                )

        self._write(
            self.release_root,
            "conformance/tck/registry.yaml",
            "\n".join(registry_lines) + "\n",
        )

    @staticmethod
    def release_metadata() -> dict[str, object]:
        return {
            "tag_name": EXPECTED_TAG,
            "resolved_tag_commit": EXPECTED_RELEASE_COMMIT,
            "target_commitish": EXPECTED_RELEASE_COMMIT,
            "draft": False,
            "prerelease": True,
            "body": "AEP-0001 through AEP-0008 remain Accepted, not Final.",
            "assets": [
                {"name": "avp_reference-0.3.0rc1-py3-none-any.whl"},
                {"name": "avp_reference-0.3.0rc1.tar.gz"},
                {"name": "MANIFEST.json"},
                {"name": "SHA256SUMS"},
            ],
        }

    def test_complete_rc_evidence_passes_but_does_not_authorize_final(self) -> None:
        result = audit(self.current_root, self.release_root, self.release_metadata())
        self.assertEqual(result["technicalFinalityEvidence"], "PASS")
        self.assertEqual(result["lifecycleEligibility"], "REQUIRES_STABLE_FINALITY_DECISION")
        self.assertEqual(len(result["aepResults"]), 8)
        for item in result["aepResults"]:
            self.assertEqual(item["technicalFinalityEvidence"], "PASS")
            self.assertEqual(item["lifecycleEligibility"], "REQUIRES_STABLE_FINALITY_DECISION")

    def test_live_tag_resolution_binds_lightweight_tag(self) -> None:
        release = self.release_metadata()
        release.pop("resolved_tag_commit")
        tag_ref = {
            "ref": f"refs/tags/{EXPECTED_TAG}",
            "object": {"type": "commit", "sha": EXPECTED_RELEASE_COMMIT},
        }
        bound = _bind_tag_resolution(release, tag_ref)
        self.assertEqual(bound["resolved_tag_commit"], EXPECTED_RELEASE_COMMIT)

    def test_annotated_tag_requires_manual_review(self) -> None:
        release = self.release_metadata()
        tag_ref = {
            "ref": f"refs/tags/{EXPECTED_TAG}",
            "object": {"type": "tag", "sha": "1" * 40},
        }
        with self.assertRaisesRegex(AuditError, "resolve directly to a commit"):
            _bind_tag_resolution(release, tag_ref)

    def test_missing_released_normative_spec_fails_closed(self) -> None:
        (self.release_root / AEP_EVIDENCE[0].normative_specs[0]).unlink()
        with self.assertRaisesRegex(AuditError, "required released asset missing"):
            audit(self.current_root, self.release_root, self.release_metadata())

    def test_current_aep_must_still_be_accepted(self) -> None:
        evidence = AEP_EVIDENCE[1]
        self._write(self.current_root, evidence.rfc, f"# {evidence.aep}\n\n- Status: Final\n")
        with self.assertRaisesRegex(AuditError, "expected current status Accepted"):
            audit(self.current_root, self.release_root, self.release_metadata())

    def test_release_source_aep_must_have_been_accepted(self) -> None:
        evidence = AEP_EVIDENCE[2]
        self._write(self.release_root, evidence.rfc, f"# {evidence.aep}\n\n- Status: Proposed\n")
        with self.assertRaisesRegex(AuditError, "release-source status expected Accepted"):
            audit(self.current_root, self.release_root, self.release_metadata())

    def test_tag_commit_substitution_fails_closed(self) -> None:
        release = self.release_metadata()
        release["resolved_tag_commit"] = "0" * 40
        with self.assertRaisesRegex(AuditError, "tag does not resolve"):
            audit(self.current_root, self.release_root, release)

    def test_release_target_substitution_fails_closed(self) -> None:
        release = self.release_metadata()
        release["target_commitish"] = "0" * 40
        with self.assertRaisesRegex(AuditError, "target_commitish"):
            audit(self.current_root, self.release_root, release)

    def test_release_must_remain_prerelease_for_this_audit(self) -> None:
        release = self.release_metadata()
        release["prerelease"] = False
        with self.assertRaisesRegex(AuditError, "must remain classified as a prerelease"):
            audit(self.current_root, self.release_root, release)

    def test_release_body_must_preserve_not_final_boundary(self) -> None:
        release = self.release_metadata()
        release["body"] = "Alpha 2 release candidate."
        with self.assertRaisesRegex(AuditError, "Accepted/not-Final"):
            audit(self.current_root, self.release_root, release)

    def test_extra_release_asset_fails_closed(self) -> None:
        release = self.release_metadata()
        assets = list(release["assets"])
        assets.append({"name": "unexpected.bin"})
        release["assets"] = assets
        with self.assertRaisesRegex(AuditError, "release asset set mismatch"):
            audit(self.current_root, self.release_root, release)

    def test_unregistered_tck_profile_fails_closed(self) -> None:
        profile_id = Path(AEP_EVIDENCE[3].tck_profiles[0]).stem
        registry_path = self.release_root / "conformance/tck/registry.yaml"
        registry = registry_path.read_text(encoding="utf-8")
        registry_path.write_text(
            "\n".join(line for line in registry.splitlines() if profile_id not in line) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(AuditError, "not registered"):
            audit(self.current_root, self.release_root, self.release_metadata())

    def test_governance_rule_change_requires_manual_review(self) -> None:
        self._write(self.current_root, "GOVERNANCE.md", "changed\n")
        with self.assertRaisesRegex(AuditError, "Final definition changed"):
            audit(self.current_root, self.release_root, self.release_metadata())

    def test_release_policy_change_requires_manual_review(self) -> None:
        self._write(self.current_root, "docs/RELEASE_PROCESS.md", "changed\n")
        with self.assertRaisesRegex(AuditError, "stability rule changed"):
            audit(self.current_root, self.release_root, self.release_metadata())

    def test_output_shape_is_json_serializable(self) -> None:
        rendered = json.dumps(
            audit(self.current_root, self.release_root, self.release_metadata()),
            sort_keys=True,
        )
        self.assertIn("avp-aep-final-eligibility/v1", rendered)


if __name__ == "__main__":
    unittest.main()

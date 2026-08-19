from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release-validation.yml"


class ReleaseValidationWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_dispatch_requires_exact_release_identity_inputs(self) -> None:
        for field in ("tag:", "commit:", "version:", "release_class:"):
            self.assertIn(field, self.text)
        self.assertIn("type: choice", self.text)
        self.assertIn("- prerelease", self.text)
        self.assertIn("- stable", self.text)

    def test_pr_path_retains_immutable_rc1_regression_target(self) -> None:
        self.assertIn("inputs.tag || 'v0.3.0-rc.1'", self.text)
        self.assertIn(
            "inputs.commit || 'ef199124017b0dcc8c4a966d00c4f407760f9a06'",
            self.text,
        )
        self.assertIn("inputs.version || '0.3.0rc1'", self.text)
        self.assertIn("inputs.release_class || 'prerelease'", self.text)

    def test_runtime_identity_assertions_use_selected_version(self) -> None:
        self.assertIn("expected = os.environ['EXPECTED_VERSION']", self.text)
        self.assertIn("version('avp-reference') == expected", self.text)
        self.assertIn("__version__ == expected", self.text)
        self.assertIn("['implementation']['version'] == expected", self.text)
        self.assertNotIn("assert __version__ == '0.3.0rc1'", self.text)

    def test_stable_class_is_forwarded_to_validator(self) -> None:
        self.assertIn('if [[ "${EXPECTED_RELEASE_CLASS}" == "stable" ]]', self.text)
        self.assertIn("args+=(--stable)", self.text)

    def test_full_tck_remains_dynamic_over_registered_profiles(self) -> None:
        self.assertIn("profiles=(conformance/tck/profiles/*.yaml)", self.text)
        self.assertIn("avp tck run", self.text)


if __name__ == "__main__":
    unittest.main()

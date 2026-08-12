from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_dependencies.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_dependencies", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load dependency validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DependencyPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = _load_validator()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.pyproject = self.root / "pyproject.toml"
        self.constraints = self.root / "constraints.txt"
        self.workflow = self.root / "ci.yml"
        self.workflow.write_text(
            "\n".join(
                (
                    "python -m pip install -c constraints/ci.txt -e '.[dev]'",
                    "python -m pip install -c constraints/ci.txt -e '.[dev]'",
                    ".wheel-venv/bin/python -m pip install dist/*.whl",
                )
            ),
            encoding="utf-8",
        )

    def _run(self, *, build_requirement: str, constrained_version: str) -> None:
        self.pyproject.write_text(
            "\n".join(
                (
                    "[build-system]",
                    f'requires = ["{build_requirement}"]',
                    'build-backend = "setuptools.build_meta"',
                    "",
                    "[project]",
                    'name = "fixture"',
                    "dependencies = []",
                    "",
                    "[project.optional-dependencies]",
                    "dev = []",
                )
            ),
            encoding="utf-8",
        )
        self.constraints.write_text(
            f"setuptools=={constrained_version}\n",
            encoding="utf-8",
        )
        with patch.object(self.validator, "PYPROJECT", self.pyproject), patch.object(
            self.validator, "CONSTRAINTS", self.constraints
        ), patch.object(self.validator, "CI_WORKFLOW", self.workflow):
            self.validator.main()

    def test_accepts_reviewed_build_backend_version_upgrade(self) -> None:
        self._run(build_requirement="setuptools==84.0.0", constrained_version="84.0.0")

    def test_rejects_constraint_version_drift(self) -> None:
        with self.assertRaisesRegex(
            SystemExit,
            "CI constraints must pin the same setuptools version as build-system.requires",
        ):
            self._run(build_requirement="setuptools==84.0.0", constrained_version="80.9.0")

    def test_rejects_non_exact_build_backend_requirement(self) -> None:
        with self.assertRaisesRegex(SystemExit, "must be an exact NAME==VERSION pin"):
            self._run(build_requirement="setuptools>=84.0.0", constrained_version="84.0.0")


if __name__ == "__main__":
    unittest.main()

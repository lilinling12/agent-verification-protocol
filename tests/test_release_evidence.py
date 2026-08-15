from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "release_evidence.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("release_evidence", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load release_evidence")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseEvidenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.dist = self.root / "dist"
        self.evidence = self.root / "evidence"
        self.dist.mkdir()
        self.version_file = self.root / "_version.py"
        self.version_file.write_text('__version__ = "0.3.0rc1"\n', encoding="utf-8")
        (self.dist / "avp_reference-0.3.0rc1-py3-none-any.whl").write_bytes(b"wheel-bytes")
        (self.dist / "avp_reference-0.3.0rc1.tar.gz").write_bytes(b"sdist-bytes")
        self.repository = "example/avp"
        self.commit = "a" * 40

    def _build(self):
        with patch.object(self.module, "VERSION_FILE", self.version_file):
            return self.module.build_evidence(
                dist_dir=self.dist,
                output_dir=self.evidence,
                repository=self.repository,
                commit=self.commit,
            )

    def _verify(self):
        with patch.object(self.module, "VERSION_FILE", self.version_file):
            return self.module.verify_evidence(
                dist_dir=self.dist,
                output_dir=self.evidence,
                repository=self.repository,
                commit=self.commit,
            )

    def test_build_and_verify_round_trip(self) -> None:
        manifest = self._build()
        self.assertEqual(manifest, self._verify())
        self.assertEqual(manifest["source"]["commit"], self.commit)
        self.assertEqual(manifest["distribution"]["version"], "0.3.0rc1")
        self.assertEqual(len(manifest["artifacts"]), 2)
        checksums = (self.evidence / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(checksums), 3)

    def test_rejects_artifact_tampering(self) -> None:
        self._build()
        (self.dist / "avp_reference-0.3.0rc1-py3-none-any.whl").write_bytes(b"tampered")
        with self.assertRaisesRegex(self.module.EvidenceError, "artifact digest/size"):
            self._verify()

    def test_rejects_source_identity_tampering(self) -> None:
        self._build()
        manifest_path = self.evidence / "MANIFEST.json"
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        document["source"]["commit"] = "b" * 40
        manifest_path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(self.module.EvidenceError, "source identity mismatch"):
            self._verify()

    def test_rejects_unexpected_distribution_file(self) -> None:
        (self.dist / "unexpected.txt").write_text("unexpected", encoding="utf-8")
        with patch.object(self.module, "VERSION_FILE", self.version_file):
            with self.assertRaisesRegex(self.module.EvidenceError, "unexpected files"):
                self.module.build_evidence(
                    dist_dir=self.dist,
                    output_dir=self.evidence,
                    repository=self.repository,
                    commit=self.commit,
                )

    def test_rejects_non_exact_commit(self) -> None:
        with patch.object(self.module, "VERSION_FILE", self.version_file):
            with self.assertRaisesRegex(self.module.EvidenceError, "exact lowercase 40-character"):
                self.module.build_evidence(
                    dist_dir=self.dist,
                    output_dir=self.evidence,
                    repository=self.repository,
                    commit="main",
                )


if __name__ == "__main__":
    unittest.main()

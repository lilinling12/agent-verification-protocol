"""Ordinary-CI tests for the PTL-002 privileged evidence CLI publication boundary."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from scripts.run_network_control_packet_path_evidence import _publish_retained_artifacts


class PacketPathEvidenceCliPublicationTests(unittest.TestCase):
    def test_privileged_artifacts_become_runner_readable_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "artifacts"
            nested = root / "sha256" / "ab"
            nested.mkdir(parents=True)
            artifact = nested / ("ab" * 32)
            artifact.write_bytes(b"retained-evidence")
            artifact.chmod(0o600)

            _publish_retained_artifacts(root)

            self.assertEqual(root.stat().st_mode & 0o777, 0o755)
            self.assertEqual(nested.stat().st_mode & 0o777, 0o755)
            self.assertEqual(artifact.stat().st_mode & 0o777, 0o444)
            self.assertEqual(artifact.read_bytes(), b"retained-evidence")

    def test_symlink_is_rejected_before_permission_mutation(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symbolic links are unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "artifacts"
            root.mkdir()
            retained = root / "retained.bin"
            retained.write_bytes(b"evidence")
            external = Path(directory) / "external.bin"
            external.write_bytes(b"outside")
            link = root / "escape"
            link.symlink_to(external)
            original_mode = retained.stat().st_mode & 0o777

            with self.assertRaisesRegex(RuntimeError, "symbolic links"):
                _publish_retained_artifacts(root)

            self.assertEqual(retained.stat().st_mode & 0o777, original_mode)
            self.assertEqual(external.read_bytes(), b"outside")


if __name__ == "__main__":
    unittest.main()

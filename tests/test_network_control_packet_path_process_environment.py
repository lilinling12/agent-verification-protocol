"""Ordinary-CI coverage for the PTL-002 packet-path process environment."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from acceptance.network_control.evidence_core import EvidenceMaterializationError
from acceptance.network_control.packet_path.process_environment import (
    sanitize_packet_path_process_environment,
)


class PacketPathProcessEnvironmentTests(unittest.TestCase):
    def test_worker_pythonpath_is_exact_reviewed_tests_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "tests" / "acceptance").mkdir(parents=True)
            environment = {
                "PATH": "/usr/bin:/bin",
                "LANG": "C.UTF-8",
                "PYTHONPATH": "/tmp/attacker:/opt/injected",
                "GITHUB_TOKEN": "must-not-cross-boundary",
                "GITHUB_SHA": "must-not-cross-boundary",
                "ACTIONS_RUNTIME_TOKEN": "must-not-cross-boundary",
            }

            sanitize_packet_path_process_environment(
                workspace=workspace,
                environment=environment,
            )

            self.assertEqual(
                environment,
                {
                    "PATH": "/usr/bin:/bin",
                    "LANG": "C.UTF-8",
                    "PYTHONPATH": str((workspace / "tests").resolve()),
                },
            )

    def test_empty_caller_pythonpath_is_still_bound_for_acceptance_worker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "tests" / "acceptance").mkdir(parents=True)
            environment = {"PATH": "/usr/bin:/bin"}

            sanitize_packet_path_process_environment(
                workspace=workspace,
                environment=environment,
            )

            self.assertEqual(
                environment["PYTHONPATH"],
                str((workspace / "tests").resolve()),
            )

    def test_invalid_workspace_fails_before_environment_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            environment = {
                "PATH": "/usr/bin:/bin",
                "PYTHONPATH": "/tmp/original",
                "GITHUB_TOKEN": "still-present-on-rejected-call",
            }
            before = dict(environment)

            with self.assertRaises(EvidenceMaterializationError):
                sanitize_packet_path_process_environment(
                    workspace=workspace,
                    environment=environment,
                )

            self.assertEqual(environment, before)

    def test_source_is_mechanism_local_not_generic_environment_policy(self) -> None:
        import acceptance.network_control.packet_path.process_environment as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("class EnvironmentPolicy", source)
        self.assertNotIn("ProviderRegistry", source)
        self.assertNotIn("toxiproxy", source.lower())
        self.assertIn('retained["PYTHONPATH"] = str(tests)', source)


if __name__ == "__main__":
    unittest.main()

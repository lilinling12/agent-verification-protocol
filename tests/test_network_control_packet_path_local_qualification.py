"""PTL-001 ordinary-CI tests for the explicit local privileged entrypoint."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from acceptance.network_control.packet_path import local_qualification


class PacketPathLocalQualificationEntrypointTests(unittest.TestCase):
    def test_entrypoint_refuses_without_explicit_network_mutation_opt_in(self) -> None:
        with self.assertRaises(SystemExit):
            local_qualification.main(["--run-id", "local-qualification-test"])

    def test_entrypoint_refuses_non_linux_before_constructing_runner(self) -> None:
        with patch.object(sys, "platform", "darwin"):
            with patch.object(local_qualification, "PacketPathLocalQualification") as runner:
                with self.assertRaises(SystemExit):
                    local_qualification.main(
                        [
                            "--allow-local-privileged-network-mutation",
                            "--run-id",
                            "local-qualification-test",
                        ]
                    )
        runner.assert_not_called()

    def test_entrypoint_refuses_non_root_before_constructing_runner(self) -> None:
        with patch.object(sys, "platform", "linux"):
            with patch.object(local_qualification.os, "geteuid", return_value=1000):
                with patch.object(local_qualification, "PacketPathLocalQualification") as runner:
                    with self.assertRaises(SystemExit):
                        local_qualification.main(
                            [
                                "--allow-local-privileged-network-mutation",
                                "--run-id",
                                "local-qualification-test",
                            ]
                        )
        runner.assert_not_called()

    def test_explicit_linux_root_opt_in_runs_only_local_qualification(self) -> None:
        instance = Mock()
        instance.execute.return_value = {"ready": True}
        with patch.object(sys, "platform", "linux"):
            with patch.object(local_qualification.os, "geteuid", return_value=0):
                with patch.object(
                    local_qualification,
                    "PacketPathLocalQualification",
                    return_value=instance,
                ) as runner:
                    self.assertEqual(
                        local_qualification.main(
                            [
                                "--allow-local-privileged-network-mutation",
                                "--run-id",
                                "local-qualification-test",
                                "--workspace",
                                ".",
                                "--observation-budget-ms",
                                "250",
                            ]
                        ),
                        0,
                    )
        runner.assert_called_once_with(
            workspace=Path("."),
            run_id="local-qualification-test",
            semantic_baseline_commit=local_qualification._DEFAULT_BASELINE,
            observation_budget_ns=250_000_000,
        )
        instance.execute.assert_called_once_with()

    def test_unready_local_qualification_returns_nonzero(self) -> None:
        instance = Mock()
        instance.execute.return_value = {"ready": False, "problems": ["qualification-failed"]}
        with patch.object(sys, "platform", "linux"):
            with patch.object(local_qualification.os, "geteuid", return_value=0):
                with patch.object(
                    local_qualification,
                    "PacketPathLocalQualification",
                    return_value=instance,
                ):
                    self.assertEqual(
                        local_qualification.main(
                            [
                                "--allow-local-privileged-network-mutation",
                                "--run-id",
                                "local-qualification-test",
                            ]
                        ),
                        2,
                    )


class PacketPathLocalQualificationBoundaryTests(unittest.TestCase):
    def test_entrypoint_never_acquires_privilege_or_owns_workflow_policy(self) -> None:
        source = open(local_qualification.__file__, "r", encoding="utf-8").read()

        self.assertNotIn("sudo", source)
        self.assertNotIn("pkexec", source)
        self.assertNotIn("pull_request_target", source)
        self.assertNotIn("Toxiproxy", source)
        self.assertNotIn("toxiproxy", source.lower())
        self.assertNotIn("compare_portable_evidence", source)
        self.assertNotIn("SATISFIED", source)

    def test_constructor_does_not_materialize_network_resources(self) -> None:
        workspace = Path(local_qualification.__file__).resolve().parents[4]
        runner = local_qualification.PacketPathLocalQualification(
            workspace=workspace,
            run_id="constructor-no-mutation",
            semantic_baseline_commit=local_qualification._DEFAULT_BASELINE,
            observation_budget_ns=1_000_000,
        )

        self.assertFalse(runner.controller.topology_ready)
        self.assertFalse(runner.controller.fault_active)


if __name__ == "__main__":
    unittest.main()

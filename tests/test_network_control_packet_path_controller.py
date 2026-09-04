"""PTL-001 unit tests for bounded netns/veth/nftables mechanism control."""

from __future__ import annotations

import subprocess
import unittest
from typing import Any

from acceptance.network_control.packet_path.controller import (
    BoundedLinuxCli,
    PacketPathControlError,
    PacketPathController,
    PacketPathFaultMode,
    PacketPathPrerequisiteError,
)
from acceptance.network_control.packet_path.topology import PacketPathRunTopology


class RecordingLinuxRunner:
    def __init__(self, *, fail_contains: tuple[str, ...] | None = None) -> None:
        self.commands: list[list[str]] = []
        self.namespaces: set[str] = set()
        self.fail_contains = fail_contains

    def __call__(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        del kwargs
        self.commands.append(list(command))
        if self.fail_contains and _contains_sequence(command, self.fail_contains):
            return subprocess.CompletedProcess(command, 1, "", "forced failure")

        if command[:3] == ["ip", "netns", "list"]:
            output = "".join(f"{name}\n" for name in sorted(self.namespaces))
            return subprocess.CompletedProcess(command, 0, output, "")
        if command[:3] == ["ip", "netns", "add"] and len(command) == 4:
            self.namespaces.add(command[3])
        if command[:3] == ["ip", "netns", "del"] and len(command) == 4:
            self.namespaces.discard(command[3])
        return subprocess.CompletedProcess(command, 0, "ok", "")


def _contains_sequence(command: list[str], sequence: tuple[str, ...]) -> bool:
    width = len(sequence)
    return any(
        tuple(command[index : index + width]) == sequence
        for index in range(len(command) - width + 1)
    )


class PacketPathControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology = PacketPathRunTopology.for_run("controller-tests")
        self.runner = RecordingLinuxRunner()
        self.controller = PacketPathController(
            topology=self.topology,
            cli=BoundedLinuxCli(runner=self.runner),
        )

    def test_setup_is_run_scoped_and_enables_forwarding_only_in_control_namespace(self) -> None:
        self.controller.setup()
        commands = self.runner.commands
        t = self.topology

        self.assertEqual(self.runner.namespaces, set(t.namespace_names))
        self.assertIn(
            [
                "ip",
                "netns",
                "exec",
                t.control_namespace,
                "sysctl",
                "-qw",
                "net.ipv4.ip_forward=1",
            ],
            commands,
        )
        self.assertFalse(
            any(command[:2] == ["sysctl", "-w"] for command in commands),
            "host-global forwarding mutation is forbidden",
        )
        self.assertFalse(any(command and command[0] == "sh" for command in commands))
        self.assertTrue(
            any(
                command[:7]
                == [
                    "ip",
                    "netns",
                    "exec",
                    t.control_namespace,
                    "nft",
                    "add",
                    "table",
                ]
                for command in commands
            )
        )

    def test_selected_drop_is_narrow_to_crossed_fixture_socket(self) -> None:
        self.controller.setup()
        self.controller.install_fault()
        command = self.runner.commands[-1]
        t = self.topology

        self.assertIn(t.router_subject_interface, command)
        self.assertIn(t.router_fixture_interface, command)
        self.assertIn(t.fixture_address, command)
        self.assertIn(str(t.selected_port), command)
        self.assertNotIn(str(t.control_port), command)
        self.assertEqual(command[-1], "drop")

        self.controller.clear_fault()
        self.assertEqual(
            self.runner.commands[-1][-5:],
            ["flush", "chain", "ip", t.nft_table, t.nft_chain],
        )

    def test_negative_fault_scopes_are_structurally_distinct(self) -> None:
        t = self.topology
        selected = self.controller.fault_command(PacketPathFaultMode.SELECTED)
        bypass = self.controller.fault_command(PacketPathFaultMode.BYPASS)
        collateral = self.controller.fault_command(PacketPathFaultMode.COLLATERAL)

        self.assertIn(str(t.selected_port), selected)
        self.assertIn(str(t.unused_fault_port), bypass)
        self.assertNotIn("dport", collateral)
        self.assertEqual(collateral[-1], "drop")

    def test_subject_command_drops_linux_capabilities_without_shell(self) -> None:
        command = self.controller.subject_command(("python", "-m", "qualification-worker"))
        t = self.topology

        self.assertEqual(command[:4], ("ip", "netns", "exec", t.subject_namespace))
        self.assertIn("setpriv", command)
        self.assertIn("--clear-groups", command)
        self.assertIn("--bounding-set=-all", command)
        self.assertIn("--inh-caps=-all", command)
        self.assertIn("--ambient-caps=-all", command)
        self.assertIn("--no-new-privs", command)
        separator = command.index("--")
        self.assertEqual(command[separator + 1 :], ("python", "-m", "qualification-worker"))
        self.assertNotIn("sh", command)
        self.assertNotIn("sudo", command)

    def test_partial_setup_failure_triggers_bounded_cleanup(self) -> None:
        runner = RecordingLinuxRunner(fail_contains=("link", "add"))
        controller = PacketPathController(
            topology=self.topology,
            cli=BoundedLinuxCli(runner=runner),
        )

        with self.assertRaises(PacketPathControlError):
            controller.setup()

        self.assertEqual(runner.namespaces, set())
        deletes = [command for command in runner.commands if command[:3] == ["ip", "netns", "del"]]
        self.assertLessEqual(len(deletes), 3)

    def test_cleanup_is_idempotent_and_never_flushes_host_ruleset(self) -> None:
        self.controller.setup()
        first = self.controller.cleanup()
        command_count = len(self.runner.commands)
        second = self.controller.cleanup()
        after_second_cleanup = len(self.runner.commands)

        self.assertEqual(first, ())
        self.assertEqual(second, ())
        self.assertEqual(self.controller.residual_resources(), ())
        second_cleanup_commands = self.runner.commands[command_count:after_second_cleanup]
        self.assertEqual(
            second_cleanup_commands,
            [["ip", "netns", "list"], ["ip", "netns", "list"]],
        )
        self.assertFalse(any(command[:2] == ["nft", "flush"] for command in self.runner.commands))

    def test_fault_lifecycle_fails_closed(self) -> None:
        with self.assertRaises(PacketPathControlError):
            self.controller.install_fault()

        self.controller.setup()
        self.controller.install_fault()
        with self.assertRaises(PacketPathControlError):
            self.controller.install_fault()
        self.controller.clear_fault()
        with self.assertRaises(PacketPathControlError):
            self.controller.clear_fault()

    def test_cli_execution_failure_is_typed(self) -> None:
        def missing_runner(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            del kwargs
            raise FileNotFoundError(command[0])

        cli = BoundedLinuxCli(runner=missing_runner)
        with self.assertRaises(PacketPathPrerequisiteError):
            cli.run(("ip", "netns", "list"))


if __name__ == "__main__":
    unittest.main()

"""Concrete bounded Linux control plane for Network Control PTL-001.

The controller owns only the run-scoped netns/veth/router/nftables mechanism.
It is deliberately not a generic Network Control backend, provider SPI, or
portable verdict source.
"""

from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Sequence

from ..evidence_core import EvidenceMaterializationError
from .topology import PacketPathRunTopology


class PacketPathPrerequisiteError(RuntimeError):
    """Raised when the reviewed local Linux control prerequisites are absent."""


class PacketPathControlError(RuntimeError):
    """Raised when a bounded run-scoped Linux control operation fails."""


class PacketPathFaultMode(str, Enum):
    """Mechanism-local fault assemblies; not portable AVP verdict identities."""

    SELECTED = "selected"
    BYPASS = "bypass"
    COLLATERAL = "collateral"


@dataclass(frozen=True, slots=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class BoundedLinuxCli:
    """Run argv-only Linux commands with a finite timeout and injectable seam."""

    def __init__(
        self,
        *,
        command_timeout_s: float = 10.0,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        if (
            isinstance(command_timeout_s, bool)
            or not isinstance(command_timeout_s, (int, float))
            or not math.isfinite(command_timeout_s)
            or command_timeout_s <= 0
        ):
            raise ValueError("Linux command timeout must be positive and finite")
        self.command_timeout_s = float(command_timeout_s)
        self._runner = runner

    def run(
        self,
        argv: Sequence[str],
        *,
        allow_failure: bool = False,
    ) -> CommandResult:
        if not argv or any(not isinstance(item, str) or not item for item in argv):
            raise ValueError("Linux control command must be non-empty argv strings")
        command = list(argv)
        try:
            completed = self._runner(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.command_timeout_s,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PacketPathPrerequisiteError(
                f"cannot execute bounded packet-path control command: {command!r}"
            ) from exc

        result = CommandResult(
            argv=tuple(command),
            returncode=int(completed.returncode),
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
        if result.returncode != 0 and not allow_failure:
            detail = (result.stderr or result.stdout or "Linux control command failed").strip()
            raise PacketPathControlError(
                f"packet-path control failed ({result.returncode}) for {command!r}: {detail}"
            )
        return result


class PacketPathController:
    """Concrete run-owned netns/veth/router/nftables lifecycle."""

    def __init__(
        self,
        *,
        topology: PacketPathRunTopology,
        cli: BoundedLinuxCli | None = None,
    ) -> None:
        self.topology = topology
        self.cli = cli or BoundedLinuxCli()
        self._topology_ready = False
        self._fault_active = False
        self._nft_table_created = False
        self._last_cleanup_problems: tuple[str, ...] = ()

    @property
    def topology_ready(self) -> bool:
        return self._topology_ready

    @property
    def fault_active(self) -> bool:
        return self._fault_active

    @property
    def last_cleanup_problems(self) -> tuple[str, ...]:
        """Expose bounded teardown diagnostics without replacing primary failures."""

        return self._last_cleanup_problems

    def setup(self) -> tuple[CommandResult, ...]:
        """Materialize the isolated three-namespace data plane exactly once."""

        if self._topology_ready:
            raise PacketPathControlError("packet-path topology is already materialized")
        results: list[CommandResult] = []
        try:
            for command in self.setup_commands():
                result = self.cli.run(command)
                results.append(result)
                if self._is_nft_table_create(command):
                    self._nft_table_created = True
        except BaseException:
            # Bounded best-effort teardown is mandatory after partial materialization.
            self.cleanup()
            raise
        self._topology_ready = True
        return tuple(results)

    def setup_commands(self) -> tuple[tuple[str, ...], ...]:
        """Return the reviewed argv plan without mutating host state."""

        t = self.topology
        return (
            ("ip", "netns", "add", t.subject_namespace),
            ("ip", "netns", "add", t.control_namespace),
            ("ip", "netns", "add", t.fixture_namespace),
            (
                "ip",
                "link",
                "add",
                t.subject_interface,
                "type",
                "veth",
                "peer",
                "name",
                t.router_subject_interface,
            ),
            ("ip", "link", "set", t.subject_interface, "netns", t.subject_namespace),
            (
                "ip",
                "link",
                "set",
                t.router_subject_interface,
                "netns",
                t.control_namespace,
            ),
            (
                "ip",
                "link",
                "add",
                t.router_fixture_interface,
                "type",
                "veth",
                "peer",
                "name",
                t.fixture_interface,
            ),
            (
                "ip",
                "link",
                "set",
                t.router_fixture_interface,
                "netns",
                t.control_namespace,
            ),
            ("ip", "link", "set", t.fixture_interface, "netns", t.fixture_namespace),
            (
                "ip",
                "-n",
                t.subject_namespace,
                "addr",
                "add",
                f"{t.subject_address}/30",
                "dev",
                t.subject_interface,
            ),
            (
                "ip",
                "-n",
                t.control_namespace,
                "addr",
                "add",
                f"{t.router_subject_address}/30",
                "dev",
                t.router_subject_interface,
            ),
            (
                "ip",
                "-n",
                t.control_namespace,
                "addr",
                "add",
                f"{t.router_fixture_address}/30",
                "dev",
                t.router_fixture_interface,
            ),
            (
                "ip",
                "-n",
                t.fixture_namespace,
                "addr",
                "add",
                f"{t.fixture_address}/30",
                "dev",
                t.fixture_interface,
            ),
            ("ip", "-n", t.subject_namespace, "link", "set", "lo", "up"),
            (
                "ip",
                "-n",
                t.subject_namespace,
                "link",
                "set",
                t.subject_interface,
                "up",
            ),
            ("ip", "-n", t.control_namespace, "link", "set", "lo", "up"),
            (
                "ip",
                "-n",
                t.control_namespace,
                "link",
                "set",
                t.router_subject_interface,
                "up",
            ),
            (
                "ip",
                "-n",
                t.control_namespace,
                "link",
                "set",
                t.router_fixture_interface,
                "up",
            ),
            ("ip", "-n", t.fixture_namespace, "link", "set", "lo", "up"),
            (
                "ip",
                "-n",
                t.fixture_namespace,
                "link",
                "set",
                t.fixture_interface,
                "up",
            ),
            (
                "ip",
                "-n",
                t.subject_namespace,
                "route",
                "add",
                t.fixture_subnet,
                "via",
                t.router_subject_address,
                "dev",
                t.subject_interface,
            ),
            (
                "ip",
                "-n",
                t.fixture_namespace,
                "route",
                "add",
                t.subject_subnet,
                "via",
                t.router_fixture_address,
                "dev",
                t.fixture_interface,
            ),
            (
                "ip",
                "netns",
                "exec",
                t.control_namespace,
                "sysctl",
                "-qw",
                "net.ipv4.ip_forward=1",
            ),
            (
                "ip",
                "netns",
                "exec",
                t.control_namespace,
                "nft",
                "add",
                "table",
                "ip",
                t.nft_table,
            ),
            (
                "ip",
                "netns",
                "exec",
                t.control_namespace,
                "nft",
                "add",
                "chain",
                "ip",
                t.nft_table,
                t.nft_chain,
                "{",
                "type",
                "filter",
                "hook",
                "forward",
                "priority",
                "0",
                ";",
                "policy",
                "accept",
                ";",
                "}",
            ),
        )

    def install_fault(self, mode: PacketPathFaultMode = PacketPathFaultMode.SELECTED) -> CommandResult:
        """Install exactly one run-owned forwarding DROP assembly."""

        if not self._topology_ready:
            raise PacketPathControlError("packet-path topology must be ready before fault install")
        if self._fault_active:
            raise PacketPathControlError("packet-path fault is already active")
        command = self.fault_command(mode)
        result = self.cli.run(command)
        self._fault_active = True
        return result

    def fault_command(self, mode: PacketPathFaultMode) -> tuple[str, ...]:
        t = self.topology
        base = (
            "ip",
            "netns",
            "exec",
            t.control_namespace,
            "nft",
            "add",
            "rule",
            "ip",
            t.nft_table,
            t.nft_chain,
            "iifname",
            t.router_subject_interface,
            "oifname",
            t.router_fixture_interface,
            "ip",
            "daddr",
            t.fixture_address,
        )
        if mode is PacketPathFaultMode.COLLATERAL:
            # Deliberately over-broad: both selected and non-target TCP ports match.
            return (*base, "drop")
        if mode is PacketPathFaultMode.BYPASS:
            return (*base, "tcp", "dport", str(t.unused_fault_port), "drop")
        if mode is PacketPathFaultMode.SELECTED:
            return (*base, "tcp", "dport", str(t.selected_port), "drop")
        raise EvidenceMaterializationError(f"unsupported packet-path fault mode: {mode!r}")

    def clear_fault(self) -> CommandResult:
        """Clear only the run-owned chain; provider acknowledgement is diagnostic."""

        if not self._topology_ready:
            raise PacketPathControlError("packet-path topology must be ready before fault clear")
        if not self._fault_active:
            raise PacketPathControlError("packet-path fault is not active")
        t = self.topology
        result = self.cli.run(
            (
                "ip",
                "netns",
                "exec",
                t.control_namespace,
                "nft",
                "flush",
                "chain",
                "ip",
                t.nft_table,
                t.nft_chain,
            )
        )
        self._fault_active = False
        return result

    def ruleset_snapshot(self) -> CommandResult:
        if not self._topology_ready:
            raise PacketPathControlError("packet-path topology is not materialized")
        t = self.topology
        return self.cli.run(
            (
                "ip",
                "netns",
                "exec",
                t.control_namespace,
                "nft",
                "-a",
                "list",
                "table",
                "ip",
                t.nft_table,
            )
        )

    def subject_command(
        self,
        argv: Sequence[str],
        *,
        uid: int = 65534,
        gid: int = 65534,
    ) -> tuple[str, ...]:
        """Build a Subject command with Linux capabilities removed.

        The privileged evaluator enters the namespace, then ``setpriv`` drops the
        Subject process to an unprivileged uid/gid, clears supplementary groups,
        removes inherited/ambient/bounding capabilities, and sets no-new-privs.
        No controller handle or shell is exposed to the Subject argv.
        """

        if not argv or any(not isinstance(item, str) or not item for item in argv):
            raise EvidenceMaterializationError("Subject command must contain non-empty argv")
        for value, name in ((uid, "uid"), (gid, "gid")):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise EvidenceMaterializationError(f"Subject {name} must be a non-negative integer")

        return (
            "ip",
            "netns",
            "exec",
            self.topology.subject_namespace,
            "setpriv",
            "--reuid",
            str(uid),
            "--regid",
            str(gid),
            "--clear-groups",
            "--bounding-set=-all",
            "--inh-caps=-all",
            "--ambient-caps=-all",
            "--no-new-privs",
            "--",
            *tuple(argv),
        )

    def fixture_command(self, argv: Sequence[str]) -> tuple[str, ...]:
        if not argv or any(not isinstance(item, str) or not item for item in argv):
            raise EvidenceMaterializationError("Fixture command must contain non-empty argv")
        return (
            "ip",
            "netns",
            "exec",
            self.topology.fixture_namespace,
            *tuple(argv),
        )

    def cleanup(self) -> tuple[str, ...]:
        """Boundedly remove only state owned by this run.

        The method is idempotent when namespace discovery succeeds. It never
        flushes host-global nftables state and never deletes unrelated namespaces.
        """

        problems: list[str] = []
        try:
            existing = self._namespace_names()
        except (PacketPathPrerequisiteError, PacketPathControlError) as exc:
            existing = set(self.topology.namespace_names)
            problems.append(f"namespace-discovery:{type(exc).__name__}")

        t = self.topology
        if self._nft_table_created and t.control_namespace in existing:
            result = self.cli.run(
                (
                    "ip",
                    "netns",
                    "exec",
                    t.control_namespace,
                    "nft",
                    "delete",
                    "table",
                    "ip",
                    t.nft_table,
                ),
                allow_failure=True,
            )
            if result.returncode != 0:
                problems.append(f"nft-table-delete:returncode={result.returncode}")
            else:
                self._nft_table_created = False

        teardown_order = (
            t.subject_namespace,
            t.fixture_namespace,
            t.control_namespace,
        )
        for namespace in teardown_order:
            if namespace not in existing:
                continue
            result = self.cli.run(
                ("ip", "netns", "del", namespace),
                allow_failure=True,
            )
            if result.returncode != 0:
                problems.append(f"namespace-delete:{namespace}:returncode={result.returncode}")

        self._topology_ready = False
        self._fault_active = False
        if t.control_namespace not in self._namespace_names_best_effort():
            self._nft_table_created = False
        self._last_cleanup_problems = tuple(problems)
        return self._last_cleanup_problems

    def residual_resources(self) -> tuple[str, ...]:
        """Report surviving run-owned namespaces after bounded teardown."""

        existing = self._namespace_names()
        return tuple(
            f"namespace:{namespace}"
            for namespace in self.topology.namespace_names
            if namespace in existing
        )

    def _namespace_names_best_effort(self) -> set[str]:
        try:
            return self._namespace_names()
        except (PacketPathPrerequisiteError, PacketPathControlError):
            return set(self.topology.namespace_names)

    def _is_nft_table_create(self, command: Sequence[str]) -> bool:
        t = self.topology
        return tuple(command) == (
            "ip",
            "netns",
            "exec",
            t.control_namespace,
            "nft",
            "add",
            "table",
            "ip",
            t.nft_table,
        )

    def _namespace_names(self) -> set[str]:
        result = self.cli.run(("ip", "netns", "list"))
        names: set[str] = set()
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            names.add(stripped.split()[0])
        return names

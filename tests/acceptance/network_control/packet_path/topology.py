"""Concrete Linux packet-path topology identities for Network Control PTL-001.

This module is project acceptance-evidence plumbing only. Linux namespace,
interface, address, and nftables identities are implementation provenance; they
do not define portable AVP Network Control semantics.
"""

from __future__ import annotations

import hashlib
import ipaddress
import re
from dataclasses import dataclass

from ..evidence_core import (
    EvidenceMaterializationError,
    EvidencePlan,
    ExchangeProgram,
    MaterializedEndpoint,
)

_ADDRESS_POOL = ipaddress.ip_network("198.18.0.0/15")
_RUN_BLOCK_PREFIX = 29
_RUN_BLOCK_SIZE = 1 << (32 - _RUN_BLOCK_PREFIX)
_RUN_BLOCK_COUNT = _ADDRESS_POOL.num_addresses // _RUN_BLOCK_SIZE
_RUN_TOKEN_RE = re.compile(r"[^a-z0-9-]+")
_INTERFACE_NAME_LIMIT = 15

DEFAULT_SELECTED_PORT = 42101
DEFAULT_CONTROL_PORT = 42102


@dataclass(frozen=True, slots=True)
class PacketPathRunTopology:
    """Run-scoped, deterministic three-namespace packet-path materialization."""

    run_id: str
    run_token: str
    subject_namespace: str
    control_namespace: str
    fixture_namespace: str
    subject_interface: str
    router_subject_interface: str
    router_fixture_interface: str
    fixture_interface: str
    subject_subnet: str
    fixture_subnet: str
    subject_address: str
    router_subject_address: str
    router_fixture_address: str
    fixture_address: str
    selected_port: int
    control_port: int
    nft_table: str
    nft_chain: str

    @classmethod
    def for_run(
        cls,
        run_id: str,
        *,
        selected_port: int = DEFAULT_SELECTED_PORT,
        control_port: int = DEFAULT_CONTROL_PORT,
    ) -> "PacketPathRunTopology":
        """Derive collision-resistant local identities without a mutable allocator."""

        if not run_id:
            raise EvidenceMaterializationError("packet-path run id must be non-empty")
        _validate_port(selected_port, "selected")
        _validate_port(control_port, "control")
        if selected_port == control_port:
            raise EvidenceMaterializationError("selected and control fixture ports must be distinct")

        digest = hashlib.sha256(run_id.encode("utf-8")).hexdigest()
        normalized = _RUN_TOKEN_RE.sub("-", run_id.lower()).strip("-")[:16] or "run"
        run_token = f"{normalized}-{digest[:8]}"

        slot = int(digest[:8], 16) % _RUN_BLOCK_COUNT
        block_start = int(_ADDRESS_POOL.network_address) + slot * _RUN_BLOCK_SIZE
        subject_network = ipaddress.ip_network(
            f"{ipaddress.ip_address(block_start)}/30",
            strict=False,
        )
        fixture_network = ipaddress.ip_network(
            f"{ipaddress.ip_address(block_start + 4)}/30",
            strict=False,
        )
        subject_hosts = tuple(subject_network.hosts())
        fixture_hosts = tuple(fixture_network.hosts())

        short = digest[:10]
        interfaces = (
            f"avs{short}",
            f"avc{short}",
            f"avr{short}",
            f"avf{short}",
        )
        if any(len(name) > _INTERFACE_NAME_LIMIT for name in interfaces):
            raise AssertionError("derived packet-path interface exceeds Linux IFNAMSIZ boundary")
        if len(set(interfaces)) != len(interfaces):
            raise AssertionError("derived packet-path interface identities are not unique")

        return cls(
            run_id=run_id,
            run_token=run_token,
            subject_namespace=f"avp-nc-subject-{run_token}",
            control_namespace=f"avp-nc-control-{run_token}",
            fixture_namespace=f"avp-nc-fixture-{run_token}",
            subject_interface=interfaces[0],
            router_subject_interface=interfaces[1],
            router_fixture_interface=interfaces[2],
            fixture_interface=interfaces[3],
            subject_subnet=str(subject_network),
            fixture_subnet=str(fixture_network),
            subject_address=str(subject_hosts[0]),
            router_subject_address=str(subject_hosts[1]),
            router_fixture_address=str(fixture_hosts[0]),
            fixture_address=str(fixture_hosts[1]),
            selected_port=selected_port,
            control_port=control_port,
            nft_table=f"avp_nc_{digest[:10]}",
            nft_chain="forward_cut",
        )

    @property
    def namespace_names(self) -> tuple[str, str, str]:
        return (
            self.subject_namespace,
            self.control_namespace,
            self.fixture_namespace,
        )

    @property
    def interface_names(self) -> tuple[str, str, str, str]:
        return (
            self.subject_interface,
            self.router_subject_interface,
            self.router_fixture_interface,
            self.fixture_interface,
        )

    @property
    def selected_endpoint(self) -> MaterializedEndpoint:
        return MaterializedEndpoint(
            family="ipv4",
            address=self.fixture_address,
            port=self.selected_port,
            role="selected-fixture",
        )

    @property
    def control_endpoint(self) -> MaterializedEndpoint:
        return MaterializedEndpoint(
            family="ipv4",
            address=self.fixture_address,
            port=self.control_port,
            role="control-fixture",
        )

    @property
    def unused_fault_port(self) -> int:
        """Return one deterministic TCP port not used by either fixture binding."""

        for candidate in (
            self.selected_port + 1,
            self.control_port + 1,
            self.selected_port - 1,
            self.control_port - 1,
            9,
        ):
            if 1 <= candidate <= 65535 and candidate not in {
                self.selected_port,
                self.control_port,
            }:
                return candidate
        raise AssertionError("could not derive an unused packet-path fault port")

    def evidence_plan(
        self,
        *,
        design_revision: str,
        semantic_baseline_commit: str,
        semantic_baseline_path: str,
        path_id: str,
        exchange_program: ExchangeProgram,
        observation_budget_ns: int,
        negative_mode: str | None = None,
    ) -> EvidencePlan:
        """Bind the non-terminating topology into the provider-neutral plan.

        Subject-visible and fixture endpoint positions intentionally contain the
        same socket identity. Forwarding through the router does not create a
        second TCP connection and therefore must not fabricate terminating-style
        upstream initiation evidence.
        """

        selected = self.selected_endpoint
        control = self.control_endpoint
        return EvidencePlan(
            design_revision=design_revision,
            semantic_baseline_commit=semantic_baseline_commit,
            semantic_baseline_path=semantic_baseline_path,
            run_id=self.run_id,
            path_id=path_id,
            subject_destination=selected,
            upstream_fixture=selected,
            exchange_program=exchange_program,
            observation_budget_ns=observation_budget_ns,
            non_target_subject_destination=control,
            non_target_upstream_fixture=control,
            negative_mode=negative_mode,
        )

    def provenance_document(self) -> dict[str, object]:
        """Return stable topology declarations suitable for retained diagnostics."""

        return {
            "mechanism": "linux-netns-veth-nftables",
            "runToken": self.run_token,
            "namespaces": {
                "subject": self.subject_namespace,
                "control": self.control_namespace,
                "fixture": self.fixture_namespace,
            },
            "interfaces": {
                "subject": self.subject_interface,
                "routerSubject": self.router_subject_interface,
                "routerFixture": self.router_fixture_interface,
                "fixture": self.fixture_interface,
            },
            "segments": {
                "subject": self.subject_subnet,
                "fixture": self.fixture_subnet,
            },
            "addresses": {
                "subject": self.subject_address,
                "routerSubject": self.router_subject_address,
                "routerFixture": self.router_fixture_address,
                "fixture": self.fixture_address,
            },
            "selectedPort": self.selected_port,
            "controlPort": self.control_port,
            "nft": {
                "family": "ip",
                "table": self.nft_table,
                "chain": self.nft_chain,
            },
        }


def _validate_port(port: int, role: str) -> None:
    if isinstance(port, bool) or not isinstance(port, int) or not (1 <= port <= 65535):
        raise EvidenceMaterializationError(
            f"{role} packet-path TCP port must be an integer in [1, 65535]"
        )

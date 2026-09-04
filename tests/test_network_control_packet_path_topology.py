"""PTL-001 tests for deterministic packet-path topology materialization."""

from __future__ import annotations

import ipaddress
import unittest

from acceptance.network_control.evidence_core import (
    EvidenceMaterializationError,
    ExchangeProgram,
)
from acceptance.network_control.packet_path.topology import PacketPathRunTopology

_BASELINE = "140ad041953ebea57a37273a63145258bba2a6ac"
_AEP_PATH = "rfcs/AEP-0012-network-control-resource-profile.md"


class PacketPathTopologyTests(unittest.TestCase):
    def test_topology_is_deterministic_run_scoped_and_point_to_point(self) -> None:
        first = PacketPathRunTopology.for_run("PTL 001 / Example")
        second = PacketPathRunTopology.for_run("PTL 001 / Example")
        other = PacketPathRunTopology.for_run("PTL 002 / Example")

        self.assertEqual(first, second)
        self.assertNotEqual(first.run_token, other.run_token)
        self.assertEqual(len(set(first.namespace_names)), 3)
        self.assertEqual(len(set(first.interface_names)), 4)
        self.assertTrue(all(len(name) <= 15 for name in first.interface_names))

        subject_network = ipaddress.ip_network(first.subject_subnet)
        fixture_network = ipaddress.ip_network(first.fixture_subnet)
        self.assertEqual(subject_network.prefixlen, 30)
        self.assertEqual(fixture_network.prefixlen, 30)
        self.assertTrue(subject_network.subnet_of(ipaddress.ip_network("198.18.0.0/15")))
        self.assertTrue(fixture_network.subnet_of(ipaddress.ip_network("198.18.0.0/15")))
        self.assertNotEqual(subject_network, fixture_network)
        self.assertIn(ipaddress.ip_address(first.subject_address), subject_network)
        self.assertIn(ipaddress.ip_address(first.router_subject_address), subject_network)
        self.assertIn(ipaddress.ip_address(first.router_fixture_address), fixture_network)
        self.assertIn(ipaddress.ip_address(first.fixture_address), fixture_network)

    def test_selected_and_control_bind_same_non_terminating_fixture_address(self) -> None:
        topology = PacketPathRunTopology.for_run("run-bindings")
        selected = topology.selected_endpoint
        control = topology.control_endpoint

        self.assertEqual(selected.address, topology.fixture_address)
        self.assertEqual(control.address, topology.fixture_address)
        self.assertNotEqual(selected.port, control.port)
        self.assertNotIn(
            topology.unused_fault_port,
            {topology.selected_port, topology.control_port},
        )

    def test_packet_path_evidence_plan_has_no_distinct_upstream_socket(self) -> None:
        topology = PacketPathRunTopology.for_run("run-plan")
        program = ExchangeProgram(
            program_id="exact-byte-v0.1",
            request_prefix=b"REQ\x00",
            request_suffix=b"\x00END",
            response_prefix=b"RESP\x00",
            response_suffix=b"\x00END",
        )
        plan = topology.evidence_plan(
            design_revision="NPR-011-packet-path-v0.1",
            semantic_baseline_commit=_BASELINE,
            semantic_baseline_path=_AEP_PATH,
            path_id="selected-path",
            exchange_program=program,
            observation_budget_ns=1_000_000_000,
        )

        self.assertEqual(plan.subject_destination, plan.upstream_fixture)
        self.assertEqual(
            plan.non_target_subject_destination,
            plan.non_target_upstream_fixture,
        )
        assert plan.non_target_subject_destination is not None
        self.assertNotEqual(
            (plan.subject_destination.address, plan.subject_destination.port),
            (
                plan.non_target_subject_destination.address,
                plan.non_target_subject_destination.port,
            ),
        )
        plan.seal().verify()

    def test_port_validation_fails_closed(self) -> None:
        with self.assertRaises(EvidenceMaterializationError):
            PacketPathRunTopology.for_run("same-port", selected_port=42001, control_port=42001)
        with self.assertRaises(EvidenceMaterializationError):
            PacketPathRunTopology.for_run("bad-port", selected_port=0)
        with self.assertRaises(EvidenceMaterializationError):
            PacketPathRunTopology.for_run("bool-port", selected_port=True)

    def test_provenance_is_mechanism_local_and_literal(self) -> None:
        topology = PacketPathRunTopology.for_run("run-provenance")
        document = topology.provenance_document()

        self.assertEqual(document["mechanism"], "linux-netns-veth-nftables")
        addresses = document["addresses"]
        nft = document["nft"]
        assert isinstance(addresses, dict)
        assert isinstance(nft, dict)
        self.assertEqual(addresses["fixture"], topology.fixture_address)
        self.assertEqual(nft["family"], "ip")
        self.assertNotIn("SATISFIED", repr(document))
        self.assertNotIn("verdict", repr(document).lower())


if __name__ == "__main__":
    unittest.main()

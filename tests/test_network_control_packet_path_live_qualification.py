"""PTL-001 ordinary-CI tests for packet-path live qualification orchestration."""

from __future__ import annotations

import json
import unittest

from acceptance.network_control.attempt_client import ExchangeObservation
from acceptance.network_control.evidence_core import ExchangeProgram
from acceptance.network_control.packet_path.controller import PacketPathController
from acceptance.network_control.packet_path.execution import PacketPathExecutionPlan
from acceptance.network_control.packet_path.live_qualification import (
    CleanupObservation,
    NamespaceInventoryObservation,
    PacketPathLiveQualification,
    PacketPathQualificationCommands,
    PacketPathQualificationObservations,
    PreflightObservation,
    QualifiedExchangeObservation,
    RouteCandidate,
    RouteObservation,
    SubjectSecurityObservation,
    WitnessCanaryObservation,
    derive_capture_assurance,
    parse_route_candidates,
)
from acceptance.network_control.packet_path.qualification import PacketPathQualificationPlan
from acceptance.network_control.packet_path.topology import PacketPathRunTopology

_BASELINE = "140ad041953ebea57a37273a63145258bba2a6ac"
_AEP_PATH = "rfcs/AEP-0012-network-control-resource-profile.md"
_PROVISIONAL = (
    "egress-coverage-unverified",
    "directionality-unverified",
    "offload-normalization-unverified",
    "pre-syn-connect-gap-unclosed",
)


class PacketPathLiveQualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology = PacketPathRunTopology.for_run("packet-path-live-qualification")
        plan = self.topology.evidence_plan(
            design_revision="NPR-011-packet-path-v0.1",
            semantic_baseline_commit=_BASELINE,
            semantic_baseline_path=_AEP_PATH,
            path_id="selected-path",
            exchange_program=ExchangeProgram(
                program_id="exact-byte-v0.1",
                request_prefix=b"REQ\x00",
                request_suffix=b"\x00END",
                response_prefix=b"RESP\x00",
                response_suffix=b"\x00END",
            ),
            observation_budget_ns=1_000_000_000,
        )
        self.controller = PacketPathController(topology=self.topology)
        self.execution = PacketPathExecutionPlan.build(
            topology=self.topology,
            evidence_plan=plan,
        )
        self.qualification = PacketPathQualificationPlan.for_topology(self.topology)
        self.commands = PacketPathQualificationCommands.build(
            topology=self.topology,
            controller=self.controller,
            execution_plan=self.execution,
            qualification_plan=self.qualification,
            python_executable="/usr/bin/python3",
        )

    def test_command_contract_keeps_subject_and_witness_authority_distinct(self) -> None:
        security = self.commands.subject_security_command()
        witness, witness_input = self.commands.witness_command_and_input(
            spec=self.commands.capture_canaries()[0],
            attempt_id="qualification-canary-1",
        )

        self.assertIn("setpriv", security)
        self.assertIn("--bounding-set=-all", security)
        self.assertNotIn("setpriv", witness)
        self.assertEqual(witness[:4], ("ip", "netns", "exec", self.topology.subject_namespace))
        self.assertEqual(witness_input["assurance"]["egressCoverageVerified"], False)
        self.assertEqual(witness_input["roleId"], "subject")

    def test_capture_assurance_is_derived_from_four_real_canary_shapes(self) -> None:
        assurance = derive_capture_assurance(_canaries())

        self.assertEqual(assurance.problems(), ())

        dropped = list(_canaries())
        dropped[0] = WitnessCanaryObservation(
            label=dropped[0].label,
            total_initiations=dropped[0].total_initiations,
            expected_target_initiations=dropped[0].expected_target_initiations,
            alternate_target_initiations=dropped[0].alternate_target_initiations,
            raw_syn_packets=dropped[0].raw_syn_packets,
            retransmitted_syn_packets=dropped[0].retransmitted_syn_packets,
            capture_drops=1,
            validity_problems=dropped[0].validity_problems,
            ready_before_injection=True,
        )
        self.assertTrue(derive_capture_assurance(dropped).problems())

    def test_complete_independent_observations_produce_ready_report(self) -> None:
        report = PacketPathLiveQualification(self.commands).project_report(
            self._positive_observations()
        )

        self.assertTrue(report.ready, report.problems())
        self.assertEqual(report.problems(), ())

    def test_route_escape_fails_route_and_no_escape_properties(self) -> None:
        observations = self._positive_observations()
        escaped = PacketPathQualificationObservations(
            preflight=observations.preflight,
            namespaces=observations.namespaces,
            routes=RouteObservation(
                subject_to_fixture=(
                    RouteCandidate("0.0.0.0/0", None, "eth9"),
                    *observations.routes.subject_to_fixture,
                ),
                fixture_to_subject=observations.routes.fixture_to_subject,
            ),
            subject_security=observations.subject_security,
            exchanges=observations.exchanges,
            witness_canaries=observations.witness_canaries,
            cleanup=observations.cleanup,
        )

        report = PacketPathLiveQualification(self.commands).project_report(escaped)
        self.assertIn("unverified:route-through-control", report.problems())
        self.assertIn("unverified:no-route-escape", report.problems())

    def test_subject_control_surface_presence_fails_closed(self) -> None:
        observations = self._positive_observations()
        leaked = SubjectSecurityObservation(
            uid=65534,
            euid=65534,
            gid=65534,
            egid=65534,
            supplementary_groups=(),
            no_new_privs=1,
            capability_values=("0", "0", "0", "0", "0"),
            netns_identity="net:[101]",
            environment_presence=(
                ("AVP_FUTURE_FAULT_SCHEDULE", False),
                ("AVP_PACKET_PATH_CONTROL", True),
            ),
        )
        changed = PacketPathQualificationObservations(
            preflight=observations.preflight,
            namespaces=observations.namespaces,
            routes=observations.routes,
            subject_security=leaked,
            exchanges=observations.exchanges,
            witness_canaries=observations.witness_canaries,
            cleanup=observations.cleanup,
        )

        report = PacketPathLiveQualification(self.commands).project_report(changed)
        self.assertIn("unverified:subject-control-isolation", report.problems())
        self.assertNotIn("unverified:subject-privilege-isolation", report.problems())

    def test_exchange_phase_binding_is_explicit_not_inferred_from_attempt_id(self) -> None:
        observations = self._positive_observations()
        cut = observations.exchanges[0]

        self.assertEqual(cut.phase_id, "subject-active-cut")
        self.assertEqual(cut.observation.attempt_id, "opaque-attempt-cut")
        self.assertNotIn("subject-active-cut", cut.observation.attempt_id)

    def test_route_parser_retains_all_matching_routes_for_escape_detection(self) -> None:
        payload = json.dumps(
            [
                {
                    "dst": self.topology.fixture_subnet,
                    "gateway": self.topology.router_subject_address,
                    "dev": self.topology.subject_interface,
                },
                {"dst": "0.0.0.0/0", "dev": "eth9"},
                {"dst": "203.0.113.0/24", "dev": "irrelevant"},
            ]
        )

        routes = parse_route_candidates(payload, target_address=self.topology.fixture_address)
        self.assertEqual(len(routes), 2)
        self.assertEqual(routes[0].device, self.topology.subject_interface)
        self.assertEqual(routes[1].device, "eth9")

    def test_cleanup_residual_is_not_repaired_by_control_ack(self) -> None:
        observations = self._positive_observations()
        changed = PacketPathQualificationObservations(
            preflight=observations.preflight,
            namespaces=observations.namespaces,
            routes=observations.routes,
            subject_security=observations.subject_security,
            exchanges=observations.exchanges,
            witness_canaries=observations.witness_canaries,
            cleanup=CleanupObservation((), ("namespace:residual",)),
        )

        report = PacketPathLiveQualification(self.commands).project_report(changed)
        self.assertIn("unverified:cleanup-residual-free", report.problems())

    def _positive_observations(self) -> PacketPathQualificationObservations:
        t = self.topology
        namespaces = (
            NamespaceInventoryObservation(
                t.subject_namespace,
                "net:[101]",
                ((t.subject_interface, t.subject_address),),
            ),
            NamespaceInventoryObservation(
                t.control_namespace,
                "net:[102]",
                (
                    (t.router_fixture_interface, t.router_fixture_address),
                    (t.router_subject_interface, t.router_subject_address),
                ),
            ),
            NamespaceInventoryObservation(
                t.fixture_namespace,
                "net:[103]",
                ((t.fixture_interface, t.fixture_address),),
            ),
        )
        routes = RouteObservation(
            subject_to_fixture=(
                RouteCandidate(t.fixture_subnet, t.router_subject_address, t.subject_interface),
            ),
            fixture_to_subject=(
                RouteCandidate(t.subject_subnet, t.router_fixture_address, t.fixture_interface),
            ),
        )
        security = SubjectSecurityObservation(
            uid=65534,
            euid=65534,
            gid=65534,
            egid=65534,
            supplementary_groups=(),
            no_new_privs=1,
            capability_values=("0", "0", "0", "0", "0"),
            netns_identity="net:[101]",
            environment_presence=(
                ("AVP_FUTURE_FAULT_SCHEDULE", False),
                ("AVP_PACKET_PATH_CONTROL", False),
            ),
        )
        return PacketPathQualificationObservations(
            preflight=PreflightObservation(
                uname="Linux 6.8.0 x86_64",
                effective_uid=0,
                tool_versions=(
                    ("ip", "ip utility, iproute2"),
                    ("nft", "nftables v1"),
                    ("setpriv", "setpriv util-linux"),
                    ("python", "Python 3.13"),
                ),
            ),
            namespaces=namespaces,
            routes=routes,
            subject_security=security,
            exchanges=(
                QualifiedExchangeObservation("subject-active-cut", _cut("opaque-attempt-cut")),
                QualifiedExchangeObservation("non-target-control", _success("opaque-attempt-control")),
                QualifiedExchangeObservation("recovery-1", _success("opaque-attempt-r1")),
                QualifiedExchangeObservation("recovery-2", _success("opaque-attempt-r2")),
                QualifiedExchangeObservation("stability", _success("opaque-attempt-stability")),
            ),
            witness_canaries=_canaries(),
            cleanup=CleanupObservation((), ()),
        )


def _success(attempt_id: str) -> ExchangeObservation:
    return ExchangeObservation(
        attempt_id=attempt_id,
        completed=True,
        mismatch_observed=False,
        observation_budget_expired=False,
        elapsed_ns=10,
        response_size=4,
        response_sha256="a" * 64,
        native_error=None,
    )


def _cut(attempt_id: str) -> ExchangeObservation:
    return ExchangeObservation(
        attempt_id=attempt_id,
        completed=False,
        mismatch_observed=False,
        observation_budget_expired=True,
        elapsed_ns=1_000_000_000,
        response_size=0,
        response_sha256=None,
        native_error=None,
    )


def _canaries() -> tuple[WitnessCanaryObservation, ...]:
    return (
        WitnessCanaryObservation("one-expected", 1, 1, 0, 1, 0, 0, _PROVISIONAL, True),
        WitnessCanaryObservation("two-expected", 2, 2, 0, 2, 0, 0, _PROVISIONAL, True),
        WitnessCanaryObservation("expected-plus-alternate", 2, 1, 1, 2, 0, 0, _PROVISIONAL, True),
        WitnessCanaryObservation("duplicate-syn-normalization", 1, 1, 0, 2, 1, 0, _PROVISIONAL, True),
    )


if __name__ == "__main__":
    unittest.main()

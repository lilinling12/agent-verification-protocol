"""TEL-002 tests for native-Linux live-lab composition and cleanup invariants."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import MethodType
from typing import Any

from acceptance.network_control.evidence_core import (
    ArtifactStore,
    AttemptFactory,
    EvidencePlan,
    ExchangeProgram,
    MaterializedEndpoint,
)
from acceptance.network_control.toxiproxy_binding import (
    ProxyBinding,
    ToxiproxyRunTopology,
)
from acceptance.network_control.toxiproxy_evidence import NegativeMode
from acceptance.network_control.toxiproxy_live_lab import (
    LabHelperArtifact,
    LabRoleAddresses,
    LiveMaterialization,
    ToxiproxyLiveLab,
    _combine_upstream_witnesses,
    _non_loopback_addresses,
)
from acceptance.network_control.witness_evidence import CaptureAssurance

_BASELINE = "883956784e57152537b11aaf65143209fc131429"
_HELPER_DIGEST = "sha256:f576b530293e74140ea91d262232648d5c4f45640a95ec447757701bfcacf034"


def endpoint(address: str, port: int, role: str) -> MaterializedEndpoint:
    return MaterializedEndpoint(family="ipv4", address=address, port=port, role=role)


def witness_document(
    channel: str,
    *,
    total: int,
    expected: int,
    alternate: int = 0,
    validity: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "channelFacts": [
            {
                "channel": channel,
                "totalInitiations": total,
                "expectedTargetInitiations": expected,
                "alternateTargetInitiations": alternate,
                "rawSynPackets": total,
                "retransmittedSynPackets": 0,
                "validityProblems": list(validity),
            }
        ]
    }


class HelperArtifactTests(unittest.TestCase):
    def test_helper_image_is_exact_digest_pinned(self) -> None:
        artifact = LabHelperArtifact.reviewed_amd64()
        self.assertEqual(artifact.platform, "linux/amd64")
        self.assertEqual(artifact.platform_digest, _HELPER_DIGEST)
        self.assertEqual(artifact.image_ref, f"docker.io/library/python@{_HELPER_DIGEST}")
        self.assertNotIn(artifact.reviewed_tag, artifact.image_ref)

    def test_role_addresses_are_distinct_and_inside_data_subnet(self) -> None:
        topology = ToxiproxyRunTopology.for_run("tel002-live-addresses")
        addresses = LabRoleAddresses.from_topology(topology)
        values = {
            addresses.selected_fixture,
            addresses.control_fixture,
            addresses.subject,
            addresses.privileged_probe,
            topology.data_address,
        }
        self.assertEqual(len(values), 5)
        prefix = topology.data_address.rsplit(".", 1)[0] + "."
        self.assertTrue(all(value.startswith(prefix) for value in values))


class WitnessAggregationTests(unittest.TestCase):
    def test_data_and_admin_upstream_witnesses_are_combined_without_hiding_either_path(self) -> None:
        combined = _combine_upstream_witnesses(
            [
                witness_document("W-upstream-data", total=1, expected=1),
                witness_document(
                    "W-upstream-admin",
                    total=1,
                    expected=0,
                    alternate=1,
                    validity=("unexpected-admin-initiation",),
                ),
            ]
        )
        self.assertEqual(combined.channel, "W-upstream")
        self.assertEqual(combined.total_initiations, 2)
        self.assertEqual(combined.expected_target_initiations, 1)
        self.assertEqual(combined.alternate_target_initiations, 1)
        self.assertIn("unexpected-admin-initiation", combined.validity_problems)

    def test_inventory_parser_excludes_only_loopback(self) -> None:
        payload = (
            '{"interfaces":['
            '{"interface":"lo","ipv4Address":"127.0.0.1","loopback":true},'
            '{"interface":"eth0","ipv4Address":"172.30.25.5","loopback":false}'
            ']}'
        )
        self.assertEqual(_non_loopback_addresses(payload), {"172.30.25.5"})


class _FakeFixture:
    def request(self, document: dict[str, object]) -> dict[str, object]:
        raise AssertionError(f"fixture must not be armed before all witnesses start: {document!r}")


class _FakeWitness:
    def __init__(self, name: str) -> None:
        self.container_name = name
        self.closed = False
        self.close_command_seen = False

    def send(self, document: dict[str, object]) -> None:
        self.close_command_seen = document.get("op") == "close"

    def receive(self) -> dict[str, object]:
        return witness_document("W-front", total=0, expected=0)

    def close(self) -> tuple[str, ...]:
        self.closed = True
        return ()


class WitnessStartupCleanupTests(unittest.TestCase):
    def test_second_witness_start_failure_closes_first_started_sidecar(self) -> None:
        selected_upstream = endpoint("172.30.50.3", 42001, "upstream-fixture")
        control_upstream = endpoint("172.30.50.4", 42002, "control-fixture")
        selected = ProxyBinding(
            "selected-run",
            endpoint("172.30.50.2", 41001, "subject-destination"),
            selected_upstream,
        )
        control = ProxyBinding(
            "control-run",
            endpoint("172.30.50.2", 41002, "control-subject-destination"),
            control_upstream,
        )
        plan = EvidencePlan(
            design_revision="TEL-002-v0.1",
            semantic_baseline_commit=_BASELINE,
            semantic_baseline_path="rfcs/AEP-0012-network-control-resource-profile.md",
            run_id="cleanup-witness-start",
            path_id="network-control-selected-path",
            subject_destination=selected.listen,
            upstream_fixture=selected.upstream,
            non_target_subject_destination=control.listen,
            non_target_upstream_fixture=control.upstream,
            exchange_program=ExchangeProgram(
                program_id="live-cleanup-test",
                request_prefix=b"REQ",
                request_suffix=b"END",
                response_prefix=b"RESP",
                response_suffix=b"END",
            ),
            observation_budget_ns=1_000_000,
        )

        with tempfile.TemporaryDirectory() as temporary:
            lab = object.__new__(ToxiproxyLiveLab)
            lab._materialization = LiveMaterialization(  # type: ignore[attr-defined]
                sealed_plan=plan.seal(),
                selected_binding=selected,
                control_binding=control,
                admin=object(),  # type: ignore[arg-type]
            )
            lab._attempt_factory = AttemptFactory(b"T" * 32)  # type: ignore[attr-defined]
            lab._attempt_ordinal = 0  # type: ignore[attr-defined]
            lab._selected_fixture = _FakeFixture()  # type: ignore[attr-defined]
            lab._control_fixture = _FakeFixture()  # type: ignore[attr-defined]
            lab._subject_name = "subject"  # type: ignore[attr-defined]
            lab._probe_name = "probe"  # type: ignore[attr-defined]
            lab.addresses = LabRoleAddresses(  # type: ignore[attr-defined]
                selected_fixture="172.30.50.3",
                control_fixture="172.30.50.4",
                subject="172.30.50.5",
                privileged_probe="172.30.50.6",
            )
            lab.topology = ToxiproxyRunTopology.for_run("cleanup-witness-start")  # type: ignore[attr-defined]
            lab.observation_budget_ns = 1_000_000  # type: ignore[attr-defined]
            lab.artifact_store = ArtifactStore(Path(temporary))  # type: ignore[attr-defined]
            lab.capture_assurance = CaptureAssurance(True, True, True, True)  # type: ignore[attr-defined]

            first = _FakeWitness("witness-first")
            calls = 0

            def start_witness(self: ToxiproxyLiveLab, **kwargs: Any) -> _FakeWitness:
                nonlocal calls
                del self, kwargs
                calls += 1
                if calls == 1:
                    return first
                raise RuntimeError("forced-second-witness-start-failure")

            lab._start_witness = MethodType(start_witness, lab)  # type: ignore[method-assign]

            with self.assertRaisesRegex(RuntimeError, "forced-second-witness-start-failure"):
                lab.certified_attempt("subject-active-cut", False, NegativeMode.HIDDEN_RETRY_FALLBACK)

            self.assertTrue(first.close_command_seen)
            self.assertTrue(first.closed)


if __name__ == "__main__":
    unittest.main()

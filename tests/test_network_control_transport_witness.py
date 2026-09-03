"""TEL-001 independent transport-initiation witness tests."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from acceptance.network_control.evidence_core import ArtifactStore, AssessmentClass, assess_initiation_integrity
from acceptance.network_control.tcp_packets import build_synthetic_syn_frame, parse_initial_syn
from acceptance.network_control.witness import LinuxSynWitness, WitnessPrerequisiteError
from acceptance.network_control.witness_evidence import (
    CaptureAssurance,
    RawFrameRecord,
    WitnessScope,
    capture_integrity_problems,
    normalize_channel,
    serialize_raw_witness,
    synthetic_observation,
)
from test_network_control_evidence_core import endpoint


def scope(channel: str = "W-front") -> WitnessScope:
    if channel == "W-front":
        return WitnessScope(
            channel=channel,
            role_id="subject-role",
            source_addresses=("10.10.0.2",),
            expected_target=endpoint("10.10.0.3", 19001, "subject-destination"),
        )
    return WitnessScope(
        channel=channel,
        role_id="terminating-role",
        source_addresses=("10.20.0.2",),
        expected_target=endpoint("10.20.0.3", 19002, "upstream-fixture"),
    )


class PacketParsingTests(unittest.TestCase):
    def test_parses_ipv4_and_ipv6_initial_syn(self) -> None:
        for source, target in (("10.1.0.2", "10.1.0.3"), ("2001:db8::2", "2001:db8::3")):
            parsed = parse_initial_syn(
                build_synthetic_syn_frame(
                    source_address=source,
                    destination_address=target,
                    source_port=30001,
                    destination_port=443,
                    sequence=12345,
                )
            )
            self.assertIsNotNone(parsed)
            assert parsed is not None
            self.assertEqual(parsed.source_address, source)
            self.assertEqual(parsed.destination_address, target)
            self.assertEqual(parsed.sequence, 12345)


class WitnessNormalizationTests(unittest.TestCase):
    def test_syn_retransmission_normalizes_to_one_initiation(self) -> None:
        witness_scope = scope()
        first = synthetic_observation(
            witness_scope,
            attempt_id="a",
            source_port=30001,
            sequence=99,
            monotonic_ns=1,
        )
        retransmission = dataclasses.replace(first, monotonic_ns=2)
        facts = normalize_channel(witness_scope, (first, retransmission))
        self.assertEqual(facts.total_initiations, 1)
        self.assertEqual(facts.expected_target_initiations, 1)
        self.assertEqual(facts.raw_syn_packets, 2)
        self.assertEqual(facts.retransmitted_syn_packets, 1)

    def test_two_real_connections_normalize_to_two_initiations(self) -> None:
        witness_scope = scope()
        observations = (
            synthetic_observation(witness_scope, attempt_id="a", source_port=30001, sequence=99),
            synthetic_observation(witness_scope, attempt_id="a", source_port=30002, sequence=100),
        )
        facts = normalize_channel(witness_scope, observations)
        self.assertEqual(facts.total_initiations, 2)
        self.assertEqual(facts.expected_target_initiations, 2)

    def test_failed_unaccepted_extra_attempt_is_detected_without_fixture_accept(self) -> None:
        witness_scope = scope("W-upstream")
        observations = (
            synthetic_observation(witness_scope, attempt_id="a", source_port=31001, sequence=10),
            synthetic_observation(witness_scope, attempt_id="a", source_port=31002, sequence=11),
        )
        facts = normalize_channel(witness_scope, observations)
        self.assertEqual(facts.total_initiations, 2)
        self.assertEqual(facts.expected_target_initiations, 2)

    def test_alternate_address_or_port_is_not_filtered_away(self) -> None:
        witness_scope = scope()
        expected = synthetic_observation(witness_scope, attempt_id="a", source_port=30001, sequence=1)
        alternate_address = synthetic_observation(
            witness_scope,
            attempt_id="a",
            source_port=30002,
            destination_address="10.10.0.9",
            sequence=2,
        )
        alternate_port = synthetic_observation(
            witness_scope,
            attempt_id="a",
            source_port=30003,
            destination_port=19009,
            sequence=3,
        )
        facts = normalize_channel(witness_scope, (expected, alternate_address, alternate_port))
        self.assertEqual(facts.total_initiations, 3)
        self.assertEqual(facts.expected_target_initiations, 1)
        self.assertEqual(facts.alternate_target_initiations, 2)

    def test_front_and_upstream_channels_are_independently_attributable(self) -> None:
        front = scope("W-front")
        upstream = scope("W-upstream")
        front_facts = normalize_channel(
            front,
            (synthetic_observation(front, attempt_id="a", source_port=30001),),
        )
        upstream_facts = normalize_channel(
            upstream,
            (synthetic_observation(upstream, attempt_id="a", source_port=31001),),
        )
        assessment = assess_initiation_integrity(front_facts, upstream_facts)
        self.assertEqual(assessment.classification, AssessmentClass.SATISFIED)

    def test_ambiguous_direction_fails_closed(self) -> None:
        witness_scope = scope()
        ambiguous = synthetic_observation(
            witness_scope,
            attempt_id="a",
            source_port=30001,
            packet_type=-1,
        )
        facts = normalize_channel(witness_scope, (ambiguous,))
        self.assertIn("ambiguous-packet-direction", facts.validity_problems)


class WitnessIntegrityTests(unittest.TestCase):
    def test_capture_integrity_positive_case_has_no_problems(self) -> None:
        self.assertEqual(
            capture_integrity_problems(
                assurance=CaptureAssurance(True, True, True, True),
                admitted=True,
                armed_interface_index=10,
                closing_interface_index=10,
                capture_drops=0,
            ),
            (),
        )

    def test_capture_integrity_failures_are_explicit(self) -> None:
        problems = capture_integrity_problems(
            assurance=CaptureAssurance(False, False, False, False),
            admitted=False,
            armed_interface_index=10,
            closing_interface_index=11,
            capture_drops=2,
        )
        self.assertIn("egress-coverage-unverified", problems)
        self.assertIn("directionality-unverified", problems)
        self.assertIn("offload-normalization-unverified", problems)
        self.assertIn("pre-syn-connect-gap-unclosed", problems)
        self.assertIn("attempt-never-admitted", problems)
        self.assertIn("interface-identity-drift", problems)
        self.assertIn("capture-drops=2", problems)

    def test_unknown_capture_drop_statistics_fail_closed(self) -> None:
        problems = capture_integrity_problems(
            assurance=CaptureAssurance(True, True, True, True),
            admitted=True,
            armed_interface_index=10,
            closing_interface_index=10,
            capture_drops=None,
        )
        self.assertEqual(problems, ("capture-drop-statistics-unknown",))

    def test_admit_before_arm_fails_closed(self) -> None:
        witness = LinuxSynWitness(
            interface_name="does-not-matter",
            scopes=(scope(),),
            assurance=CaptureAssurance(True, True, True, True),
        )
        with self.assertRaises(RuntimeError):
            witness.admit("attempt")

    def test_live_witness_prerequisite_error_is_precise_when_not_linux(self) -> None:
        witness = LinuxSynWitness(
            interface_name="lo",
            scopes=(scope(),),
            assurance=CaptureAssurance(True, True, True, True),
        )
        with mock.patch("acceptance.network_control.witness.sys.platform", "win32"):
            with self.assertRaises(WitnessPrerequisiteError):
                witness.arm("attempt")

    def test_raw_witness_bytes_are_content_address_verifiable(self) -> None:
        witness_scope = scope()
        observation = synthetic_observation(witness_scope, attempt_id="a", source_port=30001)
        frame = build_synthetic_syn_frame(
            source_address=observation.source_address,
            destination_address=observation.destination_address,
            source_port=observation.source_port,
            destination_port=observation.destination_port,
            sequence=observation.sequence,
        )
        raw = serialize_raw_witness(
            attempt_id="a",
            records=(RawFrameRecord("a", "synthetic0", 1, 1, 4, frame),),
            observations=(observation,),
            validity_problems=(),
            capture_packets=1,
            capture_drops=0,
        )
        document = json.loads(raw)
        self.assertEqual(document["rawFrames"][0]["frameSha256"], hashlib.sha256(frame).hexdigest())
        with tempfile.TemporaryDirectory() as temporary:
            store = ArtifactStore(Path(temporary))
            ref = store.put_bytes(raw, logical_role="transport-witness-raw")
            self.assertEqual(store.read_verified(ref), raw)


if __name__ == "__main__":
    unittest.main()

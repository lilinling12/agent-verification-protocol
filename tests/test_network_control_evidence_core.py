"""TEL-001 tests for sealed provider-neutral Network Control evidence inputs."""

from __future__ import annotations

import dataclasses
import tempfile
import unittest
from pathlib import Path

from acceptance.network_control.evidence_core import (
    ArtifactStore,
    AssessmentClass,
    AttemptFactory,
    EvidenceMaterializationError,
    EvidencePlan,
    ExchangeProgram,
    InitiationFacts,
    MaterializedEndpoint,
    assess_initiation_integrity,
)

_BASELINE = "c4269ca5166cb4a42b32c8fa5d0018a4e4b0200a"
_AEP_PATH = "rfcs/AEP-0012-network-control-resource-profile.md"


def endpoint(address: str, port: int, role: str) -> MaterializedEndpoint:
    return MaterializedEndpoint(
        family="ipv6" if ":" in address else "ipv4",
        address=address,
        port=port,
        role=role,
    )


def program() -> ExchangeProgram:
    return ExchangeProgram(
        program_id="tel001-exact-byte-v0.1",
        request_prefix=b"AVP-REQ\x00",
        request_suffix=b"\x00END",
        response_prefix=b"AVP-RESP\x00",
        response_suffix=b"\x00END",
    )


def plan(*, subject_port: int = 41001, fixture_port: int = 41002) -> EvidencePlan:
    return EvidencePlan(
        design_revision="TEL-001-v0.1",
        semantic_baseline_commit=_BASELINE,
        semantic_baseline_path=_AEP_PATH,
        run_id="run-001",
        path_id="selected-path",
        subject_destination=endpoint("127.0.0.1", subject_port, "subject-destination"),
        upstream_fixture=endpoint("127.0.0.1", fixture_port, "upstream-fixture"),
        exchange_program=program(),
        observation_budget_ns=1_000_000_000,
    )


class EvidencePlanTests(unittest.TestCase):
    def test_rejects_hostname_family_mismatch_and_invalid_budget(self) -> None:
        with self.assertRaises(EvidenceMaterializationError):
            MaterializedEndpoint(family="ipv4", address="localhost", port=1234, role="subject")
        with self.assertRaises(EvidenceMaterializationError):
            MaterializedEndpoint(family="ipv6", address="127.0.0.1", port=1234, role="subject")
        with self.assertRaises(EvidenceMaterializationError):
            dataclasses.replace(plan(), observation_budget_ns=0)

    def test_endpoint_text_formatting_is_not_semantic_identity(self) -> None:
        endpoint_value = MaterializedEndpoint(
            family="ipv6",
            address="2001:0db8:0:0:0:0:0:1",
            port=443,
            role="subject",
        )
        self.assertEqual(endpoint_value.address, "2001:db8::1")

    def test_plan_mutation_changes_exact_identity(self) -> None:
        first = plan().seal()
        second = dataclasses.replace(plan(), observation_budget_ns=2_000_000_000).seal()
        self.assertNotEqual(first.ref.sha256, second.ref.sha256)
        self.assertNotEqual(first.exact_bytes, second.exact_bytes)
        first.verify()
        second.verify()

    def test_artifact_store_detects_content_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ArtifactStore(Path(temporary))
            ref = store.put_bytes(b"evidence", logical_role="unit-test")
            self.assertEqual(store.read_verified(ref), b"evidence")
            store.path_for(ref).write_bytes(b"tampered")
            with self.assertRaises(EvidenceMaterializationError):
                store.read_verified(ref)


class AttemptMaterialTests(unittest.TestCase):
    def test_attempt_context_cannot_be_reused_and_challenges_are_distinct(self) -> None:
        factory = AttemptFactory(b"R" * 32)
        first = factory.issue(plan(), phase_id="baseline", ordinal=0)
        second = factory.issue(plan(), phase_id="pre-trigger", ordinal=1)
        self.assertNotEqual(first.attempt_id, second.attempt_id)
        self.assertNotEqual(first.challenge, second.challenge)
        self.assertNotEqual(first.request_bytes, second.request_bytes)
        with self.assertRaises(EvidenceMaterializationError):
            factory.issue(plan(), phase_id="baseline", ordinal=0)

    def test_future_challenge_is_not_materialized_until_issue(self) -> None:
        factory = AttemptFactory(b"S" * 32)
        first = factory.issue(plan(), phase_id="baseline", ordinal=0)
        second = factory.issue(plan(), phase_id="pre-trigger", ordinal=1)
        self.assertEqual(len(first.challenge), 32)
        self.assertNotEqual(first.challenge_sha256, second.challenge_sha256)


class ComparatorTests(unittest.TestCase):
    def test_provider_neutral_cardinality_pass_and_fail(self) -> None:
        good_front = InitiationFacts("W-front", 1, 1, 0, 1, 0)
        good_upstream = InitiationFacts("W-upstream", 1, 1, 0, 2, 1)
        satisfied = assess_initiation_integrity(good_front, good_upstream)
        self.assertEqual(satisfied.classification, AssessmentClass.SATISFIED)

        retry = dataclasses.replace(good_upstream, total_initiations=2, expected_target_initiations=2)
        failed = assess_initiation_integrity(good_front, retry)
        self.assertEqual(failed.classification, AssessmentClass.SEMANTIC_VIOLATION)
        self.assertIn("W-upstream", failed.primary_problem or "")

    def test_invalid_witness_precedes_semantic_cardinality_conclusion(self) -> None:
        invalid_front = InitiationFacts("W-front", 1, 1, 0, 1, 0, ("capture-drops=1",))
        upstream = InitiationFacts("W-upstream", 2, 2, 0, 2, 0)
        assessment = assess_initiation_integrity(invalid_front, upstream)
        self.assertEqual(assessment.classification, AssessmentClass.EVIDENCE_INVALID)
        self.assertIn("capture-drops=1", assessment.primary_problem or "")

    def test_cleanup_problem_does_not_overwrite_primary_failure(self) -> None:
        front = InitiationFacts("W-front", 2, 2, 0, 2, 0)
        upstream = InitiationFacts("W-upstream", 1, 1, 0, 1, 0)
        assessment = assess_initiation_integrity(front, upstream)
        primary = assessment.primary_problem
        updated = assessment.with_secondary_problem("cleanup:residual-resource")
        self.assertEqual(updated.primary_problem, primary)
        self.assertIn("cleanup:residual-resource", updated.secondary_problems)


if __name__ == "__main__":
    unittest.main()

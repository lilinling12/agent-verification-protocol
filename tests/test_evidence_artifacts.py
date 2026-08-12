from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from avp_ref.artifacts import (
    ArtifactIntegrityError,
    ArtifactRef,
    InMemoryArtifactStore,
    sha256_digest,
)
from avp_ref.evidence import EvidencePublisher, canonical_json_bytes
from avp_ref.models import Evidence
from avp_ref.reference import (
    correct_subject,
    reference_agent_system,
    reference_environment,
    reference_oracle_package,
    reference_scenario,
    reference_subject_adapter,
)
from avp_ref.runtime import ReferenceRuntime
from avp_ref.telemetry import OpenTelemetryBridge

ROOT = Path(__file__).resolve().parents[1]


def _evidence_schema() -> dict[str, object]:
    evidence = json.loads(
        (ROOT / "schemas/evidence.schema.json").read_text(encoding="utf-8")
    )
    artifact = json.loads(
        (ROOT / "schemas/artifact-ref.schema.json").read_text(encoding="utf-8")
    )
    evidence["$defs"] = {"artifactRef": artifact}
    evidence["properties"]["artifact"] = {"$ref": "#/$defs/artifactRef"}
    return evidence


def _episode(runtime: ReferenceRuntime):
    episode = runtime.create_episode(
        reference_scenario(),
        reference_agent_system("evidence-test"),
        reference_environment(),
        reference_subject_adapter(correct_subject),
        reference_oracle_package(),
    )
    runtime.provision(episode.episode_id)
    runtime.run_subject(episode.episode_id)
    runtime.verify(episode.episode_id)
    return episode


class EvidenceModelTest(unittest.TestCase):
    def test_schema_serialization_and_recursive_metadata_immutability(self) -> None:
        store = InMemoryArtifactStore()
        publisher = EvidencePublisher(store)
        evidence = publisher.publish_bytes(
            evidence_id="ev_test",
            evidence_type="state_projection",
            content=b"AVP",
            media_type="application/octet-stream",
            producer="oracle:test@1",
            redaction={
                "policy": {
                    "name": "pii-v2",
                    "fields": ["email"],
                }
            },
        )
        Draft202012Validator(_evidence_schema()).validate(evidence.to_dict())
        with self.assertRaises(TypeError):
            evidence.redaction["new"] = "value"  # type: ignore[index]
        nested = evidence.redaction["policy"]
        with self.assertRaises(TypeError):
            nested["name"] = "changed"  # type: ignore[index]

    def test_invalid_metadata_is_rejected_before_store_publication(self) -> None:
        store = InMemoryArtifactStore()
        publisher = EvidencePublisher(store)
        orphan_digest = sha256_digest(b"orphan")
        with self.assertRaises(ValueError):
            publisher.publish_bytes(
                evidence_id="ev_bad",
                evidence_type="state_projection",
                content=b"orphan",
                media_type="application/octet-stream",
                classification="not-a-classification",
            )
        self.assertFalse(store.contains(orphan_digest))

    def test_evidence_identity_is_distinct_from_artifact_identity(self) -> None:
        ref = ArtifactRef(
            sha256_digest(b"AVP"),
            3,
            "application/octet-stream",
        )
        first = Evidence("ev_one", "state_projection", ref)
        second = Evidence("ev_two", "state_projection", ref)
        self.assertNotEqual(first.evidence_id, second.evidence_id)
        self.assertEqual(first.artifact.digest, second.artifact.digest)


class RuntimeEvidenceTest(unittest.TestCase):
    def test_runtime_publishes_resolvable_oracle_evidence(self) -> None:
        runtime = ReferenceRuntime()
        episode = _episode(runtime)
        self.assertTrue(episode.evidence)
        for evidence in episode.evidence.values():
            content = runtime.read_evidence(
                episode.episode_id,
                evidence.evidence_id,
            )
            self.assertEqual(evidence.artifact.size, len(content))
            self.assertEqual(evidence.artifact.digest, sha256_digest(content))
            self.assertNotIn("data", evidence.to_dict())
        for result in episode.verification:
            self.assertTrue(result.evidence_ids)
            self.assertTrue(set(result.evidence_ids).issubset(episode.evidence))

    def test_oracle_projection_payload_is_canonical_json_artifact(self) -> None:
        runtime = ReferenceRuntime()
        episode = _episode(runtime)
        evidence = episode.evidence[f"ev_{episode.episode_id}_refunds"]
        content = runtime.read_evidence(
            episode.episode_id,
            evidence.evidence_id,
        )
        parsed = json.loads(content.decode("utf-8"))
        self.assertIsInstance(parsed, list)
        self.assertEqual(content, canonical_json_bytes(parsed))
        self.assertEqual("application/json", evidence.artifact.media_type)

    def test_integrity_failure_is_not_silently_accepted(self) -> None:
        store = InMemoryArtifactStore()
        runtime = ReferenceRuntime(artifact_store=store)
        episode = _episode(runtime)
        evidence = next(iter(episode.evidence.values()))
        store._objects[evidence.artifact.digest] = b"tampered"
        with self.assertRaises(ArtifactIntegrityError):
            runtime.read_evidence(episode.episode_id, evidence.evidence_id)

    def test_telemetry_payload_is_published_as_evidence_artifact(self) -> None:
        runtime = ReferenceRuntime(OpenTelemetryBridge())
        episode = _episode(runtime)
        evidence_id = f"ev_{episode.episode_id}_telemetry"
        evidence = episode.evidence[evidence_id]
        payload = json.loads(
            runtime.read_evidence(episode.episode_id, evidence_id).decode("utf-8")
        )
        self.assertEqual("telemetry_artifact", evidence.evidence_type)
        self.assertEqual(episode.episode_id, payload["episode_id"])
        self.assertNotIn("artifact_digest", payload)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from pathlib import Path

from avp_ref.relational import RestoreFidelity
from avp_ref.tck_adapter.reference_relational_harness import (
    InMemoryRelationalBackendHarness,
)
from avp_ref.tck_adapter.relational_fixture import RelationalParityFixtureLoader
from avp_ref.tck_adapter.relational_parity import RelationalParityVerifier

ROOT = Path(__file__).resolve().parents[1]


class RelationalParityVerifierTest(unittest.TestCase):
    """Exercise parity orchestration without requiring integration credentials."""

    def test_independent_harnesses_reproduce_locked_portable_evidence(self) -> None:
        fixture = RelationalParityFixtureLoader(ROOT).load()
        evidence = RelationalParityVerifier(
            fixture,
            {
                "reference-a": InMemoryRelationalBackendHarness(),
                "reference-b": InMemoryRelationalBackendHarness(),
            },
        ).verify()

        expected = fixture.expectations
        self.assertEqual(fixture.canonical_sha256, evidence.fixture_sha256)
        self.assertEqual(expected.manifest_digest, evidence.manifest_digest)
        self.assertEqual(
            expected.baseline_state_image_digest,
            evidence.baseline_state_image_digest,
        )
        self.assertEqual(
            expected.baseline_projection_digests,
            evidence.baseline_projection_digests,
        )
        self.assertEqual(
            expected.after_atomic_epoch_mutation_state_image_digest,
            evidence.after_atomic_state_image_digest,
        )
        self.assertEqual(
            expected.atomic_epoch_mutation_diff_digest,
            evidence.atomic_diff_digest,
        )
        self.assertIs(RestoreFidelity.STATE_EQUIVALENT, evidence.restore_fidelity)
        self.assertEqual(
            expected.baseline_state_image_digest,
            evidence.restored_state_image_digest,
        )
        self.assertEqual(
            expected.baseline_state_image_digest,
            evidence.reset_state_image_digest,
        )
        for _, epochs in evidence.atomic_observations:
            self.assertIn(epochs, fixture.allowed_consistency_epochs)

    def test_requires_distinct_backend_slots(self) -> None:
        fixture = RelationalParityFixtureLoader(ROOT).load()
        with self.assertRaisesRegex(ValueError, "at least two backends"):
            RelationalParityVerifier(
                fixture,
                {"reference": InMemoryRelationalBackendHarness()},
            )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
import unittest
from contextlib import ExitStack
from pathlib import Path

from avp_ref.relational import RestoreFidelity
from avp_ref.tck_adapter.mysql_relational_harness import MySQLRelationalBackendHarness
from avp_ref.tck_adapter.postgresql_relational_harness import (
    PostgreSQLRelationalBackendHarness,
)
from avp_ref.tck_adapter.relational_fixture import RelationalParityFixtureLoader
from avp_ref.tck_adapter.relational_parity import RelationalParityVerifier

ROOT = Path(__file__).resolve().parents[1]
_POSTGRESQL_DSN = os.environ.get("AVP_POSTGRESQL_DSN")
_MYSQL_DSN = os.environ.get("AVP_MYSQL_DSN")


@unittest.skipUnless(
    _POSTGRESQL_DSN and _MYSQL_DSN,
    "AVP_POSTGRESQL_DSN and AVP_MYSQL_DSN are required for parity integration",
)
class RelationalBackendParityTest(unittest.TestCase):
    """Prove portable equality using two real database products in one run."""

    def test_postgresql_mysql_canonical_parity(self) -> None:
        assert _POSTGRESQL_DSN is not None
        assert _MYSQL_DSN is not None
        fixture = RelationalParityFixtureLoader(ROOT).load()

        with ExitStack() as stack:
            postgresql = stack.enter_context(
                PostgreSQLRelationalBackendHarness(_POSTGRESQL_DSN)
            )
            mysql = stack.enter_context(MySQLRelationalBackendHarness(_MYSQL_DSN))
            evidence = RelationalParityVerifier(
                fixture,
                {
                    "mysql": mysql,
                    "postgresql": postgresql,
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

        observed_labels = {label for label, _ in evidence.atomic_observations}
        self.assertEqual({"mysql", "postgresql"}, observed_labels)
        for _, epochs in evidence.atomic_observations:
            self.assertIn(epochs, fixture.allowed_consistency_epochs)


if __name__ == "__main__":
    unittest.main()

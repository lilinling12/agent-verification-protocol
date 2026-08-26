from __future__ import annotations

import os
import unittest
from pathlib import Path

from avp_ref.canonical import digest
from avp_ref.tck_adapter import TCKRepository, TCKRunner
from avp_ref.tck_adapter.models import TCKCaseResult
from avp_ref.tck_adapter.postgresql_relational_harness import (
    PostgreSQLRelationalBackendHarness,
    PostgreSQLRelationalResource,
)
from avp_ref.tck_adapter.reference_relational_manifest import (
    ReferenceRelationalManifestTCKAdapter,
)
from avp_ref.tck_adapter.relational_backend_adapter import RelationalBackendTCKAdapter
from avp_ref.tck_adapter.relational_fixture import RelationalParityFixtureLoader
from avp_ref.tck_adapter.relational_harness import build_resource_spec

ROOT = Path(__file__).resolve().parents[1]
_DSN = os.environ.get("AVP_POSTGRESQL_DSN")


class _PostgreSQLRelationalComposite:
    """Integration-only ownership composition for the complete relational profile."""

    def __init__(self, backend: PostgreSQLRelationalBackendHarness) -> None:
        self._delegates = (
            RelationalBackendTCKAdapter(backend),
            ReferenceRelationalManifestTCKAdapter(),
        )
        self._owners = {
            case_id: delegate
            for delegate in self._delegates
            for case_id in delegate.supported_case_ids
        }

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return frozenset(self._owners)

    def evaluate(self, case) -> TCKCaseResult:
        case_id = case["metadata"]["id"]
        return self._owners[case_id].evaluate(case)


@unittest.skipUnless(_DSN, "AVP_POSTGRESQL_DSN is required for PostgreSQL integration")
class PostgreSQLRelationalAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        assert _DSN is not None
        self.backend = PostgreSQLRelationalBackendHarness(_DSN)
        self.fixture = RelationalParityFixtureLoader(ROOT).load()

    def tearDown(self) -> None:
        self.backend.close()

    def _provision_parity(self, instance_id: str = "postgresql-parity"):
        spec = build_resource_spec(
            self.backend,
            environment_id="env-postgresql-parity",
            resource_id="state",
            resource_instance_id=instance_id,
            manifest=self.fixture.manifest,
            baseline=self.fixture.baseline_mapping(),
            execution_input_identity="sha256:" + "b" * 64,
        )
        return self.backend.provision(spec)

    @staticmethod
    def _epochs(projection) -> tuple[str, str]:
        return tuple(
            relation["rows"][0]["values"]["epoch"]["value"]
            for relation in projection["relations"]
        )

    def test_complete_relational_profile_executes_against_postgresql(self) -> None:
        runner = TCKRunner(
            TCKRepository(ROOT),
            adapter=_PostgreSQLRelationalComposite(self.backend),
            implementation={"name": "postgresql-relational-adapter", "version": "0.1"},
        )

        result = runner.run(profile="avp-relational-state-v0.1")

        self.assertTrue(result.conformant)
        self.assertEqual(
            {"total": 11, "passed": 11, "failed": 0, "skipped": 0},
            result.report["summary"],
        )

    def test_shared_parity_fixture_recomputes_exact_evidence_from_postgresql(self) -> None:
        sut = self._provision_parity()
        self.assertIsInstance(sut, PostgreSQLRelationalResource)
        expected = self.fixture.expectations
        before = sut.state_image()

        self.assertEqual(expected.manifest_digest, sut.manifest_digest)
        self.assertEqual(expected.baseline_state_image_digest, before.digest)
        for projection in self.fixture.manifest.projections:
            self.assertEqual(
                expected.projection_digest(projection.projection_id),
                digest(sut.project(projection.projection_id)),
            )

        self.backend.fixture_control.replace_relations_atomically(
            sut,
            self.fixture.epoch_mutation_mapping(),
        )
        after = sut.state_image()
        observed_diff = sut.diff(before, after)

        self.assertEqual(
            expected.after_atomic_epoch_mutation_state_image_digest,
            after.digest,
        )
        self.assertEqual(expected.atomic_epoch_mutation_diff_digest, observed_diff.digest)
        self.assertEqual(
            [
                (item.relation_id, item.change, dict(item.key))
                for item in expected.atomic_epoch_mutation_diff_changes
            ],
            [
                (item.relation_id, item.change, dict(item.key))
                for item in observed_diff.changes
            ],
        )

    def test_atomic_projection_observes_only_shared_fixture_consistency_states(self) -> None:
        sut = self._provision_parity("postgresql-atomic-visibility")

        projection = self.backend.fixture_control.project_during_atomic_commit(
            sut,
            projection_id="consistency.pair",
            replacements=self.fixture.epoch_mutation_mapping(),
        )

        self.assertIn(self._epochs(projection), self.fixture.allowed_consistency_epochs)
        self.assertEqual(("2", "2"), self._epochs(sut.project("consistency.pair")))

    def test_postgresql_security_case_executes_through_database_backed_adapter(self) -> None:
        adapter = RelationalBackendTCKAdapter(self.backend)
        repository = TCKRepository(ROOT)
        loaded = repository.load_cases(
            "avp-relational-state-v0.1",
            selected_case_ids=("AVP-TCK-RELATIONAL-SECURITY-001",),
        )
        self.assertEqual(1, len(loaded))

        result = adapter.evaluate(loaded[0].document)

        self.assertEqual("PASS", result.status.value)


if __name__ == "__main__":
    unittest.main()

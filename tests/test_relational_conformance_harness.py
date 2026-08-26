from __future__ import annotations

import hashlib
import inspect
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from avp_ref.canonical import canonical_json, digest
from avp_ref.relational import RelationalCompatibilityError
from avp_ref.tck_adapter import TCKRepository, TCKRunner
from avp_ref.tck_adapter.models import TCKAdapterError, TCKCaseResult
from avp_ref.tck_adapter.reference_relational import RelationalConformanceTCKAdapter
from avp_ref.tck_adapter.reference_relational_harness import (
    InMemoryRelationalBackendHarness,
)
from avp_ref.tck_adapter.reference_relational_manifest import (
    ReferenceRelationalManifestTCKAdapter,
)
from avp_ref.tck_adapter.relational_fixture import RelationalParityFixtureLoader
from avp_ref.tck_adapter.relational_harness import (
    RelationalSUT,
    build_resource_spec,
)

ROOT = Path(__file__).resolve().parents[1]
_FIXTURE = ROOT / "conformance/fixtures/relational-state/v0.1/parity-fixture.json"
_LOCK = _FIXTURE.with_suffix(".sha256")
_FORBIDDEN_PORTABLE_NAMES = {
    "execute_sql",
    "query",
    "begin_transaction",
    "commit",
    "rollback",
    "inspect_catalog",
    "pg_snapshot",
    "pg_dump_restore",
    "admin_dsn",
    "credentials",
}
_FIXTURE_ONLY_NAMES = {
    "replace_relation",
    "replace_relations_atomically",
    "project_during_atomic_commit",
    "begin_held_mutation",
    "settle_held_mutation",
}


class _RelationalHarnessComposite:
    """Test-only composition of the two relational TCK case owners."""

    def __init__(self) -> None:
        backend = InMemoryRelationalBackendHarness()
        self._delegates = (
            RelationalConformanceTCKAdapter(backend),
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


class RelationalConformanceHarnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = InMemoryRelationalBackendHarness()
        self.fixture = RelationalParityFixtureLoader(ROOT).load()

    def _provision_parity(self, instance_id: str = "parity"):
        baseline = self.fixture.baseline_mapping()
        spec = build_resource_spec(
            self.backend,
            environment_id="env-parity",
            resource_id="state",
            resource_instance_id=instance_id,
            manifest=self.fixture.manifest,
            baseline=baseline,
            execution_input_identity="sha256:" + "b" * 64,
        )
        return self.backend.provision(spec)

    @staticmethod
    def _epochs(projection) -> tuple[str, str]:
        values: list[str] = []
        for relation in projection["relations"]:
            values.append(relation["rows"][0]["values"]["epoch"]["value"])
        return values[0], values[1]

    def test_full_relational_profile_executes_through_shared_harness(self) -> None:
        runner = TCKRunner(
            TCKRepository(ROOT),
            adapter=_RelationalHarnessComposite(),
            implementation={"name": "in-memory-relational-harness", "version": "0.1"},
        )

        result = runner.run(profile="avp-relational-state-v0.1")

        self.assertTrue(result.conformant)
        self.assertEqual(
            {"total": 11, "passed": 11, "failed": 0, "skipped": 0},
            result.report["summary"],
        )

    def test_fixture_bytes_are_canonical_and_locked_by_exact_sha256(self) -> None:
        payload = _FIXTURE.read_bytes()
        document = json.loads(payload.decode("utf-8"))
        expected = _LOCK.read_text(encoding="ascii").split()[0]

        self.assertEqual(canonical_json(document).encode("utf-8"), payload)
        self.assertEqual(expected, hashlib.sha256(payload).hexdigest())
        self.assertEqual(expected, self.fixture.canonical_sha256)

    def test_parity_fixture_covers_all_portable_scalar_kinds(self) -> None:
        relation = self.fixture.manifest.relation("parity.scalar_values")
        observed = {column.value_type.kind.value for column in relation.columns}

        self.assertEqual(
            {
                "boolean",
                "integer",
                "decimal",
                "text",
                "binary",
                "date",
                "time-local",
                "timestamp-local",
                "timestamp-instant",
                "uuid",
            },
            observed,
        )
        self.assertEqual(
            {
                "consistency.pair",
                "parity.all",
                "parity.keys-and-values",
            },
            {item.projection_id for item in self.fixture.manifest.projections},
        )

    def test_fixture_expected_evidence_is_recomputed_from_backend_observation(self) -> None:
        sut = self._provision_parity("expected-evidence")
        expected = self.fixture.expectations
        before = sut.state_image()

        self.assertEqual(expected.manifest_digest, sut.manifest_digest)
        self.assertEqual(expected.baseline_state_image_digest, before.digest)
        for projection in self.fixture.manifest.projections:
            observed = sut.project(projection.projection_id)
            self.assertEqual(
                expected.projection_digest(projection.projection_id),
                digest(observed),
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
            [(item.relation_id, item.change, dict(item.key)) for item in expected.atomic_epoch_mutation_diff_changes],
            [(item.relation_id, item.change, dict(item.key)) for item in observed_diff.changes],
        )

    def test_atomic_commit_projection_observes_only_allowed_consistency_state(self) -> None:
        sut = self._provision_parity("concurrency-seam")

        observed = self.backend.fixture_control.project_during_atomic_commit(
            sut,
            projection_id="consistency.pair",
            replacements=self.fixture.epoch_mutation_mapping(),
        )

        self.assertIn(self._epochs(observed), self.fixture.allowed_consistency_epochs)

    def test_fixture_materializes_and_reset_reestablishes_exact_baseline(self) -> None:
        sut = self._provision_parity()
        baseline = sut.state_image()
        control = self.backend.fixture_control

        control.replace_relations_atomically(
            sut,
            self.fixture.epoch_mutation_mapping(),
        )
        self.assertNotEqual(baseline.digest, sut.state_image().digest)

        reset = sut.reset()

        self.assertEqual(baseline.digest, reset.digest)
        self.assertEqual(sut.baseline_digest, reset.digest)

    def test_fixture_control_is_not_reachable_through_portable_sut_contract(self) -> None:
        portable_names = set(RelationalSUT.__dict__)
        fixture_names = set(type(self.backend.fixture_control).__dict__)

        self.assertTrue(_FIXTURE_ONLY_NAMES <= fixture_names)
        self.assertFalse(_FIXTURE_ONLY_NAMES & portable_names)
        self.assertFalse(_FORBIDDEN_PORTABLE_NAMES & portable_names)

    def test_harness_and_fixture_do_not_encode_backend_product_branches(self) -> None:
        fixture_text = _FIXTURE.read_text(encoding="utf-8").lower()
        source = inspect.getsource(RelationalConformanceTCKAdapter).lower()

        for product in ("postgres", "postgresql", "mysql", "innodb"):
            self.assertNotIn(product, fixture_text)
            self.assertNotIn(product, source)

    def test_fixture_loader_rejects_noncanonical_or_unlocked_bytes(self) -> None:
        fixture_payload = _FIXTURE.read_text(encoding="utf-8")
        lock_payload = _LOCK.read_text(encoding="ascii")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "conformance/fixtures/relational-state/v0.1"
            target.mkdir(parents=True)
            (target / "parity-fixture.json").write_text(
                fixture_payload + "\n",
                encoding="utf-8",
            )
            (target / "parity-fixture.sha256").write_text(
                lock_payload,
                encoding="ascii",
            )

            with self.assertRaisesRegex(TCKAdapterError, "not canonical JSON"):
                RelationalParityFixtureLoader(root).load()

    def test_backend_recomputes_fixture_identity_instead_of_trusting_input(self) -> None:
        baseline = self.fixture.baseline_mapping()
        spec = build_resource_spec(
            self.backend,
            environment_id="env-parity",
            resource_id="state",
            resource_instance_id="tampered",
            manifest=self.fixture.manifest,
            baseline=baseline,
            execution_input_identity="sha256:" + "b" * 64,
        )
        replacement = "0" if spec.manifest_artifact_digest[-1] != "0" else "1"
        bad_spec = replace(
            spec,
            manifest_artifact_digest=spec.manifest_artifact_digest[:-1] + replacement,
        )

        with self.assertRaises(RelationalCompatibilityError):
            self.backend.provision(bad_spec)


if __name__ == "__main__":
    unittest.main()

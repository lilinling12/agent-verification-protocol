from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver

from avp_ref.relational import (
    ColumnDefinition,
    ColumnType,
    InMemoryRelationalResource,
    ProjectionDefinition,
    ProjectionRelation,
    RelationDefinition,
    RelationalCompatibilityError,
    RelationalManifest,
    RelationalReferenceError,
    RelationalRow,
    RelationalSnapshot,
    RelationalValue,
    RestoreFidelity,
    ValueType,
)

ROOT = Path(__file__).resolve().parents[1]


class RelationalModelTest(unittest.TestCase):
    @staticmethod
    def _manifest() -> RelationalManifest:
        relation = RelationDefinition(
            "records",
            (
                ColumnDefinition("id", ColumnType(ValueType.INTEGER)),
                ColumnDefinition(
                    "amount",
                    ColumnType(ValueType.DECIMAL, precision=65, scale=2),
                ),
                ColumnDefinition("label", ColumnType(ValueType.TEXT)),
            ),
            ("id",),
        )
        return RelationalManifest(
            (relation,),
            (
                ProjectionDefinition(
                    "records.all",
                    (ProjectionRelation("records", ("id", "amount", "label")),),
                ),
            ),
        )

    @staticmethod
    def _row(identifier: str, amount: str, label: str) -> RelationalRow:
        return RelationalRow.from_mapping(
            {
                "id": RelationalValue(ValueType.INTEGER, identifier),
                "amount": RelationalValue(ValueType.DECIMAL, amount),
                "label": RelationalValue(ValueType.TEXT, label),
            }
        )

    def _resource(
        self,
        *,
        instance_id: str = "relational-model-test",
    ) -> InMemoryRelationalResource:
        manifest = self._manifest()
        baseline = {"records": (self._row("1", "1.00", "baseline"),)}
        manifest_digest, baseline_digest = InMemoryRelationalResource.identity_artifacts(
            manifest,
            baseline,
        )
        return InMemoryRelationalResource(
            environment_id="env-relational-test",
            resource_id="state",
            resource_instance_id=instance_id,
            manifest=manifest,
            manifest_artifact_digest=manifest_digest,
            baseline=baseline,
            baseline_artifact_digest=baseline_digest,
            execution_input_identity="sha256:" + "b" * 64,
        )

    def test_manifest_identity_is_derived_from_canonical_schema_shaped_bytes(self) -> None:
        manifest = self._manifest()
        document = manifest.as_document()
        schema = json.loads(
            (ROOT / "schemas" / "relational-state-manifest.schema.json").read_text(
                encoding="utf-8"
            )
        )
        Draft202012Validator(schema).validate(document)
        self.assertTrue(manifest.digest.startswith("sha256:"))

    def test_tampered_manifest_and_baseline_artifact_digests_fail_closed(self) -> None:
        manifest = self._manifest()
        baseline = {"records": (self._row("1", "1.00", "baseline"),)}
        manifest_digest, baseline_digest = InMemoryRelationalResource.identity_artifacts(
            manifest,
            baseline,
        )
        with self.assertRaises(RelationalCompatibilityError):
            InMemoryRelationalResource(
                environment_id="env-tampered-manifest",
                resource_id="state",
                resource_instance_id="tampered-manifest",
                manifest=manifest,
                manifest_artifact_digest="sha256:" + "a" * 64,
                baseline=baseline,
                baseline_artifact_digest=baseline_digest,
                execution_input_identity="sha256:" + "b" * 64,
            )
        with self.assertRaises(RelationalCompatibilityError):
            InMemoryRelationalResource(
                environment_id="env-tampered-baseline",
                resource_id="state",
                resource_instance_id="tampered-baseline",
                manifest=manifest,
                manifest_artifact_digest=manifest_digest,
                baseline=baseline,
                baseline_artifact_digest="sha256:" + "c" * 64,
                execution_input_identity="sha256:" + "b" * 64,
            )

    def test_state_image_serializes_only_manifest_logical_key_in_key_object(self) -> None:
        document = self._resource().state_image().as_document()
        relations = document["relations"]
        self.assertIsInstance(relations, list)
        row = relations[0]["rows"][0]

        self.assertEqual(
            {"id": {"type": "integer", "value": "1"}},
            row["key"],
        )
        self.assertEqual({"amount", "id", "label"}, set(row["values"]))

    def test_decimal_scale_and_negative_zero_fail_closed(self) -> None:
        for amount in ("1.0", "-0.00"):
            with self.subTest(amount=amount):
                manifest = self._manifest()
                baseline = {"records": (self._row("1", amount, "invalid"),)}
                with self.assertRaises(RelationalCompatibilityError):
                    InMemoryRelationalResource.identity_artifacts(manifest, baseline)

    def test_foreign_snapshot_fails_closed(self) -> None:
        resource = self._resource()
        snapshot = resource.snapshot()
        foreign = RelationalSnapshot(
            snapshot.snapshot_id,
            "env-other",
            snapshot.resource_id,
            snapshot.resource_instance_id,
            snapshot.state,
        )
        with self.assertRaises(RelationalReferenceError):
            resource.restore(foreign)

    def test_snapshot_from_released_same_id_instance_is_stale(self) -> None:
        resource = self._resource(instance_id="instance-before")
        snapshot = resource.snapshot()
        resource.release()

        replacement = self._resource(instance_id="instance-after")
        with self.assertRaises(RelationalReferenceError):
            replacement.restore(snapshot)

    def test_successful_restore_is_exactly_state_equivalent(self) -> None:
        resource = self._resource()
        snapshot = resource.snapshot()
        pending = resource.begin_subject_mutation(
            "records",
            (self._row("1", "2.00", "changed"),),
        )
        resource.settle_subject_mutation(pending, commit=True)

        self.assertNotEqual(snapshot.state.digest, resource.state_image().digest)
        fidelity = resource.restore(snapshot)

        self.assertIs(RestoreFidelity.STATE_EQUIVALENT, fidelity)
        self.assertEqual(snapshot.state.digest, resource.state_image().digest)

    def test_relational_diff_matches_normative_schema_and_identity_bindings(self) -> None:
        resource = self._resource()
        before = resource.state_image()
        pending = resource.begin_subject_mutation(
            "records",
            (self._row("1", "2.00", "changed"),),
        )
        resource.settle_subject_mutation(pending, commit=True)
        after = resource.state_image()

        document = resource.diff(before, after).as_document()
        diff_schema = json.loads(
            (ROOT / "schemas" / "relational-diff.schema.json").read_text(
                encoding="utf-8"
            )
        )
        value_schema = json.loads(
            (ROOT / "schemas" / "relational-value.schema.json").read_text(
                encoding="utf-8"
            )
        )
        resolver = RefResolver.from_schema(
            diff_schema,
            store={"relational-value.schema.json": value_schema},
        )
        Draft202012Validator(diff_schema, resolver=resolver).validate(document)

        self.assertEqual(resource.manifest_digest, document["manifestDigest"])
        self.assertEqual(before.digest, document["beforeDigest"])
        self.assertEqual(after.digest, document["afterDigest"])
        self.assertEqual({"kind": "full"}, document["scope"])
        change = document["changes"][0]
        self.assertEqual("UPDATE", change["change"])
        self.assertIn("before", change)
        self.assertIn("after", change)


if __name__ == "__main__":
    unittest.main()

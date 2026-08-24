from __future__ import annotations

import unittest

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

    def _resource(self) -> InMemoryRelationalResource:
        return InMemoryRelationalResource(
            environment_id="env-relational-test",
            resource_id="state",
            manifest=self._manifest(),
            manifest_digest="sha256:" + "a" * 64,
            baseline={"records": (self._row("1", "1.00", "baseline"),)},
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
                with self.assertRaises(RelationalCompatibilityError):
                    InMemoryRelationalResource(
                        environment_id="env-invalid-decimal",
                        resource_id="state",
                        manifest=self._manifest(),
                        manifest_digest="sha256:" + "a" * 64,
                        baseline={"records": (self._row("1", amount, "invalid"),)},
                        execution_input_identity="sha256:" + "b" * 64,
                    )

    def test_foreign_snapshot_fails_closed(self) -> None:
        resource = self._resource()
        snapshot = resource.snapshot()
        foreign = RelationalSnapshot(
            snapshot.snapshot_id,
            "env-other",
            snapshot.resource_id,
            snapshot.state,
        )
        with self.assertRaises(RelationalReferenceError):
            resource.restore(foreign)

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


if __name__ == "__main__":
    unittest.main()

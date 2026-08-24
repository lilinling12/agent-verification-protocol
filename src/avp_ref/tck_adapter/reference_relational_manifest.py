"""Execution adapter for AVP Relational Manifest semantic integrity."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from avp_ref.relational import (
    ColumnDefinition,
    ColumnType,
    InMemoryRelationalResource,
    ProjectionDefinition,
    ProjectionRelation,
    RelationDefinition,
    RelationalCompatibilityError,
    RelationalManifest,
    RelationalRow,
    RelationalValue,
    ValueType,
)
from avp_ref.relational_manifest import validate_manifest_integrity

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


class ReferenceRelationalManifestTCKAdapter:
    """Execute AVP-RELATIONAL-017 using valid and ambiguous Manifest graphs."""

    CASE_ID = "AVP-TCK-RELATIONAL-MANIFEST-INTEGRITY-001"

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return frozenset({self.CASE_ID})

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        metadata = case.get("metadata")
        if not isinstance(metadata, Mapping) or metadata.get("id") != self.CASE_ID:
            raise TCKAdapterError("unexpected Relational Manifest integrity case")
        if case.get("profile") != "avp-relational-state-v0.1":
            raise TCKAdapterError("unexpected Relational Manifest integrity profile")

        vector = case.get("vector")
        if not isinstance(vector, Mapping):
            raise TCKAdapterError("Manifest integrity vector must be an object")
        controls = vector.get("invalidControls")
        if not isinstance(controls, list) or not all(
            isinstance(item, str) for item in controls
        ):
            raise TCKAdapterError(
                "Manifest integrity invalidControls must be a string list"
            )

        validate_manifest_integrity(self._valid_manifest())
        builders = self._invalid_builders()
        if set(controls) != set(builders):
            raise TCKAdapterError(
                "Manifest integrity case/control implementation mismatch"
            )

        rejected: list[str] = []
        for control in controls:
            try:
                manifest = builders[control]()
                validate_manifest_integrity(manifest)
            except RelationalCompatibilityError:
                rejected.append(control)

        admission_rejected = self._invalid_resource_admission_rejected()
        passed = len(rejected) == len(controls) and admission_rejected
        detail = (
            "valid Manifest accepted, every duplicate/dangling/key-incomplete control rejected, and invalid graph rejected at resource admission"
            if passed
            else "Manifest integrity semantic or resource-admission control failed"
        )
        return TCKCaseResult(
            self.CASE_ID,
            TCKStatus.PASS if passed else TCKStatus.FAIL,
            detail,
        )

    @staticmethod
    def _columns() -> tuple[ColumnDefinition, ...]:
        return (
            ColumnDefinition("id", ColumnType(ValueType.INTEGER)),
            ColumnDefinition("value", ColumnType(ValueType.TEXT)),
        )

    @classmethod
    def _relation(cls, relation_id: str = "records") -> RelationDefinition:
        return RelationDefinition(relation_id, cls._columns(), ("id",))

    @classmethod
    def _valid_manifest(cls) -> RelationalManifest:
        return RelationalManifest(
            (cls._relation(),),
            (
                ProjectionDefinition(
                    "records.all",
                    (ProjectionRelation("records", ("id", "value")),),
                ),
            ),
        )

    @classmethod
    def _invalid_resource_admission_rejected(cls) -> bool:
        manifest = cls._duplicate_relation_id()
        row = RelationalRow.from_mapping(
            {
                "id": RelationalValue(ValueType.INTEGER, "1"),
                "value": RelationalValue(ValueType.TEXT, "baseline"),
            }
        )
        try:
            InMemoryRelationalResource(
                environment_id="env-invalid-manifest",
                resource_id="state",
                resource_instance_id="invalid-manifest-instance",
                manifest=manifest,
                manifest_artifact_digest="sha256:" + "a" * 64,
                baseline={"records": (row,)},
                baseline_artifact_digest="sha256:" + "b" * 64,
                execution_input_identity="sha256:" + "c" * 64,
            )
        except RelationalCompatibilityError:
            return True
        return False

    @classmethod
    def _invalid_builders(cls) -> dict[str, Callable[[], RelationalManifest]]:
        return {
            "duplicate-relation-id": cls._duplicate_relation_id,
            "duplicate-column-id": cls._duplicate_column_id,
            "duplicate-row-key-column": cls._duplicate_row_key,
            "duplicate-projection-id": cls._duplicate_projection_id,
            "duplicate-projection-relation": cls._duplicate_projection_relation,
            "unknown-projection-relation": cls._unknown_projection_relation,
            "unknown-projection-column": cls._unknown_projection_column,
            "missing-projection-row-key": cls._missing_projection_row_key,
        }

    @classmethod
    def _duplicate_relation_id(cls) -> RelationalManifest:
        return RelationalManifest((cls._relation(), cls._relation()), ())

    @staticmethod
    def _duplicate_column_id() -> RelationalManifest:
        relation = RelationDefinition(
            "records",
            (
                ColumnDefinition("id", ColumnType(ValueType.INTEGER)),
                ColumnDefinition("id", ColumnType(ValueType.TEXT)),
            ),
            ("id",),
        )
        return RelationalManifest((relation,), ())

    @classmethod
    def _duplicate_row_key(cls) -> RelationalManifest:
        relation = RelationDefinition("records", cls._columns(), ("id", "id"))
        return RelationalManifest((relation,), ())

    @classmethod
    def _duplicate_projection_id(cls) -> RelationalManifest:
        projection = ProjectionDefinition(
            "records.all",
            (ProjectionRelation("records", ("id", "value")),),
        )
        return RelationalManifest((cls._relation(),), (projection, projection))

    @classmethod
    def _duplicate_projection_relation(cls) -> RelationalManifest:
        selected = ProjectionRelation("records", ("id", "value"))
        projection = ProjectionDefinition("records.all", (selected, selected))
        return RelationalManifest((cls._relation(),), (projection,))

    @classmethod
    def _unknown_projection_relation(cls) -> RelationalManifest:
        projection = ProjectionDefinition(
            "records.all",
            (ProjectionRelation("missing", ("id",)),),
        )
        return RelationalManifest((cls._relation(),), (projection,))

    @classmethod
    def _unknown_projection_column(cls) -> RelationalManifest:
        projection = ProjectionDefinition(
            "records.all",
            (ProjectionRelation("records", ("id", "missing")),),
        )
        return RelationalManifest((cls._relation(),), (projection,))

    @classmethod
    def _missing_projection_row_key(cls) -> RelationalManifest:
        projection = ProjectionDefinition(
            "records.all",
            (ProjectionRelation("records", ("value",)),),
        )
        return RelationalManifest((cls._relation(),), (projection,))

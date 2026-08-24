"""Semantic RelationalStateManifest integrity checks.

JSON Schema owns serialized shape. This module demonstrates the cross-reference
constraints of AVP-RELATIONAL-017 that require semantic graph validation. The
normative definition remains ``spec/relational/manifest-integrity-contract.md``.
"""

from __future__ import annotations

from .relational import RelationalCompatibilityError, RelationalManifest


def validate_manifest_integrity(manifest: RelationalManifest) -> None:
    """Reject ambiguous or dangling logical Manifest references fail closed."""

    relation_ids = [relation.relation_id for relation in manifest.relations]
    if len(relation_ids) != len(set(relation_ids)):
        raise RelationalCompatibilityError("Manifest relationId values must be unique")

    relation_by_id = {relation.relation_id: relation for relation in manifest.relations}

    projection_ids = [projection.projection_id for projection in manifest.projections]
    if len(projection_ids) != len(set(projection_ids)):
        raise RelationalCompatibilityError("Manifest projectionId values must be unique")

    for projection in manifest.projections:
        selected_relation_ids = [selected.relation_id for selected in projection.relations]
        if len(selected_relation_ids) != len(set(selected_relation_ids)):
            raise RelationalCompatibilityError(
                f"projection {projection.projection_id} selects a relation more than once"
            )

        for selected in projection.relations:
            relation = relation_by_id.get(selected.relation_id)
            if relation is None:
                raise RelationalCompatibilityError(
                    f"projection {projection.projection_id} references unknown relation {selected.relation_id}"
                )

            selected_columns = list(selected.columns)
            if len(selected_columns) != len(set(selected_columns)):
                raise RelationalCompatibilityError(
                    f"projection {projection.projection_id} contains duplicate column references"
                )

            declared_columns = {column.column_id for column in relation.columns}
            unknown_columns = set(selected_columns) - declared_columns
            if unknown_columns:
                raise RelationalCompatibilityError(
                    f"projection {projection.projection_id} references unknown columns: {sorted(unknown_columns)}"
                )

            missing_key_columns = set(relation.row_key) - set(selected_columns)
            if missing_key_columns:
                raise RelationalCompatibilityError(
                    f"projection {projection.projection_id} omits logical key columns: {sorted(missing_key_columns)}"
                )

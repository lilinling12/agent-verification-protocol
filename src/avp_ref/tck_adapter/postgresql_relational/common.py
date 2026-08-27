"""PostgreSQL relational implementation helpers with no backend lifecycle state.

These functions are private implementation mechanics. They mirror already
adopted portable behavior but do not define or extend AVP protocol semantics.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from avp_ref.canonical import canonical_json
from avp_ref.relational import (
    DiffChange,
    RelationDefinition,
    RelationalCompatibilityError,
    RelationalDiff,
    RelationalManifest,
    RelationalRow,
    StateImage,
)

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def require_digest(value: str, context: str) -> None:
    """Reject implementation identity inputs outside canonical SHA-256 form."""

    if not _DIGEST_RE.fullmatch(value):
        raise RelationalCompatibilityError(
            f"{context} must be a canonical sha256 digest"
        )


def projection_document(
    manifest: RelationalManifest,
    state: Mapping[str, tuple[RelationalRow, ...]],
    projection_id: str,
) -> dict[str, object]:
    """Materialize the adopted canonical projection document from logical state."""

    projection = manifest.projection(projection_id)
    relations: list[dict[str, object]] = []
    for selected in sorted(projection.relations, key=lambda item: item.relation_id):
        relation = manifest.relation(selected.relation_id)
        selected_columns = set(selected.columns)
        rows: list[dict[str, object]] = []
        for row in state[relation.relation_id]:
            values = row.value_map()
            rows.append(
                {
                    "key": {
                        column_id: values[column_id].as_document()
                        for column_id in sorted(relation.row_key)
                    },
                    "values": {
                        column_id: values[column_id].as_document()
                        for column_id in sorted(selected_columns)
                    },
                }
            )
        relations.append({"relationId": relation.relation_id, "rows": rows})
    return {
        "apiVersion": "avp.relational/v0.1",
        "kind": "RelationalProjection",
        "manifestDigest": manifest.digest,
        "projectionId": projection_id,
        "relations": relations,
    }


def relational_diff(
    *,
    manifest: RelationalManifest,
    manifest_digest: str,
    before: StateImage,
    after: StateImage,
) -> RelationalDiff:
    """Compute deterministic logical row changes for two complete StateImages."""

    if (
        before.manifest_digest != manifest_digest
        or after.manifest_digest != manifest_digest
    ):
        raise RelationalCompatibilityError(
            "cross-Manifest comparison is not relational row diff"
        )

    before_map = dict(before.relations)
    after_map = dict(after.relations)
    expected = {relation.relation_id for relation in manifest.relations}
    if set(before_map) != expected or set(after_map) != expected:
        raise RelationalCompatibilityError(
            "diff states do not cover the full Manifest surface"
        )

    changes: list[DiffChange] = []
    for relation in sorted(manifest.relations, key=lambda item: item.relation_id):
        changes.extend(
            _relation_changes(
                relation,
                before_map[relation.relation_id],
                after_map[relation.relation_id],
            )
        )
    return RelationalDiff(
        manifest_digest=manifest_digest,
        before_digest=before.digest,
        after_digest=after.digest,
        changes=tuple(changes),
    )


def _relation_changes(
    relation: RelationDefinition,
    before_rows: tuple[RelationalRow, ...],
    after_rows: tuple[RelationalRow, ...],
) -> list[DiffChange]:
    old_rows = {_canonical_key_bytes(row): row for row in before_rows}
    new_rows = {_canonical_key_bytes(row): row for row in after_rows}
    changes: list[DiffChange] = []

    for key_bytes in sorted(old_rows.keys() | new_rows.keys()):
        old = old_rows.get(key_bytes)
        new = new_rows.get(key_bytes)
        source = old if old is not None else new
        assert source is not None
        key_values = source.value_map()
        key = tuple(
            (column_id, key_values[column_id])
            for column_id in sorted(relation.row_key)
        )
        if old is None:
            assert new is not None
            changes.append(
                DiffChange(
                    relation.relation_id,
                    "INSERT",
                    key,
                    after=new.values,
                )
            )
        elif new is None:
            changes.append(
                DiffChange(
                    relation.relation_id,
                    "DELETE",
                    key,
                    before=old.values,
                )
            )
        elif old.values != new.values:
            changes.append(
                DiffChange(
                    relation.relation_id,
                    "UPDATE",
                    key,
                    before=old.values,
                    after=new.values,
                )
            )
    return changes


def _canonical_key_bytes(row: RelationalRow) -> bytes:
    return canonical_json(row.key_document()).encode("utf-8")

"""Fail-closed loader for the shared Relational State parity fixture."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from avp_ref.canonical import canonical_json
from avp_ref.relational import (
    ColumnDefinition,
    ColumnType,
    ProjectionDefinition,
    ProjectionRelation,
    RelationDefinition,
    RelationalCompatibilityError,
    RelationalManifest,
    RelationalRow,
    RelationalValue,
    ValueType,
)

from .models import TCKAdapterError

_FIXTURE_RELATIVE_PATH = Path(
    "conformance/fixtures/relational-state/v0.1/parity-fixture.json"
)
_LOCK_RELATIVE_PATH = _FIXTURE_RELATIVE_PATH.with_suffix(".sha256")
_FORMAT_VERSION = "avp-relational-parity-fixture/v0.1"
_PROFILE = "avp-relational-state-v0.1"


@dataclass(frozen=True, slots=True)
class RelationalParityFixture:
    """Typed immutable view of language-neutral backend parity material."""

    manifest: RelationalManifest
    baseline: tuple[tuple[str, tuple[RelationalRow, ...]], ...]
    atomic_epoch_mutation: tuple[tuple[str, tuple[RelationalRow, ...]], ...]
    allowed_consistency_epochs: tuple[tuple[str, str], ...]
    drift_controls: tuple[str, ...]
    canonical_sha256: str

    def baseline_mapping(self) -> dict[str, tuple[RelationalRow, ...]]:
        return dict(self.baseline)

    def epoch_mutation_mapping(self) -> dict[str, tuple[RelationalRow, ...]]:
        return dict(self.atomic_epoch_mutation)


class RelationalParityFixtureLoader:
    """Load exact canonical fixture bytes and reject identity or semantic drift."""

    def __init__(self, repository_root: Path) -> None:
        self._repository_root = repository_root.resolve()

    def load(self) -> RelationalParityFixture:
        fixture_path = self._repository_root / _FIXTURE_RELATIVE_PATH
        lock_path = self._repository_root / _LOCK_RELATIVE_PATH
        try:
            payload = fixture_path.read_bytes()
            lock_text = lock_path.read_text(encoding="ascii")
        except OSError as exc:
            raise TCKAdapterError(f"cannot read relational parity fixture: {exc}") from exc

        try:
            document = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TCKAdapterError("relational parity fixture is not valid UTF-8 JSON") from exc
        root = self._mapping(document, "fixture root")

        # Requiring repository bytes to already be canonical prevents a backend
        # test from silently consuming semantically equal but identity-different
        # fixture material.
        canonical_bytes = canonical_json(root).encode("utf-8")
        if payload != canonical_bytes:
            raise TCKAdapterError("relational parity fixture bytes are not canonical JSON")

        actual_sha = hashlib.sha256(payload).hexdigest()
        expected_sha = self._parse_lock(lock_text)
        if actual_sha != expected_sha:
            raise TCKAdapterError("relational parity fixture SHA-256 lock mismatch")

        if root.get("formatVersion") != _FORMAT_VERSION:
            raise TCKAdapterError("unexpected relational parity fixture formatVersion")
        if root.get("profile") != _PROFILE or root.get("revision") != "0.1":
            raise TCKAdapterError("unexpected relational parity fixture profile identity")

        manifest = self._manifest(self._mapping(root.get("manifest"), "manifest"))
        baseline = self._state(
            manifest,
            self._mapping(root.get("baseline"), "baseline"),
            "baseline",
        )
        controls = self._mapping(root.get("controls"), "controls")
        atomic = self._mapping(
            self._mapping(controls.get("atomicEpochMutation"), "atomicEpochMutation").get(
                "relations"
            ),
            "atomicEpochMutation.relations",
        )
        epoch_mutation = self._partial_state(manifest, atomic, "atomicEpochMutation")

        allowed_raw = controls.get("allowedConsistencyEpochs")
        if not isinstance(allowed_raw, list) or not allowed_raw:
            raise TCKAdapterError("allowedConsistencyEpochs must be a non-empty list")
        allowed: list[tuple[str, str]] = []
        for item in allowed_raw:
            if (
                not isinstance(item, list)
                or len(item) != 2
                or not all(isinstance(value, str) for value in item)
            ):
                raise TCKAdapterError("allowedConsistencyEpochs entries must be string pairs")
            allowed.append((item[0], item[1]))
        if len(allowed) != len(set(allowed)):
            raise TCKAdapterError("allowedConsistencyEpochs contains duplicates")

        drift = self._string_tuple(controls.get("driftControls"), "driftControls")
        if len(drift) != len(set(drift)):
            raise TCKAdapterError("driftControls contains duplicates")

        return RelationalParityFixture(
            manifest=manifest,
            baseline=tuple(sorted(baseline.items())),
            atomic_epoch_mutation=tuple(sorted(epoch_mutation.items())),
            allowed_consistency_epochs=tuple(allowed),
            drift_controls=drift,
            canonical_sha256=actual_sha,
        )

    @staticmethod
    def _parse_lock(text: str) -> str:
        parts = text.strip().split()
        if len(parts) != 2 or parts[1] != "parity-fixture.json":
            raise TCKAdapterError("invalid relational parity fixture lock file")
        digest = parts[0]
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise TCKAdapterError("invalid relational parity fixture SHA-256")
        return digest

    def _manifest(self, document: Mapping[str, Any]) -> RelationalManifest:
        relations_raw = document.get("relations")
        projections_raw = document.get("projections")
        if not isinstance(relations_raw, list) or not relations_raw:
            raise TCKAdapterError("fixture manifest relations must be a non-empty list")
        if not isinstance(projections_raw, list):
            raise TCKAdapterError("fixture manifest projections must be a list")

        relations: list[RelationDefinition] = []
        for raw in relations_raw:
            item = self._mapping(raw, "manifest relation")
            columns_raw = item.get("columns")
            if not isinstance(columns_raw, list) or not columns_raw:
                raise TCKAdapterError("fixture relation columns must be non-empty")
            columns = tuple(
                self._column(self._mapping(value, "manifest column"))
                for value in columns_raw
            )
            relations.append(
                RelationDefinition(
                    self._string(item.get("relationId"), "relationId"),
                    columns,
                    self._string_tuple(item.get("rowKey"), "rowKey"),
                )
            )

        projections: list[ProjectionDefinition] = []
        for raw in projections_raw:
            item = self._mapping(raw, "manifest projection")
            selected_raw = item.get("relations")
            if not isinstance(selected_raw, list) or not selected_raw:
                raise TCKAdapterError("fixture projection relations must be non-empty")
            projections.append(
                ProjectionDefinition(
                    self._string(item.get("projectionId"), "projectionId"),
                    tuple(
                        ProjectionRelation(
                            self._string(
                                selected.get("relationId"),
                                "projection relationId",
                            ),
                            self._string_tuple(
                                selected.get("columns"),
                                "projection columns",
                            ),
                        )
                        for selected in (
                            self._mapping(value, "projection relation")
                            for value in selected_raw
                        )
                    ),
                )
            )

        manifest = RelationalManifest(tuple(relations), tuple(projections))
        try:
            manifest.validate_integrity()
        except RelationalCompatibilityError as exc:
            raise TCKAdapterError(f"invalid relational parity Manifest: {exc}") from exc
        return manifest

    def _column(self, document: Mapping[str, Any]) -> ColumnDefinition:
        value_type = self._mapping(document.get("valueType"), "column valueType")
        try:
            kind = ValueType(self._string(value_type.get("type"), "value type"))
            if kind is ValueType.DECIMAL:
                column_type = ColumnType(
                    kind,
                    precision=self._integer(value_type.get("precision"), "precision"),
                    scale=self._integer(value_type.get("scale"), "scale"),
                )
            elif kind in {
                ValueType.TIME_LOCAL,
                ValueType.TIMESTAMP_LOCAL,
                ValueType.TIMESTAMP_INSTANT,
            }:
                column_type = ColumnType(
                    kind,
                    fractional_precision=self._integer(
                        value_type.get("fractionalPrecision"),
                        "fractionalPrecision",
                    ),
                )
            else:
                column_type = ColumnType(kind)
        except (ValueError, RelationalCompatibilityError) as exc:
            raise TCKAdapterError(f"invalid fixture column type: {exc}") from exc

        nullable = document.get("nullable")
        if not isinstance(nullable, bool):
            raise TCKAdapterError("fixture column nullable must be boolean")
        return ColumnDefinition(
            self._string(document.get("columnId"), "columnId"),
            column_type,
            nullable=nullable,
        )

    def _state(
        self,
        manifest: RelationalManifest,
        document: Mapping[str, Any],
        context: str,
    ) -> dict[str, tuple[RelationalRow, ...]]:
        expected = {relation.relation_id for relation in manifest.relations}
        if set(document) != expected:
            raise TCKAdapterError(f"{context} must cover exactly the Manifest relations")
        return self._partial_state(manifest, document, context)

    def _partial_state(
        self,
        manifest: RelationalManifest,
        document: Mapping[str, Any],
        context: str,
    ) -> dict[str, tuple[RelationalRow, ...]]:
        result: dict[str, tuple[RelationalRow, ...]] = {}
        for relation_id, rows_raw in document.items():
            try:
                relation = manifest.relation(relation_id)
            except RelationalCompatibilityError as exc:
                raise TCKAdapterError(f"{context} references unknown relation") from exc
            if not isinstance(rows_raw, list):
                raise TCKAdapterError(f"{context}.{relation_id} must be a row list")
            rows: list[RelationalRow] = []
            for raw in rows_raw:
                row = self._mapping(raw, f"{context}.{relation_id} row")
                values = {
                    column_id: self._value(self._mapping(value, "typed value"))
                    for column_id, value in row.items()
                }
                rows.append(RelationalRow.from_mapping(values))
            result[relation_id] = tuple(rows)

        # Reuse the reference model only as implementation validation; the
        # resulting canonical identity is still independently recomputed by the
        # selected backend harness during provisioning.
        try:
            full = dict(self._empty_state(manifest))
            full.update(result)
            from avp_ref.relational import InMemoryRelationalResource

            InMemoryRelationalResource._validate_state_for_manifest(manifest, full)
        except RelationalCompatibilityError as exc:
            if set(result) == {relation.relation_id for relation in manifest.relations}:
                raise TCKAdapterError(f"invalid {context}: {exc}") from exc
        return result

    @staticmethod
    def _empty_state(manifest: RelationalManifest) -> dict[str, tuple[RelationalRow, ...]]:
        return {relation.relation_id: () for relation in manifest.relations}

    def _value(self, document: Mapping[str, Any]) -> RelationalValue:
        try:
            kind = ValueType(self._string(document.get("type"), "typed value type"))
        except ValueError as exc:
            raise TCKAdapterError("unsupported fixture typed value") from exc
        value = document.get("value")
        if value is not None and not isinstance(value, (str, bool)):
            raise TCKAdapterError("fixture typed value must be string, boolean, or null")
        return RelationalValue(kind, value)

    @staticmethod
    def _mapping(value: Any, context: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise TCKAdapterError(f"relational parity {context} must be an object")
        return value

    @staticmethod
    def _string(value: Any, context: str) -> str:
        if not isinstance(value, str) or not value:
            raise TCKAdapterError(f"relational parity {context} must be a non-empty string")
        return value

    @staticmethod
    def _integer(value: Any, context: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TCKAdapterError(f"relational parity {context} must be an integer")
        return value

    @staticmethod
    def _string_tuple(value: Any, context: str) -> tuple[str, ...]:
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item for item in value
        ):
            raise TCKAdapterError(f"relational parity {context} must be a string list")
        return tuple(value)

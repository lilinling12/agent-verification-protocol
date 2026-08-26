"""PostgreSQL implementation of the adopted relational conformance harness.

This module is implementation evidence, not protocol authority. PostgreSQL SQL,
roles, schemas, transaction handles, and MVCC coordination remain private to
this backend. Portable semantics continue to come from the Relational State
specification, schemas, and language-neutral TCK.
"""

from __future__ import annotations

import base64
import hashlib
import importlib
import re
import threading
import uuid
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any

from avp_ref.canonical import canonical_json
from avp_ref.relational import (
    ColumnDefinition,
    DiffChange,
    InMemoryRelationalResource,
    RelationDefinition,
    RelationalCompatibilityError,
    RelationalDiff,
    RelationalError,
    RelationalLifecycleError,
    RelationalManifest,
    RelationalReferenceError,
    RelationalRow,
    RelationalSnapshot,
    RelationalValue,
    RelationalVisibilityError,
    RestoreFidelity,
    StateImage,
    ValueType,
)

from .relational_harness import (
    NegativeControl,
    RelationalBackendHarness,
    RelationalFixtureControl,
    RelationalResourceSpec,
    RelationalSUT,
)

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _driver() -> tuple[Any, Any]:
    """Load the optional PostgreSQL driver only when this backend is used."""

    try:
        psycopg = importlib.import_module("psycopg")
        sql = importlib.import_module("psycopg.sql")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PostgreSQL support requires the optional 'postgresql' dependency"
        ) from exc
    return psycopg, sql


def _require_digest(value: str, context: str) -> None:
    if not _DIGEST_RE.fullmatch(value):
        raise RelationalCompatibilityError(
            f"{context} must be a canonical sha256 digest"
        )


def _canonical_key_bytes(row: RelationalRow) -> bytes:
    return canonical_json(row.key_document()).encode("utf-8")


def _fractional_time(value: time, precision: int) -> str:
    base = value.strftime("%H:%M:%S")
    if precision == 0:
        return base
    return f"{base}.{value.microsecond:06d}"[: len(base) + 1 + precision]


def _fractional_timestamp(value: datetime, precision: int, *, instant: bool) -> str:
    if instant:
        if value.tzinfo is None:
            raise RelationalCompatibilityError(
                "PostgreSQL returned an unzoned timestamp for timestamp-instant"
            )
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    elif value.tzinfo is not None:
        raise RelationalCompatibilityError(
            "PostgreSQL returned a zoned timestamp for timestamp-local"
        )
    base = value.strftime("%Y-%m-%dT%H:%M:%S")
    if precision:
        base = f"{base}.{value.microsecond:06d}"[: len(base) + 1 + precision]
    return base + ("Z" if instant else "")


class PostgreSQLRelationalResource(RelationalSUT):
    """Relational SUT whose authoritative state is stored in PostgreSQL."""

    def __init__(
        self,
        *,
        dsn: str,
        subject_role: str,
        evaluator_role: str,
        spec: RelationalResourceSpec,
    ) -> None:
        manifest_digest, baseline_digest = (
            InMemoryRelationalResource.identity_artifacts(
                spec.manifest,
                spec.baseline_mapping(),
            )
        )
        if manifest_digest != spec.manifest_artifact_digest:
            raise RelationalCompatibilityError(
                "Manifest Artifact digest does not match canonical Manifest bytes"
            )
        if baseline_digest != spec.baseline_artifact_digest:
            raise RelationalCompatibilityError(
                "baseline Artifact digest does not match canonical StateImage bytes"
            )
        _require_digest(spec.execution_input_identity, "execution input identity")
        if not spec.resource_instance_id:
            raise RelationalCompatibilityError(
                "resource instance identity must not be empty"
            )

        self.environment_id = spec.environment_id
        self.resource_id = spec.resource_id
        self.resource_instance_id = spec.resource_instance_id
        self.manifest = spec.manifest
        self.manifest_digest = manifest_digest
        self.baseline_digest = baseline_digest
        self.execution_input_identity = spec.execution_input_identity

        self._dsn = dsn
        self._subject_role = subject_role
        self._evaluator_role = evaluator_role
        self._bound_execution_identity = spec.execution_input_identity
        self._private_columns = spec.evaluator_private_columns
        self._baseline = InMemoryRelationalResource._validate_state_for_manifest(
            spec.manifest,
            spec.baseline_mapping(),
        )
        self._logical_binding_valid = True
        self._quiescing = False
        self._released = False
        self._snapshot_sequence = 0
        self._held_labels: set[str] = set()
        self._held_connections: dict[str, Any] = {}

        suffix = uuid.uuid4().hex[:20]
        self._schema = f"avp_r_{suffix}"
        self._tables = {
            relation.relation_id: f"r_{index:04d}"
            for index, relation in enumerate(
                sorted(self.manifest.relations, key=lambda item: item.relation_id)
            )
        }
        self._columns = {
            relation.relation_id: {
                column.column_id: f"c_{index:04d}"
                for index, column in enumerate(
                    sorted(relation.columns, key=lambda item: item.column_id)
                )
            }
            for relation in self.manifest.relations
        }
        self._provision_database()

    @property
    def is_quiescing(self) -> bool:
        """Implementation-private lifecycle state consumed by fixture control."""

        return self._quiescing

    def _ensure_live(self) -> None:
        if self._released:
            raise RelationalReferenceError("relational resource reference is released")
        if not self._logical_binding_valid:
            raise RelationalCompatibilityError("logical relational binding has drifted")
        if self.execution_input_identity != self._bound_execution_identity:
            raise RelationalCompatibilityError(
                "execution-relevant database input identity has drifted"
            )

    @staticmethod
    def _sql_type(column: ColumnDefinition, sql: Any) -> Any:
        kind = column.value_type.kind
        if kind is ValueType.BOOLEAN:
            return sql.SQL("boolean")
        if kind is ValueType.INTEGER:
            # Portable v0.1 integers may exceed bigint; numeric(65,0) preserves
            # the current closed lexical domain without changing the AVP type.
            return sql.SQL("numeric(65,0)")
        if kind is ValueType.DECIMAL:
            return sql.SQL(
                f"numeric({column.value_type.precision},{column.value_type.scale})"
            )
        if kind is ValueType.TEXT:
            return sql.SQL("text")
        if kind is ValueType.BINARY:
            return sql.SQL("bytea")
        if kind is ValueType.DATE:
            return sql.SQL("date")
        precision = column.value_type.fractional_precision
        if kind is ValueType.TIME_LOCAL:
            return sql.SQL(f"time({precision}) without time zone")
        if kind is ValueType.TIMESTAMP_LOCAL:
            return sql.SQL(f"timestamp({precision}) without time zone")
        if kind is ValueType.TIMESTAMP_INSTANT:
            return sql.SQL(f"timestamp({precision}) with time zone")
        if kind is ValueType.UUID:
            return sql.SQL("uuid")
        raise RelationalCompatibilityError(f"unsupported PostgreSQL value kind: {kind}")

    @staticmethod
    def _to_database(column: ColumnDefinition, value: RelationalValue) -> Any:
        InMemoryRelationalResource._validate_value(column, value)
        raw = value.value
        if raw is None:
            return None
        kind = value.kind
        if kind is ValueType.BOOLEAN:
            return raw
        assert isinstance(raw, str)
        if kind in {ValueType.INTEGER, ValueType.DECIMAL}:
            return Decimal(raw)
        if kind is ValueType.TEXT:
            return raw
        if kind is ValueType.BINARY:
            padding = "=" * ((4 - len(raw) % 4) % 4)
            return base64.urlsafe_b64decode(raw + padding)
        if kind is ValueType.DATE:
            return date.fromisoformat(raw)
        if kind is ValueType.TIME_LOCAL:
            return time.fromisoformat(raw)
        if kind is ValueType.TIMESTAMP_LOCAL:
            return datetime.fromisoformat(raw)
        if kind is ValueType.TIMESTAMP_INSTANT:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if kind is ValueType.UUID:
            return uuid.UUID(raw)
        raise RelationalCompatibilityError(f"unsupported PostgreSQL value kind: {kind}")

    @staticmethod
    def _from_database(column: ColumnDefinition, raw: Any) -> RelationalValue:
        kind = column.value_type.kind
        if raw is None:
            result = RelationalValue(kind, None)
        elif kind is ValueType.BOOLEAN:
            result = RelationalValue(kind, bool(raw))
        elif kind is ValueType.INTEGER:
            if not isinstance(raw, Decimal):
                raw = Decimal(raw)
            result = RelationalValue(kind, format(raw, "f"))
        elif kind is ValueType.DECIMAL:
            if not isinstance(raw, Decimal):
                raw = Decimal(raw)
            scale = column.value_type.scale or 0
            result = RelationalValue(kind, f"{raw:.{scale}f}")
        elif kind is ValueType.TEXT:
            result = RelationalValue(kind, str(raw))
        elif kind is ValueType.BINARY:
            encoded = base64.urlsafe_b64encode(bytes(raw)).decode("ascii").rstrip("=")
            result = RelationalValue(kind, encoded)
        elif kind is ValueType.DATE:
            result = RelationalValue(kind, raw.isoformat())
        elif kind is ValueType.TIME_LOCAL:
            result = RelationalValue(
                kind,
                _fractional_time(raw, column.value_type.fractional_precision or 0),
            )
        elif kind is ValueType.TIMESTAMP_LOCAL:
            result = RelationalValue(
                kind,
                _fractional_timestamp(
                    raw,
                    column.value_type.fractional_precision or 0,
                    instant=False,
                ),
            )
        elif kind is ValueType.TIMESTAMP_INSTANT:
            result = RelationalValue(
                kind,
                _fractional_timestamp(
                    raw,
                    column.value_type.fractional_precision or 0,
                    instant=True,
                ),
            )
        elif kind is ValueType.UUID:
            result = RelationalValue(kind, str(raw).lower())
        else:
            raise RelationalCompatibilityError(
                f"unsupported PostgreSQL value kind: {kind}"
            )
        InMemoryRelationalResource._validate_value(column, result)
        return result

    def _provision_database(self) -> None:
        psycopg, sql = _driver()
        with psycopg.connect(self._dsn, autocommit=True) as connection:
            connection.execute(
                sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self._schema))
            )
            connection.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(self._schema),
                    sql.Identifier(self._evaluator_role),
                )
            )
            connection.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(self._schema),
                    sql.Identifier(self._subject_role),
                )
            )
            for relation in self.manifest.relations:
                column_sql: list[Any] = []
                physical_columns = self._columns[relation.relation_id]
                for column in relation.columns:
                    fragment = sql.SQL("{} {}").format(
                        sql.Identifier(physical_columns[column.column_id]),
                        self._sql_type(column, sql),
                    )
                    if not column.nullable:
                        fragment += sql.SQL(" NOT NULL")
                    column_sql.append(fragment)
                connection.execute(
                    sql.SQL("CREATE TABLE {}.{} ({})").format(
                        sql.Identifier(self._schema),
                        sql.Identifier(self._tables[relation.relation_id]),
                        sql.SQL(", ").join(column_sql),
                    )
                )
                table = sql.SQL("{}.{}").format(
                    sql.Identifier(self._schema),
                    sql.Identifier(self._tables[relation.relation_id]),
                )
                connection.execute(
                    sql.SQL("GRANT SELECT ON {} TO {}").format(
                        table,
                        sql.Identifier(self._evaluator_role),
                    )
                )
                visible = [
                    column
                    for column in relation.columns
                    if (relation.relation_id, column.column_id)
                    not in self._private_columns
                ]
                if visible:
                    visible_sql = sql.SQL(", ").join(
                        sql.Identifier(physical_columns[column.column_id])
                        for column in visible
                    )
                    connection.execute(
                        sql.SQL("GRANT SELECT ({}) ON {} TO {}").format(
                            visible_sql,
                            table,
                            sql.Identifier(self._subject_role),
                        )
                    )
                    connection.execute(
                        sql.SQL("GRANT INSERT ({}) ON {} TO {}").format(
                            visible_sql,
                            table,
                            sql.Identifier(self._subject_role),
                        )
                    )
                    connection.execute(
                        sql.SQL("GRANT UPDATE ({}) ON {} TO {}").format(
                            visible_sql,
                            table,
                            sql.Identifier(self._subject_role),
                        )
                    )
                connection.execute(
                    sql.SQL("GRANT DELETE ON {} TO {}").format(
                        table,
                        sql.Identifier(self._subject_role),
                    )
                )
        self._replace_relations(self._baseline)
        observed = self.state_image()
        if observed.digest != self.baseline_digest:
            self._drop_schema()
            raise RelationalCompatibilityError(
                "PostgreSQL baseline materialization changed canonical StateImage identity"
            )

    def _drop_schema(self) -> None:
        psycopg, sql = _driver()
        with psycopg.connect(self._dsn, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                    sql.Identifier(self._schema)
                )
            )

    def _replace_relations_on_connection(
        self,
        connection: Any,
        replacements: Mapping[str, Sequence[RelationalRow]],
    ) -> None:
        _, sql = _driver()
        for relation_id, replacement in replacements.items():
            relation = self.manifest.relation(relation_id)
            table = sql.SQL("{}.{}").format(
                sql.Identifier(self._schema),
                sql.Identifier(self._tables[relation_id]),
            )
            connection.execute(sql.SQL("DELETE FROM {}").format(table))
            if not replacement:
                continue
            columns = sorted(relation.columns, key=lambda item: item.column_id)
            physical_columns = self._columns[relation_id]
            statement = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                table,
                sql.SQL(", ").join(
                    sql.Identifier(physical_columns[column.column_id])
                    for column in columns
                ),
                sql.SQL(", ").join(sql.Placeholder() for _ in columns),
            )
            for row in replacement:
                values = row.value_map()
                connection.execute(
                    statement,
                    [
                        self._to_database(column, values[column.column_id])
                        for column in columns
                    ],
                )

    def _replace_relations(
        self,
        replacements: Mapping[str, Sequence[RelationalRow]],
    ) -> None:
        psycopg, _ = _driver()
        with psycopg.connect(self._dsn) as connection:
            self._replace_relations_on_connection(connection, replacements)

    def _validated_candidate(
        self,
        replacements: Mapping[str, Sequence[RelationalRow]],
    ) -> dict[str, tuple[RelationalRow, ...]]:
        self._ensure_live()
        if not replacements:
            raise RelationalLifecycleError("atomic fixture mutation must not be empty")
        current = dict(self.state_image().relations)
        unknown = set(replacements) - set(current)
        if unknown:
            raise RelationalLifecycleError(
                f"fixture mutation references unknown relations: {sorted(unknown)}"
            )
        current.update(
            (relation_id, tuple(rows))
            for relation_id, rows in replacements.items()
        )
        return InMemoryRelationalResource._validate_state_for_manifest(
            self.manifest,
            current,
        )

    def _read_relation(
        self,
        connection: Any,
        relation: RelationDefinition,
        columns: Sequence[ColumnDefinition],
    ) -> tuple[RelationalRow, ...]:
        _, sql = _driver()
        physical_columns = self._columns[relation.relation_id]
        selected = sorted(columns, key=lambda item: item.column_id)
        statement = sql.SQL("SELECT {} FROM {}.{}").format(
            sql.SQL(", ").join(
                sql.Identifier(physical_columns[column.column_id])
                for column in selected
            ),
            sql.Identifier(self._schema),
            sql.Identifier(self._tables[relation.relation_id]),
        )
        rows: list[RelationalRow] = []
        for raw_row in connection.execute(statement).fetchall():
            rows.append(
                RelationalRow.from_mapping(
                    {
                        column.column_id: self._from_database(column, raw)
                        for column, raw in zip(selected, raw_row, strict=True)
                    }
                )
            )
        return tuple(rows)

    def _read_full_state(self) -> dict[str, tuple[RelationalRow, ...]]:
        self._ensure_live()
        psycopg, sql = _driver()
        raw_state: dict[str, tuple[RelationalRow, ...]] = {}
        with psycopg.connect(self._dsn, autocommit=True) as connection:
            with connection.transaction():
                connection.execute(
                    sql.SQL("SET LOCAL ROLE {}").format(
                        sql.Identifier(self._evaluator_role)
                    )
                )
                connection.execute(
                    "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
                )
                for relation in self.manifest.relations:
                    raw_state[relation.relation_id] = self._read_relation(
                        connection,
                        relation,
                        relation.columns,
                    )
        return InMemoryRelationalResource._validate_state_for_manifest(
            self.manifest,
            raw_state,
        )

    def state_image(self) -> StateImage:
        state = self._read_full_state()
        return StateImage(
            self.manifest_digest,
            tuple(
                (relation.relation_id, state[relation.relation_id])
                for relation in sorted(
                    self.manifest.relations,
                    key=lambda item: item.relation_id,
                )
            ),
        )

    @staticmethod
    def _projection_document(
        manifest: RelationalManifest,
        state: Mapping[str, tuple[RelationalRow, ...]],
        projection_id: str,
    ) -> dict[str, object]:
        projection = manifest.projection(projection_id)
        relations: list[dict[str, object]] = []
        for selected in sorted(
            projection.relations,
            key=lambda item: item.relation_id,
        ):
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

    def project(self, projection_id: str) -> Mapping[str, object]:
        state = self._read_full_state()
        return self._projection_document(self.manifest, state, projection_id)

    def enter_quiescing(self) -> None:
        self._ensure_live()
        self._quiescing = True

    def final_projection(self, projection_id: str) -> Mapping[str, object]:
        self._ensure_live()
        if not self._quiescing or self._held_labels:
            raise RelationalLifecycleError(
                "final projection requires settled QUIESCING boundary"
            )
        return self.project(projection_id)

    def snapshot(self) -> RelationalSnapshot:
        state = self.state_image()
        self._snapshot_sequence += 1
        return RelationalSnapshot(
            snapshot_id=f"relational-snapshot-{self._snapshot_sequence}",
            environment_id=self.environment_id,
            resource_id=self.resource_id,
            resource_instance_id=self.resource_instance_id,
            state=state,
        )

    def reset(self) -> StateImage:
        self._ensure_live()
        self._replace_relations(self._baseline)
        observed = self.state_image()
        if observed.digest != self.baseline_digest:
            raise RelationalError(
                "reset did not re-establish baseline StateImage identity"
            )
        return observed

    def _validate_snapshot_owner(self, snapshot: RelationalSnapshot) -> None:
        if (
            snapshot.environment_id != self.environment_id
            or snapshot.resource_id != self.resource_id
            or snapshot.resource_instance_id != self.resource_instance_id
        ):
            raise RelationalReferenceError("foreign or stale relational SnapshotRef")
        if snapshot.state.manifest_digest != self.manifest_digest:
            raise RelationalReferenceError("snapshot Manifest identity mismatch")

    def restore(self, snapshot: RelationalSnapshot) -> RestoreFidelity:
        self._ensure_live()
        self._validate_snapshot_owner(snapshot)
        candidate = InMemoryRelationalResource._validate_state_for_manifest(
            self.manifest,
            dict(snapshot.state.relations),
        )
        self._replace_relations(candidate)
        observed = self.state_image()
        if observed.digest != snapshot.state.digest:
            return RestoreFidelity.NON_EQUIVALENT
        return RestoreFidelity.STATE_EQUIVALENT

    def subject_view(
        self,
        authorized: Iterable[tuple[str, str]],
    ) -> Mapping[str, tuple[RelationalRow, ...]]:
        self._ensure_live()
        allowed = frozenset(authorized)
        if self._private_columns & allowed:
            raise RelationalVisibilityError(
                "Subject authorization includes evaluator-private column"
            )
        psycopg, sql = _driver()
        result: dict[str, tuple[RelationalRow, ...]] = {}
        with psycopg.connect(self._dsn, autocommit=True) as connection:
            with connection.transaction():
                connection.execute(
                    sql.SQL("SET LOCAL ROLE {}").format(
                        sql.Identifier(self._subject_role)
                    )
                )
                connection.execute(
                    "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
                )
                for relation in self.manifest.relations:
                    selected_ids = {
                        column_id
                        for relation_id, column_id in allowed
                        if relation_id == relation.relation_id
                    }
                    if not selected_ids:
                        continue
                    columns = tuple(
                        column
                        for column in relation.columns
                        if column.column_id in selected_ids
                    )
                    result[relation.relation_id] = self._read_relation(
                        connection,
                        relation,
                        columns,
                    )
        return result

    def diff(self, before: StateImage, after: StateImage) -> RelationalDiff:
        self._ensure_live()
        if (
            before.manifest_digest != self.manifest_digest
            or after.manifest_digest != self.manifest_digest
        ):
            raise RelationalCompatibilityError(
                "cross-Manifest comparison is not relational row diff"
            )
        before_map = dict(before.relations)
        after_map = dict(after.relations)
        expected = {relation.relation_id for relation in self.manifest.relations}
        if set(before_map) != expected or set(after_map) != expected:
            raise RelationalCompatibilityError(
                "diff states do not cover the full Manifest surface"
            )

        changes: list[DiffChange] = []
        for relation in sorted(
            self.manifest.relations,
            key=lambda item: item.relation_id,
        ):
            old_rows = {
                _canonical_key_bytes(row): row
                for row in before_map[relation.relation_id]
            }
            new_rows = {
                _canonical_key_bytes(row): row
                for row in after_map[relation.relation_id]
            }
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
        return RelationalDiff(
            manifest_digest=self.manifest_digest,
            before_digest=before.digest,
            after_digest=after.digest,
            changes=tuple(changes),
        )

    def set_logical_binding_valid(self, valid: bool) -> None:
        self._logical_binding_valid = valid

    def set_execution_input_identity(self, identity: str) -> None:
        _require_digest(identity, "execution input identity")
        self.execution_input_identity = identity

    def release(self) -> None:
        if self._released:
            return
        for connection in tuple(self._held_connections.values()):
            try:
                connection.rollback()
            finally:
                connection.close()
        self._held_connections.clear()
        self._held_labels.clear()
        self._drop_schema()
        self._released = True


class _TornPostgreSQLResource(PostgreSQLRelationalResource):
    """Negative SUT that exposes a metadata-identical torn projection."""

    def project(self, projection_id: str) -> Mapping[str, object]:
        document = dict(super().project(projection_id))
        relations = document.get("relations")
        if isinstance(relations, list) and len(relations) >= 2:
            first_rows = relations[0].get("rows")
            second_rows = relations[1].get("rows")
            if first_rows and second_rows:
                first_rows[0]["values"]["epoch"] = {
                    "type": "integer",
                    "value": "1",
                }
                second_rows[0]["values"]["epoch"] = {
                    "type": "integer",
                    "value": "2",
                }
        return document


class _FalseRestorePostgreSQLResource(PostgreSQLRelationalResource):
    """Negative SUT that claims restore without applying database state."""

    def restore(self, snapshot: RelationalSnapshot) -> RestoreFidelity:
        self._ensure_live()
        self._validate_snapshot_owner(snapshot)
        return RestoreFidelity.STATE_EQUIVALENT


class _HiddenLeakPostgreSQLResource(PostgreSQLRelationalResource):
    """Negative SUT that deliberately bypasses Subject column grants."""

    def subject_view(
        self,
        authorized: Iterable[tuple[str, str]],
    ) -> Mapping[str, tuple[RelationalRow, ...]]:
        del authorized
        return dict(self.state_image().relations)


class _ExecutionDriftPostgreSQLResource(PostgreSQLRelationalResource):
    """Negative SUT that intentionally suppresses execution-input drift."""

    def _ensure_live(self) -> None:
        if self._released:
            raise RelationalReferenceError("relational resource reference is released")
        if not self._logical_binding_valid:
            raise RelationalCompatibilityError("logical relational binding has drifted")


_NEGATIVE_RESOURCE_TYPES: Mapping[
    NegativeControl,
    type[PostgreSQLRelationalResource],
] = {
    NegativeControl.TORN_PROJECTION: _TornPostgreSQLResource,
    NegativeControl.FALSE_RESTORE: _FalseRestorePostgreSQLResource,
    NegativeControl.HIDDEN_STATE_LEAK: _HiddenLeakPostgreSQLResource,
    NegativeControl.EXECUTION_INPUT_DRIFT: _ExecutionDriftPostgreSQLResource,
}


class PostgreSQLRelationalFixtureControl(RelationalFixtureControl):
    """Privileged PostgreSQL controls implementing logical fixture intent."""

    @staticmethod
    def _resource(sut: RelationalSUT) -> PostgreSQLRelationalResource:
        if not isinstance(sut, PostgreSQLRelationalResource):
            raise TypeError("fixture control received a foreign relational SUT")
        return sut

    @staticmethod
    def _require_mutation_admission(resource: PostgreSQLRelationalResource) -> None:
        resource._ensure_live()
        if resource.is_quiescing:
            raise RelationalLifecycleError(
                "new Subject mutation rejected after QUIESCING"
            )

    def replace_relation(
        self,
        sut: RelationalSUT,
        relation_id: str,
        replacement: Sequence[RelationalRow],
    ) -> None:
        resource = self._resource(sut)
        self._require_mutation_admission(resource)
        candidate = resource._validated_candidate({relation_id: replacement})
        resource._replace_relations({relation_id: candidate[relation_id]})

    def replace_relations_atomically(
        self,
        sut: RelationalSUT,
        replacements: Mapping[str, Sequence[RelationalRow]],
    ) -> None:
        resource = self._resource(sut)
        self._require_mutation_admission(resource)
        candidate = resource._validated_candidate(replacements)
        resource._replace_relations(
            {
                relation_id: candidate[relation_id]
                for relation_id in replacements
            }
        )

    def project_during_atomic_commit(
        self,
        sut: RelationalSUT,
        *,
        projection_id: str,
        replacements: Mapping[str, Sequence[RelationalRow]],
    ) -> Mapping[str, object]:
        resource = self._resource(sut)
        self._require_mutation_admission(resource)
        candidate = resource._validated_candidate(replacements)
        normalized = {
            relation_id: candidate[relation_id]
            for relation_id in replacements
        }
        psycopg, _ = _driver()
        writer_ready = threading.Event()
        allow_commit = threading.Event()
        errors: list[BaseException] = []

        def writer() -> None:
            connection = psycopg.connect(resource._dsn)
            try:
                resource._replace_relations_on_connection(connection, normalized)
                writer_ready.set()
                if not allow_commit.wait(timeout=10):
                    raise TimeoutError("PostgreSQL commit barrier timed out")
                connection.commit()
            except BaseException as exc:  # propagated to the controlling thread
                errors.append(exc)
                connection.rollback()
            finally:
                connection.close()
                writer_ready.set()

        thread = threading.Thread(
            target=writer,
            name="avp-postgresql-atomic-fixture",
            daemon=True,
        )
        thread.start()
        if not writer_ready.wait(timeout=10):
            allow_commit.set()
            thread.join(timeout=10)
            raise RelationalError("PostgreSQL writer did not reach commit barrier")
        if errors:
            allow_commit.set()
            thread.join(timeout=10)
            raise RelationalError("PostgreSQL atomic writer failed") from errors[0]
        try:
            # While the writer transaction is uncommitted, PostgreSQL MVCC must
            # expose one committed pre-state. The writer then commits atomically.
            observed = resource.project(projection_id)
        finally:
            allow_commit.set()
            thread.join(timeout=10)
        if thread.is_alive():
            raise RelationalError("PostgreSQL atomic writer did not terminate")
        if errors:
            raise RelationalError("PostgreSQL atomic writer failed") from errors[0]
        return observed

    def begin_held_mutation(
        self,
        sut: RelationalSUT,
        *,
        label: str,
        relation_id: str,
        replacement: Sequence[RelationalRow],
    ) -> None:
        resource = self._resource(sut)
        self._require_mutation_admission(resource)
        if not label:
            raise RelationalLifecycleError("held mutation label must not be empty")
        if label in resource._held_labels:
            raise RelationalLifecycleError(
                f"held mutation label already exists: {label}"
            )
        candidate = resource._validated_candidate({relation_id: replacement})
        psycopg, _ = _driver()
        connection = psycopg.connect(resource._dsn)
        try:
            resource._replace_relations_on_connection(
                connection,
                {relation_id: candidate[relation_id]},
            )
        except BaseException:
            connection.rollback()
            connection.close()
            raise
        resource._held_labels.add(label)
        resource._held_connections[label] = connection

    def settle_held_mutation(
        self,
        sut: RelationalSUT,
        *,
        label: str,
        commit: bool,
    ) -> None:
        resource = self._resource(sut)
        resource._ensure_live()
        try:
            connection = resource._held_connections.pop(label)
        except KeyError as exc:
            raise RelationalLifecycleError(
                f"unknown held mutation label: {label}"
            ) from exc
        try:
            if commit:
                connection.commit()
            else:
                connection.rollback()
        finally:
            connection.close()
            resource._held_labels.discard(label)

    def set_logical_binding_valid(self, sut: RelationalSUT, valid: bool) -> None:
        self._resource(sut).set_logical_binding_valid(valid)

    def set_execution_input_identity(self, sut: RelationalSUT, identity: str) -> None:
        self._resource(sut).set_execution_input_identity(identity)


class PostgreSQLRelationalBackendHarness(RelationalBackendHarness):
    """Database-specific implementation of the adopted backend-neutral harness."""

    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("PostgreSQL control DSN must not be empty")
        self._dsn = dsn
        self._fixture_control = PostgreSQLRelationalFixtureControl()
        self._resources: list[PostgreSQLRelationalResource] = []
        suffix = uuid.uuid4().hex[:12]
        self._subject_role = f"avp_subject_{suffix}"
        self._evaluator_role = f"avp_evaluator_{suffix}"
        self._create_roles()

    @property
    def fixture_control(self) -> RelationalFixtureControl:
        return self._fixture_control

    def _create_roles(self) -> None:
        psycopg, sql = _driver()
        with psycopg.connect(self._dsn, autocommit=True) as connection:
            connection.execute(
                sql.SQL("CREATE ROLE {} NOLOGIN").format(
                    sql.Identifier(self._subject_role)
                )
            )
            connection.execute(
                sql.SQL("CREATE ROLE {} NOLOGIN").format(
                    sql.Identifier(self._evaluator_role)
                )
            )

    def identity_artifacts(
        self,
        manifest: RelationalManifest,
        baseline: Mapping[str, Sequence[RelationalRow]],
    ) -> tuple[str, str]:
        return InMemoryRelationalResource.identity_artifacts(manifest, baseline)

    def provision(
        self,
        spec: RelationalResourceSpec,
        *,
        negative_control: NegativeControl | None = None,
    ) -> RelationalSUT:
        resource_type = (
            PostgreSQLRelationalResource
            if negative_control is None
            else _NEGATIVE_RESOURCE_TYPES[negative_control]
        )
        resource = resource_type(
            dsn=self._dsn,
            subject_role=self._subject_role,
            evaluator_role=self._evaluator_role,
            spec=spec,
        )
        self._resources.append(resource)
        return resource

    def validate_value(
        self,
        column: ColumnDefinition,
        value: RelationalValue,
    ) -> None:
        # Validate portable lexical constraints first, then prove that the
        # selected PostgreSQL representation round-trips without loss.
        InMemoryRelationalResource._validate_value(column, value)
        psycopg, sql = _driver()
        encoded = PostgreSQLRelationalResource._to_database(column, value)
        with psycopg.connect(self._dsn, autocommit=True) as connection:
            observed = connection.execute(
                sql.SQL("SELECT {}::{}").format(
                    sql.Placeholder(),
                    PostgreSQLRelationalResource._sql_type(column, sql),
                ),
                (encoded,),
            ).fetchone()
        assert observed is not None
        decoded = PostgreSQLRelationalResource._from_database(column, observed[0])
        if decoded != value:
            raise RelationalCompatibilityError(
                "PostgreSQL scalar round-trip changed canonical AVP value"
            )

    def close(self) -> None:
        """Release all database resources and implementation-private roles."""

        for resource in reversed(self._resources):
            resource.release()
        self._resources.clear()
        psycopg, sql = _driver()
        with psycopg.connect(self._dsn, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP ROLE IF EXISTS {}").format(
                    sql.Identifier(self._subject_role)
                )
            )
            connection.execute(
                sql.SQL("DROP ROLE IF EXISTS {}").format(
                    sql.Identifier(self._evaluator_role)
                )
            )

    def __enter__(self) -> "PostgreSQLRelationalBackendHarness":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

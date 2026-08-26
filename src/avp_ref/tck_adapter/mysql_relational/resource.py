"""MySQL/InnoDB-backed relational SUT implementation."""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from avp_ref.relational import (
    ColumnDefinition,
    InMemoryRelationalResource,
    RelationDefinition,
    RelationalCompatibilityError,
    RelationalDiff,
    RelationalError,
    RelationalLifecycleError,
    RelationalReferenceError,
    RelationalRow,
    RelationalSnapshot,
    RelationalVisibilityError,
    RestoreFidelity,
    StateImage,
)

from ..relational_harness import RelationalResourceSpec, RelationalSUT
from .codec import from_database, sql_type, to_database
from .common import (
    deterministic_row_order,
    projection_document,
    relational_diff,
    require_digest,
    validate_spec,
)
from .driver import MySQLConnectionSettings, connect, quote_identifier


class MySQLRelationalResource(RelationalSUT):
    """Relational SUT whose authoritative logical state lives in InnoDB."""

    def __init__(
        self,
        *,
        control_settings: MySQLConnectionSettings,
        subject_settings: MySQLConnectionSettings,
        evaluator_settings: MySQLConnectionSettings,
        spec: RelationalResourceSpec,
    ) -> None:
        manifest_digest, baseline_digest, baseline = validate_spec(spec)

        self.environment_id = spec.environment_id
        self.resource_id = spec.resource_id
        self.resource_instance_id = spec.resource_instance_id
        self.manifest = spec.manifest
        self.manifest_digest = manifest_digest
        self.baseline_digest = baseline_digest
        self.execution_input_identity = spec.execution_input_identity

        self._control_settings = control_settings
        self._bound_execution_identity = spec.execution_input_identity
        self._private_columns = spec.evaluator_private_columns
        self._baseline = baseline
        self._logical_binding_valid = True
        self._quiescing = False
        self._released = False
        self._snapshot_sequence = 0
        self._held_labels: set[str] = set()
        self._held_connections: dict[str, Any] = {}

        suffix = uuid.uuid4().hex[:20]
        self._database = f"avp_r_{suffix}"
        self._subject_settings = subject_settings.with_principal(
            user=subject_settings.user,
            password=subject_settings.password,
            database=self._database,
        )
        self._evaluator_settings = evaluator_settings.with_principal(
            user=evaluator_settings.user,
            password=evaluator_settings.password,
            database=self._database,
        )
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

    @property
    def database(self) -> str:
        """Implementation-private physical database name used by the harness."""

        return self._database

    @property
    def is_quiescing(self) -> bool:
        return self._quiescing

    def provision_database(self) -> None:
        """Create isolated InnoDB objects and materialize the validated baseline."""

        connection = connect(self._control_settings, autocommit=True)
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"CREATE DATABASE {quote_identifier(self._database)} "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin"
                )
                cursor.execute(f"USE {quote_identifier(self._database)}")
                for relation in self.manifest.relations:
                    self._create_relation(cursor, relation)
            finally:
                cursor.close()
        finally:
            connection.close()

        self._replace_relations(self._baseline)

    def _create_relation(self, cursor: Any, relation: RelationDefinition) -> None:
        physical_columns = self._columns[relation.relation_id]
        fragments = []
        for column in relation.columns:
            fragment = (
                f"{quote_identifier(physical_columns[column.column_id])} "
                f"{sql_type(column)}"
            )
            if not column.nullable:
                fragment += " NOT NULL"
            fragments.append(fragment)
        table = quote_identifier(self._tables[relation.relation_id])
        cursor.execute(
            f"CREATE TABLE {table} ({', '.join(fragments)}) ENGINE=InnoDB"
        )

    def _ensure_live(self) -> None:
        if self._released:
            raise RelationalReferenceError("relational resource reference is released")
        if not self._logical_binding_valid:
            raise RelationalCompatibilityError("logical relational binding has drifted")
        if self.execution_input_identity != self._bound_execution_identity:
            raise RelationalCompatibilityError(
                "execution-relevant database input identity has drifted"
            )

    def _drop_database(self) -> None:
        connection = connect(self._control_settings, autocommit=True)
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"DROP DATABASE IF EXISTS {quote_identifier(self._database)}"
                )
            finally:
                cursor.close()
        finally:
            connection.close()

    def _database_control_settings(self) -> MySQLConnectionSettings:
        return self._control_settings.with_principal(
            user=self._control_settings.user,
            password=self._control_settings.password,
            database=self._database,
        )

    def _replace_relations_on_connection(
        self,
        connection: Any,
        replacements: Mapping[str, Sequence[RelationalRow]],
    ) -> None:
        cursor = connection.cursor()
        try:
            for relation_id, replacement in replacements.items():
                relation = self.manifest.relation(relation_id)
                table = quote_identifier(self._tables[relation_id])
                cursor.execute(f"DELETE FROM {table}")
                if not replacement:
                    continue
                columns = sorted(relation.columns, key=lambda item: item.column_id)
                physical_columns = self._columns[relation_id]
                names = ", ".join(
                    quote_identifier(physical_columns[column.column_id])
                    for column in columns
                )
                placeholders = ", ".join(["%s"] * len(columns))
                statement = f"INSERT INTO {table} ({names}) VALUES ({placeholders})"
                for row in replacement:
                    values = row.value_map()
                    cursor.execute(
                        statement,
                        tuple(
                            to_database(column, values[column.column_id])
                            for column in columns
                        ),
                    )
        finally:
            cursor.close()

    def _replace_relations(
        self,
        replacements: Mapping[str, Sequence[RelationalRow]],
    ) -> None:
        connection = connect(self._database_control_settings())
        try:
            self._replace_relations_on_connection(connection, replacements)
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

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
        cursor: Any,
        relation: RelationDefinition,
        columns: Sequence[ColumnDefinition],
    ) -> tuple[RelationalRow, ...]:
        physical_columns = self._columns[relation.relation_id]
        selected = sorted(columns, key=lambda item: item.column_id)
        names = ", ".join(
            quote_identifier(physical_columns[column.column_id])
            for column in selected
        )
        cursor.execute(
            f"SELECT {names} FROM {quote_identifier(self._tables[relation.relation_id])}"
        )
        rows = [
            RelationalRow.from_mapping(
                {
                    column.column_id: from_database(column, raw)
                    for column, raw in zip(selected, raw_row, strict=True)
                }
            )
            for raw_row in cursor.fetchall()
        ]
        return deterministic_row_order(rows)

    @staticmethod
    def _start_consistent_read(connection: Any) -> None:
        # Keep isolation/snapshot intent centralized in the official driver API.
        connection.start_transaction(
            consistent_snapshot=True,
            isolation_level="REPEATABLE READ",
            readonly=True,
        )

    def _read_full_state(self) -> dict[str, tuple[RelationalRow, ...]]:
        self._ensure_live()
        connection = connect(self._evaluator_settings)
        try:
            self._start_consistent_read(connection)
            cursor = connection.cursor()
            try:
                raw_state = {
                    relation.relation_id: self._read_relation(
                        cursor,
                        relation,
                        relation.columns,
                    )
                    for relation in self.manifest.relations
                }
            finally:
                cursor.close()
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
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

    def project(self, projection_id: str) -> Mapping[str, object]:
        return projection_document(
            self.manifest,
            self._read_full_state(),
            projection_id,
        )

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
        connection = connect(self._subject_settings)
        try:
            self._start_consistent_read(connection)
            cursor = connection.cursor()
            try:
                result: dict[str, tuple[RelationalRow, ...]] = {}
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
                        cursor,
                        relation,
                        columns,
                    )
            finally:
                cursor.close()
            connection.commit()
            return result
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def diff(self, before: StateImage, after: StateImage) -> RelationalDiff:
        self._ensure_live()
        return relational_diff(
            self.manifest,
            self.manifest_digest,
            before,
            after,
        )

    def set_logical_binding_valid(self, valid: bool) -> None:
        self._logical_binding_valid = valid

    def set_execution_input_identity(self, identity: str) -> None:
        require_digest(identity, "execution input identity")
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
        self._drop_database()
        self._released = True

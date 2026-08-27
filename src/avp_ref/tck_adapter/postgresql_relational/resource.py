"""PostgreSQL-backed Relational State resource implementation.

The class owns database materialization and portable resource operations while
keeping PostgreSQL identifiers, roles, SQL, transaction mechanics, and snapshot
mechanisms implementation-private.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from avp_ref.relational import (
    ColumnDefinition,
    InMemoryRelationalResource,
    RelationDefinition,
    RelationalCompatibilityError,
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
from .common import projection_document, relational_diff, require_digest
from .driver import load_driver


class PostgreSQLRelationalResource(RelationalSUT):
    """Relational SUT whose authoritative logical state is stored in PostgreSQL."""

    def __init__(
        self,
        *,
        dsn: str,
        subject_role: str,
        evaluator_role: str,
        spec: RelationalResourceSpec,
    ) -> None:
        manifest_digest, baseline_digest = InMemoryRelationalResource.identity_artifacts(
            spec.manifest,
            spec.baseline_mapping(),
        )
        if manifest_digest != spec.manifest_artifact_digest:
            raise RelationalCompatibilityError(
                "Manifest Artifact digest does not match canonical Manifest bytes"
            )
        if baseline_digest != spec.baseline_artifact_digest:
            raise RelationalCompatibilityError(
                "baseline Artifact digest does not match canonical StateImage bytes"
            )
        require_digest(spec.execution_input_identity, "execution input identity")
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

    @property
    def is_quiescing(self) -> bool:
        """Implementation-private lifecycle state consumed by fixture control."""

        return self._quiescing

    def provision_database(self) -> None:
        """Materialize schema, grants, and baseline, then verify evaluator state."""

        psycopg, sql = load_driver()
        try:
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
                    self._create_relation(connection, relation, sql)
            self._replace_relations(self._baseline)
            if self.state_image().digest != self.baseline_digest:
                raise RelationalCompatibilityError(
                    "PostgreSQL baseline materialization changed canonical StateImage identity"
                )
        except BaseException:
            # PostgreSQL DDL is transactional only within an explicit transaction;
            # autocommit provisioning can therefore fail after creating the schema.
            # Always remove the generated namespace before propagating the failure.
            self._drop_schema()
            raise

    def _create_relation(self, connection: Any, relation: RelationDefinition, sql: Any) -> None:
        physical_columns = self._columns[relation.relation_id]
        column_sql: list[Any] = []
        for column in relation.columns:
            fragment = sql.SQL("{} {}").format(
                sql.Identifier(physical_columns[column.column_id]),
                sql_type(column, sql),
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
            if (relation.relation_id, column.column_id) not in self._private_columns
        ]
        if visible:
            visible_sql = sql.SQL(", ").join(
                sql.Identifier(physical_columns[column.column_id]) for column in visible
            )
            subject = sql.Identifier(self._subject_role)
            connection.execute(
                sql.SQL("GRANT SELECT ({}) ON {} TO {}").format(
                    visible_sql,
                    table,
                    subject,
                )
            )
            connection.execute(
                sql.SQL("GRANT INSERT ({}) ON {} TO {}").format(
                    visible_sql,
                    table,
                    subject,
                )
            )
            connection.execute(
                sql.SQL("GRANT UPDATE ({}) ON {} TO {}").format(
                    visible_sql,
                    table,
                    subject,
                )
            )
        connection.execute(
            sql.SQL("GRANT DELETE ON {} TO {}").format(
                table,
                sql.Identifier(self._subject_role),
            )
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

    def _drop_schema(self) -> None:
        psycopg, sql = load_driver()
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
        _, sql = load_driver()
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
                    sql.Identifier(physical_columns[column.column_id]) for column in columns
                ),
                sql.SQL(", ").join(sql.Placeholder() for _ in columns),
            )
            for row in replacement:
                values = row.value_map()
                connection.execute(
                    statement,
                    [to_database(column, values[column.column_id]) for column in columns],
                )

    def _replace_relations(
        self,
        replacements: Mapping[str, Sequence[RelationalRow]],
    ) -> None:
        psycopg, _ = load_driver()
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
            (relation_id, tuple(rows)) for relation_id, rows in replacements.items()
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
        _, sql = load_driver()
        physical_columns = self._columns[relation.relation_id]
        selected = sorted(columns, key=lambda item: item.column_id)
        statement = sql.SQL("SELECT {} FROM {}.{}").format(
            sql.SQL(", ").join(
                sql.Identifier(physical_columns[column.column_id]) for column in selected
            ),
            sql.Identifier(self._schema),
            sql.Identifier(self._tables[relation.relation_id]),
        )
        rows: list[RelationalRow] = []
        for raw_row in connection.execute(statement).fetchall():
            rows.append(
                RelationalRow.from_mapping(
                    {
                        column.column_id: from_database(column, raw)
                        for column, raw in zip(selected, raw_row, strict=True)
                    }
                )
            )
        return tuple(rows)

    def _read_full_state(self) -> dict[str, tuple[RelationalRow, ...]]:
        self._ensure_live()
        psycopg, sql = load_driver()
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

    def project(self, projection_id: str) -> Mapping[str, object]:
        return projection_document(self.manifest, self._read_full_state(), projection_id)

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
            raise RelationalError("reset did not re-establish baseline StateImage identity")
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

        psycopg, sql = load_driver()
        result: dict[str, tuple[RelationalRow, ...]] = {}
        with psycopg.connect(self._dsn, autocommit=True) as connection:
            with connection.transaction():
                connection.execute(
                    sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(self._subject_role))
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

    def diff(self, before: StateImage, after: StateImage):
        self._ensure_live()
        return relational_diff(
            manifest=self.manifest,
            manifest_digest=self.manifest_digest,
            before=before,
            after=after,
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
        self._drop_schema()
        self._released = True

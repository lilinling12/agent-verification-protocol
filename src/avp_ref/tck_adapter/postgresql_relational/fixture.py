"""Privileged PostgreSQL fixture controls for relational conformance.

The controls implement test-only mutation intent. Native transaction handles,
commit barriers, and control credentials never escape into the portable AVP
resource surface.
"""

from __future__ import annotations

import threading
from collections.abc import Mapping, Sequence

from avp_ref.relational import (
    RelationalError,
    RelationalLifecycleError,
    RelationalRow,
)

from ..relational_harness import RelationalFixtureControl, RelationalSUT
from .driver import load_driver
from .resource import PostgreSQLRelationalResource


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
            {relation_id: candidate[relation_id] for relation_id in replacements}
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
            relation_id: candidate[relation_id] for relation_id in replacements
        }
        psycopg, _ = load_driver()
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
            # While the writer is uncommitted, MVCC must expose one complete
            # committed pre-state. The native transaction then commits atomically.
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
        psycopg, _ = load_driver()
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

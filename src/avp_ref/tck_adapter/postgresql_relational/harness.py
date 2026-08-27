"""PostgreSQL implementation of the adopted backend-neutral relational harness."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from typing import Any

from avp_ref.relational import (
    ColumnDefinition,
    InMemoryRelationalResource,
    RelationalCompatibilityError,
    RelationalManifest,
    RelationalRow,
    RelationalValue,
)

from ..relational_harness import (
    NegativeControl,
    RelationalBackendHarness,
    RelationalFixtureControl,
    RelationalResourceSpec,
    RelationalSUT,
)
from .codec import from_database, sql_type, to_database
from .driver import load_driver
from .fixture import PostgreSQLRelationalFixtureControl
from .negative import NEGATIVE_RESOURCE_TYPES
from .resource import PostgreSQLRelationalResource


class PostgreSQLRelationalBackendHarness(RelationalBackendHarness):
    """Database-specific implementation that keeps PostgreSQL mechanics private."""

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
        """Create both generated principals or leave neither behind on failure."""

        psycopg, sql = load_driver()
        with psycopg.connect(self._dsn, autocommit=True) as connection:
            try:
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
            except BaseException:
                # Role DDL executes immediately under autocommit. A failure on
                # the second CREATE must not leak the first privileged test role.
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
                raise

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
            else NEGATIVE_RESOURCE_TYPES[negative_control]
        )
        resource = resource_type(
            dsn=self._dsn,
            subject_role=self._subject_role,
            evaluator_role=self._evaluator_role,
            spec=spec,
        )
        try:
            resource.provision_database()
        except BaseException:
            # provision_database removes partial schema state; release is not
            # called because it would attempt a second schema cleanup path.
            raise
        self._resources.append(resource)
        return resource

    def validate_value(
        self,
        column: ColumnDefinition,
        value: RelationalValue,
    ) -> None:
        """Prove the selected PostgreSQL representation round-trips exactly."""

        InMemoryRelationalResource._validate_value(column, value)
        psycopg, sql = load_driver()
        encoded = to_database(column, value)
        with psycopg.connect(self._dsn, autocommit=True) as connection:
            observed = connection.execute(
                sql.SQL("SELECT {}::{}").format(
                    sql.Placeholder(),
                    sql_type(column, sql),
                ),
                (encoded,),
            ).fetchone()
        assert observed is not None
        decoded = from_database(column, observed[0])
        if decoded != value:
            raise RelationalCompatibilityError(
                "PostgreSQL scalar round-trip changed canonical AVP value"
            )

    def close(self) -> None:
        """Release resources before deleting generated implementation roles."""

        for resource in reversed(self._resources):
            resource.release()
        self._resources.clear()

        psycopg, sql = load_driver()
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

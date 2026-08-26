"""MySQL/InnoDB implementation of the adopted backend-neutral harness."""

from __future__ import annotations

import secrets
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
from .driver import (
    MySQLConnectionSettings,
    account_sql,
    connect,
    quote_identifier,
)
from .fixture import MySQLRelationalFixtureControl
from .negative import NEGATIVE_RESOURCE_TYPES
from .resource import MySQLRelationalResource


class MySQLRelationalBackendHarness(RelationalBackendHarness):
    """Database-specific implementation that keeps SQL and credentials private."""

    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("MySQL control DSN must not be empty")
        self._control_settings = MySQLConnectionSettings.from_dsn(dsn)
        self._fixture_control = MySQLRelationalFixtureControl()
        self._resources: list[MySQLRelationalResource] = []

        suffix = uuid.uuid4().hex[:12]
        self._subject_user = f"avp_subject_{suffix}"
        self._evaluator_user = f"avp_evaluator_{suffix}"
        self._subject_password = secrets.token_urlsafe(24)
        self._evaluator_password = secrets.token_urlsafe(24)
        self._create_principals()

    @property
    def fixture_control(self) -> RelationalFixtureControl:
        return self._fixture_control

    def _create_principals(self) -> None:
        connection = connect(self._control_settings, autocommit=True)
        cursor = connection.cursor()
        try:
            try:
                cursor.execute(
                    f"CREATE USER {account_sql(self._subject_user)} IDENTIFIED BY %s",
                    (self._subject_password,),
                )
                cursor.execute(
                    f"CREATE USER {account_sql(self._evaluator_user)} IDENTIFIED BY %s",
                    (self._evaluator_password,),
                )
            except BaseException:
                # Account DDL auto-commits. Cleanup both generated accounts so a
                # partial constructor failure never leaks fixture authority.
                cursor.execute(
                    f"DROP USER IF EXISTS {account_sql(self._subject_user)}"
                )
                cursor.execute(
                    f"DROP USER IF EXISTS {account_sql(self._evaluator_user)}"
                )
                raise
        finally:
            cursor.close()
            connection.close()

    def _grant_resource_access(self, resource: MySQLRelationalResource) -> None:
        database = quote_identifier(resource.database)
        connection = connect(self._control_settings, autocommit=True)
        try:
            cursor = connection.cursor()
            try:
                for relation in resource.manifest.relations:
                    table = quote_identifier(resource._tables[relation.relation_id])
                    target = f"{database}.{table}"
                    cursor.execute(
                        f"GRANT SELECT ON {target} TO "
                        f"{account_sql(self._evaluator_user)}"
                    )
                    visible = [
                        column
                        for column in relation.columns
                        if (relation.relation_id, column.column_id)
                        not in resource._private_columns
                    ]
                    if visible:
                        physical_columns = resource._columns[relation.relation_id]
                        column_list = ", ".join(
                            quote_identifier(physical_columns[column.column_id])
                            for column in visible
                        )
                        subject = account_sql(self._subject_user)
                        cursor.execute(
                            f"GRANT SELECT ({column_list}) ON {target} TO {subject}"
                        )
                        cursor.execute(
                            f"GRANT INSERT ({column_list}) ON {target} TO {subject}"
                        )
                        cursor.execute(
                            f"GRANT UPDATE ({column_list}) ON {target} TO {subject}"
                        )
                    cursor.execute(
                        f"GRANT DELETE ON {target} TO "
                        f"{account_sql(self._subject_user)}"
                    )
            finally:
                cursor.close()
        finally:
            connection.close()

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
            MySQLRelationalResource
            if negative_control is None
            else NEGATIVE_RESOURCE_TYPES[negative_control]
        )
        subject_settings = self._control_settings.with_principal(
            user=self._subject_user,
            password=self._subject_password,
            database="mysql",
        )
        evaluator_settings = self._control_settings.with_principal(
            user=self._evaluator_user,
            password=self._evaluator_password,
            database="mysql",
        )
        resource = resource_type(
            control_settings=self._control_settings,
            subject_settings=subject_settings,
            evaluator_settings=evaluator_settings,
            spec=spec,
        )
        try:
            resource.provision_database()
            self._grant_resource_access(resource)
            # Re-read through evaluator authority rather than trusting the
            # privileged connection that materialized the baseline.
            if resource.state_image().digest != resource.baseline_digest:
                raise RelationalCompatibilityError(
                    "MySQL evaluator view does not match baseline identity"
                )
        except BaseException:
            resource.release()
            raise
        self._resources.append(resource)
        return resource

    def validate_value(
        self,
        column: ColumnDefinition,
        value: RelationalValue,
    ) -> None:
        """Prove the selected MySQL type round-trips the canonical value exactly."""

        InMemoryRelationalResource._validate_value(column, value)
        table = f"avp_scalar_{uuid.uuid4().hex[:16]}"
        connection = connect(self._control_settings)
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"CREATE TEMPORARY TABLE {quote_identifier(table)} "
                    f"(v {sql_type(column)})"
                )
                cursor.execute(
                    f"INSERT INTO {quote_identifier(table)} (v) VALUES (%s)",
                    (to_database(column, value),),
                )
                cursor.execute(f"SELECT v FROM {quote_identifier(table)}")
                row = cursor.fetchone()
                assert row is not None
            finally:
                cursor.close()
            connection.rollback()
        finally:
            connection.close()
        decoded = from_database(column, row[0])
        if decoded != value:
            raise RelationalCompatibilityError(
                "MySQL scalar round-trip changed canonical AVP value"
            )

    def close(self) -> None:
        """Release resources before deleting implementation-private principals."""

        for resource in reversed(self._resources):
            resource.release()
        self._resources.clear()

        connection = connect(self._control_settings, autocommit=True)
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"DROP USER IF EXISTS {account_sql(self._subject_user)}"
                )
                cursor.execute(
                    f"DROP USER IF EXISTS {account_sql(self._evaluator_user)}"
                )
            finally:
                cursor.close()
        finally:
            connection.close()

    def __enter__(self) -> "MySQLRelationalBackendHarness":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

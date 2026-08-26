"""Implementation-private MySQL driver and connection helpers."""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass, replace
from typing import Any
from urllib.parse import unquote, urlsplit

from avp_ref.relational import RelationalCompatibilityError

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_]+$")


@dataclass(frozen=True, slots=True)
class MySQLConnectionSettings:
    """Parsed control-plane connection settings kept outside portable artifacts."""

    host: str
    port: int
    user: str
    password: str
    database: str

    @classmethod
    def from_dsn(cls, dsn: str) -> "MySQLConnectionSettings":
        parsed = urlsplit(dsn)
        if parsed.scheme != "mysql":
            raise ValueError("MySQL control DSN must use the mysql:// scheme")
        if not parsed.hostname or parsed.username is None or parsed.password is None:
            raise ValueError("MySQL control DSN must include host, user, and password")
        database = parsed.path.lstrip("/") or "mysql"
        return cls(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=unquote(parsed.username),
            password=unquote(parsed.password),
            database=unquote(database),
        )

    def with_principal(
        self,
        *,
        user: str,
        password: str,
        database: str,
    ) -> "MySQLConnectionSettings":
        return replace(self, user=user, password=password, database=database)


def driver() -> Any:
    """Load Oracle's optional MySQL Connector only when this backend is selected."""

    try:
        return importlib.import_module("mysql.connector")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "MySQL support requires the optional 'mysql' dependency"
        ) from exc


def connect(
    settings: MySQLConnectionSettings,
    *,
    autocommit: bool = False,
) -> Any:
    """Open one strict UTF-8 MySQL session with deterministic UTC time semantics."""

    connector = driver()
    connection = connector.connect(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        database=settings.database,
        charset="utf8mb4",
        use_unicode=True,
        autocommit=autocommit,
    )
    cursor = connection.cursor()
    try:
        cursor.execute("SET SESSION time_zone = '+00:00'")
        cursor.execute("SET SESSION sql_mode = 'STRICT_ALL_TABLES'")
    finally:
        cursor.close()
    return connection


def quote_identifier(value: str) -> str:
    """Quote only generated physical identifiers; logical AVP ids never enter SQL."""

    if not _IDENTIFIER_RE.fullmatch(value):
        raise RelationalCompatibilityError(
            "implementation-generated MySQL identifier is not safely quotable"
        )
    return f"`{value}`"


def account_sql(user: str, host: str = "%") -> str:
    """Render a generated MySQL account identity without accepting arbitrary SQL."""

    if not _IDENTIFIER_RE.fullmatch(user):
        raise RelationalCompatibilityError("generated MySQL account name is invalid")
    if host != "%":
        raise RelationalCompatibilityError("unexpected MySQL account host")
    return f"'{user}'@'{host}'"

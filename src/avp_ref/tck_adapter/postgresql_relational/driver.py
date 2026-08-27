"""Implementation-private PostgreSQL driver helpers.

The PostgreSQL dependency is optional. Importing the relational adapter package
must therefore remain safe for base-wheel consumers that did not install the
``postgresql`` extra.
"""

from __future__ import annotations

import importlib
from typing import Any


def load_driver() -> tuple[Any, Any]:
    """Load Psycopg and its SQL composition module only when PostgreSQL is used."""

    try:
        psycopg = importlib.import_module("psycopg")
        sql = importlib.import_module("psycopg.sql")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PostgreSQL support requires the optional 'postgresql' dependency"
        ) from exc
    return psycopg, sql

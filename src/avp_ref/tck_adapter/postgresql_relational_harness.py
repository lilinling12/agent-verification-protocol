"""Compatibility facade for the packaged PostgreSQL relational adapter.

New implementation code lives under :mod:`postgresql_relational`. This module
retains the original import path used by existing consumers and conformance tests
without duplicating backend behavior.
"""

from .postgresql_relational import (
    PostgreSQLRelationalBackendHarness,
    PostgreSQLRelationalResource,
)

__all__ = ["PostgreSQLRelationalBackendHarness", "PostgreSQLRelationalResource"]

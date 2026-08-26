"""Compatibility import for the structured MySQL relational backend package."""

from .mysql_relational import MySQLRelationalBackendHarness, MySQLRelationalResource

__all__ = ["MySQLRelationalBackendHarness", "MySQLRelationalResource"]

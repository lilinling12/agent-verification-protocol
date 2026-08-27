"""PostgreSQL implementation package for relational conformance.

The package is implementation evidence only. Portable AVP relational semantics
remain defined by the normative specification, schemas, and backend-neutral TCK.
"""

from .harness import PostgreSQLRelationalBackendHarness
from .resource import PostgreSQLRelationalResource

__all__ = ["PostgreSQLRelationalBackendHarness", "PostgreSQLRelationalResource"]

"""Canonical AVP scalar <-> PostgreSQL representation mapping.

This module implements backend mechanics only. The accepted AVP relational type
vocabulary and lexical rules remain defined by the normative Relational State
contract and are validated by the shared reference-domain validator.
"""

from __future__ import annotations

import base64
import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any

from avp_ref.relational import (
    ColumnDefinition,
    InMemoryRelationalResource,
    RelationalCompatibilityError,
    RelationalValue,
    ValueType,
)


def sql_type(column: ColumnDefinition, sql: Any) -> Any:
    """Return the exact PostgreSQL type used for one portable AVP column."""

    kind = column.value_type.kind
    if kind is ValueType.BOOLEAN:
        return sql.SQL("boolean")
    if kind is ValueType.INTEGER:
        # Portable v0.1 integers may exceed bigint. NUMERIC(65,0) preserves
        # the complete accepted lexical domain without narrowing AVP semantics.
        return sql.SQL("numeric(65,0)")
    if kind is ValueType.DECIMAL:
        return sql.SQL(
            f"numeric({column.value_type.precision},{column.value_type.scale})"
        )
    if kind is ValueType.TEXT:
        return sql.SQL("text")
    if kind is ValueType.BINARY:
        return sql.SQL("bytea")
    if kind is ValueType.DATE:
        return sql.SQL("date")

    precision = column.value_type.fractional_precision
    if kind is ValueType.TIME_LOCAL:
        return sql.SQL(f"time({precision}) without time zone")
    if kind is ValueType.TIMESTAMP_LOCAL:
        return sql.SQL(f"timestamp({precision}) without time zone")
    if kind is ValueType.TIMESTAMP_INSTANT:
        return sql.SQL(f"timestamp({precision}) with time zone")
    if kind is ValueType.UUID:
        return sql.SQL("uuid")
    raise RelationalCompatibilityError(f"unsupported PostgreSQL value kind: {kind}")


def to_database(column: ColumnDefinition, value: RelationalValue) -> Any:
    """Convert one already-portable AVP value into its PostgreSQL bind value."""

    InMemoryRelationalResource._validate_value(column, value)
    raw = value.value
    if raw is None:
        return None

    kind = value.kind
    if kind is ValueType.BOOLEAN:
        return raw

    assert isinstance(raw, str)
    if kind in {ValueType.INTEGER, ValueType.DECIMAL}:
        return Decimal(raw)
    if kind is ValueType.TEXT:
        return raw
    if kind is ValueType.BINARY:
        padding = "=" * ((4 - len(raw) % 4) % 4)
        return base64.urlsafe_b64decode(raw + padding)
    if kind is ValueType.DATE:
        return date.fromisoformat(raw)
    if kind is ValueType.TIME_LOCAL:
        return time.fromisoformat(raw)
    if kind is ValueType.TIMESTAMP_LOCAL:
        return datetime.fromisoformat(raw)
    if kind is ValueType.TIMESTAMP_INSTANT:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if kind is ValueType.UUID:
        return uuid.UUID(raw)
    raise RelationalCompatibilityError(f"unsupported PostgreSQL value kind: {kind}")


def from_database(column: ColumnDefinition, raw: Any) -> RelationalValue:
    """Decode a PostgreSQL value and revalidate the exact AVP canonical form."""

    kind = column.value_type.kind
    if raw is None:
        result = RelationalValue(kind, None)
    elif kind is ValueType.BOOLEAN:
        result = RelationalValue(kind, bool(raw))
    elif kind is ValueType.INTEGER:
        decimal = raw if isinstance(raw, Decimal) else Decimal(raw)
        result = RelationalValue(kind, format(decimal, "f"))
    elif kind is ValueType.DECIMAL:
        decimal = raw if isinstance(raw, Decimal) else Decimal(raw)
        scale = column.value_type.scale or 0
        result = RelationalValue(kind, f"{decimal:.{scale}f}")
    elif kind is ValueType.TEXT:
        result = RelationalValue(kind, str(raw))
    elif kind is ValueType.BINARY:
        encoded = base64.urlsafe_b64encode(bytes(raw)).decode("ascii").rstrip("=")
        result = RelationalValue(kind, encoded)
    elif kind is ValueType.DATE:
        result = RelationalValue(kind, raw.isoformat())
    elif kind is ValueType.TIME_LOCAL:
        result = RelationalValue(
            kind,
            _fractional_time(raw, column.value_type.fractional_precision or 0),
        )
    elif kind is ValueType.TIMESTAMP_LOCAL:
        result = RelationalValue(
            kind,
            _fractional_timestamp(
                raw,
                column.value_type.fractional_precision or 0,
                instant=False,
            ),
        )
    elif kind is ValueType.TIMESTAMP_INSTANT:
        result = RelationalValue(
            kind,
            _fractional_timestamp(
                raw,
                column.value_type.fractional_precision or 0,
                instant=True,
            ),
        )
    elif kind is ValueType.UUID:
        result = RelationalValue(kind, str(raw).lower())
    else:
        raise RelationalCompatibilityError(
            f"unsupported PostgreSQL value kind: {kind}"
        )

    # Decode success is insufficient. The shared validator proves that the
    # round-tripped representation still belongs to the portable closed domain.
    InMemoryRelationalResource._validate_value(column, result)
    return result


def _fractional_time(value: time, precision: int) -> str:
    base = value.strftime("%H:%M:%S")
    if precision == 0:
        return base
    return f"{base}.{value.microsecond:06d}"[: len(base) + 1 + precision]


def _fractional_timestamp(value: datetime, precision: int, *, instant: bool) -> str:
    if instant:
        if value.tzinfo is None:
            raise RelationalCompatibilityError(
                "PostgreSQL returned an unzoned timestamp for timestamp-instant"
            )
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    elif value.tzinfo is not None:
        raise RelationalCompatibilityError(
            "PostgreSQL returned a zoned timestamp for timestamp-local"
        )

    base = value.strftime("%Y-%m-%dT%H:%M:%S")
    if precision:
        base = f"{base}.{value.microsecond:06d}"[: len(base) + 1 + precision]
    return base + ("Z" if instant else "")

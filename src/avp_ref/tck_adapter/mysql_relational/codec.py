"""Lossless AVP scalar encoding for MySQL/InnoDB."""

from __future__ import annotations

import base64
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any

from avp_ref.relational import (
    ColumnDefinition,
    InMemoryRelationalResource,
    RelationalCompatibilityError,
    RelationalValue,
    ValueType,
)


def sql_type(column: ColumnDefinition) -> str:
    """Return a storage type that does not narrow the portable v0.1 domain."""

    kind = column.value_type.kind
    if kind is ValueType.BOOLEAN:
        return "TINYINT(1)"
    if kind is ValueType.INTEGER:
        return "DECIMAL(65,0)"
    if kind is ValueType.DECIMAL:
        return f"DECIMAL({column.value_type.precision},{column.value_type.scale})"
    if kind is ValueType.TEXT:
        return "LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin"
    if kind is ValueType.BINARY:
        return "LONGBLOB"
    if kind is ValueType.DATE:
        return "DATE"
    precision = column.value_type.fractional_precision
    if kind is ValueType.TIME_LOCAL:
        return f"TIME({precision})"
    if kind in {ValueType.TIMESTAMP_LOCAL, ValueType.TIMESTAMP_INSTANT}:
        # DATETIME avoids MySQL TIMESTAMP's narrower historical date domain.
        # Instant values are normalized to UTC by this codec and session policy.
        return f"DATETIME({precision})"
    if kind is ValueType.UUID:
        return "BINARY(16)"
    raise RelationalCompatibilityError(f"unsupported MySQL value kind: {kind}")


def to_database(column: ColumnDefinition, value: RelationalValue) -> Any:
    """Encode one canonical AVP value without backend-defined normalization."""

    InMemoryRelationalResource._validate_value(column, value)
    raw = value.value
    if raw is None:
        return None
    kind = value.kind
    if kind is ValueType.BOOLEAN:
        return 1 if raw else 0
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
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(
            timezone.utc
        ).replace(tzinfo=None)
    if kind is ValueType.UUID:
        return uuid.UUID(raw).bytes
    raise RelationalCompatibilityError(f"unsupported MySQL value kind: {kind}")


def _fractional_time(value: time | timedelta, precision: int) -> str:
    if isinstance(value, timedelta):
        total_microseconds = (
            value.days * 86_400_000_000
            + value.seconds * 1_000_000
            + value.microseconds
        )
        if not 0 <= total_microseconds < 86_400_000_000:
            raise RelationalCompatibilityError(
                "MySQL returned TIME outside the portable local-time domain"
            )
        hours, remainder = divmod(total_microseconds, 3_600_000_000)
        minutes, remainder = divmod(remainder, 60_000_000)
        seconds, microseconds = divmod(remainder, 1_000_000)
        base = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        base = value.strftime("%H:%M:%S")
        microseconds = value.microsecond
    if precision == 0:
        return base
    return f"{base}.{microseconds:06d}"[: len(base) + 1 + precision]


def _fractional_timestamp(value: datetime, precision: int, *, instant: bool) -> str:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    base = value.strftime("%Y-%m-%dT%H:%M:%S")
    if precision:
        base = f"{base}.{value.microsecond:06d}"[: len(base) + 1 + precision]
    return base + ("Z" if instant else "")


def from_database(column: ColumnDefinition, raw: Any) -> RelationalValue:
    """Decode one MySQL value and revalidate its canonical AVP lexical form."""

    kind = column.value_type.kind
    if raw is None:
        result = RelationalValue(kind, None)
    elif kind is ValueType.BOOLEAN:
        result = RelationalValue(kind, bool(raw))
    elif kind is ValueType.INTEGER:
        value = raw if isinstance(raw, Decimal) else Decimal(raw)
        result = RelationalValue(kind, format(value, "f"))
    elif kind is ValueType.DECIMAL:
        value = raw if isinstance(raw, Decimal) else Decimal(raw)
        scale = column.value_type.scale or 0
        result = RelationalValue(kind, f"{value:.{scale}f}")
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
        result = RelationalValue(kind, str(uuid.UUID(bytes=bytes(raw))).lower())
    else:
        raise RelationalCompatibilityError(f"unsupported MySQL value kind: {kind}")
    InMemoryRelationalResource._validate_value(column, result)
    return result

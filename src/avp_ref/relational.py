"""Backend-neutral reference model for AVP Relational State.

This module is downstream of ``spec/relational/relational-state-contract.md``.
It demonstrates portable observable semantics only. Database products, SQL,
driver APIs, catalog formats, and transaction tokens are intentionally absent
and must never become protocol authority through this implementation.
"""

from __future__ import annotations

import base64
import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Iterable, Mapping, Sequence

from .canonical import canonical_json


class RelationalError(RuntimeError):
    """Base error for fail-closed portable relational operations."""


class RelationalCompatibilityError(RelationalError):
    """The selected logical or execution binding cannot satisfy the profile."""


class RelationalReferenceError(RelationalError):
    """An Environment/resource/Snapshot reference is stale or foreign."""


class RelationalVisibilityError(RelationalError):
    """A Subject-visible operation attempted to disclose private state."""


class RelationalLifecycleError(RelationalError):
    """A relational operation violates the Core lifecycle boundary."""


class ValueType(str, Enum):
    BOOLEAN = "boolean"
    INTEGER = "integer"
    DECIMAL = "decimal"
    TEXT = "text"
    BINARY = "binary"
    DATE = "date"
    TIME_LOCAL = "time-local"
    TIMESTAMP_LOCAL = "timestamp-local"
    TIMESTAMP_INSTANT = "timestamp-instant"
    UUID = "uuid"


class RestoreFidelity(str, Enum):
    STATE_EQUIVALENT = "STATE_EQUIVALENT"
    NON_EQUIVALENT = "NON_EQUIVALENT"


_INTEGER_RE = re.compile(r"^(0|-?[1-9][0-9]{0,64})$")
_DECIMAL_RE = re.compile(r"^(0|-[1-9][0-9]*|[1-9][0-9]*)(?:\.([0-9]+))?$")
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
_TIME_RE = re.compile(
    r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.([0-9]{1,6}))?$"
)
_LOCAL_TS_RE = re.compile(
    r"^([1-9][0-9]{3}-[0-9]{2}-[0-9]{2})T"
    r"((?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.[0-9]{1,6})?)$"
)
_INSTANT_TS_RE = re.compile(
    r"^([1-9][0-9]{3}-[0-9]{2}-[0-9]{2})T"
    r"((?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.[0-9]{1,6})?)Z$"
)


def _canonical_bytes(value: object) -> bytes:
    """Canonicalize the restricted JSON value space emitted by this model.

    Exact relational numerics are strings, so the repository's compact sorted
    JSON serializer produces the same bytes as RFC 8785 for values emitted by
    this module. RFC 8785 itself remains the normative definition.
    """

    return canonical_json(value).encode("utf-8")


def _sha256(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class ColumnType:
    """Closed portable type parameters from AVP-RELATIONAL-003."""

    kind: ValueType
    precision: int | None = None
    scale: int | None = None
    fractional_precision: int | None = None

    def __post_init__(self) -> None:
        if self.kind is ValueType.DECIMAL:
            if self.precision is None or not 1 <= self.precision <= 65:
                raise RelationalCompatibilityError("decimal precision must be within 1..65")
            if (
                self.scale is None
                or not 0 <= self.scale <= 30
                or self.scale > self.precision
            ):
                raise RelationalCompatibilityError(
                    "decimal scale must be within 0..30 and <= precision"
                )
        elif self.precision is not None or self.scale is not None:
            raise RelationalCompatibilityError(
                "precision and scale are valid only for decimal"
            )

        temporal = {
            ValueType.TIME_LOCAL,
            ValueType.TIMESTAMP_LOCAL,
            ValueType.TIMESTAMP_INSTANT,
        }
        if self.kind in temporal:
            if self.fractional_precision is None or not 0 <= self.fractional_precision <= 6:
                raise RelationalCompatibilityError(
                    "temporal fractional precision must be within 0..6"
                )
        elif self.fractional_precision is not None:
            raise RelationalCompatibilityError(
                "fractional precision is valid only for temporal types"
            )


@dataclass(frozen=True, slots=True)
class ColumnDefinition:
    column_id: str
    value_type: ColumnType
    nullable: bool = False


@dataclass(frozen=True, slots=True)
class RelationalValue:
    """One canonical typed relational value."""

    kind: ValueType
    value: bool | str | None

    def as_document(self) -> dict[str, object]:
        return {"type": self.kind.value, "value": self.value}


@dataclass(frozen=True, slots=True)
class RelationalRow:
    """Immutable logical row with Manifest-derived canonical key metadata."""

    values: tuple[tuple[str, RelationalValue], ...]
    key_columns: tuple[str, ...] = ()

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, RelationalValue],
        *,
        key_columns: Sequence[str] = (),
    ) -> "RelationalRow":
        return cls(tuple(sorted(values.items())), tuple(sorted(key_columns)))

    def value_map(self) -> dict[str, RelationalValue]:
        return dict(self.values)

    def key_document(self) -> dict[str, object]:
        if not self.key_columns:
            raise RelationalCompatibilityError(
                "row has not been bound to a Manifest logical key"
            )
        values = self.value_map()
        return {
            column_id: values[column_id].as_document()
            for column_id in self.key_columns
        }


@dataclass(frozen=True, slots=True)
class RelationDefinition:
    relation_id: str
    columns: tuple[ColumnDefinition, ...]
    row_key: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.row_key:
            raise RelationalCompatibilityError("relation row key must not be empty")
        column_ids = tuple(column.column_id for column in self.columns)
        if len(column_ids) != len(set(column_ids)):
            raise RelationalCompatibilityError("relation column ids must be unique")
        if not set(self.row_key).issubset(column_ids):
            raise RelationalCompatibilityError(
                "row key must reference declared relation columns"
            )


@dataclass(frozen=True, slots=True)
class ProjectionRelation:
    relation_id: str
    columns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectionDefinition:
    projection_id: str
    relations: tuple[ProjectionRelation, ...]


@dataclass(frozen=True, slots=True)
class RelationalManifest:
    relations: tuple[RelationDefinition, ...]
    projections: tuple[ProjectionDefinition, ...] = ()

    def relation(self, relation_id: str) -> RelationDefinition:
        for relation in self.relations:
            if relation.relation_id == relation_id:
                return relation
        raise RelationalCompatibilityError(f"unknown logical relation: {relation_id}")

    def projection(self, projection_id: str) -> ProjectionDefinition:
        for projection in self.projections:
            if projection.projection_id == projection_id:
                return projection
        raise RelationalCompatibilityError(f"unknown projection: {projection_id}")


@dataclass(frozen=True, slots=True)
class StateImage:
    manifest_digest: str
    relations: tuple[tuple[str, tuple[RelationalRow, ...]], ...]

    def as_document(self) -> dict[str, object]:
        return {
            "apiVersion": "avp.relational/v0.1",
            "kind": "RelationalStateImage",
            "manifestDigest": self.manifest_digest,
            "relations": [
                {
                    "relationId": relation_id,
                    "rows": [
                        {
                            "key": row.key_document(),
                            "values": {
                                column_id: value.as_document()
                                for column_id, value in row.values
                            },
                        }
                        for row in rows
                    ],
                }
                for relation_id, rows in self.relations
            ],
        }

    @property
    def digest(self) -> str:
        return _sha256(self.as_document())


@dataclass(frozen=True, slots=True)
class RelationalSnapshot:
    snapshot_id: str
    environment_id: str
    resource_id: str
    state: StateImage


@dataclass(frozen=True, slots=True)
class DiffChange:
    relation_id: str
    change: str
    key_bytes: bytes


@dataclass(frozen=True, slots=True)
class RelationalDiff:
    changes: tuple[DiffChange, ...]


@dataclass(slots=True)
class _PendingMutation:
    relation_id: str
    replacement: tuple[RelationalRow, ...]
    settled: bool = False
    committed: bool = False


class InMemoryRelationalResource:
    """Backend-neutral SUT used by the relational candidate TCK."""

    def __init__(
        self,
        *,
        environment_id: str,
        resource_id: str,
        manifest: RelationalManifest,
        manifest_digest: str,
        baseline: Mapping[str, Sequence[RelationalRow]],
        execution_input_identity: str,
        evaluator_private_columns: Iterable[tuple[str, str]] = (),
    ) -> None:
        self.environment_id = environment_id
        self.resource_id = resource_id
        self.manifest = manifest
        self.manifest_digest = manifest_digest
        self.execution_input_identity = execution_input_identity
        self._bound_execution_identity = execution_input_identity
        self._private_columns = frozenset(evaluator_private_columns)
        self._logical_binding_valid = True
        self._quiescing = False
        self._released = False
        self._pending: list[_PendingMutation] = []
        self._baseline = self._validate_state(baseline)
        self._state = dict(self._baseline)
        self._snapshot_sequence = 0

    def _ensure_live(self) -> None:
        if self._released:
            raise RelationalReferenceError(
                "relational resource reference is released"
            )
        if not self._logical_binding_valid:
            raise RelationalCompatibilityError(
                "logical relational binding has drifted"
            )
        if self.execution_input_identity != self._bound_execution_identity:
            raise RelationalCompatibilityError(
                "execution-relevant database input identity has drifted"
            )

    def _validate_state(
        self,
        state: Mapping[str, Sequence[RelationalRow]],
    ) -> dict[str, tuple[RelationalRow, ...]]:
        expected_relations = {
            relation.relation_id for relation in self.manifest.relations
        }
        if set(state) != expected_relations:
            raise RelationalCompatibilityError(
                "state does not cover exactly the Manifest relations"
            )

        result: dict[str, tuple[RelationalRow, ...]] = {}
        for relation in self.manifest.relations:
            expected_columns = {column.column_id for column in relation.columns}
            validated: list[tuple[bytes, RelationalRow]] = []
            seen_keys: set[bytes] = set()
            for row in state[relation.relation_id]:
                values = row.value_map()
                if set(values) != expected_columns:
                    raise RelationalCompatibilityError(
                        "row does not cover exactly the Manifest columns"
                    )
                for column in relation.columns:
                    self._validate_value(column, values[column.column_id])

                bound_row = RelationalRow.from_mapping(
                    values,
                    key_columns=relation.row_key,
                )
                key_bytes = _canonical_bytes(bound_row.key_document())
                if key_bytes in seen_keys:
                    raise RelationalCompatibilityError(
                        "duplicate logical row key"
                    )
                seen_keys.add(key_bytes)
                validated.append((key_bytes, bound_row))

            validated.sort(key=lambda pair: pair[0])
            result[relation.relation_id] = tuple(row for _, row in validated)
        return result

    @staticmethod
    def _validate_value(
        column: ColumnDefinition,
        value: RelationalValue,
    ) -> None:
        if value.kind is not column.value_type.kind:
            raise RelationalCompatibilityError(
                "typed value does not match Manifest column type"
            )
        if value.value is None:
            if not column.nullable:
                raise RelationalCompatibilityError(
                    "null supplied for non-nullable column"
                )
            return

        raw = value.value
        kind = value.kind
        if kind is ValueType.BOOLEAN:
            if not isinstance(raw, bool):
                raise RelationalCompatibilityError(
                    "boolean value must be JSON boolean"
                )
            return
        if not isinstance(raw, str):
            raise RelationalCompatibilityError(
                "non-boolean relational values must use canonical strings"
            )

        if kind is ValueType.INTEGER:
            if not _INTEGER_RE.fullmatch(raw):
                raise RelationalCompatibilityError("non-canonical integer")
        elif kind is ValueType.DECIMAL:
            InMemoryRelationalResource._validate_decimal(column, raw)
        elif kind is ValueType.TEXT:
            try:
                raw.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise RelationalCompatibilityError(
                    "text contains invalid Unicode scalar data"
                ) from exc
        elif kind is ValueType.BINARY:
            InMemoryRelationalResource._validate_binary(raw)
        elif kind is ValueType.DATE:
            InMemoryRelationalResource._validate_date(raw)
        elif kind is ValueType.TIME_LOCAL:
            InMemoryRelationalResource._validate_local_time(
                raw,
                column.value_type.fractional_precision or 0,
            )
        elif kind is ValueType.TIMESTAMP_LOCAL:
            InMemoryRelationalResource._validate_timestamp(
                raw,
                column.value_type.fractional_precision or 0,
                instant=False,
            )
        elif kind is ValueType.TIMESTAMP_INSTANT:
            InMemoryRelationalResource._validate_timestamp(
                raw,
                column.value_type.fractional_precision or 0,
                instant=True,
            )
        elif kind is ValueType.UUID and not _UUID_RE.fullmatch(raw):
            raise RelationalCompatibilityError("non-canonical UUID")

    @staticmethod
    def _validate_decimal(column: ColumnDefinition, raw: str) -> None:
        match = _DECIMAL_RE.fullmatch(raw)
        if match is None:
            raise RelationalCompatibilityError("non-canonical decimal")
        fraction = match.group(1) or ""
        if len(fraction) != (column.value_type.scale or 0):
            raise RelationalCompatibilityError(
                "decimal lexical scale differs from Manifest"
            )
        try:
            decimal = Decimal(raw)
        except InvalidOperation as exc:
            raise RelationalCompatibilityError("invalid decimal") from exc
        if len(decimal.as_tuple().digits) > (column.value_type.precision or 0):
            raise RelationalCompatibilityError(
                "decimal exceeds Manifest precision"
            )
        if decimal.is_zero() and raw.startswith("-"):
            raise RelationalCompatibilityError(
                "negative decimal zero is non-canonical"
            )

    @staticmethod
    def _validate_binary(raw: str) -> None:
        if "=" in raw:
            raise RelationalCompatibilityError(
                "base64url padding is non-canonical"
            )
        try:
            padding = "=" * ((4 - len(raw) % 4) % 4)
            decoded = base64.urlsafe_b64decode(raw + padding)
        except (ValueError, base64.binascii.Error) as exc:
            raise RelationalCompatibilityError("invalid base64url") from exc
        encoded = base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=")
        if encoded != raw:
            raise RelationalCompatibilityError("non-canonical base64url")

    @staticmethod
    def _validate_date(raw: str) -> None:
        try:
            parsed = date.fromisoformat(raw)
        except ValueError as exc:
            raise RelationalCompatibilityError(
                "invalid Gregorian date"
            ) from exc
        if len(raw) != 10 or not 1000 <= parsed.year <= 9999:
            raise RelationalCompatibilityError(
                "date outside portable v0.1 range"
            )

    @staticmethod
    def _validate_local_time(raw: str, precision: int) -> None:
        match = _TIME_RE.fullmatch(raw)
        if match is None:
            raise RelationalCompatibilityError("invalid time-local")
        fraction = match.group(1) or ""
        if len(fraction) != precision:
            raise RelationalCompatibilityError(
                "temporal lexical precision differs from Manifest"
            )
        time.fromisoformat(raw)

    @staticmethod
    def _validate_timestamp(
        raw: str,
        precision: int,
        *,
        instant: bool,
    ) -> None:
        match = (_INSTANT_TS_RE if instant else _LOCAL_TS_RE).fullmatch(raw)
        if match is None:
            kind = "timestamp-instant" if instant else "timestamp-local"
            raise RelationalCompatibilityError(f"invalid {kind}")
        parsed_date = date.fromisoformat(match.group(1))
        if not 1000 <= parsed_date.year <= 9999:
            raise RelationalCompatibilityError(
                "timestamp outside portable year range"
            )
        InMemoryRelationalResource._validate_local_time(
            match.group(2),
            precision,
        )
        if instant:
            datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(
                timezone.utc
            )

    @staticmethod
    def _row_key_bytes(
        relation: RelationDefinition,
        row: RelationalRow,
    ) -> bytes:
        values = row.value_map()
        key: dict[str, object] = {}
        for column_id in sorted(relation.row_key):
            value = values[column_id]
            if value.value is None:
                raise RelationalCompatibilityError(
                    "logical row key cannot contain null"
                )
            key[column_id] = value.as_document()
        return _canonical_bytes(key)

    def state_image(self) -> StateImage:
        self._ensure_live()
        return StateImage(
            self.manifest_digest,
            tuple(
                (relation.relation_id, self._state[relation.relation_id])
                for relation in sorted(
                    self.manifest.relations,
                    key=lambda item: item.relation_id,
                )
            ),
        )

    def project(self, projection_id: str) -> dict[str, object]:
        self._ensure_live()
        projection = self.manifest.projection(projection_id)
        relations: list[dict[str, object]] = []
        for selected in sorted(
            projection.relations,
            key=lambda item: item.relation_id,
        ):
            relation = self.manifest.relation(selected.relation_id)
            selected_columns = set(selected.columns)
            if not set(relation.row_key).issubset(selected_columns):
                raise RelationalCompatibilityError(
                    "projection omits required logical key column"
                )
            rows: list[dict[str, object]] = []
            for row in self._state[relation.relation_id]:
                values = row.value_map()
                rows.append(
                    {
                        "key": {
                            column_id: values[column_id].as_document()
                            for column_id in sorted(relation.row_key)
                        },
                        "values": {
                            column_id: values[column_id].as_document()
                            for column_id in sorted(selected_columns)
                        },
                    }
                )
            relations.append(
                {"relationId": relation.relation_id, "rows": rows}
            )
        return {
            "apiVersion": "avp.relational/v0.1",
            "kind": "RelationalProjection",
            "manifestDigest": self.manifest_digest,
            "projectionId": projection_id,
            "relations": relations,
        }

    def begin_subject_mutation(
        self,
        relation_id: str,
        replacement: Sequence[RelationalRow],
    ) -> _PendingMutation:
        self._ensure_live()
        if self._quiescing:
            raise RelationalLifecycleError(
                "new Subject mutation rejected after QUIESCING"
            )
        candidate = dict(self._state)
        candidate[relation_id] = tuple(replacement)
        validated = self._validate_state(candidate)
        pending = _PendingMutation(relation_id, validated[relation_id])
        self._pending.append(pending)
        return pending

    def settle_subject_mutation(
        self,
        pending: _PendingMutation,
        *,
        commit: bool,
    ) -> None:
        self._ensure_live()
        if pending not in self._pending or pending.settled:
            raise RelationalLifecycleError("mutation is not pending")
        if commit:
            self._state[pending.relation_id] = pending.replacement
            pending.committed = True
        pending.settled = True

    def enter_quiescing(self) -> None:
        self._ensure_live()
        self._quiescing = True

    @property
    def settlement_complete(self) -> bool:
        return all(pending.settled for pending in self._pending)

    def final_projection(self, projection_id: str) -> dict[str, object]:
        self._ensure_live()
        if not self._quiescing or not self.settlement_complete:
            raise RelationalLifecycleError(
                "final projection requires settled QUIESCING boundary"
            )
        return self.project(projection_id)

    def snapshot(self) -> RelationalSnapshot:
        state = self.state_image()
        self._snapshot_sequence += 1
        return RelationalSnapshot(
            snapshot_id=f"relational-snapshot-{self._snapshot_sequence}",
            environment_id=self.environment_id,
            resource_id=self.resource_id,
            state=state,
        )

    def reset(self) -> StateImage:
        self._ensure_live()
        self._state = dict(self._baseline)
        observed = self.state_image()
        baseline = StateImage(
            self.manifest_digest,
            tuple(
                (relation.relation_id, self._baseline[relation.relation_id])
                for relation in sorted(
                    self.manifest.relations,
                    key=lambda item: item.relation_id,
                )
            ),
        )
        if observed.digest != baseline.digest:
            raise RelationalError(
                "reset did not re-establish baseline StateImage identity"
            )
        return observed

    def restore(self, snapshot: RelationalSnapshot) -> RestoreFidelity:
        self._ensure_live()
        self._validate_snapshot_owner(snapshot)
        self._state = {
            relation_id: tuple(rows)
            for relation_id, rows in snapshot.state.relations
        }
        observed = self.state_image()
        if observed.digest != snapshot.state.digest:
            return RestoreFidelity.NON_EQUIVALENT
        return RestoreFidelity.STATE_EQUIVALENT

    def _validate_snapshot_owner(self, snapshot: RelationalSnapshot) -> None:
        if (
            snapshot.environment_id != self.environment_id
            or snapshot.resource_id != self.resource_id
        ):
            raise RelationalReferenceError("foreign relational SnapshotRef")
        if snapshot.state.manifest_digest != self.manifest_digest:
            raise RelationalReferenceError(
                "snapshot Manifest identity mismatch"
            )

    def set_logical_binding_valid(self, valid: bool) -> None:
        self._logical_binding_valid = valid

    def set_execution_input_identity(self, identity: str) -> None:
        self.execution_input_identity = identity

    def subject_view(
        self,
        authorized: Iterable[tuple[str, str]],
    ) -> dict[str, tuple[RelationalRow, ...]]:
        self._ensure_live()
        allowed = frozenset(authorized)
        if self._private_columns & allowed:
            raise RelationalVisibilityError(
                "Subject authorization includes evaluator-private column"
            )
        result: dict[str, tuple[RelationalRow, ...]] = {}
        for relation in self.manifest.relations:
            selected = {
                column_id
                for relation_id, column_id in allowed
                if relation_id == relation.relation_id
            }
            if not selected:
                continue
            rows: list[RelationalRow] = []
            for row in self._state[relation.relation_id]:
                values = row.value_map()
                rows.append(
                    RelationalRow.from_mapping(
                        {column_id: values[column_id] for column_id in selected}
                    )
                )
            result[relation.relation_id] = tuple(rows)
        return result

    def diff(self, before: StateImage, after: StateImage) -> RelationalDiff:
        if (
            before.manifest_digest != self.manifest_digest
            or after.manifest_digest != self.manifest_digest
        ):
            raise RelationalCompatibilityError(
                "cross-Manifest comparison is not relational row diff"
            )
        before_map = dict(before.relations)
        after_map = dict(after.relations)
        changes: list[DiffChange] = []
        for relation in sorted(
            self.manifest.relations,
            key=lambda item: item.relation_id,
        ):
            old_rows = {
                self._row_key_bytes(relation, row): row
                for row in before_map[relation.relation_id]
            }
            new_rows = {
                self._row_key_bytes(relation, row): row
                for row in after_map[relation.relation_id]
            }
            for key in sorted(old_rows.keys() | new_rows.keys()):
                if key not in old_rows:
                    changes.append(
                        DiffChange(relation.relation_id, "INSERT", key)
                    )
                elif key not in new_rows:
                    changes.append(
                        DiffChange(relation.relation_id, "DELETE", key)
                    )
                elif old_rows[key] != new_rows[key]:
                    changes.append(
                        DiffChange(relation.relation_id, "UPDATE", key)
                    )
        return RelationalDiff(tuple(changes))

    def release(self) -> None:
        self._released = True


class TornProjectionResource(InMemoryRelationalResource):
    """Negative SUT returning a view impossible at one committed boundary."""

    def project(self, projection_id: str) -> dict[str, object]:
        document = super().project(projection_id)
        relations = document["relations"]
        assert isinstance(relations, list)
        if len(relations) >= 2:
            first_rows = relations[0]["rows"]
            second_rows = relations[1]["rows"]
            assert isinstance(first_rows, list)
            assert isinstance(second_rows, list)
            if first_rows and second_rows:
                first_rows[0]["values"]["epoch"] = {
                    "type": "integer",
                    "value": "1",
                }
                second_rows[0]["values"]["epoch"] = {
                    "type": "integer",
                    "value": "2",
                }
        return document


class FalseRestoreResource(InMemoryRelationalResource):
    """Negative SUT reporting restore success without restoring state."""

    def restore(self, snapshot: RelationalSnapshot) -> RestoreFidelity:
        self._ensure_live()
        self._validate_snapshot_owner(snapshot)
        return RestoreFidelity.STATE_EQUIVALENT


class HiddenStateLeakResource(InMemoryRelationalResource):
    """Negative SUT bypassing evaluator-private visibility enforcement."""

    def subject_view(
        self,
        authorized: Iterable[tuple[str, str]],
    ) -> dict[str, tuple[RelationalRow, ...]]:
        self._ensure_live()
        allowed = set(authorized) | set(self._private_columns)
        result: dict[str, tuple[RelationalRow, ...]] = {}
        for relation in self.manifest.relations:
            selected = {
                column_id
                for relation_id, column_id in allowed
                if relation_id == relation.relation_id
            }
            if not selected:
                continue
            rows: list[RelationalRow] = []
            for row in self._state[relation.relation_id]:
                values = row.value_map()
                rows.append(
                    RelationalRow.from_mapping(
                        {column_id: values[column_id] for column_id in selected}
                    )
                )
            result[relation.relation_id] = tuple(rows)
        return result


class ExecutionInputDriftResource(InMemoryRelationalResource):
    """Negative SUT intentionally suppressing execution-input drift failure."""

    def _ensure_live(self) -> None:
        if self._released:
            raise RelationalReferenceError(
                "relational resource reference is released"
            )
        if not self._logical_binding_valid:
            raise RelationalCompatibilityError(
                "logical relational binding has drifted"
            )

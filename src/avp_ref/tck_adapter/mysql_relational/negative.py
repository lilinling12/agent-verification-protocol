"""Metadata-equivalent negative MySQL SUTs used by executed conformance tests."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from avp_ref.relational import (
    RelationalCompatibilityError,
    RelationalReferenceError,
    RelationalRow,
    RelationalSnapshot,
    RestoreFidelity,
)

from ..relational_harness import NegativeControl
from .resource import MySQLRelationalResource


class TornMySQLResource(MySQLRelationalResource):
    """Negative SUT that returns a metadata-identical torn projection."""

    def project(self, projection_id: str) -> Mapping[str, object]:
        document = dict(super().project(projection_id))
        relations = document.get("relations")
        if isinstance(relations, list) and len(relations) >= 2:
            first_rows = relations[0].get("rows")
            second_rows = relations[1].get("rows")
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


class FalseRestoreMySQLResource(MySQLRelationalResource):
    """Negative SUT that claims restore without applying authoritative state."""

    def restore(self, snapshot: RelationalSnapshot) -> RestoreFidelity:
        self._ensure_live()
        self._validate_snapshot_owner(snapshot)
        return RestoreFidelity.STATE_EQUIVALENT


class HiddenLeakMySQLResource(MySQLRelationalResource):
    """Negative SUT that bypasses Subject visibility restrictions."""

    def subject_view(
        self,
        authorized: Iterable[tuple[str, str]],
    ) -> Mapping[str, tuple[RelationalRow, ...]]:
        del authorized
        return dict(self.state_image().relations)


class ExecutionDriftMySQLResource(MySQLRelationalResource):
    """Negative SUT that suppresses execution-input drift detection."""

    def _ensure_live(self) -> None:
        if self._released:
            raise RelationalReferenceError("relational resource reference is released")
        if not self._logical_binding_valid:
            raise RelationalCompatibilityError("logical relational binding has drifted")


NEGATIVE_RESOURCE_TYPES: Mapping[
    NegativeControl,
    type[MySQLRelationalResource],
] = {
    NegativeControl.TORN_PROJECTION: TornMySQLResource,
    NegativeControl.FALSE_RESTORE: FalseRestoreMySQLResource,
    NegativeControl.HIDDEN_STATE_LEAK: HiddenLeakMySQLResource,
    NegativeControl.EXECUTION_INPUT_DRIFT: ExecutionDriftMySQLResource,
}

"""Real-backend orchestration for the backend-neutral relational TCK evaluator."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from avp_ref.relational import RelationalRow, RelationalValue, ValueType

from .relational_harness import NegativeControl, RelationalBackendHarness
from .reference_relational import RelationalConformanceTCKAdapter


class RelationalBackendTCKAdapter(RelationalConformanceTCKAdapter):
    """Run relational assertions through fixture controls required by real backends.

    The semantic assertion remains backend-neutral: a multi-relation projection
    observed around one atomic commit may be fully before or fully after that
    commit, never torn. Backend-specific scheduling and transaction mechanics
    stay inside ``RelationalFixtureControl``.
    """

    def __init__(self, backend: RelationalBackendHarness) -> None:
        super().__init__(backend)

    def _projection(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        del vector
        resource = self._consistency_resource("projection-good")
        epoch_two = RelationalRow.from_mapping(
            {
                "id": RelationalValue(ValueType.INTEGER, "1"),
                "epoch": RelationalValue(ValueType.INTEGER, "2"),
            }
        )
        observed = self._epochs(
            self._fixture.project_during_atomic_commit(
                resource,
                projection_id="consistency.pair",
                replacements={
                    "consistency.left": (epoch_two,),
                    "consistency.right": (epoch_two,),
                },
            )
        )
        allowed = {(1, 1), (2, 2)}

        torn = self._consistency_resource(
            "projection-torn",
            negative_control=NegativeControl.TORN_PROJECTION,
        )
        torn_observed = self._epochs(torn.project("consistency.pair"))
        passed = observed in allowed and torn_observed not in allowed
        return passed, (
            "projection is one committed multi-relation view under coordinated commit and torn control is detectable"
            if passed
            else "projection accepted dirty/torn visibility or negative control escaped detection"
        )

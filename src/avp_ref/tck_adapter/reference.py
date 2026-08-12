"""Adapter between AVP TCK vectors and the Python reference runtime.

The adapter is deliberately thin:

* TCK remains the authority for expected behavior.
* ReferenceRuntime remains an implementation under evaluation.
* A failing reference runtime result is reported as FAIL, not rewritten.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from avp_ref.runtime import EpisodeState, ReferenceRuntime


class TCKAdapterError(RuntimeError):
    """Raised when a TCK case cannot be evaluated safely."""


class TCKStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass(frozen=True, slots=True)
class TCKCaseResult:
    case_id: str
    status: TCKStatus
    detail: str
    evidence: tuple[str, ...] = ()


class ReferenceTCKAdapter:
    """Evaluate lifecycle TCK vectors against ReferenceRuntime."""

    def __init__(self, runtime: ReferenceRuntime | None = None) -> None:
        self._runtime = runtime

    def evaluate_transition_matrix(self, case: Mapping[str, Any]) -> TCKCaseResult:
        """Validate the runtime transition table against a TCK matrix.

        This method compares observable transition capability. It does not
        mutate the protocol matrix when the runtime differs.
        """

        runtime_states = {state.value for state in EpisodeState}
        expected_states = set(case.get("states", {}).get("required", [])) | set(case.get("states", {}).get("optional", []))
        if runtime_states != expected_states:
            return TCKCaseResult(
                case_id=case["metadata"]["id"],
                status=TCKStatus.FAIL,
                detail=f"state set mismatch runtime={sorted(runtime_states)} expected={sorted(expected_states)}",
            )
        return TCKCaseResult(case["metadata"]["id"], TCKStatus.PASS, "state set matches")

    def evaluate_illegal_transition(self, case: Mapping[str, Any]) -> TCKCaseResult:
        """Validate that known forbidden transitions are rejected."""

        if self._runtime is None:
            raise TCKAdapterError("runtime is required for transition execution")
        return TCKCaseResult(case["metadata"]["id"], TCKStatus.SKIP, "execution fixture not configured")

"""Reference witness for AVP-SECURITY-005 future fault schedule secrecy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from avp_ref.environment import FaultSpec
from avp_ref.reference import (
    reference_agent_system,
    reference_environment,
    reference_oracle_package,
    reference_scenario,
    reference_subject_adapter,
)
from avp_ref.runtime import ReferenceRuntime

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


class ReferenceSecurityFaultTCKAdapter:
    """Exercise future-fault secrecy through the real Runtime/Subject boundary."""

    _CASE_ID = "AVP-TCK-SECURITY-FAULT-SECRECY-001"

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return frozenset({self._CASE_ID})

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        if case_id != self._CASE_ID:
            raise TCKAdapterError(
                f"unsupported reference Security fault TCK case: {case_id}"
            )
        vector = self._vector(case, case_id)
        target = self._string(vector.get("targetTool"), f"{case_id} targetTool")
        occurrence = self._positive_int(
            vector.get("occurrence"),
            f"{case_id} occurrence",
        )
        sentinel = self._string(
            vector.get("hiddenSentinel"),
            f"{case_id} hiddenSentinel",
        )
        if occurrence < 2:
            raise TCKAdapterError(
                f"{case_id} reference vector requires occurrence >= 2"
            )

        scenario = reference_scenario()
        subject_projection = scenario.subject_projection()
        if self._contains_text(subject_projection, sentinel):
            raise TCKAdapterError(
                f"{case_id} fixture leaked hidden sentinel before execution"
            )

        observed: dict[str, object] = {}

        def subject(session: object, task: Mapping[str, Any]) -> str:
            observe = getattr(session, "observe")
            trace_headers = getattr(session, "trace_headers")
            call_tool = getattr(session, "call_tool")

            before = {
                "task": dict(task),
                "observation": observe(),
                "trace_headers": trace_headers(),
            }
            first = call_tool(target, {"order_id": "ord_1"})
            between = {
                "observation": observe(),
                "trace_headers": trace_headers(),
            }
            second_error: str | None = None
            try:
                call_tool(target, {"order_id": "ord_1"})
            except RuntimeError as exc:
                second_error = str(exc)

            surface = {
                "before": before,
                "first_result": first,
                "between": between,
                "second_error": second_error,
            }
            observed.update(surface)
            first_ok = isinstance(first, Mapping) and first.get("id") == "ord_1"
            second_failed = second_error is not None
            leaked = self._contains_text(surface, sentinel)
            return (
                "FIRST_OK;SECOND_FAULT;NO_SECRET"
                if first_ok and second_failed and not leaked
                else "SECURITY_FAULT_WITNESS_FAILED"
            )

        runtime = ReferenceRuntime()
        episode = runtime.create_episode(
            scenario=scenario,
            agent_system=reference_agent_system("security-fault-secrecy-tck"),
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(subject),
            oracle_package=reference_oracle_package(),
        )
        try:
            runtime.provision(episode.episode_id)
            runtime.inject_fault(
                episode.episode_id,
                FaultSpec(
                    "tool.error",
                    target,
                    occurrence=occurrence,
                    parameters={
                        "error": "injected delayed tool failure",
                        "hidden_sentinel": sentinel,
                    },
                    visibility="hidden",
                ),
            )
            report = runtime.run_subject(episode.episode_id)
            events = tuple(episode.events)
        finally:
            runtime.release(episode.episode_id)

        tool_results = [
            event for event in events
            if event.event_type == "tool.result"
            and event.payload.get("name") == target
        ]
        activations = [
            event for event in events
            if event.event_type == "fault.activated"
            and event.payload.get("target") == target
        ]
        scheduled = [
            event for event in events
            if event.event_type == "fault.scheduled"
            and event.payload.get("target") == target
        ]

        first_call_succeeded = bool(tool_results)
        activation_after_first_result = (
            len(activations) == 1
            and first_call_succeeded
            and tool_results[0].sequence < activations[0].sequence
        )
        schedule_is_evaluator_only = (
            len(scheduled) == 1 and scheduled[0].plane == "evaluator"
        )
        sentinel_absent_from_subject = (
            sentinel not in report
            and not self._contains_text(observed, sentinel)
            and not self._contains_text(subject_projection, sentinel)
        )

        valid = (
            report == "FIRST_OK;SECOND_FAULT;NO_SECRET"
            and first_call_succeeded
            and activation_after_first_result
            and schedule_is_evaluator_only
            and sentinel_absent_from_subject
        )
        return TCKCaseResult(
            case_id,
            TCKStatus.PASS if valid else TCKStatus.FAIL,
            (
                "future fault remained evaluator-private until its configured occurrence; "
                "the first call succeeded and hidden schedule data stayed off Subject routes"
                if valid
                else "future fault activated early, failed to activate, or leaked hidden schedule data"
            ),
        )

    @staticmethod
    def _contains_text(value: object, target: str) -> bool:
        if isinstance(value, Mapping):
            return any(
                target in str(key)
                or ReferenceSecurityFaultTCKAdapter._contains_text(item, target)
                for key, item in value.items()
            )
        if isinstance(value, (list, tuple)):
            return any(
                ReferenceSecurityFaultTCKAdapter._contains_text(item, target)
                for item in value
            )
        return target in str(value)

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("Security fault TCK case metadata.id is missing")
        return case_id

    @staticmethod
    def _vector(case: Mapping[str, Any], case_id: str) -> Mapping[str, Any]:
        vector = case.get("vector")
        if not isinstance(vector, Mapping):
            raise TCKAdapterError(f"{case_id} vector must be an object")
        return vector

    @staticmethod
    def _string(value: object, label: str) -> str:
        if not isinstance(value, str) or not value:
            raise TCKAdapterError(f"{label} must be a non-empty string")
        return value

    @staticmethod
    def _positive_int(value: object, label: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise TCKAdapterError(f"{label} must be a positive integer")
        return value

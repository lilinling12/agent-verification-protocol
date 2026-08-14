"""Reference adapter for the AVP Subject Adapter v0.1 conformance profile."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from avp_ref.reference import (
    correct_subject,
    reference_agent_system,
    reference_scenario,
    reference_subject_adapter,
)
from avp_ref.runtime.subject_policy import SubjectExecutionDenied
from avp_ref.security import CapabilityGuardPolicy, CapabilityGuardedSubjectAdapter
from avp_ref.subject import (
    HTTPSubjectAdapter,
    InProcessSubjectAdapter,
    SubjectAdapterError,
    SubjectBudgetExceeded,
    SubjectExecutionError,
    SubjectInvocation,
    SubjectProtocolError,
    SubjectResult,
    SubjectStatus,
    SubjectTimeoutError,
    SubjectTransportError,
)

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


class _Gateway:
    """Small evaluator-owned gateway witness used by Subject TCK vectors."""

    def __init__(self) -> None:
        self.tool_calls: list[tuple[str, dict[str, Any]]] = []

    def observe(self) -> Mapping[str, Any]:
        return {"visible": True}

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Any:
        self.tool_calls.append((name, dict(arguments)))
        return {"ok": True, "name": name}

    def trace_headers(self) -> Mapping[str, str]:
        return {}


class _ScriptedHTTPSubjectAdapter(HTTPSubjectAdapter):
    """Exercise HTTP adapter semantics without depending on a network server."""

    def __init__(self, frames: list[object]) -> None:
        super().__init__("https://subject-tck.invalid")
        self._frames = list(frames)
        self.payloads: list[dict[str, Any]] = []

    def _post(
        self,
        payload: Mapping[str, Any],
        *,
        timeout: float,
        trace_headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        del timeout, trace_headers
        self.payloads.append(dict(payload))
        if not self._frames:
            raise SubjectTransportError("scripted Subject transport exhausted")
        frame = self._frames.pop(0)
        if isinstance(frame, Exception):
            raise frame
        if not isinstance(frame, dict):
            raise SubjectProtocolError("scripted Subject frame must be an object")
        return frame


class ReferenceSubjectTCKAdapter:
    """Execute language-neutral Subject vectors against real reference behavior."""

    _LIFECYCLE = "AVP-TCK-SUBJECT-LIFECYCLE-001"
    _PROJECTION = "AVP-TCK-SUBJECT-PROJECTION-001"
    _BUDGET = "AVP-TCK-SUBJECT-BUDGET-001"
    _CAPABILITY = "AVP-TCK-SUBJECT-CAPABILITY-001"
    _OUTCOME = "AVP-TCK-SUBJECT-OUTCOME-001"
    _RESULT = "AVP-TCK-SUBJECT-RESULT-001"
    _ASSURANCE = "AVP-TCK-SUBJECT-ASSURANCE-001"

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return frozenset(
            {
                self._LIFECYCLE,
                self._PROJECTION,
                self._BUDGET,
                self._CAPABILITY,
                self._OUTCOME,
                self._RESULT,
                self._ASSURANCE,
            }
        )

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        evaluator = {
            self._LIFECYCLE: self._lifecycle,
            self._PROJECTION: self._projection,
            self._BUDGET: self._budget,
            self._CAPABILITY: self._capability,
            self._OUTCOME: self._outcome,
            self._RESULT: self._result,
            self._ASSURANCE: self._assurance,
        }.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(
                f"unsupported reference Subject TCK case: {case_id}"
            )
        passed, detail = evaluator(vector)
        return TCKCaseResult(
            case_id,
            TCKStatus.PASS if passed else TCKStatus.FAIL,
            detail,
        )

    @staticmethod
    def _lifecycle(vector: Mapping[str, Any]) -> tuple[bool, str]:
        del vector
        adapter = reference_subject_adapter(correct_subject)
        agent = reference_agent_system("subject-tck-lifecycle")
        description = adapter.describe()
        handle = adapter.open(agent)

        stable_identity = description.identity_digest == adapter.describe().identity_digest
        bound_agent = handle.agent_system_digest == agent.identity_digest

        try:
            adapter.release(replace(handle, adapter_name="foreign-adapter"))
            owner_rejected = False
        except SubjectTransportError:
            owner_rejected = True

        try:
            adapter.release(
                replace(handle, agent_system_digest="sha256:" + "0" * 64)
            )
            agent_rejected = False
        except SubjectTransportError:
            agent_rejected = True

        adapter.release(handle)
        try:
            adapter.release(handle)
            stale_rejected = False
        except SubjectTransportError:
            stale_rejected = True

        passed = (
            stable_identity
            and bound_agent
            and owner_rejected
            and agent_rejected
            and stale_rejected
        )
        return passed, (
            "adapter identity, Agent binding, owner identity and released handles remain fail-closed"
            if passed
            else "Subject lifecycle identity or stale-handle semantics violated v0.1"
        )

    @staticmethod
    def _projection(vector: Mapping[str, Any]) -> tuple[bool, str]:
        scenario = reference_scenario()
        projection = scenario.subject_projection()
        protected = tuple(str(value) for value in vector.get("protectedMaterial", ()))
        task = projection.get("task", {})
        invocation = SubjectInvocation("ep_subject_projection", task, 1, 1.0)
        agent = replace(
            reference_agent_system("projection-witness", adapter="http"),
            metadata={marker: marker for marker in protected},
        )
        adapter = _ScriptedHTTPSubjectAdapter(
            [{"status": "completed", "report": "ok"}]
        )
        handle = adapter.open(agent)
        try:
            result = adapter.invoke(handle, invocation, _Gateway())
        finally:
            adapter.release(handle)
        payload = adapter.payloads[0]
        serialized = repr(payload)
        agent_projection = payload.get("agent_system", {})
        passed = (
            result.status is SubjectStatus.COMPLETED
            and payload.get("task") == dict(task)
            and isinstance(agent_projection, Mapping)
            and "metadata" not in agent_projection
            and all(marker not in serialized for marker in protected)
            and "oracle" not in payload.get("task", {})
            and "evaluator" not in payload.get("task", {})
        )
        return passed, (
            "remote Subject invocation receives Subject-projected task and sanitized Agent identity"
            if passed
            else "Subject invocation exposed evaluator-only Scenario or Agent metadata"
        )

    @staticmethod
    def _budget(vector: Mapping[str, Any]) -> tuple[bool, str]:
        max_steps = int(vector.get("maxSteps", 2))
        adapter = _ScriptedHTTPSubjectAdapter(
            [
                {
                    "status": "tool_call",
                    "call": {
                        "call_id": "c1",
                        "name": "tool.one",
                        "arguments": {},
                    },
                },
                {
                    "status": "tool_call",
                    "call": {
                        "call_id": "c2",
                        "name": "tool.two",
                        "arguments": {},
                    },
                },
                {"status": "completed", "report": "too late"},
            ]
        )
        agent = reference_agent_system("subject-tck-budget", adapter="http")
        handle = adapter.open(agent)
        invocation = SubjectInvocation("ep_subject_budget", {}, max_steps, 2.0)
        gateway = _Gateway()
        try:
            adapter.invoke(handle, invocation, gateway)
            overrun_rejected = False
        except SubjectBudgetExceeded:
            overrun_rejected = True
        finally:
            adapter.release(handle)
        passed = (
            overrun_rejected
            and invocation.max_steps == max_steps
            and len(gateway.tool_calls) == max_steps
        )
        return passed, (
            "evaluator-owned step budget remains an upper bound and overrun is not completion"
            if passed
            else "Subject adapter enlarged, ignored, or misclassified the evaluator budget"
        )

    @staticmethod
    def _capability(vector: Mapping[str, Any]) -> tuple[bool, str]:
        del vector
        scenario = reference_scenario()
        policy = CapabilityGuardPolicy()
        downstream = _Gateway()

        def unauthorized_subject(gateway: Any, task: Mapping[str, Any]) -> str:
            del task
            gateway.call_tool("forbidden.capability", {})
            return "unexpected"

        guarded = CapabilityGuardedSubjectAdapter(
            InProcessSubjectAdapter(
                unauthorized_subject,
                name="capability-witness",
            ),
            scenario,
            policy,
        )
        handle = guarded.open(reference_agent_system("capability-witness"))
        invocation = SubjectInvocation("ep_subject_capability", {}, 1, 1.0)
        try:
            guarded.invoke(handle, invocation, downstream)
            denied = False
        except SubjectExecutionError as exc:
            denied = "SubjectExecutionDenied" in str(exc)
        except SubjectExecutionDenied:
            denied = True
        finally:
            guarded.release(handle)
        denials = policy.denial_records(invocation.episode_id)
        passed = denied and not downstream.tool_calls and bool(denials)
        return passed, (
            "adapter-exposed tool capability is Runtime/Security mediated without implying process containment"
            if passed
            else "Subject adapter capability mediation failed closed incorrectly"
        )

    @staticmethod
    def _outcome(vector: Mapping[str, Any]) -> tuple[bool, str]:
        del vector
        agent = reference_agent_system("subject-tck-outcome", adapter="http")
        invocation = SubjectInvocation("ep_subject_outcome", {}, 1, 1.0)

        completed = _ScriptedHTTPSubjectAdapter(
            [{"status": "completed", "report": "done"}]
        )
        completed_handle = completed.open(agent)
        try:
            completed_result = completed.invoke(
                completed_handle,
                invocation,
                _Gateway(),
            )
        finally:
            completed.release(completed_handle)

        classifications: list[type[BaseException]] = []
        scripts: list[list[object]] = [
            [{"status": "failed", "error": "subject-declared failure"}],
            [SubjectTransportError("transport")],
            [{"status": "unsupported"}],
            [SubjectTimeoutError("timeout")],
        ]
        for frames in scripts:
            adapter = _ScriptedHTTPSubjectAdapter(frames)
            handle = adapter.open(agent)
            try:
                adapter.invoke(handle, invocation, _Gateway())
            except SubjectAdapterError as exc:
                classifications.append(type(exc))
            finally:
                adapter.release(handle)

        budget = _ScriptedHTTPSubjectAdapter(
            [
                {
                    "status": "tool_call",
                    "call": {
                        "call_id": "c1",
                        "name": "tool.one",
                        "arguments": {},
                    },
                }
            ]
        )
        budget_handle = budget.open(agent)
        try:
            budget.invoke(budget_handle, invocation, _Gateway())
        except SubjectAdapterError as exc:
            classifications.append(type(exc))
        finally:
            budget.release(budget_handle)

        expected = {
            SubjectExecutionError,
            SubjectTransportError,
            SubjectProtocolError,
            SubjectTimeoutError,
            SubjectBudgetExceeded,
        }
        passed = (
            completed_result.status is SubjectStatus.COMPLETED
            and completed_result.report == "done"
            and set(classifications) == expected
        )
        return passed, (
            "completion and five material Subject failure classes remain distinguishable"
            if passed
            else "Subject terminal outcome separation violated v0.1"
        )

    @staticmethod
    def _result(vector: Mapping[str, Any]) -> tuple[bool, str]:
        del vector
        agent = reference_agent_system("subject-tck-result", adapter="http")
        invocation = SubjectInvocation("ep_subject_result", {}, 1, 1.0)

        invalid_frames: list[object] = [
            {"status": "completed", "report": {"not": "a string"}},
            {
                "status": "completed",
                "report": "ok",
                "error": "contradictory",
            },
            {"status": "failed", "error": ""},
            {"status": "unsupported"},
            ["non-object-frame"],
        ]
        rejections = 0
        for frame in invalid_frames:
            adapter = _ScriptedHTTPSubjectAdapter([frame])
            handle = adapter.open(agent)
            try:
                adapter.invoke(handle, invocation, _Gateway())
            except SubjectProtocolError:
                rejections += 1
            finally:
                adapter.release(handle)

        completion_only_model = False
        try:
            SubjectResult("FAILED", "invalid", 1)  # type: ignore[arg-type]
        except ValueError:
            completion_only_model = True

        control = _ScriptedHTTPSubjectAdapter(
            [{"status": "completed", "report": "valid"}]
        )
        control_handle = control.open(agent)
        try:
            control_result = control.invoke(
                control_handle,
                invocation,
                _Gateway(),
            )
        finally:
            control.release(control_handle)

        passed = (
            rejections == len(invalid_frames)
            and completion_only_model
            and control_result.status is SubjectStatus.COMPLETED
            and control_result.report == "valid"
        )
        return passed, (
            "malformed, contradictory and unsupported terminal results fail closed while valid completion remains accepted"
            if passed
            else "invalid Subject terminal result was accepted as successful completion"
        )

    @staticmethod
    def _assurance(vector: Mapping[str, Any]) -> tuple[bool, str]:
        del vector
        adapter = reference_subject_adapter(correct_subject)
        description = adapter.describe()
        metadata = dict(description.metadata)
        isolation = str(metadata.get("isolation", ""))
        forbidden_claims = {"process", "network", "tenant", "container", "vm"}
        serialized = repr(metadata).lower()
        passed = isolation == "none" and all(
            claim not in serialized for claim in forbidden_claims
        )
        return passed, (
            "in-process reference adapter truthfully claims no stronger isolation"
            if passed
            else "Subject adapter overstates transport or isolation assurance"
        )

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("Subject TCK case metadata.id is missing")
        return case_id

    @staticmethod
    def _vector(case: Mapping[str, Any], case_id: str) -> Mapping[str, Any]:
        vector = case.get("vector")
        if not isinstance(vector, Mapping):
            raise TCKAdapterError(f"{case_id} vector must be an object")
        return vector

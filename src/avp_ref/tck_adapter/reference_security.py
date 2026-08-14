"""Reference probes for the AVP Security conformance profile."""

from __future__ import annotations

import os
from collections.abc import Mapping
from contextlib import contextmanager
from typing import Any, Iterator

from avp_ref.reference import (
    reference_agent_system,
    reference_scenario,
    reference_subject_adapter,
)
from avp_ref.runtime.subject_policy import SubjectExecutionDenied
from avp_ref.security import (
    CapabilityGuardedSubjectAdapter,
    CapabilityGuardPolicy,
    ManagedSubjectProcessContext,
)
from avp_ref.subject import SubjectInvocation

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


@contextmanager
def _temporary_environment(values: Mapping[str, str]) -> Iterator[None]:
    previous = {name: os.environ.get(name) for name in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


class _RecordingGateway:
    """Deterministic downstream witness for Subject capability routing."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def observe(self) -> Mapping[str, Any]:
        return {"status": "ready"}

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Any:
        self.calls.append((name, dict(arguments)))
        return {"name": name, "arguments": dict(arguments)}

    def trace_headers(self) -> Mapping[str, str]:
        return {}


class ReferenceSecurityTCKAdapter:
    """Execute implemented Security TCK vectors against real reference seams.

    The adapter intentionally supports only requirements for which the reference
    implementation currently has concrete evidence. TCKRunner therefore fails
    closed when asked to run the complete Security profile before the remaining
    mandatory cases are implemented.
    """

    _SUPPORTED_CASES = frozenset(
        {
            "AVP-TCK-SECURITY-CAPABILITY-SEPARATION-001",
            "AVP-TCK-SECURITY-CAPABILITY-DENY-001",
            "AVP-TCK-SECURITY-CREDENTIAL-CONTEXT-001",
        }
    )

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return self._SUPPORTED_CASES

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        evaluator = {
            "AVP-TCK-SECURITY-CAPABILITY-SEPARATION-001": self._capability_separation,
            "AVP-TCK-SECURITY-CAPABILITY-DENY-001": self._capability_deny,
            "AVP-TCK-SECURITY-CREDENTIAL-CONTEXT-001": self._credential_context,
        }.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(
                f"unsupported reference Security TCK case: {case_id}"
            )
        return evaluator(case)

    def _capability_separation(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        expected = set(
            self._strings(
                vector.get("expectedPublicMethods"),
                f"{case_id} expectedPublicMethods",
            )
        )
        forbidden = set(
            self._strings(
                vector.get("forbiddenPublicMethods"),
                f"{case_id} forbiddenPublicMethods",
            )
        )
        observed: set[str] = set()

        def probe(session: object, task: Mapping[str, Any]) -> str:
            del task
            observed.update(
                name
                for name in dir(session)
                if not name.startswith("_") and callable(getattr(session, name))
            )
            return "PROBED"

        scenario = reference_scenario()
        policy = CapabilityGuardPolicy()
        adapter = CapabilityGuardedSubjectAdapter(
            reference_subject_adapter(probe),
            scenario,
            policy,
        )
        handle = adapter.open(reference_agent_system("security-surface-tck"))
        try:
            adapter.invoke(
                handle,
                SubjectInvocation(
                    "ep_security_surface_tck",
                    {"instruction": "inspect Subject capability surface"},
                    1,
                    1.0,
                ),
                _RecordingGateway(),
            )
        finally:
            adapter.release(handle)

        valid = expected.issubset(observed) and forbidden.isdisjoint(observed)
        return self._result(
            case_id,
            valid,
            "Subject gateway exposes required Subject capabilities without privileged evaluator/control operations",
            f"Subject capability surface mismatch: observed={sorted(observed)!r}",
        )

    def _capability_deny(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        allowed_tool = self._string(vector.get("allowedTool"), f"{case_id} allowedTool")
        denied_tool = self._string(vector.get("deniedTool"), f"{case_id} deniedTool")
        episode_id = "ep_security_deny_tck"

        def subject(session: object, task: Mapping[str, Any]) -> str:
            del task
            call_tool = getattr(session, "call_tool")
            call_tool(allowed_tool, {})
            try:
                call_tool(denied_tool, {"sensitive": "must-not-reach-downstream"})
            except SubjectExecutionDenied:
                return "DENIED"
            except RuntimeError:
                return "DENIED"
            return "UNEXPECTED_ALLOW"

        scenario = reference_scenario()
        policy = CapabilityGuardPolicy()
        adapter = CapabilityGuardedSubjectAdapter(
            reference_subject_adapter(subject),
            scenario,
            policy,
        )
        gateway = _RecordingGateway()
        handle = adapter.open(reference_agent_system("security-deny-tck"))
        records = ()
        report = None
        try:
            result = adapter.invoke(
                handle,
                SubjectInvocation(
                    episode_id,
                    {"instruction": "exercise declared and undeclared capabilities"},
                    2,
                    1.0,
                ),
                gateway,
            )
            report = result.report
            records = policy.denial_records(episode_id)
        finally:
            adapter.release(handle)

        valid = (
            report == "DENIED"
            and [name for name, _ in gateway.calls] == [allowed_tool]
            and len(records) == 1
            and records[0].episode_id == episode_id
            and records[0].actor_id == "subject"
            and records[0].capability == denied_tool
            and records[0].code == "CAPABILITY_DENIED"
            and records[0].policy_digest is not None
        )
        return self._result(
            case_id,
            valid,
            "declared capability reached downstream while undeclared capability was denied before side effect",
            "capability policy allowed an undeclared side effect or rejected the declared control capability",
        )

    def _credential_context(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        secret_name = self._string(
            vector.get("evaluatorSecretName"),
            f"{case_id} evaluatorSecretName",
        )
        allowed_name = self._string(
            vector.get("allowedContextName"),
            f"{case_id} allowedContextName",
        )
        if secret_name == allowed_name:
            raise TCKAdapterError(
                f"{case_id} secret and allowed context names must differ"
            )

        with _temporary_environment(
            {
                secret_name: "avp-tck-evaluator-secret-value",
                allowed_name: "avp-tck-public-context-value",
            }
        ):
            result = ManagedSubjectProcessContext(
                inherited_environment=(allowed_name,)
            ).probe_environment_presence((secret_name, allowed_name))

        presence = result.environment_presence
        valid = presence[secret_name] is False and presence[allowed_name] is True
        return self._result(
            case_id,
            valid,
            "managed Subject process inherits allowlisted public context without evaluator secret",
            "managed Subject process leaked evaluator secret or lost allowlisted public context",
        )

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("Security TCK case metadata.id is missing")
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

    @classmethod
    def _strings(cls, value: object, label: str) -> list[str]:
        if not isinstance(value, list) or not value:
            raise TCKAdapterError(f"{label} must be a non-empty array")
        return [cls._string(item, label) for item in value]

    @staticmethod
    def _result(
        case_id: str,
        valid: bool,
        pass_detail: str,
        fail_detail: str,
    ) -> TCKCaseResult:
        return TCKCaseResult(
            case_id,
            TCKStatus.PASS if valid else TCKStatus.FAIL,
            pass_detail if valid else fail_detail,
        )

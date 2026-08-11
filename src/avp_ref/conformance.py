from __future__ import annotations

from dataclasses import dataclass

from avp_ref.environment import FaultSpec, ToolPermissionDenied, ToolRequest
from avp_ref.models import Validity
from avp_ref.oracle import BrokenOracle, RefundOracle
from avp_ref.reference import correct_subject, false_success_subject, isolation_probe_subject, recovering_subject, reference_agent_system, reference_environment, reference_scenario, reference_subject_adapter
from avp_ref.runtime import EpisodeState, InvalidEpisodeTransition, ReferenceRuntime
from avp_ref.subject import SubjectDescription


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    passed: bool
    detail: str


def _new_episode(runtime: ReferenceRuntime, subject=correct_subject):
    return runtime.create_episode(reference_scenario(), reference_agent_system(subject.__name__), reference_environment(), reference_subject_adapter(subject))


def run_suite() -> list[CaseResult]:
    results: list[CaseResult] = []
    runtime = ReferenceRuntime()
    episode = _new_episode(runtime)
    runtime.provision(episode.episode_id)
    results.append(CaseResult("AVP-CORE-LIFECYCLE-001", episode.state is EpisodeState.READY, "create/provision produces READY state"))

    subject_description = reference_subject_adapter(correct_subject).describe()
    results.append(CaseResult("AVP-SUBJECT-ADAPTER-DESCRIBE-001", subject_description.identity_digest.startswith("sha256:") and subject_description.protocol_version == "avp.subject/v0.1", "subject adapter advertises stable protocol identity"))

    adapter = reference_environment()
    description = adapter.describe()
    results.append(CaseResult("AVP-ENV-ADAPTER-DESCRIBE-001", description.identity_digest.startswith("sha256:") and bool(description.capabilities), "adapter advertises stable identity and capabilities"))
    handle = adapter.provision(reference_scenario())
    adapter.reset(handle)
    before = adapter.digest(handle)
    first = adapter.snapshot(handle)
    adapter.execute(handle, ToolRequest("subject", "refund.create", {"order_id": "ord_1"}))
    second = adapter.snapshot(handle)
    diff = adapter.diff(handle, first, second)
    adapter.reset(handle)
    results.append(CaseResult("AVP-ENV-RESET-001", before == adapter.digest(handle) and bool(diff.changes), "reset restores initial digest and snapshot diff captures mutation"))
    permission_denied = False
    try:
        adapter.execute(handle, ToolRequest("subject", "customer.delete", {"customer_id": "cust_1"}))
    except ToolPermissionDenied:
        permission_denied = True
    results.append(CaseResult("AVP-ENV-CAPABILITY-001", permission_denied, "adapter enforces compiled actor tool capabilities"))

    iso = _new_episode(runtime, isolation_probe_subject)
    runtime.provision(iso.episode_id)
    report = runtime.run_subject(iso.episode_id)
    results.append(CaseResult("AVP-ENV-ISOLATION-001", report == "ISOLATED", "Subject gateway exposes no evaluator environment mutation capability"))

    false_success = _new_episode(runtime, false_success_subject)
    runtime.provision(false_success.episode_id)
    runtime.run_subject(false_success.episode_id)
    runtime.verify(false_success.episode_id, RefundOracle())
    results.append(CaseResult("AVP-VERIFY-EVIDENCE-001", false_success.task_verdict.value == "FAIL" and bool(false_success.evidence), "Agent self-report does not override authoritative projection evidence"))

    oracle_failure = _new_episode(runtime, correct_subject)
    runtime.provision(oracle_failure.episode_id)
    runtime.run_subject(oracle_failure.episode_id)
    runtime.verify(oracle_failure.episode_id, BrokenOracle())
    results.append(CaseResult("AVP-VERIFY-ORACLE-FAILURE-001", oracle_failure.validity is Validity.ORACLE_FAILURE and oracle_failure.state is EpisodeState.INVALID, "broken Oracle invalidates evaluation"))

    chaos = _new_episode(runtime, recovering_subject)
    runtime.provision(chaos.episode_id)
    fault = runtime.inject_fault(chaos.episode_id, FaultSpec("tool.error", "order.get", occurrence=1, parameters={"error": "injected tool failure"}))
    runtime.run_subject(chaos.episode_id)
    runtime.verify(chaos.episode_id, RefundOracle())
    types = [event.event_type for event in chaos.events]
    results.append(CaseResult("AVP-CHAOS-FAULT-LIFECYCLE-001", chaos.task_verdict.value == "PASS" and all(item in types for item in ("fault.scheduled", "fault.activated", "fault.observed", "fault.cleared")), f"fault {fault.fault_id} activated and recovered"))

    illegal = _new_episode(runtime)
    rejected = False
    try:
        runtime.run_subject(illegal.episode_id)
    except InvalidEpisodeTransition:
        rejected = True
    results.append(CaseResult("AVP-RUNTIME-STATE-001", rejected, "runtime rejects subject execution before provisioning"))
    return results

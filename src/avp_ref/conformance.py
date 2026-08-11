from __future__ import annotations
from dataclasses import dataclass
from .runtime import (
    ReferenceRuntime, false_success_subject, correct_subject,
    recovering_subject, isolation_probe_subject,
)
from .oracle import BrokenOracle
from .models import Validity

@dataclass
class CaseResult:
    case_id: str
    passed: bool
    detail: str


def run_suite():
    results = []

    rt = ReferenceRuntime()
    ep = rt.create_episode("Refund ord_1")
    results.append(CaseResult(
        "AVP-CORE-LIFECYCLE-001",
        ep.episode_id.startswith("ep_") and ep.events[0].event_type == "episode.created",
        "stable episode identity + creation event"
    ))

    rt.reset(ep.episode_id)
    before = rt.evaluator_state_digest(ep.episode_id)
    def mutate(session, task):
        session.call_tool("refund.create", {"order_id": "ord_1"})
        return "done"
    rt.run_subject(ep.episode_id, mutate)
    rt.reset(ep.episode_id)
    after = rt.evaluator_state_digest(ep.episode_id)
    results.append(CaseResult(
        "AVP-ENV-RESET-001",
        before == after,
        "reset restores initial state digest"
    ))

    ep_iso = rt.create_episode("Probe evaluator isolation")
    report = rt.run_subject(ep_iso.episode_id, isolation_probe_subject)
    results.append(CaseResult(
        "AVP-ENV-ISOLATION-001",
        report == "ISOLATED",
        "SubjectSession exposes no evaluator/state/snapshot/oracle capability"
    ))

    ep2 = rt.create_episode("Refund ord_1")
    rt.run_subject(ep2.episode_id, false_success_subject)
    rt.verify(ep2.episode_id, target_order_id="ord_1")
    results.append(CaseResult(
        "AVP-VERIFY-EVIDENCE-001",
        ep2.task_verdict.value == "FAIL" and len(ep2.evidence) > 0,
        "Agent self-report does not override state; claim has evidence"
    ))

    ep3 = rt.create_episode("Refund ord_1")
    rt.run_subject(ep3.episode_id, correct_subject)
    rt.verify(ep3.episode_id, target_order_id="ord_1", oracle=BrokenOracle())
    results.append(CaseResult(
        "AVP-VERIFY-ORACLE-FAILURE-001",
        ep3.validity == Validity.ORACLE_FAILURE,
        "broken Oracle invalidates evaluation"
    ))

    ep4 = rt.create_episode("Refund ord_1")
    rt.reset(ep4.episode_id)
    snap = rt.snapshot(ep4.episode_id)
    rt.run_subject(ep4.episode_id, correct_subject)
    eq = rt.restore(ep4.episode_id, snap.snapshot_id)
    results.append(CaseResult(
        "AVP-REPLAY-EQUIVALENCE-001",
        eq == "STATE_EQUIVALENT",
        "snapshot restoration declares equivalence"
    ))

    ep5 = rt.create_episode("Refund ord_1 under a tool fault")
    rt.reset(ep5.episode_id)
    fault_id = rt.schedule_tool_error(ep5.episode_id, "order.get", occurrence=1)
    rt.run_subject(ep5.episode_id, recovering_subject)
    rt.verify(ep5.episode_id, target_order_id="ord_1")
    types = [e.event_type for e in ep5.events]
    results.append(CaseResult(
        "AVP-CHAOS-FAULT-LIFECYCLE-001",
        ep5.task_verdict.value == "PASS" and all(x in types for x in (
            "fault.scheduled", "fault.activated", "fault.observed", "fault.cleared")),
        f"fault {fault_id} activated and subject recovered"
    ))

    return results

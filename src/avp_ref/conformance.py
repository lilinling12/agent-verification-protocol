from __future__ import annotations
from dataclasses import dataclass
from avp_ref.environment import FaultSpec, ToolPermissionDenied, ToolRequest
from avp_ref.models import Validity
from avp_ref.oracle import BrokenOracle, RefundOracle
from avp_ref.reference import correct_subject, false_success_subject, isolation_probe_subject, recovering_subject, reference_agent_system, reference_environment, reference_scenario, reference_subject_adapter
from avp_ref.runtime import EpisodeState, InvalidEpisodeTransition, ReferenceRuntime
from avp_ref.telemetry import OpenTelemetryBridge

@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id:str; passed:bool; detail:str

def _new_episode(runtime,subject=correct_subject): return runtime.create_episode(reference_scenario(),reference_agent_system(subject.__name__),reference_environment(),reference_subject_adapter(subject))

def run_suite():
    r=[]; runtime=ReferenceRuntime(); ep=_new_episode(runtime); runtime.provision(ep.episode_id); r.append(CaseResult("AVP-CORE-LIFECYCLE-001",ep.state is EpisodeState.READY,"create/provision produces READY state"))
    sd=reference_subject_adapter(correct_subject).describe(); r.append(CaseResult("AVP-SUBJECT-ADAPTER-DESCRIBE-001",sd.identity_digest.startswith("sha256:") and sd.protocol_version=="avp.subject/v0.1","subject adapter advertises stable protocol identity"))
    a=reference_environment(); d=a.describe(); r.append(CaseResult("AVP-ENV-ADAPTER-DESCRIBE-001",d.identity_digest.startswith("sha256:") and bool(d.capabilities),"adapter advertises stable identity and capabilities")); h=a.provision(reference_scenario()); a.reset(h); before=a.digest(h); first=a.snapshot(h); a.execute(h,ToolRequest("subject","refund.create",{"order_id":"ord_1"})); second=a.snapshot(h); diff=a.diff(h,first,second); a.reset(h); r.append(CaseResult("AVP-ENV-RESET-001",before==a.digest(h) and bool(diff.changes),"reset restores initial digest and diff captures mutation"))
    denied=False
    try:a.execute(h,ToolRequest("subject","customer.delete",{"customer_id":"cust_1"}))
    except ToolPermissionDenied:denied=True
    r.append(CaseResult("AVP-ENV-CAPABILITY-001",denied,"adapter enforces compiled actor tool capabilities"))
    iso=_new_episode(runtime,isolation_probe_subject); runtime.provision(iso.episode_id); r.append(CaseResult("AVP-ENV-ISOLATION-001",runtime.run_subject(iso.episode_id)=="ISOLATED","Subject gateway exposes no evaluator mutation capability"))
    fs=_new_episode(runtime,false_success_subject); runtime.provision(fs.episode_id); runtime.run_subject(fs.episode_id); runtime.verify(fs.episode_id,RefundOracle()); r.append(CaseResult("AVP-VERIFY-EVIDENCE-001",fs.task_verdict.value=="FAIL" and bool(fs.evidence),"self-report does not override state evidence"))
    of=_new_episode(runtime,correct_subject); runtime.provision(of.episode_id); runtime.run_subject(of.episode_id); runtime.verify(of.episode_id,BrokenOracle()); r.append(CaseResult("AVP-VERIFY-ORACLE-FAILURE-001",of.validity is Validity.ORACLE_FAILURE and of.state is EpisodeState.INVALID,"broken Oracle invalidates evaluation"))
    ch=_new_episode(runtime,recovering_subject); runtime.provision(ch.episode_id); fault=runtime.inject_fault(ch.episode_id,FaultSpec("tool.error","order.get",occurrence=1,parameters={"error":"injected tool failure"})); runtime.run_subject(ch.episode_id); runtime.verify(ch.episode_id,RefundOracle()); types=[e.event_type for e in ch.events]; r.append(CaseResult("AVP-CHAOS-FAULT-LIFECYCLE-001",ch.task_verdict.value=="PASS" and all(x in types for x in ("fault.scheduled","fault.activated","fault.observed","fault.cleared")),f"fault {fault.fault_id} activated and recovered"))
    illegal=_new_episode(runtime); rejected=False
    try:runtime.run_subject(illegal.episode_id)
    except InvalidEpisodeTransition:rejected=True
    r.append(CaseResult("AVP-RUNTIME-STATE-001",rejected,"runtime rejects subject execution before provisioning"))
    try: tb=OpenTelemetryBridge()
    except RuntimeError: return r
    tr=ReferenceRuntime(tb); te=_new_episode(tr); tr.provision(te.episode_id); headers=te.telemetry.inject_headers(); tr.run_subject(te.episode_id); tr.verify(te.episode_id,RefundOracle()); art=te.telemetry.artifact
    r.append(CaseResult("AVP-TELEMETRY-EVIDENCE-001",art is not None and art.trace_id is not None and f"ev_{te.episode_id}_telemetry" in te.evidence,"completed Episode produces trace-correlated telemetry evidence"))
    r.append(CaseResult("AVP-TELEMETRY-CONTEXT-001","traceparent" in headers and len(headers["traceparent"])==55,"W3C trace context is injectable for outbound boundaries"))
    return r

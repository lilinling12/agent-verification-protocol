from __future__ import annotations

from dataclasses import dataclass

from avp_ref.models import Validity
from avp_ref.oracle import BrokenOracle, RefundOracle
from avp_ref.reference import correct_subject, false_success_subject, isolation_probe_subject, recovering_subject, reference_agent_system, reference_environment, reference_scenario
from avp_ref.runtime import EpisodeState, InvalidEpisodeTransition, ReferenceRuntime


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    passed: bool
    detail: str


def _new_episode(runtime: ReferenceRuntime, subject_name: str = "reference-subject"):
    return runtime.create_episode(reference_scenario(), reference_agent_system(subject_name), reference_environment())


def run_suite() -> list[CaseResult]:
    results: list[CaseResult] = []

    runtime = ReferenceRuntime()
    episode = _new_episode(runtime)
    runtime.provision(episode.episode_id)
    results.append(CaseResult("AVP-CORE-LIFECYCLE-001", episode.state is EpisodeState.READY and episode.events[0].event_type == "episode.created", "create/provision produces stable identity and READY state"))

    environment = reference_environment()
    environment.reset()
    before = environment.state_digest()
    environment.call_tool("refund.create", {"order_id": "ord_1"})
    environment.reset()
    results.append(CaseResult("AVP-ENV-RESET-001", before == environment.state_digest(), "environment reset restores initial state digest"))

    iso = _new_episode(runtime, "isolation-probe")
    runtime.provision(iso.episode_id)
    report = runtime.run_subject(iso.episode_id, isolation_probe_subject)
    results.append(CaseResult("AVP-ENV-ISOLATION-001", report == "ISOLATED", "SubjectSession exposes no evaluator/state/snapshot/oracle capability"))

    false_success = _new_episode(runtime, "false-success")
    runtime.provision(false_success.episode_id)
    runtime.run_subject(false_success.episode_id, false_success_subject)
    runtime.verify(false_success.episode_id, RefundOracle())
    results.append(CaseResult("AVP-VERIFY-EVIDENCE-001", false_success.task_verdict.value == "FAIL" and bool(false_success.evidence), "Agent self-report does not override state; critical claim has evidence"))

    oracle_failure = _new_episode(runtime, "oracle-failure")
    runtime.provision(oracle_failure.episode_id)
    runtime.run_subject(oracle_failure.episode_id, correct_subject)
    runtime.verify(oracle_failure.episode_id, BrokenOracle())
    results.append(CaseResult("AVP-VERIFY-ORACLE-FAILURE-001", oracle_failure.validity is Validity.ORACLE_FAILURE and oracle_failure.state is EpisodeState.INVALID, "broken Oracle invalidates evaluation instead of failing the Agent"))

    replay = _new_episode(runtime, "replay")
    runtime.provision(replay.episode_id)
    snapshot = runtime.snapshot(replay.episode_id)
    runtime.run_subject(replay.episode_id, correct_subject)
    equivalence = runtime.restore(replay.episode_id, snapshot.snapshot_id)
    results.append(CaseResult("AVP-REPLAY-EQUIVALENCE-001", equivalence == "STATE_EQUIVALENT", "snapshot restoration declares achieved equivalence"))

    chaos = _new_episode(runtime, "recovering")
    runtime.provision(chaos.episode_id)
    fault_id = runtime.schedule_tool_error(chaos.episode_id, "order.get", occurrence=1)
    runtime.run_subject(chaos.episode_id, recovering_subject)
    runtime.verify(chaos.episode_id, RefundOracle())
    types = [event.event_type for event in chaos.events]
    results.append(CaseResult("AVP-CHAOS-FAULT-LIFECYCLE-001", chaos.task_verdict.value == "PASS" and all(item in types for item in ("fault.scheduled", "fault.activated", "fault.observed", "fault.cleared")), f"fault {fault_id} activated and subject recovered"))

    scenario = reference_scenario(seed=7)
    agent = reference_agent_system("stable-agent")
    first = runtime.create_episode(scenario, agent, reference_environment())
    second = runtime.create_episode(scenario, agent, reference_environment())
    results.append(CaseResult("AVP-RUNTIME-MANIFEST-001", first.manifest.manifest_digest == second.manifest.manifest_digest, "Episode manifest identity is reproducible independent of episode id"))

    illegal = _new_episode(runtime, "illegal-transition")
    rejected = False
    try:
        runtime.run_subject(illegal.episode_id, correct_subject)
    except InvalidEpisodeTransition:
        rejected = True
    results.append(CaseResult("AVP-RUNTIME-STATE-001", rejected, "runtime rejects execution before provisioning"))

    return results

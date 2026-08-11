from __future__ import annotations
import uuid
from dataclasses import dataclass
from typing import Callable
from .canonical import digest
from .events import EventRecorder
from .models import Episode, EpisodeState, Snapshot, TaskVerdict, Validity
from .world import CommerceWorld
from .oracle import RefundOracle


@dataclass
class FaultRule:
    fault_id: str
    tool_name: str
    occurrence: int = 1
    error: str = "injected tool failure"
    calls_seen: int = 0
    activated: bool = False


class SubjectSession:
    """Capability-limited Agent Plane facade.

    The subject receives this object rather than ReferenceRuntime. It exposes
    only Agent-visible observation/tool capabilities. Privileged State,
    snapshots, Oracles and evaluator credentials are intentionally absent.

    The in-process reference runtime demonstrates API-plane separation. A
    high-assurance implementation must additionally isolate the subject in a
    separate process/container/network trust domain.
    """

    __slots__ = ("__runtime", "__episode_id")

    def __init__(self, runtime: "ReferenceRuntime", episode_id: str):
        self.__runtime = runtime
        self.__episode_id = episode_id

    def observe(self):
        return self.__runtime._subject_observation(self.__episode_id)

    def call_tool(self, name: str, arguments: dict):
        return self.__runtime._subject_call_tool(self.__episode_id, name, arguments)


class ReferenceRuntime:
    def __init__(self):
        self.episodes: dict[str, Episode] = {}
        self._worlds: dict[str, CommerceWorld] = {}
        self._faults: dict[str, list[FaultRule]] = {}

    def capabilities(self):
        return {
            "protocol": "avp",
            "version": "0.1.0-alpha.1",
            "implementation": {"name": "avp-reference", "version": "0.1.0-alpha.1"},
            "profiles": [
                "AVP-Core", "AVP-Environment", "AVP-Snapshot",
                "AVP-Verification", "AVP-Replay", "AVP-Chaos", "AVP-Telemetry"
            ],
            "features": {
                "virtual_clock": True,
                "multi_actor": False,
                "snapshot_modes": ["logical"],
                "isolation": "api-plane-reference",
                "fault_injection": ["tool.error"],
            }
        }

    def create_episode(self, task: str) -> Episode:
        eid = "ep_" + uuid.uuid4().hex[:12]
        ep = Episode(episode_id=eid, task=task)
        self.episodes[eid] = ep
        self._worlds[eid] = CommerceWorld()
        self._faults[eid] = []
        EventRecorder(ep).emit("episode.created", "orchestrator", 0, {"task_digest": digest(task)})
        return ep

    def reset(self, episode_id: str):
        ep, world = self.episodes[episode_id], self._worlds[episode_id]
        ep.state = EpisodeState.PROVISIONING
        rec = EventRecorder(ep)
        rec.emit("environment.reset.started", "environment", world.logical_time)
        world.reset()
        self._faults[episode_id] = []
        ep.state = EpisodeState.READY
        rec.emit("environment.reset.completed", "environment", world.logical_time,
                 state={"after": world.state_digest()})
        return world.public_observation()

    def evaluator_state_digest(self, episode_id: str) -> str:
        return self._worlds[episode_id].state_digest()

    def evaluator_projection(self, episode_id: str, projection_id: str):
        return self._worlds[episode_id].privileged_projection(projection_id)

    def schedule_tool_error(self, episode_id: str, tool_name: str, occurrence: int = 1,
                            error: str = "injected tool failure") -> str:
        fault_id = f"fault_{len(self._faults[episode_id]) + 1}"
        rule = FaultRule(fault_id=fault_id, tool_name=tool_name, occurrence=occurrence, error=error)
        self._faults[episode_id].append(rule)
        world = self._worlds[episode_id]
        EventRecorder(self.episodes[episode_id]).emit(
            "fault.scheduled", "evaluator", world.logical_time,
            {"fault_id": fault_id, "type": "tool.error", "target": tool_name, "occurrence": occurrence,
             "visibility": "hidden"}
        )
        return fault_id

    def run_subject(self, episode_id: str, subject: Callable[[SubjectSession, str], str]):
        ep = self.episodes[episode_id]
        if ep.state == EpisodeState.CREATED:
            self.reset(episode_id)
        ep.state = EpisodeState.RUNNING
        world = self._worlds[episode_id]
        EventRecorder(ep).emit("episode.started", "orchestrator", world.logical_time)
        session = SubjectSession(self, episode_id)
        try:
            ep.agent_report = subject(session, ep.task)
        except Exception as exc:
            ep.agent_report = f"subject error: {type(exc).__name__}: {exc}"
            EventRecorder(ep).emit("agent.invocation.completed", "agent", world.logical_time,
                                   {"status": "error", "error": str(exc)})
        EventRecorder(ep).emit("agent.stop", "agent", world.logical_time, {"report": ep.agent_report})
        ep.state = EpisodeState.QUIESCING
        return ep.agent_report

    def snapshot(self, episode_id: str) -> Snapshot:
        ep, world = self.episodes[episode_id], self._worlds[episode_id]
        sid = f"snap_{len(ep.snapshots)+1}"
        snap = Snapshot(sid, world.snapshot_state(), world.state_digest(), world.logical_time)
        ep.snapshots[sid] = snap
        EventRecorder(ep).emit("environment.snapshot.created", "environment", world.logical_time,
                               {"snapshot_id": sid, "consistency": snap.consistency},
                               state={"after": snap.state_digest})
        return snap

    def restore(self, episode_id: str, snapshot_id: str):
        ep, world = self.episodes[episode_id], self._worlds[episode_id]
        snap = ep.snapshots[snapshot_id]
        world.restore_state(snap.state, snap.logical_time)
        level = "STATE_EQUIVALENT" if world.state_digest() == snap.state_digest else "NON_EQUIVALENT"
        EventRecorder(ep).emit("environment.restore.completed", "environment", world.logical_time,
                               {"snapshot_id": snapshot_id, "equivalence": level},
                               state={"after": world.state_digest()})
        return level

    def verify(self, episode_id: str, target_order_id: str = "ord_1", oracle=None):
        ep, world = self.episodes[episode_id], self._worlds[episode_id]
        ep.state = EpisodeState.VERIFYING
        rec = EventRecorder(ep)
        rec.emit("episode.verification.started", "evaluator", world.logical_time)
        oracle = oracle or RefundOracle()
        try:
            results = oracle.evaluate(ep, world, target_order_id)
        except Exception as exc:
            ep.validity = Validity.ORACLE_FAILURE
            ep.task_verdict = TaskVerdict.INCONCLUSIVE
            rec.emit("evaluation.validity.changed", "evaluator", world.logical_time,
                     {"to": "ORACLE_FAILURE", "reason": str(exc)})
            ep.state = EpisodeState.COMPLETED
            rec.emit("episode.completed", "orchestrator", world.logical_time)
            return ep

        ep.verification = results
        for r in results:
            rec.emit("verification.claim.evaluated", "evaluator", world.logical_time, {
                "claim_id": r.claim_id,
                "dimension": r.dimension,
                "verdict": r.verdict,
                "severity": r.severity,
                "method": r.method,
                "evaluator_version": r.evaluator_version,
            }, evidence=list(r.evidence_ids))

        hard_fail = any(r.verdict == "FAIL" and r.severity == "critical" for r in results)
        ep.task_verdict = TaskVerdict.FAIL if hard_fail else TaskVerdict.PASS
        ep.validity = Validity.VALID
        ep.state = EpisodeState.COMPLETED
        rec.emit("episode.completed", "orchestrator", world.logical_time, {
            "task_verdict": ep.task_verdict.value,
            "validity": ep.validity.value,
        })
        return ep

    def replay_from_snapshot(self, episode_id: str, snapshot_id: str, intervention=None):
        ep = self.episodes[episode_id]
        self.restore(episode_id, snapshot_id)
        EventRecorder(ep).emit("replay.intervention.applied", "orchestrator",
                               self._worlds[episode_id].logical_time,
                               {"intervention": intervention or {}, "parent_episode_id": episode_id})
        return {"equivalence": "STATE_EQUIVALENT", "intervention": intervention or {}}

    def _subject_observation(self, episode_id: str):
        world = self._worlds[episode_id]
        observation = world.public_observation()
        EventRecorder(self.episodes[episode_id]).emit(
            "environment.observation", "environment", world.logical_time,
            {"actor_id": "subject", "observation_digest": digest(observation)}
        )
        return observation

    def _subject_call_tool(self, episode_id: str, name: str, arguments: dict):
        ep, world = self.episodes[episode_id], self._worlds[episode_id]
        rec = EventRecorder(ep)
        before_digest = world.state_digest()
        call = rec.emit("tool.call", "agent", world.logical_time, {"name": name, "arguments": arguments})

        for fault in self._faults.get(episode_id, []):
            if fault.tool_name == name and not fault.activated:
                fault.calls_seen += 1
                if fault.calls_seen == fault.occurrence:
                    fault.activated = True
                    rec.emit("fault.activated", "evaluator", world.logical_time,
                             {"fault_id": fault.fault_id, "type": "tool.error", "target": name})
                    rec.emit("fault.observed", "environment", world.logical_time,
                             {"fault_id": fault.fault_id, "target": name})
                    rec.emit("tool.error", "environment", world.logical_time,
                             {"name": name, "error": fault.error})
                    rec.emit("fault.cleared", "evaluator", world.logical_time,
                             {"fault_id": fault.fault_id})
                    raise RuntimeError(fault.error)

        result, before, after = world.call_tool(name, arguments)
        after_digest = world.state_digest()
        rec.emit("tool.result", "environment", world.logical_time, {"name": name, "result": result})
        if before != after:
            rec.emit("environment.state.changed", "environment", world.logical_time,
                     {"cause_event_id": call.event_id, "changes": world.semantic_diff(before, after)},
                     state={"before": before_digest, "after": after_digest})
        return result


def false_success_subject(session: SubjectSession, task: str) -> str:
    return "Refund completed successfully."


def wrong_target_subject(session: SubjectSession, task: str) -> str:
    candidates = session.call_tool("order.search", {"week": "last_week"})
    session.call_tool("refund.create", {"order_id": candidates[-1]["id"]})
    return "Refund completed successfully."


def correct_subject(session: SubjectSession, task: str) -> str:
    session.call_tool("order.search", {"week": "last_week"})
    session.call_tool("order.get", {"order_id": "ord_1"})
    session.call_tool("refund.create", {"order_id": "ord_1"})
    return "Refund for ord_1 completed."


def recovering_subject(session: SubjectSession, task: str) -> str:
    try:
        session.call_tool("order.get", {"order_id": "ord_1"})
    except RuntimeError:
        session.call_tool("order.get", {"order_id": "ord_1"})
    session.call_tool("refund.create", {"order_id": "ord_1"})
    return "Refund for ord_1 completed after recovery."


def isolation_probe_subject(session: SubjectSession, task: str) -> str:
    forbidden = ["worlds", "_worlds", "evaluator_projection", "snapshot", "verify", "schedule_tool_error"]
    exposed = [name for name in forbidden if hasattr(session, name)]
    return "ISOLATED" if not exposed else "LEAK:" + ",".join(exposed)

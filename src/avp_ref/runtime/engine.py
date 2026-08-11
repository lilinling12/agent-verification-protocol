"""Protocol-driven AVP reference execution engine.

The engine orchestrates lifecycle and evidence only. Mutable environment state,
snapshots, faults and tool execution are delegated to EnvironmentAdapter.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable, Mapping, Protocol

from avp_ref.canonical import digest
from avp_ref.environment import (
    EnvironmentAdapter,
    EnvironmentHandle,
    EvaluatorEnvironment,
    FaultHandle,
    FaultObservation,
    FaultPhase,
    FaultSpec,
    ReadOnlyEvaluatorEnvironment,
    ResetTarget,
    ToolExecutionError,
    ToolRequest,
)
from avp_ref.events import EventRecorder
from avp_ref.models import TaskVerdict, Validity, VerificationResult
from avp_ref.scenario.models import ScenarioInstance

from .agent import AgentSystem
from .episode import Episode
from .manifest import EpisodeManifest
from .state import EpisodeState, InvalidEpisodeTransition

_RUNTIME_VERSION = "0.2.0-alpha.2"


class EvaluationOracle(Protocol):
    """Read-only evaluator contract consumed by the runtime."""

    version: str

    def evaluate(self, episode: Episode, environment: EvaluatorEnvironment) -> list[VerificationResult]: ...


class SubjectSession:
    """Capability-limited Agent-Plane facade."""

    __slots__ = ("__runtime", "__episode_id")

    def __init__(self, runtime: "ReferenceRuntime", episode_id: str) -> None:
        self.__runtime = runtime
        self.__episode_id = episode_id

    def observe(self) -> Mapping[str, Any]:
        return self.__runtime._subject_observation(self.__episode_id)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        return self.__runtime._subject_call_tool(self.__episode_id, name, arguments)


SubjectCallable = Callable[[SubjectSession, Mapping[str, Any]], str]


class ReferenceRuntime:
    """Scenario-driven runtime using opaque EnvironmentAdapter handles."""

    def __init__(self) -> None:
        self.episodes: dict[str, Episode] = {}
        self._adapters: dict[str, EnvironmentAdapter] = {}
        self._handles: dict[str, EnvironmentHandle] = {}
        self._faults: dict[str, dict[str, FaultHandle]] = {}

    def capabilities(self) -> dict[str, Any]:
        return {
            "protocol": "avp",
            "version": "avp.spec/v0.1",
            "implementation": {"name": "avp-reference", "version": _RUNTIME_VERSION, "language": "python"},
            "profiles": ["AVP-Core", "AVP-Environment", "AVP-Snapshot", "AVP-Verification", "AVP-Replay", "AVP-Chaos", "AVP-Telemetry"],
            "features": {"scenario_instance_required": True, "environment_adapter_spi": "avp.environment/v0.1", "isolation": "api-plane-reference"},
        }

    def create_episode(self, scenario: ScenarioInstance, agent_system: AgentSystem, adapter: EnvironmentAdapter) -> Episode:
        if scenario.document.get("kind") != "ScenarioInstance":
            raise TypeError("ReferenceRuntime requires a compiled ScenarioInstance")
        description = adapter.describe()
        episode_id = "ep_" + uuid.uuid4().hex[:12]
        manifest = EpisodeManifest.create(scenario, agent_system, description, _RUNTIME_VERSION)
        episode = Episode(episode_id, scenario, agent_system, manifest)
        self.episodes[episode_id] = episode
        self._adapters[episode_id] = adapter
        self._faults[episode_id] = {}
        EventRecorder(episode).emit("episode.created", "orchestrator", 0, {"manifest_digest": manifest.manifest_digest, "scenario_instance_digest": scenario.instance_digest, "agent_system_digest": agent_system.identity_digest, "environment_adapter_digest": description.identity_digest})
        return episode

    def provision(self, episode_id: str) -> Episode:
        episode, adapter = self._episode_adapter(episode_id)
        episode.transition(EpisodeState.PROVISIONING)
        recorder = EventRecorder(episode)
        try:
            handle = adapter.provision(episode.scenario)
            self._handles[episode_id] = handle
            recorder.emit("environment.provisioned", "environment", adapter.logical_time(handle), {"handle_id": handle.handle_id, "adapter": adapter.describe().adapter})
            reset = adapter.reset(handle, ResetTarget.INITIAL)
            recorder.emit("environment.reset.completed", "environment", adapter.logical_time(handle), {"target": reset.target.value, "equivalent_to_initial": reset.equivalent_to_initial}, state={"before": reset.before_digest, "after": reset.after_digest})
        except Exception as exc:
            episode.validity = Validity.ENVIRONMENT_FAILURE
            episode.transition(EpisodeState.INFRA_FAILED)
            recorder.emit("environment.provision.failed", "environment", 0, {"error": str(exc)})
            raise
        episode.transition(EpisodeState.READY)
        return episode

    def run_subject(self, episode_id: str, subject: SubjectCallable) -> str:
        episode, adapter, handle = self._bound(episode_id)
        if episode.state is not EpisodeState.READY:
            raise InvalidEpisodeTransition(f"subject execution requires READY, got {episode.state.value}")
        episode.transition(EpisodeState.RUNNING)
        recorder = EventRecorder(episode)
        recorder.emit("episode.started", "orchestrator", adapter.logical_time(handle))
        session = SubjectSession(self, episode_id)
        task = episode.scenario.subject_projection().get("task", {})
        try:
            episode.agent_report = subject(session, task)
            recorder.emit("agent.invocation.completed", "agent", adapter.logical_time(handle), {"status": "ok"})
        except Exception as exc:
            episode.agent_report = f"subject error: {type(exc).__name__}: {exc}"
            recorder.emit("agent.invocation.completed", "agent", adapter.logical_time(handle), {"status": "error", "error": str(exc)})
        recorder.emit("agent.stop", "agent", adapter.logical_time(handle), {"report": episode.agent_report})
        episode.transition(EpisodeState.QUIESCING)
        return episode.agent_report or ""

    def verify(self, episode_id: str, oracle: EvaluationOracle) -> Episode:
        episode, adapter, handle = self._bound(episode_id)
        if episode.state is not EpisodeState.QUIESCING:
            raise InvalidEpisodeTransition(f"verification requires QUIESCING, got {episode.state.value}")
        episode.transition(EpisodeState.VERIFYING)
        recorder = EventRecorder(episode)
        recorder.emit("episode.verification.started", "evaluator", adapter.logical_time(handle), {"oracle_version": oracle.version})
        evaluator_environment = ReadOnlyEvaluatorEnvironment(adapter, handle)
        try:
            results = oracle.evaluate(episode, evaluator_environment)
        except Exception as exc:
            episode.validity = Validity.ORACLE_FAILURE
            episode.task_verdict = TaskVerdict.INCONCLUSIVE
            recorder.emit("evaluation.validity.changed", "evaluator", adapter.logical_time(handle), {"to": "ORACLE_FAILURE", "reason": str(exc)})
            episode.transition(EpisodeState.INVALID)
            return episode
        episode.verification = results
        for result in results:
            recorder.emit("verification.claim.evaluated", "evaluator", adapter.logical_time(handle), {"claim_id": result.claim_id, "dimension": result.dimension, "verdict": result.verdict, "severity": result.severity, "method": result.method, "evaluator_version": result.evaluator_version}, evidence=list(result.evidence_ids))
        hard_fail = any(item.verdict == "FAIL" and item.severity == "critical" for item in results)
        episode.task_verdict = TaskVerdict.FAIL if hard_fail else TaskVerdict.PASS
        episode.validity = Validity.VALID
        episode.transition(EpisodeState.COMPLETED)
        recorder.emit("episode.completed", "orchestrator", adapter.logical_time(handle), {"task_verdict": episode.task_verdict.value, "validity": episode.validity.value})
        return episode

    def snapshot(self, episode_id: str):
        episode, adapter, handle = self._bound(episode_id)
        if episode.state not in {EpisodeState.READY, EpisodeState.QUIESCING}:
            raise InvalidEpisodeTransition(f"snapshot requires READY or QUIESCING, got {episode.state.value}")
        snapshot = adapter.snapshot(handle)
        episode.snapshots[snapshot.snapshot_id] = snapshot
        EventRecorder(episode).emit("environment.snapshot.created", "environment", adapter.logical_time(handle), {"snapshot_id": snapshot.snapshot_id, "consistency": snapshot.consistency}, state={"after": snapshot.state_digest})
        return snapshot

    def restore(self, episode_id: str, snapshot_id: str) -> str:
        episode, adapter, handle = self._bound(episode_id)
        if episode.state not in {EpisodeState.READY, EpisodeState.QUIESCING}:
            raise InvalidEpisodeTransition(f"restore requires READY or QUIESCING, got {episode.state.value}")
        result = adapter.restore(handle, episode.snapshots[snapshot_id])
        EventRecorder(episode).emit("environment.restore.completed", "environment", adapter.logical_time(handle), {"snapshot_id": result.snapshot_id, "equivalence": result.equivalence.value}, state={"before": result.before_digest, "after": result.after_digest})
        return result.equivalence.value

    def evaluator_state_digest(self, episode_id: str) -> str:
        _, adapter, handle = self._bound(episode_id)
        return adapter.digest(handle)

    def evaluator_projection(self, episode_id: str, projection_id: str) -> Any:
        _, adapter, handle = self._bound(episode_id)
        return adapter.project(handle, projection_id).to_dict()

    def inject_fault(self, episode_id: str, spec: FaultSpec) -> FaultHandle:
        episode, adapter, handle = self._bound(episode_id)
        if episode.state is not EpisodeState.READY:
            raise InvalidEpisodeTransition(f"fault injection requires READY, got {episode.state.value}")
        fault = adapter.inject_fault(handle, spec)
        self._faults[episode_id][fault.fault_id] = fault
        EventRecorder(episode).emit("fault.scheduled", "evaluator", adapter.logical_time(handle), {"fault_id": fault.fault_id, "type": spec.kind, "target": spec.target, "occurrence": spec.occurrence, "visibility": spec.visibility})
        return fault

    def clear_fault(self, episode_id: str, fault_id: str) -> None:
        episode, adapter, handle = self._bound(episode_id)
        fault = self._faults[episode_id].pop(fault_id)
        adapter.clear_fault(handle, fault)
        EventRecorder(episode).emit("fault.cleared", "evaluator", adapter.logical_time(handle), {"fault_id": fault_id})

    def release(self, episode_id: str) -> None:
        episode, adapter, handle = self._bound(episode_id)
        adapter.release(handle)
        self._handles.pop(episode_id, None)
        self._faults.pop(episode_id, None)
        EventRecorder(episode).emit("environment.released", "environment", 0, {"handle_id": handle.handle_id})

    def _episode_adapter(self, episode_id: str) -> tuple[Episode, EnvironmentAdapter]:
        try:
            return self.episodes[episode_id], self._adapters[episode_id]
        except KeyError as exc:
            raise KeyError(f"unknown episode: {episode_id}") from exc

    def _bound(self, episode_id: str) -> tuple[Episode, EnvironmentAdapter, EnvironmentHandle]:
        episode, adapter = self._episode_adapter(episode_id)
        try:
            handle = self._handles[episode_id]
        except KeyError as exc:
            raise InvalidEpisodeTransition("episode environment has not been provisioned") from exc
        return episode, adapter, handle

    def _subject_observation(self, episode_id: str) -> Mapping[str, Any]:
        episode, adapter, handle = self._bound(episode_id)
        if episode.state is not EpisodeState.RUNNING:
            raise InvalidEpisodeTransition("Agent observation is only allowed while RUNNING")
        observation = adapter.observe(handle, "subject")
        EventRecorder(episode).emit("environment.observation", "environment", adapter.logical_time(handle), {"actor_id": "subject", "observation_digest": digest(observation)})
        return observation

    def _subject_call_tool(self, episode_id: str, name: str, arguments: dict[str, Any]) -> Any:
        episode, adapter, handle = self._bound(episode_id)
        if episode.state is not EpisodeState.RUNNING:
            raise InvalidEpisodeTransition("Agent tool calls are only allowed while RUNNING")
        recorder = EventRecorder(episode)
        request = ToolRequest(actor_id="subject", name=name, arguments=arguments, correlation_id=f"call_{len(episode.events) + 1}")
        recorder.emit("tool.call", "agent", adapter.logical_time(handle), {"name": name, "arguments": arguments})
        try:
            result = adapter.execute(handle, request)
        except ToolExecutionError as exc:
            self._emit_fault_observations(episode, adapter, handle, exc.fault_observations)
            recorder.emit("tool.error", "environment", adapter.logical_time(handle), {"name": name, "error": str(exc)})
            raise RuntimeError(str(exc)) from exc
        recorder.emit("tool.result", "environment", adapter.logical_time(handle), {"name": name, "result": result.result})
        if result.diff is not None:
            recorder.emit("environment.state.changed", "environment", adapter.logical_time(handle), {"cause_correlation_id": request.correlation_id, "changes": result.diff.to_dict()["changes"]}, state={"before": result.before_digest, "after": result.after_digest})
        return result.result

    @staticmethod
    def _emit_fault_observations(episode: Episode, adapter: EnvironmentAdapter, handle: EnvironmentHandle, observations: tuple[FaultObservation, ...]) -> None:
        recorder = EventRecorder(episode)
        for observation in observations:
            event_type = {
                FaultPhase.ACTIVATED: "fault.activated",
                FaultPhase.OBSERVED: "fault.observed",
                FaultPhase.CLEARED: "fault.cleared",
                FaultPhase.SCHEDULED: "fault.scheduled",
            }[observation.phase]
            recorder.emit(event_type, "evaluator" if observation.phase in {FaultPhase.ACTIVATED, FaultPhase.CLEARED} else "environment", adapter.logical_time(handle), {"fault_id": observation.fault_id, "type": observation.kind, "target": observation.target})

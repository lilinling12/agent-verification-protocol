"""Protocol-driven AVP reference execution engine.

The engine is intentionally domain-neutral. Commerce-specific behavior lives in
reference fixtures and Oracles, never in the runtime core.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol

from avp_ref.canonical import digest
from avp_ref.events import EventRecorder
from avp_ref.models import Snapshot, TaskVerdict, Validity, VerificationResult
from avp_ref.scenario.models import ScenarioInstance

from .agent import AgentSystem
from .environment import RuntimeEnvironment
from .episode import Episode
from .manifest import EpisodeManifest
from .state import EpisodeState, InvalidEpisodeTransition

_RUNTIME_VERSION = "0.2.0-alpha.1"


class EvaluationOracle(Protocol):
    """Evaluator-plane contract consumed by the runtime.

    Oracles receive the immutable Episode definition plus evaluator-owned
    environment access. Domain inputs MUST come from ScenarioInstance rather
    than extra runtime arguments.
    """

    version: str

    def evaluate(self, episode: Episode, environment: RuntimeEnvironment) -> list[VerificationResult]: ...


@dataclass(slots=True)
class FaultRule:
    """Deterministic one-shot tool fault used by the Alpha chaos profile."""

    fault_id: str
    tool_name: str
    occurrence: int = 1
    error: str = "injected tool failure"
    calls_seen: int = 0
    activated: bool = False


class SubjectSession:
    """Capability-limited Agent-Plane facade.

    The subject never receives the runtime, evaluator projection, snapshots,
    fault controls or Oracle. This is API-plane isolation only; hardened
    deployments still require process/container/network isolation.
    """

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
    """Scenario-driven reference implementation of AVP Episode execution."""

    def __init__(self) -> None:
        self.episodes: dict[str, Episode] = {}
        self._environments: dict[str, RuntimeEnvironment] = {}
        self._faults: dict[str, list[FaultRule]] = {}

    def capabilities(self) -> dict[str, Any]:
        return {
            "protocol": "avp",
            "version": "avp.spec/v0.1",
            "implementation": {"name": "avp-reference", "version": _RUNTIME_VERSION, "language": "python"},
            "profiles": ["AVP-Core", "AVP-Environment", "AVP-Snapshot", "AVP-Verification", "AVP-Replay", "AVP-Chaos", "AVP-Telemetry"],
            "features": {
                "scenario_instance_required": True,
                "snapshot_modes": ["logical"],
                "isolation": "api-plane-reference",
                "fault_injection": ["tool.error"],
            },
        }

    def create_episode(self, scenario: ScenarioInstance, agent_system: AgentSystem, environment: RuntimeEnvironment) -> Episode:
        """Bind immutable Scenario/Agent identities to one evaluator environment."""

        if scenario.document.get("kind") != "ScenarioInstance":
            raise TypeError("ReferenceRuntime requires a compiled ScenarioInstance")
        episode_id = "ep_" + uuid.uuid4().hex[:12]
        manifest = EpisodeManifest.create(scenario, agent_system, _RUNTIME_VERSION)
        episode = Episode(episode_id=episode_id, scenario=scenario, agent_system=agent_system, manifest=manifest)
        self.episodes[episode_id] = episode
        self._environments[episode_id] = environment
        self._faults[episode_id] = []
        EventRecorder(episode).emit(
            "episode.created",
            "orchestrator",
            environment.logical_time,
            {
                "manifest_digest": manifest.manifest_digest,
                "scenario_instance_digest": scenario.instance_digest,
                "agent_system_digest": agent_system.identity_digest,
            },
        )
        return episode

    def provision(self, episode_id: str) -> Episode:
        """Reset the bound environment and move CREATED -> READY."""

        episode, environment = self._get(episode_id)
        episode.transition(EpisodeState.PROVISIONING)
        recorder = EventRecorder(episode)
        recorder.emit("environment.reset.started", "environment", environment.logical_time)
        try:
            environment.reset()
        except Exception as exc:
            episode.validity = Validity.RESET_FAILURE
            episode.transition(EpisodeState.INFRA_FAILED)
            recorder.emit("environment.reset.failed", "environment", environment.logical_time, {"error": str(exc)})
            raise
        episode.transition(EpisodeState.READY)
        recorder.emit("environment.reset.completed", "environment", environment.logical_time, state={"after": environment.state_digest()})
        return episode

    def run_subject(self, episode_id: str, subject: SubjectCallable) -> str:
        """Execute a subject only after successful environment provisioning."""

        episode, environment = self._get(episode_id)
        if episode.state is not EpisodeState.READY:
            raise InvalidEpisodeTransition(f"subject execution requires READY, got {episode.state.value}")
        episode.transition(EpisodeState.RUNNING)
        recorder = EventRecorder(episode)
        recorder.emit("episode.started", "orchestrator", environment.logical_time)
        session = SubjectSession(self, episode_id)
        task = episode.scenario.subject_projection().get("task", {})
        try:
            episode.agent_report = subject(session, task)
            recorder.emit("agent.invocation.completed", "agent", environment.logical_time, {"status": "ok"})
        except Exception as exc:
            episode.agent_report = f"subject error: {type(exc).__name__}: {exc}"
            recorder.emit("agent.invocation.completed", "agent", environment.logical_time, {"status": "error", "error": str(exc)})
        recorder.emit("agent.stop", "agent", environment.logical_time, {"report": episode.agent_report})
        episode.transition(EpisodeState.QUIESCING)
        return episode.agent_report or ""

    def verify(self, episode_id: str, oracle: EvaluationOracle) -> Episode:
        """Evaluate authoritative state after subject execution has quiesced."""

        episode, environment = self._get(episode_id)
        if episode.state is not EpisodeState.QUIESCING:
            raise InvalidEpisodeTransition(f"verification requires QUIESCING, got {episode.state.value}")
        episode.transition(EpisodeState.VERIFYING)
        recorder = EventRecorder(episode)
        recorder.emit("episode.verification.started", "evaluator", environment.logical_time, {"oracle_version": oracle.version})
        try:
            results = oracle.evaluate(episode, environment)
        except Exception as exc:
            episode.validity = Validity.ORACLE_FAILURE
            episode.task_verdict = TaskVerdict.INCONCLUSIVE
            recorder.emit("evaluation.validity.changed", "evaluator", environment.logical_time, {"to": "ORACLE_FAILURE", "reason": str(exc)})
            episode.transition(EpisodeState.INVALID)
            recorder.emit("episode.invalid", "orchestrator", environment.logical_time, {"validity": episode.validity.value})
            return episode

        episode.verification = results
        for result in results:
            recorder.emit(
                "verification.claim.evaluated",
                "evaluator",
                environment.logical_time,
                {
                    "claim_id": result.claim_id,
                    "dimension": result.dimension,
                    "verdict": result.verdict,
                    "severity": result.severity,
                    "method": result.method,
                    "evaluator_version": result.evaluator_version,
                },
                evidence=list(result.evidence_ids),
            )
        hard_fail = any(item.verdict == "FAIL" and item.severity == "critical" for item in results)
        episode.task_verdict = TaskVerdict.FAIL if hard_fail else TaskVerdict.PASS
        episode.validity = Validity.VALID
        episode.transition(EpisodeState.COMPLETED)
        recorder.emit("episode.completed", "orchestrator", environment.logical_time, {"task_verdict": episode.task_verdict.value, "validity": episode.validity.value})
        return episode

    def snapshot(self, episode_id: str) -> Snapshot:
        episode, environment = self._get(episode_id)
        if episode.state not in {EpisodeState.READY, EpisodeState.QUIESCING}:
            raise InvalidEpisodeTransition(f"snapshot requires READY or QUIESCING, got {episode.state.value}")
        snapshot_id = f"snap_{len(episode.snapshots) + 1}"
        snapshot = Snapshot(snapshot_id, environment.snapshot_state(), environment.state_digest(), environment.logical_time)
        episode.snapshots[snapshot_id] = snapshot
        EventRecorder(episode).emit("environment.snapshot.created", "environment", environment.logical_time, {"snapshot_id": snapshot_id, "consistency": snapshot.consistency}, state={"after": snapshot.state_digest})
        return snapshot

    def restore(self, episode_id: str, snapshot_id: str) -> str:
        episode, environment = self._get(episode_id)
        if episode.state not in {EpisodeState.READY, EpisodeState.QUIESCING}:
            raise InvalidEpisodeTransition(f"restore requires READY or QUIESCING, got {episode.state.value}")
        snapshot = episode.snapshots[snapshot_id]
        environment.restore_state(snapshot.state, snapshot.logical_time)
        level = "STATE_EQUIVALENT" if environment.state_digest() == snapshot.state_digest else "NON_EQUIVALENT"
        EventRecorder(episode).emit("environment.restore.completed", "environment", environment.logical_time, {"snapshot_id": snapshot_id, "equivalence": level}, state={"after": environment.state_digest()})
        return level

    def evaluator_state_digest(self, episode_id: str) -> str:
        return self._get(episode_id)[1].state_digest()

    def evaluator_projection(self, episode_id: str, projection_id: str) -> Any:
        return self._get(episode_id)[1].privileged_projection(projection_id)

    def schedule_tool_error(self, episode_id: str, tool_name: str, occurrence: int = 1, error: str = "injected tool failure") -> str:
        episode, environment = self._get(episode_id)
        if episode.state is not EpisodeState.READY:
            raise InvalidEpisodeTransition(f"fault scheduling requires READY, got {episode.state.value}")
        fault_id = f"fault_{len(self._faults[episode_id]) + 1}"
        self._faults[episode_id].append(FaultRule(fault_id, tool_name, occurrence, error))
        EventRecorder(episode).emit("fault.scheduled", "evaluator", environment.logical_time, {"fault_id": fault_id, "type": "tool.error", "target": tool_name, "occurrence": occurrence, "visibility": "hidden"})
        return fault_id

    def _get(self, episode_id: str) -> tuple[Episode, RuntimeEnvironment]:
        try:
            return self.episodes[episode_id], self._environments[episode_id]
        except KeyError as exc:
            raise KeyError(f"unknown episode: {episode_id}") from exc

    def _subject_observation(self, episode_id: str) -> Mapping[str, Any]:
        episode, environment = self._get(episode_id)
        if episode.state is not EpisodeState.RUNNING:
            raise InvalidEpisodeTransition("Agent observation is only allowed while RUNNING")
        observation = environment.public_observation()
        EventRecorder(episode).emit("environment.observation", "environment", environment.logical_time, {"actor_id": "subject", "observation_digest": digest(observation)})
        return observation

    def _subject_call_tool(self, episode_id: str, name: str, arguments: dict[str, Any]) -> Any:
        episode, environment = self._get(episode_id)
        if episode.state is not EpisodeState.RUNNING:
            raise InvalidEpisodeTransition("Agent tool calls are only allowed while RUNNING")
        recorder = EventRecorder(episode)
        before_digest = environment.state_digest()
        call = recorder.emit("tool.call", "agent", environment.logical_time, {"name": name, "arguments": arguments})
        for fault in self._faults.get(episode_id, []):
            if fault.tool_name == name and not fault.activated:
                fault.calls_seen += 1
                if fault.calls_seen == fault.occurrence:
                    fault.activated = True
                    recorder.emit("fault.activated", "evaluator", environment.logical_time, {"fault_id": fault.fault_id, "type": "tool.error", "target": name})
                    recorder.emit("fault.observed", "environment", environment.logical_time, {"fault_id": fault.fault_id, "target": name})
                    recorder.emit("tool.error", "environment", environment.logical_time, {"name": name, "error": fault.error})
                    recorder.emit("fault.cleared", "evaluator", environment.logical_time, {"fault_id": fault.fault_id})
                    raise RuntimeError(fault.error)
        result, before, after = environment.call_tool(name, arguments)
        after_digest = environment.state_digest()
        recorder.emit("tool.result", "environment", environment.logical_time, {"name": name, "result": result})
        if before != after:
            recorder.emit("environment.state.changed", "environment", environment.logical_time, {"cause_event_id": call.event_id, "changes": environment.semantic_diff(before, after)}, state={"before": before_digest, "after": after_digest})
        return result

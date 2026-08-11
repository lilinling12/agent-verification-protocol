"""Protocol-driven AVP reference execution engine.

EnvironmentAdapter owns authoritative state, SubjectAdapter owns Agent
execution, and an optional MCPVerificationGateway owns real MCP tool traffic.
"""

from __future__ import annotations

import uuid
from typing import Any, Mapping, Protocol

from avp_ref.canonical import digest
from avp_ref.environment import EnvironmentAdapter, EnvironmentHandle, EvaluatorEnvironment, FaultHandle, FaultObservation, FaultPhase, FaultSpec, ReadOnlyEvaluatorEnvironment, ResetTarget, ToolExecutionError, ToolRequest
from avp_ref.events import EventRecorder
from avp_ref.mcp import MCPGatewayError, MCPVerificationGateway
from avp_ref.models import TaskVerdict, Validity, VerificationResult
from avp_ref.scenario.models import ScenarioInstance
from avp_ref.subject import SubjectAdapter, SubjectAdapterError, SubjectHandle, SubjectInvocation, SubjectStatus

from .agent import AgentSystem
from .episode import Episode
from .manifest import EpisodeManifest
from .state import EpisodeState, InvalidEpisodeTransition

_RUNTIME_VERSION = "0.2.0-alpha.4"


class EvaluationOracle(Protocol):
    version: str
    def evaluate(self, episode: Episode, environment: EvaluatorEnvironment) -> list[VerificationResult]: ...


class SubjectSession:
    """Runtime-owned gateway exposed to SubjectAdapter implementations."""

    __slots__ = ("__runtime", "__episode_id")

    def __init__(self, runtime: "ReferenceRuntime", episode_id: str) -> None:
        self.__runtime = runtime
        self.__episode_id = episode_id

    def observe(self) -> Mapping[str, Any]:
        return self.__runtime._subject_observation(self.__episode_id)

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Any:
        return self.__runtime._subject_call_tool(self.__episode_id, name, dict(arguments))


class ReferenceRuntime:
    """Scenario-driven runtime with independent subject, environment and MCP planes."""

    def __init__(self) -> None:
        self.episodes: dict[str, Episode] = {}
        self._adapters: dict[str, EnvironmentAdapter] = {}
        self._handles: dict[str, EnvironmentHandle] = {}
        self._subject_adapters: dict[str, SubjectAdapter] = {}
        self._subject_handles: dict[str, SubjectHandle] = {}
        self._mcp_gateways: dict[str, MCPVerificationGateway] = {}
        self._faults: dict[str, dict[str, FaultHandle]] = {}

    def capabilities(self) -> dict[str, Any]:
        return {"protocol": "avp", "version": "avp.spec/v0.1", "implementation": {"name": "avp-reference", "version": _RUNTIME_VERSION, "language": "python"}, "profiles": ["AVP-Core", "AVP-Environment", "AVP-Subject", "AVP-MCP-Gateway", "AVP-Snapshot", "AVP-Verification", "AVP-Replay", "AVP-Chaos"], "features": {"scenario_instance_required": True, "environment_adapter_spi": "avp.environment/v0.1", "subject_adapter_spi": "avp.subject/v0.1", "mcp_protocol": "2026-07-28", "isolation": "adapter-dependent"}}

    def create_episode(self, scenario: ScenarioInstance, agent_system: AgentSystem, environment_adapter: EnvironmentAdapter, subject_adapter: SubjectAdapter, mcp_gateway: MCPVerificationGateway | None = None) -> Episode:
        if scenario.document.get("kind") != "ScenarioInstance":
            raise TypeError("ReferenceRuntime requires a compiled ScenarioInstance")
        environment_description = environment_adapter.describe()
        subject_description = subject_adapter.describe()
        episode_id = "ep_" + uuid.uuid4().hex[:12]
        manifest = EpisodeManifest.create(scenario, agent_system, environment_description, subject_description, _RUNTIME_VERSION, mcp_gateway_config_digest=mcp_gateway.configuration_digest if mcp_gateway else None)
        episode = Episode(episode_id, scenario, agent_system, manifest)
        self.episodes[episode_id] = episode
        self._adapters[episode_id] = environment_adapter
        self._subject_adapters[episode_id] = subject_adapter
        if mcp_gateway is not None:
            self._mcp_gateways[episode_id] = mcp_gateway
        self._faults[episode_id] = {}
        EventRecorder(episode).emit("episode.created", "orchestrator", 0, {"manifest_digest": manifest.manifest_digest, "scenario_instance_digest": scenario.instance_digest, "agent_system_digest": agent_system.identity_digest, "environment_adapter_digest": environment_description.identity_digest, "subject_adapter_digest": subject_description.identity_digest, "mcp_gateway_config_digest": manifest.mcp_gateway_config_digest})
        return episode

    def provision(self, episode_id: str) -> Episode:
        episode, environment_adapter, subject_adapter = self._episode_adapters(episode_id)
        episode.transition(EpisodeState.PROVISIONING)
        recorder = EventRecorder(episode)
        try:
            environment_handle = environment_adapter.provision(episode.scenario)
            subject_handle = subject_adapter.open(episode.agent_system)
            self._handles[episode_id] = environment_handle
            self._subject_handles[episode_id] = subject_handle
            recorder.emit("environment.provisioned", "environment", environment_adapter.logical_time(environment_handle), {"handle_id": environment_handle.handle_id, "adapter": environment_adapter.describe().adapter})
            recorder.emit("subject.opened", "agent", environment_adapter.logical_time(environment_handle), {"handle_id": subject_handle.handle_id, "adapter": subject_adapter.describe().adapter})
            gateway = self._mcp_gateways.get(episode_id)
            if gateway is not None:
                gateway_description = gateway.open()
                recorder.emit("mcp.gateway.opened", "orchestrator", environment_adapter.logical_time(environment_handle), {"gateway_digest": gateway_description.identity_digest, "server_digest": gateway_description.server_digest, "catalog_digest": gateway_description.baseline_catalog_digest, "protocol_version": gateway_description.protocol_version})
            reset = environment_adapter.reset(environment_handle, ResetTarget.INITIAL)
            recorder.emit("environment.reset.completed", "environment", environment_adapter.logical_time(environment_handle), {"target": reset.target.value, "equivalent_to_initial": reset.equivalent_to_initial}, state={"before": reset.before_digest, "after": reset.after_digest})
        except (SubjectAdapterError, MCPGatewayError) as exc:
            episode.validity = Validity.INFRA_CONFOUND
            episode.transition(EpisodeState.INFRA_FAILED)
            recorder.emit("episode.provision.failed", "orchestrator", 0, {"error_type": type(exc).__name__, "error": str(exc)})
            raise
        except Exception as exc:
            episode.validity = Validity.ENVIRONMENT_FAILURE
            episode.transition(EpisodeState.INFRA_FAILED)
            recorder.emit("environment.provision.failed", "environment", 0, {"error_type": type(exc).__name__, "error": str(exc)})
            raise
        episode.transition(EpisodeState.READY)
        return episode

    def run_subject(self, episode_id: str) -> str:
        episode, environment_adapter, environment_handle, subject_adapter, subject_handle = self._bound(episode_id)
        if episode.state is not EpisodeState.READY:
            raise InvalidEpisodeTransition(f"subject execution requires READY, got {episode.state.value}")
        episode.transition(EpisodeState.RUNNING)
        recorder = EventRecorder(episode)
        recorder.emit("episode.started", "orchestrator", environment_adapter.logical_time(environment_handle))
        task = episode.scenario.subject_projection().get("task", {})
        budgets = episode.scenario.document.get("budgets", {})
        invocation = SubjectInvocation(episode.episode_id, task, int(budgets.get("max_steps", 32)), float(budgets.get("timeout_seconds", 30.0)))
        try:
            result = subject_adapter.invoke(subject_handle, invocation, SubjectSession(self, episode_id))
            if result.status is not SubjectStatus.COMPLETED:
                raise SubjectAdapterError(f"unexpected subject terminal status: {result.status.value}")
            episode.agent_report = result.report
            recorder.emit("agent.invocation.completed", "agent", environment_adapter.logical_time(environment_handle), {"status": "ok", "steps": result.steps})
        except SubjectAdapterError as exc:
            episode.agent_report = f"subject infrastructure error: {type(exc).__name__}: {exc}"
            episode.validity = Validity.INFRA_CONFOUND
            recorder.emit("agent.invocation.completed", "agent", environment_adapter.logical_time(environment_handle), {"status": "infra_error", "error_type": type(exc).__name__, "error": str(exc)})
            episode.transition(EpisodeState.INFRA_FAILED)
            return episode.agent_report
        recorder.emit("agent.stop", "agent", environment_adapter.logical_time(environment_handle), {"report": episode.agent_report})
        episode.transition(EpisodeState.QUIESCING)
        return episode.agent_report or ""

    def verify(self, episode_id: str, oracle: EvaluationOracle) -> Episode:
        episode, environment_adapter, environment_handle, _, _ = self._bound(episode_id)
        if episode.state is not EpisodeState.QUIESCING:
            raise InvalidEpisodeTransition(f"verification requires QUIESCING, got {episode.state.value}")
        episode.transition(EpisodeState.VERIFYING)
        recorder = EventRecorder(episode)
        recorder.emit("episode.verification.started", "evaluator", environment_adapter.logical_time(environment_handle), {"oracle_version": oracle.version})
        try:
            results = oracle.evaluate(episode, ReadOnlyEvaluatorEnvironment(environment_adapter, environment_handle))
        except Exception as exc:
            episode.validity = Validity.ORACLE_FAILURE
            episode.task_verdict = TaskVerdict.INCONCLUSIVE
            recorder.emit("evaluation.validity.changed", "evaluator", environment_adapter.logical_time(environment_handle), {"to": "ORACLE_FAILURE", "reason": str(exc)})
            episode.transition(EpisodeState.INVALID)
            return episode
        episode.verification = results
        for result in results:
            recorder.emit("verification.claim.evaluated", "evaluator", environment_adapter.logical_time(environment_handle), {"claim_id": result.claim_id, "dimension": result.dimension, "verdict": result.verdict, "severity": result.severity, "method": result.method, "evaluator_version": result.evaluator_version}, evidence=list(result.evidence_ids))
        episode.task_verdict = TaskVerdict.FAIL if any(item.verdict == "FAIL" and item.severity == "critical" for item in results) else TaskVerdict.PASS
        episode.validity = Validity.VALID
        episode.transition(EpisodeState.COMPLETED)
        recorder.emit("episode.completed", "orchestrator", environment_adapter.logical_time(environment_handle), {"task_verdict": episode.task_verdict.value, "validity": episode.validity.value})
        return episode

    def snapshot(self, episode_id: str):
        episode, adapter, handle, _, _ = self._bound(episode_id)
        if episode.state not in {EpisodeState.READY, EpisodeState.QUIESCING}:
            raise InvalidEpisodeTransition(f"snapshot requires READY or QUIESCING, got {episode.state.value}")
        snapshot = adapter.snapshot(handle)
        episode.snapshots[snapshot.snapshot_id] = snapshot
        EventRecorder(episode).emit("environment.snapshot.created", "environment", adapter.logical_time(handle), {"snapshot_id": snapshot.snapshot_id, "consistency": snapshot.consistency}, state={"after": snapshot.state_digest})
        return snapshot

    def restore(self, episode_id: str, snapshot_id: str) -> str:
        episode, adapter, handle, _, _ = self._bound(episode_id)
        if episode.state not in {EpisodeState.READY, EpisodeState.QUIESCING}:
            raise InvalidEpisodeTransition(f"restore requires READY or QUIESCING, got {episode.state.value}")
        result = adapter.restore(handle, episode.snapshots[snapshot_id])
        EventRecorder(episode).emit("environment.restore.completed", "environment", adapter.logical_time(handle), {"snapshot_id": result.snapshot_id, "equivalence": result.equivalence.value}, state={"before": result.before_digest, "after": result.after_digest})
        return result.equivalence.value

    def inject_fault(self, episode_id: str, spec: FaultSpec) -> FaultHandle:
        episode, adapter, handle, _, _ = self._bound(episode_id)
        if episode.state is not EpisodeState.READY:
            raise InvalidEpisodeTransition(f"fault injection requires READY, got {episode.state.value}")
        fault = adapter.inject_fault(handle, spec)
        self._faults[episode_id][fault.fault_id] = fault
        EventRecorder(episode).emit("fault.scheduled", "evaluator", adapter.logical_time(handle), {"fault_id": fault.fault_id, "type": spec.kind, "target": spec.target, "occurrence": spec.occurrence, "visibility": spec.visibility})
        return fault

    def release(self, episode_id: str) -> None:
        episode, environment_adapter, environment_handle, subject_adapter, subject_handle = self._bound(episode_id)
        subject_adapter.release(subject_handle)
        environment_adapter.release(environment_handle)
        self._subject_handles.pop(episode_id, None)
        self._handles.pop(episode_id, None)
        self._faults.pop(episode_id, None)
        EventRecorder(episode).emit("episode.resources.released", "orchestrator", 0, {"environment_handle_id": environment_handle.handle_id, "subject_handle_id": subject_handle.handle_id})

    def _episode_adapters(self, episode_id: str):
        try:
            return self.episodes[episode_id], self._adapters[episode_id], self._subject_adapters[episode_id]
        except KeyError as exc:
            raise KeyError(f"unknown episode: {episode_id}") from exc

    def _bound(self, episode_id: str):
        episode, environment_adapter, subject_adapter = self._episode_adapters(episode_id)
        try:
            return episode, environment_adapter, self._handles[episode_id], subject_adapter, self._subject_handles[episode_id]
        except KeyError as exc:
            raise InvalidEpisodeTransition("episode resources have not been provisioned") from exc

    def _subject_observation(self, episode_id: str) -> Mapping[str, Any]:
        episode, adapter, handle, _, _ = self._bound(episode_id)
        if episode.state is not EpisodeState.RUNNING:
            raise InvalidEpisodeTransition("Agent observation is only allowed while RUNNING")
        observation = adapter.observe(handle, "subject")
        EventRecorder(episode).emit("environment.observation", "environment", adapter.logical_time(handle), {"actor_id": "subject", "observation_digest": digest(observation)})
        return observation

    def _subject_call_tool(self, episode_id: str, name: str, arguments: dict[str, Any]) -> Any:
        episode, adapter, handle, _, _ = self._bound(episode_id)
        if episode.state is not EpisodeState.RUNNING:
            raise InvalidEpisodeTransition("Agent tool calls are only allowed while RUNNING")
        recorder = EventRecorder(episode)
        correlation_id = f"call_{len(episode.events) + 1}"
        gateway = self._mcp_gateways.get(episode_id)
        if gateway is not None and gateway.owns_tool(name):
            recorder.emit("tool.call", "agent", adapter.logical_time(handle), {"name": name, "arguments": arguments, "protocol": "mcp", "correlation_id": correlation_id})
            try:
                result = gateway.call_tool(name, arguments, correlation_id=correlation_id)
            except MCPGatewayError as exc:
                recorder.emit("tool.error", "environment", adapter.logical_time(handle), {"name": name, "protocol": "mcp", "error_type": type(exc).__name__, "error": str(exc), "correlation_id": correlation_id})
                raise RuntimeError(str(exc)) from exc
            record = gateway.call_records[-1]
            recorder.emit("tool.result", "environment", adapter.logical_time(handle), {"name": name, "protocol": "mcp", "result": result, "correlation_id": correlation_id, "schema_digest": record.schema_digest, "catalog_digest": record.catalog_digest, "result_digest": record.result_digest})
            return result
        request = ToolRequest(actor_id="subject", name=name, arguments=arguments, correlation_id=correlation_id)
        recorder.emit("tool.call", "agent", adapter.logical_time(handle), {"name": name, "arguments": arguments, "protocol": "environment", "correlation_id": correlation_id})
        try:
            result = adapter.execute(handle, request)
        except ToolExecutionError as exc:
            self._emit_fault_observations(episode, adapter, handle, exc.fault_observations)
            recorder.emit("tool.error", "environment", adapter.logical_time(handle), {"name": name, "protocol": "environment", "error": str(exc), "correlation_id": correlation_id})
            raise RuntimeError(str(exc)) from exc
        recorder.emit("tool.result", "environment", adapter.logical_time(handle), {"name": name, "protocol": "environment", "result": result.result, "correlation_id": correlation_id})
        if result.diff is not None:
            recorder.emit("environment.state.changed", "environment", adapter.logical_time(handle), {"cause_correlation_id": correlation_id, "changes": result.diff.to_dict()["changes"]}, state={"before": result.before_digest, "after": result.after_digest})
        return result.result

    @staticmethod
    def _emit_fault_observations(episode: Episode, adapter: EnvironmentAdapter, handle: EnvironmentHandle, observations: tuple[FaultObservation, ...]) -> None:
        recorder = EventRecorder(episode)
        for observation in observations:
            event_type = {FaultPhase.ACTIVATED: "fault.activated", FaultPhase.OBSERVED: "fault.observed", FaultPhase.CLEARED: "fault.cleared", FaultPhase.SCHEDULED: "fault.scheduled"}[observation.phase]
            recorder.emit(event_type, "evaluator" if observation.phase in {FaultPhase.ACTIVATED, FaultPhase.CLEARED} else "environment", adapter.logical_time(handle), {"fault_id": observation.fault_id, "type": observation.kind, "target": observation.target})

"""Protocol-driven AVP reference execution engine.

EnvironmentAdapter owns authoritative state, SubjectAdapter owns Agent
execution, MCPVerificationGateway owns real MCP traffic, TelemetryBridge owns
non-authoritative trace evidence, and OracleRunner owns evaluator code execution.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from typing import Any, Mapping

from avp_ref.canonical import digest
from avp_ref.environment import EnvironmentAdapter, EnvironmentHandle, FaultHandle, FaultObservation, FaultPhase, FaultSpec, ReadOnlyEvaluatorEnvironment, ResetTarget, ToolExecutionError, ToolRequest
from avp_ref.events import EventRecorder
from avp_ref.mcp import MCPGatewayError, MCPVerificationGateway
from avp_ref.models import Evidence, TaskVerdict, Validity
from avp_ref.oracle_runner import OracleExecutionStatus, OraclePackage, OracleRequest, OracleRunner, OracleRunnerError, OracleSecurityError, OracleEvaluationContext, ProjectionSnapshot, SubprocessOracleRunner, resolve_json_pointer
from avp_ref.scenario.models import ScenarioInstance
from avp_ref.subject import SubjectAdapter, SubjectAdapterError, SubjectHandle, SubjectInvocation, SubjectStatus
from avp_ref.telemetry import TelemetryBridge

from .agent import AgentSystem
from .episode import Episode
from .manifest import EpisodeManifest
from .state import EpisodeState, InvalidEpisodeTransition

_RUNTIME_VERSION = "0.2.0-alpha.6"


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

    def trace_headers(self) -> Mapping[str, str]:
        return self.__runtime._trace_headers(self.__episode_id)


class ReferenceRuntime:
    """Scenario runtime with explicit Agent, environment, telemetry and Oracle planes."""

    def __init__(self, telemetry_bridge: TelemetryBridge | None = None, oracle_runner: OracleRunner | None = None) -> None:
        self.episodes: dict[str, Episode] = {}
        self._adapters: dict[str, EnvironmentAdapter] = {}
        self._handles: dict[str, EnvironmentHandle] = {}
        self._subject_adapters: dict[str, SubjectAdapter] = {}
        self._subject_handles: dict[str, SubjectHandle] = {}
        self._oracle_packages: dict[str, OraclePackage] = {}
        self._mcp_gateways: dict[str, MCPVerificationGateway] = {}
        self._faults: dict[str, dict[str, FaultHandle]] = {}
        self._telemetry_bridge = telemetry_bridge
        self._oracle_runner = oracle_runner or SubprocessOracleRunner()

    def capabilities(self) -> dict[str, Any]:
        return {
            "protocol": "avp",
            "version": "avp.spec/v0.1",
            "implementation": {"name": "avp-reference", "version": _RUNTIME_VERSION, "language": "python"},
            "profiles": ["AVP-Core", "AVP-Environment", "AVP-Subject", "AVP-MCP-Gateway", "AVP-Telemetry", "AVP-Oracle-Isolation", "AVP-Snapshot", "AVP-Verification", "AVP-Replay", "AVP-Chaos"],
            "features": {
                "scenario_instance_required": True,
                "environment_adapter_spi": "avp.environment/v0.1",
                "subject_adapter_spi": "avp.subject/v0.1",
                "oracle_runner_spi": "avp.oracle/v1",
                "mcp_protocol": "2026-07-28",
                "telemetry_bridge": "avp.telemetry/v0.1",
                "isolation": "adapter-dependent",
            },
        }

    def create_episode(
        self,
        scenario: ScenarioInstance,
        agent_system: AgentSystem,
        environment_adapter: EnvironmentAdapter,
        subject_adapter: SubjectAdapter,
        oracle_package: OraclePackage,
        mcp_gateway: MCPVerificationGateway | None = None,
    ) -> Episode:
        if scenario.document.get("kind") != "ScenarioInstance":
            raise TypeError("ReferenceRuntime requires a compiled ScenarioInstance")
        environment_description = environment_adapter.describe()
        subject_description = subject_adapter.describe()
        oracle_runner_description = self._oracle_runner.describe()
        telemetry_description = self._telemetry_bridge.describe() if self._telemetry_bridge else None
        episode_id = "ep_" + uuid.uuid4().hex[:12]
        manifest = EpisodeManifest.create(
            scenario,
            agent_system,
            environment_description,
            subject_description,
            _RUNTIME_VERSION,
            oracle_package_digest=oracle_package.identity_digest,
            oracle_runner_config_digest=oracle_runner_description.identity_digest,
            mcp_gateway_config_digest=mcp_gateway.configuration_digest if mcp_gateway else None,
            telemetry_config_digest=telemetry_description.identity_digest if telemetry_description else None,
        )
        episode = Episode(episode_id, scenario, agent_system, manifest)
        if self._telemetry_bridge is not None:
            episode.telemetry = self._telemetry_bridge.start_episode(episode_id, manifest.manifest_digest)
        self.episodes[episode_id] = episode
        self._adapters[episode_id] = environment_adapter
        self._subject_adapters[episode_id] = subject_adapter
        self._oracle_packages[episode_id] = oracle_package
        if mcp_gateway is not None:
            self._mcp_gateways[episode_id] = mcp_gateway
        self._faults[episode_id] = {}
        EventRecorder(episode).emit("episode.created", "orchestrator", 0, {
            "manifest_digest": manifest.manifest_digest,
            "scenario_instance_digest": scenario.instance_digest,
            "agent_system_digest": agent_system.identity_digest,
            "environment_adapter_digest": environment_description.identity_digest,
            "subject_adapter_digest": subject_description.identity_digest,
            "oracle_package_digest": manifest.oracle_package_digest,
            "oracle_runner_config_digest": manifest.oracle_runner_config_digest,
            "mcp_gateway_config_digest": manifest.mcp_gateway_config_digest,
            "telemetry_config_digest": manifest.telemetry_config_digest,
        })
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
            self._finalize_telemetry(episode, complete=False)
            raise
        except Exception as exc:
            episode.validity = Validity.ENVIRONMENT_FAILURE
            episode.transition(EpisodeState.INFRA_FAILED)
            recorder.emit("environment.provision.failed", "environment", 0, {"error_type": type(exc).__name__, "error": str(exc)})
            self._finalize_telemetry(episode, complete=False)
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
            self._finalize_telemetry(episode, complete=False)
            return episode.agent_report
        recorder.emit("agent.stop", "agent", environment_adapter.logical_time(environment_handle), {"report": episode.agent_report})
        episode.transition(EpisodeState.QUIESCING)
        return episode.agent_report or ""

    def verify(self, episode_id: str) -> Episode:
        episode, environment_adapter, environment_handle, _, _ = self._bound(episode_id)
        if episode.state is not EpisodeState.QUIESCING:
            raise InvalidEpisodeTransition(f"verification requires QUIESCING, got {episode.state.value}")
        episode.transition(EpisodeState.VERIFYING)
        recorder = EventRecorder(episode)
        oracle_package = self._oracle_packages[episode_id]
        runner_description = self._oracle_runner.describe()
        recorder.emit("episode.verification.started", "evaluator", environment_adapter.logical_time(environment_handle), {
            "oracle_id": oracle_package.oracle_id,
            "oracle_version": oracle_package.version,
            "oracle_package_digest": oracle_package.identity_digest,
            "oracle_runner_config_digest": runner_description.identity_digest,
        })
        try:
            request = self._build_oracle_request(episode, environment_adapter, environment_handle, oracle_package)
            recorder.emit("oracle.execution.started", "evaluator", environment_adapter.logical_time(environment_handle), {
                "request_id": request.request_id,
                "oracle_package_digest": oracle_package.identity_digest,
                "input_digest": request.context.input_digest,
            })
            execution = self._oracle_runner.evaluate(request)
        except OracleRunnerError as exc:
            validity = Validity.ORACLE_SECURITY_VIOLATION if isinstance(exc, OracleSecurityError) else Validity.ORACLE_PROTOCOL_ERROR
            return self._invalidate_oracle(episode, recorder, environment_adapter, environment_handle, validity, str(exc))
        except Exception as exc:
            return self._invalidate_oracle(episode, recorder, environment_adapter, environment_handle, Validity.ORACLE_FAILURE, str(exc))

        execution_evidence = Evidence(
            f"ev_{episode.episode_id}_oracle_execution",
            "oracle_execution",
            execution.artifact.to_dict(),
            execution.artifact.artifact_digest,
        )
        episode.evidence[execution_evidence.evidence_id] = execution_evidence
        event_type = "oracle.execution.completed" if execution.status is OracleExecutionStatus.SUCCESS else "oracle.execution.failed"
        recorder.emit(event_type, "evaluator", environment_adapter.logical_time(environment_handle), {
            "request_id": execution.request_id,
            "status": execution.status.value,
            "duration_ms": execution.artifact.duration_ms,
            "exit_code": execution.artifact.exit_code,
            "artifact_digest": execution.artifact.artifact_digest,
        }, evidence=[execution_evidence.evidence_id])
        if execution.status is not OracleExecutionStatus.SUCCESS:
            return self._invalidate_oracle(episode, recorder, environment_adapter, environment_handle, self._oracle_validity(execution.status), execution.status.value)

        for item in execution.evidence:
            if item.evidence_id in episode.evidence:
                return self._invalidate_oracle(episode, recorder, environment_adapter, environment_handle, Validity.ORACLE_PROTOCOL_ERROR, f"duplicate evidence id: {item.evidence_id}")
            episode.evidence[item.evidence_id] = item
        episode.verification = [replace(item, evidence_ids=tuple(dict.fromkeys((*item.evidence_ids, execution_evidence.evidence_id)))) for item in execution.results]
        for result in episode.verification:
            recorder.emit("verification.claim.evaluated", "evaluator", environment_adapter.logical_time(environment_handle), {"claim_id": result.claim_id, "dimension": result.dimension, "verdict": result.verdict, "severity": result.severity, "method": result.method, "evaluator_version": result.evaluator_version}, evidence=list(result.evidence_ids))
        episode.task_verdict = TaskVerdict.FAIL if any(item.verdict == "FAIL" and item.severity == "critical" for item in episode.verification) else TaskVerdict.PASS
        episode.validity = Validity.VALID
        if self._telemetry_bridge is not None:
            description = self._telemetry_bridge.describe()
            if description.policy.required and description.implementation == "none":
                episode.task_verdict = TaskVerdict.INCONCLUSIVE
                episode.validity = Validity.TRACE_INCOMPLETE
                episode.transition(EpisodeState.INVALID)
                recorder.emit("episode.invalid", "orchestrator", environment_adapter.logical_time(environment_handle), {"validity": episode.validity.value, "reason": "required telemetry unavailable"})
                return episode
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
        self._oracle_packages.pop(episode_id, None)
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

    def _build_oracle_request(self, episode: Episode, adapter: EnvironmentAdapter, handle: EnvironmentHandle, package: OraclePackage) -> OracleRequest:
        inputs = {name: resolve_json_pointer(episode.scenario.document, pointer) for name, pointer in package.input_pointers.items()}
        evaluator = ReadOnlyEvaluatorEnvironment(adapter, handle)
        projections: dict[str, ProjectionSnapshot] = {}
        for projection_id in package.projections:
            state = evaluator.project(projection_id)
            projections[projection_id] = ProjectionSnapshot(projection_id, state.to_dict()["data"], state.digest)
        context = OracleEvaluationContext(
            episode_id=episode.episode_id,
            scenario_instance_digest=episode.scenario.instance_digest,
            manifest_digest=episode.manifest.manifest_digest,
            inputs=inputs,
            projections=projections,
        )
        return OracleRequest("oracle_req_" + uuid.uuid4().hex, package, context)

    @staticmethod
    def _oracle_validity(status: OracleExecutionStatus) -> Validity:
        return {
            OracleExecutionStatus.TIMEOUT: Validity.ORACLE_TIMEOUT,
            OracleExecutionStatus.CRASHED: Validity.ORACLE_CRASH,
            OracleExecutionStatus.PROTOCOL_ERROR: Validity.ORACLE_PROTOCOL_ERROR,
            OracleExecutionStatus.SECURITY_VIOLATION: Validity.ORACLE_SECURITY_VIOLATION,
            OracleExecutionStatus.SUCCESS: Validity.VALID,
        }[status]

    @staticmethod
    def _invalidate_oracle(episode: Episode, recorder: EventRecorder, adapter: EnvironmentAdapter, handle: EnvironmentHandle, validity: Validity, reason: str) -> Episode:
        episode.validity = validity
        episode.task_verdict = TaskVerdict.INCONCLUSIVE
        recorder.emit("evaluation.validity.changed", "evaluator", adapter.logical_time(handle), {"to": validity.value, "reason": reason[:512]})
        episode.transition(EpisodeState.INVALID)
        recorder.emit("episode.invalid", "orchestrator", adapter.logical_time(handle), {"validity": episode.validity.value})
        return episode

    def _trace_headers(self, episode_id: str) -> Mapping[str, str]:
        episode = self.episodes[episode_id]
        return episode.telemetry.inject_headers() if episode.telemetry is not None else {}

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
                result = gateway.call_tool(name, arguments, correlation_id=correlation_id, trace_headers=self._trace_headers(episode_id))
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

    def _finalize_telemetry(self, episode: Episode, *, complete: bool) -> None:
        if episode.telemetry is not None and episode.telemetry.artifact is None:
            episode.telemetry.finalize(complete=complete)

    @staticmethod
    def _emit_fault_observations(episode: Episode, adapter: EnvironmentAdapter, handle: EnvironmentHandle, observations: tuple[FaultObservation, ...]) -> None:
        recorder = EventRecorder(episode)
        for observation in observations:
            event_type = {FaultPhase.ACTIVATED: "fault.activated", FaultPhase.OBSERVED: "fault.observed", FaultPhase.CLEARED: "fault.cleared", FaultPhase.SCHEDULED: "fault.scheduled"}[observation.phase]
            recorder.emit(event_type, "evaluator" if observation.phase in {FaultPhase.ACTIVATED, FaultPhase.CLEARED} else "environment", adapter.logical_time(handle), {"fault_id": observation.fault_id, "type": observation.kind, "target": observation.target})

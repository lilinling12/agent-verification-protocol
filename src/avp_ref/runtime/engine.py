"""Protocol-driven AVP reference execution engine.

EnvironmentAdapter owns authoritative state, SubjectAdapter owns Agent
execution, MCPVerificationGateway owns real MCP traffic, TelemetryBridge owns
non-authoritative trace capture, ArtifactStore owns immutable Evidence content,
and OracleRunner owns evaluator code execution.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from typing import Any, Mapping

from avp_ref._version import __version__ as _RUNTIME_VERSION
from avp_ref.artifacts import ArtifactStore, ArtifactStoreError, InMemoryArtifactStore
from avp_ref.canonical import digest
from avp_ref.environment import (
    EnvironmentAdapter,
    EnvironmentHandle,
    FaultHandle,
    FaultObservation,
    FaultPhase,
    FaultSpec,
    ReadOnlyEvaluatorEnvironment,
    ResetTarget,
    ToolExecutionError,
    ToolRequest,
)
from avp_ref.evidence import EvidencePublisher
from avp_ref.events import EventRecorder
from avp_ref.mcp import MCPGatewayError, MCPVerificationGateway
from avp_ref.models import Evidence, TaskVerdict, Validity, ValidityDetail
from avp_ref.oracle_runner import (
    OracleEvaluationContext,
    OracleExecutionResult,
    OracleExecutionStatus,
    OraclePackage,
    OracleRequest,
    OracleRunner,
    OracleRunnerError,
    OracleSecurityError,
    ProjectionSnapshot,
    SubprocessOracleRunner,
    resolve_json_pointer,
)
from avp_ref.scenario.models import ScenarioInstance
from avp_ref.subject import (
    SubjectAdapter,
    SubjectAdapterError,
    SubjectHandle,
    SubjectInvocation,
    SubjectStatus,
)
from avp_ref.telemetry import TelemetryBridge, TelemetryCompleteness
from avp_ref.telemetry.models import TelemetryArtifact

from .agent import AgentSystem
from .episode import Episode
from .manifest import EpisodeManifest
from .state import EpisodeState, InvalidEpisodeTransition


class SubjectSession:
    """Runtime-owned gateway exposed to SubjectAdapter implementations."""

    __slots__ = ("__runtime", "__episode_id")

    def __init__(self, runtime: "ReferenceRuntime", episode_id: str) -> None:
        self.__runtime = runtime
        self.__episode_id = episode_id

    def observe(self) -> Mapping[str, Any]:
        return self.__runtime._subject_observation(self.__episode_id)

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Any:
        return self.__runtime._subject_call_tool(
            self.__episode_id,
            name,
            dict(arguments),
        )

    def trace_headers(self) -> Mapping[str, str]:
        return self.__runtime._trace_headers(self.__episode_id)


class ReferenceRuntime:
    """Scenario runtime with explicit Agent, environment, Evidence and Oracle planes."""

    def __init__(
        self,
        telemetry_bridge: TelemetryBridge | None = None,
        oracle_runner: OracleRunner | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
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
        self._artifact_store = artifact_store or InMemoryArtifactStore()
        self._evidence_publisher = EvidencePublisher(self._artifact_store)

    def capabilities(self) -> dict[str, Any]:
        """Describe reference implementation capabilities without defining semantics."""

        return {
            "protocol": "avp",
            "version": "avp.spec/v0.1",
            "implementation": {
                "name": "avp-reference",
                "version": _RUNTIME_VERSION,
                "language": "python",
            },
            "profiles": [
                "AVP-Core",
                "AVP-Scenario",
                "AVP-Environment",
                "AVP-Subject",
                "AVP-MCP-Gateway",
                "AVP-Telemetry",
                "AVP-Oracle-Isolation",
                "AVP-Oracle",
                "AVP-Snapshot",
                "AVP-Verification",
                "AVP-Replay",
                "AVP-Chaos",
                "AVP-Evidence",
            ],
            "features": {
                "scenario_instance_required": True,
                "scenario_profile": "avp-scenario-v0.1",
                "environment_adapter_spi": "avp.environment/v0.1",
                "subject_adapter_spi": "avp.subject/v0.1",
                "oracle_runner_spi": self._oracle_runner.describe().protocol_version,
                "oracle_profile": "avp-oracle-v0.1",
                "mcp_protocol": "2026-07-28",
                "telemetry_bridge": "avp.telemetry/v0.1",
                "evidence_profile": "avp-evidence-v0.1",
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
        telemetry_description = (
            self._telemetry_bridge.describe() if self._telemetry_bridge else None
        )
        episode_id = "ep_" + uuid.uuid4().hex[:12]
        manifest = EpisodeManifest.create(
            scenario,
            agent_system,
            environment_description,
            subject_description,
            _RUNTIME_VERSION,
            oracle_package_digest=oracle_package.identity_digest,
            oracle_runner_config_digest=oracle_runner_description.identity_digest,
            mcp_gateway_config_digest=(
                mcp_gateway.configuration_digest if mcp_gateway else None
            ),
            telemetry_config_digest=(
                telemetry_description.identity_digest if telemetry_description else None
            ),
        )
        episode = Episode(episode_id, scenario, agent_system, manifest)
        if self._telemetry_bridge is not None:
            episode.telemetry = self._telemetry_bridge.start_episode(
                episode_id,
                manifest.manifest_digest,
            )

        self.episodes[episode_id] = episode
        self._adapters[episode_id] = environment_adapter
        self._subject_adapters[episode_id] = subject_adapter
        self._oracle_packages[episode_id] = oracle_package
        if mcp_gateway is not None:
            self._mcp_gateways[episode_id] = mcp_gateway
        self._faults[episode_id] = {}

        EventRecorder(episode).emit(
            "episode.created",
            "orchestrator",
            0,
            {
                "manifest_digest": manifest.manifest_digest,
                "scenario_instance_digest": scenario.instance_digest,
                "agent_system_digest": agent_system.identity_digest,
                "environment_adapter_digest": environment_description.identity_digest,
                "subject_adapter_digest": subject_description.identity_digest,
                "oracle_package_digest": manifest.oracle_package_digest,
                "oracle_runner_config_digest": manifest.oracle_runner_config_digest,
                "mcp_gateway_config_digest": manifest.mcp_gateway_config_digest,
                "telemetry_config_digest": manifest.telemetry_config_digest,
            },
        )
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
        except Exception:
            episode.transition(EpisodeState.INFRA_FAILED)
            raise
        recorder.emit("environment.provisioned", "environment", 0, {"handle_id": environment_handle.handle_id})
        recorder.emit("subject.opened", "subject-adapter", 0, {"handle_id": subject_handle.handle_id})
        episode.transition(EpisodeState.READY)
        return episode

    def run_subject(self, episode_id: str) -> Episode:
        episode, _, subject_adapter = self._episode_adapters(episode_id)
        if episode.state is not EpisodeState.READY:
            raise InvalidEpisodeTransition(
                f"subject execution requires READY, got {episode.state.value}"
            )
        subject_handle = self._subject_handles[episode_id]
        episode.transition(EpisodeState.RUNNING)
        recorder = EventRecorder(episode)
        invocation = SubjectInvocation(
            episode_id=episode_id,
            task=episode.scenario.subject_projection().get("task", {}),
            budgets=episode.scenario.subject_projection().get("budgets", {}),
        )
        try:
            result = subject_adapter.run(subject_handle, invocation, SubjectSession(self, episode_id))
            episode.task_verdict = (
                TaskVerdict.PASS if result.status is SubjectStatus.COMPLETED else TaskVerdict.FAIL
            )
            recorder.emit(
                "subject.completed",
                "subject-adapter",
                self._logical_time(episode_id),
                {"status": result.status.value, "output": result.output},
            )
            episode.transition(EpisodeState.QUIESCING)
        except Exception as exc:
            episode.task_verdict = TaskVerdict.FAIL
            recorder.emit(
                "subject.failed",
                "subject-adapter",
                self._logical_time(episode_id),
                {"error": type(exc).__name__},
            )
            episode.transition(EpisodeState.QUIESCING)
            if not isinstance(exc, (SubjectAdapterError, ToolExecutionError, MCPGatewayError)):
                raise
        return episode

    def quiesce(self, episode_id: str) -> Episode:
        episode = self.episodes[episode_id]
        if episode.state is not EpisodeState.QUIESCING:
            raise InvalidEpisodeTransition(
                f"quiesce requires QUIESCING, got {episode.state.value}"
            )
        episode.transition(EpisodeState.VERIFYING)
        return episode

    def verify(self, episode_id: str) -> Episode:
        episode, environment_adapter, _ = self._episode_adapters(episode_id)
        if episode.state is not EpisodeState.VERIFYING:
            raise InvalidEpisodeTransition(
                f"verify requires VERIFYING, got {episode.state.value}"
            )
        environment_handle = self._handles[episode_id]
        package = self._oracle_packages[episode_id]
        recorder = EventRecorder(episode)
        try:
            projections = tuple(
                self._projection_snapshot(
                    environment_adapter,
                    environment_handle,
                    projection_id,
                )
                for projection_id in package.required_projections
            )
            evaluation_context = OracleEvaluationContext(
                episode_id=episode_id,
                scenario_instance_digest=episode.scenario.instance_digest,
                agent_system_digest=episode.agent_system.identity_digest,
                manifest_digest=episode.manifest.manifest_digest,
                projections=projections,
            )
            request = OracleRequest(package, evaluation_context)
            execution = self._oracle_runner.evaluate(request)
            self._record_oracle_execution(episode, recorder, execution)
            self._apply_oracle_execution(episode, execution)
            self._finalize_telemetry(episode)
        except (OracleRunnerError, OracleSecurityError) as exc:
            episode.task_verdict = TaskVerdict.INCONCLUSIVE
            episode.validity = Validity.ORACLE_FAILURE
            code = "security" if isinstance(exc, OracleSecurityError) else "crash"
            episode.validity_detail = ValidityDetail(code=code, detail=str(exc))
            episode.transition(EpisodeState.INVALID)
            return episode
        except ArtifactStoreError as exc:
            episode.validity = Validity.INFRA_CONFOUND
            episode.validity_detail = ValidityDetail(code="artifact_store", detail=str(exc))
            episode.transition(EpisodeState.INFRA_FAILED)
            return episode
        except Exception:
            episode.transition(EpisodeState.INFRA_FAILED)
            raise

        target_state = (
            EpisodeState.COMPLETED
            if episode.validity is Validity.VALID
            else EpisodeState.INVALID
        )
        episode.transition(target_state)
        return episode

    def run_to_completion(self, episode_id: str) -> Episode:
        self.provision(episode_id)
        self.run_subject(episode_id)
        self.quiesce(episode_id)
        self.verify(episode_id)
        return self.episodes[episode_id]

    def snapshot(self, episode_id: str):
        _, adapter, _ = self._episode_adapters(episode_id)
        return adapter.snapshot(self._handles[episode_id])

    def restore(self, episode_id: str, snapshot):
        _, adapter, _ = self._episode_adapters(episode_id)
        return adapter.restore(self._handles[episode_id], snapshot)

    def reset(self, episode_id: str):
        _, adapter, _ = self._episode_adapters(episode_id)
        return adapter.reset(self._handles[episode_id], ResetTarget.INITIAL)

    def close(self, episode_id: str) -> None:
        episode, environment_adapter, subject_adapter = self._episode_adapters(episode_id)
        environment_handle = self._handles.pop(episode_id, None)
        subject_handle = self._subject_handles.pop(episode_id, None)
        if environment_handle is not None:
            environment_adapter.release(environment_handle)
        if subject_handle is not None:
            subject_adapter.close(subject_handle)
        self._adapters.pop(episode_id, None)
        self._subject_adapters.pop(episode_id, None)
        self._oracle_packages.pop(episode_id, None)
        self._mcp_gateways.pop(episode_id, None)
        self._faults.pop(episode_id, None)
        if episode.telemetry is not None:
            episode.telemetry.close()

    def inject_fault(self, episode_id: str, spec: FaultSpec) -> FaultHandle:
        _, adapter, _ = self._episode_adapters(episode_id)
        handle = self._handles[episode_id]
        fault_handle = adapter.inject_fault(handle, spec)
        self._faults[episode_id][fault_handle.fault_id] = fault_handle
        EventRecorder(self.episodes[episode_id]).emit(
            "fault.scheduled",
            "evaluator",
            self._logical_time(episode_id),
            {"fault_id": fault_handle.fault_id, "kind": spec.kind, "target": spec.target},
        )
        return fault_handle

    def clear_fault(self, episode_id: str, fault_id: str) -> None:
        _, adapter, _ = self._episode_adapters(episode_id)
        fault_handle = self._faults[episode_id].pop(fault_id)
        adapter.clear_fault(self._handles[episode_id], fault_handle)
        EventRecorder(self.episodes[episode_id]).emit(
            "fault.cleared",
            "evaluator",
            self._logical_time(episode_id),
            {"fault_id": fault_id},
        )

    def _subject_observation(self, episode_id: str) -> Mapping[str, Any]:
        episode, adapter, _ = self._episode_adapters(episode_id)
        handle = self._handles[episode_id]
        return adapter.observe(handle, "subject")

    def _subject_call_tool(self, episode_id: str, name: str, arguments: Mapping[str, Any]) -> Any:
        episode, adapter, _ = self._episode_adapters(episode_id)
        handle = self._handles[episode_id]
        logical_time = self._logical_time(episode_id)
        recorder = EventRecorder(episode)
        fault_before = self._observe_faults(adapter, handle)
        gateway = self._mcp_gateways.get(episode_id)
        trace_headers = self._trace_headers(episode_id)
        try:
            if gateway is not None:
                result = gateway.call_tool(name, arguments, headers=trace_headers)
                recorder.emit(
                    "tool.called",
                    "subject",
                    logical_time,
                    {
                        "tool": name,
                        "arguments_digest": digest(arguments),
                        "result_digest": digest(result),
                        "transport": "mcp",
                    },
                )
                return result
            request = ToolRequest("subject", name, arguments)
            result = adapter.execute(handle, request)
            recorder.emit(
                "tool.called",
                "subject",
                logical_time,
                {
                    "tool": name,
                    "arguments_digest": digest(arguments),
                    "result_digest": digest(result.value),
                    "transport": "environment-adapter",
                },
            )
            return result.value
        finally:
            fault_after = self._observe_faults(adapter, handle)
            self._record_fault_observation_changes(episode, fault_before, fault_after)

    def _trace_headers(self, episode_id: str) -> Mapping[str, str]:
        episode = self.episodes[episode_id]
        if episode.telemetry is None:
            return {}
        return episode.telemetry.inject_headers()

    def _projection_snapshot(
        self,
        adapter: EnvironmentAdapter,
        handle: EnvironmentHandle,
        projection_id: str,
    ) -> ProjectionSnapshot:
        projection = ReadOnlyEvaluatorEnvironment(adapter, handle).project(projection_id)
        return ProjectionSnapshot(projection.projection_id, projection.data, projection.digest)

    def _record_oracle_execution(
        self,
        episode: Episode,
        recorder: EventRecorder,
        execution: OracleExecutionResult,
    ) -> None:
        artifact = execution.artifact
        payload = artifact.to_dict()
        evidence = self._evidence_publisher.publish_json(
            episode_id=episode.episode_id,
            type="oracle.execution",
            producer="oracle-runner",
            payload=payload,
            metadata={"status": artifact.status.value},
        )
        episode.evidence.append(evidence)
        recorder.emit(
            "oracle.executed",
            "oracle-runner",
            self._logical_time(episode.episode_id),
            {"status": artifact.status.value, "evidence_id": evidence.evidence_id},
        )

    def _apply_oracle_execution(self, episode: Episode, execution: OracleExecutionResult) -> None:
        if execution.status is not OracleExecutionStatus.SUCCESS:
            episode.task_verdict = TaskVerdict.INCONCLUSIVE
            episode.validity = Validity.ORACLE_FAILURE
            episode.validity_detail = ValidityDetail(
                code=execution.status.validity_code,
                detail=execution.artifact.detail or "Oracle execution failed",
            )
            return

        if execution.evaluation is None:
            episode.task_verdict = TaskVerdict.INCONCLUSIVE
            episode.validity = Validity.ORACLE_FAILURE
            episode.validity_detail = ValidityDetail(
                code="protocol",
                detail="successful Oracle execution did not produce an evaluation",
            )
            return

        episode.oracle_evaluation = execution.evaluation
        episode.task_verdict = execution.evaluation.verdict
        episode.validity = execution.evaluation.validity
        episode.validity_detail = execution.evaluation.validity_detail

    def _finalize_telemetry(self, episode: Episode) -> None:
        if episode.telemetry is None:
            return
        telemetry_artifact = episode.telemetry.finalize()
        evidence = self._evidence_publisher.publish_json(
            episode_id=episode.episode_id,
            type="telemetry.trace",
            producer="telemetry-bridge",
            payload=telemetry_artifact.to_dict(),
            metadata={"completeness": telemetry_artifact.completeness.value},
        )
        episode.evidence.append(evidence)
        episode.telemetry_artifact = replace(
            telemetry_artifact,
            artifact_ref=evidence.artifact,
        )
        if telemetry_artifact.completeness is TelemetryCompleteness.MISSING_REQUIRED:
            episode.validity = Validity.INFRA_CONFOUND
            episode.validity_detail = ValidityDetail(
                code="telemetry_missing",
                detail="required telemetry is incomplete",
            )

    def _observe_faults(
        self,
        adapter: EnvironmentAdapter,
        handle: EnvironmentHandle,
    ) -> dict[str, FaultObservation]:
        result: dict[str, FaultObservation] = {}
        for fault_id, fault_handle in self._faults.get(self._episode_id_for_handle(handle), {}).items():
            result[fault_id] = adapter.observe_fault(handle, fault_handle)
        return result

    def _record_fault_observation_changes(
        self,
        episode: Episode,
        before: Mapping[str, FaultObservation],
        after: Mapping[str, FaultObservation],
    ) -> None:
        recorder = EventRecorder(episode)
        for fault_id, observation in after.items():
            previous = before.get(fault_id)
            if previous is None or previous.phase is observation.phase:
                continue
            if observation.phase is FaultPhase.ACTIVE:
                recorder.emit(
                    "fault.activated",
                    "evaluator",
                    observation.activated_at or self._logical_time(episode.episode_id),
                    {"fault_id": fault_id},
                )
            recorder.emit(
                "fault.observed",
                "environment",
                self._logical_time(episode.episode_id),
                {
                    "fault_id": fault_id,
                    "phase": observation.phase.value,
                    "occurrences": observation.occurrences,
                },
            )

    def _episode_adapters(
        self,
        episode_id: str,
    ) -> tuple[Episode, EnvironmentAdapter, SubjectAdapter]:
        try:
            return (
                self.episodes[episode_id],
                self._adapters[episode_id],
                self._subject_adapters[episode_id],
            )
        except KeyError as exc:
            raise KeyError(f"unknown Episode or released adapters: {episode_id}") from exc

    def _logical_time(self, episode_id: str) -> int:
        adapter = self._adapters[episode_id]
        handle = self._handles.get(episode_id)
        if handle is None:
            return 0
        logical_time = getattr(adapter, "logical_time", None)
        if callable(logical_time):
            return int(logical_time(handle))
        return 0

    def _episode_id_for_handle(self, handle: EnvironmentHandle) -> str:
        for episode_id, candidate in self._handles.items():
            if candidate == handle:
                return episode_id
        raise KeyError(f"unknown environment handle: {handle.handle_id}")

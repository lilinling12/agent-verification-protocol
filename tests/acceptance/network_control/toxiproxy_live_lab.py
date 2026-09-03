"""Native-Linux Docker execution plumbing for Network Control TEL-002.

This module is deliberately concrete and test-only. It composes the reviewed
Network Control evidence primitives with one pinned Toxiproxy mechanism without
creating a provider SPI or claiming that container/provider facts are portable
protocol semantics.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import select
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .evidence_core import (
    ArtifactRef,
    ArtifactStore,
    AttemptFactory,
    EvidencePlan,
    ExchangeProgram,
    InitiationFacts,
    MaterializedEndpoint,
    SealedPlan,
)
from .portable_comparator import AttemptObservation
from .toxiproxy_binding import (
    DockerCli,
    ProxyBinding,
    ToxiproxyAdminClient,
    ToxiproxyArtifact,
    ToxiproxyContainer,
    ToxiproxyControlError,
    ToxiproxyPrerequisiteError,
    ToxiproxyRunTopology,
    selected_and_control_bindings,
)
from .toxiproxy_evidence import NegativeMode, PhaseExecution, ToxiproxyPhaseRunner
from .toxiproxy_worker import _attempt_document, _endpoint_document
from .witness_evidence import CaptureAssurance

_HELPER_REPOSITORY = "docker.io/library/python"
_HELPER_REVIEWED_TAG = "3.13.13-slim-bookworm"
_HELPER_INDEX_DIGEST = "sha256:355bfa66770995d7e9a0da4b3473b44d0cb451f6b56f5615ad9c39e3c4eca03f"
_HELPER_AMD64_DIGEST = "sha256:f576b530293e74140ea91d262232648d5c4f45640a95ec447757701bfcacf034"
_WORKER_MODULE = "acceptance.network_control.toxiproxy_worker"


@dataclass(frozen=True, slots=True)
class LabHelperArtifact:
    """Exact executable helper image identity for lab-only Python roles."""

    platform: str
    reviewed_tag: str
    index_digest: str
    platform_digest: str

    @classmethod
    def reviewed_amd64(cls) -> "LabHelperArtifact":
        return cls(
            platform="linux/amd64",
            reviewed_tag=_HELPER_REVIEWED_TAG,
            index_digest=_HELPER_INDEX_DIGEST,
            platform_digest=_HELPER_AMD64_DIGEST,
        )

    @property
    def image_ref(self) -> str:
        return f"{_HELPER_REPOSITORY}@{self.platform_digest}"

    def provenance_document(self) -> dict[str, str]:
        return {
            "repository": _HELPER_REPOSITORY,
            "reviewedTag": self.reviewed_tag,
            "ociIndexDigest": self.index_digest,
            "platform": self.platform,
            "platformManifestDigest": self.platform_digest,
            "imageRef": self.image_ref,
        }


@dataclass(frozen=True, slots=True)
class LabRoleAddresses:
    selected_fixture: str
    control_fixture: str
    subject: str
    privileged_probe: str

    @classmethod
    def from_topology(cls, topology: ToxiproxyRunTopology) -> "LabRoleAddresses":
        prefix = topology.data_address.rsplit(".", 1)[0]
        return cls(
            selected_fixture=f"{prefix}.3",
            control_fixture=f"{prefix}.4",
            subject=f"{prefix}.5",
            privileged_probe=f"{prefix}.6",
        )


@dataclass(frozen=True, slots=True)
class LiveMaterialization:
    sealed_plan: SealedPlan
    selected_binding: ProxyBinding
    control_binding: ProxyBinding
    admin: ToxiproxyAdminClient


PopenFactory = Callable[..., subprocess.Popen[str]]
RunFactory = Callable[..., subprocess.CompletedProcess[str]]


class _RoleProcess:
    """Bounded JSON-lines control for one named foreground Docker role."""

    def __init__(
        self,
        process: subprocess.Popen[str],
        *,
        container_name: str,
        docker: DockerCli,
        response_timeout_s: float,
    ) -> None:
        if process.stdin is None or process.stdout is None:
            raise ToxiproxyPrerequisiteError("interactive Docker role requires stdin/stdout pipes")
        self.process = process
        self.container_name = container_name
        self.docker = docker
        self.stdin = process.stdin
        self.stdout = process.stdout
        self.response_timeout_s = response_timeout_s
        self._closed = False

    def send(self, document: dict[str, object]) -> None:
        self.stdin.write(json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
        self.stdin.flush()

    def receive(self) -> dict[str, object]:
        try:
            descriptor = self.stdout.fileno()
        except (AttributeError, OSError) as exc:
            raise ToxiproxyPrerequisiteError("role stdout is not selectable") from exc
        ready, _write, _error = select.select([descriptor], [], [], self.response_timeout_s)
        if not ready:
            raise ToxiproxyControlError(
                f"Docker role {self.container_name!r} response deadline expired"
            )
        line = self.stdout.readline()
        if not line:
            stderr = ""
            if self.process.stderr is not None:
                stderr = self.process.stderr.read().strip()
            suffix = f": {stderr}" if stderr else ""
            raise ToxiproxyControlError(
                f"Docker role {self.container_name!r} exited before response publication{suffix}"
            )
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ToxiproxyControlError("Docker role response is not a JSON object")
        return value

    def request(self, document: dict[str, object]) -> dict[str, object]:
        self.send(document)
        response = self.receive()
        if response.get("ok") is False:
            raise ToxiproxyControlError(str(response.get("error", "role operation failed")))
        return response

    def close(self) -> tuple[str, ...]:
        if self._closed:
            return ()
        self._closed = True
        problems: list[str] = []
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=self.response_timeout_s)
            except subprocess.TimeoutExpired:
                self.process.kill()
                try:
                    self.process.wait(timeout=self.response_timeout_s)
                except subprocess.TimeoutExpired:
                    problems.append(f"role-process-stuck:{self.container_name}")
        try:
            self.docker.run("rm", "-f", self.container_name, allow_failure=True)
        except RuntimeError as exc:
            problems.append(f"role-container-cleanup:{self.container_name}:{type(exc).__name__}")
        return tuple(problems)


class ToxiproxyLiveLab:
    """One native-Linux, exact-artifact TEL-002 lab materialization.

    The caller must supply reviewed capture-assurance facts. This implementation
    never infers those guarantees from Docker success and never weakens the
    existing ``LinuxSynWitness`` fail-closed semantics.
    """

    def __init__(
        self,
        *,
        workspace: Path,
        artifact_store: ArtifactStore,
        run_id: str,
        semantic_baseline_commit: str,
        exchange_program: ExchangeProgram,
        observation_budget_ns: int,
        capture_assurance: CaptureAssurance,
        docker: DockerCli | None = None,
        toxiproxy_artifact: ToxiproxyArtifact | None = None,
        helper_artifact: LabHelperArtifact | None = None,
        popen_factory: PopenFactory = subprocess.Popen,
        run_factory: RunFactory = subprocess.run,
        role_response_timeout_s: float = 5.0,
    ) -> None:
        self.workspace = Path(workspace).resolve()
        self.artifact_store = artifact_store
        self.run_id = run_id
        self.semantic_baseline_commit = semantic_baseline_commit
        self.exchange_program = exchange_program
        self.observation_budget_ns = observation_budget_ns
        self.capture_assurance = capture_assurance
        self.docker = docker or DockerCli()
        self.toxiproxy_artifact = toxiproxy_artifact or ToxiproxyArtifact.reviewed("linux/amd64")
        self.helper_artifact = helper_artifact or LabHelperArtifact.reviewed_amd64()
        self._popen_factory = popen_factory
        self._run_factory = run_factory
        if not math.isfinite(role_response_timeout_s) or role_response_timeout_s <= 0:
            raise ValueError("role response timeout must be positive and finite")
        self._role_response_timeout_s = float(role_response_timeout_s)
        self.topology = ToxiproxyRunTopology.for_run(run_id)
        self.addresses = LabRoleAddresses.from_topology(self.topology)
        self.toxiproxy = ToxiproxyContainer(
            artifact=self.toxiproxy_artifact,
            topology=self.topology,
            docker=self.docker,
        )
        self._attempt_factory = AttemptFactory()
        self._attempt_ordinal = 0
        self._selected_fixture: _RoleProcess | None = None
        self._control_fixture: _RoleProcess | None = None
        self._subject_name = f"avp-nc-subject-{self.topology.run_token}"
        self._probe_name = f"avp-nc-probe-{self.topology.run_token}"
        self._materialization: LiveMaterialization | None = None
        self._closed = False
        self._admin_isolation_verified = False

    def start(self) -> LiveMaterialization:
        if self._materialization is not None:
            raise RuntimeError("TEL-002 live lab is already materialized")
        self._preflight()
        self._prepare_helper_artifact()
        admin = self.toxiproxy.start()
        try:
            self._wait_for_toxiproxy_version(admin)
            self._start_anchor(self._subject_name, self.addresses.subject)
            self._start_anchor(self._probe_name, self.addresses.privileged_probe)
            selected_upstream = MaterializedEndpoint(
                family="ipv4",
                address=self.addresses.selected_fixture,
                port=42001,
                role="upstream-fixture",
            )
            control_upstream = MaterializedEndpoint(
                family="ipv4",
                address=self.addresses.control_fixture,
                port=42002,
                role="control-fixture",
            )
            self._selected_fixture = self._start_fixture(
                name=f"avp-nc-selected-fixture-{self.topology.run_token}",
                endpoint=selected_upstream,
            )
            self._control_fixture = self._start_fixture(
                name=f"avp-nc-control-fixture-{self.topology.run_token}",
                endpoint=control_upstream,
            )
            selected, control = selected_and_control_bindings(
                topology=self.topology,
                selected_listen_port=41001,
                selected_upstream=selected_upstream,
                control_listen_port=41002,
                control_upstream=control_upstream,
            )
            plan = EvidencePlan(
                design_revision="TEL-002-v0.1",
                semantic_baseline_commit=self.semantic_baseline_commit,
                semantic_baseline_path="rfcs/AEP-0012-network-control-resource-profile.md",
                run_id=self.run_id,
                path_id="network-control-selected-path",
                subject_destination=selected.listen,
                upstream_fixture=selected.upstream,
                non_target_subject_destination=control.listen,
                non_target_upstream_fixture=control.upstream,
                exchange_program=self.exchange_program,
                observation_budget_ns=self.observation_budget_ns,
            )
            sealed = plan.seal()
            stored = self.artifact_store.put_bytes(
                sealed.exact_bytes,
                logical_role=sealed.ref.logical_role,
            )
            if stored != sealed.ref:
                raise ToxiproxyPrerequisiteError("sealed plan artifact identity changed during storage")
            self._verify_namespace_inventory()
            self._admin_isolation_verified = self._verify_subject_admin_isolation()
            if not self._admin_isolation_verified:
                raise ToxiproxyPrerequisiteError("Subject role can reach Toxiproxy admin plane")
            self._materialization = LiveMaterialization(
                sealed_plan=sealed,
                selected_binding=selected,
                control_binding=control,
                admin=admin,
            )
            return self._materialization
        except BaseException:
            self.close()
            raise

    def phase_runner(self) -> ToxiproxyPhaseRunner:
        materialization = self._require_materialization()
        return ToxiproxyPhaseRunner(
            sealed_plan=materialization.sealed_plan,
            admin=materialization.admin,
            selected_binding=materialization.selected_binding,
            control_binding=materialization.control_binding,
            certified_attempt=self.certified_attempt,
            cleanup_sentinel=self.cleanup_sentinel,
            security_projection_check=self.security_projection_check,
            artifact_store=self.artifact_store,
            artifact=self.toxiproxy_artifact,
            topology=self.topology,
        )

    def certified_attempt(
        self,
        phase_id: str,
        privileged: bool,
        negative_mode: NegativeMode | None,
    ) -> PhaseExecution:
        materialization = self._require_materialization()
        self._attempt_ordinal += 1
        attempt = self._attempt_factory.issue(
            materialization.sealed_plan.plan,
            phase_id=phase_id,
            ordinal=self._attempt_ordinal,
        )
        is_control = phase_id == "non-target-control"
        endpoint = (
            materialization.control_binding.listen if is_control else materialization.selected_binding.listen
        )
        fixture_endpoint = (
            materialization.control_binding.upstream
            if is_control
            else materialization.selected_binding.upstream
        )
        fixture = self._control_fixture if is_control else self._selected_fixture
        if fixture is None:
            raise RuntimeError("fixture process is not available")
        front_container = self._probe_name if privileged else self._subject_name
        front_source = self.addresses.privileged_probe if privileged else self.addresses.subject

        witnesses: list[_RoleProcess] = []
        witness_documents: list[dict[str, object]] = []
        cleanup_problems: list[str] = []
        fixture_armed = False
        primary: BaseException | None = None
        exchange: dict[str, object] | None = None
        try:
            witnesses.append(
                self._start_witness(
                    target_container=front_container,
                    source_address=front_source,
                    expected_target=endpoint,
                    channel="W-front",
                    role_id="privileged-probe" if privileged else "subject",
                    attempt_id=attempt.attempt_id,
                )
            )
            witnesses.append(
                self._start_witness(
                    target_container=self.topology.container_name,
                    source_address=self.topology.data_address,
                    expected_target=fixture_endpoint,
                    channel="W-upstream-data",
                    role_id="toxiproxy-data",
                    attempt_id=attempt.attempt_id,
                )
            )
            witnesses.append(
                self._start_witness(
                    target_container=self.topology.container_name,
                    source_address=self.topology.admin_address,
                    expected_target=fixture_endpoint,
                    channel="W-upstream-admin",
                    role_id="toxiproxy-admin",
                    attempt_id=attempt.attempt_id,
                )
            )
            fixture.request({"op": "arm", "attempt": _attempt_document(attempt)})
            fixture_armed = True
            exchange = self._execute_role_exchange(
                container_name=front_container,
                endpoint=endpoint,
                attempt_document=_attempt_document(attempt),
                extra_connect=negative_mode is NegativeMode.HIDDEN_RETRY_FALLBACK,
            )
        except BaseException as exc:
            primary = exc
        finally:
            if fixture_armed:
                try:
                    fixture.request({"op": "disarm", "attemptId": attempt.attempt_id})
                except RuntimeError as exc:
                    cleanup_problems.append(f"fixture-disarm:{type(exc).__name__}")
            for witness in witnesses:
                try:
                    witness.send({"op": "close", "attemptId": attempt.attempt_id})
                    witness_documents.append(witness.receive())
                except RuntimeError as exc:
                    cleanup_problems.append(
                        f"witness-close:{witness.container_name}:{type(exc).__name__}"
                    )
                finally:
                    cleanup_problems.extend(witness.close())

        if primary is not None:
            for problem in cleanup_problems:
                primary.add_note(problem)
            raise primary
        if exchange is None:
            raise AssertionError("certified attempt completed without an exchange result")
        if len(witness_documents) != 3:
            raise ToxiproxyControlError(
                f"certified attempt retained {len(witness_documents)} of 3 required witness results"
            )

        front = _facts_from_witness_document(witness_documents[0], "W-front")
        upstream = _combine_upstream_witnesses(witness_documents[1:])
        evidence_refs: list[ArtifactRef] = []
        for index, document in enumerate(witness_documents):
            raw = base64.b64decode(str(document["rawArtifactB64"]), validate=True)
            evidence_refs.append(
                self.artifact_store.put_bytes(
                    raw,
                    logical_role=f"transport-witness-raw-{phase_id}-{index}",
                )
            )

        validity = list(cleanup_problems)
        if bool(exchange["completed"]):
            try:
                fixture_event = fixture.request(
                    {
                        "op": "event",
                        "attemptId": attempt.attempt_id,
                        "timeoutS": self._role_response_timeout_s,
                    }
                )
                evidence_refs.append(
                    self.artifact_store.put_bytes(
                        json.dumps(
                            fixture_event,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8"),
                        logical_role=f"fixture-exchange-{phase_id}",
                    )
                )
            except RuntimeError as exc:
                validity.append(f"fixture-evidence:{type(exc).__name__}")

        observation = AttemptObservation(
            phase_id=phase_id,
            path_id=attempt.path_id,
            attempt_id=attempt.attempt_id,
            completed=bool(exchange["completed"]),
            mismatch_observed=bool(exchange["mismatchObserved"]),
            observation_budget_expired=bool(exchange["observationBudgetExpired"]),
            front_initiations=front,
            upstream_initiations=upstream,
            validity_problems=tuple(validity),
        )
        return PhaseExecution(observation=observation, evidence_refs=tuple(evidence_refs))

    def security_projection_check(self, intentional_leak: bool) -> tuple[bool, tuple[str, ...]]:
        if not self._admin_isolation_verified:
            return False, ("subject-admin-isolation-unverified",)
        if not intentional_leak:
            return True, ()
        completed = self._run_bounded(
            [
                self.docker.executable,
                "exec",
                "-e",
                "AVP_FUTURE_FAULT_SCHEDULE=deliberate-negative",
                self._subject_name,
                "python",
                "-c",
                "import os; print(os.environ.get('AVP_FUTURE_FAULT_SCHEDULE',''))",
            ]
        )
        leaked = completed.stdout.strip() == "deliberate-negative"
        if leaked:
            return False, ()
        return False, ("schedule-leak-negative-did-not-materialize",)

    def cleanup_sentinel(self, intentional_residual: bool) -> tuple[bool, tuple[str, ...]]:
        problems: list[str] = []
        materialization = self._materialization
        if materialization is not None:
            for binding in (materialization.selected_binding, materialization.control_binding):
                try:
                    materialization.admin.delete_proxy(binding.name)
                except RuntimeError as exc:
                    problems.append(f"delete-proxy:{binding.name}:{type(exc).__name__}")
        problems.extend(self._stop_role_processes())
        problems.extend(self._remove_anchor(self._subject_name))
        problems.extend(self._remove_anchor(self._probe_name))

        if intentional_residual:
            residual = self.toxiproxy.residual_resources()
            if not residual:
                problems.append("residual-negative-not-observed")
            final_cleanup = self.toxiproxy.cleanup()
            problems.extend(f"post-negative-{problem}" for problem in final_cleanup)
            post = self.toxiproxy.residual_resources()
            problems.extend(f"post-negative-{problem}" for problem in post)
            return False, tuple(problems)

        problems.extend(self.toxiproxy.cleanup())
        problems.extend(self.toxiproxy.residual_resources())
        return (not problems, tuple(problems))

    def close(self) -> tuple[str, ...]:
        if self._closed:
            return ()
        self._closed = True
        problems = list(self._stop_role_processes())
        problems.extend(self._remove_anchor(self._subject_name))
        problems.extend(self._remove_anchor(self._probe_name))
        problems.extend(self.toxiproxy.cleanup())
        return tuple(problems)

    def __enter__(self) -> "ToxiproxyLiveLab":
        self.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _preflight(self) -> None:
        if not sys.platform.startswith("linux"):
            raise ToxiproxyPrerequisiteError("TEL-002 live evidence requires native Linux")
        worker = self.workspace / "tests" / "acceptance" / "network_control" / "toxiproxy_worker.py"
        if not self.workspace.is_dir() or not worker.is_file():
            raise ToxiproxyPrerequisiteError("workspace does not contain the TEL-002 role worker")
        info = self.docker.run("info", "--format", "{{json .}}")
        try:
            document = json.loads(info)
        except json.JSONDecodeError as exc:
            raise ToxiproxyPrerequisiteError("Docker info is not valid JSON") from exc
        operating_system = str(document.get("OperatingSystem", ""))
        os_type = str(document.get("OSType", ""))
        architecture = str(document.get("Architecture", ""))
        if os_type != "linux" or architecture not in {"x86_64", "amd64"}:
            raise ToxiproxyPrerequisiteError(
                f"TEL-002 canonical live binding requires linux/amd64 Docker, got {os_type}/{architecture}"
            )
        if "docker desktop" in operating_system.lower():
            raise ToxiproxyPrerequisiteError("Docker Desktop topology is unsupported for TEL-002 evidence")

    def _prepare_helper_artifact(self) -> None:
        self.docker.run("pull", "--platform", self.helper_artifact.platform, self.helper_artifact.image_ref)
        repo_digests = self.docker.run(
            "image",
            "inspect",
            self.helper_artifact.image_ref,
            "--format",
            "{{json .RepoDigests}}",
        )
        try:
            values = json.loads(repo_digests)
        except json.JSONDecodeError as exc:
            raise ToxiproxyPrerequisiteError("helper image RepoDigests are invalid JSON") from exc
        if not isinstance(values, list) or self.helper_artifact.image_ref not in values:
            raise ToxiproxyPrerequisiteError("helper image exact digest cannot be verified locally")

    def _wait_for_toxiproxy_version(self, admin: ToxiproxyAdminClient) -> None:
        deadline = time.monotonic() + self._role_response_timeout_s
        last_problem: RuntimeError | None = None
        while time.monotonic() < deadline:
            try:
                self.toxiproxy.verify_version(admin)
                return
            except RuntimeError as exc:
                last_problem = exc
                # Bounded process readiness only; not fault settlement/recovery.
                remaining = max(0.0, deadline - time.monotonic())
                if remaining:
                    time.sleep(min(0.02, remaining))
        raise ToxiproxyPrerequisiteError("Toxiproxy admin API did not become ready") from last_problem

    def _start_anchor(self, name: str, address: str) -> None:
        self.docker.run(
            "run",
            "-d",
            "--name",
            name,
            "--network",
            self.topology.data_network,
            "--ip",
            address,
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--mount",
            self._workspace_mount,
            "--workdir",
            "/workspace",
            "-e",
            "PYTHONPATH=/workspace/tests",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
            self.helper_artifact.image_ref,
            "python",
            "-c",
            "import signal; signal.pause()",
        )

    def _start_fixture(self, *, name: str, endpoint: MaterializedEndpoint) -> _RoleProcess:
        process = self._interactive_container(
            name=name,
            network_args=("--network", self.topology.data_network, "--ip", endpoint.address),
            capability_args=("--cap-drop=ALL",),
            worker_command="fixture",
        )
        try:
            process.send(
                {
                    "endpoint": _endpoint_document(endpoint),
                    "hygieneTimeoutS": max(
                        2.0,
                        self.observation_budget_ns / 1_000_000_000 + 1.0,
                    ),
                }
            )
            ready = process.receive()
            if ready.get("event") != "ready" or ready.get("endpoint") != _endpoint_document(endpoint):
                raise ToxiproxyPrerequisiteError(
                    "fixture worker did not bind the materialized endpoint"
                )
            return process
        except BaseException:
            process.close()
            raise

    def _start_witness(
        self,
        *,
        target_container: str,
        source_address: str,
        expected_target: MaterializedEndpoint,
        channel: str,
        role_id: str,
        attempt_id: str,
    ) -> _RoleProcess:
        suffix = hashlib.sha256(f"{attempt_id}:{channel}".encode("utf-8")).hexdigest()[:10]
        name = f"avp-nc-witness-{self.topology.run_token}-{suffix}"
        process = self._interactive_container(
            name=name,
            network_args=("--network", f"container:{target_container}"),
            capability_args=("--cap-drop=ALL", "--cap-add=NET_RAW"),
            worker_command="witness",
        )
        try:
            process.send(
                {
                    "attemptId": attempt_id,
                    "sourceAddress": source_address,
                    "expectedTarget": _endpoint_document(expected_target),
                    "channel": channel,
                    "roleId": role_id,
                    "assurance": {
                        "egressCoverageVerified": self.capture_assurance.egress_coverage_verified,
                        "directionalityVerified": self.capture_assurance.directionality_verified,
                        "offloadNormalizationVerified": self.capture_assurance.offload_normalization_verified,
                        "preSynConnectGapClosed": self.capture_assurance.pre_syn_connect_gap_closed,
                    },
                }
            )
            ready = process.receive()
            if ready.get("event") != "ready" or ready.get("attemptId") != attempt_id:
                raise ToxiproxyPrerequisiteError("witness worker did not reach arm/admit barrier")
            return process
        except BaseException:
            process.close()
            raise

    def _interactive_container(
        self,
        *,
        name: str,
        network_args: tuple[str, ...],
        capability_args: tuple[str, ...],
        worker_command: str,
    ) -> _RoleProcess:
        command = [
            self.docker.executable,
            "run",
            "--rm",
            "-i",
            "--name",
            name,
            *network_args,
            "--read-only",
            *capability_args,
            "--security-opt=no-new-privileges",
            "--mount",
            self._workspace_mount,
            "--workdir",
            "/workspace",
            "-e",
            "PYTHONPATH=/workspace/tests",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
            self.helper_artifact.image_ref,
            "python",
            "-m",
            _WORKER_MODULE,
            worker_command,
        ]
        try:
            process = self._popen_factory(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            raise ToxiproxyPrerequisiteError("cannot start interactive Docker role") from exc
        return _RoleProcess(
            process,
            container_name=name,
            docker=self.docker,
            response_timeout_s=self._role_response_timeout_s,
        )

    def _execute_role_exchange(
        self,
        *,
        container_name: str,
        endpoint: MaterializedEndpoint,
        attempt_document: dict[str, object],
        extra_connect: bool,
    ) -> dict[str, object]:
        payload = json.dumps(
            {
                "endpoint": _endpoint_document(endpoint),
                "attempt": attempt_document,
                "observationBudgetNs": self.observation_budget_ns,
                "extraConnect": extra_connect,
            },
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
        completed = self._run_bounded(
            [
                self.docker.executable,
                "exec",
                "-i",
                container_name,
                "python",
                "-m",
                _WORKER_MODULE,
                "exchange",
            ],
            input_text=payload,
        )
        value = json.loads(completed.stdout)
        if not isinstance(value, dict) or value.get("attemptId") != attempt_document["attemptId"]:
            raise ToxiproxyControlError("Subject role returned invalid attempt observation")
        return value

    def _verify_namespace_inventory(self) -> None:
        subject = self._inventory_for_container(self._subject_name)
        if subject != {self.addresses.subject}:
            raise ToxiproxyPrerequisiteError(
                f"Subject namespace has unexpected non-loopback IPv4 set: {subject}"
            )
        probe = self._inventory_for_container(self._probe_name)
        if probe != {self.addresses.privileged_probe}:
            raise ToxiproxyPrerequisiteError(
                f"probe namespace has unexpected non-loopback IPv4 set: {probe}"
            )
        toxiproxy = self._inventory_for_shared_namespace(self.topology.container_name)
        expected = {self.topology.admin_address, self.topology.data_address}
        if toxiproxy != expected:
            raise ToxiproxyPrerequisiteError(
                f"Toxiproxy namespace has unexpected non-loopback IPv4 set: {toxiproxy}"
            )

    def _inventory_for_container(self, container_name: str) -> set[str]:
        completed = self._run_bounded(
            [
                self.docker.executable,
                "exec",
                container_name,
                "python",
                "-m",
                _WORKER_MODULE,
                "inventory",
            ]
        )
        return _non_loopback_addresses(completed.stdout)

    def _inventory_for_shared_namespace(self, container_name: str) -> set[str]:
        completed = self._run_bounded(
            [
                self.docker.executable,
                "run",
                "--rm",
                "--network",
                f"container:{container_name}",
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--mount",
                self._workspace_mount,
                "--workdir",
                "/workspace",
                "-e",
                "PYTHONPATH=/workspace/tests",
                "-e",
                "PYTHONDONTWRITEBYTECODE=1",
                self.helper_artifact.image_ref,
                "python",
                "-m",
                _WORKER_MODULE,
                "inventory",
            ]
        )
        return _non_loopback_addresses(completed.stdout)

    def _verify_subject_admin_isolation(self) -> bool:
        script = (
            "import socket; s=socket.socket(); s.settimeout(0.5); "
            f"r=s.connect_ex(('{self.topology.admin_address}',8474)); s.close(); print(r)"
        )
        completed = self._run_bounded(
            [self.docker.executable, "exec", self._subject_name, "python", "-c", script]
        )
        try:
            return int(completed.stdout.strip()) != 0
        except ValueError as exc:
            raise ToxiproxyPrerequisiteError("admin-isolation probe returned invalid result") from exc

    def _run_bounded(
        self,
        command: list[str],
        *,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        timeout_s = max(
            self._role_response_timeout_s,
            self.observation_budget_ns / 1_000_000_000 + 1.0,
        )
        try:
            completed = self._run_factory(
                command,
                input=input_text,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ToxiproxyPrerequisiteError(
                f"bounded TEL-002 role command failed: {command!r}"
            ) from exc
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "role command failed").strip()
            raise ToxiproxyControlError(
                f"TEL-002 role command failed ({completed.returncode}): {detail}"
            )
        return completed

    def _stop_role_processes(self) -> tuple[str, ...]:
        problems: list[str] = []
        for fixture in (self._selected_fixture, self._control_fixture):
            if fixture is None:
                continue
            try:
                fixture.request({"op": "stop"})
            except RuntimeError as exc:
                problems.append(f"fixture-stop:{fixture.container_name}:{type(exc).__name__}")
            problems.extend(fixture.close())
        self._selected_fixture = None
        self._control_fixture = None
        return tuple(problems)

    def _remove_anchor(self, name: str) -> tuple[str, ...]:
        try:
            self.docker.run("rm", "-f", name, allow_failure=True)
        except RuntimeError as exc:
            return (f"anchor-cleanup:{name}:{type(exc).__name__}",)
        return ()

    def _require_materialization(self) -> LiveMaterialization:
        if self._materialization is None:
            raise RuntimeError("TEL-002 live lab is not materialized")
        return self._materialization

    @property
    def _workspace_mount(self) -> str:
        return f"type=bind,src={self.workspace},dst=/workspace,readonly"


def _non_loopback_addresses(payload: str) -> set[str]:
    document = json.loads(payload)
    interfaces = document.get("interfaces")
    if not isinstance(interfaces, list):
        raise ToxiproxyControlError("network inventory lacks interfaces list")
    return {
        str(item["ipv4Address"])
        for item in interfaces
        if isinstance(item, dict) and not bool(item.get("loopback", False))
    }


def _facts_from_witness_document(document: dict[str, object], channel: str) -> InitiationFacts:
    values = document.get("channelFacts")
    if not isinstance(values, list) or len(values) != 1 or not isinstance(values[0], dict):
        raise ToxiproxyControlError(f"witness {channel!r} did not return one facts record")
    item = values[0]
    if str(item.get("channel")) != channel:
        raise ToxiproxyControlError(f"witness channel mismatch for {channel!r}")
    validity = item.get("validityProblems", [])
    if not isinstance(validity, list):
        raise ToxiproxyControlError("witness validity problems must be a list")
    return InitiationFacts(
        channel=channel,
        total_initiations=int(item["totalInitiations"]),
        expected_target_initiations=int(item["expectedTargetInitiations"]),
        alternate_target_initiations=int(item["alternateTargetInitiations"]),
        raw_syn_packets=int(item["rawSynPackets"]),
        retransmitted_syn_packets=int(item["retransmittedSynPackets"]),
        validity_problems=tuple(str(problem) for problem in validity),
    )


def _combine_upstream_witnesses(documents: list[dict[str, object]]) -> InitiationFacts:
    if len(documents) != 2:
        raise ToxiproxyControlError("upstream evidence requires data and admin namespace witnesses")
    data = _facts_from_witness_document(documents[0], "W-upstream-data")
    admin = _facts_from_witness_document(documents[1], "W-upstream-admin")
    facts = (data, admin)
    return InitiationFacts(
        channel="W-upstream",
        total_initiations=sum(item.total_initiations for item in facts),
        expected_target_initiations=sum(item.expected_target_initiations for item in facts),
        alternate_target_initiations=sum(item.alternate_target_initiations for item in facts),
        raw_syn_packets=sum(item.raw_syn_packets for item in facts),
        retransmitted_syn_packets=sum(item.retransmitted_syn_packets for item in facts),
        validity_problems=tuple(
            dict.fromkeys(problem for item in facts for problem in item.validity_problems)
        ),
    )

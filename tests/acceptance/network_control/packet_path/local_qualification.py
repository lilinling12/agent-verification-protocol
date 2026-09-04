"""Explicit opt-in native-Linux qualification for Network Control PTL-001.

This entrypoint is intentionally local and privileged. It is not referenced by a
GitHub Actions workflow and it never grants privilege itself. The caller must
supply an explicit acknowledgement flag and already be native-Linux root. The
run proves the reviewed packet-path topology, Subject isolation, route placement,
Subject-egress witness assumptions, selected cut, non-target survival, recovery,
and residual-free cleanup before reporting qualification readiness.
"""

from __future__ import annotations

import argparse
import json
import os
import select
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from ..attempt_client import ExchangeObservation
from ..evidence_core import AttemptFactory, EvidenceMaterializationError, ExchangeProgram
from ..witness_evidence import CaptureAssurance
from .controller import BoundedLinuxCli, PacketPathController, PacketPathControlError
from .execution import PacketPathActor, PacketPathExecutionPlan
from .live_qualification import (
    CleanupObservation,
    NamespaceInventoryObservation,
    PacketPathLiveQualification,
    PacketPathQualificationCommands,
    PacketPathQualificationObservations,
    PacketPathWitnessCanarySpec,
    PreflightObservation,
    QualifiedExchangeObservation,
    RouteObservation,
    SubjectSecurityObservation,
    WitnessCanaryObservation,
    derive_capture_assurance,
    parse_namespace_inventory,
    parse_route_candidates,
)
from .qualification import PacketPathQualificationPlan
from .topology import PacketPathRunTopology
from .worker import _attempt_document, _endpoint_document

_OPT_IN_FLAG = "--allow-local-privileged-network-mutation"
_WORKER_MODULE = "acceptance.network_control.packet_path.worker"
_AEP_PATH = "rfcs/AEP-0012-network-control-resource-profile.md"
_DEFAULT_BASELINE = "140ad041953ebea57a37273a63145258bba2a6ac"


class PacketPathLocalQualificationError(RuntimeError):
    """Raised when local privileged qualification cannot prove a reviewed fact."""


@dataclass(frozen=True, slots=True)
class _AttemptResult:
    exchange: ExchangeObservation
    witness: Mapping[str, object]


class _JsonRole:
    """Bounded JSON-lines control for one local foreground worker process."""

    def __init__(self, process: subprocess.Popen[str], *, label: str, timeout_s: float) -> None:
        if process.stdin is None or process.stdout is None:
            raise PacketPathLocalQualificationError(f"{label} requires stdin/stdout pipes")
        self.process = process
        self.stdin = process.stdin
        self.stdout = process.stdout
        self.label = label
        self.timeout_s = timeout_s
        self._closed = False

    def send(self, document: Mapping[str, object]) -> None:
        self.stdin.write(json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
        self.stdin.flush()

    def receive(self) -> dict[str, object]:
        ready, _write, _error = select.select([self.stdout.fileno()], [], [], self.timeout_s)
        if not ready:
            raise PacketPathLocalQualificationError(f"{self.label} response deadline expired")
        line = self.stdout.readline()
        if not line:
            stderr = ""
            if self.process.stderr is not None:
                stderr = self.process.stderr.read().strip()
            raise PacketPathLocalQualificationError(
                f"{self.label} exited before response publication"
                + (f": {stderr}" if stderr else "")
            )
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PacketPathLocalQualificationError(f"{self.label} emitted invalid JSON") from exc
        if not isinstance(value, dict):
            raise PacketPathLocalQualificationError(f"{self.label} response is not an object")
        if value.get("ok") is False:
            raise PacketPathLocalQualificationError(str(value.get("error", f"{self.label} failed")))
        return value

    def request(self, document: Mapping[str, object]) -> dict[str, object]:
        self.send(document)
        return self.receive()

    def close(self) -> tuple[str, ...]:
        if self._closed:
            return ()
        self._closed = True
        problems: list[str] = []
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=self.timeout_s)
            except subprocess.TimeoutExpired:
                self.process.kill()
                try:
                    self.process.wait(timeout=self.timeout_s)
                except subprocess.TimeoutExpired:
                    problems.append(f"role-stuck:{self.label}")
        return tuple(problems)


class PacketPathLocalQualification:
    """Execute one finite positive PTL-001 qualification run on local Linux root."""

    def __init__(
        self,
        *,
        workspace: Path,
        run_id: str,
        semantic_baseline_commit: str,
        observation_budget_ns: int,
        role_timeout_s: float = 5.0,
        cli: BoundedLinuxCli | None = None,
    ) -> None:
        self.workspace = Path(workspace).resolve()
        self.run_id = run_id
        self.semantic_baseline_commit = semantic_baseline_commit
        self.observation_budget_ns = observation_budget_ns
        self.role_timeout_s = float(role_timeout_s)
        if not self.workspace.is_dir():
            raise EvidenceMaterializationError("packet-path local qualification workspace is missing")
        if not run_id:
            raise EvidenceMaterializationError("packet-path local qualification run id is required")
        if observation_budget_ns <= 0:
            raise EvidenceMaterializationError("packet-path local qualification budget must be positive")
        if self.role_timeout_s <= 0:
            raise EvidenceMaterializationError("packet-path local qualification role timeout must be positive")

        self.topology = PacketPathRunTopology.for_run(run_id)
        self.cli = cli or BoundedLinuxCli(command_timeout_s=max(10.0, self.role_timeout_s))
        self.controller = PacketPathController(topology=self.topology, cli=self.cli)
        self.plan = self.topology.evidence_plan(
            design_revision="NPR-011-packet-path-v0.1",
            semantic_baseline_commit=semantic_baseline_commit,
            semantic_baseline_path=_AEP_PATH,
            path_id="network-control-selected-path",
            exchange_program=ExchangeProgram(
                program_id="exact-byte-v0.1",
                request_prefix=b"AVP-NC-REQ\x00",
                request_suffix=b"\x00END",
                response_prefix=b"AVP-NC-RESP\x00",
                response_suffix=b"\x00END",
            ),
            observation_budget_ns=observation_budget_ns,
        )
        self.execution = PacketPathExecutionPlan.build(
            topology=self.topology,
            evidence_plan=self.plan,
        )
        self.qualification_plan = PacketPathQualificationPlan.for_topology(self.topology)
        self.commands = PacketPathQualificationCommands.build(
            topology=self.topology,
            controller=self.controller,
            execution_plan=self.execution,
            qualification_plan=self.qualification_plan,
            python_executable=sys.executable,
        )
        self.attempt_factory = AttemptFactory()
        self._ordinal = 0
        self._selected_fixture: _JsonRole | None = None
        self._control_fixture: _JsonRole | None = None

    def execute(self) -> dict[str, object]:
        """Run qualification and return a project-local diagnostic document."""

        preflight = self._preflight()
        setup_complete = False
        cleanup = CleanupObservation((), ())
        primary: BaseException | None = None
        observations: PacketPathQualificationObservations | None = None
        try:
            self.controller.setup()
            setup_complete = True
            namespaces = self._namespace_observations()
            routes = self._route_observation()
            security = self._subject_security_observation()
            canaries = self._capture_canaries()
            assurance = derive_capture_assurance(canaries)
            if assurance.problems():
                raise PacketPathLocalQualificationError(
                    f"packet-path capture assurance did not qualify: {assurance.problems()!r}"
                )

            self._start_fixtures()
            baseline = self._certified_attempt("baseline", actor=PacketPathActor.SUBJECT, assurance=assurance)
            if not _successful_exchange(baseline.exchange):
                raise PacketPathLocalQualificationError("packet-path baseline exact exchange failed")
            pre_trigger = self._certified_attempt("pre-trigger", actor=PacketPathActor.SUBJECT, assurance=assurance)
            if not _successful_exchange(pre_trigger.exchange):
                raise PacketPathLocalQualificationError("packet-path pre-trigger exact exchange failed")

            self.controller.install_fault()
            settlement = self._certified_attempt(
                "activation-settlement",
                actor=PacketPathActor.PRIVILEGED_PROBE,
                assurance=assurance,
            )
            if not _cut_exchange(settlement.exchange):
                raise PacketPathLocalQualificationError("packet-path activation settlement was not independently observed")
            active_cut = self._certified_attempt(
                "subject-active-cut",
                actor=PacketPathActor.SUBJECT,
                assurance=assurance,
            )
            control = self._certified_attempt(
                "non-target-control",
                actor=PacketPathActor.SUBJECT,
                assurance=assurance,
            )
            self.controller.clear_fault()
            recovery_1 = self._certified_attempt(
                "recovery-1",
                actor=PacketPathActor.PRIVILEGED_PROBE,
                assurance=assurance,
            )
            recovery_2 = self._certified_attempt(
                "recovery-2",
                actor=PacketPathActor.PRIVILEGED_PROBE,
                assurance=assurance,
            )
            stability = self._certified_attempt(
                "stability",
                actor=PacketPathActor.SUBJECT,
                assurance=assurance,
            )

            observations = PacketPathQualificationObservations(
                preflight=preflight,
                namespaces=namespaces,
                routes=routes,
                subject_security=security,
                exchanges=(
                    QualifiedExchangeObservation("subject-active-cut", active_cut.exchange),
                    QualifiedExchangeObservation("non-target-control", control.exchange),
                    QualifiedExchangeObservation("recovery-1", recovery_1.exchange),
                    QualifiedExchangeObservation("recovery-2", recovery_2.exchange),
                    QualifiedExchangeObservation("stability", stability.exchange),
                ),
                witness_canaries=canaries,
                cleanup=CleanupObservation((), ()),
            )
        except BaseException as exc:
            primary = exc
        finally:
            fixture_problems = self._stop_fixtures()
            cleanup_problems = tuple(fixture_problems)
            if setup_complete:
                cleanup_problems += self.controller.cleanup()
                try:
                    residual = self.controller.residual_resources()
                except BaseException as exc:
                    residual = (f"residual-check:{type(exc).__name__}",)
            else:
                residual = ()
            cleanup = CleanupObservation(cleanup_problems, residual)

        if primary is not None:
            for problem in (*cleanup.cleanup_problems, *cleanup.residual_resources):
                primary.add_note(f"packet-path qualification cleanup: {problem}")
            raise primary
        if observations is None:
            raise AssertionError("packet-path qualification completed without observations")

        observations = PacketPathQualificationObservations(
            preflight=observations.preflight,
            namespaces=observations.namespaces,
            routes=observations.routes,
            subject_security=observations.subject_security,
            exchanges=observations.exchanges,
            witness_canaries=observations.witness_canaries,
            cleanup=cleanup,
        )
        report = PacketPathLiveQualification(self.commands).project_report(observations)
        return {
            "format": "avp-project-network-packet-path-local-qualification-v0.1",
            "runId": self.run_id,
            "ready": report.ready,
            "problems": list(report.problems()),
            "captureAssurance": {
                "egressCoverageVerified": report.capture_assurance.egress_coverage_verified,
                "directionalityVerified": report.capture_assurance.directionality_verified,
                "offloadNormalizationVerified": report.capture_assurance.offload_normalization_verified,
                "preSynConnectGapClosed": report.capture_assurance.pre_syn_connect_gap_closed,
            },
            "facts": [
                {
                    "property": fact.property.value,
                    "source": fact.source.value,
                    "verified": fact.verified,
                    "detail": fact.detail,
                }
                for fact in report.facts
            ],
            "cleanup": {
                "problems": list(cleanup.cleanup_problems),
                "residualResources": list(cleanup.residual_resources),
            },
        }

    def _preflight(self) -> PreflightObservation:
        if not sys.platform.startswith("linux"):
            raise PacketPathLocalQualificationError("PTL-001 local qualification requires native Linux")
        if os.geteuid() != 0:
            raise PacketPathLocalQualificationError("PTL-001 local qualification requires euid 0")
        worker = self.workspace / "tests" / "acceptance" / "network_control" / "packet_path" / "worker.py"
        if not worker.is_file():
            raise PacketPathLocalQualificationError("workspace does not contain packet-path worker")

        uname = self.cli.run(("uname", "-srm")).stdout.strip()
        uid_text = self.cli.run(("id", "-u")).stdout.strip()
        try:
            effective_uid = int(uid_text, 10)
        except ValueError as exc:
            raise PacketPathLocalQualificationError("id -u did not return an integer") from exc
        versions = (
            ("ip", self.cli.run(("ip", "-Version")).stdout.strip()),
            ("nft", self.cli.run(("nft", "--version")).stdout.strip()),
            ("setpriv", self.cli.run(("setpriv", "--version")).stdout.strip()),
            ("python", self.cli.run((sys.executable, "--version")).stdout.strip() or self.cli.run((sys.executable, "--version")).stderr.strip()),
        )
        return PreflightObservation(uname, effective_uid, versions)

    def _namespace_observations(self) -> tuple[NamespaceInventoryObservation, ...]:
        values: list[NamespaceInventoryObservation] = []
        for namespace, command in self.commands.inventory_commands():
            result = self._run_worker_once(command)
            values.append(parse_namespace_inventory(namespace_name=namespace, document=result))
        return tuple(values)

    def _route_observation(self) -> RouteObservation:
        subject_command, fixture_command = self.commands.route_commands()
        subject = self.cli.run(subject_command).stdout
        fixture = self.cli.run(fixture_command).stdout
        return RouteObservation(
            subject_to_fixture=parse_route_candidates(subject, target_address=self.topology.fixture_address),
            fixture_to_subject=parse_route_candidates(fixture, target_address=self.topology.subject_address),
        )

    def _subject_security_observation(self) -> SubjectSecurityObservation:
        document = self._run_worker_once(
            self.commands.subject_security_command(),
            input_document=self.commands.subject_security_input(),
        )
        capabilities = document.get("capabilities")
        environment = document.get("environmentPresence")
        if not isinstance(capabilities, dict) or not isinstance(environment, dict):
            raise PacketPathLocalQualificationError("Subject security probe response is incomplete")
        groups = document.get("supplementaryGroups")
        if not isinstance(groups, list) or not all(isinstance(item, int) for item in groups):
            raise PacketPathLocalQualificationError("Subject security groups are invalid")
        return SubjectSecurityObservation(
            uid=_required_int(document, "uid"),
            euid=_required_int(document, "euid"),
            gid=_required_int(document, "gid"),
            egid=_required_int(document, "egid"),
            supplementary_groups=tuple(groups),
            no_new_privs=_required_int(document, "noNewPrivs"),
            capability_values=tuple(
                _required_string(capabilities, key)
                for key in ("inheritable", "permitted", "effective", "bounding", "ambient")
            ),
            netns_identity=_required_string(document, "netNamespace"),
            environment_presence=tuple(
                sorted((str(key), bool(value)) for key, value in environment.items())
            ),
        )

    def _capture_canaries(self) -> tuple[WitnessCanaryObservation, ...]:
        observations: list[WitnessCanaryObservation] = []
        for index, spec in enumerate(self.commands.capture_canaries()):
            attempt_id = f"qualification-canary-{index}-{self.topology.run_token}"
            witness_command, witness_input = self.commands.witness_command_and_input(
                spec=spec,
                attempt_id=attempt_id,
            )
            witness = self._start_role(witness_command, label=f"witness-canary:{spec.label}")
            try:
                witness.send(witness_input)
                ready = witness.receive()
                ready_before_injection = ready.get("event") == "ready" and ready.get("attemptId") == attempt_id
                self._inject_canary(spec)
                witness.send({"op": "close", "attemptId": attempt_id})
                result = witness.receive()
            finally:
                problems = witness.close()
            if problems:
                raise PacketPathLocalQualificationError(f"canary witness cleanup failed: {problems!r}")
            observations.append(
                _canary_observation(
                    spec.label,
                    result,
                    ready_before_injection=ready_before_injection,
                )
            )
        return tuple(observations)

    def _inject_canary(self, spec: PacketPathWitnessCanarySpec) -> None:
        command = (
            "ip",
            "netns",
            "exec",
            self.topology.subject_namespace,
            sys.executable,
            "-c",
            _raw_syn_script(self.topology.subject_address, spec),
        )
        completed = subprocess.run(
            list(command),
            check=False,
            capture_output=True,
            text=True,
            timeout=self.role_timeout_s,
            env=self._worker_environment(),
        )
        if completed.returncode != 0:
            raise PacketPathLocalQualificationError(
                f"capture canary injector failed for {spec.label}: {completed.stderr.strip()}"
            )

    def _start_fixtures(self) -> None:
        self._selected_fixture = self._start_fixture("selected", self.topology.selected_endpoint)
        try:
            self._control_fixture = self._start_fixture("control", self.topology.control_endpoint)
        except BaseException:
            self._stop_fixtures()
            raise

    def _start_fixture(self, label: str, endpoint: object) -> _JsonRole:
        command = self.controller.fixture_command((sys.executable, "-m", _WORKER_MODULE, "fixture"))
        role = self._start_role(command, label=f"fixture:{label}")
        role.send({"endpoint": _endpoint_document(endpoint)})
        ready = role.receive()
        if ready.get("event") != "ready":
            role.close()
            raise PacketPathLocalQualificationError(f"fixture {label} did not publish readiness")
        return role

    def _stop_fixtures(self) -> tuple[str, ...]:
        problems: list[str] = []
        for label, role in (("selected", self._selected_fixture), ("control", self._control_fixture)):
            if role is None:
                continue
            try:
                if role.process.poll() is None:
                    response = role.request({"op": "stop"})
                    if response.get("op") != "stop":
                        problems.append(f"fixture-stop-ack:{label}")
            except BaseException as exc:
                problems.append(f"fixture-stop:{label}:{type(exc).__name__}")
            problems.extend(role.close())
        self._selected_fixture = None
        self._control_fixture = None
        return tuple(problems)

    def _certified_attempt(
        self,
        phase_id: str,
        *,
        actor: PacketPathActor,
        assurance: CaptureAssurance,
    ) -> _AttemptResult:
        step = next(
            (item for item in self.execution.attempt_steps if item.attempt_phase == phase_id),
            None,
        )
        if step is None or step.target is None:
            raise PacketPathLocalQualificationError(f"execution plan lacks attempt phase {phase_id!r}")
        if step.actor is not actor:
            raise PacketPathLocalQualificationError(f"execution actor drift for phase {phase_id!r}")
        self._ordinal += 1
        attempt = self.attempt_factory.issue(self.plan, phase_id=phase_id, ordinal=self._ordinal)
        fixture = self._control_fixture if phase_id == "non-target-control" else self._selected_fixture
        if fixture is None:
            raise PacketPathLocalQualificationError("packet-path fixture is unavailable")
        fixture.request({"op": "arm", "attempt": _attempt_document(attempt)})

        witness_command, witness_input = self._attempt_witness_command(
            phase_id=phase_id,
            attempt_id=attempt.attempt_id,
            target=step.target,
            assurance=assurance,
            privileged=actor is PacketPathActor.PRIVILEGED_PROBE,
        )
        witness = self._start_role(witness_command, label=f"attempt-witness:{phase_id}")
        primary: BaseException | None = None
        result_document: dict[str, object] | None = None
        exchange_document: dict[str, object] | None = None
        try:
            witness.send(witness_input)
            ready = witness.receive()
            if ready.get("event") != "ready" or ready.get("attemptId") != attempt.attempt_id:
                raise PacketPathLocalQualificationError(f"attempt witness was not ready for {phase_id}")
            exchange_document = self._run_exchange(
                step=step,
                attempt_document=_attempt_document(attempt),
                actor=actor,
            )
        except BaseException as exc:
            primary = exc
        finally:
            try:
                fixture.request({"op": "disarm", "attemptId": attempt.attempt_id})
            except BaseException as exc:
                if primary is None:
                    primary = exc
                else:
                    primary.add_note(f"fixture-disarm:{type(exc).__name__}")
            try:
                witness.send({"op": "close", "attemptId": attempt.attempt_id})
                result_document = witness.receive()
            except BaseException as exc:
                if primary is None:
                    primary = exc
                else:
                    primary.add_note(f"witness-close:{type(exc).__name__}")
            for problem in witness.close():
                if primary is not None:
                    primary.add_note(problem)
        if primary is not None:
            raise primary
        if exchange_document is None or result_document is None:
            raise AssertionError("certified attempt completed without exchange/witness documents")
        _require_one_expected_initiation(result_document)
        return _AttemptResult(
            exchange=_exchange_from_document(exchange_document),
            witness=result_document,
        )

    def _attempt_witness_command(
        self,
        *,
        phase_id: str,
        attempt_id: str,
        target: object,
        assurance: CaptureAssurance,
        privileged: bool,
    ) -> tuple[tuple[str, ...], dict[str, object]]:
        from .witness_binding import PacketPathWitnessBinding

        binding = PacketPathWitnessBinding.for_attempt(
            topology=self.topology,
            plan=self.plan,
            expected_target=target,
            assurance=assurance,
            privileged_probe=privileged,
        )
        return (
            binding.evaluator_namespace_command((sys.executable, "-m", _WORKER_MODULE, "witness")),
            {
                "interfaceName": binding.interface_name,
                "sourceAddress": self.topology.subject_address,
                "expectedTarget": _endpoint_document(target),
                "channel": binding.scope.channel,
                "roleId": binding.scope.role_id,
                "attemptId": attempt_id,
                "assurance": {
                    "egressCoverageVerified": assurance.egress_coverage_verified,
                    "directionalityVerified": assurance.directionality_verified,
                    "offloadNormalizationVerified": assurance.offload_normalization_verified,
                    "preSynConnectGapClosed": assurance.pre_syn_connect_gap_closed,
                },
            },
        )

    def _run_exchange(
        self,
        *,
        step: object,
        attempt_document: Mapping[str, object],
        actor: PacketPathActor,
    ) -> dict[str, object]:
        target = step.target
        command = (sys.executable, "-m", _WORKER_MODULE, "exchange")
        if actor is PacketPathActor.SUBJECT:
            argv = self.controller.subject_command(command)
        elif actor is PacketPathActor.PRIVILEGED_PROBE:
            argv = ("ip", "netns", "exec", self.topology.subject_namespace, *command)
        else:
            raise PacketPathLocalQualificationError("unsupported packet-path attempt actor")
        payload: dict[str, object] = {
            "endpoint": _endpoint_document(target),
            "attempt": dict(attempt_document),
            "observationBudgetNs": self.observation_budget_ns,
        }
        if len(step.connection_targets) == 2:
            payload["additionalConnectTarget"] = _endpoint_document(step.connection_targets[1])
        return self._run_worker_once(argv, input_document=payload)

    def _run_worker_once(
        self,
        command: Sequence[str],
        *,
        input_document: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        payload = "" if input_document is None else json.dumps(input_document, sort_keys=True, separators=(",", ":")) + "\n"
        completed = subprocess.run(
            list(command),
            input=payload,
            check=False,
            capture_output=True,
            text=True,
            timeout=max(self.role_timeout_s, self.observation_budget_ns / 1_000_000_000 + 1.0),
            env=self._worker_environment(),
        )
        if completed.returncode != 0:
            raise PacketPathLocalQualificationError(
                f"worker command failed ({completed.returncode}) {list(command)!r}: {completed.stderr.strip()}"
            )
        line = completed.stdout.strip()
        if not line:
            raise PacketPathLocalQualificationError("worker command emitted no JSON document")
        try:
            value = json.loads(line.splitlines()[-1])
        except json.JSONDecodeError as exc:
            raise PacketPathLocalQualificationError("worker command emitted invalid JSON") from exc
        if not isinstance(value, dict):
            raise PacketPathLocalQualificationError("worker command output is not an object")
        return value

    def _start_role(self, command: Sequence[str], *, label: str) -> _JsonRole:
        process = subprocess.Popen(
            list(command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=self._worker_environment(),
        )
        return _JsonRole(process, label=label, timeout_s=self.role_timeout_s)

    def _worker_environment(self) -> dict[str, str]:
        environment = dict(os.environ)
        tests_path = str(self.workspace / "tests")
        existing = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = tests_path if not existing else tests_path + os.pathsep + existing
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return environment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AVP PTL-001 local privileged qualification")
    parser.add_argument(_OPT_IN_FLAG, action="store_true", dest="allow_privileged")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--semantic-baseline-commit", default=_DEFAULT_BASELINE)
    parser.add_argument("--observation-budget-ms", type=int, default=1000)
    args = parser.parse_args(argv)

    if not args.allow_privileged:
        parser.error(
            f"refusing network mutation without explicit {_OPT_IN_FLAG} acknowledgement"
        )
    if not sys.platform.startswith("linux"):
        parser.error("PTL-001 local qualification requires native Linux")
    if os.geteuid() != 0:
        parser.error("PTL-001 local qualification requires euid 0; privilege is never acquired automatically")
    if args.observation_budget_ms <= 0:
        parser.error("--observation-budget-ms must be positive")

    qualification = PacketPathLocalQualification(
        workspace=Path(args.workspace),
        run_id=args.run_id,
        semantic_baseline_commit=args.semantic_baseline_commit,
        observation_budget_ns=args.observation_budget_ms * 1_000_000,
    )
    document = qualification.execute()
    print(json.dumps(document, sort_keys=True, separators=(",", ":")))
    return 0 if bool(document.get("ready")) else 2


def _required_int(document: Mapping[str, object], key: str) -> int:
    value = document.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise PacketPathLocalQualificationError(f"worker field {key!r} must be integer")
    return value


def _required_string(document: Mapping[str, object], key: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value:
        raise PacketPathLocalQualificationError(f"worker field {key!r} must be non-empty string")
    return value


def _canary_observation(
    label: str,
    document: Mapping[str, object],
    *,
    ready_before_injection: bool,
) -> WitnessCanaryObservation:
    channel_facts = document.get("channelFacts")
    if not isinstance(channel_facts, list) or len(channel_facts) != 1 or not isinstance(channel_facts[0], dict):
        raise PacketPathLocalQualificationError("canary witness must publish exactly one channel fact")
    facts = channel_facts[0]
    validity = document.get("validityProblems")
    if not isinstance(validity, list) or not all(isinstance(item, str) for item in validity):
        raise PacketPathLocalQualificationError("canary witness validity problems are invalid")
    drops = document.get("captureDrops")
    if drops is not None and (isinstance(drops, bool) or not isinstance(drops, int)):
        raise PacketPathLocalQualificationError("canary witness captureDrops is invalid")
    return WitnessCanaryObservation(
        label=label,
        total_initiations=_required_int(facts, "totalInitiations"),
        expected_target_initiations=_required_int(facts, "expectedTargetInitiations"),
        alternate_target_initiations=_required_int(facts, "alternateTargetInitiations"),
        raw_syn_packets=_required_int(facts, "rawSynPackets"),
        retransmitted_syn_packets=_required_int(facts, "retransmittedSynPackets"),
        capture_drops=drops,
        validity_problems=tuple(validity),
        ready_before_injection=ready_before_injection,
    )


def _require_one_expected_initiation(document: Mapping[str, object]) -> None:
    channel_facts = document.get("channelFacts")
    validity = document.get("validityProblems")
    drops = document.get("captureDrops")
    if (
        not isinstance(channel_facts, list)
        or len(channel_facts) != 1
        or not isinstance(channel_facts[0], dict)
        or validity != []
        or drops != 0
    ):
        raise PacketPathLocalQualificationError("certified attempt witness integrity is invalid")
    facts = channel_facts[0]
    if not (
        facts.get("channel") == "W-front"
        and facts.get("totalInitiations") == 1
        and facts.get("expectedTargetInitiations") == 1
        and facts.get("alternateTargetInitiations") == 0
    ):
        raise PacketPathLocalQualificationError("certified attempt initiation cardinality is invalid")


def _exchange_from_document(document: Mapping[str, object]) -> ExchangeObservation:
    return ExchangeObservation(
        attempt_id=_required_string(document, "attemptId"),
        completed=bool(document.get("completed")),
        mismatch_observed=bool(document.get("mismatchObserved")),
        observation_budget_expired=bool(document.get("observationBudgetExpired")),
        elapsed_ns=_required_int(document, "elapsedNs"),
        response_size=_required_int(document, "responseSize"),
        response_sha256=(
            None
            if document.get("responseSha256") is None
            else _required_string(document, "responseSha256")
        ),
        native_error=(
            None
            if document.get("nativeError") is None
            else _required_string(document, "nativeError")
        ),
    )


def _successful_exchange(observation: ExchangeObservation) -> bool:
    return (
        observation.completed
        and not observation.mismatch_observed
        and not observation.observation_budget_expired
        and observation.native_error is None
    )


def _cut_exchange(observation: ExchangeObservation) -> bool:
    return (
        not observation.completed
        and not observation.mismatch_observed
        and observation.observation_budget_expired
        and observation.native_error is None
    )


def _raw_syn_script(source_address: str, spec: PacketPathWitnessCanarySpec) -> str:
    rows = tuple(
        (endpoint.address, endpoint.port, source_port, sequence)
        for endpoint, source_port, sequence in spec.packets
    )
    return (
        "import socket,struct,time\n"
        f"src={source_address!r}; rows={rows!r}\n"
        "def checksum(data):\n"
        " if len(data)%2: data+=b'\\x00'\n"
        " words=struct.unpack(f'!{len(data)//2}H',data); total=sum(words)\n"
        " while total>>16: total=(total&0xffff)+(total>>16)\n"
        " return (~total)&0xffff\n"
        "src_b=socket.inet_aton(src)\n"
        "sock=socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_RAW)\n"
        "sock.setsockopt(socket.IPPROTO_IP,socket.IP_HDRINCL,1)\n"
        "for dst,dport,sport,seq in rows:\n"
        " dst_b=socket.inet_aton(dst); ver_ihl=(4<<4)|5\n"
        " ip=struct.pack('!BBHHHBBH4s4s',ver_ihl,0,40,0x4A11,0,64,socket.IPPROTO_TCP,0,src_b,dst_b)\n"
        " ip=struct.pack('!BBHHHBBH4s4s',ver_ihl,0,40,0x4A11,0,64,socket.IPPROTO_TCP,checksum(ip),src_b,dst_b)\n"
        " flags=(5<<12)|0x002\n"
        " tcp=struct.pack('!HHLLHHHH',sport,dport,seq,0,flags,65535,0,0)\n"
        " pseudo=struct.pack('!4s4sBBH',src_b,dst_b,0,socket.IPPROTO_TCP,len(tcp))\n"
        " tcp=struct.pack('!HHLLHHHH',sport,dport,seq,0,flags,65535,checksum(pseudo+tcp),0)\n"
        " sock.sendto(ip+tcp,(dst,0)); time.sleep(0.01)\n"
        "sock.close()\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())

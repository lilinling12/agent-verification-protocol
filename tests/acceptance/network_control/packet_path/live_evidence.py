"""Concrete privileged packet-path evidence execution for Network Control PTL-002.

This module executes the already-reviewed PTL-001 Linux netns/veth/nftables
mechanism against one sealed positive or single-negative execution plan. It
retains exact attempt/witness/provenance artifacts and projects only observed
facts into ``PacketPathRunEvidence``. Portable C1-C12 assessment remains owned by
the unchanged provider-neutral comparator.

The implementation intentionally subclasses the concrete PTL-001 local runner to
reuse bounded process/topology plumbing. It is not a generic backend, provider
registry, SPI, or shared mechanism-control abstraction.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from ..attempt_client import ExchangeObservation
from ..evidence_core import (
    ArtifactRef,
    ArtifactStore,
    AttemptMaterial,
    EvidenceAssessment,
    EvidenceMaterializationError,
    ExchangeProgram,
)
from ..witness_evidence import CaptureAssurance
from .evidence_lane import parse_front_initiations
from .execution import (
    PacketPathActor,
    PacketPathExecutionPlan,
    PacketPathExecutionStep,
    PacketPathStepId,
)
from .local_qualification import (
    PacketPathLocalQualification,
    PacketPathLocalQualificationError,
)
from .negative_assemblies import (
    PacketPathNegativeAssembly,
    PacketPathNegativeMode,
)
from .projection import PacketPathAttemptEvidence, PacketPathRunEvidence
from .topology import PacketPathRunTopology
from .worker import _attempt_document, _endpoint_document

_AEP_PATH = "rfcs/AEP-0012-network-control-resource-profile.md"
_WORKER_MODULE = "acceptance.network_control.packet_path.worker"
_MATERIALIZATION_FORMAT = "avp-project-network-packet-path-live-materialization-v0.1"
_IMPLEMENTATION_FORMAT = "avp-project-network-packet-path-live-result-v0.1"
_SENSITIVE_SUBJECT_ENVIRONMENT = (
    "AVP_FUTURE_FAULT_SCHEDULE",
    "AVP_PACKET_PATH_CONTROL",
)


@dataclass(frozen=True, slots=True)
class PacketPathLiveAttempt:
    """Observed facts retained for one certified packet-path attempt."""

    attempt: AttemptMaterial
    exchange: ExchangeObservation
    witness_document: Mapping[str, object]
    attempt_ref: ArtifactRef
    exchange_ref: ArtifactRef
    witness_ref: ArtifactRef
    raw_witness_ref: ArtifactRef

    def portable(self) -> PacketPathAttemptEvidence:
        return PacketPathAttemptEvidence(
            phase_id=self.attempt.phase_id,
            attempt=self.attempt,
            exchange=self.exchange,
            front_initiations=parse_front_initiations(self.witness_document),
        )


@dataclass(frozen=True, slots=True)
class PacketPathLiveExecutionResult:
    """One concrete packet-path case result and retained implementation records."""

    assessment: EvidenceAssessment
    materialization_provenance_ref: ArtifactRef
    implementation_record_ref: ArtifactRef
    sealed_plan_ref: ArtifactRef


class PacketPathLiveEvidenceLab(PacketPathLocalQualification):
    """Execute one positive or single-negative packet-path evidence case."""

    def __init__(
        self,
        *,
        workspace: Path,
        artifact_store: ArtifactStore,
        run_id: str,
        semantic_baseline_commit: str,
        observation_budget_ns: int,
        capture_assurance: CaptureAssurance,
        negative_mode: PacketPathNegativeMode | None = None,
        role_timeout_s: float = 5.0,
    ) -> None:
        if capture_assurance.problems():
            raise EvidenceMaterializationError(
                "PTL-002 packet-path live evidence requires fully qualified capture assurance"
            )
        self.artifact_store = artifact_store
        self.capture_assurance = capture_assurance
        self.negative_mode = negative_mode
        super().__init__(
            workspace=workspace,
            run_id=run_id,
            semantic_baseline_commit=semantic_baseline_commit,
            observation_budget_ns=observation_budget_ns,
            role_timeout_s=role_timeout_s,
        )

        # Replace the qualification-only positive plan with the exact PTL-002
        # case plan. The controller and process plumbing remain the same concrete
        # packet-path implementation.
        self.topology = PacketPathRunTopology.for_run(run_id)
        self.controller = type(self.controller)(topology=self.topology, cli=self.cli)
        negative = (
            None
            if negative_mode is None
            else PacketPathNegativeAssembly.for_mode(
                topology=self.topology,
                mode=negative_mode,
            )
        )
        self.plan = self.topology.evidence_plan(
            design_revision="NPR-011-packet-path-v0.1",
            semantic_baseline_commit=semantic_baseline_commit,
            semantic_baseline_path=_AEP_PATH,
            path_id="network-control-selected-path",
            exchange_program=ExchangeProgram(
                program_id="ptl002-packet-path-exact-byte-v0.1",
                request_prefix=b"AVP-PTL002-REQ\x00",
                request_suffix=b"\x00END",
                response_prefix=b"AVP-PTL002-RESP\x00",
                response_suffix=b"\x00END",
            ),
            observation_budget_ns=observation_budget_ns,
            negative_mode=None if negative is None else negative.mode.value,
        )
        self.execution = PacketPathExecutionPlan.build(
            topology=self.topology,
            evidence_plan=self.plan,
            negative=negative,
        )
        self._negative = negative

    def execute_evidence(self) -> PacketPathLiveExecutionResult:
        """Execute one finite case, retain facts, and delegate assessment unchanged."""

        if not sys.platform.startswith("linux"):
            raise PacketPathLocalQualificationError(
                "PTL-002 packet-path evidence requires native Linux"
            )
        if os.geteuid() != 0:
            raise PacketPathLocalQualificationError(
                "PTL-002 packet-path evidence requires existing euid 0"
            )

        sealed = self.plan.seal()
        sealed_plan_ref = self.artifact_store.put_bytes(
            sealed.exact_bytes,
            logical_role=sealed.ref.logical_role,
        )
        if sealed_plan_ref != sealed.ref:
            raise EvidenceMaterializationError(
                "packet-path sealed plan store identity drift"
            )

        attempts: list[PacketPathLiveAttempt] = []
        infrastructure_problems: list[str] = []
        cleanup_noninterference_ok: bool | None = None
        setup_complete = False
        final_cleanup_performed = False
        security_projection_ok: bool | None = None
        ruleset_refs: list[ArtifactRef] = []
        primary: BaseException | None = None
        result: PacketPathLiveExecutionResult | None = None

        try:
            for step in self.execution.steps:
                if step.step_id is PacketPathStepId.SETUP:
                    self.controller.setup()
                    setup_complete = True
                    ruleset_refs.append(self._retain_ruleset("before-fault"))
                    security_projection_ok = self._observe_security_projection()
                    continue
                if step.step_id is PacketPathStepId.START_FIXTURES:
                    self._start_fixtures()
                    continue
                if step.step_id is PacketPathStepId.TRIGGER:
                    # The finite execution-plan position is the Environment-owned
                    # occurrence boundary for this project evidence assembly.
                    continue
                if step.step_id is PacketPathStepId.INSTALL_FAULT:
                    if step.fault_mode is None:
                        raise AssertionError("fault installation step lacks mechanism mode")
                    self.controller.install_fault(step.fault_mode)
                    ruleset_refs.append(self._retain_ruleset("active-fault"))
                    continue
                if step.step_id is PacketPathStepId.CLEAR_FAULT:
                    self.controller.clear_fault()
                    ruleset_refs.append(self._retain_ruleset("after-clear"))
                    continue
                if step.step_id is PacketPathStepId.STOP_FIXTURES:
                    fixture_problems = self._stop_fixtures()
                    infrastructure_problems.extend(
                        f"fixture-stop:{problem}" for problem in fixture_problems
                    )
                    continue
                if step.step_id is PacketPathStepId.CLEANUP:
                    cleanup_problems = self.controller.cleanup()
                    final_cleanup_performed = True
                    if cleanup_problems:
                        infrastructure_problems.extend(
                            f"cleanup:{problem}" for problem in cleanup_problems
                        )
                    residual = self.controller.residual_resources()
                    if residual:
                        infrastructure_problems.extend(
                            f"cleanup-residual:{problem}" for problem in residual
                        )
                    continue
                if step.step_id is PacketPathStepId.CLEANUP_SENTINEL:
                    residual = self.controller.residual_resources()
                    cleanup_noninterference_ok = not residual
                    continue
                if step.is_attempt:
                    attempts.append(self._execute_attempt(step))
                    continue
                raise AssertionError(f"unhandled packet-path execution step: {step.step_id.value}")

            if cleanup_noninterference_ok is None:
                raise AssertionError("packet-path execution omitted cleanup sentinel")

            # ScheduleLeak must be a real Subject-visible projection mutation. The
            # execution plan places it on pre-trigger; independently execute the
            # read-only Subject security probe with that exact environment so C12
            # is based on observed visibility rather than mode-name branching.
            if self._negative is not None and self._negative.subject_environment_overrides():
                security_projection_ok = self._observe_security_projection(
                    self._negative.subject_environment_overrides()
                )
            if security_projection_ok is None:
                raise AssertionError("packet-path execution omitted Subject security observation")

            run_evidence = PacketPathRunEvidence(
                sealed_plan=sealed,
                attempts=tuple(item.portable() for item in attempts),
                cleanup_noninterference_ok=cleanup_noninterference_ok,
                security_projection_ok=security_projection_ok,
                infrastructure_problems=tuple(infrastructure_problems),
            )
            assessment = run_evidence.assess()
            materialization_ref = self._retain_materialization_provenance(
                sealed_plan_ref=sealed_plan_ref,
                ruleset_refs=tuple(ruleset_refs),
            )
            implementation_ref = self._retain_implementation_record(
                assessment=assessment,
                attempts=tuple(attempts),
                cleanup_noninterference_ok=cleanup_noninterference_ok,
                security_projection_ok=security_projection_ok,
                infrastructure_problems=tuple(infrastructure_problems),
                materialization_ref=materialization_ref,
                sealed_plan_ref=sealed_plan_ref,
            )
            result = PacketPathLiveExecutionResult(
                assessment=assessment,
                materialization_provenance_ref=materialization_ref,
                implementation_record_ref=implementation_ref,
                sealed_plan_ref=sealed_plan_ref,
            )
        except BaseException as exc:
            primary = exc
        finally:
            fixture_problems = self._stop_fixtures()
            if primary is not None:
                for problem in fixture_problems:
                    primary.add_note(f"packet-path fixture cleanup: {problem}")
            if setup_complete and not final_cleanup_performed:
                cleanup_problems = self.controller.cleanup()
                if primary is not None:
                    for problem in cleanup_problems:
                        primary.add_note(f"packet-path final cleanup: {problem}")
                try:
                    residual = self.controller.residual_resources()
                except BaseException as exc:
                    if primary is not None:
                        primary.add_note(
                            f"packet-path final residual check: {type(exc).__name__}"
                        )
                else:
                    if primary is not None:
                        for problem in residual:
                            primary.add_note(f"packet-path final residual: {problem}")

        if primary is not None:
            raise primary
        if result is None:
            raise AssertionError("packet-path live evidence completed without result")
        return result

    def _execute_attempt(self, step: PacketPathExecutionStep) -> PacketPathLiveAttempt:
        phase_id = step.attempt_phase
        if phase_id is None or step.target is None:
            raise AssertionError("packet-path attempt step is incomplete")
        self._ordinal += 1
        attempt = self.attempt_factory.issue(
            self.plan,
            phase_id=phase_id,
            ordinal=self._ordinal,
        )
        fixture = self._control_fixture if phase_id == "non-target-control" else self._selected_fixture
        if fixture is None:
            raise PacketPathLocalQualificationError("packet-path fixture is unavailable")
        fixture.request({"op": "arm", "attempt": _attempt_document(attempt)})

        witness_command, witness_input = self._attempt_witness_command(
            phase_id=phase_id,
            attempt_id=attempt.attempt_id,
            target=step.target,
            assurance=self.capture_assurance,
            privileged=step.actor is PacketPathActor.PRIVILEGED_PROBE,
        )
        witness = self._start_role(
            witness_command,
            label=f"evidence-witness:{phase_id}",
        )
        primary: BaseException | None = None
        exchange_document: dict[str, object] | None = None
        witness_document: dict[str, object] | None = None
        try:
            witness.send(witness_input)
            ready = witness.receive()
            if ready.get("event") != "ready" or ready.get("attemptId") != attempt.attempt_id:
                raise PacketPathLocalQualificationError(
                    f"packet-path evidence witness was not ready for {phase_id}"
                )
            exchange_document = self._run_evidence_exchange(
                step=step,
                attempt=attempt,
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
                witness_document = witness.receive()
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
        if exchange_document is None or witness_document is None:
            raise AssertionError("packet-path evidence attempt lacks exchange/witness output")

        # Strict parser both validates the witness document and deliberately
        # preserves semantic cardinality violations such as HiddenRetry/Fallback.
        parse_front_initiations(witness_document)
        exchange = _exchange_from_document(exchange_document)
        attempt_ref = self._put_json(
            _attempt_document(attempt),
            logical_role=f"packet-path-attempt-{phase_id}",
        )
        exchange_ref = self._put_json(
            exchange_document,
            logical_role=f"packet-path-exchange-{phase_id}",
        )
        witness_ref = self._put_json(
            witness_document,
            logical_role=f"packet-path-witness-{phase_id}",
        )
        raw = witness_document.get("rawArtifactB64")
        if not isinstance(raw, str) or not raw:
            raise EvidenceMaterializationError(
                "packet-path witness raw artifact is missing"
            )
        try:
            raw_bytes = base64.b64decode(raw, validate=True)
        except ValueError as exc:
            raise EvidenceMaterializationError(
                "packet-path witness raw artifact is invalid base64"
            ) from exc
        raw_ref = self.artifact_store.put_bytes(
            raw_bytes,
            logical_role=f"packet-path-witness-raw-{phase_id}",
        )
        return PacketPathLiveAttempt(
            attempt=attempt,
            exchange=exchange,
            witness_document=witness_document,
            attempt_ref=attempt_ref,
            exchange_ref=exchange_ref,
            witness_ref=witness_ref,
            raw_witness_ref=raw_ref,
        )

    def _run_evidence_exchange(
        self,
        *,
        step: PacketPathExecutionStep,
        attempt: AttemptMaterial,
    ) -> dict[str, object]:
        command = (sys.executable, "-m", _WORKER_MODULE, "exchange")
        if step.actor is PacketPathActor.SUBJECT:
            argv = self.controller.subject_command(command)
        elif step.actor is PacketPathActor.PRIVILEGED_PROBE:
            argv = (
                "ip",
                "netns",
                "exec",
                self.topology.subject_namespace,
                *command,
            )
        else:
            raise PacketPathLocalQualificationError(
                f"unsupported packet-path attempt actor {step.actor.value!r}"
            )
        payload: dict[str, object] = {
            "endpoint": _endpoint_document(step.target),
            "attempt": _attempt_document(attempt),
            "observationBudgetNs": self.observation_budget_ns,
        }
        if len(step.connection_targets) == 2:
            payload["additionalConnectTarget"] = _endpoint_document(
                step.connection_targets[1]
            )
        return self._run_worker_once_with_environment(
            argv,
            input_document=payload,
            environment_overrides=step.subject_environment,
        )

    def _observe_security_projection(
        self,
        environment_overrides: Sequence[tuple[str, str]] = (),
    ) -> bool:
        command = self.controller.subject_command(
            (sys.executable, "-m", _WORKER_MODULE, "security-probe")
        )
        document = self._run_worker_once_with_environment(
            command,
            input_document={"environmentKeys": list(_SENSITIVE_SUBJECT_ENVIRONMENT)},
            environment_overrides=environment_overrides,
        )
        presence = document.get("environmentPresence")
        if not isinstance(presence, dict) or set(presence) != set(
            _SENSITIVE_SUBJECT_ENVIRONMENT
        ):
            raise EvidenceMaterializationError(
                "packet-path Subject security projection is incomplete"
            )
        values: list[bool] = []
        for key in _SENSITIVE_SUBJECT_ENVIRONMENT:
            value = presence.get(key)
            if not isinstance(value, bool):
                raise EvidenceMaterializationError(
                    f"packet-path Subject environment presence {key!r} must be boolean"
                )
            values.append(value)
        self._put_json(
            document,
            logical_role="packet-path-subject-security-projection",
        )
        return not any(values)

    def _run_worker_once_with_environment(
        self,
        command: Sequence[str],
        *,
        input_document: Mapping[str, object],
        environment_overrides: Sequence[tuple[str, str]] = (),
    ) -> dict[str, object]:
        environment = self._worker_environment()
        for key, value in environment_overrides:
            if not isinstance(key, str) or not key or not isinstance(value, str):
                raise EvidenceMaterializationError(
                    "packet-path Subject environment override must be string pair"
                )
            environment[key] = value
        payload = json.dumps(
            input_document,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
        completed = subprocess.run(
            list(command),
            input=payload,
            check=False,
            capture_output=True,
            text=True,
            timeout=max(
                self.role_timeout_s,
                self.observation_budget_ns / 1_000_000_000 + 1.0,
            ),
            env=environment,
        )
        if completed.returncode != 0:
            raise PacketPathLocalQualificationError(
                f"packet-path evidence worker failed ({completed.returncode}): "
                f"{completed.stderr.strip()}"
            )
        line = completed.stdout.strip()
        if not line:
            raise PacketPathLocalQualificationError(
                "packet-path evidence worker emitted no JSON document"
            )
        try:
            value = json.loads(line.splitlines()[-1])
        except json.JSONDecodeError as exc:
            raise PacketPathLocalQualificationError(
                "packet-path evidence worker emitted invalid JSON"
            ) from exc
        if not isinstance(value, dict):
            raise PacketPathLocalQualificationError(
                "packet-path evidence worker output is not object"
            )
        return value

    def _retain_ruleset(self, label: str) -> ArtifactRef:
        snapshot = self.controller.ruleset_snapshot()
        document = {
            "label": label,
            "argv": list(snapshot.argv),
            "returnCode": snapshot.returncode,
            "stdout": snapshot.stdout,
            "stderr": snapshot.stderr,
        }
        return self._put_json(
            document,
            logical_role=f"packet-path-ruleset-{label}",
        )

    def _retain_materialization_provenance(
        self,
        *,
        sealed_plan_ref: ArtifactRef,
        ruleset_refs: tuple[ArtifactRef, ...],
    ) -> ArtifactRef:
        versions = {
            "uname": self.cli.run(("uname", "-srm")).stdout.strip(),
            "ip": self.cli.run(("ip", "-Version")).stdout.strip(),
            "nft": self.cli.run(("nft", "--version")).stdout.strip(),
            "setpriv": self.cli.run(("setpriv", "--version")).stdout.strip(),
        }
        document = {
            "format": _MATERIALIZATION_FORMAT,
            "runId": self.run_id,
            "semanticBaselineCommit": self.semantic_baseline_commit,
            "sealedPlan": _ref_document(sealed_plan_ref),
            "captureAssurance": {
                "egressCoverageVerified": self.capture_assurance.egress_coverage_verified,
                "directionalityVerified": self.capture_assurance.directionality_verified,
                "offloadNormalizationVerified": self.capture_assurance.offload_normalization_verified,
                "preSynConnectGapClosed": self.capture_assurance.pre_syn_connect_gap_closed,
            },
            "topology": self.topology.provenance_document(),
            "versions": versions,
            "rulesetSnapshots": [_ref_document(item) for item in ruleset_refs],
        }
        return self._put_json(
            document,
            logical_role="packet-path-live-materialization-provenance",
        )

    def _retain_implementation_record(
        self,
        *,
        assessment: EvidenceAssessment,
        attempts: tuple[PacketPathLiveAttempt, ...],
        cleanup_noninterference_ok: bool,
        security_projection_ok: bool,
        infrastructure_problems: tuple[str, ...],
        materialization_ref: ArtifactRef,
        sealed_plan_ref: ArtifactRef,
    ) -> ArtifactRef:
        document = {
            "format": _IMPLEMENTATION_FORMAT,
            "runId": self.run_id,
            "negativeMode": None if self.negative_mode is None else self.negative_mode.value,
            "assessment": {
                "classification": assessment.classification.value,
                "primaryProblem": assessment.primary_problem,
                "secondaryProblems": list(assessment.secondary_problems),
            },
            "cleanupNoninterferenceOk": cleanup_noninterference_ok,
            "securityProjectionOk": security_projection_ok,
            "infrastructureProblems": list(infrastructure_problems),
            "sealedPlan": _ref_document(sealed_plan_ref),
            "materializationProvenance": _ref_document(materialization_ref),
            "attempts": [
                {
                    "phaseId": item.attempt.phase_id,
                    "attemptId": item.attempt.attempt_id,
                    "attempt": _ref_document(item.attempt_ref),
                    "exchange": _ref_document(item.exchange_ref),
                    "witness": _ref_document(item.witness_ref),
                    "rawWitness": _ref_document(item.raw_witness_ref),
                }
                for item in attempts
            ],
        }
        return self._put_json(
            document,
            logical_role="packet-path-live-implementation-record",
        )

    def _put_json(
        self,
        document: Mapping[str, object],
        *,
        logical_role: str,
    ) -> ArtifactRef:
        payload = json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return self.artifact_store.put_bytes(payload, logical_role=logical_role)


def _exchange_from_document(document: Mapping[str, object]) -> ExchangeObservation:
    return ExchangeObservation(
        attempt_id=_required_string(document, "attemptId"),
        completed=_required_bool(document, "completed"),
        mismatch_observed=_required_bool(document, "mismatchObserved"),
        observation_budget_expired=_required_bool(document, "observationBudgetExpired"),
        elapsed_ns=_required_non_negative_int(document, "elapsedNs"),
        response_size=_required_non_negative_int(document, "responseSize"),
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


def _required_bool(document: Mapping[str, object], key: str) -> bool:
    value = document.get(key)
    if not isinstance(value, bool):
        raise EvidenceMaterializationError(
            f"packet-path exchange field {key!r} must be boolean"
        )
    return value


def _required_non_negative_int(document: Mapping[str, object], key: str) -> int:
    value = document.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EvidenceMaterializationError(
            f"packet-path exchange field {key!r} must be non-negative integer"
        )
    return value


def _required_string(document: Mapping[str, object], key: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value:
        raise EvidenceMaterializationError(
            f"packet-path exchange field {key!r} must be non-empty string"
        )
    return value


def _ref_document(ref: ArtifactRef) -> dict[str, object]:
    return {
        "sha256": ref.sha256,
        "size": ref.size,
        "logicalRole": ref.logical_role,
    }

"""Reference implementation probes for the AVP Oracle conformance profile."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from avp_ref.artifacts import sha256_digest
from avp_ref.canonical import digest
from avp_ref.models import TaskVerdict, Validity, VerificationResult
from avp_ref.oracle_runner import (
    OracleEvaluationContext,
    OracleExecutionArtifact,
    OracleExecutionResult,
    OracleExecutionStatus,
    OraclePackage,
    OracleRequest,
    OracleRunnerDescription,
    ProjectionSnapshot,
    SubprocessOracleRunner,
)
from avp_ref.reference import (
    correct_subject,
    reference_agent_system,
    reference_environment,
    reference_oracle_package,
    reference_scenario,
    reference_subject_adapter,
)
from avp_ref.runtime import EpisodeState, ReferenceRuntime

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


@dataclass(frozen=True, slots=True)
class _UntrustedEvidencePayload:
    """Test-only worker output that can represent protocol-invalid Evidence.

    The public OracleEvidencePayload constructor correctly rejects digest drift,
    so the TCK needs an explicitly untrusted boundary fixture to verify that the
    trusted parent runtime also fails closed when a hostile runner bypasses that
    convenience model.
    """

    evidence_id: str
    evidence_type: str
    content: bytes
    media_type: str
    digest: str
    classification: str = "evaluator-confidential"
    producer: str | None = "oracle-tck"


class _ScriptedOracleRunner:
    """Deterministic external-runner double; ReferenceRuntime remains under test."""

    def __init__(
        self,
        response: Callable[[OracleRequest, OracleRunnerDescription], OracleExecutionResult],
    ) -> None:
        self._description = SubprocessOracleRunner().describe()
        self._response = response
        self.requests: list[OracleRequest] = []

    def describe(self) -> OracleRunnerDescription:
        return self._description

    def evaluate(self, request: OracleRequest) -> OracleExecutionResult:
        self.requests.append(request)
        return self._response(request, self._description)


def _execution(
    request: OracleRequest,
    description: OracleRunnerDescription,
    *,
    status: OracleExecutionStatus,
    results: tuple[VerificationResult, ...] = (),
    evidence: tuple[object, ...] = (),
) -> OracleExecutionResult:
    empty_digest = sha256_digest(b"")
    artifact = OracleExecutionArtifact(
        request_id=request.request_id,
        oracle_package_digest=request.package.identity_digest,
        oracle_code_digest=request.package.code_digest,
        runner_config_digest=description.identity_digest,
        input_digest=request.context.input_digest,
        status=status,
        duration_ms=1,
        exit_code=0 if status is OracleExecutionStatus.SUCCESS else 1,
        stdout_digest=empty_digest,
        stderr_digest=empty_digest,
        output_digest=empty_digest if status is OracleExecutionStatus.SUCCESS else None,
    )
    return OracleExecutionResult(
        request_id=request.request_id,
        status=status,
        results=results,
        evidence=evidence,  # type: ignore[arg-type] -- deliberately hostile TCK fixture.
        artifact=artifact,
    )


def _success(
    request: OracleRequest,
    description: OracleRunnerDescription,
) -> OracleExecutionResult:
    return _execution(
        request,
        description,
        status=OracleExecutionStatus.SUCCESS,
    )


def _run_episode(
    runner: _ScriptedOracleRunner,
    *,
    package: OraclePackage | None = None,
):
    runtime = ReferenceRuntime(oracle_runner=runner)
    episode = runtime.create_episode(
        scenario=reference_scenario(),
        agent_system=reference_agent_system("oracle-tck-subject"),
        environment_adapter=reference_environment(),
        subject_adapter=reference_subject_adapter(correct_subject),
        oracle_package=package or reference_oracle_package(),
    )
    runtime.provision(episode.episode_id)
    runtime.run_subject(episode.episode_id)
    runtime.verify(episode.episode_id)
    return runtime, episode


class ReferenceOracleTCKAdapter:
    """Execute portable Oracle vectors against real reference-runtime boundaries."""

    _SUPPORTED_CASES = frozenset(
        {
            "AVP-TCK-ORACLE-IDENTITY-001",
            "AVP-TCK-ORACLE-INPUT-SCOPE-001",
            "AVP-TCK-ORACLE-FAILURE-SEPARATION-001",
            "AVP-TCK-ORACLE-EVIDENCE-INTEGRITY-001",
        }
    )

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return self._SUPPORTED_CASES

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        evaluator = {
            "AVP-TCK-ORACLE-IDENTITY-001": self._evaluate_identity,
            "AVP-TCK-ORACLE-INPUT-SCOPE-001": self._evaluate_input_scope,
            "AVP-TCK-ORACLE-FAILURE-SEPARATION-001": self._evaluate_failure_separation,
            "AVP-TCK-ORACLE-EVIDENCE-INTEGRITY-001": self._evaluate_evidence_integrity,
        }.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(
                f"reference Oracle adapter does not implement TCK case {case_id}"
            )
        return evaluator(case)

    def _evaluate_identity(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        package_digest = self._string(
            vector.get("packageDigest"), f"{case_id} packageDigest"
        )
        package = OraclePackage(
            oracle_id=self._string(vector.get("oracleId"), f"{case_id} oracleId"),
            version=self._string(vector.get("version"), f"{case_id} version"),
            entrypoint="tck://oracle-identity",
            code_digest=package_digest,
            projections=("tck.identity",),
        )
        projection = ProjectionSnapshot("tck.identity", [], digest([]))
        context = OracleEvaluationContext(
            episode_id="ep_oracle_identity_tck",
            scenario_instance_digest=self._string(
                vector.get("scenarioInstanceDigest"),
                f"{case_id} scenarioInstanceDigest",
            ),
            manifest_digest=self._string(
                vector.get("manifestDigest"), f"{case_id} manifestDigest"
            ),
            inputs={},
            projections={"tck.identity": projection},
        )
        request = OracleRequest("oracle_req_identity_tck", package, context)
        description = SubprocessOracleRunner().describe()
        execution = _execution(
            request,
            description,
            status=OracleExecutionStatus.SUCCESS,
        )

        identity_bound = (
            package.oracle_id == vector["oracleId"]
            and package.version == vector["version"]
            and execution.artifact.oracle_code_digest == package_digest
            and execution.artifact.oracle_package_digest == package.identity_digest
        )
        input_bound = (
            execution.artifact.input_digest == context.input_digest
            and context.input_digest == digest(context.to_dict())
        )
        auditable = (
            execution.artifact.record_digest
            == digest(execution.artifact.to_dict())
            and execution.artifact.runner_config_digest == description.identity_digest
        )
        if not (identity_bound and input_bound and auditable):
            return self._fail(case_id, "Oracle identity/input/execution binding drifted")
        return self._pass(
            case_id,
            "Oracle identity, evaluated context and execution record are digest-bound",
        )

    def _evaluate_input_scope(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        declared_inputs = self._string_list(
            vector.get("declaredInputs"), f"{case_id} declaredInputs"
        )
        declared_projections = self._string_list(
            vector.get("declaredProjections"), f"{case_id} declaredProjections"
        )
        forbidden = set(
            self._string_list(
                vector.get("forbiddenContextKeys"),
                f"{case_id} forbiddenContextKeys",
            )
        )
        if declared_inputs != ["target_order_id"]:
            raise TCKAdapterError(
                f"{case_id} reference vector currently requires target_order_id"
            )

        package = OraclePackage(
            oracle_id="tck.input-scope",
            version="0.1.0",
            entrypoint="tck://input-scope",
            code_digest=sha256_digest(b"avp-oracle-input-scope-tck"),
            projections=tuple(declared_projections),
            input_pointers={
                "target_order_id": "/extensions/avp_ref/target_order_id"
            },
        )
        runner = _ScriptedOracleRunner(_success)
        _run_episode(runner, package=package)
        if len(runner.requests) != 1:
            return self._fail(case_id, "runtime did not produce exactly one Oracle request")
        context = runner.requests[0].context
        serialized = context.to_dict()
        if set(context.inputs) != set(declared_inputs):
            return self._fail(case_id, "Oracle received undeclared or missing scalar inputs")
        if set(context.projections) != set(declared_projections):
            return self._fail(case_id, "Oracle received undeclared or missing projections")
        if forbidden.intersection(serialized):
            return self._fail(case_id, "Oracle context exposes a forbidden runtime handle")
        if context.input_digest != digest(serialized):
            return self._fail(case_id, "Oracle context digest is not deterministic")
        return self._pass(
            case_id,
            "runtime constructs a declared, handle-free and digest-bound Oracle context",
        )

    def _evaluate_failure_separation(
        self,
        case: Mapping[str, Any],
    ) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        failures = vector.get("failures")
        if not isinstance(failures, list) or not failures:
            raise TCKAdapterError(f"{case_id} failures must be a non-empty array")
        for raw in failures:
            if not isinstance(raw, Mapping):
                raise TCKAdapterError(f"{case_id} failure entry must be an object")
            try:
                status = OracleExecutionStatus(
                    self._string(raw.get("executionStatus"), f"{case_id} executionStatus")
                )
            except ValueError as exc:
                raise TCKAdapterError(f"{case_id} has an unknown Oracle status") from exc
            if status is OracleExecutionStatus.SUCCESS:
                raise TCKAdapterError(f"{case_id} failure vector cannot contain SUCCESS")
            expected_detail = self._string(
                raw.get("expectedDetailCode"), f"{case_id} expectedDetailCode"
            )

            def respond(
                request: OracleRequest,
                description: OracleRunnerDescription,
                *,
                scripted_status: OracleExecutionStatus = status,
            ) -> OracleExecutionResult:
                return _execution(
                    request,
                    description,
                    status=scripted_status,
                )

            runner = _ScriptedOracleRunner(respond)
            _, episode = _run_episode(runner)
            observed_detail = (
                episode.validity_detail.code
                if episode.validity_detail is not None
                else None
            )
            if not (
                episode.validity is Validity.ORACLE_FAILURE
                and episode.task_verdict is TaskVerdict.INCONCLUSIVE
                and episode.state is EpisodeState.INVALID
                and observed_detail == expected_detail
            ):
                return self._fail(
                    case_id,
                    f"{status.value} escaped the stable Oracle failure semantics",
                )
        return self._pass(
            case_id,
            "all Oracle runner failures remain evaluation-invalid and task-inconclusive",
        )

    def _evaluate_evidence_integrity(
        self,
        case: Mapping[str, Any],
    ) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        missing_id = self._string(
            vector.get("missingEvidenceId"), f"{case_id} missingEvidenceId"
        )

        def missing_response(
            request: OracleRequest,
            description: OracleRunnerDescription,
        ) -> OracleExecutionResult:
            result = VerificationResult(
                "tck.oracle.missing-evidence",
                "evidence.integrity",
                "PASS",
                "critical",
                "oracle_tck",
                "0.1.0",
                (missing_id,),
            )
            return _execution(
                request,
                description,
                status=OracleExecutionStatus.SUCCESS,
                results=(result,),
            )

        _, missing_episode = _run_episode(_ScriptedOracleRunner(missing_response))
        missing_rejected = self._is_oracle_protocol_invalid(missing_episode)

        declared_digest = self._string(
            vector.get("declaredDigest"), f"{case_id} declaredDigest"
        )
        tampered_bytes = self._hex_bytes(
            vector.get("tamperedBytesHex"), f"{case_id} tamperedBytesHex"
        )
        tampered_id = "ev_oracle_tck_tampered"

        def tampered_response(
            request: OracleRequest,
            description: OracleRunnerDescription,
        ) -> OracleExecutionResult:
            payload = _UntrustedEvidencePayload(
                evidence_id=tampered_id,
                evidence_type="state_projection",
                content=tampered_bytes,
                media_type="application/octet-stream",
                digest=declared_digest,
            )
            result = VerificationResult(
                "tck.oracle.tampered-evidence",
                "evidence.integrity",
                "PASS",
                "critical",
                "oracle_tck",
                "0.1.0",
                (tampered_id,),
            )
            return _execution(
                request,
                description,
                status=OracleExecutionStatus.SUCCESS,
                results=(result,),
                evidence=(payload,),
            )

        _, tampered_episode = _run_episode(_ScriptedOracleRunner(tampered_response))
        tampered_rejected = self._is_oracle_protocol_invalid(tampered_episode)
        task_failure_not_inferred = (
            missing_episode.task_verdict is TaskVerdict.INCONCLUSIVE
            and tampered_episode.task_verdict is TaskVerdict.INCONCLUSIVE
        )
        if not (missing_rejected and tampered_rejected and task_failure_not_inferred):
            return self._fail(
                case_id,
                "missing or digest-invalid Oracle Evidence was not rejected safely",
            )
        return self._pass(
            case_id,
            "missing and digest-invalid Oracle Evidence invalidate evaluation without task failure",
        )

    @staticmethod
    def _is_oracle_protocol_invalid(episode: object) -> bool:
        return (
            getattr(episode, "validity", None) is Validity.ORACLE_FAILURE
            and getattr(episode, "state", None) is EpisodeState.INVALID
            and getattr(episode, "task_verdict", None) is TaskVerdict.INCONCLUSIVE
            and getattr(getattr(episode, "validity_detail", None), "code", None)
            == "ORACLE_PROTOCOL_ERROR"
        )

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("Oracle TCK case metadata.id is missing")
        return case_id

    @staticmethod
    def _vector(case: Mapping[str, Any], case_id: str) -> Mapping[str, Any]:
        vector = case.get("vector")
        if not isinstance(vector, Mapping):
            raise TCKAdapterError(f"{case_id} vector must be an object")
        return vector

    @staticmethod
    def _string(value: object, label: str) -> str:
        if not isinstance(value, str) or not value:
            raise TCKAdapterError(f"{label} must be a non-empty string")
        return value

    @classmethod
    def _string_list(cls, value: object, label: str) -> list[str]:
        if not isinstance(value, list):
            raise TCKAdapterError(f"{label} must be an array")
        result = [cls._string(item, label) for item in value]
        if len(result) != len(set(result)):
            raise TCKAdapterError(f"{label} must not contain duplicates")
        return result

    @staticmethod
    def _hex_bytes(value: object, label: str) -> bytes:
        if not isinstance(value, str):
            raise TCKAdapterError(f"{label} must be a hexadecimal string")
        try:
            return bytes.fromhex(value)
        except ValueError as exc:
            raise TCKAdapterError(f"{label} is not valid hexadecimal") from exc

    @staticmethod
    def _pass(case_id: str, detail: str) -> TCKCaseResult:
        return TCKCaseResult(case_id, TCKStatus.PASS, detail)

    @staticmethod
    def _fail(case_id: str, detail: str) -> TCKCaseResult:
        return TCKCaseResult(case_id, TCKStatus.FAIL, detail)

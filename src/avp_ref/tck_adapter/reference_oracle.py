"""Reference probes for the language-neutral AVP Oracle conformance profile."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import FrozenInstanceError, dataclass
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
    OracleProtocolError,
    OracleRequest,
    OracleRunnerDescription,
    ProjectionSnapshot,
    SubprocessOracleRunner,
    oracle_output_digest,
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

_Response = Callable[[OracleRequest, OracleRunnerDescription], OracleExecutionResult]


@dataclass(frozen=True, slots=True)
class _UntrustedEvidencePayload:
    """Protocol-invalid worker payload used only to test the trusted boundary."""

    evidence_id: str
    evidence_type: str
    content: bytes
    media_type: str
    digest: str
    classification: str = "evaluator-confidential"
    producer: str | None = "oracle-tck"


class _ScriptedOracleRunner:
    """Deterministic runner double while keeping ReferenceRuntime under test."""

    def __init__(self, response: _Response) -> None:
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
    status: OracleExecutionStatus,
    *,
    results: tuple[VerificationResult, ...] = (),
    evidence: tuple[object, ...] = (),
) -> OracleExecutionResult:
    empty_digest = sha256_digest(b"")
    output_digest = (
        oracle_output_digest(results, evidence)
        if status is OracleExecutionStatus.SUCCESS
        else None
    )
    return OracleExecutionResult(
        request_id=request.request_id,
        status=status,
        results=results,
        evidence=evidence,  # type: ignore[arg-type] -- deliberately hostile fixture.
        artifact=OracleExecutionArtifact(
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
            output_digest=output_digest,
        ),
    )


def _success(request: OracleRequest, description: OracleRunnerDescription) -> OracleExecutionResult:
    return _execution(request, description, OracleExecutionStatus.SUCCESS)


def _run_episode(runner: _ScriptedOracleRunner, package: OraclePackage | None = None):
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
    return runtime.verify(episode.episode_id)


class ReferenceOracleTCKAdapter:
    """Execute Oracle TCK vectors against real reference implementation seams."""

    _SUPPORTED_CASES = frozenset(
        {
            "AVP-TCK-ORACLE-IDENTITY-001",
            "AVP-TCK-ORACLE-INPUT-SCOPE-001",
            "AVP-TCK-ORACLE-FAILURE-SEPARATION-001",
            "AVP-TCK-ORACLE-EVIDENCE-INTEGRITY-001",
            "AVP-TCK-ORACLE-EXECUTION-AUDIT-001",
        }
    )

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return self._SUPPORTED_CASES

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        evaluator = {
            "AVP-TCK-ORACLE-IDENTITY-001": self._identity,
            "AVP-TCK-ORACLE-INPUT-SCOPE-001": self._input_scope,
            "AVP-TCK-ORACLE-FAILURE-SEPARATION-001": self._failure_separation,
            "AVP-TCK-ORACLE-EVIDENCE-INTEGRITY-001": self._evidence_integrity,
            "AVP-TCK-ORACLE-EXECUTION-AUDIT-001": self._execution_audit,
        }.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(f"unsupported reference Oracle TCK case: {case_id}")
        return evaluator(case)

    def _identity(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        projections = self._strings(vector.get("projections"), f"{case_id} projections")
        raw_pointers = vector.get("inputPointers")
        if not isinstance(raw_pointers, Mapping):
            raise TCKAdapterError(f"{case_id} inputPointers must be an object")
        expected_package_digest = self._string(
            vector.get("packageDigest"), f"{case_id} packageDigest"
        )
        package_bytes = self._hex(
            vector.get("packageBytesHex"), f"{case_id} packageBytesHex"
        )
        package = OraclePackage(
            oracle_id=self._string(vector.get("oracleId"), f"{case_id} oracleId"),
            version=self._string(vector.get("version"), f"{case_id} version"),
            entrypoint=self._string(vector.get("entrypoint"), f"{case_id} entrypoint"),
            code_digest=self._string(vector.get("codeDigest"), f"{case_id} codeDigest"),
            projections=tuple(projections),
            input_pointers={
                self._string(k, f"{case_id} input name"): self._string(v, f"{case_id} input pointer")
                for k, v in raw_pointers.items()
            },
            package_digest=expected_package_digest,
        )
        projection = ProjectionSnapshot(projections[0], [], digest([]))
        context = OracleEvaluationContext(
            episode_id="ep_oracle_identity_tck",
            scenario_instance_digest=self._string(
                vector.get("scenarioInstanceDigest"), f"{case_id} scenarioInstanceDigest"
            ),
            manifest_digest=self._string(vector.get("manifestDigest"), f"{case_id} manifestDigest"),
            inputs={},
            projections={projections[0]: projection},
        )
        request = OracleRequest("oracle_req_identity_tck", package, context)
        description = SubprocessOracleRunner().describe()
        execution = _execution(request, description, OracleExecutionStatus.SUCCESS)
        valid = (
            sha256_digest(package_bytes) == expected_package_digest
            and package.identity_digest == expected_package_digest
            and execution.artifact.oracle_package_digest == expected_package_digest
            and execution.artifact.oracle_code_digest == package.code_digest
            and execution.artifact.input_digest == context.input_digest
            and context.input_digest == digest(context.to_dict())
            and execution.artifact.record_digest == digest(execution.artifact.to_dict())
        )
        return self._result(
            case_id,
            valid,
            "opaque package identity, input identity and execution identity are independently bound",
            "Oracle package/input/execution identity binding drifted",
        )

    def _input_scope(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        inputs = self._strings(vector.get("declaredInputs"), f"{case_id} declaredInputs")
        projections = self._strings(
            vector.get("declaredProjections"), f"{case_id} declaredProjections"
        )
        forbidden = set(
            self._strings(vector.get("forbiddenContextKeys"), f"{case_id} forbiddenContextKeys")
        )
        if inputs != ["target_order_id"]:
            raise TCKAdapterError(f"{case_id} reference vector requires target_order_id")
        package = OraclePackage(
            "tck.input-scope",
            "0.1.0",
            "tck.oracle:input_scope",
            sha256_digest(b"avp-oracle-input-scope-tck"),
            tuple(projections),
            {"target_order_id": "/extensions/avp_ref/target_order_id"},
        )
        runner = _ScriptedOracleRunner(_success)
        _run_episode(runner, package)
        if len(runner.requests) != 1:
            return self._fail(case_id, "runtime did not issue exactly one Oracle request")
        context = runner.requests[0].context
        document = context.to_dict()
        valid = (
            set(context.inputs) == set(inputs)
            and set(context.projections) == set(projections)
            and not forbidden.intersection(document)
            and context.input_digest == digest(document)
        )
        return self._result(
            case_id,
            valid,
            "runtime emits only declared, handle-free and digest-bound Oracle inputs",
            "runtime leaked or substituted Oracle evaluation input",
        )

    def _failure_separation(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        failures = self._vector(case, case_id).get("failures")
        if not isinstance(failures, list) or not failures:
            raise TCKAdapterError(f"{case_id} failures must be a non-empty array")
        for item in failures:
            if not isinstance(item, Mapping):
                raise TCKAdapterError(f"{case_id} failure entry must be an object")
            try:
                status = OracleExecutionStatus(
                    self._string(item.get("executionStatus"), f"{case_id} executionStatus")
                )
            except ValueError as exc:
                raise TCKAdapterError(f"{case_id} contains an unknown Oracle status") from exc
            if status is OracleExecutionStatus.SUCCESS:
                raise TCKAdapterError(f"{case_id} failure entry cannot use SUCCESS")
            expected = self._string(item.get("expectedDetailCode"), f"{case_id} expectedDetailCode")

            def respond(
                request: OracleRequest,
                description: OracleRunnerDescription,
                scripted_status: OracleExecutionStatus = status,
            ) -> OracleExecutionResult:
                return _execution(request, description, scripted_status)

            episode = _run_episode(_ScriptedOracleRunner(respond))
            detail = episode.validity_detail.code if episode.validity_detail else None
            if not (
                episode.validity is Validity.ORACLE_FAILURE
                and episode.task_verdict is TaskVerdict.INCONCLUSIVE
                and episode.state is EpisodeState.INVALID
                and detail == expected
            ):
                return self._fail(case_id, f"{status.value} escaped stable failure semantics")
        return self._pass(
            case_id,
            "all Oracle failures are evaluation-invalid, task-inconclusive, and detail-preserving",
        )

    def _evidence_integrity(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        missing_id = self._string(vector.get("missingEvidenceId"), f"{case_id} missingEvidenceId")

        def missing(request: OracleRequest, description: OracleRunnerDescription) -> OracleExecutionResult:
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
                OracleExecutionStatus.SUCCESS,
                results=(result,),
            )

        missing_episode = _run_episode(_ScriptedOracleRunner(missing))
        declared_digest = self._string(vector.get("declaredDigest"), f"{case_id} declaredDigest")
        tampered = self._hex(vector.get("tamperedBytesHex"), f"{case_id} tamperedBytesHex")
        tampered_id = "ev_oracle_tck_tampered"

        def mismatch(request: OracleRequest, description: OracleRunnerDescription) -> OracleExecutionResult:
            payload = _UntrustedEvidencePayload(
                tampered_id,
                "state_projection",
                tampered,
                "application/octet-stream",
                declared_digest,
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
                OracleExecutionStatus.SUCCESS,
                results=(result,),
                evidence=(payload,),
            )

        mismatch_episode = _run_episode(_ScriptedOracleRunner(mismatch))
        valid = self._protocol_invalid(missing_episode) and self._protocol_invalid(mismatch_episode)
        return self._result(
            case_id,
            valid,
            "missing and digest-invalid Evidence invalidate Oracle evaluation without task failure",
            "Oracle Evidence integrity failure was accepted or misclassified",
        )

    def _execution_audit(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        raw = vector.get("acceptedResult")
        if not isinstance(raw, Mapping):
            raise TCKAdapterError(f"{case_id} acceptedResult must be an object")
        result = VerificationResult(
            self._string(raw.get("claimId"), f"{case_id} claimId"),
            self._string(raw.get("dimension"), f"{case_id} dimension"),
            self._string(raw.get("verdict"), f"{case_id} verdict"),
            self._string(raw.get("severity"), f"{case_id} severity"),
            self._string(raw.get("method"), f"{case_id} method"),
            self._string(raw.get("evaluatorVersion"), f"{case_id} evaluatorVersion"),
            confidence=float(raw.get("confidence", 1.0)),
        )

        def accepted(request: OracleRequest, description: OracleRunnerDescription) -> OracleExecutionResult:
            return _execution(
                request,
                description,
                OracleExecutionStatus.SUCCESS,
                results=(result,),
            )

        episode = _run_episode(_ScriptedOracleRunner(accepted))
        record = episode.oracle_evaluation
        execution_event = next(
            event for event in episode.events if event.event_type == "oracle.execution.completed"
        )
        execution_evidence_id = f"ev_{episode.episode_id}_oracle_execution"
        accepted_bound = (
            record is not None
            and record.evaluation_validity is Validity.VALID
            and record.execution_record_digest == execution_event.payload.get("artifact_digest")
            and len(record.accepted_results) == 1
            and record.accepted_results[0].claim_id == result.claim_id
            and execution_evidence_id in record.accepted_results[0].evidence_ids
            and record.record_digest == digest(record.to_dict())
        )
        immutable = False
        if record is not None:
            try:
                record.oracle_id = "tampered"  # type: ignore[misc]
            except (FrozenInstanceError, AttributeError):
                immutable = True

        def substituted(
            request: OracleRequest,
            description: OracleRunnerDescription,
        ) -> OracleExecutionResult:
            empty_digest = sha256_digest(b"")
            artifact = OracleExecutionArtifact(
                request_id=request.request_id,
                oracle_package_digest=request.package.identity_digest,
                oracle_code_digest=request.package.code_digest,
                runner_config_digest=description.identity_digest,
                input_digest=request.context.input_digest,
                status=OracleExecutionStatus.SUCCESS,
                duration_ms=1,
                exit_code=0,
                stdout_digest=empty_digest,
                stderr_digest=empty_digest,
                output_digest=sha256_digest(b"substituted-output"),
            )
            return OracleExecutionResult(
                request.request_id,
                OracleExecutionStatus.SUCCESS,
                (result,),
                (),
                artifact,
            )

        substituted_episode = _run_episode(_ScriptedOracleRunner(substituted))
        substituted_detail = (
            substituted_episode.validity_detail.code
            if substituted_episode.validity_detail is not None
            else None
        )
        substitution_rejected = (
            substituted_episode.validity is Validity.ORACLE_FAILURE
            and substituted_episode.task_verdict is TaskVerdict.INCONCLUSIVE
            and substituted_episode.state is EpisodeState.INVALID
            and substituted_detail == "ORACLE_PROTOCOL_ERROR"
            and not substituted_episode.verification
        )
        return self._result(
            case_id,
            accepted_bound and immutable and substitution_rejected,
            "execution identity, accepted result representation and substitution rejection are auditable",
            "Oracle execution acceptance audit binding is incomplete",
        )

    @staticmethod
    def _protocol_invalid(episode: object) -> bool:
        detail = getattr(episode, "validity_detail", None)
        return (
            getattr(episode, "validity", None) is Validity.ORACLE_FAILURE
            and getattr(episode, "state", None) is EpisodeState.INVALID
            and getattr(episode, "task_verdict", None) is TaskVerdict.INCONCLUSIVE
            and getattr(detail, "code", None) == "ORACLE_PROTOCOL_ERROR"
        )

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        value = metadata.get("id") if isinstance(metadata, Mapping) else None
        return ReferenceOracleTCKAdapter._string(value, "Oracle TCK metadata.id")

    @staticmethod
    def _vector(case: Mapping[str, Any], case_id: str) -> Mapping[str, Any]:
        value = case.get("vector")
        if not isinstance(value, Mapping):
            raise TCKAdapterError(f"{case_id} vector must be an object")
        return value

    @staticmethod
    def _string(value: object, label: str) -> str:
        if not isinstance(value, str) or not value:
            raise TCKAdapterError(f"{label} must be a non-empty string")
        return value

    @classmethod
    def _strings(cls, value: object, label: str) -> list[str]:
        if not isinstance(value, list) or not value:
            raise TCKAdapterError(f"{label} must be a non-empty array")
        result = [cls._string(item, label) for item in value]
        if len(result) != len(set(result)):
            raise TCKAdapterError(f"{label} must not contain duplicates")
        return result

    @staticmethod
    def _hex(value: object, label: str) -> bytes:
        if not isinstance(value, str):
            raise TCKAdapterError(f"{label} must be hexadecimal")
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

    @classmethod
    def _result(
        cls, case_id: str, condition: bool, success: str, failure: str
    ) -> TCKCaseResult:
        return cls._pass(case_id, success) if condition else cls._fail(case_id, failure)

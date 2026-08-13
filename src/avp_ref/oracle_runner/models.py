"""Immutable models for isolated Oracle execution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from avp_ref.artifacts import ArtifactRef, sha256_digest, validate_sha256_digest
from avp_ref.canonical import digest
from avp_ref.models import TaskVerdict, Validity, ValidityDetail, VerificationResult

from .errors import OracleProtocolError


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _require_sha256(value: str, label: str) -> None:
    try:
        validate_sha256_digest(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a sha256 digest") from exc


def _verification_result_dict(item: VerificationResult) -> dict[str, object]:
    return {
        "claimId": item.claim_id,
        "dimension": item.dimension,
        "verdict": item.verdict,
        "severity": item.severity,
        "method": item.method,
        "evaluatorVersion": item.evaluator_version,
        "evidenceIds": list(item.evidence_ids),
        "confidence": item.confidence,
        "validity": item.validity.value,
    }


def oracle_output_digest(
    results: tuple[VerificationResult, ...],
    evidence: tuple[object, ...],
) -> str:
    """Digest the trusted metadata representation of one Oracle output."""

    return digest(
        {
            "results": [
                {
                    "claim_id": item.claim_id,
                    "dimension": item.dimension,
                    "verdict": item.verdict,
                    "severity": item.severity,
                    "method": item.method,
                    "evaluator_version": item.evaluator_version,
                    "evidence_ids": list(item.evidence_ids),
                    "confidence": item.confidence,
                    "validity": item.validity.value,
                }
                for item in results
            ],
            "evidence": [
                {
                    "evidence_id": item.evidence_id,
                    "type": item.evidence_type,
                    "media_type": item.media_type,
                    "digest": item.digest,
                    "classification": item.classification,
                    "producer": item.producer,
                }
                for item in evidence
            ],
        }
    )


class OracleExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    CRASHED = "CRASHED"
    PROTOCOL_ERROR = "PROTOCOL_ERROR"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"


@dataclass(frozen=True, slots=True)
class OracleSandboxPolicy:
    """Resource and inheritance policy for one Oracle worker process."""

    timeout_seconds: float = 5.0
    cpu_seconds: int = 3
    memory_bytes: int = 256 * 1024 * 1024
    max_file_bytes: int = 1024 * 1024
    max_open_files: int = 64
    max_request_bytes: int = 1024 * 1024
    max_response_bytes: int = 1024 * 1024
    inherited_environment: tuple[str, ...] = ()
    enforce_resource_limits: bool = True

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("oracle timeout_seconds must be > 0")
        for name in (
            "cpu_seconds",
            "memory_bytes",
            "max_file_bytes",
            "max_open_files",
            "max_request_bytes",
            "max_response_bytes",
        ):
            if int(getattr(self, name)) <= 0:
                raise ValueError(f"oracle {name} must be > 0")
        inherited = tuple(
            sorted({item for item in self.inherited_environment if item})
        )
        object.__setattr__(self, "inherited_environment", inherited)

    def to_dict(self) -> dict[str, object]:
        return {
            "timeout_seconds": self.timeout_seconds,
            "cpu_seconds": self.cpu_seconds,
            "memory_bytes": self.memory_bytes,
            "max_file_bytes": self.max_file_bytes,
            "max_open_files": self.max_open_files,
            "max_request_bytes": self.max_request_bytes,
            "max_response_bytes": self.max_response_bytes,
            "inherited_environment": list(self.inherited_environment),
            "enforce_resource_limits": self.enforce_resource_limits,
        }


@dataclass(frozen=True, slots=True)
class OracleRunnerDescription:
    name: str
    version: str
    protocol_version: str
    isolation: str
    policy: OracleSandboxPolicy
    worker_module: str
    worker_code_digest: str
    allowed_module_prefixes: tuple[str, ...]
    filesystem_isolation: bool = False
    network_isolation: bool = False

    def __post_init__(self) -> None:
        _require_sha256(self.worker_code_digest, "oracle worker_code_digest")
        if not self.worker_module or not self.allowed_module_prefixes:
            raise ValueError(
                "oracle runner worker/module allowlist must be non-empty"
            )
        object.__setattr__(
            self,
            "allowed_module_prefixes",
            tuple(sorted(set(self.allowed_module_prefixes))),
        )

    @property
    def identity_digest(self) -> str:
        return digest(
            {
                "name": self.name,
                "version": self.version,
                "protocol_version": self.protocol_version,
                "isolation": self.isolation,
                "policy": self.policy.to_dict(),
                "worker_module": self.worker_module,
                "worker_code_digest": self.worker_code_digest,
                "allowed_module_prefixes": list(self.allowed_module_prefixes),
                "filesystem_isolation": self.filesystem_isolation,
                "network_isolation": self.network_isolation,
            }
        )


@dataclass(frozen=True, slots=True)
class OraclePackage:
    """Immutable Oracle descriptor with an optional packaging-layer identity."""

    oracle_id: str
    version: str
    entrypoint: str
    code_digest: str
    projections: tuple[str, ...]
    input_pointers: Mapping[str, str] = field(default_factory=dict)
    package_digest: str | None = None

    def __post_init__(self) -> None:
        if not self.oracle_id or not self.version or not self.entrypoint:
            raise ValueError("oracle package identity fields must be non-empty")
        _require_sha256(self.code_digest, "oracle code_digest")
        if self.package_digest is not None:
            _require_sha256(self.package_digest, "oracle package_digest")
        projections = tuple(sorted({item for item in self.projections if item}))
        if not projections:
            raise ValueError("oracle package must request at least one projection")
        pointers = {
            str(name): str(pointer)
            for name, pointer in self.input_pointers.items()
        }
        if any(
            not name or not pointer.startswith("/")
            for name, pointer in pointers.items()
        ):
            raise ValueError(
                "oracle input_pointers must use non-empty RFC 6901 JSON Pointers"
            )
        object.__setattr__(self, "projections", projections)
        object.__setattr__(
            self,
            "input_pointers",
            MappingProxyType(dict(sorted(pointers.items()))),
        )

    def descriptor_dict(self) -> dict[str, object]:
        return {
            "oracle_id": self.oracle_id,
            "version": self.version,
            "entrypoint": self.entrypoint,
            "code_digest": self.code_digest,
            "projections": list(self.projections),
            "input_pointers": dict(self.input_pointers),
        }

    def to_dict(self) -> dict[str, object]:
        result = self.descriptor_dict()
        if self.package_digest is not None:
            result["package_digest"] = self.package_digest
        return result

    @property
    def identity_digest(self) -> str:
        return self.package_digest or digest(self.descriptor_dict())


@dataclass(frozen=True, slots=True)
class ProjectionSnapshot:
    projection_id: str
    data: object
    state_digest: str

    def __post_init__(self) -> None:
        if not self.projection_id:
            raise ValueError("projection_id must be non-empty")
        _require_sha256(self.state_digest, "projection state_digest")
        frozen = _freeze(self.data)
        if digest(_thaw(frozen)) != self.state_digest:
            raise ValueError(f"projection digest mismatch: {self.projection_id}")
        object.__setattr__(self, "data", frozen)

    def to_dict(self) -> dict[str, object]:
        return {
            "projection_id": self.projection_id,
            "data": _thaw(self.data),
            "state_digest": self.state_digest,
        }


@dataclass(frozen=True, slots=True)
class OracleEvaluationContext:
    """Complete parent-to-Oracle data surface; no live evaluator handles exist."""

    episode_id: str
    scenario_instance_digest: str
    manifest_digest: str
    inputs: Mapping[str, object]
    projections: Mapping[str, ProjectionSnapshot]

    def __post_init__(self) -> None:
        if not self.episode_id:
            raise ValueError("oracle context episode_id must be non-empty")
        _require_sha256(self.scenario_instance_digest, "scenario_instance_digest")
        _require_sha256(self.manifest_digest, "manifest_digest")
        object.__setattr__(self, "inputs", _freeze(self.inputs))
        object.__setattr__(
            self,
            "projections",
            MappingProxyType(dict(sorted(self.projections.items()))),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "episode_id": self.episode_id,
            "scenario_instance_digest": self.scenario_instance_digest,
            "manifest_digest": self.manifest_digest,
            "inputs": _thaw(self.inputs),
            "projections": {
                key: value.to_dict() for key, value in self.projections.items()
            },
        }

    @property
    def input_digest(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class OracleRequest:
    request_id: str
    package: OraclePackage
    context: OracleEvaluationContext

    def __post_init__(self) -> None:
        if not self.request_id:
            raise ValueError("oracle request_id must be non-empty")

    def to_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "package": self.package.to_dict(),
            "context": self.context.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class OracleEvidencePayload:
    """Private worker-to-parent Evidence representation awaiting publication."""

    evidence_id: str
    evidence_type: str
    content: bytes
    media_type: str
    digest: str
    classification: str = "evaluator-confidential"
    producer: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, str) or not self.evidence_id:
            raise ValueError("oracle evidence_id must be non-empty")
        if not isinstance(self.evidence_type, str) or not self.evidence_type:
            raise ValueError("oracle evidence_type must be non-empty")
        if not isinstance(self.content, bytes):
            raise TypeError("oracle evidence content must be bytes")

        # ArtifactRef is the public validator for digest/media-type/size shape.
        # Constructing it here validates representation metadata without
        # publishing worker-controlled bytes into the trusted parent store.
        ArtifactRef(self.digest, len(self.content), self.media_type)
        if sha256_digest(self.content) != self.digest:
            raise ValueError(f"oracle evidence digest mismatch: {self.evidence_id}")
        if not isinstance(self.classification, str) or not self.classification:
            raise ValueError("oracle evidence classification must be non-empty")
        if self.producer is not None and (
            not isinstance(self.producer, str) or not self.producer
        ):
            raise ValueError("oracle evidence producer must be non-empty when present")


@dataclass(frozen=True, slots=True)
class OracleEvaluationOutput:
    results: tuple[VerificationResult, ...]
    evidence: tuple[OracleEvidencePayload, ...] = ()


@dataclass(frozen=True, slots=True)
class OracleExecutionArtifact:
    request_id: str
    oracle_package_digest: str
    oracle_code_digest: str
    runner_config_digest: str
    input_digest: str
    status: OracleExecutionStatus
    duration_ms: int
    exit_code: int | None
    stdout_digest: str
    stderr_digest: str
    output_digest: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "oracle_package_digest": self.oracle_package_digest,
            "oracle_code_digest": self.oracle_code_digest,
            "runner_config_digest": self.runner_config_digest,
            "input_digest": self.input_digest,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "exit_code": self.exit_code,
            "stdout_digest": self.stdout_digest,
            "stderr_digest": self.stderr_digest,
            "output_digest": self.output_digest,
        }

    @property
    def record_digest(self) -> str:
        """Digest the structured execution record; this is not Artifact identity."""

        return digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class OracleExecutionResult:
    request_id: str
    status: OracleExecutionStatus
    results: tuple[VerificationResult, ...]
    evidence: tuple[OracleEvidencePayload, ...]
    artifact: OracleExecutionArtifact

    def __post_init__(self) -> None:
        # Protocol objects may arrive from third-party runner adapters. Normalize
        # mutable list inputs before validating the output digest so the object
        # cannot be changed through a caller-held collection after construction.
        results = tuple(self.results)
        evidence = tuple(self.evidence)
        object.__setattr__(self, "results", results)
        object.__setattr__(self, "evidence", evidence)

        if self.request_id != self.artifact.request_id:
            raise OracleProtocolError("Oracle execution request identity mismatch")
        if self.status is not self.artifact.status:
            raise OracleProtocolError("Oracle execution status and artifact status differ")
        if self.status is OracleExecutionStatus.SUCCESS:
            expected = oracle_output_digest(results, evidence)
            if self.artifact.output_digest != expected:
                raise OracleProtocolError("Oracle execution output digest mismatch")
        elif results or evidence or self.artifact.output_digest is not None:
            raise OracleProtocolError("failed Oracle execution cannot expose accepted output")


@dataclass(frozen=True, slots=True)
class OracleEvaluationRecord:
    oracle_id: str
    oracle_version: str
    package_digest: str
    input_digest: str
    execution_record_digest: str | None
    evaluation_validity: Validity
    task_verdict: TaskVerdict
    accepted_results: tuple[VerificationResult, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    validity_detail: ValidityDetail | None = None

    def __post_init__(self) -> None:
        if not self.oracle_id or not self.oracle_version:
            raise ValueError("Oracle evaluation identity fields must be non-empty")
        _require_sha256(self.package_digest, "Oracle evaluation package_digest")
        _require_sha256(self.input_digest, "Oracle evaluation input_digest")
        if self.execution_record_digest is not None:
            _require_sha256(
                self.execution_record_digest,
                "Oracle evaluation execution_record_digest",
            )
        if self.evaluation_validity not in {Validity.VALID, Validity.ORACLE_FAILURE}:
            raise ValueError("Oracle evaluation validity must be VALID or ORACLE_FAILURE")
        accepted = tuple(self.accepted_results)
        evidence_ids = tuple(self.evidence_ids)
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("Oracle evaluation evidence ids must be unique")
        if not all(isinstance(item, str) and 1 <= len(item) <= 256 for item in evidence_ids):
            raise ValueError("Oracle evaluation evidence ids must contain 1..256 characters")
        if any(item.validity is not Validity.VALID for item in accepted):
            raise ValueError("accepted Oracle verification results must be VALID")
        if self.evaluation_validity is Validity.ORACLE_FAILURE:
            if self.validity_detail is None:
                raise ValueError("ORACLE_FAILURE requires validity_detail")
            if self.task_verdict is not TaskVerdict.INCONCLUSIVE:
                raise ValueError("ORACLE_FAILURE requires INCONCLUSIVE task verdict")
            if accepted:
                raise ValueError("ORACLE_FAILURE cannot contain accepted results")
        else:
            if self.execution_record_digest is None:
                raise ValueError("VALID Oracle evaluation requires execution_record_digest")
            if self.validity_detail is not None:
                raise ValueError("VALID Oracle evaluation cannot contain validity_detail")
        object.__setattr__(self, "accepted_results", accepted)
        object.__setattr__(self, "evidence_ids", evidence_ids)

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "oracle": {
                "oracleId": self.oracle_id,
                "version": self.oracle_version,
                "packageDigest": self.package_digest,
            },
            "inputDigest": self.input_digest,
            "evaluationValidity": self.evaluation_validity.value,
            "taskVerdict": self.task_verdict.value,
            "acceptedResults": [
                _verification_result_dict(item) for item in self.accepted_results
            ],
            "evidenceIds": list(self.evidence_ids),
        }
        if self.execution_record_digest is not None:
            result["executionRecordDigest"] = self.execution_record_digest
        if self.validity_detail is not None:
            result["validityDetail"] = self.validity_detail.to_dict()
        return result

    @property
    def record_digest(self) -> str:
        return digest(self.to_dict())

"""Immutable models for isolated Oracle execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from avp_ref.canonical import digest
from avp_ref.models import Evidence, VerificationResult


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


class OracleExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    CRASHED = "CRASHED"
    PROTOCOL_ERROR = "PROTOCOL_ERROR"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"


@dataclass(frozen=True, slots=True)
class OracleSandboxPolicy:
    """Resource/inheritance policy for one Oracle worker process.

    The reference subprocess runner provides a process boundary plus POSIX
    resource limits where available. It intentionally does not claim network or
    filesystem sandboxing; stronger isolation belongs to container/microVM
    runners.
    """

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
        for name in ("cpu_seconds", "memory_bytes", "max_file_bytes", "max_open_files", "max_request_bytes", "max_response_bytes"):
            if int(getattr(self, name)) <= 0:
                raise ValueError(f"oracle {name} must be > 0")
        object.__setattr__(self, "inherited_environment", tuple(sorted({item for item in self.inherited_environment if item})))

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
    filesystem_isolation: bool = False
    network_isolation: bool = False

    @property
    def identity_digest(self) -> str:
        return digest({
            "name": self.name,
            "version": self.version,
            "protocol_version": self.protocol_version,
            "isolation": self.isolation,
            "policy": self.policy.to_dict(),
            "filesystem_isolation": self.filesystem_isolation,
            "network_isolation": self.network_isolation,
        })


@dataclass(frozen=True, slots=True)
class OraclePackage:
    """Immutable identity and minimum data contract of an Oracle package."""

    oracle_id: str
    version: str
    entrypoint: str
    code_digest: str
    projections: tuple[str, ...]
    input_pointers: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.oracle_id or not self.version or not self.entrypoint:
            raise ValueError("oracle package identity fields must be non-empty")
        if not self.code_digest.startswith("sha256:") or len(self.code_digest) != 71:
            raise ValueError("oracle code_digest must be a sha256 digest")
        projections = tuple(sorted({item for item in self.projections if item}))
        if not projections:
            raise ValueError("oracle package must request at least one projection")
        pointers = {str(name): str(pointer) for name, pointer in self.input_pointers.items()}
        if any(not name or not pointer.startswith("/") for name, pointer in pointers.items()):
            raise ValueError("oracle input_pointers must use non-empty RFC 6901 JSON Pointers")
        object.__setattr__(self, "projections", projections)
        object.__setattr__(self, "input_pointers", MappingProxyType(dict(sorted(pointers.items()))))

    def to_dict(self) -> dict[str, object]:
        return {
            "oracle_id": self.oracle_id,
            "version": self.version,
            "entrypoint": self.entrypoint,
            "code_digest": self.code_digest,
            "projections": list(self.projections),
            "input_pointers": dict(self.input_pointers),
        }

    @property
    def identity_digest(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class ProjectionSnapshot:
    projection_id: str
    data: object
    state_digest: str

    def __post_init__(self) -> None:
        frozen = _freeze(self.data)
        if digest(_thaw(frozen)) != self.state_digest:
            raise ValueError(f"projection digest mismatch: {self.projection_id}")
        object.__setattr__(self, "data", frozen)

    def to_dict(self) -> dict[str, object]:
        return {"projection_id": self.projection_id, "data": _thaw(self.data), "state_digest": self.state_digest}


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
        object.__setattr__(self, "inputs", _freeze(self.inputs))
        object.__setattr__(self, "projections", MappingProxyType(dict(sorted(self.projections.items()))))

    def to_dict(self) -> dict[str, object]:
        return {
            "episode_id": self.episode_id,
            "scenario_instance_digest": self.scenario_instance_digest,
            "manifest_digest": self.manifest_digest,
            "inputs": _thaw(self.inputs),
            "projections": {key: value.to_dict() for key, value in self.projections.items()},
        }

    @property
    def input_digest(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class OracleRequest:
    request_id: str
    package: OraclePackage
    context: OracleEvaluationContext

    def to_dict(self) -> dict[str, object]:
        return {"request_id": self.request_id, "package": self.package.to_dict(), "context": self.context.to_dict()}


@dataclass(frozen=True, slots=True)
class OracleEvaluationOutput:
    results: tuple[VerificationResult, ...]
    evidence: tuple[Evidence, ...] = ()


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
    def artifact_digest(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class OracleExecutionResult:
    request_id: str
    status: OracleExecutionStatus
    results: tuple[VerificationResult, ...]
    evidence: tuple[Evidence, ...]
    artifact: OracleExecutionArtifact

"""Typed reference model for the AVP Environment Fabric candidate contract.

These Python types implement the language-neutral specification; they are not
protocol authority.  The normative field semantics live under ``spec/fabric``
and the root JSON Schemas encode the serialized contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from avp_ref.environment import RestoreEquivalence


class Participation(str, Enum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"


class ResourceKind(str, Enum):
    STATE = "state"
    BROWSER = "browser"
    NETWORK = "network"
    TIME = "time"
    COMPUTE = "compute"


class FabricOperation(str, Enum):
    RESET = "RESET"
    SNAPSHOT = "SNAPSHOT"
    RESTORE = "RESTORE"
    RELEASE = "RELEASE"


class OperationStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    NOT_PARTICIPATING = "NOT_PARTICIPATING"


@dataclass(frozen=True, slots=True)
class ArtifactIdentity:
    digest: str
    size: int
    media_type: str

    def to_dict(self) -> dict[str, object]:
        return {"digest": self.digest, "size": self.size, "mediaType": self.media_type}


@dataclass(frozen=True, slots=True)
class ResourceCapabilityDeclaration:
    capability_id: str
    profile: str
    revision: str
    participation: Participation

    @property
    def semantic_identity(self) -> tuple[str, str, str]:
        return self.capability_id, self.profile, self.revision

    def to_dict(self) -> dict[str, str]:
        return {
            "capabilityId": self.capability_id,
            "profile": self.profile,
            "revision": self.revision,
            "participation": self.participation.value,
        }


@dataclass(frozen=True, slots=True)
class EnvironmentResourceDescriptor:
    resource_id: str
    environment_id: str
    resource_kind: ResourceKind
    participation: Participation
    capabilities: tuple[ResourceCapabilityDeclaration, ...] = ()
    identity_artifacts: tuple[ArtifactIdentity, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "resourceId": self.resource_id,
            "environmentId": self.environment_id,
            "resourceKind": self.resource_kind.value,
            "participation": self.participation.value,
            "capabilities": [item.to_dict() for item in self.capabilities],
            "identityArtifacts": [item.to_dict() for item in self.identity_artifacts],
        }


@dataclass(frozen=True, slots=True)
class EnvironmentFabricManifest:
    environment_id: str
    scenario_instance_digest: str
    resources: tuple[EnvironmentResourceDescriptor, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "apiVersion": "avp.fabric/v0.1",
            "kind": "EnvironmentFabricManifest",
            "environmentId": self.environment_id,
            "scenarioInstanceDigest": self.scenario_instance_digest,
            "resources": [item.to_dict() for item in self.resources],
        }


@dataclass(frozen=True, slots=True)
class ResourceOperationResult:
    resource_id: str
    participation: Participation
    status: OperationStatus
    restore_fidelity: RestoreEquivalence | None = None
    failure_code: str | None = None

    def to_dict(self) -> dict[str, str]:
        value = {
            "resourceId": self.resource_id,
            "participation": self.participation.value,
            "status": self.status.value,
        }
        if self.restore_fidelity is not None:
            value["restoreFidelity"] = self.restore_fidelity.value
        if self.failure_code is not None:
            value["failureCode"] = self.failure_code
        return value


@dataclass(frozen=True, slots=True)
class FabricOperationResult:
    operation_id: str
    operation: FabricOperation
    environment_id: str
    status: OperationStatus
    resource_results: tuple[ResourceOperationResult, ...]
    aggregate_restore_fidelity: RestoreEquivalence | None = None

    def to_dict(self) -> dict[str, object]:
        value: dict[str, object] = {
            "apiVersion": "avp.fabric/v0.1",
            "kind": "FabricOperationResult",
            "operationId": self.operation_id,
            "operation": self.operation.value,
            "environmentId": self.environment_id,
            "status": self.status.value,
            "resourceResults": [item.to_dict() for item in self.resource_results],
        }
        if self.aggregate_restore_fidelity is not None:
            value["aggregateRestoreFidelity"] = self.aggregate_restore_fidelity.value
        return value

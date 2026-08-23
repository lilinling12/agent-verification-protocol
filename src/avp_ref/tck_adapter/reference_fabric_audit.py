"""Focused execution controls for Environment Fabric completeness invariants.

These cases stay separate from the broader Fabric vectors so missing required
resource handling and released-Fabric fail-closed behavior remain directly
auditable conformance obligations.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from avp_ref.fabric import (
    CapabilityRequirement,
    EnvironmentFabric,
    EnvironmentResourceDescriptor,
    FabricCompatibilityError,
    FabricOperation,
    FabricReferenceError,
    InMemoryFabricResource,
    Participation,
    ResourceCapabilityDeclaration,
    ResourceKind,
)

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


class ReferenceFabricAuditTCKAdapter:
    """Execute focused fail-closed controls omitted from aggregate Fabric cases."""

    _REQUIRED_RESOURCE = "AVP-TCK-FABRIC-REQUIRED-RESOURCE-001"
    _STALE_FABRIC = "AVP-TCK-FABRIC-STALE-FABRIC-001"

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return frozenset({self._REQUIRED_RESOURCE, self._STALE_FABRIC})

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._mapping(case.get("vector"), f"{case_id}.vector")
        if case_id == self._REQUIRED_RESOURCE:
            passed, detail = self._required_resource(vector)
        elif case_id == self._STALE_FABRIC:
            passed, detail = self._stale_fabric(vector)
        else:
            raise TCKAdapterError(f"unsupported Fabric audit case: {case_id}")
        return TCKCaseResult(case_id, TCKStatus.PASS if passed else TCKStatus.FAIL, detail)

    def _required_resource(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        environment_id = "env-required-resource"
        present_id = self._string(vector.get("presentResourceId"), "presentResourceId")
        missing_id = self._string(
            vector.get("missingRequiredResourceId"), "missingRequiredResourceId"
        )
        capability_doc = self._mapping(vector.get("requiredCapability"), "requiredCapability")
        required = ResourceCapabilityDeclaration(
            self._string(capability_doc.get("capabilityId"), "capabilityId"),
            self._string(capability_doc.get("profile"), "profile"),
            self._string(capability_doc.get("revision"), "revision"),
            Participation(self._string(capability_doc.get("participation"), "participation")),
        )
        if required.participation is not Participation.REQUIRED:
            raise TCKAdapterError("required-resource vector must select REQUIRED participation")

        present = InMemoryFabricResource(
            EnvironmentResourceDescriptor(
                resource_id=present_id,
                environment_id=environment_id,
                resource_kind=ResourceKind.STATE,
                participation=Participation.REQUIRED,
            )
        )
        fabric = EnvironmentFabric(
            environment_id=environment_id,
            scenario_instance_digest=self._digest("f"),
            resources=(present,),
            capability_requirements=(CapabilityRequirement(missing_id, required),),
        )
        try:
            fabric.provision()
            rejected = False
        except FabricCompatibilityError:
            rejected = True

        passed = (
            rejected
            and present.provision_side_effects == 0
            and not fabric.ready
            and not present.released
        )
        return passed, (
            "missing required resource rejects provisioning before any existing-resource side effect"
            if passed
            else "missing required resource was downgraded, partially provisioned, or reached READY"
        )

    def _stale_fabric(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        environment_id = "env-stale-fabric"
        resource = InMemoryFabricResource(
            EnvironmentResourceDescriptor(
                resource_id="primary-state",
                environment_id=environment_id,
                resource_kind=ResourceKind.STATE,
                participation=Participation.REQUIRED,
            )
        )
        fabric = EnvironmentFabric(
            environment_id=environment_id,
            scenario_instance_digest=self._digest("9"),
            resources=(resource,),
        )
        fabric.provision()
        fabric.release()

        try:
            fabric.manifest()
            manifest_rejected = False
        except FabricReferenceError:
            manifest_rejected = True

        try:
            fabric.execute_composite(FabricOperation.RESET)
            operation_rejected = False
        except FabricReferenceError:
            operation_rejected = True

        passed = (
            manifest_rejected
            and operation_rejected
            and not fabric.ready
            and resource.released
            and resource.provision_side_effects == 1
        )
        return passed, (
            "released Fabric and owned resource references remain stale and fail closed"
            if passed
            else "released Fabric reference remained usable or resurrected owned resources"
        )

    @staticmethod
    def _digest(character: str) -> str:
        return "sha256:" + character * 64

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("Fabric audit TCK case metadata.id is missing")
        return case_id

    @staticmethod
    def _mapping(value: Any, context: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise TCKAdapterError(f"Fabric audit TCK {context} must be an object")
        return value

    @staticmethod
    def _string(value: Any, context: str) -> str:
        if not isinstance(value, str) or not value:
            raise TCKAdapterError(f"Fabric audit TCK {context} must be a non-empty string")
        return value

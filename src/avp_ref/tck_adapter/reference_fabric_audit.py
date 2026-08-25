"""Focused execution controls layered onto the Environment Fabric TCK.

The broad Fabric adapter executes every registered vector first. This wrapper
adds two requirement-specific fail-closed controls to the existing capability
and cleanup case identities, avoiding duplicate registry entries while keeping
all conformance behavior executable from the packaged wheel.
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
from .reference_fabric import ReferenceFabricTCKAdapter


class ReferenceFabricAuditTCKAdapter:
    """Execute registered Fabric vectors plus focused completeness assertions."""

    _CAPABILITY = "AVP-TCK-FABRIC-CAPABILITY-001"
    _CLEANUP = "AVP-TCK-FABRIC-CLEANUP-001"

    def __init__(self) -> None:
        self._delegate = ReferenceFabricTCKAdapter()

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return self._delegate.supported_case_ids

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        baseline = self._delegate.evaluate(case)
        if baseline.status is not TCKStatus.PASS:
            return baseline

        case_id = baseline.case_id
        vector = self._mapping(case.get("vector"), f"{case_id}.vector")
        if case_id == self._CAPABILITY:
            passed, detail = self._required_resource_absence(vector)
        elif case_id == self._CLEANUP:
            passed, detail = self._released_fabric_reference()
        else:
            return baseline

        if not passed:
            return TCKCaseResult(case_id, TCKStatus.FAIL, detail)
        return TCKCaseResult(case_id, TCKStatus.PASS, f"{baseline.detail}; {detail}")

    def _required_resource_absence(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        environment_id = "env-required-resource-control"
        capability_doc = self._mapping(vector.get("requiredCapability"), "requiredCapability")
        required = ResourceCapabilityDeclaration(
            self._string(capability_doc.get("capabilityId"), "capabilityId"),
            self._string(capability_doc.get("profile"), "profile"),
            self._string(capability_doc.get("revision"), "revision"),
            Participation(self._string(capability_doc.get("participation"), "participation")),
        )
        if required.participation is not Participation.REQUIRED:
            raise TCKAdapterError("Fabric capability vector must keep requiredCapability REQUIRED")

        present = InMemoryFabricResource(
            EnvironmentResourceDescriptor(
                resource_id="primary-state",
                environment_id=environment_id,
                resource_kind=ResourceKind.STATE,
                participation=Participation.REQUIRED,
            )
        )
        fabric = EnvironmentFabric(
            environment_id=environment_id,
            scenario_instance_digest=self._digest("f"),
            resources=(present,),
            capability_requirements=(
                CapabilityRequirement("required-resource-not-present", required),
            ),
        )
        try:
            fabric.provision()
            rejected = False
        except FabricCompatibilityError:
            rejected = True

        passed = rejected and present.provision_side_effects == 0 and not fabric.ready
        return passed, (
            "missing required resource fails before any present-resource provision side effect"
            if passed
            else "missing required resource was downgraded, partially provisioned, or reached READY"
        )

    def _released_fabric_reference(self) -> tuple[bool, str]:
        environment_id = "env-stale-fabric-control"
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
            "released Fabric reference rejects reads and operations without resurrecting owned resources"
            if passed
            else "released Fabric reference remained usable or resurrected owned resources"
        )

    @staticmethod
    def _digest(character: str) -> str:
        return "sha256:" + character * 64

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

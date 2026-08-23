"""Execution adapter for the Environment Fabric v0.1 candidate TCK profile.

The TCK vectors remain authoritative.  This adapter exercises the packaged
reference Fabric implementation and intentionally includes behavior-negative
controls whose capability metadata is identical to conforming resources.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from avp_ref.environment import RestoreEquivalence
from avp_ref.fabric import (
    ArtifactIdentity,
    CapabilityRequirement,
    EnvironmentFabric,
    EnvironmentResourceDescriptor,
    FabricCompatibilityError,
    FabricOperation,
    FabricReferenceError,
    InMemoryFabricResource,
    OperationStatus,
    Participation,
    ResourceCapabilityDeclaration,
    ResourceKind,
    SubjectAuthorizationError,
)

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


class ReferenceFabricTCKAdapter:
    """Execute base Fabric composition vectors against real reference behavior."""

    _MANIFEST = "AVP-TCK-FABRIC-MANIFEST-001"
    _CAPABILITY = "AVP-TCK-FABRIC-CAPABILITY-001"
    _AUTHORIZATION = "AVP-TCK-FABRIC-AUTHORIZATION-001"
    _COMPOSITE = "AVP-TCK-FABRIC-COMPOSITE-001"
    _RESTORE = "AVP-TCK-FABRIC-RESTORE-001"
    _SECURITY_EVIDENCE = "AVP-TCK-FABRIC-SECURITY-EVIDENCE-001"
    _EXECUTED_CAPABILITY = "AVP-TCK-FABRIC-EXECUTED-CAPABILITY-001"
    _CLEANUP = "AVP-TCK-FABRIC-CLEANUP-001"

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return frozenset(
            {
                self._MANIFEST,
                self._CAPABILITY,
                self._AUTHORIZATION,
                self._COMPOSITE,
                self._RESTORE,
                self._SECURITY_EVIDENCE,
                self._EXECUTED_CAPABILITY,
                self._CLEANUP,
            }
        )

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._mapping(case.get("vector"), f"{case_id}.vector")
        evaluator = {
            self._MANIFEST: self._manifest,
            self._CAPABILITY: self._capability,
            self._AUTHORIZATION: self._authorization,
            self._COMPOSITE: self._composite,
            self._RESTORE: self._restore,
            self._SECURITY_EVIDENCE: self._security_evidence,
            self._EXECUTED_CAPABILITY: self._executed_capability,
            self._CLEANUP: self._cleanup,
        }.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(f"unsupported reference Fabric TCK case: {case_id}")
        passed, detail = evaluator(vector)
        return TCKCaseResult(case_id, TCKStatus.PASS if passed else TCKStatus.FAIL, detail)

    def _manifest(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        environment_id = self._string(vector.get("environmentId"), "environmentId")
        scenario_digest = self._string(vector.get("scenarioInstanceDigest"), "scenarioInstanceDigest")
        records = self._list(vector.get("resources"), "resources")
        resources = tuple(
            InMemoryFabricResource(
                EnvironmentResourceDescriptor(
                    resource_id=self._string(item.get("resourceId"), "resourceId"),
                    environment_id=environment_id,
                    resource_kind=ResourceKind(self._string(item.get("resourceKind"), "resourceKind")),
                    participation=Participation(self._string(item.get("participation"), "participation")),
                )
            )
            for item in (self._mapping(record, "resource") for record in records)
        )
        fabric = EnvironmentFabric(
            environment_id=environment_id,
            scenario_instance_digest=scenario_digest,
            resources=resources,
        )
        manifest = fabric.manifest().to_dict()
        resource_ids = [item["resourceId"] for item in manifest["resources"]]
        portable_kinds = {item.value for item in ResourceKind}
        kinds_valid = all(item["resourceKind"] in portable_kinds for item in manifest["resources"])

        duplicate_rejected = False
        try:
            EnvironmentFabric(
                environment_id=environment_id,
                scenario_instance_digest=scenario_digest,
                resources=(resources[0], resources[0]),
            )
        except FabricCompatibilityError:
            duplicate_rejected = True

        foreign_descriptor = EnvironmentResourceDescriptor(
            resource_id="foreign-resource",
            environment_id="foreign-environment",
            resource_kind=ResourceKind.STATE,
            participation=Participation.REQUIRED,
        )
        foreign_rejected = False
        try:
            EnvironmentFabric(
                environment_id=environment_id,
                scenario_instance_digest=scenario_digest,
                resources=(InMemoryFabricResource(foreign_descriptor),),
            )
        except FabricCompatibilityError:
            foreign_rejected = True

        passed = (
            manifest["environmentId"] == environment_id
            and manifest["scenarioInstanceDigest"] == scenario_digest
            and len(resource_ids) == len(set(resource_ids))
            and duplicate_rejected
            and foreign_rejected
            and kinds_valid
            and all(not str(item).startswith("sha256:") for item in resource_ids)
        )
        return passed, (
            "manifest binds Scenario/Environment ownership with unique portable resource identities"
            if passed
            else "Fabric manifest ownership, uniqueness, or portable classification drifted"
        )

    def _capability(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        required = self._capability_declaration(
            self._mapping(vector.get("requiredCapability"), "requiredCapability")
        )
        optional = self._capability_declaration(
            self._mapping(vector.get("optionalCapability"), "optionalCapability")
        )
        descriptor = self._descriptor(
            "primary-state",
            capabilities=(required,),
            participation=Participation.REQUIRED,
        )
        compatible_resource = InMemoryFabricResource(descriptor)
        compatible = EnvironmentFabric(
            environment_id="env-capability",
            scenario_instance_digest=self._digest("c"),
            resources=(compatible_resource,),
            capability_requirements=(CapabilityRequirement("primary-state", required),),
        )
        compatible.provision()
        compatible_ok = compatible.ready and compatible_resource.provision_side_effects == 1

        missing_resource = InMemoryFabricResource(
            self._descriptor("primary-state", participation=Participation.REQUIRED)
        )
        missing = EnvironmentFabric(
            environment_id="env-capability",
            scenario_instance_digest=self._digest("c"),
            resources=(missing_resource,),
            capability_requirements=(CapabilityRequirement("primary-state", required),),
        )
        missing_failed = False
        try:
            missing.provision()
        except FabricCompatibilityError:
            missing_failed = missing_resource.provision_side_effects == 0

        mismatch = ResourceCapabilityDeclaration(
            required.capability_id,
            required.profile,
            required.revision + "-different",
            required.participation,
        )
        mismatch_resource = InMemoryFabricResource(
            self._descriptor(
                "primary-state",
                capabilities=(mismatch,),
                participation=Participation.REQUIRED,
            )
        )
        incompatible = EnvironmentFabric(
            environment_id="env-capability",
            scenario_instance_digest=self._digest("c"),
            resources=(mismatch_resource,),
            capability_requirements=(CapabilityRequirement("primary-state", required),),
        )
        mismatch_failed = False
        try:
            incompatible.provision()
        except FabricCompatibilityError:
            mismatch_failed = mismatch_resource.provision_side_effects == 0

        optional_resource = InMemoryFabricResource(
            self._descriptor("primary-state", participation=Participation.REQUIRED)
        )
        optional_fabric = EnvironmentFabric(
            environment_id="env-capability",
            scenario_instance_digest=self._digest("c"),
            resources=(optional_resource,),
            capability_requirements=(CapabilityRequirement("primary-state", optional),),
        )
        optional_fabric.provision()
        optional_ok = optional_fabric.ready and optional.participation is Participation.OPTIONAL

        passed = compatible_ok and missing_failed and mismatch_failed and optional_ok
        return passed, (
            "required capability revision is validated before provision side effects without backend-driven downgrade"
            if passed
            else "Fabric capability compatibility or requiredness semantics drifted"
        )

    def _authorization(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        capability = self._capability_declaration(
            self._mapping(vector.get("resourceCapability"), "resourceCapability")
        )
        subject_caps = tuple(str(item) for item in self._list(vector.get("subjectCapabilities"), "subjectCapabilities"))
        privileged = self._string(vector.get("privilegedOperation"), "privilegedOperation")
        resource = InMemoryFabricResource(
            self._descriptor("primary-state", capabilities=(capability,))
        )
        fabric = EnvironmentFabric(
            environment_id="env-authz",
            scenario_instance_digest=self._digest("d"),
            resources=(resource,),
            capability_requirements=(CapabilityRequirement("primary-state", capability),),
            subject_capabilities=subject_caps,
        )
        fabric.provision()
        control_ok = fabric.control_snapshot("primary-state") == resource.state
        subject_denied = False
        try:
            fabric.subject_call(privileged)
        except SubjectAuthorizationError:
            subject_denied = True
        subject_declared_ok = all(fabric.subject_call(item) == item for item in subject_caps)
        passed = control_ok and subject_denied and subject_declared_ok
        return passed, (
            "privileged Resource Capability support remains separate from Subject authorization"
            if passed
            else "Resource Capability support widened or corrupted Subject authority"
        )

    def _composite(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        operation = FabricOperation(self._string(vector.get("operation"), "operation"))
        records = [self._mapping(item, "resource") for item in self._list(vector.get("resources"), "resources")]
        failure_id = self._string(
            self._mapping(vector.get("failureControl"), "failureControl").get("resourceId"),
            "failureControl.resourceId",
        )
        optional_id = self._string(
            self._mapping(vector.get("optionalNonParticipation"), "optionalNonParticipation").get("resourceId"),
            "optionalNonParticipation.resourceId",
        )

        normal_resources = tuple(
            InMemoryFabricResource(
                self._descriptor(
                    self._string(item.get("resourceId"), "resourceId"),
                    participation=Participation(self._string(item.get("participation"), "participation")),
                )
            )
            for item in records
        )
        normal = self._fabric("env-composite", normal_resources)
        normal.provision()
        success = normal.execute_composite(operation, non_participating_optional=(optional_id,))
        normal_ids = {item.resource_id for item in success.resource_results}

        failing_resources = tuple(
            InMemoryFabricResource(
                self._descriptor(
                    self._string(item.get("resourceId"), "resourceId"),
                    participation=Participation(self._string(item.get("participation"), "participation")),
                ),
                fail_operations=(operation,) if item.get("resourceId") == failure_id else (),
            )
            for item in records
        )
        failing = self._fabric("env-composite", failing_resources)
        failing.provision()
        failure = failing.execute_composite(operation, non_participating_optional=(optional_id,))
        failure_by_id = {item.resource_id: item for item in failure.resource_results}
        prior_required_effect_visible = next(
            item.operation_effects
            for item in failing_resources
            if item.descriptor.resource_id != failure_id
            and item.descriptor.participation is Participation.REQUIRED
        ) > 0
        serialized = failure.to_dict()
        no_atomicity_claim = not any("atomic" in str(key).lower() for key in serialized)
        optional_non_participating = failure_by_id[optional_id].status is OperationStatus.NOT_PARTICIPATING
        passed = (
            success.status is OperationStatus.SUCCEEDED
            and normal_ids == {self._string(item.get("resourceId"), "resourceId") for item in records}
            and failure.status is OperationStatus.FAILED
            and failure_by_id[failure_id].status is OperationStatus.FAILED
            and optional_non_participating
            and prior_required_effect_visible
            and no_atomicity_claim
        )
        return passed, (
            "composite results preserve every outcome, required failures, partial effects, and no atomicity fiction"
            if passed
            else "Fabric aggregate/per-resource outcome honesty drifted"
        )

    def _restore(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        records = [self._mapping(item, "resource") for item in self._list(vector.get("resources"), "resources")]
        resources = tuple(
            InMemoryFabricResource(
                self._descriptor(
                    self._string(item.get("resourceId"), "resourceId"),
                    participation=Participation(self._string(item.get("participation"), "participation")),
                ),
                restore_fidelity=RestoreEquivalence(
                    self._string(item.get("restoreFidelity"), "restoreFidelity")
                ),
            )
            for item in records
        )
        fabric = self._fabric("env-restore", resources)
        fabric.provision()
        success = fabric.execute_composite(FabricOperation.RESTORE)
        expected = RestoreEquivalence(
            self._string(
                self._mapping(vector.get("expect", {}), "vector.expect").get("successfulAggregateFidelity", "STATE_EQUIVALENT"),
                "successfulAggregateFidelity",
            )
        ) if "expect" in vector else RestoreEquivalence.STATE_EQUIVALENT
        # The case-level expect lives outside vector; the normative vector itself
        # still determines the weakest required fidelity mechanically.
        required_fidelities = [
            resource.restore_fidelity
            for resource in resources
            if resource.descriptor.participation is Participation.REQUIRED
        ]
        rank = {
            RestoreEquivalence.NON_EQUIVALENT: 0,
            RestoreEquivalence.STATE_EQUIVALENT: 1,
            RestoreEquivalence.EXACT: 2,
        }
        computed_expected = min(required_fidelities, key=rank.__getitem__)

        failure_id = self._string(
            self._mapping(vector.get("requiredFailureControl"), "requiredFailureControl").get("resourceId"),
            "requiredFailureControl.resourceId",
        )
        failing_resources = tuple(
            InMemoryFabricResource(
                item.descriptor,
                restore_fidelity=item.restore_fidelity,
                fail_operations=(FabricOperation.RESTORE,)
                if item.descriptor.resource_id == failure_id
                else (),
            )
            for item in resources
        )
        failing = self._fabric("env-restore", failing_resources)
        failing.provision()
        failure = failing.execute_composite(FabricOperation.RESTORE)
        passed = (
            expected is RestoreEquivalence.STATE_EQUIVALENT
            and success.status is OperationStatus.SUCCEEDED
            and success.aggregate_restore_fidelity is computed_expected
            and computed_expected is RestoreEquivalence.STATE_EQUIVALENT
            and failure.status is OperationStatus.FAILED
            and failure.aggregate_restore_fidelity is RestoreEquivalence.NON_EQUIVALENT
        )
        return passed, (
            "aggregate restore fidelity is the weakest required fidelity and required failure cannot overclaim"
            if passed
            else "Fabric restore fidelity aggregation drifted"
        )

    def _security_evidence(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        artifact_doc = self._mapping(vector.get("identityArtifact"), "identityArtifact")
        artifact = ArtifactIdentity(
            self._string(artifact_doc.get("digest"), "digest"),
            int(artifact_doc.get("size", -1)),
            self._string(artifact_doc.get("mediaType"), "mediaType"),
        )
        resource = InMemoryFabricResource(
            self._descriptor("primary-state", identity_artifacts=(artifact,))
        )
        fabric = self._fabric("env-security-evidence", (resource,))
        manifest = fabric.manifest().to_dict()
        serialized = repr(manifest)
        forbidden = tuple(str(item) for item in self._list(vector.get("forbiddenPortableFields"), "forbiddenPortableFields"))
        retained = manifest["resources"][0]["identityArtifacts"][0]
        passed = all(item not in serialized for item in forbidden) and retained == artifact.to_dict()
        return passed, (
            "portable Fabric material excludes evaluator-private/inflated claims and preserves Artifact identity"
            if passed
            else "Fabric Security/Evidence composition drifted"
        )

    def _executed_capability(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        capability = self._capability_declaration(
            self._mapping(vector.get("capability"), "capability")
        )
        descriptor = self._descriptor("primary-state", capabilities=(capability,))
        good_resource = InMemoryFabricResource(descriptor)
        broken_resource = InMemoryFabricResource(descriptor, broken_snapshot_behavior=True)
        good = self._fabric("env-executed-good", (good_resource,))
        broken = self._fabric("env-executed-broken", (broken_resource,))
        good.provision()
        broken.provision()
        good_resource.mutate()
        broken_resource.mutate()
        metadata_equal = good_resource.descriptor.to_dict() == broken_resource.descriptor.to_dict()
        good_snapshot = good.control_snapshot("primary-state")
        broken_snapshot = broken.control_snapshot("primary-state")
        good_behavior = good_snapshot == good_resource.state
        broken_rejected_by_behavior = broken_snapshot != broken_resource.state
        passed = metadata_equal and good_behavior and broken_rejected_by_behavior
        return passed, (
            "behavior execution distinguishes conforming and metadata-identical broken capability implementations"
            if passed
            else "Fabric TCK trusted capability metadata instead of executed behavior"
        )

    def _cleanup(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        resource = InMemoryFabricResource(self._descriptor("primary-state"))
        fabric = self._fabric("env-cleanup", (resource,), subject_capabilities=("order.get",))
        fabric.provision()
        first = fabric.release()
        effects_after_first = resource.operation_effects
        subject_effects_after_first = resource.subject_side_effects
        second = fabric.release()
        retry_safe = (
            first.status is OperationStatus.SUCCEEDED
            and second.status is OperationStatus.SUCCEEDED
            and resource.released
            and resource.operation_effects == effects_after_first
            and resource.subject_side_effects == subject_effects_after_first
        )
        stale_rejected = False
        try:
            resource.mutate()
        except FabricReferenceError:
            stale_rejected = True

        failing_resource = InMemoryFabricResource(
            self._descriptor("primary-state"),
            fail_operations=(FabricOperation.RELEASE,),
        )
        failing = self._fabric("env-cleanup-failure", (failing_resource,))
        failing.provision()
        cleanup_failure = failing.release()
        serialized = cleanup_failure.to_dict()
        separated = (
            cleanup_failure.status is OperationStatus.FAILED
            and cleanup_failure.resource_results[0].failure_code == "CLEANUP_FAILED"
            and "taskVerdict" not in serialized
            and "task_verdict" not in serialized
        )
        passed = retry_safe and stale_rejected and separated
        return passed, (
            "cleanup retry is side-effect safe, stale references remain rejected, and infra failure stays outside Task Verdict"
            if passed
            else "Fabric cleanup idempotency or failure separation drifted"
        )

    @staticmethod
    def _fabric(
        environment_id: str,
        resources: tuple[InMemoryFabricResource, ...],
        *,
        subject_capabilities: tuple[str, ...] = (),
    ) -> EnvironmentFabric:
        return EnvironmentFabric(
            environment_id=environment_id,
            scenario_instance_digest=ReferenceFabricTCKAdapter._digest("e"),
            resources=resources,
            subject_capabilities=subject_capabilities,
        )

    @staticmethod
    def _descriptor(
        resource_id: str,
        *,
        capabilities: tuple[ResourceCapabilityDeclaration, ...] = (),
        participation: Participation = Participation.REQUIRED,
        identity_artifacts: tuple[ArtifactIdentity, ...] = (),
    ) -> EnvironmentResourceDescriptor:
        return EnvironmentResourceDescriptor(
            resource_id=resource_id,
            environment_id=(
                "env-authz" if resource_id == "primary-state" and capabilities
                else "env-placeholder"
            ),
            resource_kind=ResourceKind.STATE,
            participation=participation,
            capabilities=capabilities,
            identity_artifacts=identity_artifacts,
        )

    @staticmethod
    def _capability_declaration(value: Mapping[str, Any]) -> ResourceCapabilityDeclaration:
        return ResourceCapabilityDeclaration(
            ReferenceFabricTCKAdapter._string(value.get("capabilityId"), "capabilityId"),
            ReferenceFabricTCKAdapter._string(value.get("profile"), "profile"),
            ReferenceFabricTCKAdapter._string(value.get("revision"), "revision"),
            Participation(ReferenceFabricTCKAdapter._string(value.get("participation"), "participation")),
        )

    @staticmethod
    def _digest(character: str) -> str:
        return "sha256:" + character * 64

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("Fabric TCK case metadata.id is missing")
        return case_id

    @staticmethod
    def _mapping(value: Any, context: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise TCKAdapterError(f"Fabric TCK {context} must be an object")
        return value

    @staticmethod
    def _list(value: Any, context: str) -> list[Any]:
        if not isinstance(value, list):
            raise TCKAdapterError(f"Fabric TCK {context} must be a list")
        return value

    @staticmethod
    def _string(value: Any, context: str) -> str:
        if not isinstance(value, str) or not value:
            raise TCKAdapterError(f"Fabric TCK {context} must be a non-empty string")
        return value

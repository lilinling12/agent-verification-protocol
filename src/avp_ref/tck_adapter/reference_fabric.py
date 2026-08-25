"""Execution adapter for the Environment Fabric v0.1 candidate TCK profile.

The vectors remain authoritative. This adapter exercises packaged reference
behavior and includes behavior-negative controls with metadata identical to
conforming resources, so declarations alone can never satisfy conformance.
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
        records = [self._mapping(item, "resource") for item in self._list(vector.get("resources"), "resources")]
        resources = tuple(
            InMemoryFabricResource(
                self._descriptor(
                    environment_id,
                    self._string(item.get("resourceId"), "resourceId"),
                    kind=ResourceKind(self._string(item.get("resourceKind"), "resourceKind")),
                    participation=Participation(self._string(item.get("participation"), "participation")),
                )
            )
            for item in records
        )
        fabric = EnvironmentFabric(
            environment_id=environment_id,
            scenario_instance_digest=scenario_digest,
            resources=resources,
        )
        manifest = fabric.manifest().to_dict()
        resource_docs = manifest["resources"]
        ids = [item["resourceId"] for item in resource_docs]
        kinds = {item.value for item in ResourceKind}

        try:
            EnvironmentFabric(
                environment_id=environment_id,
                scenario_instance_digest=scenario_digest,
                resources=(resources[0], resources[0]),
            )
            duplicate_rejected = False
        except FabricCompatibilityError:
            duplicate_rejected = True

        foreign = InMemoryFabricResource(
            self._descriptor("foreign-environment", "foreign-resource")
        )
        try:
            EnvironmentFabric(
                environment_id=environment_id,
                scenario_instance_digest=scenario_digest,
                resources=(foreign,),
            )
            foreign_rejected = False
        except FabricCompatibilityError:
            foreign_rejected = True

        passed = (
            manifest["environmentId"] == environment_id
            and manifest["scenarioInstanceDigest"] == scenario_digest
            and len(ids) == len(set(ids))
            and all(item["resourceKind"] in kinds for item in resource_docs)
            and all(not str(item).startswith("sha256:") for item in ids)
            and duplicate_rejected
            and foreign_rejected
        )
        return passed, (
            "manifest binds Scenario/Environment ownership with unique portable resources"
            if passed
            else "Fabric manifest ownership, uniqueness, or classification drifted"
        )

    def _capability(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        environment_id = "env-capability"
        required = self._capability_declaration(
            self._mapping(vector.get("requiredCapability"), "requiredCapability")
        )
        optional = self._capability_declaration(
            self._mapping(vector.get("optionalCapability"), "optionalCapability")
        )

        good_resource = InMemoryFabricResource(
            self._descriptor(environment_id, "primary-state", capabilities=(required,))
        )
        good = self._fabric(
            environment_id,
            (good_resource,),
            requirements=(CapabilityRequirement("primary-state", required),),
        )
        good.provision()
        good_ok = good.ready and good_resource.provision_side_effects == 1

        missing_resource = InMemoryFabricResource(
            self._descriptor(environment_id, "primary-state")
        )
        missing = self._fabric(
            environment_id,
            (missing_resource,),
            requirements=(CapabilityRequirement("primary-state", required),),
        )
        try:
            missing.provision()
            missing_rejected_before_effect = False
        except FabricCompatibilityError:
            missing_rejected_before_effect = missing_resource.provision_side_effects == 0

        mismatched = ResourceCapabilityDeclaration(
            required.capability_id,
            required.profile,
            required.revision + "-different",
            required.participation,
        )
        mismatch_resource = InMemoryFabricResource(
            self._descriptor(environment_id, "primary-state", capabilities=(mismatched,))
        )
        mismatch = self._fabric(
            environment_id,
            (mismatch_resource,),
            requirements=(CapabilityRequirement("primary-state", required),),
        )
        try:
            mismatch.provision()
            mismatch_rejected_before_effect = False
        except FabricCompatibilityError:
            mismatch_rejected_before_effect = mismatch_resource.provision_side_effects == 0

        optional_resource = InMemoryFabricResource(
            self._descriptor(environment_id, "primary-state")
        )
        optional_fabric = self._fabric(
            environment_id,
            (optional_resource,),
            requirements=(CapabilityRequirement("primary-state", optional),),
        )
        optional_fabric.provision()
        optional_ok = optional_fabric.ready

        passed = good_ok and missing_rejected_before_effect and mismatch_rejected_before_effect and optional_ok
        return passed, (
            "required capability compatibility is validated before provision side effects"
            if passed
            else "Fabric capability honesty or requiredness drifted"
        )

    def _authorization(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        environment_id = "env-authz"
        capability = self._capability_declaration(
            self._mapping(vector.get("resourceCapability"), "resourceCapability")
        )
        subject_caps = tuple(str(item) for item in self._list(vector.get("subjectCapabilities"), "subjectCapabilities"))
        privileged = self._string(vector.get("privilegedOperation"), "privilegedOperation")
        resource = InMemoryFabricResource(
            self._descriptor(environment_id, "primary-state", capabilities=(capability,))
        )
        fabric = self._fabric(
            environment_id,
            (resource,),
            requirements=(CapabilityRequirement("primary-state", capability),),
            subject_capabilities=subject_caps,
        )
        fabric.provision()
        control_ok = fabric.control_snapshot("primary-state") == resource.state
        try:
            fabric.subject_call(privileged)
            subject_denied = False
        except SubjectAuthorizationError:
            subject_denied = True
        declared_subject_ok = all(fabric.subject_call(item) == item for item in subject_caps)
        passed = control_ok and subject_denied and declared_subject_ok
        return passed, (
            "Resource Capability support remains separate from Subject authorization"
            if passed
            else "Resource support widened or corrupted Subject authority"
        )

    def _composite(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        environment_id = "env-composite"
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

        def build(*, fail: bool) -> tuple[InMemoryFabricResource, ...]:
            return tuple(
                InMemoryFabricResource(
                    self._descriptor(
                        environment_id,
                        self._string(item.get("resourceId"), "resourceId"),
                        participation=Participation(self._string(item.get("participation"), "participation")),
                    ),
                    fail_operations=(operation,) if fail and item.get("resourceId") == failure_id else (),
                )
                for item in records
            )

        normal_resources = build(fail=False)
        normal = self._fabric(environment_id, normal_resources)
        normal.provision()
        success = normal.execute_composite(operation, non_participating_optional=(optional_id,))

        failing_resources = build(fail=True)
        failing = self._fabric(environment_id, failing_resources)
        failing.provision()
        failure = failing.execute_composite(operation, non_participating_optional=(optional_id,))
        by_id = {item.resource_id: item for item in failure.resource_results}
        prior_required_effect = any(
            item.operation_effects > 0
            for item in failing_resources
            if item.descriptor.resource_id != failure_id
            and item.descriptor.participation is Participation.REQUIRED
        )
        no_atomicity_claim = not any("atomic" in str(key).lower() for key in failure.to_dict())
        expected_ids = {self._string(item.get("resourceId"), "resourceId") for item in records}
        passed = (
            success.status is OperationStatus.SUCCEEDED
            and {item.resource_id for item in success.resource_results} == expected_ids
            and failure.status is OperationStatus.FAILED
            and by_id[failure_id].status is OperationStatus.FAILED
            and by_id[optional_id].status is OperationStatus.NOT_PARTICIPATING
            and prior_required_effect
            and no_atomicity_claim
        )
        return passed, (
            "composite outcomes preserve required failure, optional non-participation and partial effects"
            if passed
            else "Fabric aggregate/per-resource outcome honesty drifted"
        )

    def _restore(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        environment_id = "env-restore"
        records = [self._mapping(item, "resource") for item in self._list(vector.get("resources"), "resources")]
        failure_id = self._string(
            self._mapping(vector.get("requiredFailureControl"), "requiredFailureControl").get("resourceId"),
            "requiredFailureControl.resourceId",
        )

        def build(*, fail: bool) -> tuple[InMemoryFabricResource, ...]:
            return tuple(
                InMemoryFabricResource(
                    self._descriptor(
                        environment_id,
                        self._string(item.get("resourceId"), "resourceId"),
                        participation=Participation(self._string(item.get("participation"), "participation")),
                    ),
                    restore_fidelity=RestoreEquivalence(
                        self._string(item.get("restoreFidelity"), "restoreFidelity")
                    ),
                    fail_operations=(FabricOperation.RESTORE,)
                    if fail and item.get("resourceId") == failure_id
                    else (),
                )
                for item in records
            )

        good_resources = build(fail=False)
        good = self._fabric(environment_id, good_resources)
        good.provision()
        success = good.execute_composite(FabricOperation.RESTORE)
        required_fidelity = [
            item.restore_fidelity
            for item in good_resources
            if item.descriptor.participation is Participation.REQUIRED
        ]
        rank = {
            RestoreEquivalence.NON_EQUIVALENT: 0,
            RestoreEquivalence.STATE_EQUIVALENT: 1,
            RestoreEquivalence.EXACT: 2,
        }
        weakest_required = min(required_fidelity, key=rank.__getitem__)

        failing_resources = build(fail=True)
        failing = self._fabric(environment_id, failing_resources)
        failing.provision()
        failure = failing.execute_composite(FabricOperation.RESTORE)
        optional_fidelity = [
            item.restore_fidelity
            for item in good_resources
            if item.descriptor.participation is Participation.OPTIONAL
        ]
        passed = (
            success.status is OperationStatus.SUCCEEDED
            and success.aggregate_restore_fidelity is weakest_required
            and weakest_required is RestoreEquivalence.STATE_EQUIVALENT
            and optional_fidelity == [RestoreEquivalence.NON_EQUIVALENT]
            and failure.status is OperationStatus.FAILED
            and failure.aggregate_restore_fidelity is RestoreEquivalence.NON_EQUIVALENT
        )
        return passed, (
            "aggregate restore fidelity is bounded by required resources and required failure cannot overclaim"
            if passed
            else "Fabric restore fidelity aggregation drifted"
        )

    def _security_evidence(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        environment_id = "env-security-evidence"
        artifact_doc = self._mapping(vector.get("identityArtifact"), "identityArtifact")
        artifact = ArtifactIdentity(
            self._string(artifact_doc.get("digest"), "digest"),
            int(artifact_doc.get("size", -1)),
            self._string(artifact_doc.get("mediaType"), "mediaType"),
        )
        resource = InMemoryFabricResource(
            self._descriptor(environment_id, "primary-state", identity_artifacts=(artifact,))
        )
        manifest = self._fabric(environment_id, (resource,)).manifest().to_dict()
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
        environment_id = "env-executed"
        capability = self._capability_declaration(
            self._mapping(vector.get("capability"), "capability")
        )
        descriptor = self._descriptor(environment_id, "primary-state", capabilities=(capability,))
        good_resource = InMemoryFabricResource(descriptor)
        broken_resource = InMemoryFabricResource(descriptor, broken_snapshot_behavior=True)
        good = self._fabric(environment_id, (good_resource,))
        broken = self._fabric(environment_id, (broken_resource,))
        good.provision()
        broken.provision()
        good_resource.mutate()
        broken_resource.mutate()
        metadata_equal = good_resource.descriptor.to_dict() == broken_resource.descriptor.to_dict()
        good_behavior = good.control_snapshot("primary-state") == good_resource.state
        broken_behavior_detected = broken.control_snapshot("primary-state") != broken_resource.state
        passed = metadata_equal and good_behavior and broken_behavior_detected
        return passed, (
            "executed behavior distinguishes metadata-identical conforming and broken capability implementations"
            if passed
            else "Fabric conformance trusted declaration metadata instead of behavior"
        )

    def _cleanup(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        environment_id = "env-cleanup"
        resource = InMemoryFabricResource(self._descriptor(environment_id, "primary-state"))
        fabric = self._fabric(environment_id, (resource,), subject_capabilities=("order.get",))
        fabric.provision()
        first = fabric.release()
        first_effects = resource.operation_effects
        first_subject_effects = resource.subject_side_effects
        second = fabric.release()
        retry_safe = (
            first.status is OperationStatus.SUCCEEDED
            and second.status is OperationStatus.SUCCEEDED
            and resource.released
            and resource.operation_effects == first_effects
            and resource.subject_side_effects == first_subject_effects
        )
        try:
            resource.mutate()
            stale_rejected = False
        except FabricReferenceError:
            stale_rejected = True

        failing_resource = InMemoryFabricResource(
            self._descriptor("env-cleanup-failure", "primary-state"),
            fail_operations=(FabricOperation.RELEASE,),
        )
        failing = self._fabric("env-cleanup-failure", (failing_resource,))
        failing.provision()
        cleanup_failure = failing.release()
        serialized = cleanup_failure.to_dict()
        failure_separated = (
            cleanup_failure.status is OperationStatus.FAILED
            and cleanup_failure.resource_results[0].failure_code == "CLEANUP_FAILED"
            and "taskVerdict" not in serialized
            and "task_verdict" not in serialized
        )
        passed = retry_safe and stale_rejected and failure_separated
        return passed, (
            "cleanup retry is safe, stale references fail closed, and cleanup failure stays outside Task Verdict"
            if passed
            else "Fabric cleanup or failure separation drifted"
        )

    @staticmethod
    def _fabric(
        environment_id: str,
        resources: tuple[InMemoryFabricResource, ...],
        *,
        requirements: tuple[CapabilityRequirement, ...] = (),
        subject_capabilities: tuple[str, ...] = (),
    ) -> EnvironmentFabric:
        return EnvironmentFabric(
            environment_id=environment_id,
            scenario_instance_digest=ReferenceFabricTCKAdapter._digest("e"),
            resources=resources,
            capability_requirements=requirements,
            subject_capabilities=subject_capabilities,
        )

    @staticmethod
    def _descriptor(
        environment_id: str,
        resource_id: str,
        *,
        kind: ResourceKind = ResourceKind.STATE,
        capabilities: tuple[ResourceCapabilityDeclaration, ...] = (),
        participation: Participation = Participation.REQUIRED,
        identity_artifacts: tuple[ArtifactIdentity, ...] = (),
    ) -> EnvironmentResourceDescriptor:
        return EnvironmentResourceDescriptor(
            resource_id=resource_id,
            environment_id=environment_id,
            resource_kind=kind,
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

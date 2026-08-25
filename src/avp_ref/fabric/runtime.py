"""Backend-neutral reference implementation of Environment Fabric composition.

The implementation deliberately models only semantics already defined by the
Fabric candidate specification.  Database, browser, network, time, compute and
microVM mechanisms belong to later profiles/adapters and are not inferred here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from avp_ref.environment import RestoreEquivalence

from .models import (
    EnvironmentFabricManifest,
    EnvironmentResourceDescriptor,
    FabricOperation,
    FabricOperationResult,
    OperationStatus,
    Participation,
    ResourceCapabilityDeclaration,
    ResourceOperationResult,
)


class FabricError(RuntimeError):
    """Base error for reference Fabric contract failures."""


class FabricCompatibilityError(FabricError):
    """Raised when materialized required resources/capabilities are incompatible."""


class FabricReferenceError(FabricError):
    """Raised when a foreign, stale, or unknown Fabric resource reference is used."""


class SubjectAuthorizationError(FabricError):
    """Raised when Subject authority is confused with privileged Fabric support."""


@dataclass(frozen=True, slots=True)
class CapabilityRequirement:
    resource_id: str
    declaration: ResourceCapabilityDeclaration


class InMemoryFabricResource:
    """Small deterministic resource used by the reference composition runtime.

    Fault controls are constructor-only implementation test controls.  They are
    not serialized and are intentionally absent from the protocol schemas.
    """

    def __init__(
        self,
        descriptor: EnvironmentResourceDescriptor,
        *,
        restore_fidelity: RestoreEquivalence = RestoreEquivalence.EXACT,
        fail_operations: Iterable[FabricOperation] = (),
        broken_snapshot_behavior: bool = False,
    ) -> None:
        self.descriptor = descriptor
        self.restore_fidelity = restore_fidelity
        self._fail_operations = frozenset(fail_operations)
        self._broken_snapshot_behavior = broken_snapshot_behavior
        self._released = False
        self._provisioned = False
        self._state = 0
        self.provision_side_effects = 0
        self.subject_side_effects = 0
        self.operation_effects = 0

    @property
    def released(self) -> bool:
        return self._released

    @property
    def state(self) -> int:
        return self._state

    def provision(self) -> None:
        self._assert_live_reference()
        if not self._provisioned:
            self._provisioned = True
            self.provision_side_effects += 1

    def mutate(self) -> None:
        self._assert_usable()
        self._state += 1
        self.subject_side_effects += 1

    def snapshot(self) -> int:
        self._assert_usable()
        if self._broken_snapshot_behavior:
            return self._state + 1
        return self._state

    def reset(self) -> ResourceOperationResult:
        return self._operation(FabricOperation.RESET, new_state=0)

    def restore(self) -> ResourceOperationResult:
        result = self._operation(FabricOperation.RESTORE)
        if result.status is OperationStatus.FAILED:
            return ResourceOperationResult(
                self.descriptor.resource_id,
                self.descriptor.participation,
                OperationStatus.FAILED,
                RestoreEquivalence.NON_EQUIVALENT,
                result.failure_code,
            )
        return ResourceOperationResult(
            self.descriptor.resource_id,
            self.descriptor.participation,
            OperationStatus.SUCCEEDED,
            self.restore_fidelity,
        )

    def release(self) -> ResourceOperationResult:
        if self._released:
            return ResourceOperationResult(
                self.descriptor.resource_id,
                self.descriptor.participation,
                OperationStatus.SUCCEEDED,
            )
        if FabricOperation.RELEASE in self._fail_operations:
            return ResourceOperationResult(
                self.descriptor.resource_id,
                self.descriptor.participation,
                OperationStatus.FAILED,
                failure_code="CLEANUP_FAILED",
            )
        self.operation_effects += 1
        self._released = True
        self._provisioned = False
        return ResourceOperationResult(
            self.descriptor.resource_id,
            self.descriptor.participation,
            OperationStatus.SUCCEEDED,
        )

    def execute(self, operation: FabricOperation) -> ResourceOperationResult:
        if operation is FabricOperation.RESET:
            return self.reset()
        if operation is FabricOperation.RESTORE:
            return self.restore()
        if operation is FabricOperation.SNAPSHOT:
            self._assert_usable()
            if operation in self._fail_operations:
                return ResourceOperationResult(
                    self.descriptor.resource_id,
                    self.descriptor.participation,
                    OperationStatus.FAILED,
                    failure_code="OPERATION_FAILED",
                )
            self.operation_effects += 1
            self.snapshot()
            return ResourceOperationResult(
                self.descriptor.resource_id,
                self.descriptor.participation,
                OperationStatus.SUCCEEDED,
            )
        if operation is FabricOperation.RELEASE:
            return self.release()
        raise FabricError(f"unsupported Fabric operation: {operation}")

    def _operation(
        self,
        operation: FabricOperation,
        *,
        new_state: int | None = None,
    ) -> ResourceOperationResult:
        self._assert_usable()
        if operation in self._fail_operations:
            return ResourceOperationResult(
                self.descriptor.resource_id,
                self.descriptor.participation,
                OperationStatus.FAILED,
                failure_code="OPERATION_FAILED",
            )
        self.operation_effects += 1
        if new_state is not None:
            self._state = new_state
        return ResourceOperationResult(
            self.descriptor.resource_id,
            self.descriptor.participation,
            OperationStatus.SUCCEEDED,
        )

    def _assert_live_reference(self) -> None:
        if self._released:
            raise FabricReferenceError(
                f"resource reference is released: {self.descriptor.resource_id}"
            )

    def _assert_usable(self) -> None:
        self._assert_live_reference()
        if not self._provisioned:
            raise FabricReferenceError(
                f"resource is not provisioned: {self.descriptor.resource_id}"
            )


class EnvironmentFabric:
    """Reference coordinator for the portable base Fabric semantics."""

    _FIDELITY_RANK = {
        RestoreEquivalence.NON_EQUIVALENT: 0,
        RestoreEquivalence.STATE_EQUIVALENT: 1,
        RestoreEquivalence.EXACT: 2,
    }

    def __init__(
        self,
        *,
        environment_id: str,
        scenario_instance_digest: str,
        resources: Iterable[InMemoryFabricResource],
        capability_requirements: Iterable[CapabilityRequirement] = (),
        subject_capabilities: Iterable[str] = (),
    ) -> None:
        self.environment_id = environment_id
        self.scenario_instance_digest = scenario_instance_digest
        self._resources = tuple(resources)
        self._requirements = tuple(capability_requirements)
        self._subject_capabilities = frozenset(subject_capabilities)
        self._ready = False
        self._released = False
        self._operation_sequence = 0
        self._validate_composition_identity()

    @property
    def resources(self) -> tuple[InMemoryFabricResource, ...]:
        return self._resources

    @property
    def ready(self) -> bool:
        return self._ready and not self._released

    def manifest(self) -> EnvironmentFabricManifest:
        self._assert_live()
        return EnvironmentFabricManifest(
            self.environment_id,
            self.scenario_instance_digest,
            tuple(item.descriptor for item in self._resources),
        )

    def provision(self) -> None:
        self._assert_live()
        self._validate_required_capabilities()
        # Compatibility is deliberately checked before any resource provision
        # side effect, which is the observable AVP-FABRIC-003 guarantee.
        for resource in self._resources:
            if resource.descriptor.participation is Participation.REQUIRED:
                resource.provision()
            else:
                resource.provision()
        self._ready = True

    def subject_call(self, operation: str) -> str:
        self._assert_ready()
        if operation not in self._subject_capabilities:
            raise SubjectAuthorizationError(
                f"Subject capability is not materialized: {operation}"
            )
        return operation

    def control_snapshot(self, resource_id: str) -> int:
        self._assert_ready()
        return self._resource(resource_id).snapshot()

    def execute_composite(
        self,
        operation: FabricOperation,
        *,
        non_participating_optional: Iterable[str] = (),
    ) -> FabricOperationResult:
        self._assert_ready()
        omitted = frozenset(non_participating_optional)
        results: list[ResourceOperationResult] = []
        for resource in self._resources:
            descriptor = resource.descriptor
            if descriptor.resource_id in omitted:
                if descriptor.participation is Participation.REQUIRED:
                    raise FabricCompatibilityError(
                        f"required resource cannot be non-participating: {descriptor.resource_id}"
                    )
                results.append(
                    ResourceOperationResult(
                        descriptor.resource_id,
                        descriptor.participation,
                        OperationStatus.NOT_PARTICIPATING,
                    )
                )
                continue
            results.append(resource.execute(operation))

        required_failed = any(
            result.participation is Participation.REQUIRED
            and result.status is not OperationStatus.SUCCEEDED
            for result in results
        )
        status = OperationStatus.FAILED if required_failed else OperationStatus.SUCCEEDED
        fidelity = None
        if operation is FabricOperation.RESTORE:
            if required_failed:
                fidelity = RestoreEquivalence.NON_EQUIVALENT
            else:
                required_fidelities = [
                    result.restore_fidelity
                    for result in results
                    if result.participation is Participation.REQUIRED
                    and result.status is OperationStatus.SUCCEEDED
                ]
                if not required_fidelities or any(item is None for item in required_fidelities):
                    raise FabricError("required restore result is missing fidelity")
                fidelity = min(
                    (item for item in required_fidelities if item is not None),
                    key=self._FIDELITY_RANK.__getitem__,
                )

        self._operation_sequence += 1
        return FabricOperationResult(
            operation_id=f"fabric-op-{self._operation_sequence}",
            operation=operation,
            environment_id=self.environment_id,
            status=status,
            resource_results=tuple(results),
            aggregate_restore_fidelity=fidelity,
        )

    def release(self) -> FabricOperationResult:
        if self._released:
            self._operation_sequence += 1
            results = tuple(
                ResourceOperationResult(
                    item.descriptor.resource_id,
                    item.descriptor.participation,
                    OperationStatus.SUCCEEDED,
                )
                for item in self._resources
            )
            return FabricOperationResult(
                f"fabric-op-{self._operation_sequence}",
                FabricOperation.RELEASE,
                self.environment_id,
                OperationStatus.SUCCEEDED,
                results,
            )

        results = tuple(item.release() for item in self._resources)
        required_failed = any(
            result.participation is Participation.REQUIRED
            and result.status is OperationStatus.FAILED
            for result in results
        )
        self._operation_sequence += 1
        result = FabricOperationResult(
            f"fabric-op-{self._operation_sequence}",
            FabricOperation.RELEASE,
            self.environment_id,
            OperationStatus.FAILED if required_failed else OperationStatus.SUCCEEDED,
            results,
        )
        if not required_failed:
            self._ready = False
            self._released = True
        return result

    def _validate_composition_identity(self) -> None:
        if not self.environment_id or not self._resources:
            raise FabricCompatibilityError("Fabric requires environment identity and resources")
        resource_ids: set[str] = set()
        for resource in self._resources:
            descriptor = resource.descriptor
            if descriptor.environment_id != self.environment_id:
                raise FabricCompatibilityError(
                    f"foreign resource {descriptor.resource_id} belongs to {descriptor.environment_id}"
                )
            if descriptor.resource_id in resource_ids:
                raise FabricCompatibilityError(
                    f"duplicate resource id: {descriptor.resource_id}"
                )
            resource_ids.add(descriptor.resource_id)

    def _validate_required_capabilities(self) -> None:
        by_id = {item.descriptor.resource_id: item for item in self._resources}
        for requirement in self._requirements:
            required = requirement.declaration
            resource = by_id.get(requirement.resource_id)
            if resource is None:
                if required.participation is Participation.REQUIRED:
                    raise FabricCompatibilityError(
                        f"required resource missing: {requirement.resource_id}"
                    )
                continue
            actual = {item.semantic_identity for item in resource.descriptor.capabilities}
            if required.semantic_identity not in actual and required.participation is Participation.REQUIRED:
                raise FabricCompatibilityError(
                    "required capability missing or incompatible: "
                    f"{requirement.resource_id}:{required.semantic_identity}"
                )

    def _resource(self, resource_id: str) -> InMemoryFabricResource:
        for resource in self._resources:
            if resource.descriptor.resource_id == resource_id:
                return resource
        raise FabricReferenceError(f"unknown Fabric resource: {resource_id}")

    def _assert_live(self) -> None:
        if self._released:
            raise FabricReferenceError("Fabric reference is released")

    def _assert_ready(self) -> None:
        self._assert_live()
        if not self._ready:
            raise FabricReferenceError("Fabric is not ready")

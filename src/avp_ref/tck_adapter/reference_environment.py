"""Reference adapter for the AVP Environment v0.1 conformance profile."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from avp_ref.canonical import digest
from avp_ref.environment import (
    EnvironmentHandle,
    FaultSpec,
    InMemoryCommerceAdapter,
    RestoreEquivalence,
    SnapshotNotFoundError,
    ToolExecutionError,
    ToolPermissionDenied,
    ToolRequest,
    UnknownEnvironmentHandle,
)
from avp_ref.reference import reference_scenario

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


class ReferenceEnvironmentTCKAdapter:
    """Execute language-neutral Environment vectors against the reference adapter."""

    _LIFECYCLE = "AVP-TCK-ENVIRONMENT-LIFECYCLE-001"
    _RESET_TIME = "AVP-TCK-ENVIRONMENT-RESET-TIME-001"
    _OBSERVATION = "AVP-TCK-ENVIRONMENT-OBSERVATION-001"
    _PROJECTION = "AVP-TCK-ENVIRONMENT-PROJECTION-001"
    _SNAPSHOT_RESTORE = "AVP-TCK-ENVIRONMENT-SNAPSHOT-RESTORE-001"
    _DIFF = "AVP-TCK-ENVIRONMENT-DIFF-001"
    _FAULT = "AVP-TCK-ENVIRONMENT-FAULT-001"

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return frozenset(
            {
                self._LIFECYCLE,
                self._RESET_TIME,
                self._OBSERVATION,
                self._PROJECTION,
                self._SNAPSHOT_RESTORE,
                self._DIFF,
                self._FAULT,
            }
        )

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        evaluator = {
            self._LIFECYCLE: self._lifecycle,
            self._RESET_TIME: self._reset_time,
            self._OBSERVATION: self._observation,
            self._PROJECTION: self._projection,
            self._SNAPSHOT_RESTORE: self._snapshot_restore,
            self._DIFF: self._diff,
            self._FAULT: self._fault,
        }.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(f"unsupported reference Environment TCK case: {case_id}")
        passed, detail = evaluator(vector)
        return TCKCaseResult(
            case_id,
            TCKStatus.PASS if passed else TCKStatus.FAIL,
            detail,
        )

    @staticmethod
    def _lifecycle(vector: Mapping[str, Any]) -> tuple[bool, str]:
        adapter = InMemoryCommerceAdapter()
        scenario = reference_scenario()
        handle = adapter.provision(scenario)
        bound = handle.scenario_digest == scenario.instance_digest

        forged = EnvironmentHandle(
            handle_id=handle.handle_id,
            adapter_name=handle.adapter_name,
            adapter_version=handle.adapter_version,
            scenario_digest="sha256:" + "0" * 64,
        )
        try:
            adapter.digest(forged)
            scenario_mismatch_rejected = False
        except UnknownEnvironmentHandle:
            scenario_mismatch_rejected = True

        adapter.release(handle)
        try:
            adapter.digest(handle)
            released_rejected = False
        except UnknownEnvironmentHandle:
            released_rejected = True

        passed = bound and scenario_mismatch_rejected and released_rejected
        return passed, (
            "environment identity remains Scenario-bound and released/stale handles fail closed"
            if passed
            else "environment lifecycle or Scenario binding violated the v0.1 contract"
        )

    @staticmethod
    def _reset_time(vector: Mapping[str, Any]) -> tuple[bool, str]:
        adapter, handle = ReferenceEnvironmentTCKAdapter._provision()
        initial_digest = adapter.digest(handle)
        initial_time = adapter.logical_time(handle)
        mutation = ReferenceEnvironmentTCKAdapter._mapping(vector.get("mutation"), "mutation")
        adapter.execute(handle, ReferenceEnvironmentTCKAdapter._tool_request(mutation))
        mutated_digest = adapter.digest(handle)
        mutated_time = adapter.logical_time(handle)

        result = adapter.reset(handle)
        reset_time = adapter.logical_time(handle)
        reset_digest = adapter.digest(handle)
        adapter.execute(handle, ToolRequest("subject", "order.get", {"order_id": "ord_1"}))
        post_reset_time = adapter.logical_time(handle)

        passed = (
            mutated_digest != initial_digest
            and mutated_time >= initial_time
            and result.before_digest == mutated_digest
            and result.after_digest == reset_digest
            and result.equivalent_to_initial
            and reset_digest == initial_digest
            and reset_time == initial_time
            and post_reset_time >= reset_time
        )
        return passed, (
            "reset re-establishes the declared initial lineage with bound digests and deterministic logical time"
            if passed
            else "reset or logical-time semantics violated the v0.1 contract"
        )

    @staticmethod
    def _observation(vector: Mapping[str, Any]) -> tuple[bool, str]:
        adapter, handle = ReferenceEnvironmentTCKAdapter._provision()
        actor_id = str(vector.get("actorId", "subject"))
        unknown_actor = str(vector.get("unknownActorId", "unknown"))
        forbidden = tuple(str(item) for item in vector.get("forbiddenMarkers", ()))
        observation = adapter.observe(handle, actor_id)
        serialized = repr(observation)
        try:
            adapter.observe(handle, unknown_actor)
            unknown_rejected = False
        except ToolPermissionDenied:
            unknown_rejected = True
        passed = bool(observation) and unknown_rejected and all(item not in serialized for item in forbidden)
        return passed, (
            "Subject observation is actor-scoped and excludes evaluator-only markers"
            if passed
            else "Subject observation scope or confidentiality violated the v0.1 contract"
        )

    @staticmethod
    def _projection(vector: Mapping[str, Any]) -> tuple[bool, str]:
        adapter, handle = ReferenceEnvironmentTCKAdapter._provision()
        projection_names = tuple(str(item) for item in vector.get("projections", ()))
        if len(projection_names) < 2:
            raise TCKAdapterError("Environment projection vector requires at least two projections")
        first = adapter.project(handle, projection_names[0])
        first_repeat = adapter.project(handle, projection_names[0])
        second = adapter.project(handle, projection_names[1])
        mutation = ReferenceEnvironmentTCKAdapter._mapping(vector.get("mutation"), "mutation")
        adapter.execute(handle, ReferenceEnvironmentTCKAdapter._tool_request(mutation))
        second_after = adapter.project(handle, projection_names[1])

        first_data = first.to_dict()["data"]
        second_data = second.to_dict()["data"]
        first_identity = (first.projection_id, first.digest)
        second_identity = (second.projection_id, second.digest)
        passed = (
            first.digest == digest(first_data)
            and second.digest == digest(second_data)
            and first.digest == first_repeat.digest
            and first.projection_id == projection_names[0]
            and second.projection_id == projection_names[1]
            and first_identity != second_identity
            and second_after.digest != second.digest
        )
        return passed, (
            "projection identifier and content digest remain bound as one evidence identity"
            if passed
            else "projection identity or digest binding violated the v0.1 contract"
        )

    @staticmethod
    def _snapshot_restore(vector: Mapping[str, Any]) -> tuple[bool, str]:
        adapter, handle = ReferenceEnvironmentTCKAdapter._provision()
        snapshot = adapter.snapshot(handle)
        mutation = ReferenceEnvironmentTCKAdapter._mapping(vector.get("mutation"), "mutation")
        adapter.execute(handle, ReferenceEnvironmentTCKAdapter._tool_request(mutation))
        restore = adapter.restore(handle, snapshot)
        restored_digest = adapter.digest(handle)

        other = adapter.provision(reference_scenario())
        try:
            adapter.restore(other, snapshot)
            foreign_rejected = False
        except SnapshotNotFoundError:
            foreign_rejected = True

        allowed = str(vector.get("allowedEquivalence", "STATE_EQUIVALENT"))
        passed = (
            snapshot.handle_id == handle.handle_id
            and bool(snapshot.state_digest)
            and restored_digest == snapshot.state_digest
            and restore.after_digest == snapshot.state_digest
            and restore.equivalence.value == allowed
            and restore.equivalence is not RestoreEquivalence.EXACT
            and foreign_rejected
        )
        return passed, (
            "snapshot ownership and state identity are bound and restore fidelity is not overstated"
            if passed
            else "snapshot ownership or restore-equivalence honesty violated the v0.1 contract"
        )

    @staticmethod
    def _diff(vector: Mapping[str, Any]) -> tuple[bool, str]:
        adapter, handle = ReferenceEnvironmentTCKAdapter._provision()
        projection = str(vector.get("projection", ""))
        before_projection = adapter.project(handle, projection)
        before = adapter.snapshot(handle)
        mutation = ReferenceEnvironmentTCKAdapter._mapping(vector.get("mutation"), "mutation")
        adapter.execute(handle, ReferenceEnvironmentTCKAdapter._tool_request(mutation))
        after_projection = adapter.project(handle, projection)
        after = adapter.snapshot(handle)

        changed = adapter.diff(handle, before, after, projection)
        no_op = adapter.diff(handle, after, after, projection)
        passed = (
            changed.projection_id == projection
            and changed.before_digest == before_projection.digest
            and changed.after_digest == after_projection.digest
            and bool(changed.changes)
            and no_op.projection_id == projection
            and no_op.before_digest == no_op.after_digest
            and not no_op.changes
        )
        return passed, (
            "StateDiff binds before/after projection identities and distinguishes mutation from no-op"
            if passed
            else "StateDiff binding or semantic-change reporting violated the v0.1 contract"
        )

    @staticmethod
    def _fault(vector: Mapping[str, Any]) -> tuple[bool, str]:
        adapter, handle = ReferenceEnvironmentTCKAdapter._provision()
        delayed = ReferenceEnvironmentTCKAdapter._mapping(vector.get("delayedFault"), "delayedFault")
        delayed_handle = adapter.inject_fault(handle, ReferenceEnvironmentTCKAdapter._fault_spec(delayed))

        first = adapter.execute(handle, ToolRequest("subject", "order.get", {"order_id": "ord_1"}))
        try:
            adapter.execute(handle, ToolRequest("subject", "order.get", {"order_id": "ord_1"}))
            activated = False
            observed_identity = False
        except ToolExecutionError as exc:
            activated = True
            observed_identity = bool(exc.fault_observations) and exc.fault_observations[0].fault_id == delayed_handle.fault_id
        third = adapter.execute(handle, ToolRequest("subject", "order.get", {"order_id": "ord_1"}))

        clear_vector = ReferenceEnvironmentTCKAdapter._mapping(vector.get("clearBeforeActivation"), "clearBeforeActivation")
        clear_handle = adapter.inject_fault(handle, ReferenceEnvironmentTCKAdapter._fault_spec(clear_vector))
        adapter.execute(handle, ToolRequest("subject", "order.get", {"order_id": "ord_1"}))
        adapter.clear_fault(handle, clear_handle)
        try:
            cleared_result = adapter.execute(handle, ToolRequest("subject", "order.get", {"order_id": "ord_1"}))
            clear_prevented = True
        except ToolExecutionError:
            clear_prevented = False
            cleared_result = None

        passed = (
            first.result.get("id") == "ord_1"
            and activated
            and observed_identity
            and third.result.get("id") == "ord_1"
            and delayed_handle.handle_id == handle.handle_id
            and clear_handle.handle_id == handle.handle_id
            and clear_prevented
            and cleared_result is not None
        )
        return passed, (
            "fault occurrence activates neither early nor repeatedly, and clear prevents later activation"
            if passed
            else "fault identity, occurrence, or clear semantics violated the v0.1 contract"
        )

    @staticmethod
    def _provision() -> tuple[InMemoryCommerceAdapter, EnvironmentHandle]:
        adapter = InMemoryCommerceAdapter()
        handle = adapter.provision(reference_scenario())
        adapter.reset(handle)
        return adapter, handle

    @staticmethod
    def _tool_request(vector: Mapping[str, Any]) -> ToolRequest:
        actor_id = str(vector.get("actorId", "subject"))
        name = str(vector.get("tool", ""))
        arguments = ReferenceEnvironmentTCKAdapter._mapping(vector.get("arguments", {}), "arguments")
        return ToolRequest(actor_id, name, arguments)

    @staticmethod
    def _fault_spec(vector: Mapping[str, Any]) -> FaultSpec:
        parameters = ReferenceEnvironmentTCKAdapter._mapping(vector.get("parameters", {}), "parameters")
        return FaultSpec(
            str(vector.get("kind", "")),
            str(vector.get("target", "")),
            occurrence=int(vector.get("occurrence", 1)),
            parameters=parameters,
        )

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("Environment TCK case metadata.id is missing")
        return case_id

    @staticmethod
    def _vector(case: Mapping[str, Any], case_id: str) -> Mapping[str, Any]:
        vector = case.get("vector")
        if not isinstance(vector, Mapping):
            raise TCKAdapterError(f"{case_id} vector must be an object")
        return vector

    @staticmethod
    def _mapping(value: Any, name: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise TCKAdapterError(f"Environment TCK {name} must be an object")
        return value

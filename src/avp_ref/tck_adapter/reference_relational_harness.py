"""In-memory implementation of the backend-neutral relational conformance harness.

Concrete mutation handles and negative-control resource classes are confined to
this module. The generic relational evaluator therefore has no reason to learn
which storage mechanism backs the SUT.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from avp_ref.relational import (
    ColumnDefinition,
    ExecutionInputDriftResource,
    FalseRestoreResource,
    HiddenStateLeakResource,
    InMemoryRelationalResource,
    RelationalLifecycleError,
    RelationalManifest,
    RelationalRow,
    RelationalValue,
    TornProjectionResource,
)

from .relational_harness import (
    NegativeControl,
    RelationalBackendHarness,
    RelationalFixtureControl,
    RelationalResourceSpec,
    RelationalSUT,
)


_NEGATIVE_RESOURCE_TYPES: Mapping[
    NegativeControl,
    type[InMemoryRelationalResource],
] = {
    NegativeControl.TORN_PROJECTION: TornProjectionResource,
    NegativeControl.FALSE_RESTORE: FalseRestoreResource,
    NegativeControl.HIDDEN_STATE_LEAK: HiddenStateLeakResource,
    NegativeControl.EXECUTION_INPUT_DRIFT: ExecutionInputDriftResource,
}


class InMemoryRelationalFixtureControl(RelationalFixtureControl):
    """Privileged controls for the in-memory conformance backend."""

    def __init__(self) -> None:
        self._held: dict[tuple[int, str], Any] = {}

    @staticmethod
    def _resource(sut: RelationalSUT) -> InMemoryRelationalResource:
        if not isinstance(sut, InMemoryRelationalResource):
            raise TypeError("fixture control received a foreign relational SUT")
        return sut

    @staticmethod
    def _key(sut: RelationalSUT, label: str) -> tuple[int, str]:
        if not label:
            raise RelationalLifecycleError("held mutation label must not be empty")
        return id(sut), label

    def replace_relation(
        self,
        sut: RelationalSUT,
        relation_id: str,
        replacement: Sequence[RelationalRow],
    ) -> None:
        resource = self._resource(sut)
        pending = resource.begin_subject_mutation(relation_id, replacement)
        resource.settle_subject_mutation(pending, commit=True)

    def replace_relations_atomically(
        self,
        sut: RelationalSUT,
        replacements: Mapping[str, Sequence[RelationalRow]],
    ) -> None:
        resource = self._resource(sut)
        resource._ensure_live()
        if resource._quiescing:
            raise RelationalLifecycleError(
                "new Subject mutation rejected after QUIESCING"
            )
        if not replacements:
            raise RelationalLifecycleError("atomic fixture mutation must not be empty")
        unknown = set(replacements) - set(resource._state)
        if unknown:
            raise RelationalLifecycleError(
                f"atomic fixture mutation references unknown relations: {sorted(unknown)}"
            )

        candidate = dict(resource._state)
        candidate.update(
            (relation_id, tuple(rows))
            for relation_id, rows in replacements.items()
        )
        # Direct state replacement is intentionally confined to this privileged
        # in-memory fixture driver. A real database driver will implement the
        # same logical operation with its native transaction mechanism.
        resource._state = resource._validate_state(candidate)

    def project_during_atomic_commit(
        self,
        sut: RelationalSUT,
        *,
        projection_id: str,
        replacements: Mapping[str, Sequence[RelationalRow]],
    ) -> Mapping[str, object]:
        # The in-memory model has no scheduler/MVCC layer, so choosing the
        # post-commit side is a valid deterministic implementation of the
        # portable pre-or-post invariant. Real backends may coordinate threads
        # and commit at an observation barrier behind this same seam.
        self.replace_relations_atomically(sut, replacements)
        return sut.project(projection_id)

    def begin_held_mutation(
        self,
        sut: RelationalSUT,
        *,
        label: str,
        relation_id: str,
        replacement: Sequence[RelationalRow],
    ) -> None:
        resource = self._resource(sut)
        key = self._key(sut, label)
        if key in self._held:
            raise RelationalLifecycleError(f"held mutation label already exists: {label}")
        self._held[key] = resource.begin_subject_mutation(relation_id, replacement)

    def settle_held_mutation(
        self,
        sut: RelationalSUT,
        *,
        label: str,
        commit: bool,
    ) -> None:
        resource = self._resource(sut)
        key = self._key(sut, label)
        try:
            pending = self._held.pop(key)
        except KeyError as exc:
            raise RelationalLifecycleError(
                f"unknown held mutation label: {label}"
            ) from exc
        # The native handle intentionally remains implementation-private. The
        # fixture API exposes only a harness-local label across this boundary.
        resource.settle_subject_mutation(pending, commit=commit)

    def set_logical_binding_valid(self, sut: RelationalSUT, valid: bool) -> None:
        self._resource(sut).set_logical_binding_valid(valid)

    def set_execution_input_identity(self, sut: RelationalSUT, identity: str) -> None:
        self._resource(sut).set_execution_input_identity(identity)


class InMemoryRelationalBackendHarness(RelationalBackendHarness):
    """Reference backend used to prove the shared harness before real databases."""

    def __init__(self) -> None:
        self._fixture_control = InMemoryRelationalFixtureControl()

    @property
    def fixture_control(self) -> RelationalFixtureControl:
        return self._fixture_control

    def identity_artifacts(
        self,
        manifest: RelationalManifest,
        baseline: Mapping[str, Sequence[RelationalRow]],
    ) -> tuple[str, str]:
        return InMemoryRelationalResource.identity_artifacts(manifest, baseline)

    def provision(
        self,
        spec: RelationalResourceSpec,
        *,
        negative_control: NegativeControl | None = None,
    ) -> RelationalSUT:
        resource_type = (
            InMemoryRelationalResource
            if negative_control is None
            else _NEGATIVE_RESOURCE_TYPES[negative_control]
        )
        return resource_type(
            environment_id=spec.environment_id,
            resource_id=spec.resource_id,
            resource_instance_id=spec.resource_instance_id,
            manifest=spec.manifest,
            manifest_artifact_digest=spec.manifest_artifact_digest,
            baseline=spec.baseline,
            baseline_artifact_digest=spec.baseline_artifact_digest,
            execution_input_identity=spec.execution_input_identity,
            evaluator_private_columns=spec.evaluator_private_columns,
        )

    def validate_value(
        self,
        column: ColumnDefinition,
        value: RelationalValue,
    ) -> None:
        InMemoryRelationalResource._validate_value(column, value)

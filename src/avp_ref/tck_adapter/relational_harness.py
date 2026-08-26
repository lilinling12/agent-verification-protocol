"""Backend-neutral execution boundaries for Relational State conformance.

This module is implementation infrastructure, not protocol authority. It keeps
portable SUT operations separate from privileged fixture controls so a database
backend can be exercised without exposing SQL, credentials, catalog access, or
backend transaction handles as AVP capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Protocol, Sequence, runtime_checkable

from avp_ref.relational import (
    ColumnDefinition,
    RelationalDiff,
    RelationalManifest,
    RelationalRow,
    RelationalSnapshot,
    RelationalValue,
    RestoreFidelity,
    StateImage,
)


class NegativeControl(str, Enum):
    """Metadata-equivalent broken behavior used only by conformance tests."""

    TORN_PROJECTION = "torn-projection"
    FALSE_RESTORE = "false-restore"
    HIDDEN_STATE_LEAK = "hidden-state-leak"
    EXECUTION_INPUT_DRIFT = "execution-input-drift"


@dataclass(frozen=True, slots=True)
class RelationalResourceSpec:
    """Immutable materialized inputs required to provision one relational SUT."""

    environment_id: str
    resource_id: str
    resource_instance_id: str
    manifest: RelationalManifest
    baseline: Mapping[str, Sequence[RelationalRow]]
    manifest_artifact_digest: str
    baseline_artifact_digest: str
    execution_input_identity: str
    evaluator_private_columns: frozenset[tuple[str, str]] = frozenset()


@runtime_checkable
class RelationalSUT(Protocol):
    """Portable observable operations consumed by relational conformance."""

    environment_id: str
    resource_id: str
    resource_instance_id: str
    manifest: RelationalManifest
    manifest_digest: str
    baseline_digest: str

    def state_image(self) -> StateImage: ...

    def project(self, projection_id: str) -> Mapping[str, object]: ...

    def enter_quiescing(self) -> None: ...

    def final_projection(self, projection_id: str) -> Mapping[str, object]: ...

    def snapshot(self) -> RelationalSnapshot: ...

    def reset(self) -> StateImage: ...

    def restore(self, snapshot: RelationalSnapshot) -> RestoreFidelity: ...

    def subject_view(
        self,
        authorized: Iterable[tuple[str, str]],
    ) -> Mapping[str, tuple[RelationalRow, ...]]: ...

    def diff(self, before: StateImage, after: StateImage) -> RelationalDiff: ...

    def release(self) -> None: ...


@runtime_checkable
class RelationalFixtureControl(Protocol):
    """Privileged logical controls that are deliberately absent from ``RelationalSUT``.

    A backend implementation may use SQL, DDL, admin credentials, or native
    transaction handles internally. Those mechanics must remain behind this
    test-only boundary and must never appear in portable TCK resources.
    """

    def replace_relation(
        self,
        sut: RelationalSUT,
        relation_id: str,
        replacement: Sequence[RelationalRow],
    ) -> None: ...

    def begin_held_mutation(
        self,
        sut: RelationalSUT,
        *,
        label: str,
        relation_id: str,
        replacement: Sequence[RelationalRow],
    ) -> None: ...

    def settle_held_mutation(
        self,
        sut: RelationalSUT,
        *,
        label: str,
        commit: bool,
    ) -> None: ...

    def set_logical_binding_valid(self, sut: RelationalSUT, valid: bool) -> None: ...

    def set_execution_input_identity(self, sut: RelationalSUT, identity: str) -> None: ...


@runtime_checkable
class RelationalBackendHarness(Protocol):
    """Factory and compatibility contract independently implemented per backend."""

    @property
    def fixture_control(self) -> RelationalFixtureControl: ...

    def identity_artifacts(
        self,
        manifest: RelationalManifest,
        baseline: Mapping[str, Sequence[RelationalRow]],
    ) -> tuple[str, str]: ...

    def provision(
        self,
        spec: RelationalResourceSpec,
        *,
        negative_control: NegativeControl | None = None,
    ) -> RelationalSUT: ...

    def validate_value(
        self,
        column: ColumnDefinition,
        value: RelationalValue,
    ) -> None: ...


def build_resource_spec(
    harness: RelationalBackendHarness,
    *,
    environment_id: str,
    resource_id: str,
    resource_instance_id: str,
    manifest: RelationalManifest,
    baseline: Mapping[str, Sequence[RelationalRow]],
    execution_input_identity: str,
    evaluator_private_columns: Iterable[tuple[str, str]] = (),
) -> RelationalResourceSpec:
    """Bind canonical identity before provisioning instead of trusting a backend."""

    manifest_digest, baseline_digest = harness.identity_artifacts(manifest, baseline)
    return RelationalResourceSpec(
        environment_id=environment_id,
        resource_id=resource_id,
        resource_instance_id=resource_instance_id,
        manifest=manifest,
        baseline=baseline,
        manifest_artifact_digest=manifest_digest,
        baseline_artifact_digest=baseline_digest,
        execution_input_identity=execution_input_identity,
        evaluator_private_columns=frozenset(evaluator_private_columns),
    )

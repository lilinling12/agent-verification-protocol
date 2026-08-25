"""Execution-sensitive TCK adapter for the AVP Relational State candidate.

The adapter exercises the backend-neutral reference model defined downstream of
``spec/relational/relational-state-contract.md``. Backend-specific SQL and
product identity are deliberately absent from this conformance surface.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from avp_ref.relational import (
    ColumnDefinition,
    ColumnType,
    ExecutionInputDriftResource,
    FalseRestoreResource,
    HiddenStateLeakResource,
    InMemoryRelationalResource,
    ProjectionDefinition,
    ProjectionRelation,
    RelationDefinition,
    RelationalCompatibilityError,
    RelationalLifecycleError,
    RelationalManifest,
    RelationalReferenceError,
    RelationalRow,
    RelationalSnapshot,
    RelationalValue,
    RelationalVisibilityError,
    RestoreFidelity,
    TornProjectionResource,
    ValueType,
)

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


class ReferenceRelationalTCKAdapter:
    """Execute all mandatory ``avp-relational-state-v0.1`` case families."""

    _IDENTITY = "AVP-TCK-RELATIONAL-IDENTITY-001"
    _CANONICAL = "AVP-TCK-RELATIONAL-CANONICAL-001"
    _PROJECTION = "AVP-TCK-RELATIONAL-PROJECTION-001"
    _QUIESCING = "AVP-TCK-RELATIONAL-QUIESCING-001"
    _DRIFT = "AVP-TCK-RELATIONAL-DRIFT-001"
    _SNAPSHOT_RESET = "AVP-TCK-RELATIONAL-SNAPSHOT-RESET-001"
    _RESTORE = "AVP-TCK-RELATIONAL-RESTORE-001"
    _DIFF = "AVP-TCK-RELATIONAL-DIFF-001"
    _SECURITY = "AVP-TCK-RELATIONAL-SECURITY-001"
    _EXECUTED = "AVP-TCK-RELATIONAL-EXECUTED-CAPABILITY-001"

    def __init__(self) -> None:
        self._evaluators: dict[str, Callable[[Mapping[str, Any]], tuple[bool, str]]] = {
            self._IDENTITY: self._identity,
            self._CANONICAL: self._canonical,
            self._PROJECTION: self._projection,
            self._QUIESCING: self._quiescing,
            self._DRIFT: self._drift,
            self._SNAPSHOT_RESET: self._snapshot_reset,
            self._RESTORE: self._restore,
            self._DIFF: self._diff,
            self._SECURITY: self._security,
            self._EXECUTED: self._executed_capability,
        }

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return frozenset(self._evaluators)

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        metadata = self._mapping(case.get("metadata"), "metadata")
        case_id = self._string(metadata.get("id"), "metadata.id")
        evaluator = self._evaluators.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(f"unsupported relational TCK case: {case_id}")
        if case.get("profile") != "avp-relational-state-v0.1":
            raise TCKAdapterError(f"{case_id} has unexpected profile")
        vector = self._mapping(case.get("vector"), f"{case_id}.vector")
        passed, detail = evaluator(vector)
        return TCKCaseResult(
            case_id,
            TCKStatus.PASS if passed else TCKStatus.FAIL,
            detail,
        )

    def _identity(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        capability = self._mapping(vector.get("capability"), "identity capability")
        media_types = self._string_tuple(
            vector.get("identityMediaTypes"),
            "identity media types",
        )
        tamper_controls = set(
            self._string_tuple(vector.get("tamperControls"), "tamper controls")
        )
        manifest = self._simple_manifest()
        baseline = {"records": (self._simple_row("1", "baseline"),)}
        manifest_digest, baseline_digest = InMemoryRelationalResource.identity_artifacts(
            manifest,
            baseline,
        )
        resource = self._resource(
            manifest=manifest,
            baseline=baseline,
            instance_id="identity-good",
        )

        rejected: set[str] = set()
        if "manifest-artifact-digest" in tamper_controls:
            try:
                InMemoryRelationalResource(
                    environment_id="env-identity-tamper",
                    resource_id="state",
                    resource_instance_id="identity-bad-manifest",
                    manifest=manifest,
                    manifest_artifact_digest=self._different_digest(manifest_digest),
                    baseline=baseline,
                    baseline_artifact_digest=baseline_digest,
                    execution_input_identity=self._digest("b"),
                )
            except RelationalCompatibilityError:
                rejected.add("manifest-artifact-digest")
        if "baseline-artifact-digest" in tamper_controls:
            try:
                InMemoryRelationalResource(
                    environment_id="env-identity-tamper",
                    resource_id="state",
                    resource_instance_id="identity-bad-baseline",
                    manifest=manifest,
                    manifest_artifact_digest=manifest_digest,
                    baseline=baseline,
                    baseline_artifact_digest=self._different_digest(baseline_digest),
                    execution_input_identity=self._digest("b"),
                )
            except RelationalCompatibilityError:
                rejected.add("baseline-artifact-digest")

        manifest_doc = manifest.as_document()
        passed = (
            vector.get("resourceKind") == "state"
            and capability.get("capabilityId") == "state.relational"
            and capability.get("profile") == "avp-relational-state-v0.1"
            and capability.get("revision") == "0.1"
            and media_types
            == (
                "application/vnd.avp.relational-state-manifest+json",
                "application/vnd.avp.relational-state-image+json",
            )
            and vector.get("manifestContainsBaselineReference") is False
            and manifest_doc.get("kind") == "RelationalStateManifest"
            and resource.manifest_digest == manifest_digest
            and resource.baseline_digest == baseline_digest
            and rejected == tamper_controls
        )
        return passed, (
            "canonical Manifest/baseline Artifact identities are derived and tamper controls fail closed"
            if passed
            else "relational content-address identity binding was trusted or incomplete"
        )

    def _canonical(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        manifest = self._canonical_manifest()
        rows = (
            self._canonical_row("2", "2.50", "e\u0301"),
            self._canonical_row("1", "1.00", "é"),
        )
        resource = self._resource(
            environment_id="env-canonical",
            resource_id="state",
            instance_id="canonical",
            manifest=manifest,
            baseline={"records": rows},
            execution_input_identity=self._digest("e"),
        )
        ordered = [
            row.value_map()["id"].value
            for row in resource.state_image().relations[0][1]
        ]

        valid_controls = vector.get("validControls")
        invalid_controls = vector.get("invalidControls")
        invalid_type_controls = vector.get("invalidTypeControls")
        if not isinstance(valid_controls, list):
            raise TCKAdapterError("canonical validControls must be a list")
        if not isinstance(invalid_controls, list):
            raise TCKAdapterError("canonical invalidControls must be a list")
        if not isinstance(invalid_type_controls, list):
            raise TCKAdapterError("canonical invalidTypeControls must be a list")

        accepted = 0
        for item in valid_controls:
            control = self._mapping(item, "canonical valid control")
            column, value = self._scalar_control(control)
            InMemoryRelationalResource._validate_value(column, value)
            accepted += 1

        rejected = 0
        for item in invalid_controls:
            control = self._mapping(item, "canonical invalid control")
            try:
                column, value = self._scalar_control(control)
                InMemoryRelationalResource._validate_value(column, value)
            except (RelationalCompatibilityError, ValueError):
                rejected += 1

        rejected_types = 0
        for item in invalid_type_controls:
            control = self._mapping(item, "canonical invalid type control")
            try:
                self._column_type(control)
            except (RelationalCompatibilityError, ValueError):
                rejected_types += 1

        text_values = [
            row.value_map()["text"].value
            for row in resource.state_image().relations[0][1]
        ]
        passed = (
            ordered == ["1", "2"]
            and accepted == len(valid_controls)
            and rejected == len(invalid_controls)
            and rejected_types == len(invalid_type_controls)
            and len(set(text_values)) == 2
        )
        return passed, (
            "complete closed scalar vocabulary, parameter boundaries, logical-key ordering, and exact Unicode identity verified"
            if passed
            else "mandatory scalar/canonical execution coverage failed"
        )

    def _projection(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        resource = self._consistency_resource(InMemoryRelationalResource, "projection-good")
        projection = resource.project("consistency.pair")
        observed = self._epochs(projection)
        allowed = {(1, 1), (2, 2)}

        torn = self._consistency_resource(TornProjectionResource, "projection-torn")
        torn_observed = self._epochs(torn.project("consistency.pair"))
        passed = observed in allowed and torn_observed not in allowed
        return passed, (
            "projection is one committed multi-relation view and torn control is detectable"
            if passed
            else "projection accepted dirty/torn visibility or negative control escaped detection"
        )

    def _quiescing(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        commit_resource = self._simple_resource(instance_id="quiescing-commit")
        replacement = (self._simple_row("1", "committed"),)
        pending = commit_resource.begin_subject_mutation("records", replacement)
        commit_resource.enter_quiescing()
        try:
            commit_resource.begin_subject_mutation("records", replacement)
            rejected_new = False
        except RelationalLifecycleError:
            rejected_new = True
        try:
            commit_resource.final_projection("records.all")
            unresolved_blocked = False
        except RelationalLifecycleError:
            unresolved_blocked = True
        commit_resource.settle_subject_mutation(pending, commit=True)
        final = commit_resource.final_projection("records.all")
        committed_observed = self._projection_text(final) == "committed"

        rollback_resource = self._simple_resource(instance_id="quiescing-rollback")
        rollback = rollback_resource.begin_subject_mutation(
            "records",
            (self._simple_row("1", "rolled"),),
        )
        rollback_resource.enter_quiescing()
        rollback_resource.settle_subject_mutation(rollback, commit=False)
        rolled_back_hidden = (
            self._projection_text(
                rollback_resource.final_projection("records.all")
            )
            == "baseline"
        )

        passed = (
            rejected_new
            and unresolved_blocked
            and committed_observed
            and rolled_back_hidden
        )
        return passed, (
            "QUIESCING closes admission and waits for commit/rollback settlement without fabrication"
            if passed
            else "QUIESCING admission or settlement semantics were violated"
        )

    def _drift(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        logical = self._simple_resource(instance_id="drift-logical")
        logical.set_logical_binding_valid(False)
        try:
            logical.state_image()
            logical_rejected = False
        except RelationalCompatibilityError:
            logical_rejected = True

        irrelevant = self._simple_resource(instance_id="drift-irrelevant")
        irrelevant_ok = bool(irrelevant.state_image().digest)

        execution = self._simple_resource(instance_id="drift-execution")
        execution.set_execution_input_identity(self._digest("f"))
        try:
            execution.state_image()
            execution_rejected = False
        except RelationalCompatibilityError:
            execution_rejected = True

        negative = self._simple_resource(
            resource_type=ExecutionInputDriftResource,
            instance_id="drift-negative",
        )
        negative.set_execution_input_identity(self._digest("f"))
        negative_wrongly_accepts = bool(negative.state_image().digest)

        passed = (
            logical_rejected
            and irrelevant_ok
            and execution_rejected
            and negative_wrongly_accepts
        )
        return passed, (
            "logical binding and execution-input drift fail closed without raw catalog equality"
            if passed
            else "relational drift boundary was not enforced or negative control was not observable"
        )

    def _snapshot_reset(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        resource = self._simple_resource(instance_id="snapshot-owner")
        snapshot = resource.snapshot()
        mutation = resource.begin_subject_mutation(
            "records",
            (self._simple_row("1", "changed"),),
        )
        resource.settle_subject_mutation(mutation, commit=True)
        changed = resource.state_image().digest != snapshot.state.digest
        reset = resource.reset()
        reset_equal = reset.digest == resource.baseline_digest

        foreign = RelationalSnapshot(
            snapshot.snapshot_id,
            "env-other",
            snapshot.resource_id,
            snapshot.resource_instance_id,
            snapshot.state,
        )
        try:
            resource.restore(foreign)
            foreign_rejected = False
        except RelationalReferenceError:
            foreign_rejected = True

        resource.release()
        replacement = self._simple_resource(instance_id="snapshot-replacement")
        try:
            replacement.restore(snapshot)
            stale_rejected = False
        except RelationalReferenceError:
            stale_rejected = True

        passed = changed and reset_equal and foreign_rejected and stale_rejected
        return passed, (
            "snapshot owner-instance binding, stale-reference rejection, and independently verified reset passed"
            if passed
            else "snapshot ownership/staleness or reset verification failed"
        )

    def _restore(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        resource = self._simple_resource(instance_id="restore-good")
        snapshot = resource.snapshot()
        mutation = resource.begin_subject_mutation(
            "records",
            (self._simple_row("1", "changed"),),
        )
        resource.settle_subject_mutation(mutation, commit=True)
        fidelity = resource.restore(snapshot)
        restored = resource.state_image().digest == snapshot.state.digest

        false_resource = self._simple_resource(
            resource_type=FalseRestoreResource,
            instance_id="restore-false",
        )
        false_snapshot = false_resource.snapshot()
        false_mutation = false_resource.begin_subject_mutation(
            "records",
            (self._simple_row("1", "changed"),),
        )
        false_resource.settle_subject_mutation(false_mutation, commit=True)
        false_claim = false_resource.restore(false_snapshot)
        false_detected = (
            false_claim is RestoreFidelity.STATE_EQUIVALENT
            and false_resource.state_image().digest != false_snapshot.state.digest
        )
        passed = (
            fidelity is RestoreFidelity.STATE_EQUIVALENT
            and restored
            and false_detected
        )
        return passed, (
            "successful restore proves StateImage equality at exact STATE_EQUIVALENT fidelity and false restore is detectable"
            if passed
            else "restore fidelity/equality semantics failed"
        )

    def _diff(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        resource = self._diff_resource()
        before = resource.state_image()
        replacement = (
            self._simple_row("1", "updated"),
            self._simple_row("3", "c"),
            self._simple_row("5", "key-before"),
        )
        pending = resource.begin_subject_mutation("records", replacement)
        resource.settle_subject_mutation(pending, commit=True)
        after = resource.state_image()
        diff = resource.diff(before, after)
        document = diff.as_document()

        by_change: dict[str, list[str]] = {
            "INSERT": [],
            "DELETE": [],
            "UPDATE": [],
        }
        change_shape_valid = True
        for change in diff.changes:
            key = dict(change.key)
            identifier = key["id"].value
            if isinstance(identifier, str):
                by_change[change.change].append(identifier)
            if change.change == "INSERT":
                change_shape_valid &= change.before is None and change.after is not None
            elif change.change == "DELETE":
                change_shape_valid &= change.before is not None and change.after is None
            elif change.change == "UPDATE":
                change_shape_valid &= change.before is not None and change.after is not None
            else:
                change_shape_valid = False

        required = {
            "apiVersion",
            "kind",
            "manifestDigest",
            "scope",
            "beforeDigest",
            "afterDigest",
            "changes",
        }
        passed = (
            set(document) == required
            and document["manifestDigest"] == resource.manifest_digest
            and document["scope"] == {"kind": "full"}
            and document["beforeDigest"] == before.digest
            and document["afterDigest"] == after.digest
            and by_change["UPDATE"] == ["1"]
            and by_change["DELETE"] == ["2", "4"]
            and by_change["INSERT"] == ["3", "5"]
            and change_shape_valid
        )
        return passed, (
            "schema-shaped semantic diff binds Manifest/scope/before/after identity and deterministic logical changes"
            if passed
            else "relational diff protocol shape or identity/change semantics diverged"
        )

    def _security(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        resource = self._security_resource(
            InMemoryRelationalResource,
            "security-good",
        )
        complete = resource.state_image()
        subject = resource.subject_view(
            {("records", "id"), ("records", "public_value")}
        )
        subject_values = subject["records"][0].value_map()
        private_preserved = (
            "hidden_evaluator_value" in complete.relations[0][1][0].value_map()
        )
        hidden_excluded = "hidden_evaluator_value" not in subject_values

        leakage = self._security_resource(HiddenStateLeakResource, "security-leak")
        leaked = leakage.subject_view(
            {("records", "id"), ("records", "public_value")}
        )
        leak_detected = (
            "hidden_evaluator_value" in leaked["records"][0].value_map()
        )

        try:
            resource.subject_view({("records", "hidden_evaluator_value")})
            explicit_private_rejected = False
        except RelationalVisibilityError:
            explicit_private_rejected = True

        passed = (
            private_preserved
            and hidden_excluded
            and leak_detected
            and explicit_private_rejected
        )
        return passed, (
            "evaluator-private authoritative state is preserved while Subject visibility remains fail closed"
            if passed
            else "relational hidden-state visibility boundary failed"
        )

    def _executed_capability(self, vector: Mapping[str, Any]) -> tuple[bool, str]:
        torn = self._consistency_resource(TornProjectionResource, "executed-torn")
        torn_failed = self._epochs(torn.project("consistency.pair")) not in {
            (1, 1),
            (2, 2),
        }

        false_restore = self._simple_resource(
            resource_type=FalseRestoreResource,
            instance_id="executed-false-restore",
        )
        snapshot = false_restore.snapshot()
        mutation = false_restore.begin_subject_mutation(
            "records",
            (self._simple_row("1", "changed"),),
        )
        false_restore.settle_subject_mutation(mutation, commit=True)
        claim = false_restore.restore(snapshot)
        false_restore_failed = (
            claim is RestoreFidelity.STATE_EQUIVALENT
            and false_restore.state_image().digest != snapshot.state.digest
        )

        leak = self._security_resource(HiddenStateLeakResource, "executed-leak")
        leaked = leak.subject_view(
            {("records", "id"), ("records", "public_value")}
        )
        leak_failed = "hidden_evaluator_value" in leaked["records"][0].value_map()

        drift = self._simple_resource(
            resource_type=ExecutionInputDriftResource,
            instance_id="executed-drift",
        )
        drift.set_execution_input_identity(self._digest("f"))
        drift_failed = bool(drift.state_image().digest)

        passed = torn_failed and false_restore_failed and leak_failed and drift_failed
        return passed, (
            "metadata-identical torn/false-restore/hidden-leak/execution-drift controls are rejected from observed behavior"
            if passed
            else "execution-sensitive relational conformance could be satisfied by a broken implementation"
        )

    @staticmethod
    def _simple_manifest() -> RelationalManifest:
        relation = RelationDefinition(
            "records",
            (
                ColumnDefinition("id", ColumnType(ValueType.INTEGER)),
                ColumnDefinition("value", ColumnType(ValueType.TEXT)),
            ),
            ("id",),
        )
        return RelationalManifest(
            (relation,),
            (
                ProjectionDefinition(
                    "records.all",
                    (ProjectionRelation("records", ("id", "value")),),
                ),
            ),
        )

    @staticmethod
    def _canonical_manifest() -> RelationalManifest:
        relation = RelationDefinition(
            "records",
            (
                ColumnDefinition("id", ColumnType(ValueType.INTEGER)),
                ColumnDefinition(
                    "amount",
                    ColumnType(ValueType.DECIMAL, precision=65, scale=2),
                ),
                ColumnDefinition("text", ColumnType(ValueType.TEXT)),
            ),
            ("id",),
        )
        return RelationalManifest((relation,))

    @staticmethod
    def _simple_row(identifier: str, value: str) -> RelationalRow:
        return RelationalRow.from_mapping(
            {
                "id": RelationalValue(ValueType.INTEGER, identifier),
                "value": RelationalValue(ValueType.TEXT, value),
            }
        )

    @staticmethod
    def _canonical_row(identifier: str, amount: str, text: str) -> RelationalRow:
        return RelationalRow.from_mapping(
            {
                "id": RelationalValue(ValueType.INTEGER, identifier),
                "amount": RelationalValue(ValueType.DECIMAL, amount),
                "text": RelationalValue(ValueType.TEXT, text),
            }
        )

    def _simple_resource(
        self,
        *,
        resource_type: type[InMemoryRelationalResource] = InMemoryRelationalResource,
        instance_id: str,
    ) -> InMemoryRelationalResource:
        manifest = self._simple_manifest()
        baseline = {"records": (self._simple_row("1", "baseline"),)}
        return self._resource(
            resource_type=resource_type,
            environment_id="env-relational",
            resource_id="primary-state",
            instance_id=instance_id,
            manifest=manifest,
            baseline=baseline,
        )

    def _diff_resource(self) -> InMemoryRelationalResource:
        manifest = self._simple_manifest()
        baseline = {
            "records": (
                self._simple_row("1", "a"),
                self._simple_row("2", "b"),
                self._simple_row("4", "key-before"),
            )
        }
        return self._resource(
            environment_id="env-diff",
            resource_id="primary-state",
            instance_id="diff",
            manifest=manifest,
            baseline=baseline,
        )

    @staticmethod
    def _consistency_manifest() -> RelationalManifest:
        columns = (
            ColumnDefinition("id", ColumnType(ValueType.INTEGER)),
            ColumnDefinition("epoch", ColumnType(ValueType.INTEGER)),
        )
        return RelationalManifest(
            (
                RelationDefinition("consistency.left", columns, ("id",)),
                RelationDefinition("consistency.right", columns, ("id",)),
            ),
            (
                ProjectionDefinition(
                    "consistency.pair",
                    (
                        ProjectionRelation("consistency.left", ("id", "epoch")),
                        ProjectionRelation("consistency.right", ("id", "epoch")),
                    ),
                ),
            ),
        )

    def _consistency_resource(
        self,
        resource_type: type[InMemoryRelationalResource],
        instance_id: str,
    ) -> InMemoryRelationalResource:
        row = RelationalRow.from_mapping(
            {
                "id": RelationalValue(ValueType.INTEGER, "1"),
                "epoch": RelationalValue(ValueType.INTEGER, "1"),
            }
        )
        manifest = self._consistency_manifest()
        baseline = {
            "consistency.left": (row,),
            "consistency.right": (row,),
        }
        return self._resource(
            resource_type=resource_type,
            environment_id="env-consistency",
            resource_id="state",
            instance_id=instance_id,
            manifest=manifest,
            baseline=baseline,
        )

    def _security_resource(
        self,
        resource_type: type[InMemoryRelationalResource],
        instance_id: str,
    ) -> InMemoryRelationalResource:
        relation = RelationDefinition(
            "records",
            (
                ColumnDefinition("id", ColumnType(ValueType.INTEGER)),
                ColumnDefinition("public_value", ColumnType(ValueType.TEXT)),
                ColumnDefinition(
                    "hidden_evaluator_value",
                    ColumnType(ValueType.TEXT),
                ),
            ),
            ("id",),
        )
        manifest = RelationalManifest((relation,))
        row = RelationalRow.from_mapping(
            {
                "id": RelationalValue(ValueType.INTEGER, "1"),
                "public_value": RelationalValue(ValueType.TEXT, "visible"),
                "hidden_evaluator_value": RelationalValue(ValueType.TEXT, "secret"),
            }
        )
        return self._resource(
            resource_type=resource_type,
            environment_id="env-security",
            resource_id="state",
            instance_id=instance_id,
            manifest=manifest,
            baseline={"records": (row,)},
            evaluator_private_columns={("records", "hidden_evaluator_value")},
        )

    def _resource(
        self,
        *,
        manifest: RelationalManifest,
        baseline: Mapping[str, tuple[RelationalRow, ...]],
        instance_id: str,
        environment_id: str = "env-relational",
        resource_id: str = "state",
        execution_input_identity: str | None = None,
        evaluator_private_columns: set[tuple[str, str]] | None = None,
        resource_type: type[InMemoryRelationalResource] = InMemoryRelationalResource,
    ) -> InMemoryRelationalResource:
        manifest_digest, baseline_digest = InMemoryRelationalResource.identity_artifacts(
            manifest,
            baseline,
        )
        return resource_type(
            environment_id=environment_id,
            resource_id=resource_id,
            resource_instance_id=instance_id,
            manifest=manifest,
            manifest_artifact_digest=manifest_digest,
            baseline=baseline,
            baseline_artifact_digest=baseline_digest,
            execution_input_identity=execution_input_identity or self._digest("b"),
            evaluator_private_columns=evaluator_private_columns or (),
        )

    def _scalar_control(
        self,
        control: Mapping[str, Any],
    ) -> tuple[ColumnDefinition, RelationalValue]:
        column_type = self._column_type(control)
        nullable = control.get("nullable", False)
        if not isinstance(nullable, bool):
            raise TCKAdapterError("scalar nullable must be boolean")
        column = ColumnDefinition("value", column_type, nullable=nullable)
        value = RelationalValue(column_type.kind, control.get("value"))
        return column, value

    def _column_type(self, control: Mapping[str, Any]) -> ColumnType:
        kind = ValueType(self._string(control.get("type"), "scalar type"))
        if kind is ValueType.DECIMAL:
            return ColumnType(
                kind,
                precision=self._integer(control.get("precision"), "precision"),
                scale=self._integer(control.get("scale"), "scale"),
            )
        if kind in {
            ValueType.TIME_LOCAL,
            ValueType.TIMESTAMP_LOCAL,
            ValueType.TIMESTAMP_INSTANT,
        }:
            return ColumnType(
                kind,
                fractional_precision=self._integer(
                    control.get("fractionalPrecision"),
                    "fractionalPrecision",
                ),
            )
        return ColumnType(kind)

    @staticmethod
    def _epochs(projection: Mapping[str, object]) -> tuple[int, int]:
        relations = projection.get("relations")
        if not isinstance(relations, list) or len(relations) != 2:
            raise TCKAdapterError(
                "consistency projection must contain exactly two relations"
            )
        epochs: list[int] = []
        for relation in relations:
            if not isinstance(relation, Mapping):
                raise TCKAdapterError("projection relation must be a mapping")
            rows = relation.get("rows")
            if (
                not isinstance(rows, list)
                or len(rows) != 1
                or not isinstance(rows[0], Mapping)
            ):
                raise TCKAdapterError("consistency relation must contain one row")
            values = rows[0].get("values")
            if not isinstance(values, Mapping):
                raise TCKAdapterError("projection row values missing")
            epoch = values.get("epoch")
            if not isinstance(epoch, Mapping) or not isinstance(
                epoch.get("value"),
                str,
            ):
                raise TCKAdapterError("projection epoch missing")
            epochs.append(int(epoch["value"]))
        return epochs[0], epochs[1]

    @staticmethod
    def _projection_text(projection: Mapping[str, object]) -> str:
        relations = projection.get("relations")
        if (
            not isinstance(relations, list)
            or not relations
            or not isinstance(relations[0], Mapping)
        ):
            raise TCKAdapterError("records projection missing relation")
        rows = relations[0].get("rows")
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], Mapping):
            raise TCKAdapterError("records projection missing row")
        values = rows[0].get("values")
        if not isinstance(values, Mapping):
            raise TCKAdapterError("records projection missing values")
        value = values.get("value")
        if not isinstance(value, Mapping) or not isinstance(value.get("value"), str):
            raise TCKAdapterError("records projection missing text value")
        return value["value"]

    @staticmethod
    def _mapping(value: Any, context: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise TCKAdapterError(f"relational TCK {context} must be an object")
        return value

    @staticmethod
    def _string(value: Any, context: str) -> str:
        if not isinstance(value, str) or not value:
            raise TCKAdapterError(
                f"relational TCK {context} must be a non-empty string"
            )
        return value

    @staticmethod
    def _integer(value: Any, context: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TCKAdapterError(f"relational TCK {context} must be an integer")
        return value

    @staticmethod
    def _string_tuple(value: Any, context: str) -> tuple[str, ...]:
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise TCKAdapterError(
                f"relational TCK {context} must be a string list"
            )
        return tuple(value)

    @staticmethod
    def _digest(character: str) -> str:
        return "sha256:" + character * 64

    @staticmethod
    def _different_digest(digest: str) -> str:
        replacement = "0" if digest[-1] != "0" else "1"
        return digest[:-1] + replacement

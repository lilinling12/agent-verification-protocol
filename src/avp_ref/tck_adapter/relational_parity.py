"""Cross-backend canonical evidence for the Relational State implementation.

This module is implementation/test infrastructure, not protocol authority.  It
compares portable observations produced by two independently provisioned
``RelationalBackendHarness`` implementations against the same immutable parity
fixture.  Backend SQL, storage types, transaction handles, and product identity
remain outside this boundary.

Parity deliberately does *not* require concurrent observations to select the
same side of a commit.  AVP-RELATIONAL-007 permits either complete pre-commit or
complete post-commit visibility; the portable invariant is that neither side is
torn.  Every deterministic canonical artifact, however, must compare byte for
byte and must also match the fixture's independently locked expectations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from avp_ref.canonical import canonical_json, digest
from avp_ref.relational import RelationalDiff, RestoreFidelity, StateImage

from .relational_fixture import RelationalParityFixture
from .relational_harness import (
    RelationalBackendHarness,
    RelationalSUT,
    build_resource_spec,
)

_EXECUTION_INPUT_IDENTITY = "sha256:" + "d" * 64


class RelationalParityError(AssertionError):
    """Portable observations from the paired backends failed parity."""


@dataclass(frozen=True, slots=True)
class RelationalParityEvidence:
    """Compact portable result of one real cross-backend parity execution."""

    fixture_sha256: str
    manifest_digest: str
    baseline_state_image_digest: str
    baseline_projection_digests: tuple[tuple[str, str], ...]
    atomic_observations: tuple[tuple[str, tuple[str, str]], ...]
    after_atomic_state_image_digest: str
    atomic_diff_digest: str
    restore_fidelity: RestoreFidelity
    restored_state_image_digest: str
    reset_state_image_digest: str


class RelationalParityVerifier:
    """Verify canonical parity without making either backend the oracle.

    The immutable fixture is the expected-value authority for this implementation
    acceptance slice.  Both backends are compared independently with that fixture
    and with each other, preventing a shared backend defect from becoming accepted
    merely because the second implementation copied the same expectation.
    """

    def __init__(
        self,
        fixture: RelationalParityFixture,
        backends: Mapping[str, RelationalBackendHarness],
    ) -> None:
        if len(backends) < 2:
            raise ValueError("canonical parity requires at least two backends")
        if any(not label for label in backends):
            raise ValueError("parity backend labels must not be empty")
        if len({id(backend) for backend in backends.values()}) != len(backends):
            raise ValueError("canonical parity requires distinct backend harness instances")
        self._fixture = fixture
        self._backends = tuple(sorted(backends.items()))
        self._backend_by_label = dict(self._backends)

    def verify(self) -> RelationalParityEvidence:
        """Execute the fixture lifecycle and return portable acceptance evidence."""

        resources = {
            label: self._provision(backend, label)
            for label, backend in self._backends
        }
        try:
            baseline = self._verify_baseline(resources)
            projections = self._verify_baseline_projections(resources)
            self._verify_snapshot_state(resources, baseline)
            atomic_observations, after_atomic, atomic_diff = self._verify_atomic_mutation(
                resources,
                baseline,
            )
            restore_fidelity, restored = self._verify_restore(resources)
            reset = self._verify_reset(resources)
            return RelationalParityEvidence(
                fixture_sha256=self._fixture.canonical_sha256,
                manifest_digest=self._fixture.expectations.manifest_digest,
                baseline_state_image_digest=baseline.digest,
                baseline_projection_digests=projections,
                atomic_observations=atomic_observations,
                after_atomic_state_image_digest=after_atomic.digest,
                atomic_diff_digest=atomic_diff.digest,
                restore_fidelity=restore_fidelity,
                restored_state_image_digest=restored.digest,
                reset_state_image_digest=reset.digest,
            )
        finally:
            for resource in reversed(tuple(resources.values())):
                resource.release()

    def _provision(
        self,
        backend: RelationalBackendHarness,
        label: str,
    ) -> RelationalSUT:
        spec = build_resource_spec(
            backend,
            environment_id="env-relational-parity",
            resource_id="state",
            resource_instance_id=f"parity-{label}",
            manifest=self._fixture.manifest,
            baseline=self._fixture.baseline_mapping(),
            execution_input_identity=_EXECUTION_INPUT_IDENTITY,
        )
        resource = backend.provision(spec)
        self._require_equal(
            f"{label} manifest digest",
            resource.manifest_digest,
            self._fixture.expectations.manifest_digest,
        )
        self._require_equal(
            f"{label} baseline digest binding",
            resource.baseline_digest,
            self._fixture.expectations.baseline_state_image_digest,
        )
        return resource

    def _verify_baseline(
        self,
        resources: Mapping[str, RelationalSUT],
    ) -> StateImage:
        observed = {label: resource.state_image() for label, resource in resources.items()}
        expected_digest = self._fixture.expectations.baseline_state_image_digest
        for label, state in observed.items():
            self._require_equal(
                f"{label} baseline StateImage digest",
                state.digest,
                expected_digest,
            )
        return self._require_canonical_state_parity("baseline StateImage", observed)

    def _verify_baseline_projections(
        self,
        resources: Mapping[str, RelationalSUT],
    ) -> tuple[tuple[str, str], ...]:
        evidence: list[tuple[str, str]] = []
        for projection in sorted(
            self._fixture.manifest.projections,
            key=lambda item: item.projection_id,
        ):
            projection_id = projection.projection_id
            observed = {
                label: resource.project(projection_id)
                for label, resource in resources.items()
            }
            expected_digest = self._fixture.expectations.projection_digest(projection_id)
            for label, document in observed.items():
                self._require_equal(
                    f"{label} projection {projection_id} digest",
                    digest(document),
                    expected_digest,
                )
            self._require_canonical_document_parity(
                f"baseline projection {projection_id}",
                observed,
            )
            evidence.append((projection_id, expected_digest))
        return tuple(evidence)

    def _verify_snapshot_state(
        self,
        resources: Mapping[str, RelationalSUT],
        baseline: StateImage,
    ) -> None:
        snapshots = {
            label: resource.snapshot()
            for label, resource in resources.items()
        }
        observed = {
            label: snapshot.state
            for label, snapshot in snapshots.items()
        }
        canonical = self._require_canonical_state_parity(
            "snapshot StateImage",
            observed,
        )
        self._require_equal("snapshot baseline identity", canonical.digest, baseline.digest)

    def _verify_atomic_mutation(
        self,
        resources: Mapping[str, RelationalSUT],
        baseline: StateImage,
    ) -> tuple[
        tuple[tuple[str, tuple[str, str]], ...],
        StateImage,
        RelationalDiff,
    ]:
        observations: list[tuple[str, tuple[str, str]]] = []
        allowed = set(self._fixture.allowed_consistency_epochs)
        after_states: dict[str, StateImage] = {}
        diffs: dict[str, RelationalDiff] = {}

        for label, resource in resources.items():
            backend = self._backend_by_label[label]
            document = backend.fixture_control.project_during_atomic_commit(
                resource,
                projection_id="consistency.pair",
                replacements=self._fixture.epoch_mutation_mapping(),
            )
            epochs = self._epochs(document)
            if epochs not in allowed:
                raise RelationalParityError(
                    f"{label} atomic observation is torn or outside the fixture: {epochs!r}"
                )
            observations.append((label, epochs))

            after = resource.state_image()
            expected_after = (
                self._fixture.expectations.after_atomic_epoch_mutation_state_image_digest
            )
            self._require_equal(
                f"{label} post-commit StateImage digest",
                after.digest,
                expected_after,
            )
            after_states[label] = after

            observed_diff = resource.diff(baseline, after)
            self._require_equal(
                f"{label} atomic diff digest",
                observed_diff.digest,
                self._fixture.expectations.atomic_epoch_mutation_diff_digest,
            )
            diffs[label] = observed_diff

        after = self._require_canonical_state_parity(
            "post-commit StateImage",
            after_states,
        )
        diff = self._require_canonical_diff_parity("atomic mutation diff", diffs)
        return tuple(sorted(observations)), after, diff

    def _verify_restore(
        self,
        resources: Mapping[str, RelationalSUT],
    ) -> tuple[RestoreFidelity, StateImage]:
        restored: dict[str, StateImage] = {}
        fidelities: dict[str, RestoreFidelity] = {}
        expected_baseline = self._fixture.expectations.baseline_state_image_digest

        for label, resource in resources.items():
            backend = self._backend_by_label[label]
            resource.reset()
            snapshot = resource.snapshot()
            backend.fixture_control.replace_relations_atomically(
                resource,
                self._fixture.epoch_mutation_mapping(),
            )
            fidelity = resource.restore(snapshot)
            if fidelity is not RestoreFidelity.STATE_EQUIVALENT:
                raise RelationalParityError(
                    f"{label} restore fidelity is {fidelity.value}, "
                    "expected STATE_EQUIVALENT"
                )
            state = resource.state_image()
            self._require_equal(
                f"{label} restored StateImage digest",
                state.digest,
                expected_baseline,
            )
            fidelities[label] = fidelity
            restored[label] = state

        if len(set(fidelities.values())) != 1:
            raise RelationalParityError(
                "paired backends reported different restore fidelity"
            )
        return (
            next(iter(fidelities.values())),
            self._require_canonical_state_parity("restored StateImage", restored),
        )

    def _verify_reset(
        self,
        resources: Mapping[str, RelationalSUT],
    ) -> StateImage:
        observed: dict[str, StateImage] = {}
        expected = self._fixture.expectations.baseline_state_image_digest
        for label, resource in resources.items():
            backend = self._backend_by_label[label]
            backend.fixture_control.replace_relations_atomically(
                resource,
                self._fixture.epoch_mutation_mapping(),
            )
            state = resource.reset()
            self._require_equal(
                f"{label} reset StateImage digest",
                state.digest,
                expected,
            )
            observed[label] = state
        return self._require_canonical_state_parity("reset StateImage", observed)

    @staticmethod
    def _epochs(document: Mapping[str, object]) -> tuple[str, str]:
        relations = document.get("relations")
        if not isinstance(relations, list) or len(relations) != 2:
            raise RelationalParityError(
                "consistency projection must contain exactly two relations"
            )
        values: list[str] = []
        for relation in relations:
            if not isinstance(relation, dict):
                raise RelationalParityError(
                    "consistency projection relation is malformed"
                )
            rows = relation.get("rows")
            if (
                not isinstance(rows, list)
                or len(rows) != 1
                or not isinstance(rows[0], dict)
            ):
                raise RelationalParityError(
                    "consistency projection must contain one row per relation"
                )
            row_values = rows[0].get("values")
            if not isinstance(row_values, dict):
                raise RelationalParityError(
                    "consistency projection values are malformed"
                )
            epoch = row_values.get("epoch")
            if not isinstance(epoch, dict) or not isinstance(epoch.get("value"), str):
                raise RelationalParityError(
                    "consistency projection epoch is malformed"
                )
            values.append(epoch["value"])
        return values[0], values[1]

    def _require_canonical_state_parity(
        self,
        context: str,
        observed: Mapping[str, StateImage],
    ) -> StateImage:
        documents = {
            label: state.as_document()
            for label, state in observed.items()
        }
        self._require_canonical_document_parity(context, documents)
        return next(iter(observed.values()))

    def _require_canonical_diff_parity(
        self,
        context: str,
        observed: Mapping[str, RelationalDiff],
    ) -> RelationalDiff:
        documents = {
            label: value.as_document()
            for label, value in observed.items()
        }
        self._require_canonical_document_parity(context, documents)
        return next(iter(observed.values()))

    @staticmethod
    def _require_canonical_document_parity(
        context: str,
        observed: Mapping[str, object],
    ) -> None:
        encoded = {
            label: canonical_json(document).encode("utf-8")
            for label, document in observed.items()
        }
        values = tuple(encoded.values())
        if not values or any(value != values[0] for value in values[1:]):
            summaries = {
                label: digest(document)
                for label, document in observed.items()
            }
            raise RelationalParityError(
                f"{context} canonical bytes differ across backends: {summaries}"
            )

    @staticmethod
    def _require_equal(context: str, observed: object, expected: object) -> None:
        if observed != expected:
            raise RelationalParityError(
                f"{context} mismatch: observed {observed!r}, expected {expected!r}"
            )

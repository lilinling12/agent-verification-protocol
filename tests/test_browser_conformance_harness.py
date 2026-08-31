from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import pytest

from avp_ref.environment.models import RestoreEquivalence, SnapshotRef
from avp_ref.tck_adapter.browser_harness import (
    BrowserCanonicalizationError,
    BrowserConformanceHarness,
    BrowserSettlementError,
    BrowserSettlementLedger,
    BrowserVerificationError,
    MaterializedBrowserFixture,
    canonical_state_image_digest,
    canonicalize_state_image,
    decode_dom_string_code_units,
    encode_dom_string_code_units,
    materialize_browser_fixture,
)
from avp_ref.tck_adapter.reference_composite import ReferenceConformanceAdapter


_BROWSER_CASE_IDS = frozenset(
    {
        "AVP-TCK-BROWSER-IDENTITY-001",
        "AVP-TCK-BROWSER-SELECTION-CANONICAL-001",
        "AVP-TCK-BROWSER-COOKIE-001",
        "AVP-TCK-BROWSER-STATE-IMAGE-001",
        "AVP-TCK-BROWSER-EXECUTION-RESIDUAL-001",
        "AVP-TCK-BROWSER-SETTLEMENT-LIFECYCLE-001",
        "AVP-TCK-BROWSER-SECURITY-001",
        "AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001",
    }
)


class _FixtureIdentityVerifier:
    def __init__(self, origins: Sequence[str]) -> None:
        self._origins = frozenset(origins)

    def verify_canonical_origin(self, origin: str) -> None:
        if origin not in self._origins:
            raise BrowserCanonicalizationError(f"fixture origin is not admitted: {origin}")

    def verify_canonical_cookie_domain(self, domain: str) -> None:
        if domain != "a.test":
            raise BrowserCanonicalizationError(f"fixture domain is not admitted: {domain}")


def _fixture_source() -> dict[str, Any]:
    path = Path("conformance/fixtures/browser-state/v0.1/fixture-source.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _materialized() -> tuple[MaterializedBrowserFixture, _FixtureIdentityVerifier]:
    origins = ("http://a.test:41001", "http://b.test:41002")
    verifier = _FixtureIdentityVerifier(origins)
    fixture = materialize_browser_fixture(
        _fixture_source(),
        resolved_origins={"primary": origins[0], "secondary": origins[1]},
        verifier=verifier,
    )
    return fixture, verifier


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return copy.deepcopy(value)


class _MemoryBrowserSUT:
    def __init__(
        self,
        fixture: MaterializedBrowserFixture,
        verifier: _FixtureIdentityVerifier,
        *,
        false_reset: bool = False,
        false_restore: bool = False,
    ) -> None:
        self.handle_id = "browser-handle-1"
        self._fixture = fixture
        self._verifier = verifier
        self._state = _thaw(fixture.baseline_image)
        self._snapshots: dict[str, dict[str, Any]] = {}
        self._counter = 0
        self._false_reset = false_reset
        self._false_restore = false_restore
        self.released = False
        self.provider_idle = False
        self.restore_eligible = True
        self.execution_conditions_valid = True

    def snapshot(self) -> SnapshotRef:
        self._counter += 1
        snapshot_id = f"snapshot-{self._counter}"
        self._snapshots[snapshot_id] = _thaw(self._state)
        return SnapshotRef(
            snapshot_id=snapshot_id,
            handle_id=self.handle_id,
            state_digest=canonical_state_image_digest(
                self._state,
                self._fixture.manifest,
                self._verifier,
            ),
            logical_time=self._counter,
            consistency="settled",
            adapter_name="test-browser",
        )

    def reset(self) -> None:
        if not self._false_reset:
            self._state = _thaw(self._fixture.baseline_image)

    def restore(self, snapshot: SnapshotRef) -> None:
        if not self._false_restore:
            self._state = _thaw(self._snapshots[snapshot.snapshot_id])

    def release(self) -> None:
        self.released = True


class _MemoryObserver:
    def project_selected_state(
        self,
        sut: _MemoryBrowserSUT,
        fixture: MaterializedBrowserFixture,
    ) -> Mapping[str, Any]:
        del fixture
        if not sut.execution_conditions_valid:
            raise BrowserVerificationError("execution input drift or excluded-state interference")
        return _thaw(sut._state)

    def verify_restore_eligibility(
        self,
        sut: _MemoryBrowserSUT,
        fixture: MaterializedBrowserFixture,
    ) -> None:
        del fixture
        if not sut.restore_eligible:
            raise BrowserVerificationError("cookie temporal restore eligibility is unresolved")


class _MemoryFixtureControl:
    def seed_baseline(self, sut: _MemoryBrowserSUT, fixture: MaterializedBrowserFixture) -> None:
        sut._state = _thaw(fixture.baseline_image)

    def seed_cookie(
        self,
        sut: _MemoryBrowserSUT,
        cookie: Mapping[str, Any],
        *,
        provenance: Mapping[str, Any] | None = None,
    ) -> None:
        del provenance
        sut._state["cookies"].append(dict(cookie))

    def seed_local_storage(
        self,
        sut: _MemoryBrowserSUT,
        origin: str,
        entries: Sequence[Mapping[str, str]],
    ) -> None:
        for origin_state in sut._state["origins"]:
            if origin_state["origin"] == origin:
                origin_state["localStorage"] = [dict(entry) for entry in entries]
                return
        raise AssertionError(f"unknown origin: {origin}")

    def seed_partitioned_cookie(self, sut: _MemoryBrowserSUT, cookie: Mapping[str, Any]) -> None:
        del sut, cookie

    def set_execution_binding(self, sut: _MemoryBrowserSUT, reference: str, identity: str) -> None:
        del reference, identity
        sut.execution_conditions_valid = False

    def set_excluded_state_interference(self, sut: _MemoryBrowserSUT, *, interfering: bool) -> None:
        sut.execution_conditions_valid = not interfering

    def seed_evaluator_private_state(self, sut: _MemoryBrowserSUT) -> None:
        del sut


class _MemoryBackend:
    def __init__(
        self,
        verifier: _FixtureIdentityVerifier,
        *,
        false_reset: bool = False,
        false_restore: bool = False,
    ) -> None:
        self._verifier = verifier
        self._control = _MemoryFixtureControl()
        self._observer = _MemoryObserver()
        self._false_reset = false_reset
        self._false_restore = false_restore

    @property
    def observer(self) -> _MemoryObserver:
        return self._observer

    @property
    def fixture_control(self) -> _MemoryFixtureControl:
        return self._control

    def provision(self, fixture: MaterializedBrowserFixture) -> _MemoryBrowserSUT:
        return _MemoryBrowserSUT(
            fixture,
            self._verifier,
            false_reset=self._false_reset,
            false_restore=self._false_restore,
        )


def _settled() -> BrowserSettlementLedger:
    ledger = BrowserSettlementLedger()
    ledger.close_subject_admission()
    return ledger


def test_domstring_code_units_are_lossless_and_canonical() -> None:
    assert encode_dom_string_code_units([0x0061]) == "AGE"
    assert encode_dom_string_code_units([0x0061, 0x0062]) == "AGEAYg"
    assert encode_dom_string_code_units([0xD800]) == "2AA"
    assert decode_dom_string_code_units("2AA") == (0xD800,)

    for invalid in ("AA", "AAA", "AAA=", "AAB"):
        with pytest.raises(BrowserCanonicalizationError):
            decode_dom_string_code_units(invalid)


def test_fixture_materialization_resolves_and_freezes_exact_origins() -> None:
    fixture, _ = _materialized()
    assert fixture.manifest["localStorageOrigins"] == (
        "http://a.test:41001",
        "http://b.test:41002",
    )
    assert fixture.baseline_image["origins"][1]["localStorage"] == ()
    assert fixture.manifest_digest.startswith("sha256:")
    assert fixture.baseline_image_digest.startswith("sha256:")

    with pytest.raises(TypeError):
        fixture.manifest["profile"] = "changed"  # type: ignore[index]


def test_fixture_materialization_fails_closed_for_unresolved_or_duplicate_slots() -> None:
    source = _fixture_source()
    verifier = _FixtureIdentityVerifier(("http://a.test:41001", "http://b.test:41002"))

    with pytest.raises(BrowserCanonicalizationError):
        materialize_browser_fixture(
            source,
            resolved_origins={"primary": "http://a.test:41001"},
            verifier=verifier,
        )

    with pytest.raises(BrowserCanonicalizationError):
        materialize_browser_fixture(
            source,
            resolved_origins={
                "primary": "http://a.test:41001",
                "secondary": "http://a.test:41001",
            },
            verifier=verifier,
        )


def test_canonical_state_identity_is_independent_of_observation_enumeration() -> None:
    fixture, verifier = _materialized()
    first = _thaw(fixture.baseline_image)
    second = _thaw(fixture.baseline_image)
    second["origins"].reverse()
    second["cookies"].reverse()
    second["origins"][1]["localStorage"].reverse()

    first_canonical = canonicalize_state_image(first, fixture.manifest, verifier)
    second_canonical = canonicalize_state_image(second, fixture.manifest, verifier)
    assert first_canonical == second_canonical
    assert canonical_state_image_digest(first, fixture.manifest, verifier) == fixture.baseline_image_digest
    assert canonical_state_image_digest(second, fixture.manifest, verifier) == fixture.baseline_image_digest


def test_positive_settlement_rejects_provider_idle_while_mutation_is_unresolved() -> None:
    fixture, verifier = _materialized()
    backend = _MemoryBackend(verifier)
    harness = BrowserConformanceHarness(backend, fixture, verifier)
    sut = harness.provision()
    ledger = BrowserSettlementLedger()
    ledger.accept_relevant_mutation("local-storage-write")
    ledger.close_subject_admission()
    sut.provider_idle = True

    with pytest.raises(BrowserSettlementError):
        harness.authoritative_projection(sut, ledger)

    ledger.mark_terminal("local-storage-write")
    assert harness.authoritative_projection(sut, ledger).digest == fixture.baseline_image_digest

    with pytest.raises(BrowserSettlementError):
        ledger.accept_relevant_mutation("after-close")


def test_snapshot_reset_restore_are_verified_by_independent_reprojection() -> None:
    fixture, verifier = _materialized()
    backend = _MemoryBackend(verifier)
    harness = BrowserConformanceHarness(backend, fixture, verifier)
    sut = harness.provision()
    settled = _settled()

    snapshot = harness.verified_snapshot(sut, settled)
    control = harness.fixture_control
    mutated = _thaw(fixture.baseline_image["cookies"][0])
    mutated["value"] = "mutated"
    sut._state["cookies"][0] = mutated

    reset_result = harness.verified_reset(sut, settled, _settled())
    assert reset_result.equivalent_to_initial is True
    assert reset_result.after_digest == fixture.baseline_image_digest

    sut._state["cookies"][0]["value"] = "again"
    restore_result = harness.verified_restore(sut, snapshot, settled, _settled())
    assert restore_result.equivalence is RestoreEquivalence.STATE_EQUIVALENT
    assert restore_result.after_digest == snapshot.state_digest
    assert not hasattr(sut, "seed_cookie")
    assert hasattr(control, "seed_cookie")


def test_false_reset_and_false_restore_success_are_rejected() -> None:
    fixture, verifier = _materialized()

    reset_harness = BrowserConformanceHarness(
        _MemoryBackend(verifier, false_reset=True), fixture, verifier
    )
    reset_sut = reset_harness.provision()
    reset_sut._state["cookies"][0]["value"] = "mutated"
    with pytest.raises(BrowserVerificationError):
        reset_harness.verified_reset(reset_sut, _settled(), _settled())

    restore_harness = BrowserConformanceHarness(
        _MemoryBackend(verifier, false_restore=True), fixture, verifier
    )
    restore_sut = restore_harness.provision()
    snapshot = restore_harness.verified_snapshot(restore_sut, _settled())
    restore_sut._state["cookies"][0]["value"] = "mutated"
    with pytest.raises(BrowserVerificationError):
        restore_harness.verified_restore(restore_sut, snapshot, _settled(), _settled())


def test_foreign_snapshot_and_temporally_ineligible_restore_fail_closed() -> None:
    fixture, verifier = _materialized()
    harness = BrowserConformanceHarness(_MemoryBackend(verifier), fixture, verifier)
    sut = harness.provision()
    snapshot = harness.verified_snapshot(sut, _settled())

    foreign = SnapshotRef(
        snapshot_id=snapshot.snapshot_id,
        handle_id="other-browser",
        state_digest=snapshot.state_digest,
        logical_time=snapshot.logical_time,
        consistency=snapshot.consistency,
        adapter_name=snapshot.adapter_name,
    )
    with pytest.raises(BrowserVerificationError):
        harness.verified_restore(sut, foreign, _settled(), _settled())

    sut.restore_eligible = False
    with pytest.raises(BrowserVerificationError):
        harness.verified_restore(sut, snapshot, _settled(), _settled())


def test_execution_condition_drift_is_rejected_before_authoritative_projection() -> None:
    fixture, verifier = _materialized()
    backend = _MemoryBackend(verifier)
    harness = BrowserConformanceHarness(backend, fixture, verifier)
    sut = harness.provision()
    backend.fixture_control.set_excluded_state_interference(sut, interfering=True)

    with pytest.raises(BrowserVerificationError):
        harness.authoritative_projection(sut, _settled())


def test_reference_profile_support_remains_atomic_and_pending() -> None:
    supported = ReferenceConformanceAdapter().supported_case_ids
    assert supported.isdisjoint(_BROWSER_CASE_IDS)

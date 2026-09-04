"""Unit checks for the project-local pinned-Toxiproxy transport qualification."""

from __future__ import annotations

import unittest

from acceptance.network_control.evidence_core import ArtifactRef, InitiationFacts
from acceptance.network_control.portable_comparator import AttemptObservation
from acceptance.network_control.toxiproxy_binding import ToxiproxyControlError
from acceptance.network_control.toxiproxy_evidence import PhaseExecution
from acceptance.network_control.toxiproxy_transport_qualification import (
    _require_successful_exchange,
    _require_timeout_cut,
)


def _facts(channel: str, *, total: int = 1, expected: int = 1) -> InitiationFacts:
    return InitiationFacts(
        channel=channel,
        total_initiations=total,
        expected_target_initiations=expected,
        alternate_target_initiations=0,
        raw_syn_packets=total,
        retransmitted_syn_packets=0,
    )


def _ref(role: str, marker: str) -> ArtifactRef:
    return ArtifactRef(sha256=marker * 64, size=1, logical_role=role)


def _execution(
    phase: str,
    *,
    completed: bool,
    expired: bool,
    fixture: bool,
    total: int = 1,
) -> PhaseExecution:
    refs = [_ref(f"exchange-diagnostic-{phase}", "a")]
    if fixture:
        refs.append(_ref(f"fixture-exchange-{phase}", "b"))
    return PhaseExecution(
        observation=AttemptObservation(
            phase_id=phase,
            path_id="selected-path",
            attempt_id=f"attempt-{phase}",
            completed=completed,
            mismatch_observed=False,
            observation_budget_expired=expired,
            front_initiations=_facts("W-front", total=total, expected=total),
            upstream_initiations=_facts("W-upstream", total=total, expected=total),
        ),
        evidence_refs=tuple(refs),
    )


class ToxiproxyTransportQualificationPredicateTests(unittest.TestCase):
    def test_pass_through_requires_completed_exact_exchange_and_evidence(self) -> None:
        execution = _execution("baseline", completed=True, expired=False, fixture=True)
        _require_successful_exchange("baseline", execution)

    def test_pass_through_without_fixture_evidence_fails_closed(self) -> None:
        execution = _execution("baseline", completed=True, expired=False, fixture=False)
        with self.assertRaisesRegex(ToxiproxyControlError, "evidence refs are incomplete"):
            _require_successful_exchange("baseline", execution)

    def test_timeout_zero_cut_requires_evaluator_budget_expiry(self) -> None:
        execution = _execution("subject-active-cut", completed=False, expired=True, fixture=False)
        _require_timeout_cut("subject-active-cut", execution)

    def test_cut_that_ends_before_budget_expiry_is_not_qualified(self) -> None:
        execution = _execution("subject-active-cut", completed=False, expired=False, fixture=False)
        with self.assertRaisesRegex(ToxiproxyControlError, "before evaluator budget expiry"):
            _require_timeout_cut("subject-active-cut", execution)

    def test_hidden_second_initiation_is_rejected_by_qualification(self) -> None:
        execution = _execution("baseline", completed=True, expired=False, fixture=True, total=2)
        with self.assertRaisesRegex(ToxiproxyControlError, "initiation evidence is not exact"):
            _require_successful_exchange("baseline", execution)


if __name__ == "__main__":
    unittest.main()

"""Regression tests for canonical trusted TEL-002 attempt evidence retention."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from acceptance.network_control.evidence_core import ArtifactStore, InitiationFacts, MaterializedEndpoint
from acceptance.network_control.portable_comparator import AttemptObservation
from acceptance.network_control.toxiproxy_evidence import PhaseExecution
from acceptance.network_control.verified_live_labs import (
    _ReviewedAttemptEvidenceBinding,
    fixture_integrity_problem,
)


def _facts(channel: str) -> InitiationFacts:
    return InitiationFacts(
        channel=channel,
        total_initiations=1,
        expected_target_initiations=1,
        alternate_target_initiations=0,
        raw_syn_packets=1,
        retransmitted_syn_packets=0,
    )


def _observation(*, completed: bool) -> AttemptObservation:
    return AttemptObservation(
        phase_id="baseline",
        path_id="selected-path",
        attempt_id="attempt-001",
        completed=completed,
        mismatch_observed=False,
        observation_budget_expired=not completed,
        front_initiations=_facts("W-front"),
        upstream_initiations=_facts("W-upstream"),
    )


class FixtureIntegrityProblemTests(unittest.TestCase):
    def test_exact_completed_fixture_event_is_accepted(self) -> None:
        self.assertIsNone(
            fixture_integrity_problem(
                {
                    "ok": True,
                    "op": "event",
                    "event": {
                        "requestValid": True,
                        "responseEmitted": True,
                        "problem": None,
                    },
                }
            )
        )

    def test_trailing_request_bytes_invalidate_completed_exchange(self) -> None:
        self.assertEqual(
            fixture_integrity_problem(
                {
                    "ok": True,
                    "op": "event",
                    "event": {
                        "requestValid": False,
                        "responseEmitted": True,
                        "problem": "request-has-trailing-bytes",
                    },
                }
            ),
            "fixture-evidence:request-has-trailing-bytes",
        )

    def test_missing_or_malformed_fixture_event_fails_closed(self) -> None:
        self.assertEqual(fixture_integrity_problem([]), "fixture-evidence:not-object")
        self.assertEqual(fixture_integrity_problem({"ok": True}), "fixture-evidence:event-missing")


class _BaseAttemptLab:
    def __init__(self, store: ArtifactStore, *, completed: bool, fixture_document: dict[str, Any] | None) -> None:
        self.artifact_store = store
        self.completed = completed
        self.fixture_document = fixture_document
        self._selected_fixture = None
        self._control_fixture = None

    def _execute_role_exchange(
        self,
        *,
        container_name: str,
        endpoint: MaterializedEndpoint,
        attempt_document: dict[str, object],
        extra_connect: bool,
    ) -> dict[str, object]:
        del container_name, endpoint, attempt_document, extra_connect
        return {
            "attemptId": "attempt-001",
            "completed": self.completed,
            "mismatchObserved": False,
            "observationBudgetExpired": not self.completed,
            "elapsedNs": 123456,
            "responseSize": 4 if self.completed else 0,
            "responseSha256": "diagnostic-sha" if self.completed else None,
            "nativeError": None,
        }

    def certified_attempt(self, phase_id: str, privileged: bool, negative_mode: object) -> PhaseExecution:
        del privileged, negative_mode
        exchange = self._execute_role_exchange(
            container_name="subject",
            endpoint=MaterializedEndpoint(
                family="ipv4",
                address="127.0.0.1",
                port=41001,
                role="subject-destination",
            ),
            attempt_document={"phaseId": phase_id, "attemptId": "attempt-001"},
            extra_connect=False,
        )
        refs = []
        if bool(exchange["completed"]) and self.fixture_document is not None:
            refs.append(
                self.artifact_store.put_bytes(
                    json.dumps(self.fixture_document, sort_keys=True, separators=(",", ":")).encode("utf-8"),
                    logical_role=f"fixture-exchange-{phase_id}",
                )
            )
        return PhaseExecution(observation=_observation(completed=bool(exchange["completed"])), evidence_refs=tuple(refs))


class _ReviewedAttemptLab(_ReviewedAttemptEvidenceBinding, _BaseAttemptLab):
    pass


class ReviewedAttemptEvidenceTests(unittest.TestCase):
    def test_incomplete_exchange_retains_diagnostic_ref_without_inventing_fixture_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ArtifactStore(Path(temporary))
            lab = _ReviewedAttemptLab(store, completed=False, fixture_document=None)
            execution = lab.certified_attempt("baseline", False, None)

            self.assertFalse(execution.observation.completed)
            self.assertEqual(execution.observation.validity_problems, ())
            diagnostic = [
                ref for ref in execution.evidence_refs if ref.logical_role == "exchange-diagnostic-baseline"
            ]
            self.assertEqual(len(diagnostic), 1)
            document = json.loads(store.read_verified(diagnostic[0]))
            self.assertEqual(document["elapsedNs"], 123456)
            self.assertEqual(document["responseSize"], 0)
            self.assertTrue(document["observationBudgetExpired"])

    def test_completed_exchange_with_trailing_fixture_bytes_is_evidence_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ArtifactStore(Path(temporary))
            fixture = {
                "ok": True,
                "op": "event",
                "event": {
                    "requestValid": False,
                    "responseEmitted": True,
                    "problem": "request-has-trailing-bytes",
                },
            }
            lab = _ReviewedAttemptLab(store, completed=True, fixture_document=fixture)
            execution = lab.certified_attempt("baseline", False, None)

            self.assertTrue(execution.observation.completed)
            self.assertIn(
                "fixture-evidence:request-has-trailing-bytes",
                execution.observation.validity_problems,
            )
            roles = {ref.logical_role for ref in execution.evidence_refs}
            self.assertIn("fixture-exchange-baseline", roles)
            self.assertIn("exchange-diagnostic-baseline", roles)

    def test_completed_exchange_without_fixture_event_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            lab = _ReviewedAttemptLab(
                ArtifactStore(Path(temporary)),
                completed=True,
                fixture_document=None,
            )
            execution = lab.certified_attempt("baseline", False, None)
            self.assertIn(
                "fixture-evidence:completed-exchange-missing-exact-event",
                execution.observation.validity_problems,
            )


if __name__ == "__main__":
    unittest.main()

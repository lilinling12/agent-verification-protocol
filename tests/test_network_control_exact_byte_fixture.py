"""TEL-001 deterministic fixture and single-initiation client tests."""

from __future__ import annotations

import dataclasses
import errno
import unittest
from unittest import mock

from acceptance.network_control.attempt_client import execute_exact_exchange
from acceptance.network_control.evidence_core import AttemptFactory
from acceptance.network_control.fixture import ExactByteFixture
from test_network_control_evidence_core import plan


class ExactByteFixtureTests(unittest.TestCase):
    def test_exact_exchange_completes_with_fresh_client_socket(self) -> None:
        with ExactByteFixture() as fixture:
            evidence_plan = dataclasses.replace(
                plan(),
                subject_destination=dataclasses.replace(fixture.endpoint, role="subject-destination"),
                upstream_fixture=fixture.endpoint,
            )
            attempt = AttemptFactory(b"A" * 32).issue(evidence_plan, phase_id="baseline", ordinal=0)
            fixture.arm(attempt)
            observation = execute_exact_exchange(
                evidence_plan.subject_destination,
                attempt,
                observation_budget_ns=evidence_plan.observation_budget_ns,
            )
            fixture.disarm(attempt.attempt_id)

            self.assertTrue(observation.completed)
            self.assertFalse(observation.mismatch_observed)
            events = fixture.events()
            self.assertEqual(len(events), 1)
            self.assertTrue(events[0].request_valid)
            self.assertTrue(events[0].response_emitted)
            self.assertEqual(events[0].attempt_id, attempt.attempt_id)
            self.assertIsNone(fixture.fatal_problem)

    def test_stale_request_cannot_satisfy_later_attempt(self) -> None:
        with ExactByteFixture() as fixture:
            evidence_plan = dataclasses.replace(
                plan(),
                subject_destination=dataclasses.replace(fixture.endpoint, role="subject-destination"),
                upstream_fixture=fixture.endpoint,
                observation_budget_ns=300_000_000,
            )
            factory = AttemptFactory(b"B" * 32)
            stale = factory.issue(evidence_plan, phase_id="baseline", ordinal=0)
            current = factory.issue(evidence_plan, phase_id="pre-trigger", ordinal=1)
            fixture.arm(current)
            observation = execute_exact_exchange(
                evidence_plan.subject_destination,
                current,
                observation_budget_ns=evidence_plan.observation_budget_ns,
                request_override=stale.request_bytes,
            )
            fixture.disarm(current.attempt_id)

            self.assertFalse(observation.completed)
            events = fixture.events()
            self.assertEqual(len(events), 1)
            self.assertFalse(events[0].request_valid)
            self.assertFalse(events[0].response_emitted)
            self.assertEqual(events[0].problem, "request-byte-mismatch")

    def test_attempt_client_does_not_retry_failed_connect(self) -> None:
        class CountingSocket:
            instances = 0
            connect_calls = 0

            def __init__(self, family: int, kind: int) -> None:
                del family, kind
                CountingSocket.instances += 1

            def setblocking(self, flag: bool) -> None:
                del flag

            def fileno(self) -> int:
                return 10_000 + CountingSocket.instances

            def connect_ex(self, address: object) -> int:
                del address
                CountingSocket.connect_calls += 1
                return errno.ECONNREFUSED

            def close(self) -> None:
                return

        class FakeSelector:
            def register(self, fileobj: object, events: int) -> None:
                del fileobj, events

            def modify(self, fileobj: object, events: int) -> None:
                del fileobj, events

            def select(self, timeout: float | None = None) -> list[tuple[object, int]]:
                del timeout
                return []

            def close(self) -> None:
                return

        attempt = AttemptFactory(b"C" * 32).issue(plan(), phase_id="baseline", ordinal=0)
        with mock.patch(
            "acceptance.network_control.attempt_client.selectors.DefaultSelector",
            FakeSelector,
        ):
            observation = execute_exact_exchange(
                plan().subject_destination,
                attempt,
                observation_budget_ns=100_000_000,
                socket_factory=CountingSocket,
            )
        self.assertFalse(observation.completed)
        self.assertEqual(CountingSocket.instances, 1)
        self.assertEqual(CountingSocket.connect_calls, 1)


if __name__ == "__main__":
    unittest.main()

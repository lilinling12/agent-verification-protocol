"""TEL-001 deterministic fixture and single-initiation client tests."""

from __future__ import annotations

import dataclasses
import errno
import unittest
from unittest import mock

from acceptance.network_control.attempt_client import execute_exact_exchange
from acceptance.network_control.evidence_core import AttemptFactory, EvidenceMaterializationError
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
            event = fixture.wait_for_event(attempt.attempt_id)
            fixture.disarm(attempt.attempt_id)

            self.assertTrue(observation.completed)
            self.assertFalse(observation.mismatch_observed)
            self.assertTrue(event.request_valid)
            self.assertTrue(event.response_emitted)
            self.assertEqual(event.attempt_id, attempt.attempt_id)
            self.assertEqual(fixture.events(), (event,))
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
            event = fixture.wait_for_event(current.attempt_id)
            fixture.disarm(current.attempt_id)

            self.assertFalse(observation.completed)
            self.assertFalse(event.request_valid)
            self.assertFalse(event.response_emitted)
            self.assertEqual(event.problem, "request-byte-mismatch")

    def test_trailing_request_bytes_are_rejected(self) -> None:
        with ExactByteFixture() as fixture:
            evidence_plan = dataclasses.replace(
                plan(),
                subject_destination=dataclasses.replace(fixture.endpoint, role="subject-destination"),
                upstream_fixture=fixture.endpoint,
                observation_budget_ns=300_000_000,
            )
            attempt = AttemptFactory(b"T" * 32).issue(evidence_plan, phase_id="baseline", ordinal=0)
            fixture.arm(attempt)
            observation = execute_exact_exchange(
                evidence_plan.subject_destination,
                attempt,
                observation_budget_ns=evidence_plan.observation_budget_ns,
                request_override=attempt.request_bytes + b"EXTRA",
            )
            event = fixture.wait_for_event(attempt.attempt_id)
            fixture.disarm(attempt.attempt_id)

            self.assertFalse(observation.completed)
            self.assertEqual(event.problem, "request-has-trailing-bytes")
            self.assertFalse(event.response_emitted)

    def test_event_barrier_rejects_invalid_timeout(self) -> None:
        with ExactByteFixture() as fixture:
            with self.assertRaises(EvidenceMaterializationError):
                fixture.wait_for_event("attempt", timeout_s=0)

    def test_event_barrier_is_bounded_when_attempt_has_no_connection(self) -> None:
        with ExactByteFixture(hygiene_timeout_s=0.05) as fixture:
            with self.assertRaises(TimeoutError):
                fixture.wait_for_event("attempt-never-connected")

    def test_shutdown_failure_is_diagnostic_and_does_not_retry(self) -> None:
        class ShutdownFailSocket:
            connect_calls = 0

            def __init__(self, family: int, kind: int) -> None:
                del family, kind

            def setblocking(self, flag: bool) -> None:
                del flag

            def fileno(self) -> int:
                return 10001

            def connect_ex(self, address: object) -> int:
                del address
                ShutdownFailSocket.connect_calls += 1
                return 0

            def send(self, view: memoryview) -> int:
                return len(view)

            def shutdown(self, how: int) -> None:
                del how
                raise OSError(errno.ENOTCONN, "not connected")

            def close(self) -> None:
                return

        class ReadySelector:
            def register(self, fileobj: object, events: int) -> None:
                del fileobj, events

            def modify(self, fileobj: object, events: int) -> None:
                del fileobj, events

            def select(self, timeout: float | None = None) -> list[tuple[object, int]]:
                del timeout
                return [(object(), 2)]

            def close(self) -> None:
                return

        attempt = AttemptFactory(b"D" * 32).issue(plan(), phase_id="baseline", ordinal=0)
        with mock.patch(
            "acceptance.network_control.attempt_client.selectors.DefaultSelector",
            ReadySelector,
        ):
            observation = execute_exact_exchange(
                plan().subject_destination,
                attempt,
                observation_budget_ns=100_000_000,
                socket_factory=ShutdownFailSocket,
            )
        self.assertFalse(observation.completed)
        self.assertIn("OSError", observation.native_error or "")
        self.assertEqual(ShutdownFailSocket.connect_calls, 1)

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

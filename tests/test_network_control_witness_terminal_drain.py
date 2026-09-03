"""Regression tests for the Linux witness terminal-drain boundary."""

from __future__ import annotations

import unittest

from acceptance.network_control.evidence_core import MaterializedEndpoint
from acceptance.network_control.tcp_packets import build_synthetic_syn_frame
from acceptance.network_control.witness import LinuxSynWitness
from acceptance.network_control.witness_evidence import CaptureAssurance, WitnessScope


class _QueuedCapture:
    def __init__(self, events: list[object]) -> None:
        self.events = list(events)
        self.recv_calls = 0

    def recvfrom(self, _size: int) -> tuple[bytes, object]:
        self.recv_calls += 1
        if not self.events:
            raise AssertionError("capture loop read beyond deterministic terminal drain")
        event = self.events.pop(0)
        if isinstance(event, BaseException):
            raise event
        assert isinstance(event, tuple)
        return event  # type: ignore[return-value]


class LinuxSynWitnessTerminalDrainTests(unittest.TestCase):
    def _witness(self) -> LinuxSynWitness:
        scope = WitnessScope(
            channel="W-front",
            role_id="subject",
            source_addresses=("10.0.0.2",),
            expected_target=MaterializedEndpoint(
                family="ipv4",
                address="10.0.0.3",
                port=43001,
                role="subject-destination",
            ),
        )
        witness = LinuxSynWitness(
            interface_name="eth0",
            scopes=(scope,),
            assurance=CaptureAssurance(
                egress_coverage_verified=True,
                directionality_verified=True,
                offload_normalization_verified=True,
                pre_syn_connect_gap_closed=True,
            ),
        )
        witness._attempt_id = "attempt-terminal-drain"  # noqa: SLF001
        witness._interface_index = 7  # noqa: SLF001
        witness._admitted = True  # noqa: SLF001
        return witness

    def test_frame_already_queued_when_close_signal_arrives_is_retained(self) -> None:
        frame = build_synthetic_syn_frame(
            source_address="10.0.0.2",
            destination_address="10.0.0.3",
            source_port=51000,
            destination_port=43001,
            sequence=1234,
        )
        capture = _QueuedCapture(
            [
                (frame, ("eth0", 0, 4)),
                TimeoutError(),
            ]
        )
        witness = self._witness()
        witness._socket = capture  # type: ignore[assignment]  # noqa: SLF001
        witness._stop.set()  # noqa: SLF001

        witness._capture_loop()  # noqa: SLF001

        self.assertEqual(capture.recv_calls, 2)
        self.assertEqual(len(witness._observations), 1)  # noqa: SLF001
        observation = witness._observations[0]  # noqa: SLF001
        self.assertEqual(observation.destination_address, "10.0.0.3")
        self.assertEqual(observation.destination_port, 43001)

    def test_terminal_drain_ends_on_first_bounded_receive_inactivity(self) -> None:
        capture = _QueuedCapture([TimeoutError()])
        witness = self._witness()
        witness._socket = capture  # type: ignore[assignment]  # noqa: SLF001
        witness._stop.set()  # noqa: SLF001

        witness._capture_loop()  # noqa: SLF001

        self.assertEqual(capture.recv_calls, 1)
        self.assertEqual(witness._observations, [])  # noqa: SLF001

    def test_multiple_queued_syns_are_drained_before_inactivity_boundary(self) -> None:
        first = build_synthetic_syn_frame(
            source_address="10.0.0.2",
            destination_address="10.0.0.3",
            source_port=51000,
            destination_port=43001,
            sequence=1234,
        )
        second = build_synthetic_syn_frame(
            source_address="10.0.0.2",
            destination_address="10.0.0.3",
            source_port=51001,
            destination_port=43001,
            sequence=5678,
        )
        capture = _QueuedCapture(
            [
                (first, ("eth0", 0, 4)),
                (second, ("eth0", 0, 4)),
                TimeoutError(),
            ]
        )
        witness = self._witness()
        witness._socket = capture  # type: ignore[assignment]  # noqa: SLF001
        witness._stop.set()  # noqa: SLF001

        witness._capture_loop()  # noqa: SLF001

        self.assertEqual(capture.recv_calls, 3)
        self.assertEqual(len(witness._observations), 2)  # noqa: SLF001
        self.assertEqual(
            {item.source_port for item in witness._observations},  # noqa: SLF001
            {51000, 51001},
        )


if __name__ == "__main__":
    unittest.main()

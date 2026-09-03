"""Concrete Linux AF_PACKET collector for TEL-001 initiation evidence."""

from __future__ import annotations

import hashlib
import socket
import struct
import sys
import threading
import time

from .evidence_core import ArtifactStore
from .tcp_packets import PacketParseError, parse_initial_syn
from .witness_evidence import (
    CaptureAssurance,
    RawFrameRecord,
    TcpSynObservation,
    WitnessResult,
    WitnessScope,
    capture_integrity_problems,
    normalize_channel,
    scope_for_source,
    serialize_raw_witness,
)

_ETH_P_ALL = 0x0003
_PACKET_OUTGOING = getattr(socket, "PACKET_OUTGOING", 4)
_SOL_PACKET = 263
_PACKET_STATISTICS = 6


class WitnessPrerequisiteError(RuntimeError):
    """Raised when a controlled Linux packet boundary cannot be established."""


class LinuxSynWitness:
    """One-shot collector for one isolated role-boundary attempt window.

    It intentionally installs no target-only filter: every initial SYN from the
    declared role addresses remains visible, including alternate destinations.
    A new instance is required for every certified attempt.
    """

    def __init__(
        self,
        *,
        interface_name: str,
        scopes: tuple[WitnessScope, ...],
        assurance: CaptureAssurance,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        if not interface_name or not scopes:
            raise ValueError("interface and at least one witness scope are required")
        all_addresses = [address for scope in scopes for address in scope.source_addresses]
        if len(set(all_addresses)) != len(all_addresses):
            raise ValueError("role source addresses cannot overlap across witness scopes")
        self.interface_name = interface_name
        self.scopes = scopes
        self.assurance = assurance
        self.artifact_store = artifact_store
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._lock = threading.Lock()
        self._attempt_id: str | None = None
        self._admitted = False
        self._interface_index: int | None = None
        self._raw: list[RawFrameRecord] = []
        self._observations: list[TcpSynObservation] = []
        self._problems: list[str] = []
        self._capture_packets: int | None = None
        self._capture_drops: int | None = None

    def arm(self, attempt_id: str) -> None:
        if self._thread is not None or self._socket is not None:
            raise RuntimeError("witness is already armed")
        if not attempt_id:
            raise ValueError("attempt id must be non-empty")
        if not sys.platform.startswith("linux") or not hasattr(socket, "AF_PACKET"):
            raise WitnessPrerequisiteError("TEL-001 live transport witness requires Linux AF_PACKET")
        try:
            index = socket.if_nametoindex(self.interface_name)
            capture = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(_ETH_P_ALL))
            capture.bind((self.interface_name, 0))
            capture.settimeout(0.1)
        except PermissionError as exc:
            raise WitnessPrerequisiteError(
                "TEL-001 live witness requires CAP_NET_RAW or equivalent packet-observation authority"
            ) from exc
        except OSError as exc:
            raise WitnessPrerequisiteError("cannot establish reviewed AF_PACKET witness boundary") from exc
        self._attempt_id = attempt_id
        self._interface_index = index
        self._socket = capture
        self._thread = threading.Thread(target=self._capture_loop, name="avp-network-syn-witness", daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=2.0):
            self._close_socket()
            raise WitnessPrerequisiteError("witness did not reach arm/readiness barrier")

    def admit(self, attempt_id: str) -> None:
        if self._attempt_id != attempt_id or not self._ready.is_set():
            raise RuntimeError("attempt admission is forbidden before witness arm acknowledgement")
        with self._lock:
            if self._admitted:
                raise RuntimeError("attempt has already been admitted")
            self._admitted = True

    def close(self, attempt_id: str) -> WitnessResult:
        if self._attempt_id != attempt_id:
            raise RuntimeError("cannot close a witness window for another attempt")
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            if self._thread.is_alive():
                self._add_problem("capture-thread-did-not-stop")
        self._read_capture_statistics()
        try:
            closing_index = socket.if_nametoindex(self.interface_name)
        except OSError:
            closing_index = None
        with self._lock:
            admitted = self._admitted
        for problem in capture_integrity_problems(
            assurance=self.assurance,
            admitted=admitted,
            armed_interface_index=self._interface_index,
            closing_interface_index=closing_index,
            capture_drops=self._capture_drops,
        ):
            self._add_problem(problem)

        raw_bytes = serialize_raw_witness(
            attempt_id=attempt_id,
            records=tuple(self._raw),
            observations=tuple(self._observations),
            validity_problems=tuple(self._problems),
            capture_packets=self._capture_packets,
            capture_drops=self._capture_drops,
        )
        raw_ref = None
        if self.artifact_store is not None:
            raw_ref = self.artifact_store.put_bytes(raw_bytes, logical_role="transport-witness-raw")
        facts = tuple(
            normalize_channel(
                scope,
                (item for item in self._observations if item.channel == scope.channel),
                global_validity_problems=tuple(self._problems),
            )
            for scope in self.scopes
        )
        result = WitnessResult(
            attempt_id=attempt_id,
            channel_facts=facts,
            validity_problems=tuple(self._problems),
            raw_artifact_ref=raw_ref,
            raw_artifact_bytes=raw_bytes,
            capture_packets=self._capture_packets,
            capture_drops=self._capture_drops,
        )
        self._close_socket()
        return result

    def _capture_loop(self) -> None:
        self._ready.set()
        capture = self._socket
        assert capture is not None
        # ``close()`` marks the evaluator's terminal boundary, but that signal can
        # race with a SYN that the kernel has already queued for this AF_PACKET
        # socket. Exiting merely because ``_stop`` is set can therefore undercount
        # a real initiation. After the terminal signal, keep consuming frames until
        # the first bounded receive inactivity timeout. This is a conservative
        # terminal drain: any late SYN from the isolated attempt role is retained
        # rather than hidden, while continuously arriving traffic still fails
        # closed through the bounded join in ``close()``.
        while True:
            try:
                frame, address = capture.recvfrom(65535)
            except TimeoutError:
                if self._stop.is_set():
                    break
                continue
            except OSError:
                if not self._stop.is_set():
                    self._add_problem("capture-read-failed")
                break
            now = time.monotonic_ns()
            packet_type = _packet_type(address)
            index = self._interface_index or 0
            try:
                parsed = parse_initial_syn(frame)
            except PacketParseError as exc:
                self._retain_raw(frame, now, packet_type, index)
                self._add_problem(f"packet-normalization-ambiguous:{exc}")
                continue
            if parsed is None:
                continue
            scope = scope_for_source(self.scopes, parsed.source_address)
            if scope is None:
                continue
            self._retain_raw(frame, now, packet_type, index)
            if packet_type != _PACKET_OUTGOING:
                self._add_problem("ambiguous-packet-direction")
                continue
            with self._lock:
                admitted = self._admitted
                current_attempt = self._attempt_id or ""
            if not admitted:
                self._add_problem("role-syn-before-attempt-admission")
                continue
            observation = TcpSynObservation(
                channel=scope.channel,
                role_id=scope.role_id,
                attempt_id=current_attempt,
                interface_name=self.interface_name,
                interface_index=index,
                monotonic_ns=now,
                family=parsed.family,
                source_address=parsed.source_address,
                source_port=parsed.source_port,
                destination_address=parsed.destination_address,
                destination_port=parsed.destination_port,
                sequence=parsed.sequence,
                packet_type=packet_type,
                raw_frame_sha256=hashlib.sha256(frame).hexdigest(),
            )
            with self._lock:
                self._observations.append(observation)

    def _retain_raw(self, frame: bytes, now: int, packet_type: int, index: int) -> None:
        with self._lock:
            self._raw.append(
                RawFrameRecord(
                    attempt_id=self._attempt_id or "",
                    interface_name=self.interface_name,
                    interface_index=index,
                    monotonic_ns=now,
                    packet_type=packet_type,
                    frame=bytes(frame),
                )
            )

    def _read_capture_statistics(self) -> None:
        capture = self._socket
        if capture is None:
            return
        try:
            raw = capture.getsockopt(_SOL_PACKET, _PACKET_STATISTICS, 8)
            if len(raw) < 8:
                raise OSError("short PACKET_STATISTICS result")
            self._capture_packets, self._capture_drops = map(int, struct.unpack("=II", raw[:8]))
        except OSError:
            self._capture_packets = None
            self._capture_drops = None

    def _add_problem(self, problem: str) -> None:
        with self._lock:
            if problem not in self._problems:
                self._problems.append(problem)

    def _close_socket(self) -> None:
        capture = self._socket
        if capture is not None:
            capture.close()
            self._socket = None


def _packet_type(address: object) -> int:
    if isinstance(address, tuple) and len(address) >= 3 and isinstance(address[2], int):
        return address[2]
    return -1

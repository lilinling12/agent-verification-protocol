"""Deterministic evaluator-owned exact-byte fixture for Network Control TEL-001.

Application ``accept`` records are intentionally supplemental evidence. They do
not certify transport-initiation cardinality; that claim belongs to the separate
transport-boundary witness.
"""

from __future__ import annotations

import hashlib
import ipaddress
import math
import socket
import threading
from dataclasses import dataclass

from .evidence_core import AttemptMaterial, EvidenceMaterializationError, MaterializedEndpoint


@dataclass(frozen=True, slots=True)
class FixtureExchangeEvent:
    ordinal: int
    attempt_id: str | None
    peer: str
    received_size: int
    received_sha256: str
    request_valid: bool
    response_emitted: bool
    problem: str | None = None


class ExactByteFixture:
    """Run a literal-address TCP fixture with explicitly armed attempt material."""

    def __init__(
        self,
        *,
        family: str = "ipv4",
        address: str = "127.0.0.1",
        role: str = "upstream-fixture",
        bind_port: int = 0,
        hygiene_timeout_s: float = 2.0,
    ) -> None:
        if role not in {"upstream-fixture", "control-fixture", "fixture"}:
            raise EvidenceMaterializationError("fixture endpoint role is not evaluator-fixture scoped")
        if family not in {"ipv4", "ipv6"}:
            raise EvidenceMaterializationError("fixture family must be ipv4 or ipv6")
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError as exc:
            raise EvidenceMaterializationError("fixture bind address must be a literal IP") from exc
        if (parsed.version == 4) != (family == "ipv4"):
            raise EvidenceMaterializationError("fixture family does not match literal bind address")
        if isinstance(bind_port, bool) or not isinstance(bind_port, int) or not (0 <= bind_port <= 65535):
            raise EvidenceMaterializationError("fixture bind port must be an integer in [0, 65535]")
        if (
            isinstance(hygiene_timeout_s, bool)
            or not isinstance(hygiene_timeout_s, (int, float))
            or not math.isfinite(hygiene_timeout_s)
            or hygiene_timeout_s <= 0
        ):
            raise EvidenceMaterializationError("fixture hygiene timeout must be positive and finite")

        self._family = family
        self._address = str(parsed)
        self._role = role
        self._bind_port = bind_port
        self._hygiene_timeout_s = float(hygiene_timeout_s)
        self._listener: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._lock = threading.Lock()
        self._armed: AttemptMaterial | None = None
        self._events: list[FixtureExchangeEvent] = []
        self._connections: set[threading.Thread] = set()
        self._ordinal = 0
        self._fatal_problem: str | None = None

    @property
    def endpoint(self) -> MaterializedEndpoint:
        listener = self._listener
        if listener is None:
            raise RuntimeError("fixture is not started")
        address = listener.getsockname()[0]
        port = int(listener.getsockname()[1])
        return MaterializedEndpoint(family=self._family, address=address, port=port, role=self._role)

    @property
    def fatal_problem(self) -> str | None:
        with self._lock:
            return self._fatal_problem

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("fixture already started")
        family = socket.AF_INET if self._family == "ipv4" else socket.AF_INET6
        listener = socket.socket(family, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bind_address = (
            (self._address, self._bind_port)
            if self._family == "ipv4"
            else (self._address, self._bind_port, 0, 0)
        )
        try:
            listener.bind(bind_address)
            listener.listen(16)
            listener.settimeout(0.1)
        except BaseException:
            listener.close()
            raise
        self._listener = listener
        self._thread = threading.Thread(target=self._accept_loop, name="avp-exact-byte-fixture", daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=2.0):
            self.stop()
            raise RuntimeError("fixture did not reach readiness barrier")

    def arm(self, attempt: AttemptMaterial) -> None:
        if self._listener is None or not self._ready.is_set():
            raise RuntimeError("fixture must be ready before attempt admission")
        with self._lock:
            if self._fatal_problem is not None:
                raise RuntimeError(f"fixture is unhealthy: {self._fatal_problem}")
            if self._armed is not None:
                raise RuntimeError("another attempt is still armed")
            self._armed = attempt

    def disarm(self, attempt_id: str) -> None:
        with self._lock:
            if self._armed is None:
                return
            if self._armed.attempt_id != attempt_id:
                raise RuntimeError("cannot disarm a different attempt")
            self._armed = None

    def events(self) -> tuple[FixtureExchangeEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def stop(self) -> None:
        self._stop.set()
        listener = self._listener
        if listener is not None:
            listener.close()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=2.0)
            if thread.is_alive():
                self._set_fatal("fixture-accept-thread-did-not-stop")
        with self._lock:
            connection_threads = tuple(self._connections)
        for connection_thread in connection_threads:
            connection_thread.join(timeout=self._hygiene_timeout_s)
            if connection_thread.is_alive():
                self._set_fatal("fixture-connection-thread-did-not-stop")
        self._listener = None
        self._thread = None

    def __enter__(self) -> "ExactByteFixture":
        self.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.stop()

    def _accept_loop(self) -> None:
        self._ready.set()
        assert self._listener is not None
        while not self._stop.is_set():
            try:
                connection, peer = self._listener.accept()
            except TimeoutError:
                continue
            except OSError as exc:
                if self._stop.is_set():
                    break
                self._set_fatal(f"fixture-accept:{type(exc).__name__}")
                break
            worker = threading.Thread(
                target=self._handle_connection,
                args=(connection, peer),
                name="avp-exact-byte-fixture-connection",
                daemon=True,
            )
            with self._lock:
                self._connections.add(worker)
            worker.start()

    def _handle_connection(self, connection: socket.socket, peer: object) -> None:
        with self._lock:
            attempt = self._armed
            self._ordinal += 1
            ordinal = self._ordinal
        received = b""
        problem: str | None = None
        response_emitted = False
        try:
            connection.settimeout(self._hygiene_timeout_s)
            if attempt is None:
                problem = "connection-without-armed-attempt"
                return
            received, problem = _receive_exact_request(connection, len(attempt.request_bytes))
            if problem is None and received == attempt.request_bytes:
                connection.sendall(attempt.expected_response_bytes)
                response_emitted = True
            elif problem is None:
                problem = "request-byte-mismatch"
        except (OSError, TimeoutError) as exc:
            problem = f"fixture-io:{type(exc).__name__}"
        finally:
            event = FixtureExchangeEvent(
                ordinal=ordinal,
                attempt_id=None if attempt is None else attempt.attempt_id,
                peer=str(peer),
                received_size=len(received),
                received_sha256=hashlib.sha256(received).hexdigest(),
                request_valid=attempt is not None and problem is None,
                response_emitted=response_emitted,
                problem=problem,
            )
            with self._lock:
                self._events.append(event)
                self._connections.discard(threading.current_thread())
            connection.close()

    def _set_fatal(self, problem: str) -> None:
        with self._lock:
            if self._fatal_problem is None:
                self._fatal_problem = problem


def _receive_exact_request(connection: socket.socket, length: int) -> tuple[bytes, str | None]:
    received = bytearray()
    while len(received) < length:
        chunk = connection.recv(length - len(received))
        if not chunk:
            return bytes(received), "request-truncated"
        received.extend(chunk)
    return bytes(received), None

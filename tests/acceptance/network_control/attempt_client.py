"""Single-initiation exact-byte TCP client for Network Control TEL-001."""

from __future__ import annotations

import errno
import hashlib
import selectors
import socket
import time
from dataclasses import dataclass
from typing import Callable

from .evidence_core import AttemptMaterial, EvidenceMaterializationError, MaterializedEndpoint


@dataclass(frozen=True, slots=True)
class ExchangeObservation:
    attempt_id: str
    completed: bool
    mismatch_observed: bool
    observation_budget_expired: bool
    elapsed_ns: int
    response_size: int
    response_sha256: str | None
    native_error: str | None = None


def execute_exact_exchange(
    endpoint: MaterializedEndpoint,
    attempt: AttemptMaterial,
    *,
    observation_budget_ns: int,
    request_override: bytes | None = None,
    socket_factory: Callable[[int, int], socket.socket] = socket.socket,
) -> ExchangeObservation:
    """Execute exactly one TCP connect initiation and one exact-byte exchange.

    There is no reconnect, destination fallback, or application retry loop. The
    portable completion decision is bounded with evaluator-owned ``monotonic_ns``;
    any native socket error is retained as diagnostics only.
    """

    if isinstance(observation_budget_ns, bool) or not isinstance(observation_budget_ns, int):
        raise EvidenceMaterializationError("observation budget must be integer nanoseconds")
    if observation_budget_ns <= 0:
        raise EvidenceMaterializationError("observation budget must be positive")

    family = socket.AF_INET if endpoint.family == "ipv4" else socket.AF_INET6
    sock = socket_factory(family, socket.SOCK_STREAM)
    started = time.monotonic_ns()
    deadline = started + observation_budget_ns
    selector = selectors.DefaultSelector()
    response = bytearray()
    mismatch = False
    expired = False
    native_error: str | None = None
    try:
        sock.setblocking(False)
        selector.register(sock, selectors.EVENT_WRITE)
        connect_result = sock.connect_ex(_socket_address(endpoint))  # exactly one connect initiation
        if connect_result not in _connect_in_progress_codes():
            native_error = errno.errorcode.get(connect_result, f"errno-{connect_result}")
            return _observation(attempt, started, response, mismatch, False, native_error)

        if connect_result != 0:
            if not _wait(selector, selectors.EVENT_WRITE, deadline):
                expired = True
                return _observation(attempt, started, response, mismatch, expired, native_error)
            socket_error = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if socket_error != 0:
                native_error = errno.errorcode.get(socket_error, f"errno-{socket_error}")
                return _observation(attempt, started, response, mismatch, False, native_error)

        request = attempt.request_bytes if request_override is None else request_override
        view = memoryview(request)
        while view:
            if not _wait(selector, selectors.EVENT_WRITE, deadline):
                expired = True
                return _observation(attempt, started, response, mismatch, expired, native_error)
            try:
                sent = sock.send(view)
            except BlockingIOError:
                continue
            if sent <= 0:
                native_error = "send-returned-zero"
                return _observation(attempt, started, response, mismatch, False, native_error)
            view = view[sent:]

        # EOF frames the request exactly: the fixture must observe no trailing
        # request bytes before it is allowed to emit the expected response.
        try:
            sock.shutdown(socket.SHUT_WR)
        except OSError as exc:
            native_error = f"{type(exc).__name__}:{getattr(exc, 'errno', None)}"
            return _observation(attempt, started, response, mismatch, False, native_error)
        selector.modify(sock, selectors.EVENT_READ)
        expected = attempt.expected_response_bytes
        while len(response) < len(expected):
            if not _wait(selector, selectors.EVENT_READ, deadline):
                expired = True
                break
            try:
                chunk = sock.recv(len(expected) - len(response))
            except BlockingIOError:
                continue
            except OSError as exc:
                native_error = f"{type(exc).__name__}:{getattr(exc, 'errno', None)}"
                break
            if not chunk:
                break
            response.extend(chunk)
            if bytes(response) != expected[: len(response)]:
                mismatch = True
                break
        return _observation(attempt, started, response, mismatch, expired, native_error)
    finally:
        selector.close()
        sock.close()


def _observation(
    attempt: AttemptMaterial,
    started_ns: int,
    response: bytearray,
    mismatch: bool,
    expired: bool,
    native_error: str | None,
) -> ExchangeObservation:
    payload = bytes(response)
    completed = (
        not mismatch
        and not expired
        and native_error is None
        and payload == attempt.expected_response_bytes
    )
    return ExchangeObservation(
        attempt_id=attempt.attempt_id,
        completed=completed,
        mismatch_observed=mismatch,
        observation_budget_expired=expired,
        elapsed_ns=max(0, time.monotonic_ns() - started_ns),
        response_size=len(payload),
        response_sha256=(hashlib.sha256(payload).hexdigest() if payload else None),
        native_error=native_error,
    )


def _wait(selector: selectors.BaseSelector, event: int, deadline_ns: int) -> bool:
    while True:
        remaining_ns = deadline_ns - time.monotonic_ns()
        if remaining_ns <= 0:
            return False
        ready = selector.select(remaining_ns / 1_000_000_000)
        if any(mask & event for _key, mask in ready):
            return True


def _socket_address(endpoint: MaterializedEndpoint) -> tuple[object, ...]:
    if endpoint.family == "ipv4":
        return (endpoint.address, endpoint.port)
    return (endpoint.address, endpoint.port, 0, 0)


def _connect_in_progress_codes() -> set[int]:
    names = ("EINPROGRESS", "EWOULDBLOCK", "EALREADY", "EINTR")
    return {0, *(getattr(errno, name) for name in names if hasattr(errno, name))}

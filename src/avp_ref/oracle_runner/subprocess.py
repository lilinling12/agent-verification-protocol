"""Subprocess based Oracle execution boundary."""

from __future__ import annotations

import subprocess
import sys
import time
import uuid

from avp_ref.canonical import digest

from .models import OracleExecutionResult, OracleExecutionStatus, OracleRequest
from .protocol import decode, encode


class SubprocessOracleRunner:
    def __init__(self, timeout_seconds: float = 5.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds

    def evaluate(self, request: OracleRequest) -> OracleExecutionResult:
        started = time.monotonic()
        process = subprocess.Popen(
            [sys.executable, "-m", "avp_ref.oracle_worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
        )
        try:
            stdout, stderr = process.communicate(
                encode({"request_id": request.request_id, "context": request.context}),
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            return OracleExecutionResult(request.request_id, OracleExecutionStatus.TIMEOUT)

        duration = int((time.monotonic() - started) * 1000)
        if process.returncode != 0:
            return OracleExecutionResult(request.request_id, OracleExecutionStatus.CRASHED, duration_ms=duration, exit_code=process.returncode)
        try:
            response = decode(stdout)
        except Exception:
            return OracleExecutionResult(request.request_id, OracleExecutionStatus.PROTOCOL_ERROR, duration_ms=duration)
        return OracleExecutionResult(
            request.request_id,
            OracleExecutionStatus.SUCCESS,
            tuple(response.get("results", [])),
            tuple(response.get("evidence", [])),
            duration,
            process.returncode,
        )

    @staticmethod
    def request_id() -> str:
        return "oracle_req_" + uuid.uuid4().hex

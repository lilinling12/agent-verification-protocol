"""Process-isolated Oracle runner with bounded I/O and sanitized inheritance."""

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from typing import BinaryIO

from avp_ref.canonical import digest

from .errors import OracleConfigurationError, OracleProtocolError, OracleSecurityError
from .models import (
    OracleExecutionArtifact,
    OracleExecutionResult,
    OracleExecutionStatus,
    OracleRequest,
    OracleRunnerDescription,
    OracleSandboxPolicy,
)
from .package import module_code_digest, parse_entrypoint
from .protocol import PROTOCOL_VERSION, decode_success, encode_request

_RUNNER_VERSION = "0.2.0-alpha.7"
_PROTOCOL_EXIT = 65
_ORACLE_CRASH_EXIT = 70
_SECURITY_EXIT = 77
_POLL_SECONDS = 0.005


class SubprocessOracleRunner:
    """Reference process boundary for evaluator-owned Oracle code.

    The subprocess receives a sanitized environment and a temporary working
    directory. On POSIX, the worker applies rlimits before importing the Oracle.
    This is intentionally not described as a network/filesystem sandbox.
    """

    def __init__(
        self,
        policy: OracleSandboxPolicy | None = None,
        *,
        worker_module: str = "avp_ref.oracle_worker",
        allowed_module_prefixes: tuple[str, ...] = ("avp_ref.",),
    ) -> None:
        self.policy = policy or OracleSandboxPolicy(enforce_resource_limits=(os.name == "posix"))
        if not worker_module or not allowed_module_prefixes:
            raise OracleConfigurationError("worker_module and allowed_module_prefixes must be configured")
        self.worker_module = worker_module
        self.allowed_module_prefixes = tuple(sorted(set(allowed_module_prefixes)))
        if self.policy.enforce_resource_limits and os.name != "posix":
            raise OracleSecurityError("POSIX resource limits were required on a platform that cannot enforce them")

    def describe(self) -> OracleRunnerDescription:
        return OracleRunnerDescription(
            name="subprocess-oracle-runner",
            version=_RUNNER_VERSION,
            protocol_version=PROTOCOL_VERSION,
            isolation="process+rlimit" if self.policy.enforce_resource_limits else "process",
            policy=self.policy,
            worker_module=self.worker_module,
            worker_code_digest=module_code_digest(f"{self.worker_module}:main"),
            allowed_module_prefixes=self.allowed_module_prefixes,
            filesystem_isolation=False,
            network_isolation=False,
        )

    def evaluate(self, request: OracleRequest) -> OracleExecutionResult:
        module_name, _ = parse_entrypoint(request.package.entrypoint)
        if not self._module_allowed(module_name):
            raise OracleSecurityError(f"Oracle module is outside runner allowlist: {module_name}")
        frame = encode_request(request, max_bytes=self.policy.max_request_bytes)
        started = time.monotonic()
        status = OracleExecutionStatus.CRASHED
        output = None
        return_code: int | None = None

        with (
            tempfile.TemporaryDirectory(prefix="avp-oracle-") as workdir,
            tempfile.TemporaryFile() as stdout_file,
            tempfile.TemporaryFile() as stderr_file,
        ):
            process = subprocess.Popen(
                [sys.executable, "-I", "-B", "-m", self.worker_module],
                stdin=subprocess.PIPE,
                stdout=stdout_file,
                stderr=stderr_file,
                cwd=workdir,
                env=self._worker_environment(),
                shell=False,
                start_new_session=True,
                close_fds=True,
            )
            self._send_request(process, frame)
            termination = self._wait_bounded(process, stdout_file, stderr_file)
            return_code = process.returncode
            stdout_bytes, stdout_digest, stdout_oversized = self._read_and_digest(
                stdout_file, self.policy.max_response_bytes
            )
            _, stderr_digest, stderr_oversized = self._read_and_digest(
                stderr_file, self.policy.max_file_bytes
            )

            if termination == "timeout":
                status = OracleExecutionStatus.TIMEOUT
            elif termination == "output_limit" or stdout_oversized or stderr_oversized:
                status = OracleExecutionStatus.SECURITY_VIOLATION
            elif self._resource_limit_exit(return_code) or return_code == _SECURITY_EXIT:
                status = OracleExecutionStatus.SECURITY_VIOLATION
            elif return_code == _PROTOCOL_EXIT:
                status = OracleExecutionStatus.PROTOCOL_ERROR
            elif return_code != 0:
                status = OracleExecutionStatus.CRASHED
            else:
                try:
                    output = decode_success(
                        stdout_bytes,
                        expected_request_id=request.request_id,
                        max_bytes=self.policy.max_response_bytes,
                    )
                    status = OracleExecutionStatus.SUCCESS
                except OracleProtocolError:
                    status = OracleExecutionStatus.PROTOCOL_ERROR

        duration_ms = int((time.monotonic() - started) * 1000)
        output_digest = self._output_digest(output) if output is not None else None
        artifact = OracleExecutionArtifact(
            request_id=request.request_id,
            oracle_package_digest=request.package.identity_digest,
            oracle_code_digest=request.package.code_digest,
            runner_config_digest=self.describe().identity_digest,
            input_digest=request.context.input_digest,
            status=status,
            duration_ms=duration_ms,
            exit_code=return_code,
            stdout_digest=stdout_digest,
            stderr_digest=stderr_digest,
            output_digest=output_digest,
        )
        return OracleExecutionResult(
            request.request_id,
            status,
            output.results if output is not None else (),
            output.evidence if output is not None else (),
            artifact,
        )

    @staticmethod
    def request_id() -> str:
        return "oracle_req_" + uuid.uuid4().hex

    def _module_allowed(self, module_name: str) -> bool:
        return any(
            module_name == prefix.rstrip(".") or module_name.startswith(prefix)
            for prefix in self.allowed_module_prefixes
        )

    def _worker_environment(self) -> dict[str, str]:
        env: dict[str, str] = {
            "TZ": "UTC",
            "AVP_ORACLE_ENFORCE_LIMITS": "1" if self.policy.enforce_resource_limits else "0",
            "AVP_ORACLE_CPU_SECONDS": str(self.policy.cpu_seconds),
            "AVP_ORACLE_MEMORY_BYTES": str(self.policy.memory_bytes),
            "AVP_ORACLE_FILE_BYTES": str(self.policy.max_file_bytes),
            "AVP_ORACLE_NOFILE": str(self.policy.max_open_files),
            "AVP_ORACLE_MAX_REQUEST_BYTES": str(self.policy.max_request_bytes),
            "AVP_ORACLE_MAX_RESPONSE_BYTES": str(self.policy.max_response_bytes),
            "AVP_ORACLE_ALLOWED_MODULE_PREFIXES": json.dumps(self.allowed_module_prefixes),
        }
        for name in ("SYSTEMROOT", "WINDIR", "LANG", "LC_ALL"):
            value = os.environ.get(name)
            if value is not None:
                env[name] = value
        for name in self.policy.inherited_environment:
            value = os.environ.get(name)
            if value is not None:
                env[name] = value
        return env

    @staticmethod
    def _send_request(process: subprocess.Popen[bytes], frame: bytes) -> None:
        if process.stdin is None:
            raise OracleProtocolError("Oracle worker stdin was not created")
        try:
            process.stdin.write(frame)
            process.stdin.flush()
        except BrokenPipeError:
            pass
        finally:
            process.stdin.close()

    def _wait_bounded(
        self,
        process: subprocess.Popen[bytes],
        stdout_file: BinaryIO,
        stderr_file: BinaryIO,
    ) -> str:
        deadline = time.monotonic() + self.policy.timeout_seconds
        while process.poll() is None:
            if self._file_size(stdout_file) > self.policy.max_response_bytes:
                self._kill_process_group(process)
                process.wait()
                return "output_limit"
            if self._file_size(stderr_file) > self.policy.max_file_bytes:
                self._kill_process_group(process)
                process.wait()
                return "output_limit"
            if time.monotonic() >= deadline:
                self._kill_process_group(process)
                process.wait()
                return "timeout"
            time.sleep(_POLL_SECONDS)
        return "completed"

    @staticmethod
    def _file_size(file_object: BinaryIO) -> int:
        return os.fstat(file_object.fileno()).st_size

    @staticmethod
    def _read_and_digest(file_object: BinaryIO, capture_limit: int) -> tuple[bytes, str, bool]:
        file_object.seek(0)
        hasher = hashlib.sha256()
        captured = bytearray()
        total = 0
        while True:
            chunk = file_object.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            hasher.update(chunk)
            if len(captured) < capture_limit:
                remaining = capture_limit - len(captured)
                captured.extend(chunk[:remaining])
        return bytes(captured), "sha256:" + hasher.hexdigest(), total > capture_limit

    @staticmethod
    def _kill_process_group(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is not None:
            return
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
                return
            except ProcessLookupError:
                return
        process.kill()

    @staticmethod
    def _resource_limit_exit(return_code: int | None) -> bool:
        if return_code is None or return_code >= 0 or os.name != "posix":
            return False
        signal_number = -return_code
        limited = {getattr(signal, name, -1) for name in ("SIGXCPU", "SIGXFSZ")}
        return signal_number in limited

    @staticmethod
    def _output_digest(output) -> str:
        return digest(
            {
                "results": [
                    {
                        "claim_id": item.claim_id,
                        "dimension": item.dimension,
                        "verdict": item.verdict,
                        "severity": item.severity,
                        "method": item.method,
                        "evaluator_version": item.evaluator_version,
                        "evidence_ids": list(item.evidence_ids),
                        "confidence": item.confidence,
                        "validity": item.validity.value,
                    }
                    for item in output.results
                ],
                "evidence": [
                    {
                        "evidence_id": item.evidence_id,
                        "kind": item.kind,
                        "digest": item.digest,
                        "classification": item.classification,
                    }
                    for item in output.evidence
                ],
            }
        )

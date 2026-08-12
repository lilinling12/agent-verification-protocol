"""Process-isolated Oracle runner with bounded I/O and sanitized inheritance."""

from __future__ import annotations

import hashlib
import os
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from typing import Mapping

from avp_ref.canonical import digest

from .errors import OracleConfigurationError, OracleProtocolError, OracleSecurityError
from .models import OracleExecutionArtifact, OracleExecutionResult, OracleExecutionStatus, OracleRequest, OracleRunnerDescription, OracleSandboxPolicy
from .package import parse_entrypoint
from .protocol import PROTOCOL_VERSION, decode_success, encode_request

_RUNNER_VERSION = "0.2.0-alpha.6"
_SECURITY_EXIT = 77


def _bytes_digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


class SubprocessOracleRunner:
    """Reference process boundary for evaluator-owned Oracle code.

    The subprocess gets a sanitized environment and a temporary working
    directory. On POSIX, the worker applies rlimits before importing the Oracle.
    This is not a network/filesystem sandbox; the description reports that
    limitation explicitly instead of overclaiming isolation.
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
            filesystem_isolation=False,
            network_isolation=False,
        )

    def evaluate(self, request: OracleRequest) -> OracleExecutionResult:
        module_name, _ = parse_entrypoint(request.package.entrypoint)
        if not any(module_name == prefix.rstrip(".") or module_name.startswith(prefix) for prefix in self.allowed_module_prefixes):
            raise OracleSecurityError(f"Oracle module is outside runner allowlist: {module_name}")
        frame = encode_request(request, max_bytes=self.policy.max_request_bytes)
        started = time.monotonic()
        stdout_bytes = b""
        stderr_bytes = b""
        return_code: int | None = None
        status = OracleExecutionStatus.CRASHED
        output = None
        with tempfile.TemporaryDirectory(prefix="avp-oracle-") as workdir, tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
            process = subprocess.Popen(
                [sys.executable, "-I", "-m", self.worker_module],
                stdin=subprocess.PIPE,
                stdout=stdout_file,
                stderr=stderr_file,
                cwd=workdir,
                env=self._worker_environment(),
                shell=False,
                start_new_session=True,
                close_fds=True,
            )
            try:
                process.communicate(input=frame, timeout=self.policy.timeout_seconds)
            except subprocess.TimeoutExpired:
                self._kill_process_group(process)
                process.communicate()
                status = OracleExecutionStatus.TIMEOUT
            return_code = process.returncode
            stdout_bytes = self._read_bounded(stdout_file, self.policy.max_response_bytes)
            stderr_bytes = self._read_bounded(stderr_file, self.policy.max_file_bytes)
            if status is not OracleExecutionStatus.TIMEOUT:
                if self._resource_limit_exit(return_code):
                    status = OracleExecutionStatus.SECURITY_VIOLATION
                elif return_code == _SECURITY_EXIT:
                    status = OracleExecutionStatus.SECURITY_VIOLATION
                elif return_code != 0:
                    status = OracleExecutionStatus.CRASHED
                else:
                    try:
                        output = decode_success(stdout_bytes, expected_request_id=request.request_id, max_bytes=self.policy.max_response_bytes)
                        status = OracleExecutionStatus.SUCCESS
                    except OracleProtocolError:
                        status = OracleExecutionStatus.PROTOCOL_ERROR
        duration_ms = int((time.monotonic() - started) * 1000)
        output_digest = None
        if output is not None:
            output_digest = digest({
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
                    {"evidence_id": item.evidence_id, "kind": item.kind, "digest": item.digest, "classification": item.classification}
                    for item in output.evidence
                ],
            })
        artifact = OracleExecutionArtifact(
            request_id=request.request_id,
            oracle_package_digest=request.package.identity_digest,
            oracle_code_digest=request.package.code_digest,
            runner_config_digest=self.describe().identity_digest,
            input_digest=request.context.input_digest,
            status=status,
            duration_ms=duration_ms,
            exit_code=return_code,
            stdout_digest=_bytes_digest(stdout_bytes),
            stderr_digest=_bytes_digest(stderr_bytes),
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

    def _worker_environment(self) -> dict[str, str]:
        env: dict[str, str] = {
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "TZ": "UTC",
            "AVP_ORACLE_ENFORCE_LIMITS": "1" if self.policy.enforce_resource_limits else "0",
            "AVP_ORACLE_CPU_SECONDS": str(self.policy.cpu_seconds),
            "AVP_ORACLE_MEMORY_BYTES": str(self.policy.memory_bytes),
            "AVP_ORACLE_FILE_BYTES": str(self.policy.max_file_bytes),
            "AVP_ORACLE_NOFILE": str(self.policy.max_open_files),
            "AVP_ORACLE_MAX_REQUEST_BYTES": str(self.policy.max_request_bytes),
            "AVP_ORACLE_MAX_RESPONSE_BYTES": str(self.policy.max_response_bytes),
        }
        for name in ("PATH", "SYSTEMROOT", "WINDIR", "LANG", "LC_ALL"):
            value = os.environ.get(name)
            if value is not None:
                env[name] = value
        for name in self.policy.inherited_environment:
            value = os.environ.get(name)
            if value is not None:
                env[name] = value
        return env

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
    def _read_bounded(file_object, limit: int) -> bytes:
        file_object.seek(0)
        value = file_object.read(limit + 1)
        if len(value) > limit:
            raise OracleSecurityError("Oracle process output exceeded configured limit")
        return value

    @staticmethod
    def _resource_limit_exit(return_code: int | None) -> bool:
        if return_code is None or return_code >= 0 or os.name != "posix":
            return False
        signal_number = -return_code
        limited = {getattr(signal, name, -1) for name in ("SIGXCPU", "SIGXFSZ")}
        return signal_number in limited

"""Minimal isolated worker process for evaluator-owned Oracle code."""

from __future__ import annotations

import errno
import importlib
import json
import os
import sys

from avp_ref.oracle_runner.errors import OracleProtocolError, OracleSecurityError
from avp_ref.oracle_runner.models import OracleEvaluationOutput
from avp_ref.oracle_runner.package import module_code_digest, parse_entrypoint
from avp_ref.oracle_runner.protocol import decode_request, encode_success

_PROTOCOL_EXIT = 65
_ORACLE_CRASH_EXIT = 70
_SECURITY_EXIT = 77
_RESOURCE_ERRNOS = {errno.EFBIG, errno.EMFILE, errno.ENFILE, errno.ENOMEM}


def _apply_resource_limits() -> None:
    if os.environ.get("AVP_ORACLE_ENFORCE_LIMITS") != "1":
        return
    try:
        import resource
    except ImportError as exc:
        raise OracleSecurityError("resource limits are required but unavailable") from exc
    cpu = int(os.environ["AVP_ORACLE_CPU_SECONDS"])
    memory = int(os.environ["AVP_ORACLE_MEMORY_BYTES"])
    file_bytes = int(os.environ["AVP_ORACLE_FILE_BYTES"])
    nofile = int(os.environ["AVP_ORACLE_NOFILE"])
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    resource.setrlimit(resource.RLIMIT_FSIZE, (file_bytes, file_bytes))
    resource.setrlimit(resource.RLIMIT_NOFILE, (nofile, nofile))
    if hasattr(resource, "RLIMIT_CORE"):
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _allowed_module(module_name: str) -> bool:
    try:
        raw = json.loads(os.environ["AVP_ORACLE_ALLOWED_MODULE_PREFIXES"])
    except (KeyError, json.JSONDecodeError, TypeError) as exc:
        raise OracleSecurityError("Oracle module allowlist is missing or malformed") from exc
    if not isinstance(raw, list) or not raw or not all(isinstance(item, str) and item for item in raw):
        raise OracleSecurityError("Oracle module allowlist is invalid")
    return any(module_name == prefix.rstrip(".") or module_name.startswith(prefix) for prefix in raw)


def _safe_error(exc: BaseException) -> bytes:
    text = f"{type(exc).__name__}: {exc}".replace("\n", " ")[:512]
    return (text + "\n").encode("utf-8", errors="replace")


def _is_resource_error(exc: OSError) -> bool:
    return exc.errno in _RESOURCE_ERRNOS


def main() -> int:
    try:
        _apply_resource_limits()
        max_request = int(os.environ.get("AVP_ORACLE_MAX_REQUEST_BYTES", str(1024 * 1024)))
        max_response = int(os.environ.get("AVP_ORACLE_MAX_RESPONSE_BYTES", str(1024 * 1024)))
        frame = sys.stdin.buffer.readline(max_request + 1)
        if len(frame) > max_request or not frame.endswith(b"\n") or sys.stdin.buffer.read(1):
            raise OracleProtocolError("Oracle worker accepts exactly one bounded request frame")
        request = decode_request(frame, max_bytes=max_request)
        module_name, callable_name = parse_entrypoint(request.package.entrypoint)
        if not _allowed_module(module_name):
            raise OracleSecurityError(f"Oracle module is outside worker allowlist: {module_name}")
        if module_code_digest(request.package.entrypoint) != request.package.code_digest:
            raise OracleSecurityError("Oracle package code digest changed before execution")
        oracle_module = importlib.import_module(module_name)
        oracle_callable = getattr(oracle_module, callable_name, None)
        if not callable(oracle_callable):
            raise OracleProtocolError("Oracle entrypoint is not callable")
        output = oracle_callable(request.context)
        if not isinstance(output, OracleEvaluationOutput):
            raise OracleProtocolError("Oracle entrypoint must return OracleEvaluationOutput")
        sys.stdout.buffer.write(encode_success(request.request_id, output, max_bytes=max_response))
        sys.stdout.buffer.flush()
        return 0
    except OracleSecurityError as exc:
        sys.stderr.buffer.write(_safe_error(exc))
        return _SECURITY_EXIT
    except OracleProtocolError as exc:
        sys.stderr.buffer.write(_safe_error(exc))
        return _PROTOCOL_EXIT
    except MemoryError as exc:
        sys.stderr.buffer.write(_safe_error(exc))
        return _SECURITY_EXIT
    except OSError as exc:
        sys.stderr.buffer.write(_safe_error(exc))
        return _SECURITY_EXIT if _is_resource_error(exc) else _ORACLE_CRASH_EXIT
    except BaseException as exc:
        sys.stderr.buffer.write(_safe_error(exc))
        return _ORACLE_CRASH_EXIT


if __name__ == "__main__":
    raise SystemExit(main())

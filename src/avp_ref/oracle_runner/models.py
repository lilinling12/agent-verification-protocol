"""Immutable models for isolated Oracle execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class OracleExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    CRASHED = "CRASHED"
    PROTOCOL_ERROR = "PROTOCOL_ERROR"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"


@dataclass(frozen=True, slots=True)
class OracleRequest:
    request_id: str
    oracle_digest: str
    context: dict[str, Any]


@dataclass(frozen=True, slots=True)
class OracleExecutionResult:
    request_id: str
    status: OracleExecutionStatus
    results: tuple[dict[str, Any], ...] = ()
    evidence: tuple[dict[str, Any], ...] = ()
    duration_ms: int = 0
    exit_code: int | None = None


@dataclass(frozen=True, slots=True)
class OracleExecutionArtifact:
    request_id: str
    status: OracleExecutionStatus
    duration_ms: int
    stdout_digest: str
    stderr_digest: str

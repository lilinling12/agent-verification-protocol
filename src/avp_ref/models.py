"""Protocol value objects shared across runtime and evaluators."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskVerdict(str, Enum):
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class Validity(str, Enum):
    VALID = "VALID"
    INVALID_TASK = "INVALID_TASK"
    INVALID_INITIAL_STATE = "INVALID_INITIAL_STATE"
    ENVIRONMENT_FAILURE = "ENVIRONMENT_FAILURE"
    RESET_FAILURE = "RESET_FAILURE"
    ORACLE_FAILURE = "ORACLE_FAILURE"
    TRACE_INCOMPLETE = "TRACE_INCOMPLETE"
    INFRA_CONFOUND = "INFRA_CONFOUND"
    CONTAMINATED = "CONTAMINATED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_id: str
    kind: str
    data: Any
    digest: str
    classification: str = "evaluator-confidential"


@dataclass(frozen=True, slots=True)
class VerificationResult:
    claim_id: str
    dimension: str
    verdict: str
    severity: str
    method: str
    evaluator_version: str
    evidence_ids: tuple[str, ...] = ()
    confidence: float = 1.0
    validity: Validity = Validity.VALID


@dataclass(slots=True)
class AVPEvent:
    event_id: str
    event_type: str
    episode_id: str
    sequence: int
    plane: str
    logical_time: int
    payload: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Snapshot:
    snapshot_id: str
    state: dict[str, Any]
    state_digest: str
    logical_time: int
    consistency: str = "application-consistent"

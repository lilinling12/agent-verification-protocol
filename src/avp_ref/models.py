from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class EpisodeState(str, Enum):
    CREATED = "CREATED"
    PROVISIONING = "PROVISIONING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    QUIESCING = "QUIESCING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    INVALID = "INVALID"
    INFRA_FAILED = "INFRA_FAILED"

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

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    kind: str
    data: Any
    digest: str
    classification: str = "evaluator-confidential"

@dataclass(frozen=True)
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

@dataclass
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

@dataclass
class Snapshot:
    snapshot_id: str
    state: dict[str, Any]
    state_digest: str
    logical_time: int
    consistency: str = "application-consistent"

@dataclass
class Episode:
    episode_id: str
    task: str
    state: EpisodeState = EpisodeState.CREATED
    validity: Validity = Validity.VALID
    task_verdict: TaskVerdict = TaskVerdict.INCONCLUSIVE
    agent_report: str | None = None
    events: list[AVPEvent] = field(default_factory=list)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    snapshots: dict[str, Snapshot] = field(default_factory=dict)
    verification: list[VerificationResult] = field(default_factory=list)

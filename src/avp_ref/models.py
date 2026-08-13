"""Protocol value objects shared across runtime and evaluators."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Final

from avp_ref.artifacts import ArtifactRef

_EVIDENCE_TYPE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_EVIDENCE_CLASSIFICATIONS: Final[frozenset[str]] = frozenset(
    {"public", "workspace", "subject-visible", "evaluator-confidential", "secret", "regulated"}
)
_VALIDITY_DETAIL_CODE: Final[re.Pattern[str]] = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


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
class ValidityDetail:
    """Structured diagnostic metadata for one invalid evaluation.

    The detail refines ``Validity`` without creating another outcome axis. It is
    intentionally immutable because it becomes part of the auditable Episode
    record once an evaluation is invalidated.
    """

    code: str
    message: str | None = None
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or _VALIDITY_DETAIL_CODE.fullmatch(self.code) is None:
            raise ValueError("validity detail code must be an AVP uppercase token")
        if self.message is not None and (
            not isinstance(self.message, str) or not 1 <= len(self.message) <= 512
        ):
            raise ValueError("validity detail message must contain 1..512 characters when present")
        evidence_ids = tuple(self.evidence_ids)
        if not all(isinstance(item, str) and 1 <= len(item) <= 256 for item in evidence_ids):
            raise ValueError("validity detail evidence ids must contain 1..256 characters")
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("validity detail evidence ids must be unique")
        object.__setattr__(self, "evidence_ids", evidence_ids)

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {"code": self.code}
        if self.message is not None:
            result["message"] = self.message
        if self.evidence_ids:
            result["evidenceIds"] = list(self.evidence_ids)
        return result


@dataclass(frozen=True, slots=True)
class Evidence:
    """Stable verification identity that references immutable Artifact content."""

    evidence_id: str
    evidence_type: str
    artifact: ArtifactRef
    classification: str = "evaluator-confidential"
    producer: str | None = None
    redaction: Mapping[str, object] | None = None
    extensions: Mapping[str, object] | None = None

    @classmethod
    def validate_metadata(
        cls,
        *,
        evidence_id: str,
        evidence_type: str,
        classification: str,
        producer: str | None,
    ) -> None:
        """Validate identity/metadata before content is published to storage."""

        if not isinstance(evidence_id, str) or not 1 <= len(evidence_id) <= 256:
            raise ValueError("evidence_id must contain 1..256 characters")
        if not isinstance(evidence_type, str) or _EVIDENCE_TYPE.fullmatch(evidence_type) is None:
            raise ValueError("evidence_type has an invalid AVP Evidence type token")
        if classification not in _EVIDENCE_CLASSIFICATIONS:
            raise ValueError(f"unsupported evidence classification: {classification!r}")
        if producer is not None and (
            not isinstance(producer, str) or not 1 <= len(producer) <= 512
        ):
            raise ValueError("evidence producer must contain 1..512 characters when present")

    def __post_init__(self) -> None:
        self.validate_metadata(
            evidence_id=self.evidence_id,
            evidence_type=self.evidence_type,
            classification=self.classification,
            producer=self.producer,
        )
        if not isinstance(self.artifact, ArtifactRef):
            raise TypeError("evidence artifact must be an ArtifactRef")
        if self.redaction is not None and not isinstance(self.redaction, Mapping):
            raise TypeError("evidence redaction must be a mapping when present")
        if self.extensions is not None and not isinstance(self.extensions, Mapping):
            raise TypeError("evidence extensions must be a mapping when present")
        object.__setattr__(self, "redaction", _freeze(self.redaction) if self.redaction is not None else None)
        object.__setattr__(self, "extensions", _freeze(self.extensions) if self.extensions is not None else None)

    def to_dict(self) -> dict[str, object]:
        """Serialize to ``schemas/evidence.schema.json`` without embedding content."""

        result: dict[str, object] = {
            "evidenceId": self.evidence_id,
            "type": self.evidence_type,
            "artifact": self.artifact.to_dict(),
            "classification": self.classification,
        }
        if self.producer is not None:
            result["producer"] = self.producer
        if self.redaction is not None:
            result["redaction"] = _thaw(self.redaction)
        if self.extensions is not None:
            result["extensions"] = _thaw(self.extensions)
        return result


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

"""Implementation-neutral value objects used by AVP TCK adapters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TCKAdapterError(RuntimeError):
    """Raised when TCK execution cannot proceed safely or deterministically."""


class TCKStatus(str, Enum):
    """Portable TCK case result values."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass(frozen=True, slots=True)
class TCKCaseResult:
    """One adapter result before serialization into a ConformanceReport."""

    case_id: str
    status: TCKStatus
    detail: str
    evidence: tuple[str, ...] = ()
    skip_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("case_id cannot be empty")
        if not self.detail:
            raise ValueError("detail cannot be empty")
        if len(self.evidence) != len(set(self.evidence)):
            raise ValueError("evidence references must be unique")
        if self.status is TCKStatus.SKIP and not self.skip_reason:
            raise ValueError("SKIP results require skip_reason")
        if self.status is not TCKStatus.SKIP and self.skip_reason is not None:
            raise ValueError("skip_reason is only valid for SKIP results")

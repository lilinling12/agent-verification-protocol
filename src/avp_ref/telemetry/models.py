"""Immutable telemetry configuration and Evidence payload models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from avp_ref.canonical import digest


class TelemetryCompleteness(str, Enum):
    BEST_EFFORT = "BEST_EFFORT"
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    REQUIRED_MISSING = "REQUIRED_MISSING"


@dataclass(frozen=True, slots=True)
class TelemetryPolicy:
    required: bool = False
    capture_sensitive_payloads: bool = False
    max_attribute_length: int = 256

    def __post_init__(self) -> None:
        if self.max_attribute_length < 32:
            raise ValueError("max_attribute_length must be >= 32")
        if self.capture_sensitive_payloads:
            raise ValueError(
                "raw sensitive telemetry capture is not supported by the reference bridge"
            )


@dataclass(frozen=True, slots=True)
class TelemetryDescription:
    name: str
    version: str
    implementation: str
    policy: TelemetryPolicy

    @property
    def identity_digest(self) -> str:
        return digest(
            {
                "name": self.name,
                "version": self.version,
                "implementation": self.implementation,
                "policy": {
                    "required": self.policy.required,
                    "capture_sensitive_payloads": self.policy.capture_sensitive_payloads,
                    "max_attribute_length": self.policy.max_attribute_length,
                },
            }
        )


@dataclass(frozen=True, slots=True)
class TelemetryArtifact:
    """Structured telemetry payload awaiting trusted Artifact publication."""

    episode_id: str
    trace_id: str | None
    root_span_id: str | None
    recorded_events: int
    propagated_requests: int
    completeness: TelemetryCompleteness
    span_count: int

    def to_dict(self) -> dict[str, Any]:
        """Return payload data only; Artifact identity belongs to ArtifactStore."""

        return {
            "episode_id": self.episode_id,
            "trace_id": self.trace_id,
            "root_span_id": self.root_span_id,
            "recorded_events": self.recorded_events,
            "propagated_requests": self.propagated_requests,
            "completeness": self.completeness.value,
            "span_count": self.span_count,
        }

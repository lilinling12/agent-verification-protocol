"""OpenTelemetry bridge for AVP verification runtime.

Telemetry is supporting evidence and diagnostics; authoritative verdicts remain
based on evaluator-owned state and Oracles.
"""

from .bridge import NoopTelemetryBridge, TelemetryBridge
from .models import TelemetryArtifact, TelemetryCompleteness, TelemetryDescription, TelemetryPolicy
from .public import OpenTelemetryBridge

__all__ = [
    "NoopTelemetryBridge",
    "OpenTelemetryBridge",
    "TelemetryArtifact",
    "TelemetryBridge",
    "TelemetryCompleteness",
    "TelemetryDescription",
    "TelemetryPolicy",
]

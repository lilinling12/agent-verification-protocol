"""Consumer-facing OpenTelemetry bridge release identity boundary."""

from __future__ import annotations

from avp_ref import __version__

from .bridge import OpenTelemetryBridge as _BridgeOpenTelemetryBridge
from .models import TelemetryDescription, TelemetryPolicy


class OpenTelemetryBridge(_BridgeOpenTelemetryBridge):
    """Public OTel bridge whose implementation identity matches the distribution."""

    def __init__(
        self,
        policy: TelemetryPolicy | None = None,
        *,
        propagator: object | None = None,
    ) -> None:
        super().__init__(policy, propagator=propagator)
        self._tracer = self._provider.get_tracer("avp.reference", __version__)
        self._description = TelemetryDescription(
            self._description.name,
            __version__,
            self._description.implementation,
            self._description.policy,
        )

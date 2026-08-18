"""Consumer-facing reference runtime boundary.

The execution engine lives in :mod:`avp_ref.runtime.engine`.  This module keeps
consumer discovery metadata separate from engine behavior so implementation
support, configured-instance state, document vocabulary, and AVP conformance
evidence are not collapsed into one ambiguous claim surface.
"""

from __future__ import annotations

from typing import Any

from .engine import ReferenceRuntime as _EngineReferenceRuntime


class ReferenceRuntime(_EngineReferenceRuntime):
    """Public reference runtime with conservative discovery metadata.

    TCK profile identity and conditional-capability declarations are recorded
    by validated ``ConformanceReport`` output.  Runtime discovery therefore
    reports implementation identity, implementation-level interoperability
    surfaces, supported document vocabulary, and current instance configuration
    separately.
    """

    def capabilities(self) -> dict[str, Any]:
        capabilities = super().capabilities()
        scenario_api_version = capabilities.pop("version", None)
        engine_features = dict(capabilities.pop("features", {}))
        capabilities.pop("profiles", None)

        capabilities["implementation_features"] = {
            "scenario_instance_required": engine_features.get(
                "scenario_instance_required"
            ),
            # ``avp.spec/v0.1`` is the Scenario document API vocabulary used by
            # the current reference implementation.  It is not a global AVP
            # protocol/conformance version claim.
            "scenario_api_version": scenario_api_version,
            "environment_adapter_spi": engine_features.get(
                "environment_adapter_spi"
            ),
            "subject_adapter_spi": engine_features.get("subject_adapter_spi"),
            "mcp_protocol": engine_features.get("mcp_protocol"),
        }
        capabilities["instance_configuration"] = {
            "oracle_runner_spi": self._oracle_runner.describe().protocol_version,
            "telemetry_bridge": (
                self._telemetry_bridge.describe().name
                if self._telemetry_bridge is not None
                else None
            ),
        }
        return capabilities

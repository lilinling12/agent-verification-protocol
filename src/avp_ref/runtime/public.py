"""Consumer-facing reference runtime boundary.

The execution engine lives in :mod:`avp_ref.runtime.engine`.  This module keeps
consumer discovery metadata separate from engine behavior so implementation
feature descriptions cannot be mistaken for AVP TCK conformance claims.
"""

from __future__ import annotations

from typing import Any

from .engine import ReferenceRuntime as _EngineReferenceRuntime


class ReferenceRuntime(_EngineReferenceRuntime):
    """Public reference runtime with conservative discovery metadata.

    TCK profile identity and conditional-capability declarations are recorded
    by validated ``ConformanceReport`` output.  The runtime discovery document
    therefore exposes implementation identity and non-normative implementation
    features, but does not self-assert conformance profiles.
    """

    def capabilities(self) -> dict[str, Any]:
        capabilities = super().capabilities()
        capabilities.pop("profiles", None)
        return capabilities

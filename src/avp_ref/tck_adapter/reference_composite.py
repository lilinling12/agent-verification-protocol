"""Composite reference adapter that delegates TCK cases by protocol domain."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Iterable

from .models import TCKAdapterError, TCKCaseResult
from .reference_aligned import AlignedReferenceTCKAdapter
from .reference_environment import ReferenceEnvironmentTCKAdapter
from .reference_evidence import ReferenceEvidenceTCKAdapter
from .reference_oracle import ReferenceOracleTCKAdapter
from .reference_scenario import ReferenceScenarioTCKAdapter
from .reference_security import ReferenceSecurityTCKAdapter
from .reference_security_assurance import ReferenceSecurityAssuranceTCKAdapter
from .reference_security_fault import ReferenceSecurityFaultTCKAdapter


class ReferenceConformanceAdapter:
    """Compose independent reference-domain adapters without overlapping case IDs."""

    def __init__(self, *, capabilities: Iterable[str] = ()) -> None:
        capability_set = frozenset(capabilities)
        self._delegates = (
            AlignedReferenceTCKAdapter(capabilities=capability_set),
            ReferenceEvidenceTCKAdapter(),
            ReferenceOracleTCKAdapter(),
            ReferenceScenarioTCKAdapter(),
            ReferenceEnvironmentTCKAdapter(),
            ReferenceSecurityTCKAdapter(),
            ReferenceSecurityFaultTCKAdapter(),
            ReferenceSecurityAssuranceTCKAdapter(),
        )
        owners: dict[str, object] = {}
        for delegate in self._delegates:
            for case_id in delegate.supported_case_ids:
                if case_id in owners:
                    raise TCKAdapterError(
                        f"reference TCK case has multiple domain adapters: {case_id}"
                    )
                owners[case_id] = delegate
        self._owners = owners

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return frozenset(self._owners)

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("TCK case metadata.id is missing")
        delegate = self._owners.get(case_id)
        if delegate is None:
            raise TCKAdapterError(
                f"reference implementation has no adapter for TCK case {case_id}"
            )
        return delegate.evaluate(case)

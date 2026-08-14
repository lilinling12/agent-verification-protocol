"""Reference TCK adapter for SecurityAssurance honesty."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from avp_ref.runtime import ReferenceRuntime
from avp_ref.security import SecurityAssurance

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


class ReferenceSecurityAssuranceTCKAdapter:
    """Evaluate the machine-readable SecurityAssurance declaration."""

    _CASE_ID = "AVP-TCK-SECURITY-ASSURANCE-HONESTY-001"

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return frozenset({self._CASE_ID})

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        if case_id != self._CASE_ID:
            raise TCKAdapterError(
                f"unsupported reference Security assurance TCK case: {case_id}"
            )

        vector = self._vector(case, case_id)
        expected_isolation = vector.get("expectedIsolation")
        if not isinstance(expected_isolation, Mapping):
            raise TCKAdapterError(f"{case_id} expectedIsolation must be an object")

        declaration = SecurityAssurance.baseline_reference()
        declaration.validate()
        actual = declaration.to_dict()

        profiles = ReferenceRuntime().capabilities().get("profiles", ())
        security_profile_advertised = any(
            str(profile).lower() in {"avp-security", "avp-security-v0.1"}
            for profile in profiles
        )

        expected = {str(key): str(value) for key, value in expected_isolation.items()}
        valid = (
            actual["isolation"] == expected
            and security_profile_advertised is False
        )
        return TCKCaseResult(
            case_id,
            TCKStatus.PASS if valid else TCKStatus.FAIL,
            (
                "base ReferenceRuntime declares only demonstrated Security isolation dimensions and does not advertise full Security conformance"
                if valid
                else "base ReferenceRuntime Security assurance declaration is inflated or its profile advertisement is inconsistent"
            ),
        )

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("Security TCK case metadata.id is missing")
        return case_id

    @staticmethod
    def _vector(case: Mapping[str, Any], case_id: str) -> Mapping[str, Any]:
        vector = case.get("vector")
        if not isinstance(vector, Mapping):
            raise TCKAdapterError(f"{case_id} vector must be an object")
        return vector

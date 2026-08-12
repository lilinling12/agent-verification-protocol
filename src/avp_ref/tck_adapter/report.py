"""Conformance report construction for AVP TCK execution."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping

from avp_ref.canonical import digest

from .loader import TCKRepository
from .reference import TCKCaseResult


def build_report(
    repository: TCKRepository,
    *,
    profile: str,
    implementation: Mapping[str, object],
    results: Iterable[TCKCaseResult],
) -> dict[str, object]:
    """Build the canonical report payload.

    The report is deliberately a plain JSON-compatible object. Serialization,
    signing, and transport are separate concerns.
    """

    result_list = list(results)
    if not isinstance(implementation, Mapping):
        raise TypeError("implementation must be a mapping")
    implementation_identity = dict(implementation)
    return {
        "apiVersion": "avp.tck/v0.1",
        "kind": "ConformanceReport",
        "metadata": {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "reportDigest": None,
        },
        "profile": profile,
        "tck": {
            "registryVersion": repository.version,
            "registryDigest": repository.registry_digest,
        },
        "implementation": {
            "identity": implementation_identity,
            "identityDigest": digest(implementation_identity),
        },
        "cases": [
            {
                "id": item.case_id,
                "status": item.status.value,
                "detail": item.detail,
                "evidence": list(item.evidence),
            }
            for item in result_list
        ],
        "summary": {
            "passed": sum(item.status.value == "PASS" for item in result_list),
            "failed": sum(item.status.value == "FAIL" for item in result_list),
            "skipped": sum(item.status.value == "SKIP" for item in result_list),
        },
    }


"""Conformance report construction for AVP TCK execution."""

from __future__ import annotations

from typing import Iterable, Mapping

from avp_ref.canonical import digest

from .loader import TCKRepository
from .reference import TCKCaseResult, TCKStatus


def build_report(
    repository: TCKRepository,
    *,
    profile: str,
    profile_version: str,
    implementation: Mapping[str, object],
    capabilities: Iterable[str],
    results: Iterable[TCKCaseResult],
) -> dict[str, object]:
    """Build the JSON-schema-compatible conformance report.

    Report construction is deterministic except for caller-provided identity
    metadata. Signing, persistence and transport remain outside this layer.
    """

    result_list = list(results)
    implementation_identity = dict(implementation)
    capability_list = sorted(set(capabilities))
    cases: list[dict[str, object]] = []
    for result in result_list:
        item: dict[str, object] = {
            "id": result.case_id,
            "status": result.status.value,
            "evidence": list(result.evidence),
        }
        if result.status is TCKStatus.SKIP:
            item["skipReason"] = result.skip_reason
        cases.append(item)

    return {
        "apiVersion": "avp.tck/v0.1",
        "kind": "ConformanceReport",
        "profile": {
            "name": profile,
            "version": profile_version,
        },
        "implementation": {
            "name": str(implementation_identity.get("name", "unknown")),
            "version": str(implementation_identity.get("version", "unknown")),
            "identityDigest": digest(implementation_identity),
        },
        "tck": {
            "version": repository.version,
            "registryDigest": repository.registry_digest,
        },
        "declaredCapabilities": capability_list,
        "cases": cases,
        "summary": {
            "total": len(result_list),
            "passed": sum(result.status is TCKStatus.PASS for result in result_list),
            "failed": sum(result.status is TCKStatus.FAIL for result in result_list),
            "skipped": sum(result.status is TCKStatus.SKIP for result in result_list),
        },
    }

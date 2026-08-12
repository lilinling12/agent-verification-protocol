"""Conformance report construction for AVP TCK execution."""

from __future__ import annotations

from typing import Iterable, Mapping

from avp_ref.canonical import digest

from .loader import TCKRepository
from .models import TCKCaseResult, TCKStatus


def build_report(
    repository: TCKRepository,
    *,
    profile: str,
    profile_version: str,
    implementation: Mapping[str, object],
    capabilities: Iterable[str],
    results: Iterable[TCKCaseResult],
) -> dict[str, object]:
    """Build a deterministic JSON-schema-compatible conformance report."""

    result_list = list(results)
    name = implementation.get("name")
    version = implementation.get("version")
    if not isinstance(name, str) or not name:
        raise ValueError("implementation.name must be a non-empty string")
    if not isinstance(version, str) or not version:
        raise ValueError("implementation.version must be a non-empty string")
    implementation_identity = {"name": name, "version": version}
    capability_list = sorted(set(capabilities))
    cases: list[dict[str, object]] = []
    for result in result_list:
        item: dict[str, object] = {
            "id": result.case_id,
            "status": result.status.value,
            "detail": result.detail,
            "evidence": list(result.evidence),
        }
        if result.status is TCKStatus.SKIP:
            item["skipReason"] = result.skip_reason
        cases.append(item)

    return {
        "apiVersion": "avp.tck/v0.1",
        "kind": "ConformanceReport",
        "profile": {"name": profile, "version": profile_version},
        "implementation": {
            **implementation_identity,
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

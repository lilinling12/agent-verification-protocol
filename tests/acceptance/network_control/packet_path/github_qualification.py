"""Trusted-main qualification binding for Network Control PTL-002.

The PTL-001 local qualification remains mechanism-local infrastructure evidence.
This module wraps one exact local qualification document with the repository
semantic baseline used by a trusted-main GitHub run and verifies that binding
before packet-path matrix execution. It does not issue a C1-C12 verdict.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Mapping

from ..evidence_core import EvidenceMaterializationError
from ..witness_evidence import CaptureAssurance

_GITHUB_QUALIFICATION_FORMAT = (
    "avp-project-network-packet-path-github-qualification-v0.1"
)
_LOCAL_QUALIFICATION_FORMAT = (
    "avp-project-network-packet-path-local-qualification-v0.1"
)
_HEX_COMMIT_RE = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}\Z")
_ASSURANCE_KEYS = (
    "egressCoverageVerified",
    "directionalityVerified",
    "offloadNormalizationVerified",
    "preSynConnectGapClosed",
)


@dataclass(frozen=True, slots=True)
class PacketPathGitHubQualification:
    """Verified same-run qualification facts admitted by the PTL-002 runner."""

    run_id: str
    semantic_baseline_commit: str
    capture_assurance: CaptureAssurance
    local_qualification_sha256: str


def build_github_qualification(
    *,
    local_document: Mapping[str, object],
    semantic_baseline_commit: str,
) -> bytes:
    """Wrap exact PTL-001 qualification output with a reviewed main commit.

    The local document is embedded verbatim as JSON data and independently
    content-addressed. A not-ready document is still serializable for diagnostic
    retention; only ``verify_github_qualification`` admits ready evidence.
    """

    if not _HEX_COMMIT_RE.fullmatch(semantic_baseline_commit):
        raise EvidenceMaterializationError(
            "packet-path GitHub qualification semantic baseline must be exact hex commit"
        )
    normalized = _validate_local_document(local_document)
    local_bytes = _exact_json(normalized)
    document = {
        "format": _GITHUB_QUALIFICATION_FORMAT,
        "runId": normalized["runId"],
        "semanticBaselineCommit": semantic_baseline_commit,
        "ready": normalized["ready"],
        "captureAssurance": normalized["captureAssurance"],
        "localQualificationSha256": hashlib.sha256(local_bytes).hexdigest(),
        "localQualification": normalized,
    }
    return _exact_json(document)


def verify_github_qualification(
    exact_bytes: bytes,
    *,
    expected_semantic_baseline_commit: str,
    expected_run_id: str,
) -> PacketPathGitHubQualification:
    """Admit only a ready qualification for this exact main/run identity."""

    if not isinstance(exact_bytes, bytes) or not exact_bytes:
        raise EvidenceMaterializationError(
            "packet-path GitHub qualification must be non-empty exact bytes"
        )
    try:
        document = json.loads(exact_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceMaterializationError(
            "packet-path GitHub qualification is not valid UTF-8 JSON"
        ) from exc
    if not isinstance(document, dict):
        raise EvidenceMaterializationError(
            "packet-path GitHub qualification root must be an object"
        )
    if document.get("format") != _GITHUB_QUALIFICATION_FORMAT:
        raise EvidenceMaterializationError(
            "packet-path GitHub qualification format is invalid"
        )
    if document.get("semanticBaselineCommit") != expected_semantic_baseline_commit:
        raise EvidenceMaterializationError(
            "packet-path GitHub qualification semantic baseline drift"
        )
    if document.get("runId") != expected_run_id:
        raise EvidenceMaterializationError(
            "packet-path GitHub qualification run identity drift"
        )
    ready = _required_bool(document, "ready")
    if not ready:
        raise EvidenceMaterializationError(
            "packet-path GitHub qualification is not ready"
        )

    local = document.get("localQualification")
    if not isinstance(local, dict):
        raise EvidenceMaterializationError(
            "packet-path GitHub qualification lacks local qualification object"
        )
    normalized_local = _validate_local_document(local)
    local_bytes = _exact_json(normalized_local)
    declared_digest = document.get("localQualificationSha256")
    actual_digest = hashlib.sha256(local_bytes).hexdigest()
    if declared_digest != actual_digest:
        raise EvidenceMaterializationError(
            "packet-path local qualification content-address binding mismatch"
        )
    if normalized_local["runId"] != expected_run_id:
        raise EvidenceMaterializationError(
            "packet-path embedded local qualification run identity drift"
        )
    if normalized_local["ready"] is not True:
        raise EvidenceMaterializationError(
            "packet-path embedded local qualification is not ready"
        )

    top_assurance = _assurance_document(document.get("captureAssurance"))
    local_assurance = _assurance_document(normalized_local["captureAssurance"])
    if top_assurance != local_assurance:
        raise EvidenceMaterializationError(
            "packet-path GitHub/local capture assurance binding mismatch"
        )
    if not all(top_assurance[key] for key in _ASSURANCE_KEYS):
        raise EvidenceMaterializationError(
            "packet-path GitHub qualification capture assurance is incomplete"
        )

    problems = normalized_local["problems"]
    cleanup = normalized_local["cleanup"]
    assert isinstance(problems, list)
    assert isinstance(cleanup, dict)
    if problems:
        raise EvidenceMaterializationError(
            "ready packet-path qualification unexpectedly retains problems"
        )
    if cleanup["problems"] or cleanup["residualResources"]:
        raise EvidenceMaterializationError(
            "ready packet-path qualification cleanup is not residual-free"
        )

    return PacketPathGitHubQualification(
        run_id=expected_run_id,
        semantic_baseline_commit=expected_semantic_baseline_commit,
        capture_assurance=CaptureAssurance(
            egress_coverage_verified=top_assurance["egressCoverageVerified"],
            directionality_verified=top_assurance["directionalityVerified"],
            offload_normalization_verified=top_assurance["offloadNormalizationVerified"],
            pre_syn_connect_gap_closed=top_assurance["preSynConnectGapClosed"],
        ),
        local_qualification_sha256=actual_digest,
    )


def _validate_local_document(document: Mapping[str, object]) -> dict[str, object]:
    if document.get("format") != _LOCAL_QUALIFICATION_FORMAT:
        raise EvidenceMaterializationError(
            "packet-path local qualification format is invalid"
        )
    run_id = document.get("runId")
    if not isinstance(run_id, str) or not run_id:
        raise EvidenceMaterializationError(
            "packet-path local qualification runId must be non-empty string"
        )
    ready = _required_bool(document, "ready")
    problems = document.get("problems")
    if not isinstance(problems, list) or not all(
        isinstance(item, str) and item for item in problems
    ):
        raise EvidenceMaterializationError(
            "packet-path local qualification problems must be string array"
        )
    assurance = _assurance_document(document.get("captureAssurance"))
    cleanup = document.get("cleanup")
    if not isinstance(cleanup, dict):
        raise EvidenceMaterializationError(
            "packet-path local qualification cleanup must be object"
        )
    cleanup_problems = cleanup.get("problems")
    residual = cleanup.get("residualResources")
    for name, value in (
        ("problems", cleanup_problems),
        ("residualResources", residual),
    ):
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item for item in value
        ):
            raise EvidenceMaterializationError(
                f"packet-path local qualification cleanup {name} must be string array"
            )
    facts = document.get("facts")
    if not isinstance(facts, list):
        raise EvidenceMaterializationError(
            "packet-path local qualification facts must be array"
        )
    return {
        "format": _LOCAL_QUALIFICATION_FORMAT,
        "runId": run_id,
        "ready": ready,
        "problems": list(problems),
        "captureAssurance": assurance,
        "facts": facts,
        "cleanup": {
            "problems": list(cleanup_problems),
            "residualResources": list(residual),
        },
    }


def _assurance_document(value: object) -> dict[str, bool]:
    if not isinstance(value, dict) or set(value) != set(_ASSURANCE_KEYS):
        raise EvidenceMaterializationError(
            "packet-path capture assurance must contain the exact reviewed fields"
        )
    result: dict[str, bool] = {}
    for key in _ASSURANCE_KEYS:
        field = value.get(key)
        if not isinstance(field, bool):
            raise EvidenceMaterializationError(
                f"packet-path capture assurance field {key!r} must be boolean"
            )
        result[key] = field
    return result


def _required_bool(document: Mapping[str, object], key: str) -> bool:
    value = document.get(key)
    if not isinstance(value, bool):
        raise EvidenceMaterializationError(
            f"packet-path qualification field {key!r} must be boolean"
        )
    return value


def _exact_json(document: Mapping[str, object]) -> bytes:
    return json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

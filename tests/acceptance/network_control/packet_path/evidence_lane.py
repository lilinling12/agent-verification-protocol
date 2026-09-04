"""PTL-002 packet-path privileged evidence-lane contract.

This module fixes the reviewed case matrix and strict evidence-document parsing
used by the future trusted-main privileged runner. It is mechanism-local project
evidence plumbing, not a provider SPI, generic backend, protocol schema, or
workflow-success oracle.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from ..evidence_core import AssessmentClass, EvidenceMaterializationError, InitiationFacts
from .negative_assemblies import PacketPathNegativeMode

_MANIFEST_FORMAT = "avp-project-network-packet-path-github-evidence-manifest-v0.1"


@dataclass(frozen=True, slots=True)
class PacketPathLaneCase:
    """One reviewed PTL-002 matrix case and its expected portable assessment."""

    slug: str
    negative_mode: PacketPathNegativeMode | None
    expected_classification: AssessmentClass
    expected_problem_prefix: str

    def __post_init__(self) -> None:
        if not self.slug or "/" in self.slug or "\\" in self.slug:
            raise EvidenceMaterializationError("packet-path lane case slug is invalid")
        if not isinstance(self.expected_classification, AssessmentClass):
            raise EvidenceMaterializationError("packet-path lane expected classification must be typed")
        if self.negative_mode is None:
            if self.slug != "positive":
                raise EvidenceMaterializationError("only the positive lane case may omit a negative mode")
            if self.expected_classification is not AssessmentClass.SATISFIED:
                raise EvidenceMaterializationError("positive packet-path lane case must expect SATISFIED")
            if self.expected_problem_prefix:
                raise EvidenceMaterializationError("positive packet-path lane case cannot expect a problem")
        elif self.expected_classification is AssessmentClass.SATISFIED:
            raise EvidenceMaterializationError("negative packet-path lane case cannot expect SATISFIED")


_PACKET_PATH_LANE_CASES = (
    PacketPathLaneCase("positive", None, AssessmentClass.SATISFIED, ""),
    PacketPathLaneCase(
        "bypass-fault",
        PacketPathNegativeMode.BYPASS_FAULT,
        AssessmentClass.SEMANTIC_VIOLATION,
        "C4:",
    ),
    PacketPathLaneCase(
        "early-activation",
        PacketPathNegativeMode.EARLY_ACTIVATION,
        AssessmentClass.SEMANTIC_VIOLATION,
        "C3:",
    ),
    PacketPathLaneCase(
        "false-settled",
        PacketPathNegativeMode.FALSE_SETTLED,
        AssessmentClass.EVIDENCE_INVALID,
        "C1:missing-observation",
    ),
    PacketPathLaneCase(
        "false-recovery",
        PacketPathNegativeMode.FALSE_RECOVERY,
        AssessmentClass.EVIDENCE_INVALID,
        "C1:missing-observation",
    ),
    PacketPathLaneCase(
        "schedule-leak",
        PacketPathNegativeMode.SCHEDULE_LEAK,
        AssessmentClass.SEMANTIC_VIOLATION,
        "C12:",
    ),
    PacketPathLaneCase(
        "hidden-retry-fallback",
        PacketPathNegativeMode.HIDDEN_RETRY_FALLBACK,
        AssessmentClass.SEMANTIC_VIOLATION,
        "C10:",
    ),
    PacketPathLaneCase(
        "collateral-target",
        PacketPathNegativeMode.COLLATERAL_TARGET,
        AssessmentClass.SEMANTIC_VIOLATION,
        "C6:",
    ),
    PacketPathLaneCase(
        "residual-cleanup",
        PacketPathNegativeMode.RESIDUAL_STATE_CLEANUP_FAILURE,
        AssessmentClass.SEMANTIC_VIOLATION,
        "C11:",
    ),
)


def packet_path_lane_cases() -> tuple[PacketPathLaneCase, ...]:
    """Return the complete, ordered PTL-002 case matrix."""

    return _PACKET_PATH_LANE_CASES


def lane_case(slug: str) -> PacketPathLaneCase:
    """Resolve exactly one reviewed case by stable artifact slug."""

    matches = tuple(item for item in _PACKET_PATH_LANE_CASES if item.slug == slug)
    if len(matches) != 1:
        raise EvidenceMaterializationError(f"unknown packet-path lane case: {slug!r}")
    return matches[0]


def parse_front_initiations(document: Mapping[str, object]) -> InitiationFacts:
    """Parse one retained W-front witness document without truthiness coercion."""

    channel_facts = document.get("channelFacts")
    validity = document.get("validityProblems")
    drops = document.get("captureDrops")
    if not isinstance(channel_facts, list) or len(channel_facts) != 1:
        raise EvidenceMaterializationError("packet-path witness must contain exactly one channel fact")
    facts = channel_facts[0]
    if not isinstance(facts, dict) or facts.get("channel") != "W-front":
        raise EvidenceMaterializationError("packet-path witness channel must be W-front")
    if not isinstance(validity, list) or not all(isinstance(item, str) for item in validity):
        raise EvidenceMaterializationError("packet-path witness validity problems are invalid")
    if isinstance(drops, bool) or not isinstance(drops, int) or drops < 0:
        raise EvidenceMaterializationError("packet-path witness captureDrops must be a non-negative integer")
    problems = tuple(validity)
    if drops:
        problems += (f"capture-drops:{drops}",)
    return InitiationFacts(
        channel="W-front",
        total_initiations=_required_non_negative_int(facts, "totalInitiations"),
        expected_target_initiations=_required_non_negative_int(facts, "expectedTargetInitiations"),
        alternate_target_initiations=_required_non_negative_int(facts, "alternateTargetInitiations"),
        raw_syn_packets=_required_non_negative_int(facts, "rawSynPackets"),
        retransmitted_syn_packets=_required_non_negative_int(facts, "retransmittedSynPackets"),
        validity_problems=problems,
    )


def assert_expected_assessment(
    *,
    case: PacketPathLaneCase,
    classification: AssessmentClass,
    primary_problem: str | None,
) -> None:
    """Fail closed when the unchanged comparator does not reject/accept as reviewed."""

    if classification is not case.expected_classification:
        raise EvidenceMaterializationError(
            f"packet-path case {case.slug!r} classification {classification.value!r} "
            f"!= expected {case.expected_classification.value!r}"
        )
    problem = primary_problem or ""
    if case.expected_problem_prefix and not problem.startswith(case.expected_problem_prefix):
        raise EvidenceMaterializationError(
            f"packet-path case {case.slug!r} primary problem {problem!r} does not start "
            f"with {case.expected_problem_prefix!r}"
        )
    if not case.expected_problem_prefix and problem:
        raise EvidenceMaterializationError(
            f"packet-path positive case unexpectedly reported primary problem {problem!r}"
        )


def build_execution_manifest(
    *,
    root: Path,
    repository: str,
    commit: str,
    run_id: str,
    run_attempt: str,
    workflow: str,
) -> bytes:
    """Build exact content-addressed manifest bytes for one retained PTL-002 bundle."""

    evidence_root = Path(root)
    if not evidence_root.is_dir():
        raise EvidenceMaterializationError("packet-path evidence root is missing")
    for name, value in (
        ("repository", repository),
        ("commit", commit),
        ("runId", run_id),
        ("runAttempt", run_attempt),
        ("workflow", workflow),
    ):
        if not value:
            raise EvidenceMaterializationError(f"packet-path manifest {name} is required")

    files = []
    for path in sorted(item for item in evidence_root.rglob("*") if item.is_file()):
        if path.name == "MANIFEST.json":
            continue
        payload = path.read_bytes()
        files.append(
            {
                "path": path.relative_to(evidence_root).as_posix(),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size": len(payload),
            }
        )
    document = {
        "format": _MANIFEST_FORMAT,
        "repository": repository,
        "commit": commit,
        "runId": run_id,
        "runAttempt": run_attempt,
        "workflow": workflow,
        "files": files,
    }
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_execution_manifest(*, root: Path, exact_bytes: bytes) -> None:
    """Verify every retained file named by an exact PTL-002 execution manifest."""

    try:
        document = json.loads(exact_bytes)
    except json.JSONDecodeError as exc:
        raise EvidenceMaterializationError("packet-path execution manifest is not valid JSON") from exc
    if not isinstance(document, dict) or document.get("format") != _MANIFEST_FORMAT:
        raise EvidenceMaterializationError("packet-path execution manifest format is invalid")
    files = document.get("files")
    if not isinstance(files, list):
        raise EvidenceMaterializationError("packet-path execution manifest files are invalid")
    seen: set[str] = set()
    evidence_root = Path(root).resolve()
    for item in files:
        if not isinstance(item, dict):
            raise EvidenceMaterializationError("packet-path execution manifest file entry is invalid")
        relative = item.get("path")
        digest = item.get("sha256")
        size = item.get("size")
        if not isinstance(relative, str) or not relative or relative in seen:
            raise EvidenceMaterializationError("packet-path execution manifest path is invalid or duplicated")
        seen.add(relative)
        candidate = (evidence_root / relative).resolve()
        try:
            candidate.relative_to(evidence_root)
        except ValueError as exc:
            raise EvidenceMaterializationError("packet-path execution manifest path escapes evidence root") from exc
        payload = candidate.read_bytes()
        if (
            not isinstance(digest, str)
            or hashlib.sha256(payload).hexdigest() != digest
            or isinstance(size, bool)
            or not isinstance(size, int)
            or len(payload) != size
        ):
            raise EvidenceMaterializationError(
                f"packet-path execution manifest integrity mismatch for {relative!r}"
            )


def _required_non_negative_int(document: Mapping[str, object], key: str) -> int:
    value = document.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EvidenceMaterializationError(f"packet-path witness field {key!r} must be non-negative integer")
    return value

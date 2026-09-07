"""NPR-011 retained-evidence cross-mechanism reassessment.

Project acceptance-evidence plumbing only. This module never controls a network
fault and never defines provider behavior. It verifies two independently adopted
source bundles, restores provider-neutral observations, and delegates C1-C12
judgment to the existing portable comparator.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import json
import posixpath
import struct
import zlib
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .evidence_core import (
    ArtifactRef,
    AssessmentClass,
    EvidenceAssessment,
    EvidenceMaterializationError,
    EvidencePlan,
    ExchangeProgram,
    InitiationFacts,
    MaterializedEndpoint,
    SealedPlan,
    artifact_ref,
)
from .portable_comparator import (
    AttemptObservation,
    PortableEvidenceObservations,
    compare_portable_evidence,
)

_RECORD_FORMAT = "avp-project-network-cross-mechanism-reassessment-v0.1"
_PLAN_FORMAT = "avp-project-network-evidence-plan-v0.1"
_AEP_PATH = "rfcs/AEP-0012-network-control-resource-profile.md"
_PHASES = (
    "baseline",
    "pre-trigger",
    "trigger",
    "activation-settlement",
    "subject-active-cut",
    "non-target-control",
    "clear",
    "recovery-1",
    "recovery-2",
    "stability",
    "cleanup-noninterference",
)
_NEGATIVE_FAMILIES = (
    "BypassFault",
    "EarlyActivation",
    "FalseSettled",
    "FalseRecovery",
    "ScheduleLeak",
    "HiddenRetry/Fallback",
    "CollateralTarget",
    "ResidualStateCleanupFailure",
)
_TEL_CASES = {
    "positive": (None, None),
    "bypass-fault": ("BypassFault", None),
    "early-activation": ("EarlyActivation", None),
    "false-settled": ("FalseSettled", None),
    "false-recovery": ("FalseRecovery", None),
    "schedule-leak": ("ScheduleLeak", None),
    "hidden-retry-front": ("HiddenRetry/Fallback", "front-extra-connect"),
    "hidden-retry-upstream": ("HiddenRetry/Fallback", "upstream-extra-connect"),
    "collateral-target": ("CollateralTarget", None),
    "residual-cleanup": ("ResidualStateCleanupFailure", None),
}
_PTL_CASES = {
    "positive": None,
    "bypass-fault": "BypassFault",
    "early-activation": "EarlyActivation",
    "false-settled": "FalseSettled",
    "false-recovery": "FalseRecovery",
    "schedule-leak": "ScheduleLeak",
    "hidden-retry-fallback": "HiddenRetry/Fallback",
    "collateral-target": "CollateralTarget",
    "residual-cleanup": "ResidualStateCleanupFailure",
}
_MAX_ENTRY = 4 * 1024 * 1024
_MAX_TOTAL = 32 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class SourceExpectation:
    mechanism_class: str
    artifact_id: str
    zip_sha256: str
    source_commit: str
    workflow_run_id: str
    manifest_format: str
    manifest_entries: int
    historical_comparator_blob: str

    def __post_init__(self) -> None:
        _hex(self.zip_sha256, 64, "source ZIP sha256")
        _hex(self.source_commit, 40, "source commit")
        _hex(self.historical_comparator_blob, 40, "historical comparator Git blob")
        if not all((self.mechanism_class, self.artifact_id, self.workflow_run_id, self.manifest_format)):
            raise EvidenceMaterializationError("source expectation contains an empty identity")
        if self.manifest_entries <= 0:
            raise EvidenceMaterializationError("manifest entry count must be positive")


@dataclass(frozen=True, slots=True)
class SemanticBinding:
    aep_path: str
    aep_git_blob: str
    current_comparator_path: str
    current_comparator_git_blob: str
    candidate_parent_commit: str

    def __post_init__(self) -> None:
        if self.aep_path != _AEP_PATH or not self.current_comparator_path:
            raise EvidenceMaterializationError("repository semantic binding is invalid")
        _hex(self.aep_git_blob, 40, "AEP Git blob")
        _hex(self.current_comparator_git_blob, 40, "comparator Git blob")
        _hex(self.candidate_parent_commit, 40, "candidate parent commit")


@dataclass(frozen=True, slots=True)
class _Case:
    slug: str
    family: str | None
    variant: str | None
    plan: SealedPlan
    observations: PortableEvidenceObservations
    historical: EvidenceAssessment
    result_ref: ArtifactRef
    implementation_ref: ArtifactRef
    provenance_ref: ArtifactRef


class _Bundle:
    def __init__(self, path: Path, expected: SourceExpectation) -> None:
        payload = Path(path).read_bytes()
        if hashlib.sha256(payload).hexdigest() != expected.zip_sha256:
            raise EvidenceMaterializationError(f"{expected.mechanism_class} source ZIP digest drift")
        self.expected = expected
        self._zip = zipfile.ZipFile(io.BytesIO(payload), "r")
        self._names = self._validate_entries()
        self.manifest = self._verify_manifest()

    def __enter__(self) -> "_Bundle":
        return self

    def __exit__(self, *_: object) -> None:
        self._zip.close()

    def read(self, path: str) -> bytes:
        if path not in self._names:
            raise EvidenceMaterializationError(f"source bundle file missing: {path}")
        return self._zip.read(path)

    def json(self, path: str) -> dict[str, object]:
        return _json(self.read(path), path)

    def artifact(self, slug: str, document: Mapping[str, object]) -> tuple[ArtifactRef, bytes]:
        ref = _ref(document)
        path = f"matrix/{slug}/artifacts/sha256/{ref.sha256[:2]}/{ref.sha256}"
        payload = self.read(path)
        if len(payload) != ref.size or hashlib.sha256(payload).hexdigest() != ref.sha256:
            raise EvidenceMaterializationError(f"content-addressed artifact drift: {path}")
        return ref, payload

    def _validate_entries(self) -> set[str]:
        names: set[str] = set()
        total = 0
        for info in self._zip.infolist():
            name = info.filename
            mode = (info.external_attr >> 16) & 0o170000
            if name in names or not _safe_path(name) or mode == 0o120000:
                raise EvidenceMaterializationError(f"unsafe or duplicate ZIP entry: {name!r}")
            if info.file_size > _MAX_ENTRY:
                raise EvidenceMaterializationError(f"ZIP entry exceeds bounded size: {name!r}")
            total += info.file_size
            if total > _MAX_TOTAL:
                raise EvidenceMaterializationError("source ZIP exceeds bounded uncompressed size")
            names.add(name)
        if "MANIFEST.json" not in names:
            raise EvidenceMaterializationError("source ZIP is missing MANIFEST.json")
        return names

    def _verify_manifest(self) -> dict[str, object]:
        doc = self.json("MANIFEST.json")
        exp = self.expected
        if (
            doc.get("format") != exp.manifest_format
            or doc.get("commit") != exp.source_commit
            or str(doc.get("runId")) != exp.workflow_run_id
        ):
            raise EvidenceMaterializationError("source manifest identity drift")
        files = doc.get("files")
        if not isinstance(files, list) or len(files) != exp.manifest_entries:
            raise EvidenceMaterializationError("source manifest entry-count drift")
        declared: set[str] = set()
        for item in files:
            if not isinstance(item, dict):
                raise EvidenceMaterializationError("source manifest entry must be an object")
            path = item.get("path")
            if not isinstance(path, str) or path in declared or not _safe_path(path):
                raise EvidenceMaterializationError("source manifest path is invalid or duplicated")
            declared.add(path)
            payload = self.read(path)
            if (
                item.get("sha256") != hashlib.sha256(payload).hexdigest()
                or item.get("size") != len(payload)
            ):
                raise EvidenceMaterializationError(f"source manifest integrity mismatch: {path}")
        if declared != self._names - {"MANIFEST.json"}:
            raise EvidenceMaterializationError("source manifest does not cover the exact ZIP payload set")
        return doc


def build_reassessment_record(
    *,
    terminating_zip: Path,
    terminating_expectation: SourceExpectation,
    packet_path_zip: Path,
    packet_path_expectation: SourceExpectation,
    semantic_binding: SemanticBinding,
) -> bytes:
    with _Bundle(terminating_zip, terminating_expectation) as tel, _Bundle(
        packet_path_zip, packet_path_expectation
    ) as ptl:
        tel_cases = tuple(_load_tel(tel, slug) for slug in _TEL_CASES)
        ptl_cases = tuple(_load_ptl(ptl, slug) for slug in _PTL_CASES)
        _matrix(tel_cases, "terminating-intercepting")
        _matrix(ptl_cases, "packet-path")
        _compatible(tel_cases, ptl_cases)
        doc = {
            "format": _RECORD_FORMAT,
            "reassessmentKind": "retained-evidence",
            "candidateParentCommit": semantic_binding.candidate_parent_commit,
            "semanticSource": {
                "path": semantic_binding.aep_path,
                "gitBlob": semantic_binding.aep_git_blob,
            },
            "currentComparator": {
                "path": semantic_binding.current_comparator_path,
                "gitBlob": semantic_binding.current_comparator_git_blob,
            },
            "portableMatrix": {
                "observationBudgetNs": 1_000_000_000,
                "phaseProgram": list(_PHASES),
                "requiredNegativeFamilies": list(_NEGATIVE_FAMILIES),
            },
            "mechanisms": {
                "terminating-intercepting": _mechanism(
                    terminating_expectation, tel.manifest, tel_cases, semantic_binding.aep_git_blob
                ),
                "packet-path": _mechanism(
                    packet_path_expectation, ptl.manifest, ptl_cases, semantic_binding.aep_git_blob
                ),
            },
        }
    exact = _canonical(doc)
    verify_reassessment_record(exact, semantic_binding=semantic_binding)
    return exact


def verify_reassessment_record(
    exact_bytes: bytes, *, semantic_binding: SemanticBinding | None = None
) -> dict[str, object]:
    doc = _json(exact_bytes, "cross-mechanism reassessment")
    if _canonical(doc) != exact_bytes:
        raise EvidenceMaterializationError("cross-mechanism reassessment JSON is not canonical exact bytes")
    if doc.get("format") != _RECORD_FORMAT or doc.get("reassessmentKind") != "retained-evidence":
        raise EvidenceMaterializationError("cross-mechanism reassessment format drift")

    semantic = _obj(doc, "semanticSource")
    comparator = _obj(doc, "currentComparator")
    parent = _str(doc, "candidateParentCommit")
    aep_blob = _str(semantic, "gitBlob")
    comparator_blob = _str(comparator, "gitBlob")
    _hex(aep_blob, 40, "reassessment AEP Git blob")
    _hex(comparator_blob, 40, "reassessment comparator Git blob")
    _hex(parent, 40, "reassessment parent commit")
    if semantic.get("path") != _AEP_PATH:
        raise EvidenceMaterializationError("reassessment AEP path drift")
    if semantic_binding is not None and (
        aep_blob != semantic_binding.aep_git_blob
        or comparator.get("path") != semantic_binding.current_comparator_path
        or comparator_blob != semantic_binding.current_comparator_git_blob
        or parent != semantic_binding.candidate_parent_commit
    ):
        raise EvidenceMaterializationError("cross-mechanism reassessment repository binding drift")

    portable = _obj(doc, "portableMatrix")
    if (
        portable.get("observationBudgetNs") != 1_000_000_000
        or portable.get("phaseProgram") != list(_PHASES)
        or portable.get("requiredNegativeFamilies") != list(_NEGATIVE_FAMILIES)
    ):
        raise EvidenceMaterializationError("cross-mechanism portable matrix drift")

    mechanisms = _obj(doc, "mechanisms")
    if set(mechanisms) != {"terminating-intercepting", "packet-path"}:
        raise EvidenceMaterializationError("cross-mechanism record must contain exactly two mechanism classes")
    restored: dict[str, tuple[_Case, ...]] = {}
    for name in ("terminating-intercepting", "packet-path"):
        mechanism = _obj(mechanisms, name)
        source = _obj(mechanism, "source")
        if source.get("semanticGitBlob") != aep_blob:
            raise EvidenceMaterializationError(f"{name} semantic Git blob drift")
        _hex(_str(source, "historicalComparatorGitBlob"), 40, "historical comparator Git blob")
        items = mechanism.get("cases")
        if not isinstance(items, list):
            raise EvidenceMaterializationError(f"{name} cases must be an array")
        cases = tuple(_case_from_record(item) for item in items)
        _matrix(cases, name)
        for case, item in zip(cases, items, strict=True):
            current = compare_portable_evidence(case.plan, case.observations)
            if current != case.historical:
                raise EvidenceMaterializationError(
                    f"{name}/{case.slug} current comparator differs from historical assessment"
                )
            if current != _assessment(_obj(_mapping(item), "currentAssessment")):
                raise EvidenceMaterializationError(f"{name}/{case.slug} retained current assessment drift")
        restored[name] = cases
    _compatible(restored["terminating-intercepting"], restored["packet-path"])
    return doc


def encode_reassessment_archive(exact_json: bytes) -> bytes:
    if _canonical(_json(exact_json, "cross-mechanism reassessment")) != exact_json:
        raise EvidenceMaterializationError("reassessment JSON must be canonical before archive encoding")
    compressor = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    body = compressor.compress(exact_json) + compressor.flush()
    gzip_bytes = (
        b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff"
        + body
        + struct.pack("<II", binascii.crc32(exact_json) & 0xFFFFFFFF, len(exact_json) & 0xFFFFFFFF)
    )
    return base64.b64encode(gzip_bytes) + b"\n"


def decode_reassessment_archive(archive_bytes: bytes) -> bytes:
    if not archive_bytes.endswith(b"\n") or b"\n" in archive_bytes[:-1]:
        raise EvidenceMaterializationError("reassessment archive must contain one base64 line")
    try:
        compressed = base64.b64decode(archive_bytes[:-1], validate=True)
        exact = zlib.decompress(compressed, 16 + zlib.MAX_WBITS)
    except (binascii.Error, ValueError, zlib.error) as exc:
        raise EvidenceMaterializationError("reassessment archive is invalid") from exc
    if compressed[:10] != b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff":
        raise EvidenceMaterializationError("reassessment archive gzip header is not deterministic")
    if encode_reassessment_archive(exact) != archive_bytes:
        raise EvidenceMaterializationError("reassessment archive is not canonical deterministic encoding")
    return exact


def _load_tel(bundle: _Bundle, slug: str) -> _Case:
    family, variant = _TEL_CASES[slug]
    result_bytes = bundle.read(f"matrix/{slug}/result.json")
    result = _json(result_bytes, f"TEL/{slug} result")
    if result.get("negativeMode") != family or result.get("hiddenRetryVariant") != variant:
        raise EvidenceMaterializationError(f"TEL case identity drift: {slug}")
    implementation_ref, implementation_bytes = bundle.artifact(slug, _obj(result, "implementationRecord"))
    implementation = _json(implementation_bytes, f"TEL/{slug} implementation")
    if implementation.get("format") != "avp-project-toxiproxy-terminating-evidence-v0.1":
        raise EvidenceMaterializationError("TEL implementation format drift")
    plan_ref, plan_bytes = bundle.artifact(slug, _obj(implementation, "sealedPlan"))
    plan = _plan(plan_bytes, plan_ref)
    refs = implementation.get("implementationEvidence")
    if not isinstance(refs, list):
        raise EvidenceMaterializationError("TEL implementationEvidence missing")
    for ref in refs:
        bundle.artifact(slug, _mapping(ref))
    provenance_ref, _ = bundle.artifact(slug, _obj(result, "materializationProvenance"))
    historical = _assessment(_obj(result, "assessment"))
    if _assessment(_obj(implementation, "assessment")) != historical:
        raise EvidenceMaterializationError("TEL assessment drift between result and implementation record")
    observations = _observations(_obj(implementation, "portableObservationSnapshot"))
    if compare_portable_evidence(plan, observations) != historical:
        raise EvidenceMaterializationError(f"TEL/{slug} does not survive current comparator reassessment")
    return _Case(
        slug, family, variant, plan, observations, historical,
        artifact_ref(result_bytes, "source-case-result"), implementation_ref, provenance_ref,
    )


def _load_ptl(bundle: _Bundle, slug: str) -> _Case:
    family = _PTL_CASES[slug]
    result_bytes = bundle.read(f"matrix/{slug}/result.json")
    result = _json(result_bytes, f"PTL/{slug} result")
    if (
        result.get("format") != "avp-project-network-packet-path-case-result-v0.1"
        or result.get("case") != slug
        or result.get("negativeMode") != family
    ):
        raise EvidenceMaterializationError(f"PTL case identity drift: {slug}")
    plan_ref, plan_bytes = bundle.artifact(slug, _obj(result, "sealedPlan"))
    plan = _plan(plan_bytes, plan_ref)
    implementation_ref, implementation_bytes = bundle.artifact(slug, _obj(result, "implementationRecord"))
    implementation = _json(implementation_bytes, f"PTL/{slug} implementation")
    if implementation.get("format") != "avp-project-network-packet-path-live-result-v0.1":
        raise EvidenceMaterializationError("PTL implementation format drift")
    attempts = implementation.get("attempts")
    if not isinstance(attempts, list):
        raise EvidenceMaterializationError("PTL attempts missing")
    by_phase: dict[str, AttemptObservation] = {}
    for entry in attempts:
        item = _mapping(entry)
        phase = _str(item, "phaseId")
        if phase in by_phase:
            raise EvidenceMaterializationError("PTL duplicate attempt phase")
        attempt_ref, attempt_bytes = bundle.artifact(slug, _obj(item, "attempt"))
        exchange_ref, exchange_bytes = bundle.artifact(slug, _obj(item, "exchange"))
        witness_ref, witness_bytes = bundle.artifact(slug, _obj(item, "witness"))
        raw_ref, raw_bytes = bundle.artifact(slug, _obj(item, "rawWitness"))
        del attempt_ref, exchange_ref, witness_ref, raw_ref
        attempt = _json(attempt_bytes, f"PTL/{slug}/{phase} attempt")
        exchange = _json(exchange_bytes, f"PTL/{slug}/{phase} exchange")
        witness = _json(witness_bytes, f"PTL/{slug}/{phase} witness")
        raw = _json(raw_bytes, f"PTL/{slug}/{phase} raw witness")
        _ptl_binding(plan, phase, item, attempt, exchange, witness, raw, raw_bytes)
        by_phase[phase] = _ptl_observation(phase, attempt, exchange, witness)
    observations = PortableEvidenceObservations(
        baseline=by_phase.get("baseline"),
        pre_trigger=by_phase.get("pre-trigger"),
        activation_settlement=by_phase.get("activation-settlement"),
        subject_active_cut=by_phase.get("subject-active-cut"),
        non_target_control=by_phase.get("non-target-control"),
        recovery_1=by_phase.get("recovery-1"),
        recovery_2=by_phase.get("recovery-2"),
        stability=by_phase.get("stability"),
        cleanup_noninterference_ok=_optional_bool(implementation, "cleanupNoninterferenceOk"),
        security_projection_ok=_optional_bool(implementation, "securityProjectionOk"),
        infrastructure_problems=_strings(implementation.get("infrastructureProblems", [])),
    )
    provenance_ref, _ = bundle.artifact(slug, _obj(result, "materializationProvenance"))
    historical = _assessment(_obj(result, "assessment"))
    if _assessment(_obj(implementation, "assessment")) != historical:
        raise EvidenceMaterializationError("PTL assessment drift between result and implementation record")
    if compare_portable_evidence(plan, observations) != historical:
        raise EvidenceMaterializationError(f"PTL/{slug} does not survive current comparator reassessment")
    return _Case(
        slug, family, None, plan, observations, historical,
        artifact_ref(result_bytes, "source-case-result"), implementation_ref, provenance_ref,
    )


def _ptl_binding(
    plan: SealedPlan,
    phase: str,
    entry: Mapping[str, object],
    attempt: Mapping[str, object],
    exchange: Mapping[str, object],
    witness: Mapping[str, object],
    raw: Mapping[str, object],
    raw_bytes: bytes,
) -> None:
    attempt_id = _str(attempt, "attemptId")
    if any(source.get("attemptId") != attempt_id for source in (entry, exchange, witness, raw)):
        raise EvidenceMaterializationError("PTL attempt/exchange/witness identity drift")
    expected_path = plan.plan.non_target_path_id if phase == "non-target-control" else plan.plan.path_id
    if (
        attempt.get("runId") != plan.plan.run_id
        or attempt.get("phaseId") != phase
        or attempt.get("pathId") != expected_path
    ):
        raise EvidenceMaterializationError("PTL attempt run/phase/path binding drift")
    ordinal = attempt.get("ordinal")
    if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0:
        raise EvidenceMaterializationError("PTL attempt ordinal invalid")
    challenge = _b64(attempt, "challengeB64")
    if hashlib.sha256(challenge).hexdigest() != attempt.get("challengeSha256"):
        raise EvidenceMaterializationError("PTL challenge digest mismatch")
    context = (plan.plan.run_id, phase, ordinal, expected_path, plan.plan.exchange_program.program_id)
    context_bytes = json.dumps(context, separators=(",", ":"), ensure_ascii=False).encode()
    if hashlib.sha256(b"attempt\x00" + context_bytes + challenge).hexdigest() != attempt_id:
        raise EvidenceMaterializationError("PTL attempt identity cannot be reproduced")
    request, response = plan.plan.exchange_program.materialize(challenge)
    if _b64(attempt, "requestB64") != request or _b64(attempt, "expectedResponseB64") != response:
        raise EvidenceMaterializationError("PTL exact exchange bytes drift from sealed plan")
    if (
        hashlib.sha256(request).hexdigest() != attempt.get("requestSha256")
        or hashlib.sha256(response).hexdigest() != attempt.get("responseSha256")
    ):
        raise EvidenceMaterializationError("PTL exact exchange digest mismatch")
    if raw.get("format") != "avp-project-network-transport-witness-v0.1":
        raise EvidenceMaterializationError("PTL raw witness format drift")
    if _b64(witness, "rawArtifactB64") != raw_bytes:
        raise EvidenceMaterializationError("PTL normalized witness does not embed exact raw witness bytes")
    if (
        witness.get("captureDrops") != raw.get("captureDrops")
        or witness.get("capturePackets") != raw.get("capturePackets")
    ):
        raise EvidenceMaterializationError("PTL witness/raw capture accounting drift")


def _ptl_observation(
    phase: str,
    attempt: Mapping[str, object],
    exchange: Mapping[str, object],
    witness: Mapping[str, object],
) -> AttemptObservation:
    facts = witness.get("channelFacts")
    if not isinstance(facts, list) or len(facts) != 1:
        raise EvidenceMaterializationError("PTL witness must contain exactly one W-front channel")
    front = _initiations(_mapping(facts[0]))
    if front.channel != "W-front":
        raise EvidenceMaterializationError("PTL witness channel must be W-front")
    validity = _strings(witness.get("validityProblems", []))
    drops = witness.get("captureDrops")
    if isinstance(drops, bool) or not isinstance(drops, int) or drops < 0:
        raise EvidenceMaterializationError("PTL captureDrops invalid")
    if drops:
        validity += (f"capture-drops:{drops}",)
    front = InitiationFacts(
        front.channel,
        front.total_initiations,
        front.expected_target_initiations,
        front.alternate_target_initiations,
        front.raw_syn_packets,
        front.retransmitted_syn_packets,
        front.validity_problems + validity,
    )
    return AttemptObservation(
        phase_id=phase,
        path_id=_str(attempt, "pathId"),
        attempt_id=_str(attempt, "attemptId"),
        completed=_bool(exchange, "completed"),
        mismatch_observed=_bool(exchange, "mismatchObserved"),
        observation_budget_expired=_bool(exchange, "observationBudgetExpired"),
        front_initiations=front,
        upstream_initiations=None,
    )


def _matrix(cases: Sequence[_Case], name: str) -> None:
    positives = [case for case in cases if case.family is None]
    if len(positives) != 1 or positives[0].historical.classification is not AssessmentClass.SATISFIED:
        raise EvidenceMaterializationError(f"{name} must contain exactly one SATISFIED positive case")
    if {case.family for case in cases if case.family is not None} != set(_NEGATIVE_FAMILIES):
        raise EvidenceMaterializationError(f"{name} required negative-family coverage drift")
    if name == "terminating-intercepting":
        variants = {case.variant for case in cases if case.family == "HiddenRetry/Fallback"}
        if variants != {"front-extra-connect", "upstream-extra-connect"}:
            raise EvidenceMaterializationError("terminating hidden-retry evidence must cover both boundaries")
    for case in cases:
        if case.family is not None and case.historical.classification is AssessmentClass.SATISFIED:
            raise EvidenceMaterializationError(f"{name}/{case.slug} negative case self-certified")
        if case.plan.plan.observation_budget_ns != 1_000_000_000 or case.plan.plan.phase_program != _PHASES:
            raise EvidenceMaterializationError(f"{name}/{case.slug} portable plan program drift")


def _compatible(tel: Sequence[_Case], ptl: Sequence[_Case]) -> None:
    left = _families(tel)
    right = _families(ptl)
    if left[None] != right[None] or left[None] != {("SATISFIED", None)}:
        raise EvidenceMaterializationError("cross-mechanism positive assessment disagreement")
    for family in _NEGATIVE_FAMILIES:
        l = {(classification, _problem_family(problem)) for classification, problem in left[family]}
        r = {(classification, _problem_family(problem)) for classification, problem in right[family]}
        if len(l) != 1 or l != r:
            raise EvidenceMaterializationError(f"cross-mechanism predicate-family disagreement: {family}")


def _families(cases: Sequence[_Case]) -> dict[str | None, set[tuple[str, str | None]]]:
    result: dict[str | None, set[tuple[str, str | None]]] = {}
    for case in cases:
        result.setdefault(case.family, set()).add(
            (case.historical.classification.value, case.historical.primary_problem)
        )
    return result


def _problem_family(problem: str | None) -> str | None:
    if problem is None:
        return None
    for exact in (
        "C1:missing-observation:activation-settlement",
        "C1:missing-observation:recovery-2",
    ):
        if problem.startswith(exact):
            return exact
    return problem.split(":", 1)[0]


def _mechanism(
    expected: SourceExpectation,
    manifest: Mapping[str, object],
    cases: Sequence[_Case],
    semantic_blob: str,
) -> dict[str, object]:
    if {case.plan.plan.semantic_baseline_commit for case in cases} != {expected.source_commit}:
        raise EvidenceMaterializationError("source semantic commit set drift")
    return {
        "source": {
            "artifactId": expected.artifact_id,
            "zipSha256": expected.zip_sha256,
            "sourceCommit": expected.source_commit,
            "workflowRunId": expected.workflow_run_id,
            "manifestFormat": expected.manifest_format,
            "manifestEntries": expected.manifest_entries,
            "repository": manifest.get("repository"),
            "workflow": manifest.get("workflow"),
            "runAttempt": str(manifest.get("runAttempt")),
            "historicalComparatorGitBlob": expected.historical_comparator_blob,
            "semanticGitBlob": semantic_blob,
        },
        "cases": [_case_document(case) for case in cases],
    }


def _case_document(case: _Case) -> dict[str, object]:
    return {
        "slug": case.slug,
        "negativeFamily": case.family,
        "hiddenRetryVariant": case.variant,
        "sourceResult": _ref_doc(case.result_ref),
        "implementationRecord": _ref_doc(case.implementation_ref),
        "materializationProvenance": _ref_doc(case.provenance_ref),
        "sealedPlan": json.loads(case.plan.exact_bytes),
        "sealedPlanRef": _ref_doc(case.plan.ref),
        "portableObservations": _observations_doc(case.observations),
        "historicalAssessment": _assessment_doc(case.historical),
        "currentAssessment": _assessment_doc(compare_portable_evidence(case.plan, case.observations)),
    }


def _case_from_record(value: object) -> _Case:
    item = _mapping(value)
    plan_doc = _obj(item, "sealedPlan")
    plan = _plan(_canonical(plan_doc), _ref(_obj(item, "sealedPlanRef")))
    return _Case(
        _str(item, "slug"),
        _optional_str(item, "negativeFamily"),
        _optional_str(item, "hiddenRetryVariant"),
        plan,
        _observations(_obj(item, "portableObservations")),
        _assessment(_obj(item, "historicalAssessment")),
        _ref(_obj(item, "sourceResult")),
        _ref(_obj(item, "implementationRecord")),
        _ref(_obj(item, "materializationProvenance")),
    )


def _plan(exact: bytes, expected_ref: ArtifactRef) -> SealedPlan:
    doc = _json(exact, "sealed evidence plan")
    if doc.get("format") != _PLAN_FORMAT or _canonical(doc) != exact:
        raise EvidenceMaterializationError("sealed evidence plan format/canonicalization drift")
    semantic = _obj(doc, "semanticBaseline")
    exchange = _obj(doc, "exchangeProgram")
    control = doc.get("nonTargetControl")
    control_subject = control_fixture = None
    if control is not None:
        control_doc = _mapping(control)
        control_subject = _endpoint(_obj(control_doc, "subjectDestination"))
        control_fixture = _endpoint(_obj(control_doc, "upstreamFixture"))
    plan = EvidencePlan(
        design_revision=_str(doc, "designRevision"),
        semantic_baseline_commit=_str(semantic, "commit"),
        semantic_baseline_path=_str(semantic, "path"),
        run_id=_str(doc, "runId"),
        path_id=_str(doc, "pathId"),
        subject_destination=_endpoint(_obj(doc, "subjectDestination")),
        upstream_fixture=_endpoint(_obj(doc, "upstreamFixture")),
        exchange_program=ExchangeProgram(
            _str(exchange, "programId"),
            _b64(exchange, "requestPrefixB64"),
            _b64(exchange, "requestSuffixB64"),
            _b64(exchange, "responsePrefixB64"),
            _b64(exchange, "responseSuffixB64"),
        ),
        observation_budget_ns=_int(doc, "observationBudgetNs", 1),
        non_target_subject_destination=control_subject,
        non_target_upstream_fixture=control_fixture,
        phase_program=tuple(_string_list(doc, "phaseProgram")),
        negative_mode=_optional_str(doc, "negativeMode"),
    )
    sealed = SealedPlan(plan, exact, expected_ref)
    sealed.verify()
    if plan.semantic_baseline_path != _AEP_PATH:
        raise EvidenceMaterializationError("sealed plan does not bind reviewed AEP-0012 path")
    return sealed


def _observations(doc: Mapping[str, object]) -> PortableEvidenceObservations:
    attempts = _obj(doc, "attempts")
    return PortableEvidenceObservations(
        baseline=_attempt(attempts.get("baseline")),
        pre_trigger=_attempt(attempts.get("preTrigger")),
        activation_settlement=_attempt(attempts.get("activationSettlement")),
        subject_active_cut=_attempt(attempts.get("subjectActiveCut")),
        non_target_control=_attempt(attempts.get("nonTargetControl")),
        recovery_1=_attempt(attempts.get("recovery1")),
        recovery_2=_attempt(attempts.get("recovery2")),
        stability=_attempt(attempts.get("stability")),
        cleanup_noninterference_ok=_optional_bool(doc, "cleanupNoninterferenceOk"),
        security_projection_ok=_optional_bool(doc, "securityProjectionOk"),
        evidence_validity_problems=_strings(doc.get("evidenceValidityProblems", [])),
        infrastructure_problems=_strings(doc.get("infrastructureProblems", [])),
        unsupported_materialization_problems=_strings(doc.get("unsupportedMaterializationProblems", [])),
    )


def _observations_doc(value: PortableEvidenceObservations) -> dict[str, object]:
    return {
        "attempts": {
            "baseline": _attempt_doc(value.baseline),
            "preTrigger": _attempt_doc(value.pre_trigger),
            "activationSettlement": _attempt_doc(value.activation_settlement),
            "subjectActiveCut": _attempt_doc(value.subject_active_cut),
            "nonTargetControl": _attempt_doc(value.non_target_control),
            "recovery1": _attempt_doc(value.recovery_1),
            "recovery2": _attempt_doc(value.recovery_2),
            "stability": _attempt_doc(value.stability),
        },
        "cleanupNoninterferenceOk": value.cleanup_noninterference_ok,
        "securityProjectionOk": value.security_projection_ok,
        "evidenceValidityProblems": list(value.evidence_validity_problems),
        "infrastructureProblems": list(value.infrastructure_problems),
        "unsupportedMaterializationProblems": list(value.unsupported_materialization_problems),
    }


def _attempt(value: object) -> AttemptObservation | None:
    if value is None:
        return None
    doc = _mapping(value)
    upstream = doc.get("upstreamInitiations")
    return AttemptObservation(
        _str(doc, "phaseId"),
        _str(doc, "pathId"),
        _str(doc, "attemptId"),
        _bool(doc, "completed"),
        _bool(doc, "mismatchObserved"),
        _bool(doc, "observationBudgetExpired"),
        _initiations(_obj(doc, "frontInitiations")),
        None if upstream is None else _initiations(_mapping(upstream)),
        _strings(doc.get("validityProblems", [])),
    )


def _attempt_doc(value: AttemptObservation | None) -> dict[str, object] | None:
    if value is None:
        return None
    return {
        "phaseId": value.phase_id,
        "pathId": value.path_id,
        "attemptId": value.attempt_id,
        "completed": value.completed,
        "mismatchObserved": value.mismatch_observed,
        "observationBudgetExpired": value.observation_budget_expired,
        "frontInitiations": _init_doc(value.front_initiations),
        "upstreamInitiations": None if value.upstream_initiations is None else _init_doc(value.upstream_initiations),
        "validityProblems": list(value.validity_problems),
    }


def _initiations(doc: Mapping[str, object]) -> InitiationFacts:
    return InitiationFacts(
        _str(doc, "channel"),
        _int(doc, "totalInitiations", 0),
        _int(doc, "expectedTargetInitiations", 0),
        _int(doc, "alternateTargetInitiations", 0),
        _int(doc, "rawSynPackets", 0),
        _int(doc, "retransmittedSynPackets", 0),
        _strings(doc.get("validityProblems", [])),
    )


def _init_doc(value: InitiationFacts) -> dict[str, object]:
    return {
        "channel": value.channel,
        "totalInitiations": value.total_initiations,
        "expectedTargetInitiations": value.expected_target_initiations,
        "alternateTargetInitiations": value.alternate_target_initiations,
        "rawSynPackets": value.raw_syn_packets,
        "retransmittedSynPackets": value.retransmitted_syn_packets,
        "validityProblems": list(value.validity_problems),
    }


def _assessment(doc: Mapping[str, object]) -> EvidenceAssessment:
    try:
        classification = AssessmentClass(doc.get("classification"))
    except (TypeError, ValueError) as exc:
        raise EvidenceMaterializationError("assessment classification invalid") from exc
    primary = doc.get("primaryProblem")
    if primary is not None and not isinstance(primary, str):
        raise EvidenceMaterializationError("assessment primaryProblem invalid")
    return EvidenceAssessment(classification, primary, _strings(doc.get("secondaryProblems", [])))


def _assessment_doc(value: EvidenceAssessment) -> dict[str, object]:
    return {
        "classification": value.classification.value,
        "primaryProblem": value.primary_problem,
        "secondaryProblems": list(value.secondary_problems),
    }


def _endpoint(doc: Mapping[str, object]) -> MaterializedEndpoint:
    return MaterializedEndpoint(_str(doc, "family"), _str(doc, "address"), _int(doc, "port", 1), _str(doc, "role"))


def _ref(doc: Mapping[str, object]) -> ArtifactRef:
    digest = _str(doc, "sha256")
    _hex(digest, 64, "artifact sha256")
    role = doc.get("logicalRole", "source-artifact")
    if not isinstance(role, str) or not role:
        raise EvidenceMaterializationError("artifact logicalRole invalid")
    return ArtifactRef(digest, _int(doc, "size", 0), role)


def _ref_doc(ref: ArtifactRef) -> dict[str, object]:
    return {"sha256": ref.sha256, "size": ref.size, "logicalRole": ref.logical_role}


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _json(payload: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceMaterializationError(f"{label} is not valid UTF-8 JSON") from exc
    return _mapping(value)


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise EvidenceMaterializationError("expected JSON object")
    return value


def _obj(doc: Mapping[str, object], key: str) -> dict[str, object]:
    return _mapping(doc.get(key))


def _str(doc: Mapping[str, object], key: str) -> str:
    value = doc.get(key)
    if not isinstance(value, str) or not value:
        raise EvidenceMaterializationError(f"field {key!r} must be a non-empty string")
    return value


def _optional_str(doc: Mapping[str, object], key: str) -> str | None:
    value = doc.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise EvidenceMaterializationError(f"field {key!r} must be string or null")
    return value


def _bool(doc: Mapping[str, object], key: str) -> bool:
    value = doc.get(key)
    if not isinstance(value, bool):
        raise EvidenceMaterializationError(f"field {key!r} must be boolean")
    return value


def _optional_bool(doc: Mapping[str, object], key: str) -> bool | None:
    value = doc.get(key)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise EvidenceMaterializationError(f"field {key!r} must be boolean or null")
    return value


def _int(doc: Mapping[str, object], key: str, minimum: int) -> int:
    value = doc.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise EvidenceMaterializationError(f"field {key!r} must be integer >= {minimum}")
    if key == "port" and value > 65535:
        raise EvidenceMaterializationError("TCP port must be <= 65535")
    return value


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise EvidenceMaterializationError("expected string array")
    return tuple(value)


def _string_list(doc: Mapping[str, object], key: str) -> list[str]:
    value = doc.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise EvidenceMaterializationError(f"field {key!r} must be a non-empty string array")
    return value


def _b64(doc: Mapping[str, object], key: str) -> bytes:
    try:
        return base64.b64decode(_str(doc, key), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise EvidenceMaterializationError(f"field {key!r} is not strict base64") from exc


def _hex(value: str, length: int, label: str) -> None:
    if len(value) != length or any(char not in "0123456789abcdef" for char in value):
        raise EvidenceMaterializationError(f"{label} must be {length} lowercase hex characters")


def _safe_path(path: str) -> bool:
    if not path or path.startswith("/") or "\\" in path or "\x00" in path:
        return False
    normalized = posixpath.normpath(path)
    return normalized == path and normalized not in {".", ".."} and not normalized.startswith("../")

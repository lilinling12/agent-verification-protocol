"""Provider-neutral, test-only evidence primitives for Network Control TEL-001.

The types in this module are project acceptance-evidence plumbing, not proposed
AVP schema or public runtime API.  Exact retained bytes are content addressed so
review can reassess recorded observations without allowing a provider to define
portable expected outcomes.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import tempfile
import threading
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path

_HEX_COMMIT_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_CHALLENGE_DOMAIN = b"avp.network.npr011.challenge.v1\x00"
_PLAN_FORMAT = "avp-project-network-evidence-plan-v0.1"
_DEFAULT_PHASE_PROGRAM = (
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


class EvidenceMaterializationError(ValueError):
    """Raised when governed evidence input cannot be safely materialized."""


class AssessmentClass(str, Enum):
    """Engineering-only evidence assessment classes; not protocol verdicts."""

    SATISFIED = "SATISFIED"
    SEMANTIC_VIOLATION = "SEMANTIC_VIOLATION"
    EVIDENCE_INVALID = "EVIDENCE_INVALID"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"
    UNSUPPORTED_MATERIALIZATION = "UNSUPPORTED_MATERIALIZATION"


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    sha256: str
    size: int
    logical_role: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            raise EvidenceMaterializationError("artifact sha256 must be 64 lowercase hex characters")
        if self.size < 0:
            raise EvidenceMaterializationError("artifact size must be non-negative")
        if not self.logical_role:
            raise EvidenceMaterializationError("artifact logical role must be non-empty")


@dataclass(frozen=True, slots=True)
class MaterializedEndpoint:
    """One literal TCP endpoint bound before the evidence plan is sealed."""

    family: str
    address: str
    port: int
    role: str

    def __post_init__(self) -> None:
        try:
            parsed = ipaddress.ip_address(self.address)
        except ValueError as exc:
            raise EvidenceMaterializationError(
                f"endpoint address must be a literal IP address: {self.address!r}"
            ) from exc
        expected_family = "ipv4" if parsed.version == 4 else "ipv6"
        if self.family != expected_family:
            raise EvidenceMaterializationError(
                f"endpoint family {self.family!r} does not match literal {self.address!r}"
            )
        if isinstance(self.port, bool) or not isinstance(self.port, int) or not (1 <= self.port <= 65535):
            raise EvidenceMaterializationError("TCP port must be an integer in [1, 65535]")
        if not self.role:
            raise EvidenceMaterializationError("endpoint role must be non-empty")
        # AEP-0012 explicitly excludes textual IP formatting from endpoint identity.
        object.__setattr__(self, "address", str(parsed))

    @property
    def ip_version(self) -> int:
        return 4 if self.family == "ipv4" else 6


@dataclass(frozen=True, slots=True)
class ExchangeProgram:
    """Deterministic binary request/response template around one challenge."""

    program_id: str
    request_prefix: bytes
    request_suffix: bytes
    response_prefix: bytes
    response_suffix: bytes

    def __post_init__(self) -> None:
        if not self.program_id:
            raise EvidenceMaterializationError("exchange program id must be non-empty")
        # The challenge itself is non-empty, so empty prefixes/suffixes are valid.
        for name in ("request_prefix", "request_suffix", "response_prefix", "response_suffix"):
            if not isinstance(getattr(self, name), bytes):
                raise EvidenceMaterializationError(f"{name} must be exact bytes")

    def materialize(self, challenge: bytes) -> tuple[bytes, bytes]:
        if not challenge:
            raise EvidenceMaterializationError("attempt challenge must be non-empty")
        return (
            self.request_prefix + challenge + self.request_suffix,
            self.response_prefix + challenge + self.response_suffix,
        )


@dataclass(frozen=True, slots=True)
class EvidencePlan:
    """Immutable, fully materialized TEL-001 evidence input."""

    design_revision: str
    semantic_baseline_commit: str
    semantic_baseline_path: str
    run_id: str
    path_id: str
    subject_destination: MaterializedEndpoint
    upstream_fixture: MaterializedEndpoint
    exchange_program: ExchangeProgram
    observation_budget_ns: int
    phase_program: tuple[str, ...] = _DEFAULT_PHASE_PROGRAM
    negative_mode: str | None = None

    def __post_init__(self) -> None:
        if not self.design_revision:
            raise EvidenceMaterializationError("design revision must be non-empty")
        if not _HEX_COMMIT_RE.fullmatch(self.semantic_baseline_commit):
            raise EvidenceMaterializationError("semantic baseline must be an exact 40- or 64-hex commit")
        if not self.semantic_baseline_path or self.semantic_baseline_path.startswith("/"):
            raise EvidenceMaterializationError("semantic baseline path must be repository-relative")
        if not self.run_id or not self.path_id:
            raise EvidenceMaterializationError("run and path identities must be non-empty")
        if isinstance(self.observation_budget_ns, bool) or not isinstance(self.observation_budget_ns, int):
            raise EvidenceMaterializationError("observation budget must be an integer nanosecond duration")
        if self.observation_budget_ns <= 0:
            raise EvidenceMaterializationError("observation budget must be positive and finite")
        if not self.phase_program or any(not phase for phase in self.phase_program):
            raise EvidenceMaterializationError("phase program must contain non-empty phase identities")
        if len(set(self.phase_program)) != len(self.phase_program):
            raise EvidenceMaterializationError("phase identities must be unique")

    def exact_bytes(self) -> bytes:
        """Return the project-local exact serialization whose bytes are retained.

        This deterministic encoding is an evidence implementation choice. It is
        intentionally not a claim about future normative AVP JSON canonicalization.
        """

        document = {
            "format": _PLAN_FORMAT,
            "designRevision": self.design_revision,
            "semanticBaseline": {
                "commit": self.semantic_baseline_commit,
                "path": self.semantic_baseline_path,
            },
            "runId": self.run_id,
            "pathId": self.path_id,
            "subjectDestination": _endpoint_document(self.subject_destination),
            "upstreamFixture": _endpoint_document(self.upstream_fixture),
            "exchangeProgram": {
                "programId": self.exchange_program.program_id,
                "requestPrefixB64": _b64(self.exchange_program.request_prefix),
                "requestSuffixB64": _b64(self.exchange_program.request_suffix),
                "responsePrefixB64": _b64(self.exchange_program.response_prefix),
                "responseSuffixB64": _b64(self.exchange_program.response_suffix),
            },
            "observationBudgetNs": self.observation_budget_ns,
            "phaseProgram": list(self.phase_program),
            "negativeMode": self.negative_mode,
        }
        return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    def seal(self) -> "SealedPlan":
        payload = self.exact_bytes()
        return SealedPlan(plan=self, exact_bytes=payload, ref=artifact_ref(payload, "evidence-plan"))


@dataclass(frozen=True, slots=True)
class SealedPlan:
    plan: EvidencePlan
    exact_bytes: bytes
    ref: ArtifactRef

    def verify(self) -> None:
        current = self.plan.exact_bytes()
        if current != self.exact_bytes:
            raise EvidenceMaterializationError("sealed plan bytes no longer match plan materialization")
        if artifact_ref(self.exact_bytes, self.ref.logical_role) != self.ref:
            raise EvidenceMaterializationError("sealed plan artifact identity mismatch")


@dataclass(frozen=True, slots=True)
class AttemptMaterial:
    run_id: str
    phase_id: str
    ordinal: int
    path_id: str
    attempt_id: str
    challenge: bytes
    challenge_sha256: str
    request_bytes: bytes
    expected_response_bytes: bytes
    request_sha256: str
    response_sha256: str


class AttemptFactory:
    """Create fresh attempt material without exposing future challenge values."""

    def __init__(self, private_run_root: bytes | None = None) -> None:
        root = private_run_root if private_run_root is not None else secrets.token_bytes(32)
        if not isinstance(root, bytes) or len(root) < 32:
            raise EvidenceMaterializationError("private run root must contain at least 256 bits")
        self._root = root
        self._issued_contexts: set[tuple[str, str, int, str, str]] = set()
        self._lock = threading.Lock()

    def issue(self, plan: EvidencePlan, *, phase_id: str, ordinal: int) -> AttemptMaterial:
        if phase_id not in plan.phase_program:
            raise EvidenceMaterializationError(f"phase {phase_id!r} is not in the sealed program")
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0:
            raise EvidenceMaterializationError("attempt ordinal must be a non-negative integer")
        context = (plan.run_id, phase_id, ordinal, plan.path_id, plan.exchange_program.program_id)
        with self._lock:
            if context in self._issued_contexts:
                raise EvidenceMaterializationError("attempt context cannot be reused")
            self._issued_contexts.add(context)

        context_bytes = json.dumps(context, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        challenge = hmac.new(self._root, _CHALLENGE_DOMAIN + context_bytes, hashlib.sha256).digest()
        request, response = plan.exchange_program.materialize(challenge)
        if not request or not response:
            raise EvidenceMaterializationError("materialized request/response must be non-empty")
        attempt_id = hashlib.sha256(b"attempt\x00" + context_bytes + challenge).hexdigest()
        return AttemptMaterial(
            run_id=plan.run_id,
            phase_id=phase_id,
            ordinal=ordinal,
            path_id=plan.path_id,
            attempt_id=attempt_id,
            challenge=challenge,
            challenge_sha256=hashlib.sha256(challenge).hexdigest(),
            request_bytes=request,
            expected_response_bytes=response,
            request_sha256=hashlib.sha256(request).hexdigest(),
            response_sha256=hashlib.sha256(response).hexdigest(),
        )


class ArtifactStore:
    """Small content-addressed store for exact TEL-001 evidence bytes."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def put_bytes(self, payload: bytes, *, logical_role: str) -> ArtifactRef:
        ref = artifact_ref(payload, logical_role)
        target = self.path_for(ref)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            existing = target.read_bytes()
            if existing != payload:
                raise EvidenceMaterializationError("content-address path contains non-matching bytes")
            return ref

        fd, temporary_name = tempfile.mkstemp(prefix=f".{ref.sha256}.", dir=target.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                if target.read_bytes() != payload:
                    raise EvidenceMaterializationError("concurrent artifact write produced conflicting bytes")
            finally:
                temporary.unlink(missing_ok=True)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        return ref

    def path_for(self, ref: ArtifactRef) -> Path:
        return self.root / "sha256" / ref.sha256[:2] / ref.sha256

    def read_verified(self, ref: ArtifactRef) -> bytes:
        payload = self.path_for(ref).read_bytes()
        if len(payload) != ref.size or hashlib.sha256(payload).hexdigest() != ref.sha256:
            raise EvidenceMaterializationError(f"artifact integrity mismatch for {ref.logical_role}")
        return payload


@dataclass(frozen=True, slots=True)
class InitiationFacts:
    """Provider-neutral normalized initiation facts for one witness channel."""

    channel: str
    total_initiations: int
    expected_target_initiations: int
    alternate_target_initiations: int
    raw_syn_packets: int
    retransmitted_syn_packets: int
    validity_problems: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    classification: AssessmentClass
    primary_problem: str | None = None
    secondary_problems: tuple[str, ...] = ()

    def with_secondary_problem(self, problem: str) -> "EvidenceAssessment":
        if not problem:
            raise ValueError("secondary problem must be non-empty")
        return replace(self, secondary_problems=self.secondary_problems + (problem,))


def assess_initiation_integrity(
    front: InitiationFacts,
    upstream: InitiationFacts,
) -> EvidenceAssessment:
    """Evaluate C10-style cardinality without provider-specific branching."""

    validity = tuple(front.validity_problems) + tuple(upstream.validity_problems)
    if validity:
        return EvidenceAssessment(
            AssessmentClass.EVIDENCE_INVALID,
            primary_problem=f"witness-invalid:{validity[0]}",
            secondary_problems=tuple(f"witness-invalid:{problem}" for problem in validity[1:]),
        )

    failures: list[str] = []
    for facts in (front, upstream):
        if facts.total_initiations != 1:
            failures.append(f"{facts.channel}:total-initiations={facts.total_initiations}")
        if facts.expected_target_initiations != 1:
            failures.append(
                f"{facts.channel}:expected-target-initiations={facts.expected_target_initiations}"
            )
        if facts.alternate_target_initiations != 0:
            failures.append(
                f"{facts.channel}:alternate-target-initiations={facts.alternate_target_initiations}"
            )
    if failures:
        return EvidenceAssessment(
            AssessmentClass.SEMANTIC_VIOLATION,
            primary_problem=failures[0],
            secondary_problems=tuple(failures[1:]),
        )
    return EvidenceAssessment(AssessmentClass.SATISFIED)


def artifact_ref(payload: bytes, logical_role: str) -> ArtifactRef:
    if not isinstance(payload, bytes):
        raise TypeError("artifact payload must be exact bytes")
    return ArtifactRef(
        sha256=hashlib.sha256(payload).hexdigest(),
        size=len(payload),
        logical_role=logical_role,
    )


def _endpoint_document(endpoint: MaterializedEndpoint) -> dict[str, object]:
    return {
        "family": endpoint.family,
        "address": endpoint.address,
        "port": endpoint.port,
        "role": endpoint.role,
    }


def _b64(payload: bytes) -> str:
    return base64.b64encode(payload).decode("ascii")

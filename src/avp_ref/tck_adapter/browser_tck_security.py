"""Provider-neutral evaluator for Browser Subject/Evaluator/Control separation.

The seam in this module is Browser-specific and evidence-oriented; it is not a
new Subject automation API. Concrete implementations may use privileged browser
controls internally, but the portable evaluator sees only an authorized Subject
surface, independently observed evaluator-private values, and Artifact identity
separated from retrieval authorization.

A separate semantic probe verifies that evaluator-private state remains part of
the authoritative Browser projection. Confidentiality therefore cannot be
silently implemented by omitting selected state from authoritative identity.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .browser_executed_capability import BrowserExecutedCapabilityEvaluator
from .browser_harness import BrowserHarnessError, BrowserSUT, BrowserVerificationError
from .browser_tck_adapter import BROWSER_PROFILE
from .models import TCKAdapterError, TCKCaseResult, TCKStatus

CASE_ID = "AVP-TCK-BROWSER-SECURITY-001"
_PRIVILEGED_CONTROLS = frozenset(
    {
        "browser-launch-handle",
        "browser-debugging-handle",
        "snapshot-restore-control",
    }
)
_NEGATIVE_CONTROLS = frozenset(
    {
        "evaluator-private-cookie-leaked-to-subject",
        "evaluator-private-localstorage-leaked-to-subject",
        "privileged-control-handle-exposed-to-subject",
        "artifact-digest-treated-as-retrieval-authority",
        "redacted-bytes-reuse-unredacted-digest",
    }
)


@dataclass(frozen=True, slots=True)
class BrowserSecurityArtifact:
    """Evaluator-side Artifact identity plus opaque retrieval authorization."""

    identity: str
    locator: object
    authorization: object

    def __post_init__(self) -> None:
        if not isinstance(self.identity, str) or not self.identity:
            raise ValueError("Browser security Artifact identity must be non-empty")


@runtime_checkable
class BrowserSecurityEvidenceControl(Protocol):
    """Narrow evaluator/control seam required by AVP-BROWSER-019 TCK execution."""

    def seed_evaluator_private_state(
        self,
        sut: BrowserSUT,
        *,
        cookie_value: str,
        local_storage_value: str,
    ) -> None: ...

    def observe_subject_surface(self, sut: BrowserSUT) -> Mapping[str, Any]: ...

    def observe_evaluator_private_state(self, sut: BrowserSUT) -> Mapping[str, str]: ...

    def retain_artifact(self, content: bytes) -> BrowserSecurityArtifact: ...

    def retrieve_artifact(self, locator: object, authorization: object) -> bytes: ...

    def retain_redacted_artifacts(
        self,
        content: bytes,
        *,
        redacted_content: bytes,
    ) -> tuple[BrowserSecurityArtifact, BrowserSecurityArtifact]: ...


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TCKAdapterError(f"{label} must be an object")
    return value


def _strings(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise TCKAdapterError(f"{label} must be a non-empty array")
    values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise TCKAdapterError(f"{label} must contain non-empty strings")
        values.append(item)
    return values


def _require_exact_set(value: object, expected: frozenset[str], label: str) -> None:
    values = _strings(value, label)
    if len(values) != len(set(values)) or frozenset(values) != expected:
        raise TCKAdapterError(f"{label} changed from the governed set")


class BrowserSecurityTCKEvaluator:
    """Execute private-state visibility and Artifact authority separation."""

    case_id = CASE_ID

    def __init__(
        self,
        *,
        sut: BrowserSUT,
        evidence_control: BrowserSecurityEvidenceControl,
        verify_private_state_authoritative: Callable[[BrowserSUT], None],
    ) -> None:
        if not isinstance(evidence_control, BrowserSecurityEvidenceControl):
            raise TCKAdapterError("Browser security evidence control contract is incomplete")
        if not callable(verify_private_state_authoritative):
            raise TCKAdapterError("Browser authoritative private-state probe must be callable")
        self._sut = sut
        self._control = evidence_control
        self._verify_private_state_authoritative = verify_private_state_authoritative
        self._visibility = BrowserExecutedCapabilityEvaluator()

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        vector, expect = self._case_parts(case)
        private_cookie, private_storage, authorized = self._validate_contract(vector, expect)
        try:
            self._execute_visibility(private_cookie, private_storage, authorized)
            self._execute_artifact_authority(private_cookie, private_storage)
        except BrowserHarnessError as exc:
            return TCKCaseResult(
                self.case_id,
                TCKStatus.FAIL,
                f"Browser security obligation failed: {exc}",
            )
        return TCKCaseResult(
            self.case_id,
            TCKStatus.PASS,
            "evaluator-private state remains authoritative while Subject visibility and privileged authority stay separated; Artifact identity is not retrieval authorization",
        )

    def _case_parts(
        self,
        case: Mapping[str, Any],
    ) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
        metadata = _mapping(case.get("metadata"), f"{CASE_ID} metadata")
        if metadata.get("id") != CASE_ID or metadata.get("domain") != "browser":
            raise TCKAdapterError(f"{CASE_ID} case identity/domain mismatch")
        if case.get("profile") != BROWSER_PROFILE:
            raise TCKAdapterError(f"{CASE_ID} targets the wrong Browser profile")
        return (
            _mapping(case.get("vector"), f"{CASE_ID} vector"),
            _mapping(case.get("expect"), f"{CASE_ID} expect"),
        )

    def _validate_contract(
        self,
        vector: Mapping[str, Any],
        expect: Mapping[str, Any],
    ) -> tuple[str, str, str]:
        private = _mapping(
            vector.get("evaluatorPrivateState"),
            f"{CASE_ID} evaluatorPrivateState",
        )
        if set(private) != {"cookie", "localStorage"}:
            raise TCKAdapterError(f"{CASE_ID} evaluator private-state shape changed")
        cookie = private.get("cookie")
        storage = private.get("localStorage")
        if not isinstance(cookie, str) or not cookie:
            raise TCKAdapterError(f"{CASE_ID} private cookie marker must be non-empty")
        if not isinstance(storage, str) or not storage:
            raise TCKAdapterError(f"{CASE_ID} private localStorage marker must be non-empty")

        _require_exact_set(
            vector.get("privilegedControl"),
            _PRIVILEGED_CONTROLS,
            f"{CASE_ID} privilegedControl",
        )
        visible = _mapping(
            vector.get("subjectVisibleSurface"),
            f"{CASE_ID} subjectVisibleSurface",
        )
        if set(visible) != {"authorizedValues"}:
            raise TCKAdapterError(f"{CASE_ID} Subject-visible surface shape changed")
        authorized_values = _strings(
            visible.get("authorizedValues"),
            f"{CASE_ID} authorizedValues",
        )
        if len(authorized_values) != 1:
            raise TCKAdapterError(f"{CASE_ID} requires one authorized Subject value")

        _require_exact_set(
            vector.get("negativeControls"),
            _NEGATIVE_CONTROLS,
            f"{CASE_ID} negativeControls",
        )
        for key in (
            "subjectEvaluatorControlSeparated",
            "privateStateMayRemainAuthoritative",
            "artifactIdentityNotAuthorization",
            "negativeControlsRejected",
        ):
            if expect.get(key) is not True:
                raise TCKAdapterError(f"{CASE_ID} expect.{key} must be true")
        return cookie, storage, authorized_values[0]

    def _execute_visibility(
        self,
        private_cookie: str,
        private_storage: str,
        authorized: str,
    ) -> None:
        self._control.seed_evaluator_private_state(
            self._sut,
            cookie_value=private_cookie,
            local_storage_value=private_storage,
        )
        private_observed = dict(self._control.observe_evaluator_private_state(self._sut))
        if set(private_observed.values()) != {private_cookie, private_storage}:
            raise BrowserVerificationError(
                "evaluator-private Browser state is not independently observable"
            )
        self._verify_private_state_authoritative(self._sut)

        subject = dict(self._control.observe_subject_surface(self._sut))
        self._visibility.require_subject_visibility(
            subject,
            authorized_surface={"value": authorized},
            evaluator_private_values=(private_cookie, private_storage),
        )

    def _execute_artifact_authority(
        self,
        private_cookie: str,
        private_storage: str,
    ) -> None:
        content = f"cookie={private_cookie};storage={private_storage}".encode("utf-8")
        retained = self._control.retain_artifact(content)
        if self._control.retrieve_artifact(
            retained.locator,
            retained.authorization,
        ) != content:
            raise BrowserVerificationError("authorized Browser Artifact retrieval changed bytes")

        try:
            self._control.retrieve_artifact(retained.locator, retained.locator)
        except BrowserHarnessError:
            pass
        else:
            raise BrowserVerificationError(
                "Browser Artifact digest/locator was accepted as retrieval authorization"
            )

        redacted_bytes = b"cookie=[REDACTED];storage=[REDACTED]"
        unredacted, redacted = self._control.retain_redacted_artifacts(
            content,
            redacted_content=redacted_bytes,
        )
        if unredacted.identity == redacted.identity:
            raise BrowserVerificationError(
                "redacted Browser bytes reused unredacted Artifact identity"
            )
        if self._control.retrieve_artifact(
            redacted.locator,
            redacted.authorization,
        ) != redacted_bytes:
            raise BrowserVerificationError("redacted Browser Artifact retrieval changed bytes")

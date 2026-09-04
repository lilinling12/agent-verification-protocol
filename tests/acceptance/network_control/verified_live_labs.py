"""Canonical trusted live bindings for Network Control evidence execution.

These project-local concrete bindings apply reviewed runtime prerequisites and
failure-evidence retention to capture qualification and TEL-002/TEL-003 live
execution. They are deliberately not provider abstractions and do not define
portable AVP semantics.
"""

from __future__ import annotations

import json
import time
from dataclasses import replace

from .capture_qualification_retransmission import RetransmissionQualifiedCaptureQualification
from .evidence_core import ArtifactRef, MaterializedEndpoint
from .helper_image_verification import prepare_exact_helper_image
from .toxiproxy_binding import (
    ToxiproxyAdminClient,
    ToxiproxyControlError,
    ToxiproxyPrerequisiteError,
)
from .toxiproxy_evidence import NegativeMode, PhaseExecution
from .toxiproxy_live_lab import ToxiproxyLiveLab
from .toxiproxy_negative_assemblies import UpstreamHiddenRetryLiveLab

_INCOMPLETE_FIXTURE_DIAGNOSTIC_TIMEOUT_S = 0.05


def parse_reviewed_toxiproxy_version_response(value: str) -> str:
    """Parse the exact Toxiproxy v2.12.0 ``GET /version`` response contract."""

    try:
        document = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ToxiproxyControlError("Toxiproxy /version response is not valid JSON") from exc
    if not isinstance(document, dict):
        raise ToxiproxyControlError("Toxiproxy /version response is not an object")
    if set(document) != {"version"}:
        raise ToxiproxyControlError("Toxiproxy /version response shape is not exact")
    version = document.get("version")
    if not isinstance(version, str) or not version:
        raise ToxiproxyControlError("Toxiproxy /version value is not a non-empty string")
    return version


def fixture_integrity_problem(document: object) -> str | None:
    """Return a project-local fixture-integrity problem for a completed exchange."""

    if not isinstance(document, dict):
        return "fixture-evidence:not-object"
    event = document.get("event")
    if not isinstance(event, dict):
        return "fixture-evidence:event-missing"
    if event.get("requestValid") is not True:
        problem = event.get("problem")
        suffix = problem if isinstance(problem, str) and problem else "request-invalid"
        return f"fixture-evidence:{suffix}"
    if event.get("responseEmitted") is not True:
        return "fixture-evidence:response-not-emitted"
    if event.get("problem") is not None:
        return f"fixture-evidence:{event.get('problem')}"
    return None


class VerifiedCaptureQualification(RetransmissionQualifiedCaptureQualification):
    """Capture qualification using the shared exact helper-image boundary."""

    def _prepare_helper(self) -> None:
        prepare_exact_helper_image(self.docker, self.helper)


class _ReviewedToxiproxyVersionBinding:
    """Apply the exact pinned Toxiproxy v2.12.0 admin-version contract."""

    toxiproxy_artifact: object
    _role_response_timeout_s: float

    def _wait_for_toxiproxy_version(self, admin: ToxiproxyAdminClient) -> None:
        deadline = time.monotonic() + self._role_response_timeout_s
        last_problem: RuntimeError | None = None
        while time.monotonic() < deadline:
            try:
                raw_value, _snapshot = admin.version()
                actual = parse_reviewed_toxiproxy_version_response(raw_value)
                expected = self.toxiproxy_artifact.version  # type: ignore[attr-defined]
                if actual != expected:
                    raise ToxiproxyControlError(
                        f"unexpected Toxiproxy runtime version {actual!r}; expected {expected!r}"
                    )
                return
            except RuntimeError as exc:
                last_problem = exc
                remaining = max(0.0, deadline - time.monotonic())
                if remaining:
                    time.sleep(min(0.02, remaining))
        raise ToxiproxyPrerequisiteError("Toxiproxy admin API did not become ready") from last_problem


class _ReviewedAttemptEvidenceBinding:
    """Retain concrete exchange diagnostics and enforce fixture integrity."""

    def _execute_role_exchange(
        self,
        *,
        container_name: str,
        endpoint: MaterializedEndpoint,
        attempt_document: dict[str, object],
        extra_connect: bool,
    ) -> dict[str, object]:
        exchange = super()._execute_role_exchange(  # type: ignore[misc]
            container_name=container_name,
            endpoint=endpoint,
            attempt_document=attempt_document,
            extra_connect=extra_connect,
        )
        phase_id = str(attempt_document.get("phaseId", "unknown"))
        attempt_id = str(attempt_document.get("attemptId", ""))
        if not attempt_id:
            raise ToxiproxyControlError("exchange diagnostic cannot be bound without attempt identity")
        ref = self.artifact_store.put_bytes(  # type: ignore[attr-defined]
            json.dumps(exchange, sort_keys=True, separators=(",", ":")).encode("utf-8"),
            logical_role=f"exchange-diagnostic-{phase_id}",
        )
        pending = getattr(self, "_exchange_diagnostic_refs", None)
        if pending is None:
            pending = {}
            setattr(self, "_exchange_diagnostic_refs", pending)
        if attempt_id in pending:
            raise ToxiproxyControlError(f"duplicate exchange diagnostic for attempt {attempt_id!r}")
        pending[attempt_id] = ref
        return exchange

    def certified_attempt(
        self,
        phase_id: str,
        privileged: bool,
        negative_mode: NegativeMode | None,
    ) -> PhaseExecution:
        execution = super().certified_attempt(  # type: ignore[misc]
            phase_id,
            privileged,
            negative_mode,
        )
        pending: dict[str, ArtifactRef] = getattr(self, "_exchange_diagnostic_refs", {})
        diagnostic_ref = pending.pop(execution.observation.attempt_id, None)
        evidence_refs = execution.evidence_refs
        validity = execution.observation.validity_problems
        if diagnostic_ref is None:
            validity += ("exchange-diagnostic:missing",)
        else:
            evidence_refs += (diagnostic_ref,)

        if execution.observation.completed:
            fixture_refs = tuple(
                ref for ref in evidence_refs if ref.logical_role == f"fixture-exchange-{phase_id}"
            )
            if len(fixture_refs) != 1:
                validity += ("fixture-evidence:completed-exchange-missing-exact-event",)
            else:
                try:
                    document = json.loads(  # type: ignore[attr-defined]
                        self.artifact_store.read_verified(fixture_refs[0]).decode("utf-8")
                    )
                except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    validity += (f"fixture-evidence:unreadable:{type(exc).__name__}",)
                else:
                    problem = fixture_integrity_problem(document)
                    if problem is not None:
                        validity += (problem,)
        else:
            fixture_ref = self._retain_incomplete_fixture_diagnostic(
                phase_id,
                execution.observation.attempt_id,
            )
            if fixture_ref is not None:
                evidence_refs += (fixture_ref,)

        if validity == execution.observation.validity_problems and evidence_refs == execution.evidence_refs:
            return execution
        return PhaseExecution(
            observation=replace(execution.observation, validity_problems=validity),
            evidence_refs=evidence_refs,
        )

    def _retain_incomplete_fixture_diagnostic(
        self,
        phase_id: str,
        attempt_id: str,
    ) -> ArtifactRef | None:
        fixture = (
            self._control_fixture  # type: ignore[attr-defined]
            if phase_id == "non-target-control"
            else self._selected_fixture  # type: ignore[attr-defined]
        )
        if fixture is None:
            return None
        try:
            document = fixture.request(
                {
                    "op": "event",
                    "attemptId": attempt_id,
                    "timeoutS": _INCOMPLETE_FIXTURE_DIAGNOSTIC_TIMEOUT_S,
                }
            )
        except RuntimeError as exc:
            document = {
                "attemptId": attempt_id,
                "status": "unavailable",
                "errorType": type(exc).__name__,
            }
        return self.artifact_store.put_bytes(  # type: ignore[attr-defined]
            json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8"),
            logical_role=f"fixture-diagnostic-{phase_id}",
        )


class VerifiedToxiproxyLiveLab(
    _ReviewedAttemptEvidenceBinding,
    _ReviewedToxiproxyVersionBinding,
    ToxiproxyLiveLab,
):
    """Canonical TEL-002 concrete lab with reviewed runtime/evidence boundaries."""

    def _prepare_helper_artifact(self) -> None:
        prepare_exact_helper_image(self.docker, self.helper_artifact)


class VerifiedUpstreamHiddenRetryLiveLab(
    _ReviewedAttemptEvidenceBinding,
    _ReviewedToxiproxyVersionBinding,
    UpstreamHiddenRetryLiveLab,
):
    """Canonical upstream HiddenRetry faulty assembly with reviewed boundaries."""

    def _prepare_helper_artifact(self) -> None:
        prepare_exact_helper_image(self.docker, self.helper_artifact)

"""Narrow trusted live bindings for Network Control evidence execution.

These project-local concrete bindings apply reviewed runtime prerequisites to the
capture-qualification and TEL-002/TEL-003 execution paths. They are deliberately
not provider abstractions and do not define portable AVP semantics.
"""

from __future__ import annotations

import json
import time

from .capture_qualification_retransmission import RetransmissionQualifiedCaptureQualification
from .helper_image_verification import prepare_exact_helper_image
from .toxiproxy_binding import (
    ToxiproxyAdminClient,
    ToxiproxyControlError,
    ToxiproxyPrerequisiteError,
)
from .toxiproxy_live_lab import ToxiproxyLiveLab
from .toxiproxy_negative_assemblies import UpstreamHiddenRetryLiveLab


def parse_reviewed_toxiproxy_version_response(value: str) -> str:
    """Parse the exact Toxiproxy v2.12.0 ``GET /version`` response contract.

    The pinned upstream implementation returns one JSON object containing only a
    string ``version`` member. Plain text, malformed JSON, additional fields,
    missing fields, or non-string values are rejected rather than treated as
    compatibility aliases. The returned version is still compared against the
    reviewed artifact version by the trusted live binding.
    """

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


class VerifiedCaptureQualification(RetransmissionQualifiedCaptureQualification):
    """Capture qualification using the shared exact helper-image boundary."""

    def _prepare_helper(self) -> None:
        prepare_exact_helper_image(self.docker, self.helper)


class _ReviewedToxiproxyVersionBinding:
    """Apply the exact pinned Toxiproxy v2.12.0 admin-version contract."""

    toxiproxy_artifact: object
    toxiproxy: object
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


class VerifiedToxiproxyLiveLab(_ReviewedToxiproxyVersionBinding, ToxiproxyLiveLab):
    """TEL-002 concrete lab using reviewed helper and admin-version boundaries."""

    def _prepare_helper_artifact(self) -> None:
        prepare_exact_helper_image(self.docker, self.helper_artifact)


class VerifiedUpstreamHiddenRetryLiveLab(
    _ReviewedToxiproxyVersionBinding,
    UpstreamHiddenRetryLiveLab,
):
    """Upstream HiddenRetry faulty assembly with reviewed runtime boundaries."""

    def _prepare_helper_artifact(self) -> None:
        prepare_exact_helper_image(self.docker, self.helper_artifact)

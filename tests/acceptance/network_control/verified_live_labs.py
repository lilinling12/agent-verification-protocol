"""Narrow live-lab bindings that share exact helper-image verification.

These classes are project-local concrete execution bindings. They exist only to
apply the same reviewed helper-image materialization rule to capture qualification
and TEL-002/TEL-003 live execution; they are not provider abstractions.
"""

from __future__ import annotations

from .capture_qualification_retransmission import RetransmissionQualifiedCaptureQualification
from .helper_image_verification import prepare_exact_helper_image
from .toxiproxy_live_lab import ToxiproxyLiveLab
from .toxiproxy_negative_assemblies import UpstreamHiddenRetryLiveLab


class VerifiedCaptureQualification(RetransmissionQualifiedCaptureQualification):
    """Capture qualification using the shared exact helper-image boundary."""

    def _prepare_helper(self) -> None:
        prepare_exact_helper_image(self.docker, self.helper)


class VerifiedToxiproxyLiveLab(ToxiproxyLiveLab):
    """TEL-002 concrete lab using the shared exact helper-image boundary."""

    def _prepare_helper_artifact(self) -> None:
        prepare_exact_helper_image(self.docker, self.helper_artifact)


class VerifiedUpstreamHiddenRetryLiveLab(UpstreamHiddenRetryLiveLab):
    """Upstream HiddenRetry faulty assembly with shared helper verification."""

    def _prepare_helper_artifact(self) -> None:
        prepare_exact_helper_image(self.docker, self.helper_artifact)

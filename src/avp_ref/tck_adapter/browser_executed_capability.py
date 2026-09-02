"""Provider-neutral executed Browser capability evaluation helpers.

This module evaluates observable Browser behavior through the existing shared
harness. It deliberately contains no concrete browser, automation transport, or
engine selection logic. Provider-specific setup and fault injection belong in
private implementation/test-driver seams.

The evaluator is implementation infrastructure for AVP-BROWSER-020 evidence. It
does not activate Browser TCK ownership and does not make metadata sufficient
for conformance.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from avp_ref.tck_adapter.browser_harness import (
    BrowserConformanceHarness,
    BrowserHarnessError,
    BrowserSettlementLedger,
    BrowserSUT,
    BrowserVerificationError,
    MaterializedBrowserFixture,
)


@dataclass(frozen=True, slots=True)
class BrowserExecutedMetadata:
    """Portable metadata identity used only to prove negative twins are identical."""

    profile: str
    revision: str
    canonical_representation: str
    manifest_digest: str
    execution_bindings: tuple[tuple[str, str, str], ...]

    @classmethod
    def from_fixture(cls, fixture: MaterializedBrowserFixture) -> "BrowserExecutedMetadata":
        bindings = tuple(
            sorted(
                (
                    str(reference),
                    str(binding["identity"]),
                    str(binding["identityType"]),
                )
                for reference, binding in fixture.manifest["executionBindings"].items()
            )
        )
        return cls(
            profile=str(fixture.manifest["profile"]),
            revision=str(fixture.manifest["revision"]),
            canonical_representation=str(fixture.manifest["canonicalRepresentation"]),
            manifest_digest=fixture.manifest_digest,
            execution_bindings=bindings,
        )


class BrowserExecutedCapabilityEvaluator:
    """Evaluate required behavior without branching on implementation identity."""

    @staticmethod
    def require_metadata_identical(
        reference: BrowserExecutedMetadata,
        candidate: BrowserExecutedMetadata,
    ) -> None:
        if candidate != reference:
            raise BrowserVerificationError(
                "executed-capability negative control changed governed metadata"
            )

    @staticmethod
    def require_baseline_projection(
        harness: BrowserConformanceHarness,
        sut: BrowserSUT,
        settlement: BrowserSettlementLedger,
        *,
        expected_digest: str,
    ) -> None:
        observed = harness.authoritative_projection(sut, settlement)
        if observed.digest != expected_digest:
            raise BrowserVerificationError(
                "executed Browser behavior does not reproduce governed baseline identity"
            )

    @staticmethod
    def require_rejected(
        operation: Callable[[], object],
        *,
        obligation: str,
    ) -> None:
        """Require one negative-control operation to fail closed.

        The concrete test driver chooses how to induce the broken behavior. The
        portable expectation is only that the behavior cannot be accepted.
        """

        if not obligation:
            raise BrowserVerificationError("negative-control obligation must be non-empty")
        try:
            operation()
        except BrowserHarnessError:
            return
        raise BrowserVerificationError(
            f"executed Browser negative control was accepted: {obligation}"
        )

    @staticmethod
    def require_subject_visibility(
        subject_surface: Mapping[str, Any],
        *,
        authorized_surface: Mapping[str, Any],
        evaluator_private_values: Sequence[str],
    ) -> None:
        """Require an exact authorized Subject surface with no private-value leakage."""

        if dict(subject_surface) != dict(authorized_surface):
            raise BrowserVerificationError(
                "Subject-visible Browser surface differs from explicit authorization"
            )
        rendered_values = tuple(str(value) for value in subject_surface.values())
        for private_value in evaluator_private_values:
            if not isinstance(private_value, str) or not private_value:
                raise BrowserVerificationError(
                    "evaluator-private visibility probe values must be non-empty strings"
                )
            if any(private_value in rendered for rendered in rendered_values):
                raise BrowserVerificationError(
                    "evaluator-private Browser state leaked to Subject-visible surface"
                )

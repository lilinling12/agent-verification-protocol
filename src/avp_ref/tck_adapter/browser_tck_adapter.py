"""Atomic provider-neutral adapter assembly for the Browser v0.1 TCK.

This module enforces a repository governance invariant: the reference Browser
profile is owned as one mandatory eight-case unit or not owned at all. It does
not implement Browser semantics itself and it does not select a concrete browser
backend. Case-specific evaluators are assembled only after each governed case has
an executable provider-neutral evaluator backed by the shared Browser harness.

Keeping the assembly boundary Browser-specific avoids turning TCK dispatch into
a generic provider/plugin framework and prevents partial Browser case ownership
from accidentally becoming observable through ``supported_case_ids``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol, runtime_checkable

from .models import TCKAdapterError, TCKCaseResult

BROWSER_PROFILE = "avp-browser-unpartitioned-cookie-localstorage-v0.1"

BROWSER_MANDATORY_CASE_IDS = frozenset(
    {
        "AVP-TCK-BROWSER-IDENTITY-001",
        "AVP-TCK-BROWSER-SELECTION-CANONICAL-001",
        "AVP-TCK-BROWSER-COOKIE-001",
        "AVP-TCK-BROWSER-STATE-IMAGE-001",
        "AVP-TCK-BROWSER-EXECUTION-RESIDUAL-001",
        "AVP-TCK-BROWSER-SETTLEMENT-LIFECYCLE-001",
        "AVP-TCK-BROWSER-SECURITY-001",
        "AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001",
    }
)


@runtime_checkable
class BrowserTCKCaseEvaluator(Protocol):
    """One Browser case evaluator with a fixed governed case identity.

    Implementations may compose Browser-specific harness/control collaborators,
    but the evaluator must return the result for exactly ``case_id``. Provider
    setup remains outside this assembly boundary.
    """

    @property
    def case_id(self) -> str: ...

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult: ...


class BrowserTCKAdapter:
    """Dispatch the complete mandatory Browser profile as one atomic unit.

    Construction fails closed unless the evaluator set is exactly the governed
    eight-case Browser profile. This deliberately prevents a caller from
    exposing partial Browser ownership while implementation work is still in
    progress.
    """

    def __init__(self, evaluators: Iterable[BrowserTCKCaseEvaluator]) -> None:
        owners: dict[str, BrowserTCKCaseEvaluator] = {}
        for evaluator in evaluators:
            if not isinstance(evaluator, BrowserTCKCaseEvaluator):
                raise TCKAdapterError(
                    "Browser TCK evaluator does not satisfy the case evaluator contract"
                )
            case_id = evaluator.case_id
            if not isinstance(case_id, str) or not case_id:
                raise TCKAdapterError("Browser TCK evaluator case_id must be non-empty")
            if case_id in owners:
                raise TCKAdapterError(
                    f"Browser TCK case has multiple evaluators: {case_id}"
                )
            owners[case_id] = evaluator

        actual = frozenset(owners)
        if actual != BROWSER_MANDATORY_CASE_IDS:
            missing = sorted(BROWSER_MANDATORY_CASE_IDS - actual)
            unexpected = sorted(actual - BROWSER_MANDATORY_CASE_IDS)
            raise TCKAdapterError(
                "Browser TCK ownership must be activated atomically: "
                f"missing={missing}, unexpected={unexpected}"
            )

        self._owners = owners

    @property
    def supported_case_ids(self) -> frozenset[str]:
        """Return all eight Browser case IDs only after atomic construction."""

        return BROWSER_MANDATORY_CASE_IDS

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        """Validate Browser case identity/profile and dispatch to its evaluator."""

        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        domain = metadata.get("domain") if isinstance(metadata, Mapping) else None
        profile = case.get("profile")

        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("Browser TCK case metadata.id is missing")
        if domain != "browser":
            raise TCKAdapterError(
                f"Browser TCK case {case_id} must declare metadata.domain=browser"
            )
        if profile != BROWSER_PROFILE:
            raise TCKAdapterError(
                f"Browser TCK case {case_id} must target profile {BROWSER_PROFILE}"
            )

        evaluator = self._owners.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(f"unsupported Browser TCK case: {case_id}")

        result = evaluator.evaluate(case)
        if result.case_id != case_id:
            raise TCKAdapterError(
                "Browser TCK evaluator result identity mismatch: "
                f"expected {case_id}, got {result.case_id}"
            )
        return result

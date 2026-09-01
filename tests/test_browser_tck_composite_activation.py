from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any, Mapping

from avp_ref.tck_adapter.browser_tck_adapter import (
    BROWSER_MANDATORY_CASE_IDS,
    BROWSER_PROFILE,
    BrowserTCKAdapter,
)
from avp_ref.tck_adapter.models import TCKAdapterError, TCKCaseResult, TCKStatus
from avp_ref.tck_adapter.reference_composite import ReferenceConformanceAdapter


@dataclass(frozen=True, slots=True)
class _PassingBrowserEvaluator:
    case_id: str

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        return TCKCaseResult(
            case_id=self.case_id,
            status=TCKStatus.PASS,
            detail="synthetic provider-neutral composite routing proof",
        )


def _complete_browser_adapter() -> BrowserTCKAdapter:
    return BrowserTCKAdapter(
        _PassingBrowserEvaluator(case_id)
        for case_id in sorted(BROWSER_MANDATORY_CASE_IDS)
    )


def _browser_case(case_id: str) -> dict[str, Any]:
    return {
        "metadata": {"id": case_id, "domain": "browser"},
        "profile": BROWSER_PROFILE,
    }


class BrowserTCKCompositeActivationTest(unittest.TestCase):
    def test_default_composite_owns_zero_browser_cases(self) -> None:
        composite = ReferenceConformanceAdapter()

        self.assertTrue(
            BROWSER_MANDATORY_CASE_IDS.isdisjoint(composite.supported_case_ids)
        )

    def test_complete_browser_delegate_activates_only_all_eight_cases(self) -> None:
        default_case_ids = ReferenceConformanceAdapter().supported_case_ids
        browser_adapter = _complete_browser_adapter()
        composite = ReferenceConformanceAdapter(browser_adapter=browser_adapter)
        activated_case_ids = composite.supported_case_ids

        self.assertEqual(
            BROWSER_MANDATORY_CASE_IDS,
            activated_case_ids - default_case_ids,
            "Browser activation must add exactly the governed eight-case profile",
        )
        self.assertEqual(
            default_case_ids,
            activated_case_ids - BROWSER_MANDATORY_CASE_IDS,
            "Browser activation must not change ownership of any non-Browser case",
        )
        self.assertEqual(8, len(activated_case_ids & BROWSER_MANDATORY_CASE_IDS))

    def test_all_eight_browser_cases_dispatch_through_composite(self) -> None:
        composite = ReferenceConformanceAdapter(
            browser_adapter=_complete_browser_adapter()
        )

        results = {
            case_id: composite.evaluate(_browser_case(case_id))
            for case_id in sorted(BROWSER_MANDATORY_CASE_IDS)
        }

        self.assertEqual(BROWSER_MANDATORY_CASE_IDS, frozenset(results))
        for case_id, result in results.items():
            self.assertEqual(case_id, result.case_id)
            self.assertIs(TCKStatus.PASS, result.status)

    def test_composite_rejects_non_browser_adapter_injection(self) -> None:
        invalid_adapter: Any = object()
        with self.assertRaisesRegex(
            TCKAdapterError,
            "requires a complete BrowserTCKAdapter",
        ):
            ReferenceConformanceAdapter(browser_adapter=invalid_adapter)


if __name__ == "__main__":
    unittest.main()

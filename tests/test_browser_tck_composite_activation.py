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


class BrowserTCKCompositeActivationTest(unittest.TestCase):
    def test_default_composite_owns_zero_browser_cases(self) -> None:
        composite = ReferenceConformanceAdapter()

        self.assertTrue(
            BROWSER_MANDATORY_CASE_IDS.isdisjoint(composite.supported_case_ids)
        )

    def test_complete_browser_delegate_activates_all_eight_cases_atomically(self) -> None:
        browser_adapter = _complete_browser_adapter()
        composite = ReferenceConformanceAdapter(browser_adapter=browser_adapter)

        self.assertEqual(
            BROWSER_MANDATORY_CASE_IDS,
            composite.supported_case_ids & BROWSER_MANDATORY_CASE_IDS,
        )
        self.assertEqual(8, len(composite.supported_case_ids & BROWSER_MANDATORY_CASE_IDS))

        case_id = "AVP-TCK-BROWSER-IDENTITY-001"
        result = composite.evaluate(
            {
                "metadata": {"id": case_id, "domain": "browser"},
                "profile": BROWSER_PROFILE,
            }
        )
        self.assertEqual(case_id, result.case_id)
        self.assertIs(TCKStatus.PASS, result.status)

    def test_composite_rejects_non_browser_adapter_injection(self) -> None:
        with self.assertRaisesRegex(
            TCKAdapterError,
            "requires a complete BrowserTCKAdapter",
        ):
            ReferenceConformanceAdapter(browser_adapter=object())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()

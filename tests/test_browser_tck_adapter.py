from __future__ import annotations

import inspect
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
class _Evaluator:
    case_id: str
    result_case_id: str | None = None

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        del case
        return TCKCaseResult(
            self.result_case_id or self.case_id,
            TCKStatus.PASS,
            f"evaluated {self.case_id}",
        )


def _evaluators() -> list[_Evaluator]:
    return [_Evaluator(case_id) for case_id in sorted(BROWSER_MANDATORY_CASE_IDS)]


def _case(case_id: str) -> dict[str, object]:
    return {
        "apiVersion": "avp.tck/v0.1",
        "kind": "ConformanceCase",
        "metadata": {
            "id": case_id,
            "domain": "browser",
            "status": "draft",
        },
        "profile": BROWSER_PROFILE,
        "requirements": ["AVP-BROWSER-TEST"],
        "applicability": "mandatory",
        "type": "test",
        "vector": {},
        "expect": {},
    }


class BrowserTCKAdapterTest(unittest.TestCase):
    def test_complete_evaluator_set_exposes_exactly_eight_cases(self) -> None:
        adapter = BrowserTCKAdapter(_evaluators())

        self.assertEqual(BROWSER_MANDATORY_CASE_IDS, adapter.supported_case_ids)
        self.assertEqual(8, len(adapter.supported_case_ids))

    def test_partial_evaluator_set_is_rejected(self) -> None:
        evaluators = _evaluators()

        with self.assertRaisesRegex(
            TCKAdapterError,
            "Browser TCK ownership must be activated atomically",
        ):
            BrowserTCKAdapter(evaluators[:-1])

    def test_unexpected_case_is_rejected_even_when_count_is_eight(self) -> None:
        evaluators = _evaluators()
        evaluators[-1] = _Evaluator("AVP-TCK-BROWSER-NOT-GOVERNED-001")

        with self.assertRaisesRegex(TCKAdapterError, "unexpected="):
            BrowserTCKAdapter(evaluators)

    def test_duplicate_case_owner_is_rejected(self) -> None:
        evaluators = _evaluators()
        evaluators.append(evaluators[0])

        with self.assertRaisesRegex(TCKAdapterError, "multiple evaluators"):
            BrowserTCKAdapter(evaluators)

    def test_dispatch_preserves_exact_case_identity(self) -> None:
        adapter = BrowserTCKAdapter(_evaluators())
        case_id = "AVP-TCK-BROWSER-STATE-IMAGE-001"

        result = adapter.evaluate(_case(case_id))

        self.assertEqual(case_id, result.case_id)
        self.assertIs(TCKStatus.PASS, result.status)

    def test_wrong_result_identity_is_rejected(self) -> None:
        evaluators = _evaluators()
        target = "AVP-TCK-BROWSER-COOKIE-001"
        evaluators = [
            _Evaluator(item.case_id, "AVP-TCK-BROWSER-STATE-IMAGE-001")
            if item.case_id == target
            else item
            for item in evaluators
        ]
        adapter = BrowserTCKAdapter(evaluators)

        with self.assertRaisesRegex(TCKAdapterError, "result identity mismatch"):
            adapter.evaluate(_case(target))

    def test_non_browser_domain_is_rejected_before_dispatch(self) -> None:
        adapter = BrowserTCKAdapter(_evaluators())
        case = _case("AVP-TCK-BROWSER-IDENTITY-001")
        case["metadata"]["domain"] = "relational"

        with self.assertRaisesRegex(TCKAdapterError, "metadata.domain=browser"):
            adapter.evaluate(case)

    def test_wrong_profile_is_rejected_before_dispatch(self) -> None:
        adapter = BrowserTCKAdapter(_evaluators())
        case = _case("AVP-TCK-BROWSER-IDENTITY-001")
        case["profile"] = "avp-browser-synthetic-v9"

        with self.assertRaisesRegex(TCKAdapterError, "must target profile"):
            adapter.evaluate(case)

    def test_reference_composite_still_owns_zero_browser_cases(self) -> None:
        owned = ReferenceConformanceAdapter().supported_case_ids

        self.assertTrue(BROWSER_MANDATORY_CASE_IDS.isdisjoint(owned))

    def test_atomic_adapter_contains_no_concrete_provider_branching(self) -> None:
        import avp_ref.tck_adapter.browser_tck_adapter as module

        source = inspect.getsource(module).lower()
        forbidden = (
            "playwright",
            "selenium",
            "chromium",
            "firefox",
            "webkit",
            "cdp",
            "webdriver",
            "bidi",
        )

        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()

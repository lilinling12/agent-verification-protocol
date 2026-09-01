"""Real-browser proof for atomic Browser ownership in the reference composite.

The provider-neutral activation unit tests prove the ownership-set invariant with
synthetic evaluators. This integration layer deliberately reuses the complete
Chromium-backed Browser profile fixture from ``test_playwright_browser_tck_profile``
so the composite routing boundary is exercised without duplicating Browser case
semantics or concrete provider setup.
"""

from __future__ import annotations

import test_playwright_browser_tck_profile as browser_profile

from avp_ref.tck_adapter.browser_tck_adapter import BROWSER_MANDATORY_CASE_IDS
from avp_ref.tck_adapter.models import TCKStatus
from avp_ref.tck_adapter.reference_composite import ReferenceConformanceAdapter


class PlaywrightBrowserTCKCompositeActivationTest(
    browser_profile.PlaywrightBrowserTCKProfileTest
):
    """Route the already-proven complete Chromium profile through the composite."""

    def test_complete_eight_case_profile_executes_before_atomic_activation(self) -> None:
        """Replace the inherited pre-activation assertion with activation evidence."""

        browser_adapter = self._adapter()
        default_case_ids = ReferenceConformanceAdapter().supported_case_ids
        composite = ReferenceConformanceAdapter(browser_adapter=browser_adapter)
        activated_case_ids = composite.supported_case_ids

        self.assertEqual(
            BROWSER_MANDATORY_CASE_IDS,
            activated_case_ids - default_case_ids,
            "real Browser activation must add exactly the mandatory eight cases",
        )
        self.assertEqual(
            default_case_ids,
            activated_case_ids - BROWSER_MANDATORY_CASE_IDS,
            "real Browser activation must preserve every non-Browser owner",
        )

        results = []
        for case_id in sorted(BROWSER_MANDATORY_CASE_IDS):
            result = composite.evaluate(browser_profile._load_case(case_id))
            results.append(result)
            self.assertIs(TCKStatus.PASS, result.status, result.detail)

        self.assertEqual(
            BROWSER_MANDATORY_CASE_IDS,
            {result.case_id for result in results},
        )

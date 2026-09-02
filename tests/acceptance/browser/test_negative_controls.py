from __future__ import annotations

import unittest
from dataclasses import dataclass

from tests.acceptance.browser.evidence_runner import (
    decode_domstring_code_units,
    encode_domstring_code_units,
)


@dataclass(frozen=True, slots=True)
class _CookieState:
    name: str
    domain: str
    host_only: bool
    path: str
    same_site: str


@dataclass(frozen=True, slots=True)
class _RestoreClaim:
    backend_reported_success: bool
    independently_reprojected: bool
    target_equals_reprojection: bool
    unresolved_profile_mutations: int


def _cookie_projection_equivalent(
    target: tuple[_CookieState, ...], projected: tuple[_CookieState, ...]
) -> bool:
    return target == projected


def _restore_claim_acceptable(claim: _RestoreClaim) -> bool:
    return (
        claim.backend_reported_success
        and claim.independently_reprojected
        and claim.target_equals_reprojection
        and claim.unresolved_profile_mutations == 0
    )


class BrowserEvidenceNegativeControlsTest(unittest.TestCase):
    """Negative controls for the test-only Browser acceptance evidence oracle.

    These tests intentionally model invalid projection/restore claims. They do
    not implement a Browser runtime validator and must not be moved into
    packaged source before downstream Browser authority is separately adopted.
    """

    def setUp(self) -> None:
        self.target = (
            _CookieState(
                name="session",
                domain="a.test",
                host_only=True,
                path="/",
                same_site="Default",
            ),
        )

    def test_erasing_host_only_is_not_equivalent(self) -> None:
        lossy = (
            _CookieState(
                name="session",
                domain="a.test",
                host_only=False,
                path="/",
                same_site="Default",
            ),
        )
        self.assertFalse(_cookie_projection_equivalent(self.target, lossy))

    def test_normalizing_default_to_lax_is_not_equivalent(self) -> None:
        normalized = (
            _CookieState(
                name="session",
                domain="a.test",
                host_only=True,
                path="/",
                same_site="Lax",
            ),
        )
        self.assertFalse(_cookie_projection_equivalent(self.target, normalized))

    def test_omitting_selected_cookie_is_not_equivalent(self) -> None:
        self.assertFalse(_cookie_projection_equivalent(self.target, ()))

    def test_extra_in_scope_cookie_is_not_equivalent(self) -> None:
        extra = self.target + (
            _CookieState(
                name="runtime_dynamic",
                domain="a.test",
                host_only=True,
                path="/",
                same_site="Lax",
            ),
        )
        self.assertFalse(_cookie_projection_equivalent(self.target, extra))

    def test_lone_surrogate_must_not_be_repaired(self) -> None:
        lone_high = [0xD800]
        encoded = encode_domstring_code_units(lone_high)
        self.assertEqual(lone_high, decode_domstring_code_units(encoded))
        self.assertNotEqual([0xFFFD], decode_domstring_code_units(encoded))

    def test_backend_success_without_independent_reprojection_is_rejected(self) -> None:
        claim = _RestoreClaim(
            backend_reported_success=True,
            independently_reprojected=False,
            target_equals_reprojection=True,
            unresolved_profile_mutations=0,
        )
        self.assertFalse(_restore_claim_acceptable(claim))

    def test_unresolved_profile_mutation_rejects_restore_claim(self) -> None:
        claim = _RestoreClaim(
            backend_reported_success=True,
            independently_reprojected=True,
            target_equals_reprojection=True,
            unresolved_profile_mutations=1,
        )
        self.assertFalse(_restore_claim_acceptable(claim))

    def test_reprojection_mismatch_rejects_restore_claim(self) -> None:
        claim = _RestoreClaim(
            backend_reported_success=True,
            independently_reprojected=True,
            target_equals_reprojection=False,
            unresolved_profile_mutations=0,
        )
        self.assertFalse(_restore_claim_acceptable(claim))

    def test_complete_positive_claim_is_accepted_by_test_oracle(self) -> None:
        claim = _RestoreClaim(
            backend_reported_success=True,
            independently_reprojected=True,
            target_equals_reprojection=True,
            unresolved_profile_mutations=0,
        )
        self.assertTrue(_restore_claim_acceptable(claim))


if __name__ == "__main__":
    unittest.main()

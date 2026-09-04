"""Regression tests for AEP-0012 packet-path cut semantics."""

from __future__ import annotations

import unittest

from acceptance.network_control.attempt_client import ExchangeObservation
from acceptance.network_control.packet_path.live_qualification import _cut_exchange


class PacketPathCutSemanticsTests(unittest.TestCase):
    def test_early_native_failure_still_qualifies_as_exact_exchange_cut(self) -> None:
        observation = ExchangeObservation(
            attempt_id="opaque-cut-attempt",
            completed=False,
            mismatch_observed=False,
            observation_budget_expired=False,
            elapsed_ns=10,
            response_size=0,
            response_sha256=None,
            native_error="ECONNREFUSED",
        )

        self.assertTrue(_cut_exchange(observation))

    def test_byte_mismatch_is_not_transport_cut(self) -> None:
        observation = ExchangeObservation(
            attempt_id="opaque-mismatch-attempt",
            completed=False,
            mismatch_observed=True,
            observation_budget_expired=False,
            elapsed_ns=10,
            response_size=1,
            response_sha256="a" * 64,
            native_error="ECONNRESET",
        )

        self.assertFalse(_cut_exchange(observation))


if __name__ == "__main__":
    unittest.main()

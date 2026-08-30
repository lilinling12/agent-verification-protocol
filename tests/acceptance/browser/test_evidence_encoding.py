from __future__ import annotations

import unittest

from tests.acceptance.browser.evidence_runner import (
    decode_domstring_code_units,
    encode_domstring_code_units,
)


class BrowserEvidenceEncodingTest(unittest.TestCase):
    """Exercise the test-only DOMString evidence codec without browser tooling."""

    def test_round_trip_preserves_exact_utf16_code_units(self) -> None:
        samples = (
            [],
            [0x0000],
            [0x0041, 0x0056, 0x0050],
            [0x4E2D, 0x6587],
            [0xD83D, 0xDE80],
            [0xD800],
            [0xDC00],
            [0x00E9],
            [0x0065, 0x0301],
        )
        for sample in samples:
            with self.subTest(sample=sample):
                encoded = encode_domstring_code_units(list(sample))
                self.assertEqual(list(sample), decode_domstring_code_units(encoded))

    def test_rejects_out_of_range_code_units(self) -> None:
        for sample in ([-1], [0x10000]):
            with self.subTest(sample=sample):
                with self.assertRaises(ValueError):
                    encode_domstring_code_units(sample)

    def test_rejects_odd_decoded_byte_length(self) -> None:
        with self.assertRaises(ValueError):
            decode_domstring_code_units("AA")


if __name__ == "__main__":
    unittest.main()

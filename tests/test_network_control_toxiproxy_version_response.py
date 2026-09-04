"""Regression checks for the pinned Toxiproxy v2.12.0 version response contract."""

from __future__ import annotations

import unittest

from acceptance.network_control.toxiproxy_binding import ToxiproxyControlError
from acceptance.network_control.verified_live_labs import parse_reviewed_toxiproxy_version_response


class ToxiproxyVersionResponseTests(unittest.TestCase):
    def test_exact_v212_json_response_is_accepted(self) -> None:
        self.assertEqual(
            parse_reviewed_toxiproxy_version_response('{"version": "2.12.0"}'),
            "2.12.0",
        )

    def test_plaintext_version_is_rejected(self) -> None:
        with self.assertRaisesRegex(ToxiproxyControlError, "not valid JSON"):
            parse_reviewed_toxiproxy_version_response("2.12.0")

    def test_legacy_server_prefix_is_rejected(self) -> None:
        with self.assertRaisesRegex(ToxiproxyControlError, "not valid JSON"):
            parse_reviewed_toxiproxy_version_response("toxiproxy-server version 2.12.0")

    def test_malformed_json_is_rejected(self) -> None:
        with self.assertRaisesRegex(ToxiproxyControlError, "not valid JSON"):
            parse_reviewed_toxiproxy_version_response('{"version":')

    def test_non_object_json_is_rejected(self) -> None:
        with self.assertRaisesRegex(ToxiproxyControlError, "not an object"):
            parse_reviewed_toxiproxy_version_response('["2.12.0"]')

    def test_missing_version_is_rejected(self) -> None:
        with self.assertRaisesRegex(ToxiproxyControlError, "shape is not exact"):
            parse_reviewed_toxiproxy_version_response("{}")

    def test_additional_fields_are_rejected(self) -> None:
        with self.assertRaisesRegex(ToxiproxyControlError, "shape is not exact"):
            parse_reviewed_toxiproxy_version_response(
                '{"version":"2.12.0","provider":"unexpected"}'
            )

    def test_non_string_version_is_rejected(self) -> None:
        with self.assertRaisesRegex(ToxiproxyControlError, "non-empty string"):
            parse_reviewed_toxiproxy_version_response('{"version":2120}')


if __name__ == "__main__":
    unittest.main()

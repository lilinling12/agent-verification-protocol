"""Unit tests for Browser acceptance-evidence source provenance binding."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from .bind_evidence_source import bind_evidence_source


class BrowserEvidenceSourceBindingTest(unittest.TestCase):
    def test_binds_document_when_checkout_matches_expected_head(self) -> None:
        expected = "a" * 40
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(
                json.dumps({"repositorySha": "b" * 40, "schema": "fixture"}),
                encoding="utf-8",
            )

            with patch(
                "tests.acceptance.browser.bind_evidence_source.current_head_sha",
                return_value=expected,
            ):
                bind_evidence_source(path, expected)

            document = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(expected, document["repositorySha"])
            self.assertEqual("b" * 40, document["preBindingRepositorySha"])
            self.assertEqual(
                {"mode": "exact-checked-out-head", "verified": True},
                document["sourceBinding"],
            )

    def test_rejects_checkout_that_does_not_match_expected_head(self) -> None:
        expected = "a" * 40
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text("{}", encoding="utf-8")

            with patch(
                "tests.acceptance.browser.bind_evidence_source.current_head_sha",
                return_value="b" * 40,
            ):
                with self.assertRaisesRegex(RuntimeError, "does not match"):
                    bind_evidence_source(path, expected)

    def test_rejects_non_full_or_non_hex_source_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text("{}", encoding="utf-8")

            for invalid in ("abc", "G" * 40, "a" * 39, "a" * 41):
                with self.subTest(invalid=invalid):
                    with self.assertRaisesRegex(ValueError, "full 40-character"):
                        bind_evidence_source(path, invalid)


if __name__ == "__main__":
    unittest.main()

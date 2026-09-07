"""Ordinary-CI coverage for retained NPR-011 cross-mechanism reassessment."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from acceptance.network_control.cross_mechanism import (
    SemanticBinding,
    decode_reassessment_archive,
    encode_reassessment_archive,
    verify_reassessment_record,
)
from acceptance.network_control.evidence_core import EvidenceMaterializationError

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_ARCHIVE = (
    _REPOSITORY_ROOT
    / "docs"
    / "acceptance"
    / "evidence"
    / "alpha3-network-control-cross-mechanism-npr011-v0.1.json.gz.b64"
)
_BINDING = SemanticBinding(
    aep_path="rfcs/AEP-0012-network-control-resource-profile.md",
    aep_git_blob="0b5ebdddb45533cf91a7bc264dcfe7548b54391c",
    current_comparator_path="tests/acceptance/network_control/portable_comparator.py",
    current_comparator_git_blob="39169f40083e204560606cd9db0d8f1a1dda57bd",
    candidate_parent_commit="0ccac4339ed4c8f773b6413428e3df3b15f6b79e",
)
_EXPECTED_ARCHIVE_SHA256 = "30f2da733781f12827ee49f0ea1aace56ba2992a20a017cb806e66af3a50f079"
_EXPECTED_JSON_SHA256 = "b768f6f6d96327cffa550c0f6db1f0b35ff48696362e4113766cce7195ab28ac"


class NetworkControlCrossMechanismTests(unittest.TestCase):
    def _exact_record(self) -> bytes:
        return decode_reassessment_archive(_ARCHIVE.read_bytes())

    def _document(self) -> dict[str, object]:
        return json.loads(self._exact_record())

    def test_committed_record_reassesses_with_current_portable_comparator(self) -> None:
        document = verify_reassessment_record(self._exact_record(), semantic_binding=_BINDING)
        mechanisms = document["mechanisms"]
        self.assertEqual(len(mechanisms["terminating-intercepting"]["cases"]), 10)
        self.assertEqual(len(mechanisms["packet-path"]["cases"]), 9)

    def test_committed_archive_has_locked_exact_identity_and_canonical_encoding(self) -> None:
        archive = _ARCHIVE.read_bytes()
        exact = decode_reassessment_archive(archive)
        self.assertEqual(hashlib.sha256(archive).hexdigest(), _EXPECTED_ARCHIVE_SHA256)
        self.assertEqual(hashlib.sha256(exact).hexdigest(), _EXPECTED_JSON_SHA256)
        self.assertEqual(encode_reassessment_archive(exact), archive)

    def test_portable_observation_tamper_fails_closed(self) -> None:
        document = self._document()
        cases = document["mechanisms"]["packet-path"]["cases"]
        positive = next(item for item in cases if item["slug"] == "positive")
        positive["portableObservations"]["attempts"]["subjectActiveCut"]["completed"] = True

        with self.assertRaisesRegex(EvidenceMaterializationError, "current comparator differs"):
            verify_reassessment_record(_canonical(document), semantic_binding=_BINDING)

    def test_missing_required_negative_family_fails_closed(self) -> None:
        document = self._document()
        cases = document["mechanisms"]["packet-path"]["cases"]
        document["mechanisms"]["packet-path"]["cases"] = [
            item for item in cases if item["negativeFamily"] != "ScheduleLeak"
        ]

        with self.assertRaisesRegex(EvidenceMaterializationError, "negative-family coverage drift"):
            verify_reassessment_record(_canonical(document), semantic_binding=_BINDING)

    def test_semantic_git_blob_drift_fails_closed(self) -> None:
        document = self._document()
        document["mechanisms"]["packet-path"]["source"]["semanticGitBlob"] = "1" * 40

        with self.assertRaisesRegex(EvidenceMaterializationError, "semantic Git blob drift"):
            verify_reassessment_record(_canonical(document), semantic_binding=_BINDING)

    def test_noncanonical_json_is_not_accepted_as_exact_reassessment(self) -> None:
        document = self._document()
        pretty = json.dumps(document, indent=2, sort_keys=True).encode("utf-8")

        with self.assertRaisesRegex(EvidenceMaterializationError, "not canonical exact bytes"):
            verify_reassessment_record(pretty, semantic_binding=_BINDING)


def _canonical(document: object) -> bytes:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


if __name__ == "__main__":
    unittest.main()

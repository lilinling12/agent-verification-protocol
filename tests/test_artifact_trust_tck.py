from __future__ import annotations

import unittest
from pathlib import Path

from avp_ref.tck_adapter import TCKRepository, TCKRunner, TCKStatus

ROOT = Path(__file__).resolve().parents[1]


class ReferenceArtifactTrustTCKTest(unittest.TestCase):
    def test_reference_implementation_passes_mandatory_trust_profile(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(repository).run(
            profile="avp-artifact-trust-v0.1"
        )

        self.assertTrue(result.conformant)
        self.assertEqual(8, result.report["summary"]["total"])
        self.assertEqual(7, result.report["summary"]["passed"])
        self.assertEqual(0, result.report["summary"]["failed"])
        self.assertEqual(1, result.report["summary"]["skipped"])
        publication = next(
            item
            for item in result.case_results
            if item.case_id == "AVP-TCK-TRUST-PUBLICATION-AUTHORITY-001"
        )
        self.assertIs(TCKStatus.SKIP, publication.status)
        self.assertIsNotNone(publication.skip_reason)

    def test_reference_runtime_does_not_overclaim_publication_isolation(self) -> None:
        repository = TCKRepository(ROOT)
        result = TCKRunner.for_reference(
            repository,
            capabilities=("artifact-attestation-publication",),
        ).run(profile="avp-artifact-trust-v0.1")

        self.assertFalse(result.conformant)
        self.assertEqual(8, result.report["summary"]["total"])
        self.assertEqual(7, result.report["summary"]["passed"])
        self.assertEqual(1, result.report["summary"]["failed"])
        publication = next(
            item
            for item in result.case_results
            if item.case_id == "AVP-TCK-TRUST-PUBLICATION-AUTHORITY-001"
        )
        self.assertIs(TCKStatus.FAIL, publication.status)
        self.assertIn("does not claim", publication.detail)


if __name__ == "__main__":
    unittest.main()

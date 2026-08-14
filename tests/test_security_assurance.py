from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from avp_ref.security import (
    AssuranceClaim,
    SecurityAssurance,
    SecurityIsolationClaims,
    load_security_assurance_schema,
)

ROOT = Path(__file__).resolve().parents[1]


class SecurityAssuranceTest(unittest.TestCase):
    def test_packaged_schema_matches_normative_repository_schema(self) -> None:
        repository_schema = json.loads(
            (ROOT / "schemas" / "security-assurance.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(repository_schema, load_security_assurance_schema())

    def test_baseline_reference_declaration_is_schema_valid_and_non_inflating(self) -> None:
        assurance = SecurityAssurance.baseline_reference()
        assurance.validate()

        self.assertEqual(
            {
                "apiVersion": "avp.security/v0.1",
                "kind": "SecurityAssurance",
                "isolation": {
                    "apiCapability": "verified",
                    "credentialContext": "not-claimed",
                    "process": "not-claimed",
                    "network": "not-claimed",
                    "tenant": "not-claimed",
                    "sandbox": "not-claimed",
                },
            },
            assurance.to_dict(),
        )

    def test_stronger_claims_require_explicit_construction(self) -> None:
        baseline = SecurityAssurance.baseline_reference()
        strengthened = SecurityAssurance(
            SecurityIsolationClaims(
                api_capability=AssuranceClaim.VERIFIED,
                credential_context=AssuranceClaim.VERIFIED,
                process=AssuranceClaim.NOT_CLAIMED,
                network=AssuranceClaim.NOT_CLAIMED,
                tenant=AssuranceClaim.NOT_CLAIMED,
                sandbox=AssuranceClaim.NOT_CLAIMED,
            )
        )
        strengthened.validate()

        self.assertEqual(
            "not-claimed",
            baseline.to_dict()["isolation"]["credentialContext"],
        )
        self.assertEqual(
            "verified",
            strengthened.to_dict()["isolation"]["credentialContext"],
        )

    def test_schema_rejects_claim_inflation_vocabulary(self) -> None:
        declaration = SecurityAssurance.baseline_reference().to_dict()
        declaration["isolation"]["sandbox"] = "implied"
        validator = Draft202012Validator(load_security_assurance_schema())
        self.assertTrue(list(validator.iter_errors(declaration)))


if __name__ == "__main__":
    unittest.main()

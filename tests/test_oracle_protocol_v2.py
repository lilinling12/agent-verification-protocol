from __future__ import annotations

import base64
import json
import unittest

from avp_ref.artifacts import sha256_digest
from avp_ref.oracle_runner import OracleProtocolError, SubprocessOracleRunner
from avp_ref.oracle_runner.protocol import PROTOCOL_VERSION, decode_success


class OracleEvidenceProtocolV2Test(unittest.TestCase):
    def test_runner_advertises_breaking_v2_evidence_protocol(self) -> None:
        self.assertEqual("avp.oracle/v2", PROTOCOL_VERSION)
        self.assertEqual(
            PROTOCOL_VERSION,
            SubprocessOracleRunner().describe().protocol_version,
        )

    def test_parent_rejects_tampered_evidence_content(self) -> None:
        declared_content = b"AVP"
        tampered_content = b"AVQ"
        frame = {
            "protocol": PROTOCOL_VERSION,
            "request_id": "oracle_req_tamper",
            "status": "SUCCESS",
            "results": [],
            "evidence": [
                {
                    "evidence_id": "ev_tamper",
                    "type": "state_projection",
                    "media_type": "application/octet-stream",
                    "digest": sha256_digest(declared_content),
                    "content_base64": base64.b64encode(tampered_content).decode("ascii"),
                    "classification": "evaluator-confidential",
                }
            ],
        }
        encoded = (
            json.dumps(frame, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        with self.assertRaises(OracleProtocolError):
            decode_success(
                encoded,
                expected_request_id="oracle_req_tamper",
                max_bytes=4096,
            )


if __name__ == "__main__":
    unittest.main()

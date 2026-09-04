"""PTL-001 ordinary-CI tests for the packet-path process worker."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import unittest
from unittest.mock import patch

from acceptance.network_control.evidence_core import (
    AttemptMaterial,
    EvidenceMaterializationError,
    MaterializedEndpoint,
)
from acceptance.network_control.packet_path import worker


class PacketPathWorkerSerializationTests(unittest.TestCase):
    def setUp(self) -> None:
        challenge = b"challenge-bytes"
        request = b"REQ\x00" + challenge
        response = b"RESP\x00" + challenge
        self.attempt = AttemptMaterial(
            run_id="run-worker",
            phase_id="subject-active-cut",
            ordinal=3,
            path_id="selected-path",
            attempt_id="a" * 64,
            challenge=challenge,
            challenge_sha256=hashlib.sha256(challenge).hexdigest(),
            request_bytes=request,
            expected_response_bytes=response,
            request_sha256=hashlib.sha256(request).hexdigest(),
            response_sha256=hashlib.sha256(response).hexdigest(),
        )
        self.endpoint = MaterializedEndpoint(
            family="ipv4",
            address="198.18.0.6",
            port=42101,
            role="fixture",
        )

    def test_attempt_round_trip_preserves_exact_material_and_identity(self) -> None:
        document = worker._attempt_document(self.attempt)

        self.assertEqual(worker._attempt_from_document(document), self.attempt)
        self.assertTrue(all(not isinstance(value, bytes) for value in document.values()))

    def test_attempt_digest_tampering_fails_closed(self) -> None:
        document = worker._attempt_document(self.attempt)
        document["requestSha256"] = "0" * 64

        with self.assertRaises(EvidenceMaterializationError):
            worker._attempt_from_document(document)

    def test_closed_document_shape_rejects_unexpected_fields(self) -> None:
        document = worker._attempt_document(self.attempt)
        document["providerVerdict"] = "SATISFIED"

        with self.assertRaises(EvidenceMaterializationError):
            worker._attempt_from_document(document)

    def test_endpoint_requires_typed_integer_port(self) -> None:
        document = worker._endpoint_document(self.endpoint)
        document["port"] = "42101"

        with self.assertRaises(EvidenceMaterializationError):
            worker._endpoint_from_document(document)

    def test_oversized_json_command_fails_closed(self) -> None:
        payload = '{"value":"' + ("x" * worker._MAX_JSON_LINE_CHARS) + '"}\n'

        with self.assertRaises(EvidenceMaterializationError):
            worker._read_document(io.StringIO(payload))


class PacketPathWorkerExchangeTests(unittest.TestCase):
    def test_same_socket_additional_connect_is_rejected_before_exchange(self) -> None:
        endpoint = MaterializedEndpoint(
            family="ipv4",
            address="198.18.0.6",
            port=42101,
            role="fixture",
        )
        attempt = _attempt()
        stdin = io.StringIO(
            json.dumps(
                {
                    "endpoint": worker._endpoint_document(endpoint),
                    "attempt": worker._attempt_document(attempt),
                    "observationBudgetNs": 1_000_000,
                    "additionalConnectTarget": worker._endpoint_document(endpoint),
                }
            )
            + "\n"
        )

        with patch.object(worker, "execute_exact_exchange") as execute:
            with self.assertRaises(EvidenceMaterializationError):
                worker._exchange_worker(stdin, io.StringIO())
        execute.assert_not_called()

    def test_distinct_additional_connect_is_explicit_negative_hook(self) -> None:
        endpoint = MaterializedEndpoint(
            family="ipv4",
            address="198.18.0.6",
            port=42101,
            role="fixture",
        )
        alternate = MaterializedEndpoint(
            family="ipv4",
            address="198.18.0.6",
            port=42102,
            role="control-fixture",
        )
        attempt = _attempt()
        stdin = io.StringIO(
            json.dumps(
                {
                    "endpoint": worker._endpoint_document(endpoint),
                    "attempt": worker._attempt_document(attempt),
                    "observationBudgetNs": 1_000_000,
                    "additionalConnectTarget": worker._endpoint_document(alternate),
                }
            )
            + "\n"
        )
        stdout = io.StringIO()
        observation = worker.ExchangeObservation(
            attempt_id=attempt.attempt_id,
            completed=False,
            mismatch_observed=False,
            observation_budget_expired=True,
            elapsed_ns=1,
            response_size=0,
            response_sha256=None,
            native_error=None,
        )

        with patch.object(worker, "execute_exact_exchange", return_value=observation) as execute:
            with patch.object(worker, "_emit_additional_connect", return_value=115) as extra:
                self.assertEqual(worker._exchange_worker(stdin, stdout), 0)

        execute.assert_called_once_with(
            endpoint,
            attempt,
            observation_budget_ns=1_000_000,
        )
        extra.assert_called_once_with(alternate)
        result = json.loads(stdout.getvalue())
        self.assertTrue(result["additionalConnectAttempted"])
        self.assertEqual(result["additionalConnectNativeResult"], 115)
        self.assertNotIn("verdict", result)


class PacketPathWorkerSecurityProbeTests(unittest.TestCase):
    def test_security_probe_projects_environment_presence_never_values(self) -> None:
        secret_name = "AVP_PACKET_PATH_TEST_SECRET"
        secret_value = "must-not-be-serialized"
        stdin = io.StringIO(json.dumps({"environmentKeys": [secret_name]}) + "\n")
        stdout = io.StringIO()
        fake_status = {
            "NoNewPrivs": "1",
            "CapInh": "0000000000000000",
            "CapPrm": "0000000000000000",
            "CapEff": "0000000000000000",
            "CapBnd": "0000000000000000",
            "CapAmb": "0000000000000000",
        }

        with patch.dict(os.environ, {secret_name: secret_value}, clear=False):
            with patch.object(worker, "_process_status", return_value=fake_status):
                with patch.object(worker, "_net_namespace_identity", return_value="net:[123]"):
                    self.assertEqual(worker._security_probe_worker(stdin, stdout), 0)

        rendered = stdout.getvalue()
        result = json.loads(rendered)
        self.assertTrue(result["environmentPresence"][secret_name])
        self.assertNotIn(secret_value, rendered)
        self.assertEqual(result["noNewPrivs"], 1)
        self.assertEqual(result["capabilities"]["effective"], "0000000000000000")

    def test_security_probe_rejects_duplicate_environment_keys(self) -> None:
        stdin = io.StringIO(json.dumps({"environmentKeys": ["A", "A"]}) + "\n")

        with self.assertRaises(EvidenceMaterializationError):
            worker._security_probe_worker(stdin, io.StringIO())


class PacketPathWorkerBoundaryTests(unittest.TestCase):
    def test_worker_has_no_toxiproxy_or_control_plane_dependency(self) -> None:
        source = open(worker.__file__, "r", encoding="utf-8").read()

        self.assertNotIn("toxiproxy", source.lower())
        self.assertNotIn("PacketPathController", source)
        self.assertNotIn("nft ", source)
        self.assertNotIn("SATISFIED", source)
        self.assertNotIn("SEMANTIC_VIOLATION", source)

    def test_witness_roles_are_closed_to_subject_and_privileged_probe(self) -> None:
        self.assertEqual(worker._ALLOWED_WITNESS_ROLES, {"subject", "privileged-probe"})

    def test_environment_key_shape_is_bounded(self) -> None:
        self.assertEqual(worker._environment_keys(["VISIBLE", "OTHER"]), ("VISIBLE", "OTHER"))
        with self.assertRaises(EvidenceMaterializationError):
            worker._environment_keys(["A=B"])
        with self.assertRaises(EvidenceMaterializationError):
            worker._environment_keys(["X"] * 65)


def _attempt() -> AttemptMaterial:
    challenge = b"worker-challenge"
    request = b"REQ" + challenge
    response = b"RESP" + challenge
    return AttemptMaterial(
        run_id="worker-run",
        phase_id="subject-active-cut",
        ordinal=0,
        path_id="selected-path",
        attempt_id="b" * 64,
        challenge=challenge,
        challenge_sha256=hashlib.sha256(challenge).hexdigest(),
        request_bytes=request,
        expected_response_bytes=response,
        request_sha256=hashlib.sha256(request).hexdigest(),
        response_sha256=hashlib.sha256(response).hexdigest(),
    )


if __name__ == "__main__":
    unittest.main()

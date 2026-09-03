"""Unit tests for TEL-002 container-role worker serialization boundaries."""

from __future__ import annotations

import io
import json
import unittest

from acceptance.network_control.evidence_core import (
    AttemptFactory,
    EvidencePlan,
    ExchangeProgram,
    MaterializedEndpoint,
)
from acceptance.network_control.toxiproxy_worker import (
    _attempt_document,
    _attempt_from_document,
    _endpoint_document,
    _endpoint_from_document,
    _inventory_worker,
)

_BASELINE = "883956784e57152537b11aaf65143209fc131429"


def endpoint(address: str, port: int, role: str) -> MaterializedEndpoint:
    return MaterializedEndpoint(family="ipv4", address=address, port=port, role=role)


def plan() -> EvidencePlan:
    return EvidencePlan(
        design_revision="TEL-002-worker-v0.1",
        semantic_baseline_commit=_BASELINE,
        semantic_baseline_path="rfcs/AEP-0012-network-control-resource-profile.md",
        run_id="worker-run",
        path_id="selected-path",
        subject_destination=endpoint("127.0.0.1", 41001, "subject-destination"),
        upstream_fixture=endpoint("127.0.0.1", 42001, "upstream-fixture"),
        exchange_program=ExchangeProgram(
            program_id="worker-exchange-v0.1",
            request_prefix=b"REQ\x00",
            request_suffix=b"\x00END",
            response_prefix=b"RESP\x00",
            response_suffix=b"\x00END",
        ),
        observation_budget_ns=1_000_000_000,
    )


class SerializationTests(unittest.TestCase):
    def test_attempt_material_round_trips_exact_bytes_and_identity(self) -> None:
        attempt = AttemptFactory(b"W" * 32).issue(plan(), phase_id="baseline", ordinal=1)
        rebuilt = _attempt_from_document(_attempt_document(attempt))
        self.assertEqual(rebuilt, attempt)

    def test_endpoint_round_trips_literal_identity(self) -> None:
        value = endpoint("127.0.0.1", 41001, "subject-destination")
        self.assertEqual(_endpoint_from_document(_endpoint_document(value)), value)

    def test_attempt_document_is_json_serializable_without_raw_binary_values(self) -> None:
        attempt = AttemptFactory(b"X" * 32).issue(plan(), phase_id="baseline", ordinal=1)
        payload = json.dumps(_attempt_document(attempt), sort_keys=True).encode("utf-8")
        self.assertNotIn(attempt.challenge, payload)
        self.assertNotIn(attempt.request_bytes, payload)


class InventoryTests(unittest.TestCase):
    def test_inventory_worker_emits_one_json_document(self) -> None:
        output = io.StringIO()
        self.assertEqual(_inventory_worker(output), 0)
        document = json.loads(output.getvalue())
        self.assertIsInstance(document["interfaces"], list)
        self.assertTrue(any(item["loopback"] for item in document["interfaces"]))


if __name__ == "__main__":
    unittest.main()

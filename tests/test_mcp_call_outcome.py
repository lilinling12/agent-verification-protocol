from __future__ import annotations

import unittest

from avp_ref.canonical import digest
from avp_ref.mcp import (
    MCPCallOutcome,
    MCPCallRecord,
    MCPGatewayPolicy,
    MCPUpstreamError,
    MCPVerificationGateway,
)


class _OutcomeTransport:
    def __init__(self) -> None:
        self.mode = MCPCallOutcome.SUCCESS

    def request(self, method, params=None, *, name=None, extra_headers=None):
        if method == "server/discover":
            return {
                "supportedVersions": ["2026-07-28"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "outcome-fixture", "version": "1"},
            }
        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "order.get",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"order_id": {"type": "string"}},
                            "required": ["order_id"],
                        },
                        "outputSchema": {
                            "type": "object",
                            "properties": {"ok": {"type": "boolean"}},
                            "required": ["ok"],
                        },
                    }
                ],
                "ttlMs": 0,
                "cacheScope": "private",
            }
        if method == "tools/call":
            if self.mode is MCPCallOutcome.UPSTREAM_ERROR:
                raise MCPUpstreamError(-32001, "fixture upstream failure")
            if self.mode is MCPCallOutcome.TOOL_ERROR:
                return {
                    "resultType": "complete",
                    "isError": True,
                    "content": [{"type": "text", "text": "order not found"}],
                }
            return {
                "resultType": "complete",
                "isError": False,
                "structuredContent": {"ok": True},
            }
        raise AssertionError(method)


class MCPCallRecordInvariantTest(unittest.TestCase):
    @staticmethod
    def _record(outcome: MCPCallOutcome, result_digest: str | None) -> MCPCallRecord:
        return MCPCallRecord(
            correlation_id="call_1",
            tool_name="order.get",
            arguments_digest="sha256:" + "1" * 64,
            result_digest=result_digest,
            schema_digest="sha256:" + "2" * 64,
            catalog_digest="sha256:" + "3" * 64,
            outcome=outcome,
        )

    def test_result_outcomes_require_result_identity(self) -> None:
        for outcome in (MCPCallOutcome.SUCCESS, MCPCallOutcome.TOOL_ERROR):
            with self.subTest(outcome=outcome):
                with self.assertRaises(ValueError):
                    self._record(outcome, None)

    def test_upstream_error_forbids_result_identity(self) -> None:
        with self.assertRaises(ValueError):
            self._record(MCPCallOutcome.UPSTREAM_ERROR, "sha256:" + "4" * 64)

    def test_valid_outcomes_serialize_explicitly(self) -> None:
        success = self._record(MCPCallOutcome.SUCCESS, "sha256:" + "4" * 64)
        tool_error = self._record(MCPCallOutcome.TOOL_ERROR, "sha256:" + "5" * 64)
        upstream = self._record(MCPCallOutcome.UPSTREAM_ERROR, None)
        self.assertEqual("success", success.to_dict()["outcome"])
        self.assertEqual("tool_error", tool_error.to_dict()["outcome"])
        self.assertEqual("upstream_error", upstream.to_dict()["outcome"])


class MCPGatewayOutcomeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.transport = _OutcomeTransport()
        self.gateway = MCPVerificationGateway(
            self.transport,
            MCPGatewayPolicy(frozenset({"order.get"})),
            endpoint_identity="https://mcp.outcome.invalid/mcp",
        )
        self.gateway.open()

    def test_tool_error_is_returned_and_recorded_without_success_schema_coercion(self) -> None:
        self.transport.mode = MCPCallOutcome.TOOL_ERROR
        result = self.gateway.call_tool("order.get", {"order_id": "missing"})
        record = self.gateway.call_records[-1]

        self.assertTrue(result["isError"])
        self.assertNotIn("structuredContent", result)
        self.assertIs(record.outcome, MCPCallOutcome.TOOL_ERROR)
        self.assertEqual(digest(result), record.result_digest)

    def test_success_and_upstream_failure_remain_distinct(self) -> None:
        result = self.gateway.call_tool("order.get", {"order_id": "ord_1"})
        self.assertIs(self.gateway.call_records[-1].outcome, MCPCallOutcome.SUCCESS)
        self.assertEqual(digest(result), self.gateway.call_records[-1].result_digest)

        self.transport.mode = MCPCallOutcome.UPSTREAM_ERROR
        with self.assertRaises(MCPUpstreamError):
            self.gateway.call_tool("order.get", {"order_id": "ord_2"})
        record = self.gateway.call_records[-1]
        self.assertIs(record.outcome, MCPCallOutcome.UPSTREAM_ERROR)
        self.assertIsNone(record.result_digest)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from avp_ref.mcp import (
    HTTPMCPTransport,
    MCPGatewayPolicy,
    MCPPermissionDenied,
    MCPProtocolError,
    MCPSchemaDriftError,
    MCPVerificationGateway,
)
from avp_ref.reference import (
    reference_agent_system,
    reference_environment,
    reference_oracle_package,
    reference_scenario,
)
from avp_ref.runtime import ReferenceRuntime
from avp_ref.subject import InProcessSubjectAdapter
from avp_ref.telemetry import OpenTelemetryBridge


class FakeTransport:
    def __init__(self):
        self.schema_version = 1
        self.ttl_ms = 1000
        self.calls = []

    def request(self, method, params=None, *, name=None, extra_headers=None):
        self.calls.append((method, dict(params or {}), name, dict(extra_headers or {})))
        if method == "server/discover":
            return {
                "supportedVersions": ["2026-07-28"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "fake", "version": "1.0"},
            }
        if method == "tools/list":
            if (params or {}).get("cursor") is None:
                return {
                    "tools": [
                        {
                            "name": "order.get",
                            "title": "Get order",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "order_id": {"type": "string", "x-mcp-header": "Order-Id"}
                                },
                                "required": ["order_id"],
                                "x-version": self.schema_version,
                            },
                            "outputSchema": {
                                "type": "object",
                                "properties": {"ok": {"type": "boolean"}},
                                "required": ["ok"],
                            },
                        }
                    ],
                    "nextCursor": "p2",
                    "ttlMs": self.ttl_ms,
                    "cacheScope": "private",
                }
            return {
                "tools": [
                    {
                        "name": "refund.create",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"order_id": {"type": "string"}},
                            "required": ["order_id"],
                        },
                    }
                ],
                "ttlMs": self.ttl_ms,
                "cacheScope": "private",
            }
        if method == "tools/call":
            return {"resultType": "complete", "structuredContent": {"ok": True}, "isError": False}
        raise AssertionError(method)


class MCPGatewayTest(unittest.TestCase):
    def make_gateway(self, transport=None):
        return MCPVerificationGateway(
            transport or FakeTransport(),
            MCPGatewayPolicy(frozenset({"order.get", "refund.create"})),
            endpoint_identity="http://mcp.test/mcp",
        )

    def test_open_discovers_paginated_catalog(self):
        description = self.make_gateway().open()
        self.assertEqual("2026-07-28", description.protocol_version)
        self.assertTrue(description.baseline_catalog_digest.startswith("sha256:"))

    def test_permission_fail_closed(self):
        gateway = self.make_gateway()
        gateway.open()
        with self.assertRaises(MCPPermissionDenied):
            gateway.call_tool("customer.delete", {})

    def test_schema_drift_before_side_effect(self):
        transport = FakeTransport()
        gateway = self.make_gateway(transport)
        gateway.open()
        transport.schema_version = 2
        with self.assertRaises(MCPSchemaDriftError):
            gateway.call_tool("order.get", {"order_id": "ord_1"})
        self.assertFalse(any(call[0] == "tools/call" for call in transport.calls))

    def test_cache_metadata_change_is_not_schema_drift(self):
        transport = FakeTransport()
        gateway = self.make_gateway(transport)
        baseline = gateway.open().baseline_catalog_digest
        transport.ttl_ms = 250
        result = gateway.call_tool("order.get", {"order_id": "ord_1"})
        self.assertTrue(result["structuredContent"]["ok"])
        self.assertEqual(baseline, gateway.call_records[-1].catalog_digest)

    def test_call_validates_schema_and_mirrors_header(self):
        transport = FakeTransport()
        gateway = self.make_gateway(transport)
        gateway.open()
        gateway.call_tool(
            "order.get",
            {"order_id": "ord_1"},
            correlation_id="call_7",
            trace_headers={"traceparent": "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"},
        )
        call = [item for item in transport.calls if item[0] == "tools/call"][0]
        self.assertEqual("ord_1", call[3]["Mcp-Param-Order-Id"])
        self.assertIn("traceparent", call[3])
        self.assertEqual("call_7", gateway.call_records[-1].correlation_id)
        with self.assertRaises(MCPProtocolError):
            gateway.call_tool("order.get", {})

    def test_runtime_routes_mcp_and_emits_digests_and_trace_context(self):
        def subject(session, task):
            session.call_tool("order.get", {"order_id": "ord_1"})
            return "done"

        transport = FakeTransport()
        gateway = MCPVerificationGateway(
            transport,
            MCPGatewayPolicy(frozenset({"order.get"})),
            endpoint_identity="x",
        )
        runtime = ReferenceRuntime(OpenTelemetryBridge())
        episode = runtime.create_episode(
            scenario=reference_scenario(),
            agent_system=reference_agent_system("mcp-probe"),
            environment_adapter=reference_environment(),
            subject_adapter=InProcessSubjectAdapter(subject),
            oracle_package=reference_oracle_package(),
            mcp_gateway=gateway,
        )
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        events = [
            event
            for event in episode.events
            if event.event_type == "tool.result" and event.payload.get("protocol") == "mcp"
        ]
        self.assertEqual(1, len(events))
        self.assertTrue(events[0].payload["schema_digest"].startswith("sha256:"))
        call = [item for item in transport.calls if item[0] == "tools/call"][0]
        self.assertIn("traceparent", call[3])


class HTTPMCPTransportTest(unittest.TestCase):
    def setUp(self):
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length))
                outer.requests.append(({key.lower(): value for key, value in self.headers.items()}, payload))
                method = payload["method"]
                if method == "server/discover":
                    result = {
                        "supportedVersions": ["2026-07-28"],
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "local", "version": "1"},
                    }
                elif method == "tools/list":
                    result = {
                        "tools": [
                            {
                                "name": "order.get",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "order_id": {"type": "string", "x-mcp-header": "Order-Id"}
                                    },
                                    "required": ["order_id"],
                                },
                            }
                        ],
                        "ttlMs": 0,
                        "cacheScope": "private",
                    }
                else:
                    result = {"resultType": "complete", "structuredContent": {"ok": True}}
                body = json.dumps({"jsonrpc": "2.0", "id": payload["id"], "result": result}).encode()
                content_type = "application/json"
                if method == "tools/list":
                    body = b"event: message\ndata: " + body + b"\n\n"
                    content_type = "text/event-stream"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.endpoint = f"http://127.0.0.1:{self.server.server_address[1]}/mcp"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_json_sse_headers_and_meta(self):
        gateway = MCPVerificationGateway(
            HTTPMCPTransport(self.endpoint, timeout_seconds=2),
            MCPGatewayPolicy(frozenset({"order.get"})),
            endpoint_identity=self.endpoint,
        )
        gateway.open()
        gateway.call_tool(
            "order.get",
            {"order_id": "ord_1"},
            trace_headers={"traceparent": "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"},
        )
        for headers, payload in self.requests:
            self.assertEqual("2026-07-28", headers["mcp-protocol-version"])
            self.assertEqual(payload["method"], headers["mcp-method"])
        call_headers = [headers for headers, payload in self.requests if payload["method"] == "tools/call"][0]
        self.assertEqual("order.get", call_headers["mcp-name"])
        self.assertEqual("ord_1", call_headers["mcp-param-order-id"])
        self.assertIn("traceparent", call_headers)


if __name__ == "__main__":
    unittest.main()

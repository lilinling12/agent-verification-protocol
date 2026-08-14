from __future__ import annotations

import unittest

from avp_ref.mcp import (
    MCPGatewayPolicy,
    MCPPermissionDenied,
    MCPVerificationGateway,
)
from avp_ref.mcp.transport import encode_mcp_header_value


class HeaderTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict, str | None, dict[str, str]]] = []

    def request(self, method, params=None, *, name=None, extra_headers=None):
        self.calls.append(
            (method, dict(params or {}), name, dict(extra_headers or {}))
        )
        if method == "server/discover":
            return {
                "supportedVersions": ["2026-07-28"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "header-test", "version": "1"},
            }
        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "header.echo",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "unicode": {
                                    "type": "string",
                                    "x-mcp-header": "Unicode",
                                },
                                "padded": {
                                    "type": "string",
                                    "x-mcp-header": "Padded",
                                },
                                "sentinel": {
                                    "type": "string",
                                    "x-mcp-header": "Sentinel",
                                },
                                "count": {
                                    "type": "integer",
                                    "x-mcp-header": "Count",
                                },
                                "enabled": {
                                    "type": "boolean",
                                    "x-mcp-header": "Enabled",
                                },
                            },
                            "required": [
                                "unicode",
                                "padded",
                                "sentinel",
                                "count",
                                "enabled",
                            ],
                        },
                    }
                ],
                "ttlMs": 0,
                "cacheScope": "private",
            }
        if method == "tools/call":
            return {"resultType": "complete", "content": []}
        raise AssertionError(method)


class InvalidHeaderLocationTransport(HeaderTransport):
    def __init__(self, input_schema: dict) -> None:
        super().__init__()
        self.input_schema = input_schema

    def request(self, method, params=None, *, name=None, extra_headers=None):
        if method != "tools/list":
            return super().request(
                method,
                params,
                name=name,
                extra_headers=extra_headers,
            )
        self.calls.append(
            (method, dict(params or {}), name, dict(extra_headers or {}))
        )
        return {
            "tools": [
                {
                    "name": "invalid.header",
                    "inputSchema": self.input_schema,
                }
            ],
            "ttlMs": 0,
            "cacheScope": "private",
        }


class MCPHeaderEncodingTest(unittest.TestCase):
    def test_header_encoding_matches_mcp_examples(self):
        self.assertEqual("us-west1", encode_mcp_header_value("us-west1"))
        self.assertEqual(
            "=?base64?SGVsbG8sIOS4lueVjA==?=",
            encode_mcp_header_value("Hello, 世界"),
        )
        self.assertEqual(
            "=?base64?IHBhZGRlZCA=?=",
            encode_mcp_header_value(" padded "),
        )
        self.assertEqual(
            "=?base64?bGluZTEKbGluZTI=?=",
            encode_mcp_header_value("line1\nline2"),
        )
        self.assertEqual(
            "=?base64?PT9iYXNlNjQ/bGl0ZXJhbD89?=",
            encode_mcp_header_value("=?base64?literal?="),
        )

    def test_gateway_encodes_mirrored_tool_parameter_headers(self):
        transport = HeaderTransport()
        gateway = MCPVerificationGateway(
            transport,
            MCPGatewayPolicy(frozenset({"header.echo"})),
            endpoint_identity="https://mcp.example.test/mcp",
        )
        gateway.open()
        gateway.call_tool(
            "header.echo",
            {
                "unicode": "Hello, 世界",
                "padded": " padded ",
                "sentinel": "=?base64?literal?=",
                "count": -7,
                "enabled": True,
            },
        )

        call = next(item for item in transport.calls if item[0] == "tools/call")
        headers = call[3]
        self.assertEqual(
            "=?base64?SGVsbG8sIOS4lueVjA==?=",
            headers["Mcp-Param-Unicode"],
        )
        self.assertEqual(
            "=?base64?IHBhZGRlZCA=?=",
            headers["Mcp-Param-Padded"],
        )
        self.assertEqual(
            "=?base64?PT9iYXNlNjQ/bGl0ZXJhbD89?=",
            headers["Mcp-Param-Sentinel"],
        )
        self.assertEqual("-7", headers["Mcp-Param-Count"])
        self.assertEqual("true", headers["Mcp-Param-Enabled"])

    def test_unreachable_header_annotations_exclude_tool_definition(self):
        invalid_schemas = (
            {
                "type": "object",
                "properties": {
                    "values": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "x-mcp-header": "ArrayValue",
                        },
                    }
                },
            },
            {
                "type": "object",
                "properties": {
                    "value": {
                        "oneOf": [
                            {
                                "type": "string",
                                "x-mcp-header": "VariantValue",
                            },
                            {"type": "integer"},
                        ]
                    }
                },
            },
            {
                "type": "object",
                "$defs": {
                    "hidden": {
                        "type": "string",
                        "x-mcp-header": "DefinitionValue",
                    }
                },
                "properties": {"value": {"$ref": "#/$defs/hidden"}},
            },
        )

        for schema in invalid_schemas:
            with self.subTest(schema=schema):
                gateway = MCPVerificationGateway(
                    InvalidHeaderLocationTransport(schema),
                    MCPGatewayPolicy(frozenset({"invalid.header"})),
                    endpoint_identity="https://mcp.example.test/mcp",
                )
                with self.assertRaises(MCPPermissionDenied):
                    gateway.open()


if __name__ == "__main__":
    unittest.main()

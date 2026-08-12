"""MCP 2026-07-28 adapter primitives.

This module deliberately does not implement MCP RPC. It provides the AVP-side
capture/fingerprinting policy around an MCP gateway.
"""
from dataclasses import dataclass
from typing import Any
from ..canonical import digest

@dataclass(frozen=True)
class MCPCallIdentity:
    protocol_version: str
    server_id: str
    method: str
    name: str | None
    schema_digest: str | None = None

def fingerprint_tool(server_id: str, tool_definition: dict[str, Any]) -> str:
    return digest({"server_id": server_id, "tool": tool_definition})

def capture_headers(headers: dict[str, str]) -> dict[str, str | None]:
    lower = {k.lower(): v for k, v in headers.items()}
    return {
        "protocol_version": lower.get("mcp-protocol-version"),
        "method": lower.get("mcp-method"),
        "name": lower.get("mcp-name"),
    }

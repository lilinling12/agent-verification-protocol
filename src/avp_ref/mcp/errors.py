"""Typed MCP gateway failures.

Transport, protocol, policy and schema-drift failures are intentionally distinct
because they imply different AVP validity and failure-intelligence outcomes.
"""


class MCPGatewayError(RuntimeError):
    """Base class for verification-gateway failures."""


class MCPTransportError(MCPGatewayError):
    """The upstream MCP endpoint could not be reached or returned invalid HTTP."""


class MCPProtocolError(MCPGatewayError):
    """The upstream response violated JSON-RPC or MCP protocol invariants."""


class MCPUpstreamError(MCPGatewayError):
    """The upstream MCP server returned a JSON-RPC error response."""

    def __init__(self, code: int, message: str, data=None) -> None:
        super().__init__(f"MCP upstream error {code}: {message}")
        self.code = code
        self.message = message
        self.data = data


class MCPPermissionDenied(MCPGatewayError):
    """The compiled AVS policy does not permit the requested MCP tool."""


class MCPSchemaDriftError(MCPGatewayError):
    """The live MCP tool catalog differs from the verified baseline catalog."""

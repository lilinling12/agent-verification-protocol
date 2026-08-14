"""MCP 2026-07-28 Streamable HTTP transport."""
from __future__ import annotations

import base64
import json
import socket
import urllib.error
import urllib.request
from typing import Any, Mapping, Protocol, runtime_checkable

from .errors import MCPProtocolError, MCPTransportError, MCPUpstreamError
from .models import MCP_PROTOCOL_VERSION

_BASE64_SENTINEL_PREFIX = "=?base64?"
_BASE64_SENTINEL_SUFFIX = "?="


def encode_mcp_header_value(value: str) -> str:
    """Encode an MCP mirrored HTTP header value per the 2026-07-28 binding.

    Plain values are allowed only when every character is an HTTP field-value
    character accepted by MCP and there is no leading/trailing SP/HTAB. Values
    that are unsafe, non-ASCII, or syntactically ambiguous with MCP's Base64
    sentinel are encoded from their UTF-8 representation.
    """

    if not isinstance(value, str):
        raise TypeError("MCP header value must be a string")

    matches_sentinel = (
        value.startswith(_BASE64_SENTINEL_PREFIX)
        and value.endswith(_BASE64_SENTINEL_SUFFIX)
    )
    has_edge_whitespace = bool(value) and value[0] in {" ", "\t"} or bool(value) and value[-1] in {" ", "\t"}
    plain_safe = all(character == "\t" or 0x20 <= ord(character) <= 0x7E for character in value)

    if plain_safe and not has_edge_whitespace and not matches_sentinel:
        return value

    encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
    return f"{_BASE64_SENTINEL_PREFIX}{encoded}{_BASE64_SENTINEL_SUFFIX}"


@runtime_checkable
class MCPTransport(Protocol):
    def request(
        self,
        method: str,
        params: Mapping[str, Any] | None = None,
        *,
        name: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]: ...


class HTTPMCPTransport:
    def __init__(
        self,
        endpoint: str,
        *,
        timeout_seconds: float = 10.0,
        client_name: str = "avp-reference",
        client_version: str = "0.2.0-alpha.5",
        trace_headers_provider=None,
    ):
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("MCP endpoint must use http or https")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        self.endpoint = endpoint
        self.timeout_seconds = float(timeout_seconds)
        self.client_name = client_name
        self.client_version = client_version
        self._request_id = 0
        self._trace_headers_provider = trace_headers_provider

    def request(self, method, params=None, *, name=None, extra_headers=None):
        self._request_id += 1
        request_id = f"avp-mcp-{self._request_id}"
        merged = dict(params or {})
        meta = dict(merged.get("_meta") or {})
        meta.setdefault("io.modelcontextprotocol/protocolVersion", MCP_PROTOCOL_VERSION)
        meta.setdefault(
            "io.modelcontextprotocol/clientInfo",
            {"name": self.client_name, "version": self.client_version},
        )
        meta.setdefault("io.modelcontextprotocol/clientCapabilities", {})
        merged["_meta"] = meta
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": merged,
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
            "Mcp-Method": method,
        }
        if name is not None:
            headers["Mcp-Name"] = encode_mcp_header_value(str(name))
        if self._trace_headers_provider is not None:
            for key, value in self._trace_headers_provider().items():
                if key.lower() not in {item.lower() for item in headers}:
                    headers[str(key)] = str(value)
        for key, value in (extra_headers or {}).items():
            if key.lower() in {item.lower() for item in headers}:
                raise MCPProtocolError(
                    f"extra MCP header collides with reserved header: {key}"
                )
            headers[str(key)] = str(value)
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, separators=(",", ":")).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                content_type = response.headers.get_content_type()
                body = response.read()
        except urllib.error.HTTPError as exc:
            raise MCPTransportError(
                f"MCP HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')[:512]}"
            ) from exc
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            raise MCPTransportError(f"MCP transport failure: {exc}") from exc

        decoded = (
            self._decode_json(body)
            if content_type == "application/json"
            else self._decode_sse(body, request_id)
            if content_type == "text/event-stream"
            else None
        )
        if decoded is None:
            raise MCPTransportError(
                f"unsupported MCP response content type: {content_type}"
            )
        return self._validate_response(decoded, request_id)

    @staticmethod
    def _decode_json(body):
        try:
            return json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MCPProtocolError("MCP response is not valid UTF-8 JSON") from exc

    def _decode_sse(self, body, request_id):
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MCPProtocolError("MCP SSE response is not valid UTF-8") from exc
        data = []
        candidates = []
        for line in text.splitlines() + [""]:
            if line == "":
                if data:
                    try:
                        value = json.loads("\n".join(data))
                    except json.JSONDecodeError as exc:
                        raise MCPProtocolError(
                            "MCP SSE data event is not valid JSON"
                        ) from exc
                    data = []
                    if isinstance(value, dict):
                        candidates.append(value)
            elif line.startswith("data:"):
                data.append(line[5:].lstrip())
        for candidate in candidates:
            if (
                candidate.get("jsonrpc") == "2.0"
                and candidate.get("id") == request_id
            ):
                return candidate
        raise MCPProtocolError(
            "MCP SSE stream ended without matching JSON-RPC response"
        )

    @staticmethod
    def _validate_response(decoded, request_id):
        if (
            not isinstance(decoded, dict)
            or decoded.get("jsonrpc") != "2.0"
            or decoded.get("id") != request_id
        ):
            raise MCPProtocolError(
                "MCP JSON-RPC response envelope does not match request"
            )
        if "error" in decoded:
            error = decoded["error"]
            if (
                not isinstance(error, dict)
                or not isinstance(error.get("code"), int)
                or not isinstance(error.get("message"), str)
            ):
                raise MCPProtocolError("MCP JSON-RPC error object is malformed")
            raise MCPUpstreamError(
                error["code"], error["message"], error.get("data")
            )
        result = decoded.get("result")
        if not isinstance(result, dict):
            raise MCPProtocolError("MCP JSON-RPC result must be an object")
        return result

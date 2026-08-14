"""Verification gateway in front of a real MCP server."""
from __future__ import annotations

import re
import uuid
from collections.abc import Mapping
from typing import Any

from jsonschema import Draft202012Validator, SchemaError, ValidationError

from avp_ref.canonical import digest
from avp_ref.scenario.models import ScenarioInstance

from .errors import (
    MCPPermissionDenied,
    MCPProtocolError,
    MCPSchemaDriftError,
    MCPUpstreamError,
)
from .models import (
    MCP_PROTOCOL_VERSION,
    MCPCallOutcome,
    MCPCallRecord,
    MCPGatewayDescription,
    MCPGatewayPolicy,
    MCPServerDescription,
    MCPToolCatalog,
    MCPToolDescriptor,
)
from .transport import MCPTransport, encode_mcp_header_value

_GATEWAY_VERSION = "0.2.0-alpha.5"
_MAX_SAFE_INTEGER = 9007199254740991
_TOKEN = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


class MCPVerificationGateway:
    def __init__(
        self,
        transport: MCPTransport,
        policy: MCPGatewayPolicy,
        *,
        endpoint_identity: str,
    ):
        if not endpoint_identity:
            raise ValueError("endpoint_identity must be non-empty")
        self._transport = transport
        self._policy = policy
        self._endpoint_identity = endpoint_identity
        self._server = None
        self._catalog = None
        self._records = []

    @classmethod
    def policy_from_scenario(cls, scenario: ScenarioInstance, actor_id="subject"):
        caps = scenario.document.get("capabilities", {})
        actor = caps.get(actor_id, {}) if hasattr(caps, "get") else {}
        includes = actor.get("include", ()) if hasattr(actor, "get") else ()
        return MCPGatewayPolicy(
            frozenset(
                str(item).rsplit("/", 1)[-1]
                for item in includes
                if str(item).startswith("mcp://") and "/" in str(item)
            )
        )

    @property
    def configuration_digest(self):
        return digest(
            {
                "gateway": "avp-mcp-verification-gateway",
                "version": _GATEWAY_VERSION,
                "protocol": MCP_PROTOCOL_VERSION,
                "endpoint": digest(self._endpoint_identity),
                "policy": {
                    "allowed_tools": sorted(self._policy.allowed_tools),
                    "detect_schema_drift": self._policy.detect_schema_drift,
                    "max_catalog_tools": self._policy.max_catalog_tools,
                    "max_catalog_pages": self._policy.max_catalog_pages,
                    "max_schema_depth": self._policy.max_schema_depth,
                },
            }
        )

    def open(self):
        server = self._discover()
        if MCP_PROTOCOL_VERSION not in server.supported_versions:
            raise MCPProtocolError(
                f"upstream does not support MCP {MCP_PROTOCOL_VERSION}"
            )
        if "tools" not in server.capabilities:
            raise MCPProtocolError(
                "upstream MCP server does not advertise tools capability"
            )
        catalog = self._list_tools()
        missing = self._policy.allowed_tools - set(catalog.by_name())
        if missing:
            raise MCPPermissionDenied(
                f"allowed AVS tools missing from MCP catalog: {sorted(missing)}"
            )
        self._server = server
        self._catalog = catalog
        return self.describe()

    def describe(self):
        if self._server is None or self._catalog is None:
            raise MCPProtocolError("MCP gateway is not open")
        return MCPGatewayDescription(
            "avp-mcp-verification-gateway",
            _GATEWAY_VERSION,
            MCP_PROTOCOL_VERSION,
            digest(self._endpoint_identity),
            self._server.identity_digest,
            self._catalog.catalog_digest,
            tuple(sorted(self._policy.allowed_tools)),
        )

    @property
    def call_records(self):
        return tuple(self._records)

    def owns_tool(self, name):
        return name in self._policy.allowed_tools

    def call_tool(
        self,
        name,
        arguments,
        *,
        correlation_id=None,
        trace_headers=None,
    ):
        if self._catalog is None:
            raise MCPProtocolError("MCP gateway is not open")
        if name not in self._policy.allowed_tools:
            raise MCPPermissionDenied(
                f"MCP tool is not permitted by compiled AVS policy: {name}"
            )
        baseline = self._catalog.by_name().get(name)
        if baseline is None:
            raise MCPProtocolError(f"baseline MCP catalog has no tool: {name}")
        active = (
            self._list_tools()
            if self._policy.detect_schema_drift
            else self._catalog
        )
        current = active.by_name().get(name)
        if (
            current is None
            or current.schema_digest != baseline.schema_digest
            or active.catalog_digest != self._catalog.catalog_digest
        ):
            raise MCPSchemaDriftError(
                f"MCP tool catalog/schema drift detected before call: {name}"
            )

        args = dict(arguments)
        self._validate_instance(args, baseline.input_schema, "tool arguments")
        headers = self._extract_mcp_headers(baseline.input_schema, args)
        for key, value in (trace_headers or {}).items():
            if key.lower() in {item.lower() for item in headers}:
                raise MCPProtocolError(
                    f"trace header collides with MCP parameter header: {key}"
                )
            headers[str(key)] = str(value)

        correlation = correlation_id or "mcp_" + uuid.uuid4().hex[:16]
        try:
            result = self._transport.request(
                "tools/call",
                {"name": name, "arguments": args},
                name=name,
                extra_headers=headers,
            )
        except MCPUpstreamError:
            self._records.append(
                MCPCallRecord(
                    correlation,
                    name,
                    digest(args),
                    None,
                    baseline.schema_digest,
                    self._catalog.catalog_digest,
                    MCPCallOutcome.UPSTREAM_ERROR,
                )
            )
            raise

        normalized = self._normalize_call_result(result)
        outcome = (
            MCPCallOutcome.TOOL_ERROR
            if normalized.get("isError") is True
            else MCPCallOutcome.SUCCESS
        )

        if outcome is MCPCallOutcome.SUCCESS and baseline.output_schema is not None:
            if "structuredContent" not in normalized:
                raise MCPProtocolError(
                    "tool declares outputSchema but successful response has no structuredContent"
                )
            self._validate_instance(
                normalized["structuredContent"],
                baseline.output_schema,
                "structuredContent",
            )

        self._records.append(
            MCPCallRecord(
                correlation,
                name,
                digest(args),
                digest(normalized),
                baseline.schema_digest,
                self._catalog.catalog_digest,
                outcome,
            )
        )
        return normalized

    def refresh_catalog(self):
        if self._catalog is None:
            raise MCPProtocolError("MCP gateway is not open")
        catalog = self._list_tools()
        if catalog.catalog_digest != self._catalog.catalog_digest:
            raise MCPSchemaDriftError("MCP tool catalog drift detected")
        return catalog

    def _discover(self):
        result = self._transport.request("server/discover", {})
        versions = result.get("supportedVersions")
        capabilities = result.get("capabilities")
        info = result.get("serverInfo")
        if (
            not isinstance(versions, list)
            or not all(isinstance(item, str) for item in versions)
            or not isinstance(capabilities, dict)
            or not isinstance(info, dict)
            or not isinstance(info.get("name"), str)
            or not isinstance(info.get("version"), str)
        ):
            raise MCPProtocolError("invalid server/discover response")
        return MCPServerDescription(
            tuple(versions),
            info["name"],
            info["version"],
            capabilities,
        )

    def _list_tools(self):
        descriptors = []
        pages = []
        ttls = []
        scope = None
        cursor = None
        seen = set()
        for _ in range(self._policy.max_catalog_pages):
            result = self._transport.request(
                "tools/list", {"cursor": cursor} if cursor else {}
            )
            tools = result.get("tools")
            ttl = result.get("ttlMs")
            page_scope = result.get("cacheScope")
            if (
                not isinstance(tools, list)
                or not isinstance(ttl, int)
                or ttl < 0
                or page_scope not in {"public", "private"}
            ):
                raise MCPProtocolError(
                    "invalid MCP 2026-07-28 tools/list cache/catalog fields"
                )
            if scope is None:
                scope = page_scope
            elif scope != page_scope:
                raise MCPProtocolError(
                    "tools/list cacheScope changed across pages"
                )
            pages.append(digest(result))
            ttls.append(ttl)
            for raw in tools:
                tool = self._parse_tool(raw)
                if tool is not None:
                    descriptors.append(tool)
                if len(descriptors) > self._policy.max_catalog_tools:
                    raise MCPProtocolError("MCP catalog exceeds tool limit")
            next_cursor = result.get("nextCursor")
            if next_cursor is None:
                return MCPToolCatalog(
                    tuple(descriptors),
                    tuple(pages),
                    scope or "private",
                    min(ttls) if ttls else 0,
                )
            if (
                not isinstance(next_cursor, str)
                or not next_cursor
                or next_cursor in seen
            ):
                raise MCPProtocolError("invalid or looping tools/list cursor")
            seen.add(next_cursor)
            cursor = next_cursor
        raise MCPProtocolError("tools/list exceeded page limit")

    def _parse_tool(self, raw):
        if (
            not isinstance(raw, dict)
            or not isinstance(raw.get("name"), str)
            or not isinstance(raw.get("inputSchema"), dict)
        ):
            raise MCPProtocolError("malformed MCP tool descriptor")
        self._validate_schema(raw["inputSchema"])
        output_schema = raw.get("outputSchema")
        if output_schema is not None:
            self._validate_schema(output_schema)
        try:
            self._header_paths(raw["inputSchema"])
        except MCPProtocolError:
            return None
        return MCPToolDescriptor(
            raw["name"],
            raw.get("title"),
            raw.get("description"),
            tuple(raw.get("icons") or ()),
            raw["inputSchema"],
            output_schema,
            raw.get("annotations") or {},
        )

    def _validate_schema(self, schema):
        self._validate_schema_depth(schema)
        self._reject_external_refs(schema)
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise MCPProtocolError(
                f"invalid JSON Schema: {exc.message}"
            ) from exc

    def _validate_instance(self, value, schema, label):
        try:
            Draft202012Validator(schema).validate(value)
        except ValidationError as exc:
            raise MCPProtocolError(
                f"{label} does not conform to schema: {exc.message}"
            ) from exc

    def _validate_schema_depth(self, value, depth=0):
        if depth > self._policy.max_schema_depth:
            raise MCPProtocolError("MCP schema exceeds depth limit")
        if isinstance(value, Mapping):
            for item in value.values():
                self._validate_schema_depth(item, depth + 1)
        elif isinstance(value, (list, tuple)):
            for item in value:
                self._validate_schema_depth(item, depth + 1)

    def _reject_external_refs(self, value):
        if isinstance(value, Mapping):
            ref = value.get("$ref")
            if isinstance(ref, str) and not ref.startswith("#"):
                raise MCPProtocolError(
                    "external JSON Schema $ref is not allowed in MCP verification gateway"
                )
            for item in value.values():
                self._reject_external_refs(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                self._reject_external_refs(item)

    def _header_paths(self, schema, path=(), seen=None):
        root_call = seen is None
        seen = {} if seen is None else seen
        if root_call:
            self._reject_unreachable_header_annotations(schema)

        found = []
        properties = schema.get("properties") or {}
        if not isinstance(properties, Mapping):
            return found
        for key, prop in properties.items():
            if not isinstance(prop, Mapping):
                continue
            property_path = path + (key,)
            header = prop.get("x-mcp-header")
            if header is not None:
                if (
                    not isinstance(header, str)
                    or not header
                    or not _TOKEN.match(header)
                    or prop.get("type") not in {"string", "integer", "boolean"}
                    or header.lower() in seen
                ):
                    raise MCPProtocolError("invalid x-mcp-header annotation")
                seen[header.lower()] = property_path
                found.append((property_path, header, prop.get("type")))
            found.extend(self._header_paths(prop, property_path, seen))
        return found

    def _reject_unreachable_header_annotations(
        self,
        value,
        *,
        property_chain=True,
        annotation_allowed=False,
    ):
        if isinstance(value, Mapping):
            if "x-mcp-header" in value and not annotation_allowed:
                raise MCPProtocolError(
                    "x-mcp-header annotation is not statically reachable through properties"
                )

            properties = value.get("properties")
            if property_chain and isinstance(properties, Mapping):
                for prop in properties.values():
                    if isinstance(prop, Mapping):
                        self._reject_unreachable_header_annotations(
                            prop,
                            property_chain=True,
                            annotation_allowed=True,
                        )

            for key, item in value.items():
                if key in {"x-mcp-header", "properties"}:
                    continue
                self._reject_unreachable_header_annotations(
                    item,
                    property_chain=False,
                    annotation_allowed=False,
                )
        elif isinstance(value, (list, tuple)):
            for item in value:
                self._reject_unreachable_header_annotations(
                    item,
                    property_chain=False,
                    annotation_allowed=False,
                )

    def _extract_mcp_headers(self, schema, args):
        headers = {}
        for path, name, kind in self._header_paths(schema):
            value = args
            for part in path:
                if not isinstance(value, Mapping) or part not in value:
                    value = None
                    break
                value = value[part]
            if value is None:
                continue

            if kind == "integer":
                if isinstance(value, bool):
                    raise MCPProtocolError(
                        "x-mcp-header integer value is invalid"
                    )
                if isinstance(value, int):
                    integer_value = value
                elif isinstance(value, float) and value.is_integer():
                    integer_value = int(value)
                else:
                    raise MCPProtocolError(
                        "x-mcp-header integer value is invalid"
                    )
                if abs(integer_value) > _MAX_SAFE_INTEGER:
                    raise MCPProtocolError(
                        "x-mcp-header integer is outside safe range"
                    )
                serialized = str(integer_value)
            elif kind == "boolean":
                if not isinstance(value, bool):
                    raise MCPProtocolError(
                        "x-mcp-header boolean value is invalid"
                    )
                serialized = "true" if value else "false"
            elif kind == "string":
                if not isinstance(value, str):
                    raise MCPProtocolError(
                        "x-mcp-header string value is invalid"
                    )
                serialized = value
            else:
                raise MCPProtocolError("unsupported x-mcp-header primitive type")

            headers[f"Mcp-Param-{name}"] = encode_mcp_header_value(serialized)
        return headers

    @staticmethod
    def _normalize_call_result(result):
        result_type = result.get("resultType")
        if result_type == "input_required":
            raise MCPProtocolError(
                "MCP MRTR input_required is not supported by Alpha 2.5 gateway"
            )
        if result_type not in (None, "complete"):
            raise MCPProtocolError(
                f"unsupported MCP tools/call resultType: {result_type!r}"
            )
        if "isError" in result and not isinstance(result["isError"], bool):
            raise MCPProtocolError("MCP tools/call isError must be boolean")
        return dict(result)

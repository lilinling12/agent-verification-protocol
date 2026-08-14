"""Reference adapter for the AVP MCP interoperability v0.1 profile."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from avp_ref.canonical import digest
from avp_ref.mcp import (
    HTTPMCPTransport,
    MCPCallOutcome,
    MCPGatewayPolicy,
    MCPPermissionDenied,
    MCPProtocolError,
    MCPSchemaDriftError,
    MCPUpstreamError,
    MCPVerificationGateway,
)
from avp_ref.mcp.models import MCP_PROTOCOL_VERSION

from .models import TCKAdapterError, TCKCaseResult, TCKStatus


class _MCPFixtureTransport:
    """Deterministic in-process MCP endpoint used only by reference TCK cases."""

    def __init__(self) -> None:
        self.schema_version = 1
        self.ttl_ms = 1000
        self.upstream_failure = False
        self.tool_error = False
        self.input_required = False
        self.calls: list[tuple[str, dict[str, Any], str | None, dict[str, str]]] = []

    def request(self, method, params=None, *, name=None, extra_headers=None):
        self.calls.append(
            (
                method,
                dict(params or {}),
                name,
                dict(extra_headers or {}),
            )
        )
        if method == "server/discover":
            return {
                "supportedVersions": [MCP_PROTOCOL_VERSION],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "avp-tck-mcp", "version": "1"},
            }
        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "order.get",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "order_id": {"type": "string"},
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
                "ttlMs": self.ttl_ms,
                "cacheScope": "private",
            }
        if method == "tools/call":
            if self.upstream_failure:
                raise MCPUpstreamError(-32001, "fixture failure")
            if self.input_required:
                return {
                    "resultType": "input_required",
                    "inputRequests": {
                        "confirm": {
                            "type": "elicitation",
                            "message": "Continue?",
                            "schema": {"type": "boolean"},
                        }
                    },
                }
            if self.tool_error:
                return {
                    "resultType": "complete",
                    "isError": True,
                    "content": [
                        {"type": "text", "text": "order not found"},
                    ],
                }
            return {
                "resultType": "complete",
                "structuredContent": {"ok": True},
                "isError": False,
            }
        raise AssertionError(f"unexpected fixture MCP method: {method}")

    @property
    def tools_call_count(self) -> int:
        return sum(1 for method, *_ in self.calls if method == "tools/call")


class ReferenceMCPTCKAdapter:
    """Execute AVP-owned MCP verification mappings against the reference gateway."""

    _REVISION = "AVP-TCK-MCP-REVISION-001"
    _CAPABILITY_DENY = "AVP-TCK-MCP-CAPABILITY-DENY-001"
    _BASELINE = "AVP-TCK-MCP-BASELINE-IDENTITY-001"
    _DRIFT = "AVP-TCK-MCP-SCHEMA-DRIFT-001"
    _CALL = "AVP-TCK-MCP-CALL-BINDING-001"
    _TOOL_ERROR = "AVP-TCK-MCP-TOOL-ERROR-001"
    _UPSTREAM_FAILURE = "AVP-TCK-MCP-UPSTREAM-FAILURE-001"
    _FEATURE_HONESTY = "AVP-TCK-MCP-FEATURE-HONESTY-001"

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return frozenset(
            {
                self._REVISION,
                self._CAPABILITY_DENY,
                self._BASELINE,
                self._DRIFT,
                self._CALL,
                self._TOOL_ERROR,
                self._UPSTREAM_FAILURE,
                self._FEATURE_HONESTY,
            }
        )

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        evaluator = {
            self._REVISION: self._revision,
            self._CAPABILITY_DENY: self._capability_deny,
            self._BASELINE: self._baseline_identity,
            self._DRIFT: self._schema_drift,
            self._CALL: self._call_binding,
            self._TOOL_ERROR: self._tool_error,
            self._UPSTREAM_FAILURE: self._upstream_failure,
            self._FEATURE_HONESTY: self._feature_honesty,
        }.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(f"unsupported reference MCP TCK case: {case_id}")
        passed, detail = evaluator(vector)
        return TCKCaseResult(
            case_id,
            TCKStatus.PASS if passed else TCKStatus.FAIL,
            detail,
        )

    @staticmethod
    def _revision(vector: Mapping[str, Any]) -> tuple[bool, str]:
        selected = str(vector.get("selectedRevision", ""))
        conflict = ReferenceMCPTCKAdapter._mapping(
            vector.get("conflictingExtraHeader"),
            "conflictingExtraHeader",
        )
        transport = HTTPMCPTransport("http://127.0.0.1:1", timeout_seconds=0.1)
        try:
            transport.request(
                "tools/list",
                {},
                extra_headers={str(conflict["name"]): str(conflict["value"])},
            )
            collision_rejected = False
        except MCPProtocolError:
            collision_rejected = True

        passed = selected == MCP_PROTOCOL_VERSION and collision_rejected
        return passed, (
            "selected MCP revision is bound and AVP metadata cannot override reserved MCP headers"
            if passed
            else "MCP revision binding or reserved-metadata preservation failed"
        )

    @staticmethod
    def _capability_deny(vector: Mapping[str, Any]) -> tuple[bool, str]:
        allowed = frozenset(str(item) for item in vector.get("allowedTools", ()))
        attempted = str(vector.get("attemptedTool", ""))
        transport = _MCPFixtureTransport()
        gateway = ReferenceMCPTCKAdapter._gateway(transport, allowed)
        gateway.open()
        try:
            gateway.call_tool(attempted, {})
            denied = False
        except MCPPermissionDenied:
            denied = True
        passed = denied and transport.tools_call_count == 0 and not gateway.call_records
        return passed, (
            "unauthorized MCP tool is denied before upstream execution"
            if passed
            else "Scenario MCP capability binding failed closed incorrectly"
        )

    @staticmethod
    def _baseline_identity(vector: Mapping[str, Any]) -> tuple[bool, str]:
        transport = _MCPFixtureTransport()
        gateway = ReferenceMCPTCKAdapter._gateway(
            transport,
            frozenset({"order.get"}),
        )
        baseline = gateway.open().baseline_catalog_digest
        transport.ttl_ms = 250
        gateway.call_tool("order.get", {"order_id": "ord_1"})
        record = gateway.call_records[-1]
        passed = (
            baseline == record.catalog_digest
            and record.schema_digest.startswith("sha256:")
        )
        return passed, (
            "cache-only retrieval metadata does not change baseline tool-contract identity"
            if passed
            else "MCP baseline identity changed on non-contract retrieval metadata"
        )

    @staticmethod
    def _schema_drift(vector: Mapping[str, Any]) -> tuple[bool, str]:
        transport = _MCPFixtureTransport()
        gateway = ReferenceMCPTCKAdapter._gateway(
            transport,
            frozenset({"order.get"}),
        )
        gateway.open()
        transport.schema_version = int(vector.get("activeSchemaVersion", 2))
        before = transport.tools_call_count
        try:
            gateway.call_tool("order.get", {"order_id": "ord_1"})
            rejected = False
        except MCPSchemaDriftError:
            rejected = True
        passed = rejected and transport.tools_call_count == before
        return passed, (
            "material schema drift is rejected before upstream side effects"
            if passed
            else "MCP schema drift did not fail closed before tools/call"
        )

    @staticmethod
    def _call_binding(vector: Mapping[str, Any]) -> tuple[bool, str]:
        correlation = str(vector.get("correlationId", ""))
        tool = str(vector.get("tool", ""))
        arguments = ReferenceMCPTCKAdapter._mapping(
            vector.get("arguments", {}),
            "arguments",
        )
        transport = _MCPFixtureTransport()
        gateway = ReferenceMCPTCKAdapter._gateway(transport, frozenset({tool}))
        description = gateway.open()
        result = gateway.call_tool(
            tool,
            arguments,
            correlation_id=correlation,
        )
        record = gateway.call_records[-1]
        passed = (
            record.correlation_id == correlation
            and record.tool_name == tool
            and record.arguments_digest == digest(dict(arguments))
            and record.schema_digest.startswith("sha256:")
            and record.catalog_digest == description.baseline_catalog_digest
            and record.result_digest == digest(result)
            and record.outcome is MCPCallOutcome.SUCCESS
        )
        return passed, (
            "accepted MCP call binds correlation, arguments, contract, catalog, result identity, and success outcome"
            if passed
            else "accepted MCP verification call binding is incomplete"
        )

    @staticmethod
    def _tool_error(vector: Mapping[str, Any]) -> tuple[bool, str]:
        tool = str(vector.get("tool", ""))
        arguments = ReferenceMCPTCKAdapter._mapping(
            vector.get("arguments", {}),
            "arguments",
        )
        transport = _MCPFixtureTransport()
        transport.tool_error = True
        gateway = ReferenceMCPTCKAdapter._gateway(transport, frozenset({tool}))
        description = gateway.open()
        result = gateway.call_tool(tool, arguments, correlation_id="tool_error_1")
        record = gateway.call_records[-1]
        passed = (
            result.get("isError") is True
            and record.outcome is MCPCallOutcome.TOOL_ERROR
            and record.result_digest == digest(result)
            and record.arguments_digest == digest(dict(arguments))
            and record.catalog_digest == description.baseline_catalog_digest
        )
        return passed, (
            "MCP tool execution error is returned as an MCP result while remaining distinct from success"
            if passed
            else "MCP tool execution error was flattened into success or upstream failure"
        )

    @staticmethod
    def _upstream_failure(vector: Mapping[str, Any]) -> tuple[bool, str]:
        tool = str(vector.get("tool", ""))
        arguments = ReferenceMCPTCKAdapter._mapping(
            vector.get("arguments", {}),
            "arguments",
        )
        transport = _MCPFixtureTransport()
        transport.upstream_failure = True
        gateway = ReferenceMCPTCKAdapter._gateway(transport, frozenset({tool}))
        description = gateway.open()
        try:
            gateway.call_tool(tool, arguments, correlation_id="failure_1")
            failed = False
        except MCPUpstreamError:
            failed = True
        record = gateway.call_records[-1] if gateway.call_records else None
        passed = (
            failed
            and record is not None
            and record.result_digest is None
            and record.outcome is MCPCallOutcome.UPSTREAM_ERROR
            and record.arguments_digest == digest(dict(arguments))
            and record.catalog_digest == description.baseline_catalog_digest
        )
        return passed, (
            "upstream failure remains distinct from MCP result outcomes"
            if passed
            else "MCP upstream failure was not bound or separated correctly"
        )

    @staticmethod
    def _feature_honesty(vector: Mapping[str, Any]) -> tuple[bool, str]:
        tool = str(vector.get("tool", ""))
        transport = _MCPFixtureTransport()
        transport.input_required = True
        gateway = ReferenceMCPTCKAdapter._gateway(transport, frozenset({tool}))
        gateway.open()
        try:
            gateway.call_tool(tool, {"order_id": "ord_1"})
            rejected = False
        except MCPProtocolError:
            rejected = True
        passed = rejected and not gateway.call_records
        return passed, (
            "unsupported MRTR input_required fails closed without fabricated ordinary success"
            if passed
            else "unsupported MCP feature was flattened into accepted tool completion"
        )

    @staticmethod
    def _gateway(
        transport: _MCPFixtureTransport,
        allowed_tools: frozenset[str],
    ) -> MCPVerificationGateway:
        return MCPVerificationGateway(
            transport,
            MCPGatewayPolicy(allowed_tools),
            endpoint_identity="https://mcp.tck.invalid/mcp",
        )

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("MCP TCK case metadata.id is missing")
        return case_id

    @staticmethod
    def _vector(case: Mapping[str, Any], case_id: str) -> Mapping[str, Any]:
        vector = case.get("vector")
        if not isinstance(vector, Mapping):
            raise TCKAdapterError(f"{case_id} vector must be an object")
        return vector

    @staticmethod
    def _mapping(value: Any, name: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise TCKAdapterError(f"MCP TCK {name} must be an object")
        return value

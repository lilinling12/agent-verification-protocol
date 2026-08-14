"""Immutable MCP verification-gateway value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping

from avp_ref.canonical import digest

MCP_PROTOCOL_VERSION = "2026-07-28"


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class MCPGatewayPolicy:
    allowed_tools: frozenset[str]
    detect_schema_drift: bool = True
    max_catalog_tools: int = 512
    max_catalog_pages: int = 32
    max_schema_depth: int = 32

    def __post_init__(self) -> None:
        if min(
            self.max_catalog_tools,
            self.max_catalog_pages,
            self.max_schema_depth,
        ) < 1:
            raise ValueError("MCP policy limits must be >= 1")
        object.__setattr__(
            self,
            "allowed_tools",
            frozenset(str(item) for item in self.allowed_tools),
        )


@dataclass(frozen=True, slots=True)
class MCPServerDescription:
    supported_versions: tuple[str, ...]
    server_name: str
    server_version: str
    capabilities: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.server_name or not self.server_version:
            raise ValueError("MCP server identity must be non-empty")
        object.__setattr__(self, "capabilities", _freeze(self.capabilities))

    def to_dict(self) -> dict[str, Any]:
        return {
            "supported_versions": list(self.supported_versions),
            "server_name": self.server_name,
            "server_version": self.server_version,
            "capabilities": _thaw(self.capabilities),
        }

    @property
    def identity_digest(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class MCPToolDescriptor:
    name: str
    title: str | None
    description: str | None
    icons: tuple[Mapping[str, Any], ...]
    input_schema: Mapping[str, Any]
    output_schema: Any | None = None
    annotations: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("MCP tool name must be non-empty")
        object.__setattr__(self, "icons", tuple(_freeze(item) for item in self.icons))
        object.__setattr__(self, "input_schema", _freeze(self.input_schema))
        object.__setattr__(self, "output_schema", _freeze(self.output_schema))
        object.__setattr__(self, "annotations", _freeze(self.annotations))

    def to_dict(self) -> dict[str, Any]:
        result = {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "icons": [_thaw(item) for item in self.icons],
            "inputSchema": _thaw(self.input_schema),
            "annotations": _thaw(self.annotations),
        }
        if self.output_schema is not None:
            result["outputSchema"] = _thaw(self.output_schema)
        return result

    @property
    def schema_digest(self) -> str:
        return digest(
            {
                "inputSchema": _thaw(self.input_schema),
                "outputSchema": _thaw(self.output_schema),
            }
        )


@dataclass(frozen=True, slots=True)
class MCPToolCatalog:
    """Canonical tool contract plus non-identity retrieval metadata.

    ``catalog_digest`` intentionally excludes TTL, pagination cursor/page shape,
    and cache scope. Those values describe how the catalog was retrieved, not
    the tool contract itself; including them would create false schema-drift
    alarms when an otherwise identical server refreshes cache metadata.
    """

    tools: tuple[MCPToolDescriptor, ...]
    page_digests: tuple[str, ...]
    cache_scope: str
    min_ttl_ms: int

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.tools, key=lambda item: item.name))
        if len({item.name for item in ordered}) != len(ordered):
            raise ValueError("MCP catalog contains duplicate tool names")
        if self.cache_scope not in {"public", "private"} or self.min_ttl_ms < 0:
            raise ValueError("invalid MCP cache metadata")
        object.__setattr__(self, "tools", ordered)
        object.__setattr__(self, "page_digests", tuple(self.page_digests))

    def by_name(self) -> dict[str, MCPToolDescriptor]:
        return {item.name: item for item in self.tools}

    def to_dict(self) -> dict[str, Any]:
        return {
            "tools": [item.to_dict() for item in self.tools],
            "pageDigests": list(self.page_digests),
            "cacheScope": self.cache_scope,
            "minTtlMs": self.min_ttl_ms,
        }

    @property
    def catalog_digest(self) -> str:
        return digest({"tools": [item.to_dict() for item in self.tools]})


@dataclass(frozen=True, slots=True)
class MCPGatewayDescription:
    gateway_name: str
    gateway_version: str
    protocol_version: str
    upstream_url_digest: str
    server_digest: str
    baseline_catalog_digest: str
    allowed_tools: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "gateway_name": self.gateway_name,
            "gateway_version": self.gateway_version,
            "protocol_version": self.protocol_version,
            "upstream_url_digest": self.upstream_url_digest,
            "server_digest": self.server_digest,
            "baseline_catalog_digest": self.baseline_catalog_digest,
            "allowed_tools": list(self.allowed_tools),
        }

    @property
    def identity_digest(self) -> str:
        return digest(self.to_dict())


class MCPCallOutcome(StrEnum):
    """Verification outcome of one upstream ``tools/call`` attempt."""

    SUCCESS = "success"
    TOOL_ERROR = "tool_error"
    UPSTREAM_ERROR = "upstream_error"


@dataclass(frozen=True, slots=True)
class MCPCallRecord:
    correlation_id: str
    tool_name: str
    arguments_digest: str
    result_digest: str | None
    schema_digest: str
    catalog_digest: str
    outcome: MCPCallOutcome

    def __post_init__(self) -> None:
        if not self.correlation_id or not self.tool_name:
            raise ValueError("MCP call identity must be non-empty")
        try:
            outcome = MCPCallOutcome(self.outcome)
        except ValueError as exc:
            raise ValueError(f"invalid MCP call outcome: {self.outcome!r}") from exc
        object.__setattr__(self, "outcome", outcome)

        if outcome is MCPCallOutcome.UPSTREAM_ERROR:
            if self.result_digest is not None:
                raise ValueError("upstream-error MCP calls cannot have a result digest")
        elif self.result_digest is None:
            raise ValueError("accepted MCP result outcomes require a result digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "tool_name": self.tool_name,
            "arguments_digest": self.arguments_digest,
            "result_digest": self.result_digest,
            "schema_digest": self.schema_digest,
            "catalog_digest": self.catalog_digest,
            "outcome": self.outcome.value,
        }

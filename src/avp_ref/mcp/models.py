"""Immutable MCP verification-gateway value objects."""

from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
from avp_ref.canonical import digest

MCP_PROTOCOL_VERSION = "2026-07-28"

def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping): return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)): return tuple(_freeze(v) for v in value)
    return value

def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping): return {str(k): _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple): return [_thaw(v) for v in value]
    return value

@dataclass(frozen=True, slots=True)
class MCPGatewayPolicy:
    allowed_tools: frozenset[str]
    detect_schema_drift: bool = True
    max_catalog_tools: int = 512
    max_catalog_pages: int = 32
    max_schema_depth: int = 32
    def __post_init__(self):
        if min(self.max_catalog_tools, self.max_catalog_pages, self.max_schema_depth) < 1: raise ValueError("MCP policy limits must be >= 1")
        object.__setattr__(self, "allowed_tools", frozenset(str(x) for x in self.allowed_tools))

@dataclass(frozen=True, slots=True)
class MCPServerDescription:
    supported_versions: tuple[str, ...]; server_name: str; server_version: str; capabilities: Mapping[str, Any]
    def __post_init__(self):
        if not self.server_name or not self.server_version: raise ValueError("MCP server identity must be non-empty")
        object.__setattr__(self, "capabilities", _freeze(self.capabilities))
    def to_dict(self): return {"supported_versions": list(self.supported_versions), "server_name": self.server_name, "server_version": self.server_version, "capabilities": _thaw(self.capabilities)}
    @property
    def identity_digest(self): return digest(self.to_dict())

@dataclass(frozen=True, slots=True)
class MCPToolDescriptor:
    name: str; title: str | None; description: str | None; icons: tuple[Mapping[str, Any], ...]; input_schema: Mapping[str, Any]; output_schema: Any | None = None; annotations: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.name: raise ValueError("MCP tool name must be non-empty")
        object.__setattr__(self, "icons", tuple(_freeze(x) for x in self.icons)); object.__setattr__(self, "input_schema", _freeze(self.input_schema)); object.__setattr__(self, "output_schema", _freeze(self.output_schema)); object.__setattr__(self, "annotations", _freeze(self.annotations))
    def to_dict(self):
        out={"name":self.name,"title":self.title,"description":self.description,"icons":[_thaw(x) for x in self.icons],"inputSchema":_thaw(self.input_schema),"annotations":_thaw(self.annotations)}
        if self.output_schema is not None: out["outputSchema"]=_thaw(self.output_schema)
        return out
    @property
    def schema_digest(self): return digest({"inputSchema":_thaw(self.input_schema),"outputSchema":_thaw(self.output_schema)})

@dataclass(frozen=True, slots=True)
class MCPToolCatalog:
    """Canonical tool contract plus non-identity retrieval metadata.

    ``catalog_digest`` intentionally excludes TTL, pagination cursor/page shape,
    and cache scope. Those values describe how the catalog was retrieved, not
    the tool contract itself; including them would create false schema-drift
    alarms when an otherwise identical server refreshes cache metadata.
    """
    tools: tuple[MCPToolDescriptor, ...]; page_digests: tuple[str, ...]; cache_scope: str; min_ttl_ms: int
    def __post_init__(self):
        ordered=tuple(sorted(self.tools,key=lambda x:x.name))
        if len({x.name for x in ordered})!=len(ordered): raise ValueError("MCP catalog contains duplicate tool names")
        if self.cache_scope not in {"public","private"} or self.min_ttl_ms<0: raise ValueError("invalid MCP cache metadata")
        object.__setattr__(self,"tools",ordered); object.__setattr__(self,"page_digests",tuple(self.page_digests))
    def by_name(self): return {x.name:x for x in self.tools}
    def to_dict(self): return {"tools":[x.to_dict() for x in self.tools],"pageDigests":list(self.page_digests),"cacheScope":self.cache_scope,"minTtlMs":self.min_ttl_ms}
    @property
    def catalog_digest(self):
        return digest({"tools":[x.to_dict() for x in self.tools]})

@dataclass(frozen=True, slots=True)
class MCPGatewayDescription:
    gateway_name:str; gateway_version:str; protocol_version:str; upstream_url_digest:str; server_digest:str; baseline_catalog_digest:str; allowed_tools:tuple[str,...]
    def to_dict(self): return {"gateway_name":self.gateway_name,"gateway_version":self.gateway_version,"protocol_version":self.protocol_version,"upstream_url_digest":self.upstream_url_digest,"server_digest":self.server_digest,"baseline_catalog_digest":self.baseline_catalog_digest,"allowed_tools":list(self.allowed_tools)}
    @property
    def identity_digest(self): return digest(self.to_dict())

@dataclass(frozen=True, slots=True)
class MCPCallRecord:
    correlation_id:str; tool_name:str; arguments_digest:str; result_digest:str|None; schema_digest:str; catalog_digest:str; upstream_error:bool=False
    def to_dict(self): return {"correlation_id":self.correlation_id,"tool_name":self.tool_name,"arguments_digest":self.arguments_digest,"result_digest":self.result_digest,"schema_digest":self.schema_digest,"catalog_digest":self.catalog_digest,"upstream_error":self.upstream_error}

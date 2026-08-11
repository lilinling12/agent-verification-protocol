"""Verification gateway in front of a real MCP server."""
from __future__ import annotations
import re, uuid
from collections.abc import Mapping
from typing import Any
from jsonschema import Draft202012Validator, ValidationError, SchemaError
from avp_ref.canonical import digest
from avp_ref.scenario.models import ScenarioInstance
from .errors import MCPPermissionDenied, MCPProtocolError, MCPSchemaDriftError, MCPUpstreamError
from .models import MCP_PROTOCOL_VERSION,MCPCallRecord,MCPGatewayDescription,MCPGatewayPolicy,MCPServerDescription,MCPToolCatalog,MCPToolDescriptor
from .transport import MCPTransport
_GATEWAY_VERSION="0.2.0-alpha.4"; _TOKEN=re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")

class MCPVerificationGateway:
    def __init__(self,transport:MCPTransport,policy:MCPGatewayPolicy,*,endpoint_identity:str):
        if not endpoint_identity: raise ValueError("endpoint_identity must be non-empty")
        self._transport=transport; self._policy=policy; self._endpoint_identity=endpoint_identity; self._server=None; self._catalog=None; self._records=[]
    @classmethod
    def policy_from_scenario(cls,scenario:ScenarioInstance,actor_id="subject"):
        caps=scenario.document.get("capabilities",{}); actor=caps.get(actor_id,{}) if hasattr(caps,"get") else {}; includes=actor.get("include",()) if hasattr(actor,"get") else ()
        return MCPGatewayPolicy(frozenset(str(x).rsplit("/",1)[-1] for x in includes if str(x).startswith("mcp://") and "/" in str(x)))
    @property
    def configuration_digest(self): return digest({"gateway":"avp-mcp-verification-gateway","version":_GATEWAY_VERSION,"protocol":MCP_PROTOCOL_VERSION,"endpoint":digest(self._endpoint_identity),"policy":{"allowed_tools":sorted(self._policy.allowed_tools),"detect_schema_drift":self._policy.detect_schema_drift,"max_catalog_tools":self._policy.max_catalog_tools,"max_catalog_pages":self._policy.max_catalog_pages,"max_schema_depth":self._policy.max_schema_depth}})
    def open(self):
        server=self._discover()
        if MCP_PROTOCOL_VERSION not in server.supported_versions: raise MCPProtocolError(f"upstream does not support MCP {MCP_PROTOCOL_VERSION}")
        if "tools" not in server.capabilities: raise MCPProtocolError("upstream MCP server does not advertise tools capability")
        catalog=self._list_tools(); missing=self._policy.allowed_tools-set(catalog.by_name())
        if missing: raise MCPPermissionDenied(f"allowed AVS tools missing from MCP catalog: {sorted(missing)}")
        self._server=server; self._catalog=catalog; return self.describe()
    def describe(self):
        if self._server is None or self._catalog is None: raise MCPProtocolError("MCP gateway is not open")
        return MCPGatewayDescription("avp-mcp-verification-gateway",_GATEWAY_VERSION,MCP_PROTOCOL_VERSION,digest(self._endpoint_identity),self._server.identity_digest,self._catalog.catalog_digest,tuple(sorted(self._policy.allowed_tools)))
    @property
    def call_records(self): return tuple(self._records)
    def owns_tool(self,name): return name in self._policy.allowed_tools
    def call_tool(self,name,arguments,*,correlation_id=None):
        if self._catalog is None: raise MCPProtocolError("MCP gateway is not open")
        if name not in self._policy.allowed_tools: raise MCPPermissionDenied(f"MCP tool is not permitted by compiled AVS policy: {name}")
        baseline=self._catalog.by_name().get(name)
        if baseline is None: raise MCPProtocolError(f"baseline MCP catalog has no tool: {name}")
        active=self._list_tools() if self._policy.detect_schema_drift else self._catalog; current=active.by_name().get(name)
        if current is None or current.schema_digest!=baseline.schema_digest or active.catalog_digest!=self._catalog.catalog_digest: raise MCPSchemaDriftError(f"MCP tool catalog/schema drift detected before call: {name}")
        args=dict(arguments); self._validate_instance(args,baseline.input_schema,"tool arguments"); headers=self._extract_mcp_headers(baseline.input_schema,args); cid=correlation_id or "mcp_"+uuid.uuid4().hex[:16]
        try: result=self._transport.request("tools/call",{"name":name,"arguments":args},name=name,extra_headers=headers)
        except MCPUpstreamError:
            self._records.append(MCPCallRecord(cid,name,digest(args),None,baseline.schema_digest,self._catalog.catalog_digest,True)); raise
        normalized=self._normalize_call_result(result)
        if baseline.output_schema is not None:
            if "structuredContent" not in normalized: raise MCPProtocolError("tool declares outputSchema but response has no structuredContent")
            self._validate_instance(normalized["structuredContent"],baseline.output_schema,"structuredContent")
        self._records.append(MCPCallRecord(cid,name,digest(args),digest(normalized),baseline.schema_digest,self._catalog.catalog_digest,False)); return normalized
    def refresh_catalog(self):
        if self._catalog is None: raise MCPProtocolError("MCP gateway is not open")
        c=self._list_tools()
        if c.catalog_digest!=self._catalog.catalog_digest: raise MCPSchemaDriftError("MCP tool catalog drift detected")
        return c
    def _discover(self):
        r=self._transport.request("server/discover",{}); versions=r.get("supportedVersions"); caps=r.get("capabilities"); info=r.get("serverInfo")
        if not isinstance(versions,list) or not all(isinstance(x,str) for x in versions) or not isinstance(caps,dict) or not isinstance(info,dict) or not isinstance(info.get("name"),str) or not isinstance(info.get("version"),str): raise MCPProtocolError("invalid server/discover response")
        return MCPServerDescription(tuple(versions),info["name"],info["version"],caps)
    def _list_tools(self):
        desc=[]; pages=[]; ttls=[]; scope=None; cursor=None; seen=set()
        for _ in range(self._policy.max_catalog_pages):
            r=self._transport.request("tools/list",{"cursor":cursor} if cursor else {}); tools=r.get("tools"); ttl=r.get("ttlMs"); ps=r.get("cacheScope")
            if not isinstance(tools,list) or not isinstance(ttl,int) or ttl<0 or ps not in {"public","private"}: raise MCPProtocolError("invalid MCP 2026-07-28 tools/list cache/catalog fields")
            if scope is None: scope=ps
            elif scope!=ps: raise MCPProtocolError("tools/list cacheScope changed across pages")
            pages.append(digest(r)); ttls.append(ttl)
            for raw in tools:
                tool=self._parse_tool(raw)
                if tool is not None: desc.append(tool)
                if len(desc)>self._policy.max_catalog_tools: raise MCPProtocolError("MCP catalog exceeds tool limit")
            nxt=r.get("nextCursor")
            if nxt is None:return MCPToolCatalog(tuple(desc),tuple(pages),scope or "private",min(ttls) if ttls else 0)
            if not isinstance(nxt,str) or not nxt or nxt in seen: raise MCPProtocolError("invalid or looping tools/list cursor")
            seen.add(nxt); cursor=nxt
        raise MCPProtocolError("tools/list exceeded page limit")
    def _parse_tool(self,raw):
        if not isinstance(raw,dict) or not isinstance(raw.get("name"),str) or not isinstance(raw.get("inputSchema"),dict): raise MCPProtocolError("malformed MCP tool descriptor")
        self._validate_schema(raw["inputSchema"]); out=raw.get("outputSchema")
        if out is not None:self._validate_schema(out)
        try:self._header_paths(raw["inputSchema"])
        except MCPProtocolError:return None
        return MCPToolDescriptor(raw["name"],raw.get("title"),raw.get("description"),tuple(raw.get("icons") or ()),raw["inputSchema"],out,raw.get("annotations") or {})
    def _validate_schema(self,schema):
        self._validate_schema_depth(schema); self._reject_external_refs(schema)
        try: Draft202012Validator.check_schema(schema)
        except SchemaError as exc: raise MCPProtocolError(f"invalid JSON Schema: {exc.message}") from exc
    def _validate_instance(self,value,schema,label):
        try: Draft202012Validator(schema).validate(value)
        except ValidationError as exc: raise MCPProtocolError(f"{label} does not conform to schema: {exc.message}") from exc
    def _validate_schema_depth(self,value,depth=0):
        if depth>self._policy.max_schema_depth: raise MCPProtocolError("MCP schema exceeds depth limit")
        if isinstance(value,Mapping):
            for v in value.values():self._validate_schema_depth(v,depth+1)
        elif isinstance(value,(list,tuple)):
            for v in value:self._validate_schema_depth(v,depth+1)
    def _reject_external_refs(self,value):
        if isinstance(value,Mapping):
            ref=value.get("$ref")
            if isinstance(ref,str) and not ref.startswith("#"): raise MCPProtocolError("external JSON Schema $ref is not allowed in MCP verification gateway")
            for v in value.values():self._reject_external_refs(v)
        elif isinstance(value,(list,tuple)):
            for v in value:self._reject_external_refs(v)
    def _header_paths(self,schema,path=(),seen=None):
        seen={} if seen is None else seen; found=[]; properties=schema.get("properties") or {}
        if not isinstance(properties,Mapping): return found
        for key,prop in properties.items():
            if not isinstance(prop,Mapping):continue
            p=path+(key,); header=prop.get("x-mcp-header")
            if header is not None:
                if not isinstance(header,str) or not header or not _TOKEN.match(header) or prop.get("type") not in {"string","integer","boolean"} or header.lower() in seen: raise MCPProtocolError("invalid x-mcp-header annotation")
                seen[header.lower()]=p; found.append((p,header,prop.get("type")))
            if prop.get("type")=="object": found.extend(self._header_paths(prop,p,seen))
        return found
    def _extract_mcp_headers(self,schema,args):
        out={}
        for path,name,kind in self._header_paths(schema):
            value=args
            for part in path:
                if not isinstance(value,Mapping) or part not in value: value=None; break
                value=value[part]
            if value is None: continue
            if kind=="integer" and (not isinstance(value,int) or isinstance(value,bool) or abs(value)>9007199254740991): raise MCPProtocolError("x-mcp-header integer is outside safe range")
            if kind=="boolean" and not isinstance(value,bool): raise MCPProtocolError("x-mcp-header boolean value is invalid")
            if kind=="string" and not isinstance(value,str): raise MCPProtocolError("x-mcp-header string value is invalid")
            out[f"Mcp-Param-{name}"]="true" if value is True else "false" if value is False else str(value)
        return out
    @staticmethod
    def _normalize_call_result(r):
        rt=r.get("resultType")
        if rt=="input_required": raise MCPProtocolError("MCP MRTR input_required is not supported by Alpha 2.5 gateway")
        if rt not in (None,"complete"): raise MCPProtocolError(f"unsupported MCP tools/call resultType: {rt!r}")
        if "isError" in r and not isinstance(r["isError"],bool): raise MCPProtocolError("MCP tools/call isError must be boolean")
        return dict(r)

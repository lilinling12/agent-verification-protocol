"""MCP 2026-07-28 Streamable HTTP transport."""
from __future__ import annotations
import json, socket, urllib.error, urllib.request
from typing import Any, Mapping, Protocol, runtime_checkable
from .errors import MCPProtocolError, MCPTransportError, MCPUpstreamError
from .models import MCP_PROTOCOL_VERSION

@runtime_checkable
class MCPTransport(Protocol):
    def request(self, method:str, params:Mapping[str,Any]|None=None, *, name:str|None=None, extra_headers:Mapping[str,str]|None=None)->Mapping[str,Any]: ...

class HTTPMCPTransport:
    def __init__(self, endpoint:str, *, timeout_seconds:float=10.0, client_name:str="avp-reference", client_version:str="0.2.0-alpha.5", trace_headers_provider=None):
        if not endpoint.startswith(("http://","https://")): raise ValueError("MCP endpoint must use http or https")
        if timeout_seconds<=0: raise ValueError("timeout_seconds must be > 0")
        self.endpoint=endpoint; self.timeout_seconds=float(timeout_seconds); self.client_name=client_name; self.client_version=client_version; self._request_id=0; self._trace_headers_provider=trace_headers_provider
    def request(self, method, params=None, *, name=None, extra_headers=None):
        self._request_id+=1; request_id=f"avp-mcp-{self._request_id}"; merged=dict(params or {}); meta=dict(merged.get("_meta") or {})
        meta.setdefault("io.modelcontextprotocol/protocolVersion",MCP_PROTOCOL_VERSION); meta.setdefault("io.modelcontextprotocol/clientInfo",{"name":self.client_name,"version":self.client_version}); meta.setdefault("io.modelcontextprotocol/clientCapabilities",{}); merged["_meta"]=meta
        payload={"jsonrpc":"2.0","id":request_id,"method":method,"params":merged}; headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream","MCP-Protocol-Version":MCP_PROTOCOL_VERSION,"Mcp-Method":method}
        if name: headers["Mcp-Name"]=name
        if self._trace_headers_provider is not None:
            for k,v in self._trace_headers_provider().items():
                if k.lower() not in {item.lower() for item in headers}: headers[str(k)]=str(v)
        for k,v in (extra_headers or {}).items():
            if k.lower() in {item.lower() for item in headers}: raise MCPProtocolError(f"extra MCP header collides with reserved header: {k}")
            headers[k]=v
        req=urllib.request.Request(self.endpoint,data=json.dumps(payload,separators=(",", ":")).encode(),headers=headers,method="POST")
        try:
            with urllib.request.urlopen(req,timeout=self.timeout_seconds) as resp: ct=resp.headers.get_content_type(); body=resp.read()
        except urllib.error.HTTPError as exc: raise MCPTransportError(f"MCP HTTP {exc.code}: {exc.read().decode('utf-8',errors='replace')[:512]}") from exc
        except (urllib.error.URLError,socket.timeout,TimeoutError) as exc: raise MCPTransportError(f"MCP transport failure: {exc}") from exc
        decoded=self._decode_json(body) if ct=="application/json" else self._decode_sse(body,request_id) if ct=="text/event-stream" else None
        if decoded is None: raise MCPTransportError(f"unsupported MCP response content type: {ct}")
        return self._validate_response(decoded,request_id)
    @staticmethod
    def _decode_json(body):
        try:return json.loads(body)
        except (UnicodeDecodeError,json.JSONDecodeError) as exc: raise MCPProtocolError("MCP response is not valid UTF-8 JSON") from exc
    def _decode_sse(self,body,request_id):
        try:text=body.decode("utf-8")
        except UnicodeDecodeError as exc: raise MCPProtocolError("MCP SSE response is not valid UTF-8") from exc
        data=[]; candidates=[]
        for line in text.splitlines()+[""]:
            if line=="":
                if data:
                    try:value=json.loads("\n".join(data))
                    except json.JSONDecodeError as exc: raise MCPProtocolError("MCP SSE data event is not valid JSON") from exc
                    data=[]
                    if isinstance(value,dict): candidates.append(value)
            elif line.startswith("data:"): data.append(line[5:].lstrip())
        for c in candidates:
            if c.get("jsonrpc")=="2.0" and c.get("id")==request_id:return c
        raise MCPProtocolError("MCP SSE stream ended without matching JSON-RPC response")
    @staticmethod
    def _validate_response(decoded,request_id):
        if not isinstance(decoded,dict) or decoded.get("jsonrpc")!="2.0" or decoded.get("id")!=request_id: raise MCPProtocolError("MCP JSON-RPC response envelope does not match request")
        if "error" in decoded:
            e=decoded["error"]
            if not isinstance(e,dict) or not isinstance(e.get("code"),int) or not isinstance(e.get("message"),str): raise MCPProtocolError("MCP JSON-RPC error object is malformed")
            raise MCPUpstreamError(e["code"],e["message"],e.get("data"))
        result=decoded.get("result")
        if not isinstance(result,dict): raise MCPProtocolError("MCP JSON-RPC result must be an object")
        return result

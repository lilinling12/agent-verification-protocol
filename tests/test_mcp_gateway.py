from __future__ import annotations
import json, threading, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from avp_ref.mcp import HTTPMCPTransport, MCPGatewayPolicy, MCPPermissionDenied, MCPProtocolError, MCPSchemaDriftError, MCPVerificationGateway
from avp_ref.reference import reference_agent_system, reference_environment, reference_scenario
from avp_ref.runtime import ReferenceRuntime
from avp_ref.subject import InProcessSubjectAdapter
from avp_ref.telemetry import OpenTelemetryBridge

class FakeTransport:
    def __init__(self): self.schema_version=1; self.ttl_ms=1000; self.calls=[]
    def request(self,method,params=None,*,name=None,extra_headers=None):
        self.calls.append((method,dict(params or {}),name,dict(extra_headers or {})))
        if method=="server/discover": return {"supportedVersions":["2026-07-28"],"capabilities":{"tools":{}},"serverInfo":{"name":"fake","version":"1.0"}}
        if method=="tools/list":
            if (params or {}).get("cursor") is None:return {"tools":[{"name":"order.get","title":"Get order","inputSchema":{"type":"object","properties":{"order_id":{"type":"string","x-mcp-header":"Order-Id"}},"required":["order_id"],"x-version":self.schema_version},"outputSchema":{"type":"object","properties":{"ok":{"type":"boolean"}},"required":["ok"]}}],"nextCursor":"p2","ttlMs":self.ttl_ms,"cacheScope":"private"}
            return {"tools":[{"name":"refund.create","inputSchema":{"type":"object","properties":{"order_id":{"type":"string"}},"required":["order_id"]}}],"ttlMs":self.ttl_ms,"cacheScope":"private"}
        if method=="tools/call": return {"resultType":"complete","structuredContent":{"ok":True},"isError":False}
        raise AssertionError(method)

class MCPGatewayTest(unittest.TestCase):
    def make_gateway(self,t=None): return MCPVerificationGateway(t or FakeTransport(),MCPGatewayPolicy(frozenset({"order.get","refund.create"})),endpoint_identity="http://mcp.test/mcp")
    def test_open_discovers_paginated_catalog(self): d=self.make_gateway(); desc=d.open(); self.assertEqual("2026-07-28",desc.protocol_version); self.assertTrue(desc.baseline_catalog_digest.startswith("sha256:"))
    def test_permission_fail_closed(self):
        g=self.make_gateway(); g.open()
        with self.assertRaises(MCPPermissionDenied): g.call_tool("customer.delete",{})
    def test_schema_drift_before_side_effect(self):
        t=FakeTransport(); g=self.make_gateway(t); g.open(); t.schema_version=2
        with self.assertRaises(MCPSchemaDriftError): g.call_tool("order.get",{"order_id":"ord_1"})
        self.assertFalse(any(x[0]=="tools/call" for x in t.calls))
    def test_cache_metadata_change_is_not_schema_drift(self):
        t=FakeTransport(); g=self.make_gateway(t); baseline=g.open().baseline_catalog_digest; t.ttl_ms=250; result=g.call_tool("order.get",{"order_id":"ord_1"}); self.assertTrue(result["structuredContent"]["ok"]); self.assertEqual(baseline,g.call_records[-1].catalog_digest)
    def test_call_validates_schema_and_mirrors_header(self):
        t=FakeTransport(); g=self.make_gateway(t); g.open(); g.call_tool("order.get",{"order_id":"ord_1"},correlation_id="call_7",trace_headers={"traceparent":"00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"}); call=[x for x in t.calls if x[0]=="tools/call"][0]; self.assertEqual("ord_1",call[3]["Mcp-Param-Order-Id"]); self.assertIn("traceparent",call[3]); self.assertEqual("call_7",g.call_records[-1].correlation_id)
        with self.assertRaises(MCPProtocolError): g.call_tool("order.get",{})
    def test_runtime_routes_mcp_and_emits_digests_and_trace_context(self):
        def subject(session,task): session.call_tool("order.get",{"order_id":"ord_1"}); return "done"
        t=FakeTransport(); g=MCPVerificationGateway(t,MCPGatewayPolicy(frozenset({"order.get"})),endpoint_identity="x"); rt=ReferenceRuntime(OpenTelemetryBridge()); ep=rt.create_episode(reference_scenario(),reference_agent_system("mcp-probe"),reference_environment(),InProcessSubjectAdapter(subject),g); rt.provision(ep.episode_id); rt.run_subject(ep.episode_id); events=[e for e in ep.events if e.event_type=="tool.result" and e.payload.get("protocol")=="mcp"]; self.assertEqual(1,len(events)); self.assertTrue(events[0].payload["schema_digest"].startswith("sha256:")); call=[x for x in t.calls if x[0]=="tools/call"][0]; self.assertIn("traceparent",call[3])

class HTTPMCPTransportTest(unittest.TestCase):
    def setUp(self):
        self.requests=[]; outer=self
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                n=int(self.headers.get("Content-Length","0")); p=json.loads(self.rfile.read(n)); outer.requests.append(({k.lower():v for k,v in self.headers.items()},p)); m=p["method"]
                if m=="server/discover": r={"supportedVersions":["2026-07-28"],"capabilities":{"tools":{}},"serverInfo":{"name":"local","version":"1"}}
                elif m=="tools/list": r={"tools":[{"name":"order.get","inputSchema":{"type":"object","properties":{"order_id":{"type":"string","x-mcp-header":"Order-Id"}},"required":["order_id"]}}],"ttlMs":0,"cacheScope":"private"}
                else:r={"resultType":"complete","structuredContent":{"ok":True}}
                body=json.dumps({"jsonrpc":"2.0","id":p["id"],"result":r}).encode(); ct="application/json"
                if m=="tools/list": body=b"event: message\ndata: "+body+b"\n\n"; ct="text/event-stream"
                self.send_response(200); self.send_header("Content-Type",ct); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
            def log_message(self,*args): pass
        self.server=ThreadingHTTPServer(("127.0.0.1",0),Handler); self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start(); self.endpoint=f"http://127.0.0.1:{self.server.server_address[1]}/mcp"
    def tearDown(self): self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)
    def test_json_sse_headers_and_meta(self):
        g=MCPVerificationGateway(HTTPMCPTransport(self.endpoint,timeout_seconds=2),MCPGatewayPolicy(frozenset({"order.get"})),endpoint_identity=self.endpoint); g.open(); g.call_tool("order.get",{"order_id":"ord_1"},trace_headers={"traceparent":"00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"});
        for h,p in self.requests: self.assertEqual("2026-07-28",h["mcp-protocol-version"]); self.assertEqual(p["method"],h["mcp-method"])
        call=[h for h,p in self.requests if p["method"]=="tools/call"][0]; self.assertEqual("order.get",call["mcp-name"]); self.assertEqual("ord_1",call["mcp-param-order-id"]); self.assertIn("traceparent",call)

if __name__=="__main__": unittest.main()

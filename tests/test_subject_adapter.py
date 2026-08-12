import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from avp_ref.environment import InMemoryCommerceAdapter
from avp_ref.oracle import RefundOracle
from avp_ref.reference import correct_subject, reference_agent_system, reference_scenario, reference_subject_adapter
from avp_ref.runtime import EpisodeState, ReferenceRuntime
from avp_ref.subject import HTTPSubjectAdapter
from avp_ref.telemetry import OpenTelemetryBridge

class _AgentHandler(BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def do_POST(self):
        self.server.traceparents.append(self.headers.get("traceparent")); length=int(self.headers.get("Content-Length","0")); body=json.loads(self.rfile.read(length).decode()); step=body["step"]; previous=body.get("previous_tool_result")
        if step==1: response={"status":"tool_call","call":{"call_id":"c1","name":"order.get","arguments":{"order_id":"ord_1"}}}
        elif step==2: self.server.saw_previous_result=previous is not None and previous.get("call_id")=="c1"; response={"status":"tool_call","call":{"call_id":"c2","name":"refund.create","arguments":{"order_id":"ord_1"}}}
        else: response={"status":"completed","report":"Refund for ord_1 completed over HTTP."}
        raw=json.dumps(response).encode(); self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def log_message(self,*args): pass

class SubjectAdapterTest(unittest.TestCase):
    def test_in_process_adapter_executes_through_runtime(self):
        runtime=ReferenceRuntime(); episode=runtime.create_episode(reference_scenario(),reference_agent_system("correct"),InMemoryCommerceAdapter(),reference_subject_adapter(correct_subject)); runtime.provision(episode.episode_id); runtime.run_subject(episode.episode_id); runtime.verify(episode.episode_id,RefundOracle()); self.assertEqual("PASS",episode.task_verdict.value)
    def test_http_adapter_executes_external_step_protocol_and_propagates_trace(self):
        server=ThreadingHTTPServer(("127.0.0.1",0),_AgentHandler); server.saw_previous_result=False; server.traceparents=[]; thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            adapter=HTTPSubjectAdapter(f"http://127.0.0.1:{server.server_port}"); runtime=ReferenceRuntime(OpenTelemetryBridge()); episode=runtime.create_episode(reference_scenario(),reference_agent_system("http-agent",adapter="http"),InMemoryCommerceAdapter(),adapter); runtime.provision(episode.episode_id); runtime.run_subject(episode.episode_id); runtime.verify(episode.episode_id,RefundOracle()); self.assertEqual("PASS",episode.task_verdict.value); self.assertTrue(server.saw_previous_result); self.assertTrue(server.traceparents); self.assertTrue(all(value and value.startswith("00-") for value in server.traceparents))
        finally: server.shutdown(); server.server_close()
    def test_http_protocol_rejects_malformed_tool_call(self):
        class BadHandler(_AgentHandler):
            def do_POST(self):
                length=int(self.headers.get("Content-Length","0")); self.rfile.read(length); raw=json.dumps({"status":"tool_call","call":{"name":"order.get","arguments":{}}}).encode(); self.send_response(200); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
        server=ThreadingHTTPServer(("127.0.0.1",0),BadHandler); threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            adapter=HTTPSubjectAdapter(f"http://127.0.0.1:{server.server_port}"); runtime=ReferenceRuntime(); episode=runtime.create_episode(reference_scenario(),reference_agent_system("bad-http",adapter="http"),InMemoryCommerceAdapter(),adapter); runtime.provision(episode.episode_id); runtime.run_subject(episode.episode_id); self.assertIs(EpisodeState.INFRA_FAILED,episode.state); self.assertIn("SubjectProtocolError",episode.agent_report)
        finally: server.shutdown(); server.server_close()
    def test_user_cannot_spoof_trace_headers(self):
        with self.assertRaises(ValueError): HTTPSubjectAdapter("http://127.0.0.1:1",headers={"TraceParent":"00-deadbeef"})

if __name__=="__main__": unittest.main()

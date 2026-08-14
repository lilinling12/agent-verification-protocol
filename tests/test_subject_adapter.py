import json
import threading
import unittest
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from avp_ref.environment import InMemoryCommerceAdapter
from avp_ref.reference import (
    correct_subject,
    reference_agent_system,
    reference_oracle_package,
    reference_scenario,
    reference_subject_adapter,
)
from avp_ref.runtime import EpisodeState, ReferenceRuntime
from avp_ref.subject import (
    HTTPSubjectAdapter,
    SubjectTransportError,
)
from avp_ref.telemetry import OpenTelemetryBridge


class _AgentHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        self.server.traceparents.append(self.headers.get("traceparent"))
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length).decode())
        step = body["step"]
        previous = body.get("previous_tool_result")
        if step == 1:
            response = {
                "status": "tool_call",
                "call": {
                    "call_id": "c1",
                    "name": "order.get",
                    "arguments": {"order_id": "ord_1"},
                },
            }
        elif step == 2:
            self.server.saw_previous_result = (
                previous is not None and previous.get("call_id") == "c1"
            )
            response = {
                "status": "tool_call",
                "call": {
                    "call_id": "c2",
                    "name": "refund.create",
                    "arguments": {"order_id": "ord_1"},
                },
            }
        else:
            response = {
                "status": "completed",
                "report": "Refund for ord_1 completed over HTTP.",
            }
        raw = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


class SubjectAdapterTest(unittest.TestCase):
    def test_in_process_adapter_executes_through_runtime(self):
        runtime = ReferenceRuntime()
        episode = runtime.create_episode(
            scenario=reference_scenario(),
            agent_system=reference_agent_system("correct"),
            environment_adapter=InMemoryCommerceAdapter(),
            subject_adapter=reference_subject_adapter(correct_subject),
            oracle_package=reference_oracle_package(),
        )
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        runtime.verify(episode.episode_id)
        self.assertEqual("PASS", episode.task_verdict.value)

    def test_http_adapter_executes_external_step_protocol_and_propagates_trace(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _AgentHandler)
        server.saw_previous_result = False
        server.traceparents = []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            adapter = HTTPSubjectAdapter(
                f"http://127.0.0.1:{server.server_port}"
            )
            runtime = ReferenceRuntime(OpenTelemetryBridge())
            episode = runtime.create_episode(
                scenario=reference_scenario(),
                agent_system=reference_agent_system("http-agent", adapter="http"),
                environment_adapter=InMemoryCommerceAdapter(),
                subject_adapter=adapter,
                oracle_package=reference_oracle_package(),
            )
            runtime.provision(episode.episode_id)
            runtime.run_subject(episode.episode_id)
            runtime.verify(episode.episode_id)
            self.assertEqual("PASS", episode.task_verdict.value)
            self.assertTrue(server.saw_previous_result)
            self.assertTrue(server.traceparents)
            self.assertTrue(
                all(
                    value and value.startswith("00-")
                    for value in server.traceparents
                )
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_http_protocol_rejects_malformed_tool_call(self):
        class BadHandler(_AgentHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length)
                raw = json.dumps(
                    {
                        "status": "tool_call",
                        "call": {"name": "order.get", "arguments": {}},
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        server = ThreadingHTTPServer(("127.0.0.1", 0), BadHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            adapter = HTTPSubjectAdapter(
                f"http://127.0.0.1:{server.server_port}"
            )
            runtime = ReferenceRuntime()
            episode = runtime.create_episode(
                scenario=reference_scenario(),
                agent_system=reference_agent_system("bad-http", adapter="http"),
                environment_adapter=InMemoryCommerceAdapter(),
                subject_adapter=adapter,
                oracle_package=reference_oracle_package(),
            )
            runtime.provision(episode.episode_id)
            runtime.run_subject(episode.episode_id)
            self.assertIs(EpisodeState.INFRA_FAILED, episode.state)
            self.assertIn("SubjectProtocolError", episode.agent_report)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_handle_owner_fields_are_enforced(self):
        adapter = reference_subject_adapter(correct_subject)
        agent = reference_agent_system("owner-bound")
        handle = adapter.open(agent)
        forged = replace(handle, adapter_name="foreign-adapter")
        with self.assertRaises(SubjectTransportError):
            adapter.release(forged)
        adapter.release(handle)

    def test_http_target_is_bound_without_exposing_raw_target(self):
        first = HTTPSubjectAdapter("https://agent-a.example.test")
        second = HTTPSubjectAdapter("https://agent-b.example.test")
        first_description = first.describe()
        second_description = second.describe()
        self.assertNotEqual(
            first_description.identity_digest,
            second_description.identity_digest,
        )
        self.assertNotEqual(
            first_description.metadata["targetDigest"],
            second_description.metadata["targetDigest"],
        )
        self.assertNotIn("agent-a.example.test", repr(first_description.metadata))

    def test_http_base_url_rejects_userinfo_credentials(self):
        with self.assertRaises(ValueError):
            HTTPSubjectAdapter("https://user:secret@example.test")

    def test_user_cannot_spoof_trace_headers(self):
        with self.assertRaises(ValueError):
            HTTPSubjectAdapter(
                "http://127.0.0.1:1",
                headers={"TraceParent": "00-deadbeef"},
            )


if __name__ == "__main__":
    unittest.main()

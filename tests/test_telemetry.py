import unittest
from avp_ref.oracle import RefundOracle
from avp_ref.reference import correct_subject, reference_agent_system, reference_environment, reference_scenario, reference_subject_adapter
from avp_ref.runtime import EpisodeState, ReferenceRuntime
from avp_ref.telemetry import NoopTelemetryBridge, OpenTelemetryBridge, TelemetryCompleteness, TelemetryPolicy

class TelemetryBridgeTest(unittest.TestCase):
    def test_runtime_produces_trace_evidence_and_tool_spans(self):
        bridge=OpenTelemetryBridge(); rt=ReferenceRuntime(bridge); ep=rt.create_episode(reference_scenario(),reference_agent_system("otel"),reference_environment(),reference_subject_adapter(correct_subject)); rt.provision(ep.episode_id); rt.run_subject(ep.episode_id); rt.verify(ep.episode_id,RefundOracle())
        art=ep.telemetry.artifact; self.assertIsNotNone(art); self.assertEqual(TelemetryCompleteness.COMPLETE,art.completeness); self.assertEqual(32,len(art.trace_id)); self.assertGreaterEqual(art.span_count,2); self.assertIn(f"ev_{ep.episode_id}_telemetry",ep.evidence)
        spans=[s for s in bridge.finished_spans() if f"{s.context.trace_id:032x}"==art.trace_id]; self.assertTrue(any(s.name.startswith("avp.tool ") for s in spans))

    def test_traceparent_is_w3c_formatted(self):
        bridge=OpenTelemetryBridge(); session=bridge.start_episode("ep_trace","sha256:test"); headers=session.inject_headers(); self.assertRegex(headers["traceparent"],r"^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$"); session.finalize()

    def test_sensitive_payloads_are_not_exported(self):
        bridge=OpenTelemetryBridge(); rt=ReferenceRuntime(bridge); ep=rt.create_episode(reference_scenario(),reference_agent_system("otel-safe"),reference_environment(),reference_subject_adapter(correct_subject)); rt.provision(ep.episode_id); rt.run_subject(ep.episode_id); rt.verify(ep.episode_id,RefundOracle()); text=repr([(s.attributes,[(e.name,e.attributes) for e in s.events]) for s in bridge.finished_spans()]); self.assertNotIn("ord_1",text); self.assertNotIn("Refund for ord_1 completed",text)

    def test_required_missing_telemetry_invalidates_evaluation(self):
        rt=ReferenceRuntime(NoopTelemetryBridge(TelemetryPolicy(required=True))); ep=rt.create_episode(reference_scenario(),reference_agent_system("required"),reference_environment(),reference_subject_adapter(correct_subject)); rt.provision(ep.episode_id); rt.run_subject(ep.episode_id); rt.verify(ep.episode_id,RefundOracle()); self.assertIs(EpisodeState.INVALID,ep.state); self.assertIsNotNone(ep.telemetry.artifact); self.assertEqual(TelemetryCompleteness.REQUIRED_MISSING,ep.telemetry.artifact.completeness)

    def test_raw_sensitive_capture_fails_closed(self):
        with self.assertRaises(ValueError): TelemetryPolicy(capture_sensitive_payloads=True)

if __name__=="__main__":unittest.main()

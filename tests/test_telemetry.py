import unittest

from avp_ref.reference import (
    correct_subject,
    reference_agent_system,
    reference_environment,
    reference_oracle_package,
    reference_scenario,
    reference_subject_adapter,
)
from avp_ref.runtime import EpisodeState, ReferenceRuntime
from avp_ref.telemetry import (
    NoopTelemetryBridge,
    OpenTelemetryBridge,
    TelemetryCompleteness,
    TelemetryPolicy,
)


def _episode(runtime: ReferenceRuntime, name: str):
    return runtime.create_episode(
        scenario=reference_scenario(),
        agent_system=reference_agent_system(name),
        environment_adapter=reference_environment(),
        subject_adapter=reference_subject_adapter(correct_subject),
        oracle_package=reference_oracle_package(),
    )


class TelemetryBridgeTest(unittest.TestCase):
    def test_runtime_produces_trace_evidence_and_tool_spans(self):
        bridge = OpenTelemetryBridge()
        runtime = ReferenceRuntime(bridge)
        episode = _episode(runtime, "otel")
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        runtime.verify(episode.episode_id)
        artifact = episode.telemetry.artifact
        self.assertIsNotNone(artifact)
        self.assertEqual(TelemetryCompleteness.COMPLETE, artifact.completeness)
        self.assertEqual(32, len(artifact.trace_id))
        self.assertGreaterEqual(artifact.span_count, 2)
        self.assertIn(f"ev_{episode.episode_id}_telemetry", episode.evidence)
        spans = [
            span
            for span in bridge.finished_spans()
            if f"{span.context.trace_id:032x}" == artifact.trace_id
        ]
        self.assertTrue(any(span.name.startswith("avp.tool ") for span in spans))

    def test_traceparent_is_w3c_formatted(self):
        bridge = OpenTelemetryBridge()
        session = bridge.start_episode("ep_trace", "sha256:" + "0" * 64)
        headers = session.inject_headers()
        self.assertRegex(headers["traceparent"], r"^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$")
        session.finalize()

    def test_sensitive_payloads_are_not_exported(self):
        bridge = OpenTelemetryBridge()
        runtime = ReferenceRuntime(bridge)
        episode = _episode(runtime, "otel-safe")
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        runtime.verify(episode.episode_id)
        text = repr(
            [
                (span.attributes, [(event.name, event.attributes) for event in span.events])
                for span in bridge.finished_spans()
            ]
        )
        self.assertNotIn("ord_1", text)
        self.assertNotIn("Refund for ord_1 completed", text)

    def test_required_missing_telemetry_invalidates_evaluation(self):
        runtime = ReferenceRuntime(NoopTelemetryBridge(TelemetryPolicy(required=True)))
        episode = _episode(runtime, "required")
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        runtime.verify(episode.episode_id)
        self.assertIs(EpisodeState.INVALID, episode.state)
        self.assertIsNotNone(episode.telemetry.artifact)
        self.assertEqual(TelemetryCompleteness.REQUIRED_MISSING, episode.telemetry.artifact.completeness)

    def test_raw_sensitive_capture_fails_closed(self):
        with self.assertRaises(ValueError):
            TelemetryPolicy(capture_sensitive_payloads=True)


if __name__ == "__main__":
    unittest.main()

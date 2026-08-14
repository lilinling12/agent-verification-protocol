from __future__ import annotations

import unittest

from opentelemetry.trace import StatusCode

from avp_ref.models import AVPEvent
from avp_ref.telemetry import (
    OpenTelemetryBridge,
    TelemetryCompleteness,
    TelemetryPolicy,
)


def _event(
    event_id: str,
    event_type: str,
    sequence: int,
    payload: dict[str, object] | None = None,
) -> AVPEvent:
    return AVPEvent(
        event_id=event_id,
        event_type=event_type,
        episode_id="ep_otel_mapping",
        sequence=sequence,
        plane="environment",
        logical_time=sequence,
        payload=dict(payload or {}),
    )


class OpenTelemetryMappingInvariantTest(unittest.TestCase):
    def test_mcp_tool_error_remains_result_but_marks_tool_span_error(self) -> None:
        bridge = OpenTelemetryBridge()
        session = bridge.start_episode(
            "ep_otel_mapping",
            "sha256:" + "a" * 64,
        )
        session.record_event(
            _event(
                "ev_call",
                "tool.call",
                1,
                {
                    "name": "order.get",
                    "protocol": "mcp",
                    "correlation_id": "call_1",
                },
            )
        )
        session.record_event(
            _event(
                "ev_result",
                "tool.result",
                2,
                {
                    "name": "order.get",
                    "protocol": "mcp",
                    "correlation_id": "call_1",
                    "result": {"isError": True, "content": [{"type": "text"}]},
                },
            )
        )
        artifact = session.finalize()

        spans = [
            span
            for span in bridge.finished_spans()
            if f"{span.context.trace_id:032x}" == artifact.trace_id
            and span.attributes.get("avp.correlation_id") == "call_1"
        ]
        self.assertEqual(1, len(spans))
        self.assertEqual("tool_error", spans[0].attributes["avp.tool.outcome"])
        self.assertIs(StatusCode.ERROR, spans[0].status.status_code)
        self.assertIs(TelemetryCompleteness.COMPLETE, artifact.completeness)

    def test_success_does_not_invent_otel_ok_status(self) -> None:
        bridge = OpenTelemetryBridge()
        session = bridge.start_episode(
            "ep_otel_mapping",
            "sha256:" + "b" * 64,
        )
        session.record_event(
            _event(
                "ev_call",
                "tool.call",
                1,
                {
                    "name": "order.get",
                    "protocol": "mcp",
                    "correlation_id": "call_success",
                },
            )
        )
        session.record_event(
            _event(
                "ev_result",
                "tool.result",
                2,
                {
                    "name": "order.get",
                    "protocol": "mcp",
                    "correlation_id": "call_success",
                    "result": {"isError": False},
                },
            )
        )
        artifact = session.finalize()
        span = next(
            span
            for span in bridge.finished_spans()
            if f"{span.context.trace_id:032x}" == artifact.trace_id
            and span.attributes.get("avp.correlation_id") == "call_success"
        )
        self.assertEqual("success", span.attributes["avp.tool.outcome"])
        self.assertIs(StatusCode.UNSET, span.status.status_code)

    def test_unmatched_required_tool_call_cannot_claim_complete(self) -> None:
        bridge = OpenTelemetryBridge(TelemetryPolicy(required=True))
        session = bridge.start_episode(
            "ep_otel_mapping",
            "sha256:" + "c" * 64,
        )
        session.record_event(
            _event(
                "ev_call",
                "tool.call",
                1,
                {
                    "name": "order.get",
                    "protocol": "mcp",
                    "correlation_id": "call_missing_outcome",
                },
            )
        )
        artifact = session.finalize(complete=True)
        self.assertIs(
            TelemetryCompleteness.REQUIRED_MISSING,
            artifact.completeness,
        )

    def test_propagation_is_bound_to_active_root_context(self) -> None:
        bridge = OpenTelemetryBridge()
        session = bridge.start_episode(
            "ep_otel_mapping",
            "sha256:" + "d" * 64,
        )
        headers = session.inject_headers()
        artifact = session.finalize()
        parts = headers["traceparent"].split("-")
        self.assertEqual(artifact.trace_id, parts[1])
        self.assertEqual(artifact.root_span_id, parts[2])
        self.assertEqual(1, artifact.propagated_requests)


if __name__ == "__main__":
    unittest.main()

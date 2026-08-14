"""OpenTelemetry implementation of AVP verification telemetry correlation."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from avp_ref.models import AVPEvent

from .models import (
    TelemetryArtifact,
    TelemetryCompleteness,
    TelemetryDescription,
    TelemetryPolicy,
)

_TERMINAL_EVENTS = frozenset(
    {"episode.completed", "episode.invalid", "episode.resources.released"}
)
_SAFE_PAYLOAD_KEYS = frozenset(
    {
        "manifest_digest",
        "scenario_instance_digest",
        "agent_system_digest",
        "environment_adapter_digest",
        "subject_adapter_digest",
        "mcp_gateway_config_digest",
        "telemetry_config_digest",
        "gateway_digest",
        "server_digest",
        "catalog_digest",
        "protocol_version",
        "adapter",
        "handle_id",
        "target",
        "equivalent_to_initial",
        "status",
        "steps",
        "error_type",
        "claim_id",
        "dimension",
        "verdict",
        "severity",
        "method",
        "evaluator_version",
        "task_verdict",
        "validity",
        "snapshot_id",
        "consistency",
        "equivalence",
        "fault_id",
        "type",
        "occurrence",
        "visibility",
        "name",
        "protocol",
        "correlation_id",
        "schema_digest",
        "result_digest",
        "outcome",
    }
)
_TRACEPARENT = re.compile(
    r"^00-(?P<trace_id>[0-9a-f]{32})-(?P<span_id>[0-9a-f]{16})-(?P<flags>[0-9a-f]{2})$"
)


@runtime_checkable
class TelemetrySession(Protocol):
    @property
    def artifact(self) -> TelemetryArtifact | None: ...

    def record_event(self, event: AVPEvent) -> None: ...

    def inject_headers(self) -> Mapping[str, str]: ...

    def finalize(self, *, complete: bool = True) -> TelemetryArtifact: ...


@runtime_checkable
class TelemetryBridge(Protocol):
    def describe(self) -> TelemetryDescription: ...

    def start_episode(self, episode_id: str, manifest_digest: str) -> TelemetrySession: ...


class _NoopSession:
    def __init__(self, episode_id: str, required: bool) -> None:
        self._episode_id = episode_id
        self._required = required
        self._events = 0
        self._artifact: TelemetryArtifact | None = None

    @property
    def artifact(self) -> TelemetryArtifact | None:
        return self._artifact

    def record_event(self, event: AVPEvent) -> None:
        if self._artifact is not None:
            return
        self._events += 1
        if event.event_type in _TERMINAL_EVENTS:
            self.finalize(complete=True)

    def inject_headers(self) -> Mapping[str, str]:
        return {}

    def finalize(self, *, complete: bool = True) -> TelemetryArtifact:
        if self._artifact is None:
            completeness = (
                TelemetryCompleteness.REQUIRED_MISSING
                if self._required
                else TelemetryCompleteness.BEST_EFFORT
            )
            self._artifact = TelemetryArtifact(
                self._episode_id,
                None,
                None,
                self._events,
                0,
                completeness,
                0,
            )
        return self._artifact


class NoopTelemetryBridge:
    def __init__(self, policy: TelemetryPolicy | None = None) -> None:
        self._policy = policy or TelemetryPolicy()
        self._description = TelemetryDescription(
            "noop-telemetry",
            "0.1.0",
            "none",
            self._policy,
        )

    def describe(self) -> TelemetryDescription:
        return self._description

    def start_episode(self, episode_id: str, manifest_digest: str) -> TelemetrySession:
        del manifest_digest
        return _NoopSession(episode_id, self._policy.required)


class _OpenTelemetrySession:
    def __init__(self, episode_id, manifest_digest, tracer, exporter, policy) -> None:
        from opentelemetry import trace

        self._trace = trace
        self._episode_id = episode_id
        self._tracer = tracer
        self._exporter = exporter
        self._policy = policy
        self._root = tracer.start_span(
            "avp.episode",
            attributes={
                "avp.episode.id": episode_id,
                "avp.manifest.digest": manifest_digest,
            },
        )
        self._context = trace.set_span_in_context(self._root)
        self._events = 0
        self._propagated = 0
        self._artifact: TelemetryArtifact | None = None
        self._open_spans: dict[str, Any] = {}
        self._mapping_incomplete = False

    @property
    def artifact(self) -> TelemetryArtifact | None:
        return self._artifact

    def _safe(self, value: Any) -> bool | int | float | str:
        if isinstance(value, (bool, int, float)):
            return value
        return str(value)[: self._policy.max_attribute_length]

    def _attrs(self, event: AVPEvent) -> dict[str, Any]:
        attributes: dict[str, Any] = {
            "avp.event.id": event.event_id,
            "avp.event.type": event.event_type,
            "avp.event.sequence": event.sequence,
            "avp.plane": event.plane,
            "avp.logical_time": event.logical_time,
        }
        for key, value in event.payload.items():
            if (
                key in _SAFE_PAYLOAD_KEYS
                and value is not None
                and not isinstance(value, (Mapping, list, tuple))
            ):
                attributes[f"avp.{key}"] = self._safe(value)
        return attributes

    @staticmethod
    def _tool_outcome(event: AVPEvent) -> str:
        if event.event_type == "tool.error":
            return "upstream_error"

        declared = event.payload.get("outcome")
        if isinstance(declared, str) and declared:
            return declared.lower()

        result = event.payload.get("result")
        if isinstance(result, Mapping) and result.get("isError") is True:
            return "tool_error"
        return "success"

    def record_event(self, event: AVPEvent) -> None:
        if self._artifact is not None:
            return

        self._events += 1
        attributes = self._attrs(event)
        self._root.add_event(f"avp.{event.event_type}", attributes)
        correlation_id = str(event.payload.get("correlation_id") or "")

        if event.event_type == "tool.call" and correlation_id:
            from opentelemetry.trace import SpanKind

            if correlation_id in self._open_spans:
                self._mapping_incomplete = True
            else:
                self._open_spans[correlation_id] = self._tracer.start_span(
                    f"avp.tool {event.payload.get('name', 'unknown')}",
                    context=self._context,
                    kind=SpanKind.CLIENT,
                    attributes={
                        "avp.correlation_id": correlation_id,
                        "avp.tool.name": str(event.payload.get("name", "unknown")),
                        "avp.tool.protocol": str(
                            event.payload.get("protocol", "unknown")
                        ),
                    },
                )
        elif event.event_type in {"tool.result", "tool.error"} and correlation_id:
            span = self._open_spans.pop(correlation_id, None)
            if span is None:
                self._mapping_incomplete = True
            else:
                outcome = self._tool_outcome(event)
                span.set_attribute("avp.tool.outcome", outcome)
                if outcome != "success":
                    from opentelemetry.trace import Status, StatusCode

                    span.set_status(Status(StatusCode.ERROR, outcome))
                span.end()

        if event.event_type in _TERMINAL_EVENTS:
            self.finalize(complete=True)

    def inject_headers(self) -> Mapping[str, str]:
        from opentelemetry.propagate import inject

        carrier: dict[str, str] = {}
        inject(carrier, context=self._context)

        traceparent = carrier.get("traceparent", "")
        match = _TRACEPARENT.fullmatch(traceparent)
        context = self._root.get_span_context()
        if (
            match is None
            or not context.is_valid
            or match.group("trace_id") != f"{context.trace_id:032x}"
            or match.group("span_id") != f"{context.span_id:016x}"
        ):
            raise RuntimeError(
                "OpenTelemetry propagation did not produce trace context "
                "for the active AVP Episode"
            )

        self._propagated += 1
        return carrier

    def finalize(self, *, complete: bool = True) -> TelemetryArtifact:
        if self._artifact is not None:
            return self._artifact

        if self._open_spans:
            self._mapping_incomplete = True
        for span in self._open_spans.values():
            span.end()
        self._open_spans.clear()

        context = self._root.get_span_context()
        self._root.end()
        all_spans = (
            tuple(self._exporter.get_finished_spans())
            if self._exporter is not None
            else ()
        )
        spans = tuple(
            span for span in all_spans if span.context.trace_id == context.trace_id
        )

        if not complete:
            completeness = TelemetryCompleteness.INCOMPLETE
        elif self._mapping_incomplete:
            completeness = (
                TelemetryCompleteness.REQUIRED_MISSING
                if self._policy.required
                else TelemetryCompleteness.INCOMPLETE
            )
        else:
            completeness = TelemetryCompleteness.COMPLETE

        if self._policy.required and (not context.is_valid or not spans):
            completeness = TelemetryCompleteness.REQUIRED_MISSING

        self._artifact = TelemetryArtifact(
            self._episode_id,
            f"{context.trace_id:032x}" if context.is_valid else None,
            f"{context.span_id:016x}" if context.is_valid else None,
            self._events,
            self._propagated,
            completeness,
            len(spans),
        )
        return self._artifact


class OpenTelemetryBridge:
    def __init__(self, policy: TelemetryPolicy | None = None) -> None:
        self._policy = policy or TelemetryPolicy()
        try:
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import SimpleSpanProcessor
            from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
                InMemorySpanExporter,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Install avp-reference[otel] to use OpenTelemetryBridge"
            ) from exc

        self._exporter = InMemorySpanExporter()
        self._provider = TracerProvider(
            resource=Resource.create({"service.name": "avp-reference"})
        )
        self._provider.add_span_processor(SimpleSpanProcessor(self._exporter))
        self._tracer = self._provider.get_tracer("avp.reference", "0.2.0-alpha.5")
        self._description = TelemetryDescription(
            "opentelemetry",
            "0.2.0-alpha.5",
            "otel-sdk",
            self._policy,
        )

    def describe(self) -> TelemetryDescription:
        return self._description

    def start_episode(self, episode_id: str, manifest_digest: str) -> TelemetrySession:
        return _OpenTelemetrySession(
            episode_id,
            manifest_digest,
            self._tracer,
            self._exporter,
            self._policy,
        )

    def finished_spans(self) -> tuple[Any, ...]:
        return tuple(self._exporter.get_finished_spans())

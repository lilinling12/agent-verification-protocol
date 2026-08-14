"""Reference adapter for the AVP OpenTelemetry mapping v0.1 profile."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from opentelemetry.trace import StatusCode

from avp_ref.models import AVPEvent, TaskVerdict
from avp_ref.reference import (
    correct_subject,
    false_success_subject,
    reference_agent_system,
    reference_environment,
    reference_oracle_package,
    reference_scenario,
    reference_subject_adapter,
)
from avp_ref.runtime import EpisodeState, ReferenceRuntime
from avp_ref.telemetry import (
    OpenTelemetryBridge,
    TelemetryCompleteness,
    TelemetryPolicy,
)

from .models import TCKAdapterError, TCKCaseResult, TCKStatus

_TRACEPARENT = re.compile(
    r"^00-(?P<trace_id>[0-9a-f]{32})-(?P<span_id>[0-9a-f]{16})-(?P<flags>[0-9a-f]{2})$"
)


class _MalformedPropagator:
    """Instance-local propagator used to exercise fail-closed propagation."""

    @property
    def fields(self) -> set[str]:
        return {"traceparent"}

    def inject(self, carrier, context=None, setter=None) -> None:
        del context
        if setter is None:
            carrier["traceparent"] = "not-a-traceparent"
        else:
            setter.set(carrier, "traceparent", "not-a-traceparent")

    def extract(self, carrier, context=None, getter=None):
        del carrier, getter
        return context


class _DroppingOutcomeSession:
    """Delegate to real OTel telemetry while dropping one required tool outcome."""

    def __init__(self, delegate) -> None:
        self._delegate = delegate
        self._dropped = False

    @property
    def artifact(self):
        return self._delegate.artifact

    def record_event(self, event: AVPEvent) -> None:
        if event.event_type == "tool.result" and not self._dropped:
            self._dropped = True
            return
        self._delegate.record_event(event)

    def inject_headers(self):
        return self._delegate.inject_headers()

    def finalize(self, *, complete: bool = True):
        return self._delegate.finalize(complete=complete)


class _DroppingOutcomeBridge:
    """Real OTel bridge with deterministic telemetry-loss injection."""

    def __init__(self) -> None:
        self._inner = OpenTelemetryBridge(TelemetryPolicy(required=True))

    def describe(self):
        return self._inner.describe()

    def start_episode(self, episode_id: str, manifest_digest: str):
        return _DroppingOutcomeSession(
            self._inner.start_episode(episode_id, manifest_digest)
        )


class ReferenceOpenTelemetryTCKAdapter:
    """Execute AVP-owned OTel mappings against real reference telemetry behavior."""

    _ROOT = "AVP-TCK-OTEL-ROOT-CORRELATION-001"
    _EVENT = "AVP-TCK-OTEL-EVENT-CORRELATION-001"
    _TOOL = "AVP-TCK-OTEL-TOOL-CORRELATION-001"
    _OUTCOME = "AVP-TCK-OTEL-OUTCOME-PRESERVATION-001"
    _PROPAGATION = "AVP-TCK-OTEL-PROPAGATION-001"
    _MINIMIZATION = "AVP-TCK-OTEL-DATA-MINIMIZATION-001"
    _COMPLETENESS = "AVP-TCK-OTEL-COMPLETENESS-001"
    _EVIDENCE = "AVP-TCK-OTEL-EVIDENCE-BINDING-001"

    @property
    def supported_case_ids(self) -> frozenset[str]:
        return frozenset(
            {
                self._ROOT,
                self._EVENT,
                self._TOOL,
                self._OUTCOME,
                self._PROPAGATION,
                self._MINIMIZATION,
                self._COMPLETENESS,
                self._EVIDENCE,
            }
        )

    def evaluate(self, case: Mapping[str, Any]) -> TCKCaseResult:
        case_id = self._case_id(case)
        vector = self._vector(case, case_id)
        evaluators = {
            self._ROOT: self._root_correlation,
            self._EVENT: self._event_correlation,
            self._TOOL: self._tool_correlation,
            self._OUTCOME: self._outcome_preservation,
            self._PROPAGATION: self._propagation,
            self._MINIMIZATION: self._data_minimization,
            self._COMPLETENESS: self._completeness,
            self._EVIDENCE: self._evidence_binding,
        }
        evaluator = evaluators.get(case_id)
        if evaluator is None:
            raise TCKAdapterError(f"unsupported reference OTel TCK case: {case_id}")
        passed, detail = evaluator(vector)
        return TCKCaseResult(
            case_id,
            TCKStatus.PASS if passed else TCKStatus.FAIL,
            detail,
        )

    @staticmethod
    def _root_correlation(vector: Mapping[str, Any]) -> tuple[bool, str]:
        episode_id = str(vector.get("episodeId", ""))
        manifest_digest = str(vector.get("manifestDigest", ""))
        unrelated = str(vector.get("unrelatedManifestDigest", ""))
        bridge = OpenTelemetryBridge()
        artifact = bridge.start_episode(episode_id, manifest_digest).finalize()
        root = ReferenceOpenTelemetryTCKAdapter._root_span(bridge, artifact.trace_id)
        attributes = dict(root.attributes)
        passed = (
            attributes.get("avp.episode.id") == episode_id
            and attributes.get("avp.manifest.digest") == manifest_digest
            and attributes.get("avp.manifest.digest") != unrelated
            and artifact.episode_id == episode_id
        )
        return passed, ReferenceOpenTelemetryTCKAdapter._detail(
            passed,
            "Episode and manifest identity are bound to the telemetry root",
            "telemetry root lost Episode/manifest correlation",
        )

    @staticmethod
    def _event_correlation(vector: Mapping[str, Any]) -> tuple[bool, str]:
        bridge = OpenTelemetryBridge()
        session = bridge.start_episode("ep_otel_events", "sha256:" + "1" * 64)
        expected: list[tuple[str, str, int]] = []
        for raw in vector.get("events", ()):
            item = ReferenceOpenTelemetryTCKAdapter._mapping(raw, "events[]")
            identity = (
                str(item.get("id", "")),
                str(item.get("type", "")),
                int(item.get("sequence", 0)),
            )
            expected.append(identity)
            session.record_event(
                ReferenceOpenTelemetryTCKAdapter._event(
                    *identity,
                    {"raw_payload": "must-not-be-required"},
                )
            )
        artifact = session.finalize()
        root = ReferenceOpenTelemetryTCKAdapter._root_span(bridge, artifact.trace_id)
        expected_ids = {item[0] for item in expected}
        actual = [
            (
                event.attributes.get("avp.event.id"),
                event.attributes.get("avp.event.type"),
                event.attributes.get("avp.event.sequence"),
            )
            for event in root.events
            if event.attributes.get("avp.event.id") in expected_ids
        ]
        exported = repr(
            [(event.name, dict(event.attributes)) for event in root.events]
        )
        passed = actual == expected and "must-not-be-required" not in exported
        return passed, ReferenceOpenTelemetryTCKAdapter._detail(
            passed,
            "AVP event identity/type/order survive mapping without raw payloads",
            "event correlation or minimization was lost",
        )

    @staticmethod
    def _tool_correlation(vector: Mapping[str, Any]) -> tuple[bool, str]:
        bridge = OpenTelemetryBridge()
        session = bridge.start_episode("ep_otel_tools", "sha256:" + "2" * 64)
        calls = [
            ReferenceOpenTelemetryTCKAdapter._mapping(item, "calls[]")
            for item in vector.get("calls", ())
        ]
        outcomes = [
            ReferenceOpenTelemetryTCKAdapter._mapping(item, "outcomes[]")
            for item in vector.get("outcomes", ())
        ]
        sequence = 0
        for call in calls:
            sequence += 1
            session.record_event(
                ReferenceOpenTelemetryTCKAdapter._event(
                    f"ev_call_{sequence}",
                    "tool.call",
                    sequence,
                    {
                        "name": str(call.get("tool", "")),
                        "protocol": "mcp",
                        "correlation_id": str(call.get("correlationId", "")),
                    },
                )
            )
        for outcome in outcomes:
            sequence += 1
            session.record_event(
                ReferenceOpenTelemetryTCKAdapter._event(
                    f"ev_result_{sequence}",
                    "tool.result",
                    sequence,
                    {
                        "name": "order.get",
                        "protocol": "mcp",
                        "correlation_id": str(outcome.get("correlationId", "")),
                        "result": {"isError": False},
                    },
                )
            )
        artifact = session.finalize()
        spans = ReferenceOpenTelemetryTCKAdapter._tool_spans(bridge, artifact.trace_id)
        actual = [str(span.attributes.get("avp.correlation_id")) for span in spans]
        expected = {str(call.get("correlationId", "")) for call in calls}
        passed = (
            len(spans) == len(calls)
            and set(actual) == expected
            and len(actual) == len(set(actual))
            and all(span.attributes.get("avp.tool.name") == "order.get" for span in spans)
        )
        return passed, ReferenceOpenTelemetryTCKAdapter._detail(
            passed,
            "same-name tool calls remain independently correlated",
            "tool telemetry collapsed or rebound correlation identities",
        )

    @staticmethod
    def _outcome_preservation(vector: Mapping[str, Any]) -> tuple[bool, str]:
        del vector
        bridge = OpenTelemetryBridge()
        session = bridge.start_episode("ep_otel_outcomes", "sha256:" + "3" * 64)
        sequence = 0

        def emit(event_type: str, correlation: str, **payload: Any) -> None:
            nonlocal sequence
            sequence += 1
            session.record_event(
                ReferenceOpenTelemetryTCKAdapter._event(
                    f"ev_outcome_{sequence}",
                    event_type,
                    sequence,
                    {
                        "name": "order.get",
                        "protocol": "mcp",
                        "correlation_id": correlation,
                        **payload,
                    },
                )
            )

        emit("tool.call", "call_success")
        emit("tool.result", "call_success", result={"isError": False})
        emit("tool.call", "call_tool_error")
        emit("tool.result", "call_tool_error", result={"isError": True})
        emit("tool.call", "call_upstream_error")
        emit("tool.error", "call_upstream_error", error_type="MCPUpstreamError")
        session.record_event(
            ReferenceOpenTelemetryTCKAdapter._event(
                "ev_invalid",
                "episode.invalid",
                sequence + 1,
                {"validity": "INFRA_CONFOUND"},
            )
        )
        artifact = session.artifact
        if artifact is None:
            return False, "invalid Episode did not finalize telemetry"

        spans = {
            str(span.attributes.get("avp.correlation_id")): span
            for span in ReferenceOpenTelemetryTCKAdapter._tool_spans(
                bridge, artifact.trace_id
            )
        }
        root = ReferenceOpenTelemetryTCKAdapter._root_span(bridge, artifact.trace_id)
        event_types = {event.attributes.get("avp.event.type") for event in root.events}
        passed = (
            spans["call_success"].attributes.get("avp.tool.outcome") == "success"
            and spans["call_success"].status.status_code is StatusCode.UNSET
            and spans["call_tool_error"].attributes.get("avp.tool.outcome")
            == "tool_error"
            and spans["call_tool_error"].status.status_code is StatusCode.ERROR
            and spans["call_upstream_error"].attributes.get("avp.tool.outcome")
            == "upstream_error"
            and spans["call_upstream_error"].status.status_code is StatusCode.ERROR
            and "episode.invalid" in event_types
        )
        return passed, ReferenceOpenTelemetryTCKAdapter._detail(
            passed,
            "success, tool error, upstream error, and invalid evaluation stay distinct",
            "telemetry flattened materially different AVP outcomes",
        )

    @staticmethod
    def _propagation(vector: Mapping[str, Any]) -> tuple[bool, str]:
        if vector.get("propagationClaimed") is not True:
            return False, "portable vector must exercise a claimed propagation path"

        bridge = OpenTelemetryBridge()
        session = bridge.start_episode("ep_otel_propagation", "sha256:" + "4" * 64)
        headers = session.inject_headers()
        artifact = session.finalize()
        match = _TRACEPARENT.fullmatch(headers.get("traceparent", ""))
        valid = (
            match is not None
            and match.group("trace_id") == artifact.trace_id
            and match.group("span_id") == artifact.root_span_id
            and artifact.propagated_requests == 1
        )

        malformed_bridge = OpenTelemetryBridge(propagator=_MalformedPropagator())
        malformed_session = malformed_bridge.start_episode(
            "ep_otel_malformed",
            "sha256:" + "5" * 64,
        )
        malformed_rejected = False
        try:
            malformed_session.inject_headers()
        except RuntimeError:
            malformed_rejected = True
        malformed = malformed_session.finalize()

        passed = valid and malformed_rejected and malformed.propagated_requests == 0
        return passed, ReferenceOpenTelemetryTCKAdapter._detail(
            passed,
            "W3C propagation is Episode-bound and malformed carriers fail closed",
            "propagation was malformed, unbound, or falsely counted",
        )

    @staticmethod
    def _data_minimization(vector: Mapping[str, Any]) -> tuple[bool, str]:
        protected = [str(item) for item in vector.get("protectedValues", ())]
        bridge = OpenTelemetryBridge()
        session = bridge.start_episode("ep_otel_min", "sha256:" + "6" * 64)
        values = protected + ["raw"] * max(0, 6 - len(protected))
        session.record_event(
            ReferenceOpenTelemetryTCKAdapter._event(
                "ev_min",
                "tool.call",
                1,
                {
                    "correlation_id": "call_min",
                    "name": "order.get",
                    "protocol": "mcp",
                    "raw_prompt": values[0],
                    "arguments": values[1],
                    "result": values[2],
                    "credential": values[3],
                    "oracle_material": values[4],
                    "fault_schedule": values[5],
                },
            )
        )
        session.record_event(
            ReferenceOpenTelemetryTCKAdapter._event(
                "ev_min_result",
                "tool.result",
                2,
                {
                    "correlation_id": "call_min",
                    "name": "order.get",
                    "protocol": "mcp",
                    "result": {"isError": False},
                },
            )
        )
        artifact = session.finalize()
        spans = ReferenceOpenTelemetryTCKAdapter._trace_spans(bridge, artifact.trace_id)
        exported = repr(
            [
                (
                    dict(span.attributes),
                    [(event.name, dict(event.attributes)) for event in span.events],
                )
                for span in spans
            ]
        )
        root = ReferenceOpenTelemetryTCKAdapter._root_span(bridge, artifact.trace_id)
        identity_present = any(
            event.attributes.get("avp.event.id") == "ev_min" for event in root.events
        )
        passed = identity_present and all(item not in exported for item in protected)
        return passed, ReferenceOpenTelemetryTCKAdapter._detail(
            passed,
            "verification identity survives without protected raw values",
            "protected content leaked or required identity disappeared",
        )

    @staticmethod
    def _completeness(vector: Mapping[str, Any]) -> tuple[bool, str]:
        if vector.get("requiredTelemetry") is not True:
            return False, "portable completeness vector must require telemetry"

        runtime = ReferenceRuntime(_DroppingOutcomeBridge())
        episode = runtime.create_episode(
            scenario=reference_scenario(),
            agent_system=reference_agent_system("otel-required-loss"),
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(correct_subject),
            oracle_package=reference_oracle_package(),
        )
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        runtime.verify(episode.episode_id)
        artifact = episode.telemetry.artifact if episode.telemetry else None
        passed = (
            artifact is not None
            and artifact.trace_id is not None
            and artifact.completeness is TelemetryCompleteness.REQUIRED_MISSING
            and episode.state is EpisodeState.INVALID
            and episode.task_verdict is TaskVerdict.INCONCLUSIVE
        )
        return passed, ReferenceOpenTelemetryTCKAdapter._detail(
            passed,
            "required mapping loss cannot hide behind trace existence",
            "missing required telemetry was represented as complete/valid",
        )

    @staticmethod
    def _evidence_binding(vector: Mapping[str, Any]) -> tuple[bool, str]:
        del vector
        runtime = ReferenceRuntime(OpenTelemetryBridge())
        episode = runtime.create_episode(
            scenario=reference_scenario(),
            agent_system=reference_agent_system("otel-evidence"),
            environment_adapter=reference_environment(),
            subject_adapter=reference_subject_adapter(false_success_subject),
            oracle_package=reference_oracle_package(),
        )
        runtime.provision(episode.episode_id)
        runtime.run_subject(episode.episode_id)
        runtime.verify(episode.episode_id)
        evidence_id = f"ev_{episode.episode_id}_telemetry"
        evidence = episode.evidence.get(evidence_id)
        if evidence is None:
            return False, "runtime did not publish telemetry through AVP Evidence"
        payload = json.loads(runtime.read_evidence(episode.episode_id, evidence_id))
        passed = (
            payload.get("episode_id") == episode.episode_id
            and evidence.artifact.digest.startswith("sha256:")
            and episode.task_verdict is TaskVerdict.FAIL
            and episode.state is EpisodeState.COMPLETED
        )
        return passed, ReferenceOpenTelemetryTCKAdapter._detail(
            passed,
            "telemetry is integrity-bound while task verdict remains authoritative",
            "telemetry Evidence binding or verdict separation failed",
        )

    @staticmethod
    def _event(
        event_id: str,
        event_type: str,
        sequence: int,
        payload: Mapping[str, Any],
    ) -> AVPEvent:
        return AVPEvent(
            event_id=event_id,
            event_type=event_type,
            episode_id="ep_reference_otel",
            sequence=sequence,
            plane="environment",
            logical_time=sequence,
            payload=dict(payload),
        )

    @staticmethod
    def _trace_spans(bridge: OpenTelemetryBridge, trace_id: str | None):
        return [
            span
            for span in bridge.finished_spans()
            if trace_id is not None and f"{span.context.trace_id:032x}" == trace_id
        ]

    @staticmethod
    def _root_span(bridge: OpenTelemetryBridge, trace_id: str | None):
        roots = [
            span
            for span in ReferenceOpenTelemetryTCKAdapter._trace_spans(bridge, trace_id)
            if span.parent is None
        ]
        if len(roots) != 1:
            raise TCKAdapterError(
                f"expected one reference OTel root span, found {len(roots)}"
            )
        return roots[0]

    @staticmethod
    def _tool_spans(bridge: OpenTelemetryBridge, trace_id: str | None):
        return [
            span
            for span in ReferenceOpenTelemetryTCKAdapter._trace_spans(bridge, trace_id)
            if "avp.correlation_id" in span.attributes
        ]

    @staticmethod
    def _case_id(case: Mapping[str, Any]) -> str:
        metadata = case.get("metadata")
        case_id = metadata.get("id") if isinstance(metadata, Mapping) else None
        if not isinstance(case_id, str) or not case_id:
            raise TCKAdapterError("OpenTelemetry TCK case metadata.id is missing")
        return case_id

    @staticmethod
    def _vector(case: Mapping[str, Any], case_id: str) -> Mapping[str, Any]:
        vector = case.get("vector")
        if not isinstance(vector, Mapping):
            raise TCKAdapterError(f"{case_id} vector must be an object")
        return vector

    @staticmethod
    def _mapping(value: Any, name: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise TCKAdapterError(f"OpenTelemetry TCK {name} must be an object")
        return value

    @staticmethod
    def _detail(passed: bool, success: str, failure: str) -> str:
        return success if passed else failure

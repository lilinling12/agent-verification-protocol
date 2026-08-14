# OpenTelemetry Mapping Reconciliation Decision 001

- Status: Proposed
- Date: 2026-08-15
- Scope: AVP OpenTelemetry Mapping Profile v0.1

## Decision

Promote only AVP-owned verification correlation, outcome-preservation, data-minimization, completeness-honesty, and Evidence-binding semantics around OpenTelemetry telemetry.

OpenTelemetry remains authoritative for its telemetry data model, APIs, SDKs, propagation mechanics, exporters, semantic conventions, sampling, OTLP, and backend processing.

## Promoted AVP semantics

- bind Episode and manifest identity to the telemetry root/correlation surface;
- correlate AVP event identity and logical ordering without requiring raw payload capture;
- correlate tool calls to their terminal result/error outcome;
- preserve AVP outcome semantics in telemetry rather than flattening failures into success;
- propagate W3C Trace Context when the implementation claims outbound propagation;
- minimize telemetry so secrets, hidden evaluator state, raw tool arguments/results, and sensitive Subject content are not required for conformance;
- represent telemetry completeness explicitly and fail closed when required telemetry is missing;
- publish telemetry as AVP Evidence without treating telemetry as the source of task/oracle truth.

## OpenTelemetry-owned semantics kept external

- Span/SpanContext representation and validity;
- W3C Trace Context parsing/injection details;
- span status API behavior;
- Resource and attribute data models;
- semantic-convention namespaces and stability;
- sampling and processor behavior;
- exporter/collector/OTLP behavior;
- language SDK APIs;
- GenAI semantic conventions.

## Reference implementation consequence

The Python `OpenTelemetryBridge`, in-memory exporter, `TelemetryArtifact`, span naming, and safe-attribute allowlist remain implementation evidence only.

The existing bridge must be audited before conformance is claimed. In particular:

1. `COMPLETE` must not be inferred solely because a valid root trace and at least one exported span exist;
2. MCP `TOOL_ERROR` semantics must remain distinguishable when the Runtime records the terminal tool interaction as a result rather than an infrastructure error;
3. raw payload/secret minimization must remain fail-closed;
4. propagation claims must be backed by a valid W3C `traceparent` carrier.

## Conformance consequence

AVP TCK cases will test verification mappings, not reproduce the OpenTelemetry conformance suite. A portable test may assume an OpenTelemetry-conforming observation model and verify AVP identity binding, correlation, outcome preservation, propagation claim honesty, data minimization, completeness honesty, and Evidence binding.

# AEP-0006 — OpenTelemetry Mapping Profile v0.1

- Status: Final
- Date: 2026-08-15
- Accepted: 2026-08-16
- Acceptance decision: Approved by the protocol maintainer during the Alpha 2 readiness review. This approves the protocol direction only; the AEP is not Final and this decision does not authorize merge, tag, or release.
- Finalized: 2026-08-17
- Final decision: Explicitly approved by the protocol maintainer for `Accepted` → `Final` on 2026-08-17, based on the merged Alpha 2 Final-eligibility audit and released evidence at `v0.3.0-rc.1` / `ef199124017b0dcc8c4a966d00c4f407760f9a06`; the published release bytes passed external-consumer and full TCK validation, no post-release protocol-semantic drift invalidated that evidence, and this Finalization does not authorize stable `v0.3.0` publication.
- Target: AVP v0.1 / Alpha 2

## Context

AVP already has a reference OpenTelemetry bridge that creates an Episode root span, maps AVP events, creates tool spans, injects W3C trace context, and publishes a telemetry artifact. Implementation availability does not define the protocol.

OpenTelemetry remains authoritative for its trace data model, SpanContext, status model, resource model, propagation APIs, W3C Trace Context integration, exporters, SDK behavior, and semantic conventions. AVP must not create a competing tracing specification.

The interoperability problem AVP owns is narrower: when an implementation chooses OpenTelemetry as verification telemetry, which AVP identities and outcome semantics must remain correlatable, what sensitive information must not be required, and when the resulting telemetry may honestly be represented as complete verification evidence.

## Decision

Define an optional `avp-otel-mapping-v0.1` conformance profile that standardizes AVP-owned verification mappings onto OpenTelemetry-compatible telemetry.

The profile will require:

1. an Episode-level trace correlation identity;
2. binding of the Episode and manifest identity to the telemetry root;
3. stable correlation from AVP verification events to telemetry records without requiring raw payload capture;
4. tool interaction correlation across call/result/error boundaries;
5. preservation of AVP outcome semantics rather than flattening failures into successful telemetry;
6. W3C Trace Context-compatible outbound propagation when propagation is claimed;
7. data-minimizing telemetry that does not require raw Subject/evaluator/tool payloads or secrets;
8. explicit completeness/required-missing semantics that cannot be inferred merely from the existence of one trace/span;
9. Evidence publication that binds the telemetry artifact without making an exporter or backend authoritative for AVP verdicts.

## External authority

OpenTelemetry specifications and semantic conventions remain authoritative for:

- Span and SpanContext behavior;
- trace/span identifier validity;
- span status semantics;
- W3C Trace Context propagation behavior;
- resource/attribute/event data models;
- SDK/exporter/processor APIs;
- semantic-convention namespaces and stability;
- sampling behavior;
- OTLP and collector/backend behavior.

AVP does not redefine those semantics.

## Non-goals

AVP OTel v0.1 does not standardize:

- one OpenTelemetry SDK language binding;
- one exporter, collector, backend, or OTLP deployment;
- exact span names produced by the Python reference bridge;
- Python `TelemetryBridge` / `TelemetrySession` APIs;
- one sampling implementation;
- recording raw prompts, tool arguments/results, credentials, or hidden evaluator material;
- all OpenTelemetry GenAI semantic conventions;
- using telemetry as a substitute for AVP Evidence or Oracle verdicts.

## Conformance strategy

Portable TCK vectors should operate on a language-neutral telemetry observation surface rather than Python SDK objects. The reference adapter may use the in-memory OpenTelemetry exporter as implementation evidence.

Conformance must include negative controls for:

- missing manifest/Episode correlation;
- correlation break between tool call and terminal tool outcome;
- successful telemetry status asserted for an AVP failure outcome;
- sensitive raw payload capture where the profile does not explicitly authorize it;
- incomplete required telemetry being reported as complete;
- malformed or non-propagated claimed W3C trace context.

## Consequences

A passing AVP OpenTelemetry mapping profile means the implementation preserves AVP verification correlation and claim honesty when OpenTelemetry is used. It does not certify the OpenTelemetry SDK, exporter, collector, backend, or the implementation against every OpenTelemetry semantic convention.

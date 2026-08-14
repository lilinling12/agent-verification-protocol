# AVP OpenTelemetry Mapping Contract v0.1

Status: draft normative candidate

## 1. Scope

This specification defines AVP-owned verification semantics when OpenTelemetry-compatible telemetry is used to represent an AVP evaluation. It does not redefine OpenTelemetry.

Normative keywords MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are requirement terms for AVP conformance.

## 2. External telemetry authority

OpenTelemetry remains authoritative for Span/SpanContext, Context, propagators, span status APIs, resources, attributes, events, SDK/exporter behavior, semantic conventions, sampling, OTLP, and collector/backend processing.

AVP conformance MUST NOT reinterpret OpenTelemetry wire/data-model semantics as AVP-defined alternatives.

## 3. Episode and manifest correlation

### AVP-OTEL-001 — Episode/manifest correlation

Telemetry represented as AVP verification telemetry MUST expose a stable correlation from the AVP Episode identity and Episode manifest identity to the telemetry root or equivalent trace-level correlation surface.

The mapping MUST allow a consumer to determine which Episode and immutable manifest configuration the telemetry belongs to without depending on raw Subject content.

AVP does not prescribe an exact span name, attribute namespace implementation, SDK resource layout, or exporter representation.

## 4. AVP event correlation

### AVP-OTEL-002 — Verification event correlation

When AVP verification events are mapped to telemetry, the mapping MUST preserve enough identity to correlate each mapped telemetry record to the originating AVP event and its ordering within the Episode.

At minimum, mapped event identity MUST preserve:

- AVP event identity;
- AVP event type;
- AVP event sequence or an equivalently unambiguous Episode-local ordering identity.

The profile MUST NOT require raw AVP event payloads to be copied into telemetry.

## 5. Tool interaction correlation

### AVP-OTEL-003 — Tool call/outcome correlation

A tool interaction represented in telemetry MUST correlate the initiating AVP tool call with its terminal outcome by a stable interaction/correlation identity.

A terminal tool result or tool failure MUST NOT be represented as belonging to a different call merely because the human-readable tool name is equal.

Exact span cardinality, span naming, and SpanKind remain implementation choices unless required by an applicable OpenTelemetry semantic convention outside AVP.

## 6. Outcome preservation

### AVP-OTEL-004 — AVP outcome preservation

Telemetry mapping MUST preserve AVP outcome semantics and MUST NOT flatten a failed interaction into successful telemetry.

Where AVP distinguishes successful tool completion, MCP tool execution error, protocol/upstream failure, evaluation invalidation, or other materially different terminal outcomes, the telemetry representation MUST retain enough information for those outcomes to remain distinguishable.

If an implementation maps an AVP failure to OpenTelemetry span status, that mapping MUST remain consistent with OpenTelemetry status semantics. AVP does not require instrumentation to set `OK` for successful operations.

## 7. Propagation claim honesty

### AVP-OTEL-005 — W3C trace-context propagation honesty

An implementation that claims outbound trace propagation for AVP verification telemetry MUST propagate a valid W3C Trace Context according to the OpenTelemetry propagator requirements applicable to its selected implementation.

A claimed propagation attempt MUST remain correlated to the active AVP Episode trace context. Missing, malformed, or fabricated propagation metadata MUST NOT be reported as successful propagation.

AVP does not define the `traceparent` or `tracestate` grammar.

## 8. Data minimization and secrecy

### AVP-OTEL-006 — Verification telemetry data minimization

AVP OpenTelemetry mapping conformance MUST NOT require capture of raw Subject prompts, raw tool arguments/results, credentials, evaluator secrets, hidden Oracle material, future fault schedules, or other protected content.

An implementation MAY record additional content only under an explicit policy that is outside the mandatory AVP mapping surface and consistent with the AVP Security contract and applicable privacy/security requirements.

The baseline profile MUST remain conformant with only identity-, status-, count-, and other non-sensitive verification metadata required by the mapping contract.

## 9. Completeness honesty

### AVP-OTEL-007 — Telemetry completeness honesty

When an implementation emits an AVP completeness claim for telemetry, the claim MUST reflect whether the verification telemetry required by its declared profile/policy was actually captured and finalized.

The mere existence of a valid trace identifier, root span, exported span, or exporter response MUST NOT by itself establish `COMPLETE`.

If required verification telemetry is missing, the implementation MUST represent that condition as incomplete/required-missing (or an equivalent fail-closed state) and MUST NOT claim complete telemetry evidence.

If telemetry is configured as required for evaluation validity, required-missing telemetry MUST compose with AVP lifecycle/validity handling rather than silently producing a valid evaluation.

## 10. Evidence composition

### AVP-OTEL-008 — Telemetry Evidence binding

Telemetry accepted as AVP Evidence MUST be published through the AVP Evidence/Artifact integrity model or an equivalent AVP-conforming evidence binding.

The published Evidence MUST bind the telemetry artifact identity and its Episode correlation.

Telemetry, an OpenTelemetry backend, or a span status MUST NOT by itself override authoritative AVP Environment/Oracle Evidence, lifecycle validity, or task verdict semantics.

## 11. Non-normative implementation freedom

AVP OpenTelemetry v0.1 does not standardize:

- one OpenTelemetry language SDK;
- one SDK version or exporter implementation;
- one collector/backend;
- OTLP transport/encoding;
- one span naming scheme;
- one sampling strategy;
- the Python `TelemetryBridge` or `TelemetryArtifact` types;
- one attribute allowlist implementation;
- all OpenTelemetry GenAI semantic conventions.

## 12. Security composition

Telemetry mappings MUST compose with the AVP Security contract. Verification observability MUST NOT become a side channel that exposes evaluator-only state, hidden fault schedules, credentials, unrestricted capabilities, or protected Subject content.

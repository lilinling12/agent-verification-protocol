# Alpha 2 Reference Runtime Alignment Audit

Status: **BLOCKED — RRA-003 UNDER REMEDIATION**

Audit baseline: `main@de8fa1c61d94924f63c173fe4f8ea1cdaff73899`

## Purpose

This audit checks the non-normative Python reference implementation against the current governed authority chain:

`Normative Spec -> Schema -> TCK -> Reference Runtime`

It does not permit Python behavior, convenience APIs, historical helpers, or implementation metadata to create protocol obligations.

## Acceptance rule

Reference Runtime Alignment is READY only when:

1. consumer-visible reference behavior does not contradict current normative requirements;
2. implementation identity is bound to the installed distribution identity;
3. runtime discovery metadata does not self-assert TCK conformance that is not represented by validated `ConformanceReport` evidence;
4. mandatory TCK behavior is exercised by the reference adapter rather than manufactured by expectation rewriting;
5. conditional TCK cases are skipped only when their explicit capability condition is not declared;
6. built-wheel identity, reference smoke, full registered TCK profiles, and release-evidence gates pass on the exact candidate head;
7. no implementation correction changes normative spec, schemas, or TCK expectations merely to make the reference runtime pass.

## Findings

### RRA-001 — HTTP release identity drift

Status: **RESOLVED**

The optional FastAPI application previously exposed a stale hard-coded application version while the distribution, `avp_ref.__version__`, and `ReferenceRuntime` implementation identity used `0.3.0rc1`.

PR #54 bound the HTTP application version to the distribution single source of truth and added regression coverage. The PR passed exact-head Quality, Governance, installed-wheel full TCK conformance, and release-evidence gates before squash merge as `4376dde904d37925bf6cf2970922748629ca567c`.

### RRA-002 — ambiguous runtime profile claims

Status: **RESOLVED**

The public runtime discovery surface previously exposed a `profiles` array containing legacy implementation labels that were neither registered TCK profile identifiers nor validated conformance evidence.

PR #55 removed that self-claim from the public runtime boundary without changing execution-engine behavior or replacing it with a list of current TCK profiles. TCK conformance remains represented by validated `ConformanceReport` output. The remediation passed exact-head Quality, Governance, Release Validation, built-wheel full TCK conformance, and release-evidence gates before squash merge as `de8fa1c61d94924f63c173fe4f8ea1cdaff73899`.

### RRA-003 — OpenTelemetry release identity drift

Status: **BLOCKING — REMEDIATION CANDIDATE**

The public `OpenTelemetryBridge` implementation still inherited hard-coded `0.2.0-alpha.5` identity in two consumer-visible places:

- `TelemetryDescription.version` returned by `OpenTelemetryBridge.describe()`;
- the OpenTelemetry tracer instrumentation scope version attached to exported spans.

The reference distribution version is owned by `avp_ref._version.__version__` and is currently `0.3.0rc1`. A release-specific bridge identity that drifts from the installed distribution makes telemetry provenance ambiguous and can cause consumers to attribute spans to a stale reference-runtime release.

Remediation rule:

- the public OpenTelemetry bridge release identity MUST use the reference distribution single source of truth;
- both `TelemetryDescription.version` and tracer instrumentation scope version MUST match `avp_ref.__version__`;
- OTel mapping semantics, TCK expectations, telemetry policy, and protocol requirements MUST remain unchanged;
- no claim of `avp-otel-mapping-v0.1` conformance is inferred from the implementation version.

The current remediation candidate applies this at the public telemetry boundary while preserving the underlying bridge execution behavior.

## TCK adapter audit notes

The current reference TCK architecture dispatches registered cases through domain adapters. Mandatory and mixed cases cannot be reported as `SKIP`; conditional cases require an explicit capability condition. The reviewed Core, Evidence, Subject, MCP, OpenTelemetry, and Artifact Trust paths exercise reference implementation behavior rather than simply returning portable expectations unchanged.

The current CI package job installs the built wheel into a clean conformance environment and executes every registered TCK profile. This remains a required gate for every runtime-alignment remediation candidate.

## Remaining scope

After RRA-003 is resolved on `main`, continue the audit from the new exact baseline. The next explicit review area is the consumer-visible `features` map, which currently mixes static implementation support, configured-instance state, protocol identifiers, and profile-like labels. That claim-level review is intentionally excluded from RRA-003 so release-identity correction remains independently auditable.

Other remaining areas include implementation-only convenience behavior, packaging/runtime boundaries, and any mandatory normative requirement not genuinely exercised by the reference implementation path.

Reference Runtime Alignment is not yet READY, and this audit does not authorize stable `v0.3.0` publication.

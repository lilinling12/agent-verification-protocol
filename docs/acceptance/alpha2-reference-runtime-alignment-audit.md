# Alpha 2 Reference Runtime Alignment Audit

Status: **BLOCKED — RRA-004 UNDER REMEDIATION**

Audit baseline: `main@7666c9b04922bbc5696f1983393d8a9247f0238c`

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

Status: **RESOLVED**

The public `OpenTelemetryBridge` previously inherited hard-coded `0.2.0-alpha.5` release identity in both `TelemetryDescription.version` and exported span instrumentation scope metadata.

PR #56 bound both surfaces to the `avp-reference` distribution version without changing telemetry mapping semantics, TCK expectations, or policy. The remediation passed exact-head Quality, Governance, built-wheel full TCK conformance, and release-evidence gates before squash merge as `7666c9b04922bbc5696f1983393d8a9247f0238c`.

### RRA-004 — runtime discovery claim levels

Status: **BLOCKING — REMEDIATION CANDIDATE**

The public runtime discovery `features` map currently mixes materially different claim levels:

- implementation/API support, such as Environment and Subject adapter SPI identifiers;
- implementation interoperability metadata, such as the MCP protocol version;
- configured-instance state, such as the selected Oracle runner SPI and whether telemetry is actually configured;
- profile-like labels, including `avp-oracle-v0.1` and `avp-evidence-v0.1`, which are registered TCK profile identifiers rather than runtime configuration;
- broad labels such as `isolation: adapter-dependent`, whose meaning is not precise enough to distinguish implementation support from a verified runtime guarantee.

The default `ReferenceRuntime()` is created with no telemetry bridge, yet the current public discovery document still reports a telemetry feature string. This can cause consumers to interpret code availability as active instance configuration. Profile-like labels can similarly be mistaken for conformance evidence even though TCK conformance is represented only by validated `ConformanceReport` output.

Remediation rule:

- public runtime discovery MUST separate static implementation support from current instance configuration;
- registered TCK profile identifiers MUST NOT be used as runtime self-claims;
- optional configured components MUST reflect the actual runtime instance rather than package availability;
- broad implementation notes MUST NOT be presented as stronger protocol or security guarantees than they represent;
- TCK profile identity and conditional capabilities remain explicit conformance-runner inputs and validated report output;
- execution-engine behavior, normative specification, schemas, and TCK expectations MUST remain unchanged.

The current remediation candidate applies this normalization only at the public `avp_ref.runtime.ReferenceRuntime` boundary. It replaces the ambiguous `features` map with explicit `implementation_features` and `instance_configuration` sections while preserving implementation identity and protocol/version metadata.

## TCK adapter audit notes

The current reference TCK architecture dispatches registered cases through domain adapters. Mandatory and mixed cases cannot be reported as `SKIP`; conditional cases require an explicit capability condition. The reviewed Core, Evidence, Subject, MCP, OpenTelemetry, and Artifact Trust paths exercise reference implementation behavior rather than simply returning portable expectations unchanged.

`TCKRunner.for_reference()` consumes only the runtime `implementation` identity from discovery. It receives the selected TCK profile and declared conditional capabilities separately, so the RRA-004 discovery normalization does not alter conformance applicability or report semantics.

The current CI package job installs the built wheel into a clean conformance environment and executes every registered TCK profile. This remains a required gate for every runtime-alignment remediation candidate.

## Remaining scope

After RRA-004 is resolved on `main`, continue domain-by-domain reference-runtime alignment review for implementation-only convenience behavior, packaging/runtime boundaries, optional component wiring, and any mandatory normative requirement not genuinely exercised by the reference implementation path.

Reference Runtime Alignment is not yet READY, and this audit does not authorize stable `v0.3.0` publication.

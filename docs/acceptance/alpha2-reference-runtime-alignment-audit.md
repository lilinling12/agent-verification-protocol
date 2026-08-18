# Alpha 2 Reference Runtime Alignment Audit

Status: **BLOCKED — RRA-005 UNDER REMEDIATION**

Audit baseline: `main@c65ab1a3400ed6513eab68c4999164d95fcb1aae`

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

Status: **RESOLVED**

The public runtime discovery `features` map mixed static implementation support, interoperability metadata, configured-instance state, registered TCK profile identifiers, and broad isolation labels. The default runtime also advertised a telemetry feature even when no telemetry bridge was configured.

PR #57 normalized only the public runtime boundary. Static implementation support now lives under `implementation_features`; actual Oracle/telemetry configuration lives under `instance_configuration`; profile-like self-claims and the ambiguous isolation label were removed. `TCKRunner.for_reference()` continues to consume only implementation identity. The remediation passed exact-head Quality, Governance, built-wheel full TCK conformance, release-evidence, and Ready-transition Governance gates before squash merge as `c65ab1a3400ed6513eab68c4999164d95fcb1aae`.

### RRA-005 — public discovery version scope drift

Status: **BLOCKING — REMEDIATION CANDIDATE**

The public runtime discovery document still exposes a top-level `version: avp.spec/v0.1` alongside `protocol: avp`.

`avp.spec/v0.1` is the current Scenario document `apiVersion` vocabulary in the machine-readable ScenarioInstance contract. The current normative AVP surface is composed of multiple governed domains and TCK profiles; there is no accepted specification that promotes this Scenario document identifier into a single global AVP runtime, protocol, or conformance version.

Because `/.well-known/avp` returns this discovery document directly, a consumer can reasonably interpret the top-level `version` as a whole-AVP protocol/conformance version. That exceeds the authority of the identifier and conflates document vocabulary support with protocol conformance.

Remediation rule:

- public runtime discovery MUST NOT expose `avp.spec/v0.1` as a global AVP protocol/conformance version;
- the reference implementation MAY report the Scenario API vocabulary it supports, but the field MUST be scoped explicitly as implementation/document support metadata;
- implementation distribution identity remains under `implementation.version` and validated TCK conformance remains represented by `ConformanceReport` output;
- `protocol: avp` MAY remain as a non-versioned discovery discriminator;
- execution-engine behavior, Episode manifest identity, normative specification, schemas, and TCK expectations MUST remain unchanged in this remediation.

The current remediation candidate removes the ambiguous public top-level `version` and relabels the same engine-provided value as `implementation_features.scenario_api_version`. It does not invent a replacement global protocol version.

## TCK adapter audit notes

The current reference TCK architecture dispatches registered cases through domain adapters. Mandatory and mixed cases cannot be reported as `SKIP`; conditional cases require an explicit capability condition. The reviewed Core, Evidence, Subject, MCP, OpenTelemetry, and Artifact Trust paths exercise reference implementation behavior rather than simply returning portable expectations unchanged.

`TCKRunner.for_reference()` consumes only the runtime `implementation` identity from discovery. It receives the selected TCK profile and declared conditional capabilities separately, so discovery metadata normalization does not alter conformance applicability or report semantics.

The current CI package job installs the built wheel into a clean conformance environment and executes every registered TCK profile. This remains a required gate for every runtime-alignment remediation candidate.

## Remaining scope

After RRA-005 is resolved on `main`, continue the alignment audit independently for:

- Episode manifest version-label semantics, including whether the current `protocol_version` field is correctly scoped to Scenario document vocabulary; any correction must account for manifest-digest and replay-evidence impact;
- bundled component identity/versioning, including Oracle runner and reference adapter component versions, without assuming every component must equal the distribution version;
- development distribution identity after the immutable `v0.3.0-rc.1` source point, including whether current post-RC fixes require a separately governed prerelease/development version before publication;
- implementation-only convenience behavior, packaging/runtime boundaries, optional component wiring, and any mandatory normative requirement not genuinely exercised by the reference implementation path.

Reference Runtime Alignment is not yet READY, and this audit does not authorize stable `v0.3.0` publication.

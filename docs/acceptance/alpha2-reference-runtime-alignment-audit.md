# Alpha 2 Reference Runtime Alignment Audit

Status: **BLOCKED — RRA-006 UNDER REMEDIATION**

Audit baseline: `main@abee72c93c5caf5ccb9d66d67e60b2dad9e1d1f5`

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

Status: **RESOLVED**

The public runtime discovery document previously exposed a top-level `version: avp.spec/v0.1` alongside `protocol: avp`, even though `avp.spec/v0.1` identifies the Scenario document `apiVersion` vocabulary rather than one accepted global AVP protocol or conformance version.

PR #58 removed the ambiguous top-level version claim at the public runtime boundary and relabeled the same value as `implementation_features.scenario_api_version`. It did not invent a replacement global protocol version or alter execution-engine, manifest, normative specification, schema, or TCK semantics. The remediation passed exact-head Quality, Governance, built-wheel full TCK conformance, release-evidence, and Ready-transition Governance gates before squash merge as `abee72c93c5caf5ccb9d66d67e60b2dad9e1d1f5`.

### RRA-006 — Episode manifest version-label identity drift

Status: **BLOCKING — REMEDIATION CANDIDATE**

`EpisodeManifest.protocol_version` currently stores `ScenarioInstance.document["apiVersion"]`, whose current value is `avp.spec/v0.1`. As established by RRA-005, that value identifies the Scenario document vocabulary and is not an accepted global AVP protocol or conformance version.

This is more than a display-label problem:

- `EpisodeManifest` is exported as a public reference-runtime API;
- the field is serialized as `protocol_version` by `to_dict()`;
- the serialized key/value participates in `manifest_digest`;
- replay source identity binds the source Episode's exact `manifest_digest`;
- `ScenarioInstance` construction already validates the schema, so `apiVersion` is required before a manifest can be created and the manifest's hard-coded fallback is unnecessary.

Core replay semantics require a new Episode identity and an explicit source Episode reference. The registered replay TCK does not standardize the reference-runtime manifest shape or its field names. The reviewed `AlignedReferenceTCKAdapter` genuinely exercises `create_replay_episode()` and verifies the source Episode and manifest identity without making the manifest wire shape normative.

Remediation rule:

- the reference manifest MUST name the Scenario document vocabulary according to its actual scope, not as a whole-AVP protocol version;
- `scenario_api_version` MUST be copied from the already validated `ScenarioInstance.apiVersion` without a silent implementation fallback;
- the serialized manifest identity MUST use the corrected `scenario_api_version` key;
- because the key participates in `manifest_digest`, this remediation intentionally defines a new reference-manifest identity format: the legacy and corrected shapes MUST NOT share one digest;
- replay MUST continue to bind the exact source manifest digest generated by the active reference-manifest format;
- no compatibility alias is added solely to preserve the pre-release reference-runtime field name;
- normative specification, schemas, Core replay requirements, and TCK expectations MUST remain unchanged.

The current remediation candidate applies only to the non-normative reference-runtime manifest and its implementation tests. It renames `protocol_version` to `scenario_api_version`, removes the fallback, and adds regression coverage proving that the corrected serialization is identity-bound and digest-distinct from the legacy key shape.

## TCK adapter audit notes

The current reference TCK architecture dispatches registered cases through domain adapters. Mandatory and mixed cases cannot be reported as `SKIP`; conditional cases require an explicit capability condition. The reviewed Core, Evidence, Subject, MCP, OpenTelemetry, and Artifact Trust paths exercise reference implementation behavior rather than simply returning portable expectations unchanged.

`TCKRunner.for_reference()` consumes only the runtime `implementation` identity from discovery. It receives the selected TCK profile and declared conditional capabilities separately, so runtime/manifest metadata normalization does not alter conformance applicability or report semantics.

The lifecycle replay case is owned by `AlignedReferenceTCKAdapter`, which invokes the actual `create_replay_episode()` helper and validates new Episode identity, source Episode identity, source manifest identity, and non-mutation of the source Episode. RRA-006 therefore does not require a TCK expectation change.

The current CI package job installs the built wheel into a clean conformance environment and executes every registered TCK profile. This remains a required gate for every runtime-alignment remediation candidate.

## Remaining scope

After RRA-006 is resolved on `main`, continue the alignment audit independently for:

- bundled component identity/versioning, including Oracle runner and reference adapter component versions, without assuming every component must equal the distribution version;
- development distribution identity after the immutable `v0.3.0-rc.1` source point, including whether current post-RC fixes require a separately governed prerelease/development version before publication;
- implementation-only convenience behavior, packaging/runtime boundaries, optional component wiring, and any mandatory normative requirement not genuinely exercised by the reference implementation path.

Reference Runtime Alignment is not yet READY, and this audit does not authorize stable `v0.3.0` publication.

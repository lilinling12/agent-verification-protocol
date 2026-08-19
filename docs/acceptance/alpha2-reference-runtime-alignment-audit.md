# Alpha 2 Reference Runtime Alignment Audit

Status: **BLOCKED — RRA-007 UNDER REMEDIATION**

Audit baseline: `main@883109ac19481076e24bb65383ecba0798298b61`

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

Status: **RESOLVED**

`EpisodeManifest.protocol_version` previously stored `ScenarioInstance.document["apiVersion"]`, even though that value identifies the Scenario document vocabulary rather than one global AVP protocol or conformance version. The misleading field name was identity-affecting because the serialized manifest shape participates in `manifest_digest`, and replay binds the exact source manifest digest.

PR #59 renamed the field and serialized key to `scenario_api_version`, removed the unnecessary fallback around the already schema-validated `apiVersion`, explicitly regression-tested the identity-format correction, and preserved replay binding to the active source manifest digest. Normative specification, schemas, Core replay requirements, and TCK expectations were unchanged. The remediation passed exact-head Quality, Governance, built-wheel full TCK conformance, release-evidence, and Ready-transition Governance gates before squash merge as `883109ac19481076e24bb65383ecba0798298b61`.

### RRA-007 — Oracle runner release identity drift

Status: **BLOCKING — REMEDIATION CANDIDATE**

The bundled `SubprocessOracleRunner` currently reports `version="0.2.0-alpha.8"` while the installed `avp-reference` distribution derives its release identity from `avp_ref.__version__` (`0.3.0rc1` on this audit baseline).

The runner version is not the Oracle runner SPI/wire-protocol version. That concern already has a separate `protocol_version` field whose value is `avp.oracle/v2`. The stale `version` therefore identifies the reference implementation component rather than the interoperability protocol it speaks.

This stale release identity is also identity-bearing rather than display-only:

- `SubprocessOracleRunner.describe()` places the value in `OracleRunnerDescription.version`;
- `OracleRunnerDescription.identity_digest` hashes `version` separately from `protocol_version` together with policy, worker module/code digest, allowlist, and isolation properties;
- `ReferenceRuntime.create_episode()` places that digest into `EpisodeManifest.oracle_runner_config_digest`;
- the Episode manifest itself is identity-bound through `manifest_digest`;
- Oracle execution artifacts also record the current runner configuration digest.

Repository release policy states that reference-runtime implementation changes continue to follow the repository release version until protocol and implementation artifacts are versioned independently. There is no independently packaged/versioned Oracle runner artifact in the current repository. Leaving the runner on an old alpha release label therefore lets one installed reference distribution produce identity evidence that claims a different implementation release.

Remediation rule:

- the bundled `SubprocessOracleRunner` implementation `version` MUST use the reference distribution single source of truth, `avp_ref.__version__`;
- `protocol_version` MUST remain the independent `avp.oracle/v2` interoperability identifier and MUST NOT be relabeled as a package release version;
- the runner identity digest MUST continue binding policy, worker code, allowlist, isolation, implementation release identity, and protocol version;
- the resulting runner configuration digest change is intentional because the old digest encoded stale implementation-release identity;
- no normative Oracle requirements, schemas, TCK cases, or runner protocol frames change in this remediation.

The current remediation candidate imports the distribution version as the runner implementation version and adds regression coverage proving both concerns remain distinct and that substituting the stale release label changes `identity_digest`.

This audit does **not** mechanically bind every nested component label to the package version. In particular, the in-memory Commerce Environment Adapter currently pairs `version="0.2.0"` with the explicitly supported resource identifier `env://commerce-reference@0.2.0`. That value may represent a fixture/resource contract rather than distribution release identity and is not changed by RRA-007. Any additional component-version finding requires its own semantic evidence.

## TCK adapter audit notes

The current reference TCK architecture dispatches registered cases through domain adapters. Mandatory and mixed cases cannot be reported as `SKIP`; conditional cases require an explicit capability condition. The reviewed Core, Evidence, Subject, MCP, OpenTelemetry, Artifact Trust, and Oracle paths exercise reference implementation behavior rather than simply returning portable expectations unchanged.

`TCKRunner.for_reference()` consumes only the runtime `implementation` identity from discovery. It receives the selected TCK profile and declared conditional capabilities separately, so implementation-component identity corrections do not alter conformance applicability or report semantics.

The lifecycle replay case is owned by `AlignedReferenceTCKAdapter`, which invokes the actual `create_replay_episode()` helper and validates new Episode identity, source Episode identity, source manifest identity, and non-mutation of the source Episode. RRA-006 therefore did not require a TCK expectation change.

The current CI package job installs the built wheel into a clean conformance environment and executes every registered TCK profile. This remains a required gate for every runtime-alignment remediation candidate.

## Remaining scope

After RRA-007 is resolved on `main`, continue the alignment audit independently for:

- development distribution identity after the immutable `v0.3.0-rc.1` source point, including whether current post-RC fixes require a separately governed prerelease/development version before publication;
- any remaining bundled-component identity semantics where evidence shows a release-identity defect, without assuming resource/API/component versions must equal the distribution version;
- implementation-only convenience behavior, packaging/runtime boundaries, optional component wiring, and any mandatory normative requirement not genuinely exercised by the reference implementation path.

Reference Runtime Alignment is not yet READY, and this audit does not authorize stable `v0.3.0` publication.

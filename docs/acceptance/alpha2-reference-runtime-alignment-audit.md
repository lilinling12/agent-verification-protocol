# Alpha 2 Reference Runtime Alignment Audit

Status: **BLOCKED — RRA-008 REQUIRES VERSION-POLICY DECISION**

Audit baseline: `main@f41a409e6296c7590bbedaa7e2157ec3176d5b1b`

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
7. development and published distribution identities cannot ambiguously bind one public version to multiple source revisions;
8. no implementation correction changes normative spec, schemas, or TCK expectations merely to make the reference runtime pass.

## Findings

### RRA-001 — HTTP release identity drift

Status: **RESOLVED**

PR #54 bound the optional FastAPI application version to the distribution single source of truth and added regression coverage. It passed exact-head Quality, Governance, installed-wheel full TCK conformance, and release-evidence gates before squash merge as `4376dde904d37925bf6cf2970922748629ca567c`.

### RRA-002 — ambiguous runtime profile claims

Status: **RESOLVED**

PR #55 removed legacy runtime profile self-claims from the public discovery boundary without replacing them with current TCK profile assertions. Conformance remains represented by validated `ConformanceReport` output. The remediation merged as `de8fa1c61d94924f63c173fe4f8ea1cdaff73899` after its required gates passed.

### RRA-003 — OpenTelemetry release identity drift

Status: **RESOLVED**

PR #56 bound public OpenTelemetry bridge description and tracer instrumentation-scope identity to the `avp-reference` distribution version without changing telemetry mapping semantics or TCK expectations. The remediation merged as `7666c9b04922bbc5696f1983393d8a9247f0238c`.

### RRA-004 — runtime discovery claim levels

Status: **RESOLVED**

PR #57 separated static implementation support from actual instance configuration and removed profile-like/broad isolation self-claims from consumer discovery. The remediation merged as `c65ab1a3400ed6513eab68c4999164d95fcb1aae`.

### RRA-005 — public discovery version scope drift

Status: **RESOLVED**

PR #58 removed the ambiguous top-level `version: avp.spec/v0.1` runtime claim and scoped the value correctly as Scenario API vocabulary metadata. No replacement global AVP version was invented. The remediation merged as `abee72c93c5caf5ccb9d66d67e60b2dad9e1d1f5`.

### RRA-006 — Episode manifest version-label identity drift

Status: **RESOLVED**

PR #59 renamed the identity-bearing reference manifest field/key from `protocol_version` to `scenario_api_version`, removed the unnecessary fallback around already validated Scenario `apiVersion`, and preserved replay source binding to the exact active manifest digest. The remediation merged as `883109ac19481076e24bb65383ecba0798298b61`.

### RRA-007 — Oracle runner release identity drift

Status: **RESOLVED**

The bundled `SubprocessOracleRunner` previously reported implementation `version="0.2.0-alpha.8"` while its independent runner protocol identity was already represented by `protocol_version="avp.oracle/v2"`. The stale implementation version participated in `OracleRunnerDescription.identity_digest`, which is bound into Episode manifest and Oracle execution provenance.

PR #60 bound the bundled runner implementation version to the `avp-reference` distribution single source of truth while preserving `avp.oracle/v2` as the independent interoperability identifier. It deliberately did not mass-rewrite component/resource versions whose semantics are different. Exact-head CI #440, Governance #475, Ready Governance #476, installed-wheel full TCK conformance, and release-evidence gates passed before squash merge as `f41a409e6296c7590bbedaa7e2157ec3176d5b1b`.

### RRA-008 — post-RC development distribution provenance

Status: **BLOCKING — MAINTAINER VERSION-POLICY DECISION REQUIRED**

The published `v0.3.0-rc.1` release is immutable evidence for one exact source identity:

- tag: `v0.3.0-rc.1`;
- distribution: `avp-reference==0.3.0rc1`;
- exact source commit: `ef199124017b0dcc8c4a966d00c4f407760f9a06`.

The published-release acceptance audit and Release Validation workflow explicitly bind those three identities and reject source, artifact, tag, or release-object substitution.

Current `main@f41a409e6296c7590bbedaa7e2157ec3176d5b1b` is materially later than that immutable source point and includes multiple post-RC reference-runtime and governance corrections, including PRs #54 through #60. However, `src/avp_ref/_version.py` still declares `0.3.0rc1`.

This creates a development provenance collision:

- CI builds wheel/sdist bytes from each current PR/head using the source version `0.3.0rc1`;
- `scripts/release_evidence.py` binds those new bytes and the current `GITHUB_SHA` into a valid `avp-release-evidence/v1` manifest;
- `scripts/validate_release_metadata.py` verifies only intra-build agreement among source version, package metadata, installed distribution, and runtime identity;
- neither validator distinguishes the immutable already-published `0.3.0rc1@ef199124...` identity from a new post-RC source revision also labeled `0.3.0rc1`.

The generated CI bundles are not themselves published releases, so existing published `v0.3.0-rc.1` evidence remains valid. The blocker is that the repository currently permits post-RC source to produce publishable-looking artifacts/evidence under an already published version identity. Any accidental publication of those artifacts would violate the repository rule that release tags are immutable and defective releases require a new version rather than source substitution.

The changelog also previously claimed that no changes had been recorded after `v0.3.0-rc.1`, despite substantial merged post-RC changes. That record is corrected independently because it does not require choosing a new version.

#### Required decision boundary

A safe remediation MUST establish a distinct development/release identity before any post-RC artifact can be published, but the repository currently does not define which identity scheme to use. Therefore this audit does **not** invent one.

Maintainer policy must explicitly choose and document one future-version strategy, for example a governed next prerelease or a governed PEP 440 development-version convention. The exact identifier is intentionally undecided here.

The decision must preserve all of the following:

- `v0.3.0-rc.1` and `0.3.0rc1` remain permanently bound to `ef199124017b0dcc8c4a966d00c4f407760f9a06` and its published bytes;
- current/post-RC source must not be publishable under that same distribution version;
- CI development artifacts must remain reproducible and identity-consistent;
- release evidence must continue binding exact repository, commit, distribution version, filenames, sizes, and digests;
- a stable `v0.3.0` decision remains separate and is not authorized by resolving this blocker;
- no normative specification, schema, or TCK semantic change is implied by the version-policy decision.

Until that policy is explicitly decided and implemented, Reference Runtime Alignment remains BLOCKED rather than assigning a guessed `rc2`, `.devN`, or stable version.

## TCK adapter audit notes

The current reference TCK architecture dispatches registered cases through domain adapters. Mandatory and mixed cases cannot be reported as `SKIP`; conditional cases require an explicit capability condition. Reviewed Core, Evidence, Subject, MCP, OpenTelemetry, Artifact Trust, Oracle, and replay paths exercise reference behavior rather than rewriting expected results into passes.

`TCKRunner.for_reference()` consumes only the runtime implementation identity from discovery. Selected profiles and declared conditional capabilities remain explicit runner inputs, so the RRA-008 distribution-version policy does not alter protocol applicability or TCK semantics.

The CI package job installs the built wheel into clean consumer/conformance environments and executes every registered TCK profile. That remains required for any eventual RRA-008 implementation candidate.

## Remaining scope

After RRA-008 is resolved by an explicit version-policy decision and implementation, continue independently for:

- any remaining bundled-component identity semantics where evidence demonstrates an actual release-identity defect, without assuming resource/API/component versions must equal the distribution version;
- implementation-only convenience behavior, packaging/runtime boundaries, optional component wiring, and any mandatory normative requirement not genuinely exercised by the reference implementation path;
- final Reference Runtime Alignment acceptance before any separate stable `v0.3.0` release decision.

Reference Runtime Alignment is not yet READY. This audit does not authorize stable `v0.3.0`, a next release candidate, a development-version identifier, package-index publication, or merge of its own remediation PR.

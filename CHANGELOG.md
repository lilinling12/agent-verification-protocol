# Changelog

All notable changes to AVP protocol candidates, conformance assets, and the reference implementation are recorded here. Release entries are created from `main` during the release process; development work remains under **Unreleased** until a tag is published.

## Unreleased

### Reference implementation
- Bound the optional FastAPI application version to the installed `avp-reference` distribution identity.
- Removed ambiguous runtime profile self-claims and separated static implementation features from actual instance configuration in public runtime discovery.
- Scoped Scenario API vocabulary metadata correctly instead of exposing it as a whole-AVP runtime/protocol version.
- Corrected `EpisodeManifest` identity labeling from `protocol_version` to `scenario_api_version`, preserving exact replay source binding while intentionally changing the reference-manifest digest format.
- Bound OpenTelemetry bridge/tracer release identity and bundled subprocess Oracle runner implementation identity to the reference distribution version while preserving their independent protocol identifiers.

### Protocol and conformance
- Closed the Alpha 2 Normative Surface Closure audit without changing accepted normative semantics, schemas, or TCK expectations.
- Finalized AEP-0001 through AEP-0008 after the recorded maintainer decision and released `v0.3.0-rc.1` evidence; this does not authorize stable `v0.3.0` publication.

### Repository engineering
- Continued the Reference Runtime Alignment Audit through RRA-007 with exact-head Quality, Governance, installed-wheel full TCK, and release-evidence gates.
- Identified a post-RC development provenance blocker: current `main` contains material changes after the immutable `v0.3.0-rc.1` source commit while still declaring package version `0.3.0rc1`. A separately governed development/prerelease version policy decision is required before publishing any new artifacts from post-RC source.

## [0.3.0-rc.1] - 2026-08-16

First public AVP release candidate. Git tag `v0.3.0-rc.1` binds exact source commit `ef199124017b0dcc8c4a966d00c4f407760f9a06`; the GitHub Release is a prerelease and is not a stable conformance target.

### Protocol and conformance
- Established repository authority boundaries between specifications, schemas, TCK assets, and the non-normative reference implementation.
- Added the Episode lifecycle normative candidate and language-independent, registry-backed TCK architecture.
- Added the Evidence/Artifact identity candidate and the `avp-evidence-v0.1` conformance profile.
- Added the Oracle evaluation/failure contract and `avp-oracle-v0.1` conformance profile, preserving evaluator verdict authority and explicit execution-failure separation.
- Added the Security boundary/assurance contract and `avp-security-v0.1` profile, separating API capability guarantees from stronger deployment isolation claims.
- Added the ScenarioTemplate/ScenarioInstance v0.1 contract and `avp-scenario-v0.1` conformance profile, including deterministic materialization, fail-closed unresolved inputs, Subject projection confidentiality, and strict external-reference identity binding.
- Defined ScenarioInstance identity as SHA-256 over RFC 8785 JCS canonical bytes with only top-level `instanceDigest` and non-semantic `provenance` excluded from the identity preimage.
- Added the Environment v0.1 contract and `avp-environment-v0.1` conformance profile for portable lifecycle, observation, snapshot/restore, time, fault, projection, and semantic-diff behavior without standardizing one environment backend.
- Added the MCP Tools interoperability profile and `avp-mcp-interop-v0.1` TCK, preserving MCP ownership of tool protocol semantics while AVP verifies identity, capability, schema-drift, revision, result, and upstream-failure boundaries.
- Added the OpenTelemetry mapping profile and `avp-otel-mapping-v0.1` TCK for trace/event/evidence correlation, propagation, outcome preservation, data minimization, and completeness without redefining W3C Trace Context or OpenTelemetry semantics.
- Added the Subject Adapter interoperability contract and `avp-subject-v0.1` TCK for adapter/Agent identity binding, Subject projection, evaluator-owned budgets, controlled capabilities, terminal outcome separation, stale-handle rejection, and assurance honesty while keeping transport syntax non-normative.
- Added the Artifact Trust / attestation contract and `avp-artifact-trust-v0.1` TCK, separating exact-byte Artifact integrity, authenticated attestation content, authenticated signer identity, evaluator-owned trust policy, fail-closed outcomes, and optional privileged publication.
- Kept generic signature/envelope cryptography, PKI, key management, transparency, revocation/timestamp services, registry transport, and domain-specific attestation predicates outside AVP Core ownership.

### Reference implementation
- Added Environment and Subject adapter boundaries, MCP verification, OpenTelemetry correlation, and subprocess-isolated Oracle execution.
- Aligned lifecycle transition records and replay source identity with the current Core candidate.
- Added content-addressed ArtifactStore implementations and migrated Runtime Evidence onto immutable Artifact references.
- Aligned the Scenario compiler with the v0.1 schema split and identity contract, including declared-digest verification, immutable ScenarioInstance construction, resolver request/response binding checks, and the six-case Scenario reference TCK adapter.
- Added `rfc8785` as the reviewed JCS implementation dependency and verified Scenario behavior from built wheels in an unconstrained clean environment.
- Added Environment, MCP, OpenTelemetry, Subject, and Artifact Trust reference TCK adapters that exercise portable vectors against observable reference behavior rather than treating case identifiers as pass tokens.
- Added HTTP Subject Adapter hardening for execution-target/configuration identity, credential-bearing URL rejection, evaluator metadata minimization, typed failure separation, and completion-only results.
- Added reference Artifact Trust verifier/publisher boundaries with a deliberately non-normative deterministic authentication fixture; authentication failures sanitize unauthenticated identity/type claims instead of exposing them as authenticated result fields.
- Kept production signed/attested Artifact publication optional: the in-process reference publisher does not claim Subject credential-context isolation that it cannot demonstrate.

### Repository engineering
- Added machine-enforced governance, pinned GitHub Actions, package verification, and reproducible CI dependency resolution with an unconstrained downstream wheel check.
- Made `scenario-template.schema.json` the ScenarioTemplate validation authority while retaining `scenario.schema.json` only as an exact compatibility mirror, with repository/package parity enforced by CI.
- Expanded spec/requirement/TCK traceability and registry validation across the Alpha 2 profiles.
- Extended Package / Python 3.13 validation to build distributions, validate metadata, install the wheel in a clean unconstrained environment, verify installed-wheel identity, and execute reference/TCK smoke checks from the installed artifact.
- Prepared and published `v0.3.0-rc.1` with PEP 440 package version `0.3.0rc1`, exact-source release evidence, SHA-256 digests, and clean installed-wheel validation across every registered TCK profile.

### Security
- Preserved the Subject/Evaluator authority boundary and fail-closed evaluator validity semantics across Oracle, telemetry, Evidence integrity, Subject execution, and Artifact Trust failures.
- Kept Scenario Subject projection compatible with Security hidden-material, capability, and future-fault secrecy requirements without claiming stronger process/network/sandbox isolation.
- Required Subject Adapter transport/isolation claims to remain bounded by demonstrated SecurityAssurance evidence.
- Prevented unauthenticated signer hints, labels, locators, or failed authentication observations from becoming authoritative Artifact Trust identity.
- Kept signing credentials and equivalent privileged trust material outside the Subject execution context and made publication assurance conditional rather than implied by an in-process API.
- Prevented OpenTelemetry mappings from requiring protected raw prompts, tool payloads, evaluator secrets, hidden Oracle material, or future fault schedules for conformance.

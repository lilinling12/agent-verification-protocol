# Changelog

All notable changes to AVP protocol candidates, conformance assets, and the reference implementation are recorded here. Release entries are created from `main` during the release process; development work remains under **Unreleased** until a tag is published.

## Unreleased

### Reference implementation
- Bound the optional FastAPI application version to the installed `avp-reference` distribution identity.
- Removed ambiguous runtime profile self-claims and separated static implementation features from actual instance configuration in public runtime discovery.
- Scoped Scenario API vocabulary metadata correctly instead of exposing it as a whole-AVP runtime/protocol version.
- Corrected `EpisodeManifest` identity labeling from `protocol_version` to `scenario_api_version`, preserving exact replay source binding while intentionally changing the reference-manifest digest format.
- Bound OpenTelemetry bridge/tracer release identity and bundled subprocess Oracle runner implementation identity to the reference distribution version while preserving their independent protocol identifiers.
- Changed the mandatory Core normal-path reference TCK probe to execute the actual Episode lifecycle and validate runtime-produced transition records and terminal state instead of passing from the transition relation alone.

### Protocol and conformance
- Closed the Alpha 2 Normative Surface Closure audit without changing accepted normative semantics, schemas, or TCK expectations.
- Finalized AEP-0001 through AEP-0008 after the recorded maintainer decision and released `v0.3.0-rc.1` evidence; this does not authorize stable `v0.3.0` publication.

### Repository engineering
- Continued the Reference Runtime Alignment Audit through RRA-008, including a governed `0.3.0rc2.dev0` post-RC development identity that prevents reuse of the immutable published `0.3.0rc1` identity.
- Opened RRA-009 to ensure the mandatory Core normal-path conformance result is backed by real runtime execution rather than implementation-internal transition-table inspection.

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

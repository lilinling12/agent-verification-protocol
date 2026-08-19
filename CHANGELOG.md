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
- Completed the Reference Runtime Alignment Audit through RRA-009, including the governed `0.3.0rc2.dev0` post-RC development identity and mandatory Core normal-path runtime-execution evidence.
- Re-reviewed all registered reference TCK adapters and the installed-wheel all-profile gate without finding an additional evidence-backed implementation-alignment blocker; stable `v0.3.0`, `v0.3.0-rc.2`, and package-index publication remain separate maintainer decisions.
- Added a fail-closed published-release ledger and explicit development/release provenance states so future RC or stable release commits can be selected without disabling post-release version-identity protection.
- Generalized the published-release Actions path so future prerelease or stable GitHub Releases can be validated from explicit tag/commit/version/class inputs while pull requests continue to regression-test immutable RC1 bytes.

## [0.3.0-rc.1] - 2026-08-16

First public AVP release candidate. Git tag `v0.3.0-rc.1` binds exact source commit `ef199124017b0dcc8c4a966d00c4f407760f9a06`; the GitHub Release is a prerelease and is not a stable conformance target.

### Protocol and conformance
- Established repository authority boundaries between specifications, schemas, TCK assets, and the non-normative reference implementation.
- Added the Episode lifecycle normative candidate and language-independent, registry-backed TCK architecture.
- Added the Evidence/Artifact identity candidate and the `avp-evidence-v0.1` conformance profile.
- Added the Oracle evaluation/failure contract and `avp-oracle-v0.1` conformance profile, preserving evaluator verdict authority and explicit execution-failure separation.
- Added the Security boundary/assurance contract and `avp-security-v0.1` profile, separating API capability guarantees from stronger deployment isolation claims.
- Added the ScenarioTemplate / ScenarioInstance v0.1 contract and `avp-scenario-v0.1` conformance profile.

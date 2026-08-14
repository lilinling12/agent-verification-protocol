# Changelog

All notable changes to AVP protocol candidates, conformance assets, and the reference implementation are recorded here. Release entries are created from `main` during the release process; development work remains under **Unreleased** until a tag is published.

## Unreleased

### Protocol and conformance
- Established repository authority boundaries between specifications, schemas, TCK assets, and the non-normative reference implementation.
- Added the Episode lifecycle normative candidate and language-independent, registry-backed TCK architecture.
- Added the Evidence/Artifact identity candidate and the `avp-evidence-v0.1` conformance profile.
- Added the ScenarioTemplate/ScenarioInstance v0.1 contract and `avp-scenario-v0.1` conformance profile, including deterministic materialization, fail-closed unresolved inputs, Subject projection confidentiality, and strict external-reference identity binding.
- Defined ScenarioInstance identity as SHA-256 over RFC 8785 JCS canonical bytes with only top-level `instanceDigest` and non-semantic `provenance` excluded from the identity preimage.

### Reference implementation
- Added Environment and Subject adapter boundaries, MCP verification, OpenTelemetry correlation, and subprocess-isolated Oracle execution.
- Aligned lifecycle transition records and replay source identity with the current Core candidate.
- Added content-addressed ArtifactStore implementations and migrated Runtime Evidence onto immutable Artifact references.
- Aligned the Scenario compiler with the v0.1 schema split and identity contract, including declared-digest verification, immutable ScenarioInstance construction, resolver request/response binding checks, and the six-case Scenario reference TCK adapter.
- Added `rfc8785` as the reviewed JCS implementation dependency and verified Scenario behavior from built wheels in an unconstrained clean environment.

### Repository engineering
- Added machine-enforced governance, pinned GitHub Actions, package verification, and reproducible CI dependency resolution with an unconstrained downstream wheel check.
- Made `scenario-template.schema.json` the ScenarioTemplate validation authority while retaining `scenario.schema.json` only as an exact compatibility mirror, with repository/package parity enforced by CI.

### Security
- Preserved the Subject/Evaluator authority boundary and fail-closed evaluator validity semantics across Oracle, telemetry, and Evidence integrity failures.
- Kept Scenario Subject projection compatible with Security hidden-material, capability, and future-fault secrecy requirements without claiming stronger process/network/sandbox isolation.

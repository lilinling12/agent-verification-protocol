# Changelog

All notable changes to AVP protocol candidates, conformance assets, and the reference implementation are recorded here. Release entries are created from `main` during the release process; development work remains under **Unreleased** until a tag is published.

## Unreleased

### Protocol and conformance
- Established repository authority boundaries between specifications, schemas, TCK assets, and the non-normative reference implementation.
- Added the Episode lifecycle normative candidate and language-independent, registry-backed TCK architecture.
- Added the Evidence/Artifact identity candidate and the `avp-evidence-v0.1` conformance profile.

### Reference implementation
- Added Environment and Subject adapter boundaries, MCP verification, OpenTelemetry correlation, and subprocess-isolated Oracle execution.
- Aligned lifecycle transition records and replay source identity with the current Core candidate.
- Added content-addressed ArtifactStore implementations and migrated Runtime Evidence onto immutable Artifact references.

### Repository engineering
- Added machine-enforced governance, pinned GitHub Actions, package verification, and reproducible CI dependency resolution with an unconstrained downstream wheel check.

### Security
- Preserved the Subject/Evaluator authority boundary and fail-closed evaluator validity semantics across Oracle, telemetry, and Evidence integrity failures.

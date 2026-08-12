# Release Process

AVP separates protocol evolution from implementation convenience and treats releases as reproducible protocol evidence points.

## Versioning

Published releases use `MAJOR.MINOR.PATCH` with `v`-prefixed Git tags.

### Before 1.0

AVP is experimental. For `0.y.z` releases:

- `MINOR` may contain explicitly documented breaking normative changes;
- `PATCH` must not intentionally introduce a breaking normative change;
- breaking changes require migration notes and protocol/conformance updates in the same release.

This is stricter operational guidance around Semantic Versioning's pre-1.0 development phase so downstream implementers can distinguish ordinary fixes from protocol revisions.

### 1.0 and later

- `MAJOR`: incompatible normative protocol changes;
- `MINOR`: backward-compatible normative additions;
- `PATCH`: backward-compatible fixes, clarifications, and implementation corrections.

Reference-runtime implementation changes that do not alter protocol semantics still follow the repository release version until protocol and implementation artifacts are versioned independently.

## Release candidates

Use prerelease identifiers for stabilization, for example:

```text
v0.3.0-alpha.1
v0.3.0-beta.1
v0.3.0-rc.1
```

A prerelease is not a stable conformance target unless release notes explicitly say otherwise.

## Release readiness

A release requires:

- all required CI and governance checks green on the release commit;
- protocol schemas and packaged schemas synchronized;
- conformance suite passing from a built wheel, not only an editable checkout;
- changelog/release notes describing normative and non-normative changes separately;
- migration notes for incompatible changes;
- finalized AEP references for normative changes when required;
- security-impact review;
- no unresolved release-blocking issues;
- reproducible artifact digests recorded when release automation supports them.

## Release procedure

1. Select a commit from `main`; do not release an arbitrary feature-branch head.
2. Confirm version metadata, changelog, migration notes, and AEP references.
3. Run the full CI/package/conformance gates.
4. Build source and wheel artifacts in a clean environment.
5. Install the wheel in a fresh environment and run `avp conformance`.
6. Create the release tag and GitHub release only after the selected commit is green.
7. Publish release notes containing protocol impact, compatibility, security notes, and artifact identifiers.
8. Verify the published artifacts before announcing the release.

## Tags

Release tags use:

```text
v0.2.0
v0.3.0-rc.1
v1.0.0
```

Release tags are immutable. If a release is defective, publish a new version; do not move an existing public release tag.

Signed annotated tags are preferred for maintainer-created releases until automated release provenance is established.

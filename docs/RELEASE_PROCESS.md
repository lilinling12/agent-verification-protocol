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

A release candidate MAY contain normative changes whose governing AEPs are `Accepted` rather than `Final` when the purpose of the prerelease is to establish the released protocol/conformance evidence required for Final eligibility. The release notes MUST identify those AEPs and MUST NOT describe them as Final.

After the prerelease has been published and its actual consumer artifacts have passed the required release-acceptance checks, the corresponding AEPs may become technically eligible for an explicit maintainer `Accepted` → `Final` decision under `GOVERNANCE.md`.

A stable release that presents those normative changes as the stable conformance baseline MUST reference the governing AEPs as `Final` before publication. This ordering prevents a lifecycle cycle in which Final requires released evidence while the evidence-producing release would itself require Final first.

### Governed release provenance state

AVP records release provenance in two machine-readable resources:

- `docs/releases/published-releases.json` is the ordered ledger of already-published release identities. Its first entry is the immutable `v0.3.0-rc.1` evidence seed. Later published releases are appended through governed transitions; existing entries are not rewritten.
- `docs/releases/release-development-state.json` records the latest published anchor, the planned next release, the current source version, and whether the repository is in `development` or exact `release` mode.

`scripts/validate_release_development_state.py` validates both resources and the source version from `src/avp_ref/_version.py`.

In `development` mode:

- `latestPublished` MUST equal the final published-ledger entry;
- `sourceVersion` MUST be an unreleased PEP 440 development version;
- ordering MUST satisfy `latestPublished < sourceVersion < nextRelease`;
- `nextRelease` MUST be a valid AVP public release identity with an exact derived tag.

In `release` mode:

- `sourceVersion` MUST equal `nextRelease.version` exactly;
- the selected release MUST be newer than `latestPublished`;
- the public tag is derived from the selected release version;
- RC releases use `vX.Y.Z-rc.N`; stable releases use `vX.Y.Z`.

Entering `release` mode is a release-selection change, not publication authorization. It requires normal review and exact-head gates. Creating a tag or GitHub Release remains a separate maintainer-authorized action.

After a release is published and independently accepted, its exact version/tag/commit/class record is appended to the published ledger. A subsequent governed transition returns the repository to `development` mode with `latestPublished` bound to that ledger tail and a new monotonic unreleased source identity.

### Development identity after a published release

Once a release version has been published, `main` and pull-request builds MUST NOT continue to reuse that published distribution version for materially different source bytes.

The repository source version therefore uses an unreleased PEP 440 development identity that remains strictly newer than the latest published release and strictly older than the planned next release. For the current post-RC1 stabilization state:

```text
0.3.0rc1 < 0.3.0rc2.dev0 < 0.3.0rc2 < 0.3.0
```

This development identity has deliberately narrow meaning:

- it identifies unreleased repository artifacts built after the previous release;
- it does not authorize publication of the planned release;
- it does not authorize stable release publication;
- it does not alter normative protocol semantics or AEP lifecycle state;
- it MUST remain strictly newer than the latest published release and strictly older than the planned next release.

Changing the planned next release is itself a governed release-management decision. A release must never be selected by disabling the provenance validator or by silently reusing a previously published identity.

## Release readiness

Every release requires:

- all required CI and governance checks green on the release commit;
- protocol schemas and packaged schemas synchronized;
- conformance suite passing from a built wheel, not only an editable checkout;
- changelog/release notes describing normative and non-normative changes separately;
- migration notes for incompatible changes;
- AEP references for normative changes with lifecycle state appropriate to the release class;
- security-impact review;
- no unresolved release-blocking issues;
- reproducible artifact digests recorded when release automation supports them.

For a prerelease that is explicitly collecting Final-eligibility evidence, governing normative AEPs MUST be at least `Accepted`; release notes must make the non-Final state explicit.

For a stable release that establishes a stable conformance target, governing normative AEPs MUST be `Final` unless the change does not require an AEP under `GOVERNANCE.md`.

## Release procedure

1. Select a commit from `main`; do not release an arbitrary feature-branch head.
2. Confirm version metadata, changelog, migration notes, AEP references, and lifecycle state appropriate to the intended release class.
3. Enter the governed `release` provenance state so source version, planned version, and planned tag are exact and machine-validated.
4. Run the full CI/package/conformance gates on that exact release-selection commit.
5. Build source and wheel artifacts in a clean environment.
6. Install the wheel in a fresh environment and run `avp conformance` plus the complete registered TCK profile set.
7. Create the release tag and GitHub release only after the selected commit is green and the maintainer explicitly authorizes publication.
8. Publish release notes containing protocol impact, compatibility, security notes, AEP lifecycle state, and artifact identifiers.
9. Verify the published artifacts through the published-release consumer path before announcing the release.
10. Append the accepted published identity to `published-releases.json` and return the repository to a new governed development state before materially different source bytes are produced under another identity.
11. When a prerelease is being used as Final-eligibility evidence, record the external-consumer acceptance result before proposing the corresponding AEP Final transition.

## Tags

Release tags use:

```text
v0.2.0
v0.3.0-rc.1
v1.0.0
```

Release tags are immutable. If a release is defective, publish a new version; do not move an existing public release tag.

Signed annotated tags are preferred for maintainer-created releases until automated release provenance is established.

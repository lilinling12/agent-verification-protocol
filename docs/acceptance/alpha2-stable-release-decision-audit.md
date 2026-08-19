# Alpha 2 Stable v0.3.0 Release Decision Audit

Status: **PASS — ELIGIBLE FOR STABLE RELEASE SELECTION**

Audit baseline:

- repository: `lilinling12/agent-verification-protocol`
- exact `main`: `61177670a199d4536f753f105912fd50f5faa9e7`
- exact-main push CI: run `32299282160` / CI #467 — SUCCESS
- latest published release: `v0.3.0-rc.2`
- latest published source: `9cfbdb7f72b3418aa960100f33845249db73fbcf`
- RC2 public external-consumer acceptance: run `32294651642` / Release Validation #26 — SUCCESS
- current source identity: `0.3.0rc3.dev0`
- next governed release target: `0.3.0` / `v0.3.0`

## Decision

The repository is eligible to enter a separate governed **stable `v0.3.0` release-selection** transition.

This audit does not itself select `0.3.0`, does not enter release mode, and does not authorize creation of the stable tag, GitHub Release, or package-index publication.

## Evidence reviewed

### 1. Protocol and conformance stabilization

Alpha 2 Normative Surface Closure is complete. The repository quality gate reports the normative surface as `READY` with zero blockers across the registered domains, schemas, requirement indexes, and TCK profiles.

Reference Runtime Alignment is complete. Reference-runtime behavior remains downstream of the normative specification and language-neutral TCK rather than defining protocol semantics.

AEP-0001 through AEP-0008 are `Final`, satisfying the stable-release lifecycle requirement for the normative Alpha 2 surface.

### 2. Release-management closure

The earlier stable decision audit identified three release-management blockers:

- **SRD-001:** no fail-closed governed exact release transition state;
- **SRD-002:** published-release validation workflow was hard-coded to RC1;
- **SRD-003:** no public post-RC1 artifact had passed the external-consumer acceptance path.

All three are resolved:

- SRD-001 was closed by the governed `development` / `release` provenance state and machine validation.
- SRD-002 was closed by the generalized Release Validation workflow accepting explicit tag/commit/version/class inputs while retaining immutable RC1 regression coverage.
- SRD-003 was closed by published `v0.3.0-rc.2` and successful public external-consumer validation in Release Validation #26 (`32294651642`).

The post-RC2 reconciliation is merged. The published-release ledger now contains immutable RC1 and RC2 entries, `latestPublished` is RC2, and the repository has returned to a distinct development identity instead of reusing the published RC2 version.

### 3. Current release provenance

`docs/releases/release-development-state.json` currently declares:

- `mode = development`;
- `latestPublished = 0.3.0rc2 / v0.3.0-rc.2`;
- `sourceVersion = 0.3.0rc3.dev0`;
- `nextRelease = 0.3.0 / v0.3.0`.

This satisfies the intended monotonic ordering:

`0.3.0rc2 < 0.3.0rc3.dev0 < 0.3.0`

The stable version is therefore an explicit governed next target, not an inferred or silently substituted release identity.

### 4. Exact-main acceptance after post-RC2 reconciliation

The squash-merged reconciliation commit `61177670a199d4536f753f105912fd50f5faa9e7` independently passed push-triggered CI #467 (`32299282160`).

A repository-owned read-only audit verified that the exact run had:

- event `push`;
- branch `main`;
- exact head SHA `61177670a199d4536f753f105912fd50f5faa9e7`;
- completed conclusion `success`;
- Quality jobs successful on Python 3.11, 3.12, and 3.13;
- Package / Python 3.13 successful;
- reproducible distribution-byte verification successful;
- built-wheel metadata validation successful;
- unconstrained clean-consumer installation successful;
- installed-wheel identity verification successful;
- complete registered TCK conformance successful;
- release-evidence build, verification, staging, and upload successful.

The exact-SHA release-evidence artifact is:

`avp-release-evidence-61177670a199d4536f753f105912fd50f5faa9e7`

with Actions artifact digest:

`sha256:5fa950485d5397f26bef1316717efe824e854113bc40f7e11c364501abf99daf`

### 5. RC2 consumer evidence

`v0.3.0-rc.2` was published from exact source `9cfbdb7f72b3418aa960100f33845249db73fbcf` and then independently accepted through the governed public-consumer path.

Release Validation #26 (`32294651642`) verified the public release identity and artifact digests, clean installation of the published wheel, installed runtime identity, and the complete TCK profile set from the exact published source.

This is the required post-RC1 consumer evidence for considering stable selection.

### 6. Release-blocking issue review

The current open issue set contains branch-cleanup maintenance issue #23. It is repository housekeeping and does not affect protocol semantics, release provenance, artifact reproducibility, consumer conformance, or stable-release safety.

No unresolved release-management blocker was identified by this audit.

## Stable selection boundary

A separate stable release-selection PR may now propose all of the following as one governed transition:

1. enter `mode = release`;
2. set `sourceVersion = 0.3.0` exactly;
3. retain `nextRelease.version = 0.3.0` and `nextRelease.tag = v0.3.0`;
4. add stable `v0.3.0` release notes covering protocol impact, compatibility, security, AEP lifecycle state, and artifact expectations;
5. run the normal exact-head CI, package, full-TCK, release-evidence, Release Validation regression, and Governance gates.

The stable selection PR must not be tagged or published from its feature-branch head. If squash-merged, the resulting exact `main` commit must independently pass its push-triggered CI/package/conformance/release-evidence gates before publication can be considered.

## Explicit non-authorizations

This audit does **not** authorize:

- stable `v0.3.0` tag creation;
- GitHub stable Release publication;
- PyPI or any package-index publication;
- signed/attested artifact publication;
- Alpha 3 work;
- bypassing the governed release-state validator;
- weakening CI, schema, TCK, or release validation;
- merging the stable release-selection PR without explicit maintainer authorization.

## Final assessment

**PASS — ELIGIBLE FOR STABLE RELEASE SELECTION**

The previous SRD blockers are resolved, the RC2 public-consumer evidence is successful, the post-RC2 repository state is reconciled and exact-main green, the normative AEP surface is Final, and no current release-blocking issue was found.

The next governed step is stable `v0.3.0` **selection**, not publication.

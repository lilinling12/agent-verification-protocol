# Alpha 2 v0.3.0-rc.1 Release Evidence Gate

Status: **READY FOR REVIEW — NOT AUTHORIZED FOR MERGE, TAG, OR RELEASE**

## 1. Purpose

This stage closes the gap between a green release-candidate commit and auditable release artifacts.

The selected Alpha 2 RC baseline before this evidence mechanism was introduced is:

```text
main@992486e3abd443c1ed02feb96201b70e42adbad3
```

That commit passed post-merge CI #376, including Quality on Python 3.11/3.12/3.13, built distribution validation, an unconstrained base-wheel consumer installation, installed-wheel identity/reference smoke, and full TCK conformance across all 10 registered profiles.

However, CI #376 retained no workflow artifacts. Therefore no authoritative sdist/wheel byte identifiers or SHA-256 digests existed after the run. This gate fixes that release-supply-chain gap rather than inventing digests from logs or treating a successful build as equivalent to retained release evidence.

## 2. Evidence model

The Package job creates a release evidence bundle only after package, reproducibility, and conformance gates succeed.

The bundle contains exactly:

- one Python wheel;
- one source distribution;
- `MANIFEST.json`;
- `SHA256SUMS`.

`MANIFEST.json` uses schema identifier `avp-release-evidence/v1` and binds:

- exact GitHub repository identity;
- exact 40-character workflow source revision;
- distribution name `avp-reference`;
- distribution version from `src/avp_ref/_version.py`;
- filename, kind, byte size, and SHA-256 for each distribution artifact.

`SHA256SUMS` binds both distribution files and the exact `MANIFEST.json` bytes.

The evidence generator rejects:

- branch names or abbreviated commits in place of an exact commit SHA;
- repository identities outside `owner/name` form;
- anything other than exactly one wheel and one source distribution;
- unexpected files in the distribution directory;
- distribution filenames that do not bind the selected package version;
- artifact byte/size changes after evidence generation;
- source identity changes;
- distribution identity changes;
- checksum-file drift.

## 3. Reproducible distribution gate

Before release evidence is created, the Package job derives `SOURCE_DATE_EPOCH` from the checked-out commit timestamp and builds the distributions twice with the same reviewed build environment.

The source distribution is canonicalized only for non-semantic archive metadata before comparison:

- tar member timestamps are set to `SOURCE_DATE_EPOCH`;
- uid/gid are set to `0`;
- uname/gname are cleared;
- PAX headers are cleared;
- the gzip wrapper uses the same epoch and no embedded filename.

File bytes and tar member order are preserved. The wheel is not rewritten.

The second build is written to a separate directory. CI requires:

- exactly two artifacts in each build output;
- identical filenames;
- byte-for-byte equality for the wheel;
- byte-for-byte equality for the canonical source distribution.

A mismatch prints both SHA-256 values and fails the release gate. A digest is therefore not treated as sufficient release evidence unless the same checked-out revision can reproduce the same distribution bytes within the controlled CI build environment.

This is an in-workflow reproducibility check, not a claim that arbitrary external builders on different operating systems or toolchains will necessarily reproduce the same bytes.

## 4. Failure evidence and hardening

The gate was intentionally developed against real CI failures rather than weakened to preserve a green build.

### CI #379

A first double-build check failed at `Verify reproducible distribution bytes` even with `SOURCE_DATE_EPOCH` set. All downstream package/conformance/evidence steps were blocked. This established that the previous build output was not byte-reproducible under the stronger release requirement.

### CI #382

Normalizing only the gzip wrapper was insufficient; reproducibility still failed. The gate remained blocking.

### Resolution

The source-distribution canonicalization was narrowed to non-semantic archive metadata while preserving member content and order. Unit tests explicitly prove that:

- archives with the same content/order but volatile ownership/timestamp/PAX/gzip metadata normalize identically;
- file payload bytes are preserved;
- real file-content drift remains byte-distinct after normalization;
- invalid inputs fail closed.

CI #384 then passed the byte-for-byte reproducibility gate without relaxing wheel or source-distribution comparison.

## 5. Workflow boundary

The evidence mechanism does not replace package validation or conformance.

Ordering is:

1. derive deterministic build epoch from the checked-out revision;
2. build sdist and wheel;
3. canonicalize non-semantic sdist archive metadata;
4. rebuild independently and canonicalize the second sdist;
5. require byte-for-byte equality for both distribution artifacts;
6. validate built-wheel metadata;
7. install the base wheel in a fresh unconstrained consumer environment;
8. verify installed distribution/runtime identity;
9. execute the reference smoke suite;
10. install the same wheel with the declared non-normative `conformance` extra in a separate environment;
11. execute all registered portable TCK profiles;
12. create and verify release evidence;
13. stage only the verified release files;
14. upload the bundle as a GitHub Actions artifact.

The upload uses the official `actions/upload-artifact` action pinned to a full reviewed commit SHA, consistent with repository workflow governance.

## 6. Authority of PR artifacts versus release artifacts

Pull-request workflows run against GitHub's tested merge revision. Therefore the PR evidence manifest intentionally binds the exact tested workflow revision (`GITHUB_SHA`), which may differ from the topic-branch HEAD.

The final implementation validation before this acceptance record used:

```text
PR head:              867d2913e07f247767b2191de2fd95c49e11ed48
GitHub tested merge:  72efcfa9405328d11233845c601f7e6af28147bd
CI:                   #384 / 31913874886 / success
Governance:           #414 / 31913874887 / success
Artifact id:          9254398935
```

The retained PR artifact was independently downloaded and contained exactly:

```text
MANIFEST.json
SHA256SUMS
avp_reference-0.3.0rc1-py3-none-any.whl
avp_reference-0.3.0rc1.tar.gz
```

The independently verified checksums were:

```text
7a42670589a25d9a0768dd5a4a36c4ccbe9af88f6959c8ddffabc37d28fbf570  avp_reference-0.3.0rc1-py3-none-any.whl
4e2b2f86f71122c8a9d79fdb232582aaa7cc8d3f6c05dbc25a2d8446a146b7fd  avp_reference-0.3.0rc1.tar.gz
78e7ea16b60e5c6bd14805c4be4d888c943edd09db6bfc8995754249e7567c7f  MANIFEST.json
```

GitHub additionally reported the uploaded ZIP artifact digest as:

```text
sha256:d23c2dc5bb10fdf7bf8086262cd2455d9dde5e07b331b66b4ad9cbd84c161d5d
```

The manifest bound distribution `avp-reference` version `0.3.0rc1`, repository `lilinling12/agent-verification-protocol`, and tested merge revision `72efcfa9405328d11233845c601f7e6af28147bd`.

These PR artifacts prove the mechanism for the tested PR merge state only. They are **not** the final `v0.3.0-rc.1` release artifacts.

After this PR is separately reviewed and squash-merged, the new exact `main` commit becomes the only eligible RC release commit. Its push CI must succeed and the evidence bundle from that exact `main` push is the only candidate authoritative release artifact set.

A tag must never point to a PR branch HEAD or PR tested-merge revision merely because that revision produced valid evidence.

## 7. Readiness assessment

At the final implementation validation point:

- Quality / Python 3.11: PASS;
- Quality / Python 3.12: PASS;
- Quality / Python 3.13: PASS;
- Package / Python 3.13: PASS;
- double-build wheel/sdist reproducibility: PASS;
- built-wheel metadata validation: PASS;
- unconstrained base-wheel consumer install and `pip check`: PASS;
- installed distribution/runtime identity: PASS;
- reference smoke conformance: PASS;
- separate `[conformance]` wheel environment: PASS;
- all 10 registered portable TCK profiles: PASS;
- evidence build and self-verification: PASS;
- artifact upload and independent checksum verification: PASS;
- exact-head Governance: PASS;
- branch drift: none (`behind_by=0`, merge base is `main@992486e3abd443c1ed02feb96201b70e42adbad3`);
- unresolved review threads: zero;
- open release-blocking issues: zero (issue #23 is repository branch-cleanup hygiene and nonblocking).

Because this acceptance record itself changes the PR HEAD, the final review candidate is valid only after CI and Governance pass again on the new exact HEAD. Ready-for-review metadata must then be rechecked after the Draft transition.

## 8. Tag / release decision boundary

This document and its implementation do **not** authorize:

- merging the evidence PR;
- creating `v0.3.0-rc.1`;
- creating a GitHub Release;
- publishing `avp-reference` to a package index;
- moving any AEP from `Accepted` to `Final`;
- declaring the prerelease a stable conformance target;
- starting Alpha 3 as part of the release action.

After an explicitly authorized squash merge, the exact resulting `main` commit must pass its push CI. The retained bundle from that exact `main` push must then be downloaded and independently checked against `MANIFEST.json` / `SHA256SUMS` before the maintainer can make a separate tag/release authorization decision.

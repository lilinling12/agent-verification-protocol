# Alpha 2 v0.3.0-rc.1 Release Evidence Gate

Status: **IN PROGRESS — NOT AUTHORIZED FOR TAG OR RELEASE**

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

The second build is written to a separate directory. CI requires:

- exactly two artifacts in each build output;
- identical filenames;
- byte-for-byte equality for the wheel;
- byte-for-byte equality for the source distribution.

A mismatch prints both SHA-256 values and fails the release gate. A digest is therefore not treated as sufficient release evidence unless the same checked-out revision can reproduce the same distribution bytes within the controlled CI build environment.

This is an in-workflow reproducibility check, not a claim that arbitrary external builders on different operating systems or toolchains will necessarily reproduce the same bytes.

## 4. Workflow boundary

The evidence mechanism does not replace package validation or conformance.

Ordering is:

1. derive deterministic build epoch from the checked-out revision;
2. build sdist and wheel;
3. rebuild them independently and require byte-for-byte equality;
4. validate built-wheel metadata;
5. install the base wheel in a fresh unconstrained consumer environment;
6. verify installed distribution/runtime identity;
7. execute the reference smoke suite;
8. install the same wheel with the declared non-normative `conformance` extra in a separate environment;
9. execute all registered portable TCK profiles;
10. create and verify release evidence;
11. stage only the verified release files;
12. upload the bundle as a GitHub Actions artifact.

The upload uses the official `actions/upload-artifact` action pinned to a full reviewed commit SHA, consistent with repository workflow governance.

## 5. Authority of PR artifacts versus release artifacts

Pull-request workflows run against GitHub's tested merge revision. Therefore the PR evidence manifest intentionally binds the exact tested workflow revision (`GITHUB_SHA`), which may differ from the topic-branch HEAD.

For PR #35's first evidence run, GitHub tested merge revision `127e894d0a84efd3c7684d657e871270ff7c4490`; the branch HEAD was `1b93af5c373d76a58bb9497ab4ec2e9571fff845`. The downloaded evidence bundle contained exactly four files and all three `SHA256SUMS` entries verified successfully. This proves the mechanism for the tested PR merge state only.

PR artifacts are **not** the final `v0.3.0-rc.1` release artifacts.

After this PR is separately reviewed and squash-merged, the new exact `main` commit becomes the only eligible RC release commit. Its push CI must succeed and the evidence bundle from that exact `main` push is the only candidate authoritative release artifact set.

A tag must never point to a PR branch HEAD or PR tested-merge revision merely because that revision produced valid evidence.

## 6. Required readiness checks

Before this evidence PR can be considered ready for merge:

1. Quality / Python 3.11 succeeds.
2. Quality / Python 3.12 succeeds.
3. Quality / Python 3.13 succeeds.
4. Package / Python 3.13 succeeds.
5. Existing base-wheel and full-profile TCK gates remain green.
6. Release evidence unit tests succeed.
7. The two controlled builds produce byte-identical wheel and sdist files.
8. `MANIFEST.json` and `SHA256SUMS` generation succeeds.
9. Evidence self-verification succeeds before upload.
10. The workflow artifact contains exactly the expected release bundle files.
11. The downloaded artifact independently verifies against `SHA256SUMS`.
12. Governance succeeds on the exact PR HEAD and PR metadata.
13. The PR remains based on the current selected `main` without unresolved drift.
14. There are zero unresolved review threads and no new release-blocking issue.

## 7. Tag / release decision boundary

This document and its implementation do **not** authorize:

- merging the evidence PR;
- creating `v0.3.0-rc.1`;
- creating a GitHub Release;
- publishing `avp-reference` to a package index;
- moving any AEP from `Accepted` to `Final`;
- declaring the prerelease a stable conformance target;
- starting Alpha 3 as part of the release action.

After an explicitly authorized merge, the exact resulting `main` commit must pass its push CI. The retained bundle must then be downloaded and independently checked against `MANIFEST.json` / `SHA256SUMS` before the maintainer can make a separate tag/release authorization decision.

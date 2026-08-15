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

The Package job now creates a release evidence bundle only after all package and conformance gates have succeeded.

The bundle contains exactly:

- one Python wheel;
- one source distribution;
- `MANIFEST.json`;
- `SHA256SUMS`.

`MANIFEST.json` uses schema identifier `avp-release-evidence/v1` and binds:

- exact GitHub repository identity;
- exact 40-character commit SHA from the workflow run;
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

## 3. Workflow boundary

The evidence mechanism does not replace package validation or conformance.

Ordering remains:

1. build sdist and wheel;
2. validate built-wheel metadata;
3. install the base wheel in a fresh unconstrained consumer environment;
4. verify installed distribution/runtime identity;
5. execute the reference smoke suite;
6. install the same wheel with the declared non-normative `conformance` extra in a separate environment;
7. execute all registered portable TCK profiles;
8. create and verify release evidence;
9. stage only the verified release files;
10. upload the bundle as a GitHub Actions artifact.

The upload uses the official `actions/upload-artifact` action pinned to a full reviewed commit SHA, consistent with repository workflow governance.

## 4. Authority of PR artifacts versus release artifacts

Artifacts produced while this change is under pull-request review prove that the evidence mechanism works for that PR commit. They are **not** the final `v0.3.0-rc.1` release artifacts.

After this PR is separately reviewed and squash-merged, the new exact `main` commit becomes the only eligible RC release commit. Its push CI must succeed and its uploaded bundle becomes the candidate authoritative release evidence set.

A tag must never point to the pre-merge PR head merely because that head produced valid evidence.

## 5. Required readiness checks

Before this evidence PR can be considered ready for merge:

1. Quality / Python 3.11 succeeds.
2. Quality / Python 3.12 succeeds.
3. Quality / Python 3.13 succeeds.
4. Package / Python 3.13 succeeds.
5. Existing base-wheel and full-profile TCK gates remain green.
6. Release evidence unit tests succeed.
7. `MANIFEST.json` and `SHA256SUMS` generation succeeds.
8. Evidence self-verification succeeds before upload.
9. The workflow artifact contains exactly the expected release bundle files.
10. Governance succeeds on the exact PR HEAD and PR metadata.
11. The PR remains based on the selected current `main` without unresolved drift.
12. There are zero unresolved review threads and no new release-blocking issue.

## 6. Tag / release decision boundary

This document and its implementation do **not** authorize:

- merging the evidence PR;
- creating `v0.3.0-rc.1`;
- creating a GitHub Release;
- publishing `avp-reference` to a package index;
- moving any AEP from `Accepted` to `Final`;
- declaring the prerelease a stable conformance target;
- starting Alpha 3 as part of the release action.

After an explicitly authorized merge, the exact resulting `main` commit must pass its push CI. The retained bundle must then be downloaded and independently checked against `MANIFEST.json` / `SHA256SUMS` before the maintainer can make a separate tag/release authorization decision.

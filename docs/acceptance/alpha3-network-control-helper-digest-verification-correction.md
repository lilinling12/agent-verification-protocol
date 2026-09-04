# Alpha 3 Network Control Helper Digest Verification Correction

Status: **IMPLEMENTATION FIX UNDER REVIEW — TEL-003 EVIDENCE NOT YET PRODUCED OR ADOPTED**

Prepared: 2026-09-04

## 1. Triggering evidence

PR #150 (`ci(alpha3): qualify privileged network evidence lane`) was squash-merged to exact `main@f6b4e97b4a1a4865baae9d5484fb7655a1a1c55e`.

The first trusted-main `Network Control Privileged Evidence` execution was run `33824673863`. The workflow passed trusted-main revision checks, dependency installation, and runner/Docker provenance collection, then failed closed before any capture canary or TEL-003 matrix execution with:

```text
ToxiproxyPrerequisiteError: qualification helper exact digest cannot be verified
```

The failed run retained its manifest and runner evidence artifact (artifact ID `9919499105`). The positive and negative terminating matrix was skipped, so this run is **not** TEL-003 evidence.

## 2. Root cause

The qualification path required the exact reviewed helper reference to appear byte-for-byte in Docker image-inspect `RepoDigests` after an already digest-pinned pull.

The same assumption also existed in TEL-002 `ToxiproxyLiveLab._prepare_helper_artifact()`. Therefore a qualification-only workaround would have been insufficient: after qualification, the terminating matrix could fail again at the shared concrete helper prerequisite.

The problematic assumption was that `RepoDigests` is an identity oracle equivalent to the exact pull reference. Docker may normalize official-image repository names and expose repository/index digest metadata whose textual representation is not identical to the fully qualified platform-manifest reference used to perform the pull.

## 3. Correction

The correction does **not** weaken the reviewed helper identity.

The reviewed helper continues to be addressed only by its immutable linux/amd64 platform-manifest digest:

```text
docker.io/library/python@sha256:f576b530293e74140ea91d262232648d5c4f45640a95ec447757701bfcacf034
```

The project-local verification boundary is now:

1. require an `@sha256:` exact reference;
2. require the reviewed platform `linux/amd64`;
3. execute bounded Docker pull against that exact immutable reference and platform;
4. inspect the same exact reference locally;
5. require a local content ID and exact linux/amd64 platform metadata;
6. fail closed on pull failure, malformed inspect output, missing content ID, or platform drift.

`RepoDigests` is no longer treated as a second authority.

## 4. Scope and governance

This correction is concrete live-execution plumbing only. It does not change:

- AEP-0012 lifecycle state;
- Network Control portable C1-C12 semantics;
- `compare_portable_evidence`;
- AF_PACKET witness normalization;
- capture qualification canary requirements;
- HiddenRetry/Fallback negative semantics;
- Spec, Schema, requirement-index, TCK, release, signing, or attestation surfaces;
- provider/backend abstraction policy.

AEP-0012 remains **Proposed**. TEL-003 evidence adoption remains a separate governed Work Unit after a successful trusted-main evidence execution and independent artifact review.

## 5. Regression requirement

The fix must retain tests proving that:

- normalized or index-level `RepoDigests` metadata cannot falsely reject an already exact-digest-addressed helper;
- local platform drift fails closed;
- malformed/non-object inspect output fails closed;
- both capture qualification and TEL-002 live matrix entrypoints use the same exact-helper materialization rule.

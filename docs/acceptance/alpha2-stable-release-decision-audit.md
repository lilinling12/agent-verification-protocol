# Alpha 2 Stable v0.3.0 Release Decision Audit

Status: **BLOCKED — RELEASE MANAGEMENT CLOSURE REQUIRED**

Audit baseline: `main@87b8329487cb349e090523f163bf35d06a3e21f1`

Decision target: stable `v0.3.0`

## Purpose

This audit answers a narrower question than protocol or reference-runtime acceptance:

> Is the current governed repository state ready for a maintainer to authorize creation and publication of stable `v0.3.0` without bypassing any release, provenance, conformance, or post-publication verification control?

The answer at this baseline is **no**.

This is not a protocol-semantics failure. The Alpha 2 Normative Surface Closure and Reference Runtime Alignment gates are already closed. The remaining blockers are release-management and published-artifact-verification gaps.

## Evidence already satisfied

The following prerequisites are already satisfied and are not reopened by this audit:

- AEP-0001 through AEP-0008 are `Final` under the explicit maintainer decision recorded on 2026-08-17.
- Published `v0.3.0-rc.1` is immutable evidence bound to exact source `ef199124017b0dcc8c4a966d00c4f407760f9a06`.
- RC1 published artifacts passed independent external-consumer installation, identity checks, reference smoke, and the complete registered TCK profile set.
- Normative Surface Closure is complete.
- Reference Runtime Alignment RRA-001 through RRA-009 is complete.
- Current development source identity is `0.3.0rc2.dev0`, so post-RC1 source bytes do not reuse the already-published `0.3.0rc1` identity.

## Blocking findings

### SRD-001 — release-development validator has no governed release transition state

Status: **BLOCKING**

`scripts/validate_release_development_state.py` currently validates only `mode: development` and requires all of the following:

```text
latestPublished < sourceVersion < nextRelease
sourceVersion is a .dev release of nextRelease
nextRelease is an RC prerelease
```

The checked-in state is:

```text
latestPublished = 0.3.0rc1
sourceVersion   = 0.3.0rc2.dev0
nextRelease     = 0.3.0rc2
```

This protects RC1 provenance correctly during development, but it means the repository quality gate has no valid state for a release commit whose source version is exactly `0.3.0rc2` or stable `0.3.0`.

A release must not be created by disabling or bypassing this validator. The repository needs a governed release-transition model that can represent at least:

1. ordinary post-release development;
2. a selected release candidate commit;
3. a selected stable release commit;
4. advancement back to development after publication with the newly published immutable anchor.

The model must preserve monotonic PEP 440 ordering, exact source/tag/version binding, immutable already-published anchors, and fail-closed validation.

### SRD-002 — GitHub Actions published-release validation is hard-coded to RC1

Status: **BLOCKING**

`scripts/validate_published_release.py` is already release-generic and supports stable releases through `--stable`.

However `.github/workflows/release-validation.yml` is hard-coded to:

- job name `Published Release / v0.3.0-rc.1`;
- tag `v0.3.0-rc.1`;
- exact commit `ef199124017b0dcc8c4a966d00c4f407760f9a06`;
- distribution version `0.3.0rc1`;
- installed-wheel identity assertions equal to `0.3.0rc1`.

Therefore a future RC2 or stable release cannot use the existing governed Actions path for post-publication verification without first modifying the workflow.

The fix must preserve the immutable RC1 validation path while allowing an explicitly selected release identity to be validated without trusting mutable branch state or unreviewed free-form inputs.

### SRD-003 — post-RC1 source has no published external-consumer evidence point

Status: **BLOCKING FOR CURRENT RELEASE PLAN**

Current `main` is 23 commits ahead of the immutable RC1 source. Those commits include reconciliation closure, AEP Final lifecycle changes, Normative Surface Closure, post-RC provenance governance, and Reference Runtime Alignment fixes.

CI has repeatedly proved these changes from freshly built wheels, and Release Validation continues to prove that the immutable RC1 bytes remain valid. Those are two different facts.

What does not yet exist is a published release whose bytes contain the current post-RC1 source and have themselves passed the external-consumer download/install/full-TCK verification path.

The currently governed development state explicitly declares `0.3.0rc2` / `v0.3.0-rc.2` as `nextRelease`. Under that accepted repository policy, the conservative release path is therefore:

```text
0.3.0rc2.dev0 -> v0.3.0-rc.2 -> published RC2 acceptance -> stable v0.3.0 decision
```

This audit does **not** claim that AVP protocol semantics intrinsically require an RC2. A maintainer could instead propose a separate governed policy change that intentionally retires the RC2 next-release plan and proves an equally strong direct-to-stable provenance/acceptance path. What is prohibited is silently skipping the declared next release or bypassing the validator at publication time.

## Non-blockers

The following are explicitly not stable-release blockers at this baseline:

- optional production signed/attested Artifact publication, because the reference implementation does not claim that optional capability;
- Alpha 3 Environment Fabric features;
- stale historical PRs #37, #38, and #46, whose substance has been superseded by later merged authoritative state;
- repository branch-cleanup issue #23, which is housekeeping rather than release correctness;
- stronger process/network/tenant/sandbox isolation claims that AVP does not make for the base reference runtime.

## Required closure sequence

Stable `v0.3.0` may return to a **READY FOR MAINTAINER DECISION** state only after the release-management path is closed without weakening controls.

Recommended sequence under the current checked-in policy:

1. **Release transition state** — extend the release provenance validator/model so an explicitly selected release commit can carry exact release identity without disabling development provenance checks.
2. **Generic published-release Actions path** — make post-publication verification reusable for an explicitly governed release identity while retaining immutable RC1 verification.
3. **RC2 readiness** — prepare `0.3.0rc2` release metadata/notes on a dedicated release PR and prove exact-head CI, Governance, reproducible package, built-wheel full TCK, and release evidence.
4. **Explicit RC2 publication authorization** — only the maintainer may authorize tag/release creation.
5. **Published RC2 acceptance** — download public RC2 assets, verify exact source/digests, clean-install the wheel, and run the full registered TCK profile set.
6. **Stable decision refresh** — re-audit whether any blocker remains between accepted RC2 bytes and stable `0.3.0`.
7. **Explicit stable publication authorization** — stable tag/release/package-index publication remains a separate maintainer action.

If a future governance PR intentionally chooses a direct-to-stable path instead, it must replace steps 3–5 with controls that provide equivalent exact-source and published-consumer evidence and must update the declared release state before any release commit is selected.

## Release boundary

This audit does **not** authorize:

- changing `__version__` to `0.3.0rc2` or `0.3.0`;
- creating `v0.3.0-rc.2` or `v0.3.0` tags;
- creating a GitHub Release;
- publishing to PyPI or another package index;
- weakening or bypassing release-development validation;
- treating CI for development source as a substitute for post-publication consumer validation;
- Alpha 3 implementation.

## Decision

**BLOCKED — RELEASE MANAGEMENT CLOSURE REQUIRED.**

Protocol/conformance/reference-runtime stabilization is complete enough to enter release management, but stable `v0.3.0` is not yet an executable, fully governed release transition. The next engineering work should close SRD-001 first, then SRD-002, before preparing the next release candidate under the currently declared policy.

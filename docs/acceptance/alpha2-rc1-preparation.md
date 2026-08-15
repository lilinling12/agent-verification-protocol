# Alpha 2 v0.3.0-rc.1 Preparation Record

Status: **READY FOR REVIEW — NOT AUTHORIZED FOR MERGE, TAG, OR RELEASE**

## 1. Candidate identity

- Integrated Alpha 2 baseline: `main@e534de7ae2c763ac66062bb8ff8e6920b4f2cd75`
- Temporary stabilization branch: `release/v0.3.0-rc.1`
- Intended Git tag: `v0.3.0-rc.1`
- Reference distribution version: `0.3.0rc1`
- Preparation date: 2026-08-16

The release branch was created directly from the integrated `main` baseline after PR #33 was squash-merged. Post-merge main CI #363 completed successfully before RC preparation began.

This record authorizes no merge, tag, GitHub Release, package publication, AEP `Final` transition, or Alpha 3 work.

## 2. Preconditions already satisfied

Alpha 2 Acceptance Audit established `READY FOR RC PREPARATION` and is integrated into `main`.

The integrated baseline records:

- AEP-0001 through AEP-0008 as `Accepted`;
- no AEP as `Final`;
- passed cross-profile Security Composition Review;
- 87 indexed normative requirements;
- 71 registered language-neutral TCK cases;
- 10 conformance profiles;
- no unresolved Alpha 2 release-blocking issue;
- no prior Git tag or GitHub Release.

Repository inspection immediately before RC preparation confirmed the tag list and GitHub Release list were both empty.

## 3. Version identity

`src/avp_ref/_version.py` is the single source of truth for the Python reference distribution. For this candidate it is set to:

```text
0.3.0rc1
```

The intended repository tag uses the repository's SemVer-style prerelease spelling:

```text
v0.3.0-rc.1
```

`pyproject.toml` obtains the package version dynamically from `avp_ref._version.__version__`.

`scripts/validate_release_metadata.py` verifies that the source version agrees with:

- imported `avp_ref.__version__`;
- installed `avp-reference` distribution metadata;
- `ReferenceRuntime` implementation identity;
- built wheel `METADATA`.

A disagreement is a release-blocking validation failure; it must not be papered over in release notes.

## 4. Built-wheel conformance hardening

The pre-RC Package job already performed clean wheel build/install and identity validation, but its portable TCK execution was only a four-case smoke subset. In addition, `avp conformance` is explicitly a legacy Python reference smoke suite.

RC preparation strengthens the Package gate so a wheel-backed conformance environment runs every profile discovered under `conformance/tck/profiles/*.yaml`.

This distinction is important:

- `avp conformance` remains non-normative reference smoke evidence;
- full-profile `avp tck run` is the portable conformance gate;
- mandatory cases must pass;
- conditional cases remain governed by declared capability applicability rather than being converted into mandatory implementation features.

The profile loop fails closed if no profiles are discovered or if any selected profile is non-conformant.

### Evidence-driven hardening during preparation

The first full-profile run, CI #364, correctly exposed a packaging-boundary gap instead of being weakened: Artifact Trust, Core, Environment, Evidence, MCP, and Oracle profiles passed from the clean-installed wheel, but the OpenTelemetry profile could not register its reference adapter because the clean environment contained only mandatory package dependencies. The failure was an implementation-adapter availability failure, not a normative TCK failure.

The first remediation added an explicit non-normative `conformance` extra and installed the built wheel with that extra. CI #369 then proved that the Package job, including all ten profiles, passed, but the repository dependency policy rejected replacing the required base-wheel consumer installation with an extras-enabled installation. That rejection was correct: release evidence must separately prove that an ordinary consumer can install the base wheel without release-validation extras.

The final validation design therefore uses two independent fresh environments from the same built wheel:

1. `.wheel-venv` installs `dist/*.whl` with no extras and no repository constraints, runs `pip check`, verifies package/runtime identity, and executes the legacy reference smoke suite.
2. `.conformance-venv` installs the same wheel with `[conformance]`, runs `pip check`, and executes all registered TCK profiles.

The `conformance` extra supplies reference-validation dependencies such as the OpenTelemetry SDK without making them mandatory runtime dependencies or AVP protocol requirements. This preserves both the minimal consumer contract and the complete reference conformance gate.

## 5. Changelog and release notes policy

`CHANGELOG.md` deliberately retains `## Unreleased` during RC preparation. Repository policy states that release entries are created from `main` during the release process and development work remains under `Unreleased` until a tag is published.

Candidate release notes are separately prepared at `docs/releases/v0.3.0-rc.1.md`. They are not proof that the release exists.

Because there is no earlier public AVP tag or GitHub Release, migration notes against a prior published compatibility target are not applicable to this first RC. Candidate notes still describe protocol, compatibility, security, implementation, and non-goal boundaries.

## 6. RC preparation gates

Before this preparation PR may be considered ready for merge, all of the following must hold on its exact final HEAD:

1. Quality / Python 3.11 succeeds.
2. Quality / Python 3.12 succeeds.
3. Quality / Python 3.13 succeeds.
4. Package / Python 3.13 succeeds.
5. Built source and wheel distributions pass release metadata validation.
6. The base wheel installs without extras in a fresh unconstrained consumer environment and `pip check` succeeds.
7. Base installed-wheel distribution/runtime identity matches `0.3.0rc1`.
8. Base installed-wheel reference smoke succeeds.
9. The same built wheel with its declared `conformance` extra installs in a separate fresh unconstrained conformance environment and `pip check` succeeds.
10. Full-profile TCK conformance succeeds for all registered profiles from that wheel-backed conformance environment.
11. Governance succeeds on the exact PR HEAD and current PR metadata.
12. `main` has not drifted from the reviewed base, or the release branch is explicitly reconciled and fully revalidated.
13. There are zero unresolved review threads.
14. No new release-blocking issue has appeared.

Squash merge requires separate explicit maintainer authorization even after all gates are green.

## 7. Pre-readiness validation evidence

The implementation-complete candidate at `90dc28d8eec73bcc724d8d891420b68752d9978b` passed the full preparation gate before this readiness status was recorded:

- CI #373: **success**;
- Governance #401: **success**;
- Quality / Python 3.11: **success**;
- Quality / Python 3.12: **success**;
- Quality / Python 3.13: **success**;
- Package / Python 3.13: **success**;
- source/wheel build and release metadata validation: **success**;
- base wheel clean unconstrained consumer install and `pip check`: **success**;
- base installed-wheel identity and reference smoke: **success**;
- separate wheel `[conformance]` install and `pip check`: **success**;
- installed-wheel full TCK conformance across all 10 registered profiles: **success**;
- comparison with `main@e534de7ae2c763ac66062bb8ff8e6920b4f2cd75`: `behind_by=0`;
- unresolved PR #34 review threads: `0`;
- open issue review: only #23 (`chore(repo): delete superseded Alpha branches`), classified as repository hygiene and non-release-blocking.

This document update changes the tracked candidate HEAD, so the evidence above is not used as a substitute for final exact-head validation. The new final document-state HEAD must pass the same CI/Governance, drift, thread, and issue gates before PR #34 is promoted from Draft to Ready for review.

## 8. Post-merge release-commit rule

Even a successful merge of the RC preparation PR does not create a release.

After that merge, the selected release candidate commit must be the resulting exact commit on `main`, not the pre-merge release-branch HEAD. The release process must then:

1. re-run/verify exact-main CI and release gates;
2. build source and wheel artifacts from that exact commit in a clean environment;
3. verify both base-consumer installation and full wheel-backed conformance;
4. compute and record reproducible artifact SHA-256 digests from the exact release artifacts;
5. verify tag name, package version, candidate notes, changelog state, AEP references, security review, issues, and repository drift;
6. obtain explicit maintainer authorization for the tag / GitHub Release / any package publication;
7. create the immutable tag and release only after those gates pass;
8. verify published artifacts against the recorded identifiers before announcing the RC.

Artifact digests are intentionally not invented during this branch-preparation step because the authoritative release artifacts must be built from the selected post-merge `main` release commit.

## 9. Governance boundary

`READY FOR REVIEW` means the RC preparation change set is eligible for maintainer merge review. It does **not** authorize:

- merging PR #34;
- creating `v0.3.0-rc.1`;
- creating a GitHub Release;
- publishing `avp-reference` to a package index;
- declaring the prerelease a stable conformance target;
- moving AEP-0001 through AEP-0008 to `Final`;
- beginning Alpha 3 work as part of the RC.

Those are later, separately evidenced governance decisions.

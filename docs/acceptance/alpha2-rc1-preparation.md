# Alpha 2 v0.3.0-rc.1 Preparation Record

Status: **IN PROGRESS — NOT AUTHORIZED FOR TAG OR RELEASE**

## 1. Candidate identity

- Integrated Alpha 2 baseline: `main@e534de7ae2c763ac66062bb8ff8e6920b4f2cd75`
- Temporary stabilization branch: `release/v0.3.0-rc.1`
- Intended Git tag: `v0.3.0-rc.1`
- Reference distribution version: `0.3.0rc1`
- Preparation date: 2026-08-16

The release branch was created directly from the integrated `main` baseline after PR #33 was squash-merged. Post-merge main CI #363 completed successfully before RC preparation began.

This record authorizes no tag, GitHub Release, package publication, AEP `Final` transition, or Alpha 3 work.

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

RC preparation strengthens the Package gate so the clean-installed wheel executable runs every profile discovered under `conformance/tck/profiles/*.yaml`.

This distinction is important:

- `avp conformance` remains non-normative reference smoke evidence;
- full-profile `avp tck run` is the portable conformance gate;
- mandatory cases must pass;
- conditional cases remain governed by declared capability applicability rather than being converted into mandatory implementation features.

The profile loop fails closed if no profiles are discovered or if any selected profile is non-conformant.

The first full-profile run, CI #364, correctly exposed a packaging-boundary gap instead of being weakened: Artifact Trust, Core, Environment, Evidence, MCP, and Oracle profiles passed from the clean-installed wheel, but the OpenTelemetry profile could not register its reference adapter because the clean environment contained only mandatory package dependencies. The failure was an implementation-adapter availability failure, not a normative TCK failure.

The remediation keeps OpenTelemetry optional for ordinary package consumers and adds an explicit non-normative `conformance` extra to `avp-reference`. The clean release-validation environment installs the built wheel as `wheel[conformance]`; this supplies reference-validation dependencies such as the OpenTelemetry SDK without making those dependencies mandatory runtime requirements or AVP protocol requirements. Full-profile TCK execution remains mandatory for the RC gate.

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
6. The built wheel with its declared `conformance` extra installs in a fresh unconstrained environment and `pip check` succeeds.
7. Installed-wheel distribution/runtime identity matches `0.3.0rc1`.
8. Installed-wheel reference smoke succeeds.
9. Installed-wheel full-profile TCK conformance succeeds for all registered profiles.
10. Governance succeeds on the exact PR HEAD and current PR metadata.
11. `main` has not drifted from the reviewed base, or the release branch is explicitly reconciled and fully revalidated.
12. There are zero unresolved review threads.
13. No new release-blocking issue has appeared.

The RC preparation PR remains Draft while these gates are being established. Squash merge requires separate explicit maintainer authorization.

## 7. Post-merge release-commit rule

Even a successful merge of the RC preparation PR does not create a release.

After that merge, the selected release candidate commit must be the resulting exact commit on `main`, not the pre-merge release-branch HEAD. The release process must then:

1. re-run/verify exact-main CI and release gates;
2. build source and wheel artifacts from that exact commit in a clean environment;
3. verify full installed-wheel conformance using the declared conformance dependencies;
4. compute and record reproducible artifact SHA-256 digests from the exact release artifacts;
5. verify tag name, package version, candidate notes, changelog state, AEP references, security review, issues, and repository drift;
6. obtain explicit maintainer authorization for the tag / GitHub Release / any package publication;
7. create the immutable tag and release only after those gates pass;
8. verify published artifacts against the recorded identifiers before announcing the RC.

Artifact digests are intentionally not invented during this branch-preparation step because the authoritative release artifacts must be built from the selected post-merge `main` release commit.

## 8. Governance boundary

This preparation record does **not** authorize:

- merging the RC preparation PR;
- creating `v0.3.0-rc.1`;
- creating a GitHub Release;
- publishing `avp-reference` to a package index;
- declaring the prerelease a stable conformance target;
- moving AEP-0001 through AEP-0008 to `Final`;
- beginning Alpha 3 work as part of the RC.

Those are later, separately evidenced governance decisions.

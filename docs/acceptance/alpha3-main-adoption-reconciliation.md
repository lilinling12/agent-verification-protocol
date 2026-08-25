# Alpha 3 Main-Adoption Reconciliation

Status: REVIEW CANDIDATE

## Purpose

This audit reconciles repository governance after the reviewed Alpha 3 Environment Fabric candidate stack was squash-merged into `main` by PR #83.

It records what changed, what is now true on `main`, and what remains explicitly un-authorized. This document is governance evidence; it does not itself change protocol semantics, AEP lifecycle state, release selection, or backend implementation authority.

## Adopted main identity

- PR: #83
- squash merge commit: `428635d857c96d9df400ef5a0b16aaba53fb97cf`
- previous `main`: `cdf56cf8e8d747f26b5438086ece3fb4cd489f31`
- merge commit message explicitly preserves AEP-0009 and AEP-0010 as `Accepted`, not `Final`.

The merged aggregate contains:

1. AEP-0009 Environment Fabric Accepted direction and design evidence;
2. active normative-candidate governance;
3. Environment Fabric normative specification, requirement index, closed schemas, draft TCK profile/cases, and backend-neutral reference runtime;
4. AEP-0010 Relational State Accepted direction and review evidence;
5. Relational State normative specification, manifest-integrity contract, requirement index, closed schemas, draft TCK profile/cases, and backend-neutral reference model/adapters.

## Exact-main validation

The merge commit triggered push CI:

- CI #569
- workflow run `32852278819`
- exact head `428635d857c96d9df400ef5a0b16aaba53fb97cf`
- conclusion: SUCCESS

Successful jobs include:

- Quality / Python 3.11
- Quality / Python 3.12
- Quality / Python 3.13
- Package / Python 3.13

The package job additionally passed:

- reproducible distribution-byte verification;
- built-wheel metadata validation;
- clean-consumer wheel installation;
- installed-wheel identity verification;
- installed-wheel reference smoke;
- installed-wheel full TCK conformance;
- release-evidence build and verification.

This is exact-main execution evidence that the merged candidate authority slices are internally coherent and executable from the packaged reference distribution.

## Workflow-trigger interpretation

No exact-main Governance or Release Validation push run is expected from the current workflow definitions:

- `.github/workflows/governance.yml` listens to `pull_request` events only;
- `.github/workflows/release-validation.yml` listens to selected `pull_request` paths and `workflow_dispatch` for published-release validation;
- `.github/workflows/ci.yml` listens to pushes to `main` and pull requests.

Therefore the absence of merge-commit Governance/Release Validation runs is not a failed gate. The governing PR exact-head checks were green before merge, while exact-main CI #569 supplies the post-merge package/TCK execution evidence.

## Candidate-registry disposition

`docs/reconciliation/normative-candidates/registry.json` remains correct after main adoption.

The registry intentionally represents complete candidate authority slices that may live on `main` while their governing AEPs remain `Accepted` rather than `Final`. It is non-normative governance evidence and explicitly rejects silent promotion.

Do **not** remove the Fabric or Relational candidate entries merely because PR #83 merged.

Removal belongs to a separately governed Final/release promotion that also changes:

- AEP status to `Final` only when lifecycle requirements are met;
- requirement-index status from `draft-normative-candidate` to `normative`;
- TCK profile status from `draft` to `active` where applicable;
- stable normative-surface ownership/reconciliation records.

## AEP lifecycle state

At this reconciliation point:

- AEP-0009: `Accepted`
- AEP-0010: `Accepted`
- neither is `Final`
- both target an unselected future protocol version.

Main adoption alone does not satisfy the repository definition of `Final`, which requires the governed release/finalization evidence path.

## Release provenance

Release provenance remains unchanged:

- mode: `development`
- latest published stable version: `0.3.0`
- source version: `0.3.1.dev0`
- planned next release record: `0.3.1`

This audit does not decide whether Alpha 3 normative changes can or should be published as `0.3.1`. The release process states that pre-1.0 PATCH releases must not intentionally introduce breaking normative change, and release/version selection is a separate governance action.

## Roadmap reconciliation

Because the reviewed authority slices are now present on `main` and exact-main CI passed their packaged TCK execution, the following roadmap work items are complete as repository implementation/adoption facts:

### Environment Fabric

- normative specification and requirement index;
- candidate-owned schemas;
- base execution-sensitive TCK, including negative behavior cases.

### Relational State

- normative specification and requirement index;
- Relational State Manifest/Image and related closed schemas;
- execution-sensitive `avp-relational-state-v0.1` TCK.

Marking these items complete does **not** make either AEP Final or the candidate profiles stable/released.

## Remaining implementation boundary

The next implementation layer is backend evidence, not new portable semantics by precedent.

Still incomplete and separately governed:

- PostgreSQL adapter against the portable Relational State TCK;
- MySQL/InnoDB adapter against the same TCK;
- PostgreSQL/MySQL canonical parity acceptance evidence;
- Playwright browser runtime;
- network fault proxy;
- virtual clock service;
- container runtime;
- microVM experiment.

Before any backend work begins, implementation must preserve these constraints:

1. no backend-specific API becomes the portable contract;
2. no backend-name branches are introduced into language-neutral portable TCK semantics;
3. no raw SQL/query/transaction API is promoted as the AVP Relational State protocol;
4. no backend mechanism inflates restore fidelity, determinism, or SecurityAssurance claims;
5. PostgreSQL and MySQL must independently satisfy the same portable profile and vectors;
6. implementation evidence must fail closed when required portable capability cannot be honored.

## Reconciliation disposition

`READY FOR REVIEW` once the reconciliation PR exact-head CI/Governance/Release Validation checks are green.

This audit does not authorize:

- AEP-0009 or AEP-0010 `Accepted -> Final`;
- PostgreSQL/MySQL or other backend implementation;
- Alpha 3 release/version selection;
- entering release mode;
- tag or GitHub Release creation;
- package-index publication;
- signing or attestation publication.

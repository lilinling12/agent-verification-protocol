# Alpha 3 Relational Backend Harness Main Adoption

Status: **MAIN-ADOPTED — RBIR-001..003 IMPLEMENTATION PREREQUISITE COMPLETE**

Adopted PR: #90  
Reviewed PR head: `b6f18cd0021b381ce02adc6243db391f634c8b05`  
Main adoption commit: `06f08f686fa58aff1635ddbd2e9566cab72c390a`

## Purpose

This record closes the repository-state distinction left intentionally open by `docs/acceptance/alpha3-relational-backend-harness-acceptance.md`.

PR #90 was review-closed at its exact head and then explicitly authorized for squash merge. The reviewed RBIR-001..003 implementation is now present on `main`; this document records that mainline adoption and the exact-main execution evidence.

## Adopted implementation boundary

The adopted slice contains the implementation prerequisites required before a database-specific Relational State backend may be introduced:

- **RBIR-001** — shared backend-neutral Relational State conformance harness;
- **RBIR-002** — immutable canonical language-neutral parity fixture with an independent SHA-256 lock and shared expected canonical evidence;
- **RBIR-003** — privileged fixture-control seam for committed/held mutation, atomic multi-relation change, commit-coordinated projection, logical-binding drift, and execution-input drift.

The materialized `RelationalResourceSpec` also freezes baseline state before identity derivation/provisioning so caller mutation cannot change the logical provisioning preimage after identity calculation.

## Authority boundary

Main adoption does not change protocol authority.

The portable semantics remain governed by:

```text
AEP-0010 Accepted
  -> Relational State normative specification
  -> requirement index
  -> closed schemas
  -> avp-relational-state-v0.1 TCK
  -> backend-neutral implementation evidence
```

The adopted harness does not introduce a generic SQL/query/transaction/DDL/catalog API, backend-name portable semantics, backend-native snapshot identity, distributed-transaction semantics, `EXACT` restore claims, or SecurityAssurance inflation.

SQL, DDL, admin credentials, native transaction handles, synchronization primitives, and backend-specific catalog mechanics remain implementation-private behind `RelationalFixtureControl` for any future real database backend.

## Exact-main evidence

Squash merge PR #90 produced exact `main` commit:

`06f08f686fa58aff1635ddbd2e9566cab72c390a`

Exact-main CI #590 (`32939199537`) completed successfully on that commit. Executed evidence includes:

- Quality / Python 3.11 — SUCCESS;
- Quality / Python 3.12 — SUCCESS;
- Quality / Python 3.13 — SUCCESS;
- reproducible source/wheel distribution bytes — SUCCESS;
- clean-consumer base-wheel installation — SUCCESS;
- installed-wheel identity verification — SUCCESS;
- installed-wheel reference smoke — SUCCESS;
- **installed-wheel full TCK conformance — SUCCESS**;
- release-evidence build and verification — SUCCESS.

No exact-main Governance or Release Validation run is inferred: those workflows are PR/explicit-validation gates rather than `push: main` gates. PR #90 itself passed CI #589, Governance #652/#653/#654, Release Validation #88, and formal exact-head review `5027300643` before merge.

## Mainline disposition

The repository may now record the RBIR-001..003 prerequisite as complete on `main`.

This does **not** mean that any real database backend is complete. The following remain separate governed work units:

- PostgreSQL adapter against the existing backend-neutral harness and portable TCK;
- MySQL/InnoDB adapter against the same harness and TCK;
- PostgreSQL/MySQL canonical parity acceptance evidence.

A future PostgreSQL implementation must consume the adopted contracts rather than amend portable semantics by implementation precedent. Any discovered protocol-level deficiency must be raised as a separate authority-chain issue instead of being silently resolved inside backend-specific code.

## Non-authorizations

This adoption record does not:

- change AEP-0009 or AEP-0010 from Accepted to Final;
- authorize MySQL/InnoDB implementation;
- establish PostgreSQL/MySQL parity;
- select `0.3.1` or any other Alpha 3 release version;
- authorize package publication, signing, or attestation publication.

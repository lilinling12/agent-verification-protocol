# Alpha 3 PostgreSQL Relational Adapter Main Adoption

Status: **ADOPTED ON MAIN**

Adopted implementation commit: `70b1a6c9ce0d45c596e489533cc9600151dae2b8`  
Source pull request: PR #92  
Merge method: squash  
Exact-main CI: #599 (`32948033723`)

## Decision

The reviewed PostgreSQL Relational State adapter from PR #92 is adopted into
`main` as the first database-specific implementation of the already-accepted
portable Relational State profile.

This adoption is implementation evidence only. It does not change the authority
order `AEP/reconciliation -> normative spec -> requirement index -> schema -> TCK`
and does not allow PostgreSQL-specific behavior to define portable AVP semantics
by implementation precedent.

## Main-adoption evidence

The protocol maintainer explicitly authorized squash merge of PR #92 on
2026-08-26. GitHub created exact main commit:

`70b1a6c9ce0d45c596e489533cc9600151dae2b8`

Exact-main CI #599 ran against that merge commit and completed successfully with:

- Quality / Python 3.11 — SUCCESS;
- Quality / Python 3.12 — SUCCESS;
- Quality / Python 3.13 — SUCCESS;
- Package / Python 3.13 — SUCCESS;
- reproducible source/wheel distribution verification — SUCCESS;
- clean base-wheel consumer installation — SUCCESS;
- installed-wheel identity and reference smoke — SUCCESS;
- installed-wheel full registered TCK conformance — SUCCESS;
- release-evidence build and verification — SUCCESS;
- PostgreSQL 17.11 / Relational TCK / Python 3.13 — SUCCESS;
- PostgreSQL 18.6 / Relational TCK / Python 3.13 — SUCCESS.

Both PostgreSQL lanes execute the database-backed acceptance suite from a built
wheel installed with the optional `postgresql` extra. The complete
`avp-relational-state-v0.1` profile is required by the integration test to finish
with exactly **11 PASS / 0 FAIL / 0 SKIP**.

## Adopted implementation boundary

The implementation remains behind the existing backend-neutral
`RelationalBackendHarness`, `RelationalFixtureControl`, and `RelationalSUT`
boundaries. PostgreSQL SQL, DDL, schema/table/column identifiers, roles, DSNs,
MVCC details, and native transaction handles remain implementation-private.

The adopted implementation preserves the reviewed guarantees, including:

- generated physical identifiers rather than using logical AVP ids as SQL identifiers;
- exact scalar round-trip for the portable v0.1 type vocabulary;
- PostgreSQL `numeric(65,0)` for portable integer range and exact `numeric(p,s)` decimal mapping;
- one native transaction for atomic multi-relation fixture mutation;
- committed-state projection consistency across the atomic commit barrier;
- independent database reprojection after reset and restore;
- successful restore fidelity capped at exactly `STATE_EQUIVALENT`;
- distinct Subject-visible and evaluator-complete PostgreSQL roles;
- optional Psycopg dependency rather than a mandatory base-package dependency;
- real PostgreSQL 17.11 and 18.6 integration coverage in CI.

## Roadmap effect

The roadmap item `PostgreSQL adapter against the portable TCK` may now be marked
complete because the reviewed implementation is present on `main` and has passed
exact-main database-backed conformance.

The following items remain open and separately governed:

- MySQL/InnoDB adapter against the same portable TCK;
- PostgreSQL/MySQL canonical parity acceptance evidence.

## Non-authorizations

This adoption does not authorize:

- modification of portable Relational Spec/Schema/TCK semantics;
- MySQL/InnoDB implementation by inference from the PostgreSQL merge;
- PostgreSQL/MySQL parity acceptance;
- AEP-0009 or AEP-0010 `Accepted` -> `Final` transition;
- selection or publication of `0.3.1` or another release;
- package-index publication;
- signing or attestation publication.

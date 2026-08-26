# Alpha 3 PostgreSQL Relational Adapter Acceptance

Status: **DRAFT — IMPLEMENTATION UNDER REVIEW**

Implementation baseline: `main@ba16ddf4633c9aa178d5088db705fed5bc6918ed`

Governing authority:

- AEP-0009 — Environment Fabric Composition and Capability Contract (`Accepted`)
- AEP-0010 — Relational State Resource Profile v0.1 (`Accepted`)
- `spec/relational/relational-state-contract.md`
- `spec/relational/manifest-integrity-contract.md`
- `spec/relational/requirement-index.yaml`
- `conformance/tck/profiles/avp-relational-state-v0.1.yaml`
- `docs/acceptance/alpha3-relational-backend-implementation-readiness.md`
- `docs/acceptance/alpha3-relational-backend-harness-main-adoption.md`

## Purpose

This audit governs the first database-specific implementation evidence for the
accepted Relational State profile. It evaluates whether PostgreSQL can implement
the already-adopted `RelationalBackendHarness` / `RelationalFixtureControl`
boundaries without changing portable AVP semantics by implementation precedent.

This PR is implementation-only with respect to protocol authority. Portable
Spec, requirement-index, Schema, TCK case semantics, and the canonical shared
parity fixture are not modified.

## Required acceptance evidence

The PostgreSQL adapter is eligible for review closure only when all of the
following are true on one exact PR head:

1. the adapter implements the existing backend-neutral harness and fixture-control contracts;
2. the complete mandatory `avp-relational-state-v0.1` profile executes through a real PostgreSQL-backed SUT with **11 PASS / 0 FAIL / 0 SKIP**;
3. PostgreSQL 17 and 18 integration lanes use explicit current minor versions rather than a floating `latest` image;
4. the shared immutable parity fixture independently reproduces its Manifest, baseline StateImage, projection, post-mutation StateImage, and Diff identities from PostgreSQL observations;
5. a multi-relation mutation is one native PostgreSQL transaction and a projection observed at the commit barrier is either fully pre-commit or fully post-commit, never torn;
6. QUIESCING rejects new controlled mutations and waits for previously admitted commit/rollback settlement;
7. reset and restore are independently re-read from PostgreSQL and compared by canonical StateImage identity; successful restore reports exactly `STATE_EQUIVALENT`;
8. canonical scalar conversion round-trips the complete portable v0.1 type vocabulary without lossy normalization, including 65-digit integer representation and `decimal(65,30)`;
9. Subject-visible reads and evaluator-complete reads use distinct implementation-private PostgreSQL roles, while privileged DDL/control authority remains outside both;
10. SQL, DDL, DSNs, PostgreSQL role/schema/table identity, and native transaction handles do not appear in portable TCK resources, schemas, reports, or `RelationalSUT`;
11. the base `avp-reference` wheel remains installable and its full registered TCK continues to pass without installing a PostgreSQL driver;
12. Psycopg remains an optional implementation dependency with a compatibility range, while repository PostgreSQL CI resolves it through exact constraints;
13. PostgreSQL setup and teardown are deterministic, and cleanup failures are treated as implementation/infrastructure failures rather than Agent Task Verdicts;
14. exact-head CI, Governance, Release Validation, review threads, base drift, and mergeability are independently verified before Ready transition.

## Implementation boundary

The adapter may privately use PostgreSQL schemas, roles, transactions, MVCC,
DDL, and typed columns. Logical AVP relation and column identifiers are mapped
to generated physical identifiers and are not interpolated as SQL identifiers.

The database representation is deliberately non-normative. In particular:

- portable `integer` uses an exact PostgreSQL numeric representation rather than narrowing to `bigint`;
- portable decimal precision/scale maps to exact PostgreSQL `numeric(p,s)`;
- local and instant timestamps retain their existing distinct AVP lexical semantics;
- row ordering is recomputed from canonical logical keys rather than physical/index/collation order;
- a PostgreSQL transaction/snapshot token never becomes AVP state identity;
- physical restore fidelity never inflates Relational v0.1 above `STATE_EQUIVALENT`.

## Dependency and CI boundary

The base package has no mandatory PostgreSQL dependency. The implementation is
installed through the optional `postgresql` extra. Repository CI constrains the
integration resolution exactly, while the public optional dependency remains a
bounded compatibility range under `docs/DEPENDENCIES.md`.

The PostgreSQL integration job builds the repository wheel first, installs that
wheel with the optional PostgreSQL extra in a fresh environment, then executes
the database-backed acceptance tests. The existing package job independently
continues to install the base wheel without PostgreSQL and run the full registered
reference TCK.

## Current disposition

**DRAFT — NOT READY.**

The implementation and real-database gates must run before this audit can record
an exact-head acceptance result. The ROADMAP PostgreSQL item remains unchecked
until a separately review-closed implementation is actually adopted into
`main`.

This work does not authorize:

- modification of portable Relational Spec/Schema/TCK semantics;
- MySQL/InnoDB implementation or PostgreSQL/MySQL parity acceptance;
- AEP-0009 or AEP-0010 `Accepted` -> `Final` transition;
- selection or publication of `0.3.1` or another release;
- package-index publication;
- signing or attestation publication;
- merge of the PostgreSQL PR without separate explicit maintainer authorization.

# Alpha 3 PostgreSQL Relational Adapter Acceptance

Status: **SEMANTIC REVIEW CLOSED — FINAL EXACT-HEAD GATES PENDING**

Implementation baseline: `main@ba16ddf4633c9aa178d5088db705fed5bc6918ed`  
Reviewed semantic head: `0954140ec30946787c95dfa04eb980637945ad2f`  
Formal implementation review: `5028233705`

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

## Acceptance criteria

The PostgreSQL adapter is eligible for Ready transition only when all of the
following are true on one exact final PR head:

1. the adapter implements the existing backend-neutral harness and fixture-control contracts;
2. the complete mandatory `avp-relational-state-v0.1` profile executes through the PostgreSQL-backed implementation path with **11 PASS / 0 FAIL / 0 SKIP**;
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
14. exact-head CI, Governance, applicable Release Validation, review threads, base drift, and mergeability are independently verified before Ready transition.

## Reviewed implementation boundary

The adapter privately uses PostgreSQL schemas, roles, transactions, MVCC, DDL,
and typed columns. Logical AVP relation and column identifiers are mapped to
generated physical identifiers and are not interpolated as SQL identifiers.

The database representation is deliberately non-normative. In particular:

- portable `integer` uses exact PostgreSQL `numeric(65,0)` rather than narrowing to `bigint`;
- portable decimal precision/scale maps to exact PostgreSQL `numeric(p,s)`;
- local and instant timestamps retain their existing distinct AVP lexical semantics with the already-governed 0..6 fractional-precision domain;
- row ordering is recomputed from canonical logical keys rather than physical/index/collation order;
- a PostgreSQL transaction/snapshot token never becomes AVP state identity;
- physical restore fidelity never inflates Relational v0.1 above `STATE_EQUIVALENT`.

The implementation consumes the adopted `RelationalSUT` surface rather than
adding SQL/query/transaction/catalog APIs to it. Native mutation and commit
coordination remain behind `RelationalFixtureControl`.

## Database authority and visibility boundary

The harness creates generated implementation-private PostgreSQL roles and
physical schema/table/column identifiers. Evaluator-complete reads and
Subject-visible reads execute under distinct NOLOGIN roles while provisioning,
fixture mutation, drift controls, and cleanup retain privileged harness authority.

The CI PostgreSQL service uses authenticated test-only access. Its credential is
derived from the GitHub Actions run id; it is neither a repository secret nor
part of any AVP fixture, Artifact, Evidence, Manifest, report, or protocol identity.

## Package and dependency boundary

The base package has no mandatory PostgreSQL dependency. The implementation is
installed through the optional `postgresql` extra with bounded public compatibility
`psycopg[binary]>=3.3,<4`. Repository integration resolution is pinned to
Psycopg / psycopg-binary `3.3.4` through `constraints/ci.txt`.

The PostgreSQL integration job builds the repository wheel first, installs that
wheel with the optional PostgreSQL extra in a fresh environment, and then executes
the database-backed acceptance tests. The existing package job independently
installs the base wheel without PostgreSQL and executes the full registered
reference TCK.

## Semantic-head execution evidence

Reviewed semantic head:

`0954140ec30946787c95dfa04eb980637945ad2f`

Exact-head CI #596 completed successfully and included:

- Quality / Python 3.11 — SUCCESS;
- Quality / Python 3.12 — SUCCESS;
- Quality / Python 3.13 — SUCCESS;
- Package / Python 3.13 — SUCCESS;
- reproducible source/wheel distribution bytes — SUCCESS;
- unconstrained clean base-wheel installation — SUCCESS;
- installed-wheel identity and reference smoke — SUCCESS;
- installed-wheel full registered TCK conformance — SUCCESS;
- release-evidence build and verification — SUCCESS;
- PostgreSQL 17.11 / Relational TCK / Python 3.13 — SUCCESS;
- PostgreSQL 18.6 / Relational TCK / Python 3.13 — SUCCESS.

Each PostgreSQL lane executes the integration suite from the built wheel. Its
full-profile test requires the resulting `ConformanceReport` summary to be
exactly:

```text
11 PASS / 0 FAIL / 0 SKIP
```

The same suite independently recomputes the canonical shared parity fixture
Manifest/StateImage/projection/post-mutation/Diff identities from PostgreSQL
observations and exercises atomic-commit visibility and the database-backed
security case.

Governance #661 also passed on the semantic head. Formal exact-head implementation
review `5028233705` found no blocker requiring portable Spec/Schema/TCK changes and
closed the semantic implementation review.

At semantic review time the PR was ahead-only from its exact main baseline with
`behind_by=0` and had no unresolved inline review threads.

## Final governance gate

The remaining changes after the reviewed semantic head are limited to acceptance
and roadmap synchronization. Those governance-only changes must independently
pass final exact-head CI, Governance, and the Release Validation workflow that is
made applicable by the ROADMAP update. Base drift, mergeability, and review-thread
state must then be rechecked before the PR may leave Draft.

The ROADMAP PostgreSQL checkbox remains intentionally **unchecked** until the
reviewed implementation is actually squash-merged into `main` under a separate
explicit maintainer authorization. PR readiness is not main adoption.

## Non-authorizations

This work does not authorize:

- modification of portable Relational Spec/Schema/TCK semantics;
- MySQL/InnoDB implementation or PostgreSQL/MySQL parity acceptance;
- AEP-0009 or AEP-0010 `Accepted` -> `Final` transition;
- selection or publication of `0.3.1` or another release;
- package-index publication;
- signing or attestation publication;
- merge of the PostgreSQL PR without separate explicit maintainer authorization.

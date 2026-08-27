# Alpha 3 PostgreSQL Relational Adapter Maintainability Governance

Status: **IMPLEMENTATION REVIEW CANDIDATE — MAIN ADOPTION PENDING**

Base main: `0bc12cdecd7d35292d2720adb0963e66ebeb509d`  
Source pull request: PR #97

## 1. Purpose

This work governs the maintainability of the already-adopted PostgreSQL
Relational State adapter. The adapter originally concentrated driver loading,
canonical value conversion, SQL materialization, resource lifecycle, privileged
fixture controls, negative SUTs, transaction coordination, and backend harness
lifecycle in one implementation module.

The refactor separates those responsibilities without changing portable AVP
Relational State semantics. The authority order remains:

```text
Normative Spec -> Schema -> TCK -> Reference Runtime
```

This document is implementation evidence, not a new protocol authority surface.

## 2. Package architecture

The PostgreSQL implementation is split under
`src/avp_ref/tck_adapter/postgresql_relational/`:

- `driver.py` — lazy loading of the optional Psycopg dependency;
- `codec.py` — exact canonical AVP scalar to/from PostgreSQL representation;
- `common.py` — implementation-private deterministic identity/projection/diff
  helpers;
- `resource.py` — PostgreSQL-backed Relational SUT state and lifecycle behavior;
- `fixture.py` — privileged mutation controls, held transactions, and the MVCC
  commit barrier;
- `negative.py` — metadata-identical negative SUT implementations;
- `harness.py` — generated role lifecycle, provisioning orchestration, scalar
  round-trip checks, and cleanup;
- `__init__.py` — minimal explicit package exports.

The historical `postgresql_relational_harness.py` path remains as a thin
compatibility facade exporting the same two consumer-visible classes.

## 3. Dependency and authority boundaries

The implementation follows a one-way responsibility flow rather than a generic
SQL-backend inheritance hierarchy:

```text
harness
  -> fixture / negative / resource
  -> codec / common / driver
```

`fixture` and `negative` may depend on the concrete PostgreSQL resource because
they are implementation-private test/control planes. None of these modules are
portable Relational State APIs.

No `BaseSqlRelationalBackend`, generic SQL query API, native transaction API,
backend snapshot token, PostgreSQL catalog contract, or PostgreSQL-specific TCK
expectation is introduced. PostgreSQL and MySQL continue to implement the same
existing backend-neutral harness independently.

## 4. Preserved semantic invariants

The refactor must preserve all previously adopted PostgreSQL guarantees:

- portable Manifest and StateImage identity are computed from the existing
  canonical model, not database-native identity;
- scalar conversion remains exact for the closed v0.1 type domain;
- physical schema/table/column identifiers remain generated implementation
  details;
- evaluator-complete and Subject-visible database authority remain separated;
- multi-relation evaluator and Subject reads use one PostgreSQL repeatable-read
  logical observation boundary;
- the privileged atomic fixture mutation uses one native transaction and a real
  MVCC commit barrier;
- reset success is accepted only after independent full-state reprojection;
- restore success is accepted only after independent reprojection and remains
  exactly `STATE_EQUIVALENT`, never `EXACT`;
- execution-input drift and logical binding drift continue to fail closed;
- optional Psycopg remains lazily loaded and does not become a base-wheel
  dependency;
- existing legacy import paths remain source-compatible.

## 5. Maintainability and failure-safety improvements

The refactor additionally strengthens implementation-private lifecycle hygiene:

1. generated Subject/Evaluator role creation is fail-safe: if principal creation
   partially succeeds, generated roles are removed before the constructor error
   propagates;
2. provisioning cleanup distinguishes “schema was created” from failures that
   occur before materialization, avoiding unnecessary compensating DDL;
3. if compensating schema cleanup itself fails, the original provisioning error
   remains primary and cleanup failure is retained as an exception note rather
   than masking the root cause;
4. public/critical boundaries have focused docstrings and comments explain
   invariants, authority, transaction visibility, or failure-safety rationale
   rather than restating syntax;
5. package exports are explicit and minimal.

These are backend reliability improvements only. They do not modify portable
observable success criteria.

## 6. Structural regression coverage

`tests/test_postgresql_relational_package.py` locks two refactor-specific
properties:

- the compatibility facade exports the exact packaged class objects;
- importing the PostgreSQL adapter does not eagerly import `psycopg`.

The existing real PostgreSQL adapter suite remains the semantic acceptance path;
these structural tests do not replace database-backed TCK execution.

## 7. Required exact-head acceptance

Before this PR is eligible to leave Draft, the exact final head must pass:

- Governance;
- Quality on Python 3.11, 3.12, and 3.13;
- reproducible package construction;
- clean base-wheel installation and installed-wheel identity/smoke;
- installed-wheel full registered TCK conformance;
- release-evidence build and verification;
- PostgreSQL 17.11 real Relational TCK;
- PostgreSQL 18.6 real Relational TCK;
- MySQL 8.4.11 regression Relational TCK;
- MySQL 9.7.2 regression Relational TCK;
- PostgreSQL 17.11 + MySQL 8.4.11 real canonical parity;
- PostgreSQL 18.6 + MySQL 9.7.2 real canonical parity;
- formal exact-head implementation review with no unresolved review thread.

A successful earlier head is not reusable after a refactor change.

## 8. Non-authorizations

This work does not authorize or perform:

- changes to AEP-0009 or AEP-0010 lifecycle state;
- changes to Relational normative specification, requirement index, schemas, or
  language-neutral TCK semantics;
- changes to the immutable parity fixture or its lock;
- changes to MySQL portable behavior;
- PostgreSQL behavior becoming portable precedent;
- ROADMAP reconciliation for the already-merged canonical parity work unit;
- release selection or publication;
- package-index publication;
- signing or attestation publication;
- merge of PR #97 without separate explicit protocol-maintainer authorization.

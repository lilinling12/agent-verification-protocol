# Alpha 3 PostgreSQL Relational Adapter Maintainability Governance

Status: **ADOPTED ON MAIN — MAINTAINABILITY GOVERNANCE CLOSED**

Implementation review base: `0bc12cdecd7d35292d2720adb0963e66ebeb509d`  
Source pull request: PR #97  
Final reviewed PR head: `d1452df771237de8152a73ea03302b7438df3d9c`  
Adopted main commit: `43a437915cb078e3adde392d5560e832207ee662`  
Merge method: squash  
Exact-main CI: #616 (`33051205901`)  
Exact-main Relational Parity: #9 (`33051205914`)

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

The adopted refactor preserves the previously governed PostgreSQL guarantees:

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

## 7. Exact-head implementation acceptance

The final reviewed PR head was:

`d1452df771237de8152a73ea03302b7438df3d9c`

It was ahead of base by 12 commits and behind by 0 when reviewed. The base
remained exact `main@0bc12cdecd7d35292d2720adb0963e66ebeb509d`; no base drift or
unresolved review thread existed.

Exact-head acceptance evidence:

- CI #615 (`33050193398`) — SUCCESS;
- Governance #680 (`33050193383`) — SUCCESS;
- Relational Parity #8 (`33050193369`) — SUCCESS;
- formal exact-head review `5038329220` — `READY ELIGIBLE`;
- Ready-state Governance #681 (`33050393033`) — SUCCESS.

CI #615 included successful Quality lanes for Python 3.11/3.12/3.13, the package
lane with reproducible distribution-byte verification, clean base-wheel consumer
installation, installed-wheel identity/smoke/full registered TCK conformance,
and release-evidence build/verification. It also included successful real
PostgreSQL 17.11/18.6 Relational TCK lanes and MySQL 8.4.11/9.7.2 regression
Relational TCK lanes.

Relational Parity #8 passed both real paired-database matrices from a built wheel:

- PostgreSQL 17.11 + MySQL 8.4.11;
- PostgreSQL 18.6 + MySQL 9.7.2.

The formal review authorized the Ready transition only and did not authorize its
own merge.

## 8. Main adoption evidence

The protocol maintainer explicitly authorized **squash merge PR #97** on
2026-08-27. The merge was executed with the reviewed head SHA as the expected
head guard, so any last-moment PR-head movement would have rejected the merge.

GitHub created exact main commit:

`43a437915cb078e3adde392d5560e832207ee662`

The post-merge branch state confirmed that `main` remained on that exact commit
while the main-adoption gates executed.

Exact-main CI #616 (`33051205901`) completed successfully with all expected jobs:

- Quality / Python 3.11 — SUCCESS;
- Quality / Python 3.12 — SUCCESS;
- Quality / Python 3.13 — SUCCESS;
- Package / Python 3.13 — SUCCESS;
- PostgreSQL 17.11 / Relational TCK / Python 3.13 — SUCCESS;
- PostgreSQL 18.6 / Relational TCK / Python 3.13 — SUCCESS;
- MySQL 8.4.11 / Relational TCK / Python 3.13 — SUCCESS;
- MySQL 9.7.2 / Relational TCK / Python 3.13 — SUCCESS.

The package job again passed reproducible distribution verification, built-wheel
metadata validation, clean base-wheel consumer installation, installed-wheel
identity, installed-wheel smoke, installed-wheel full registered TCK conformance,
and release-evidence build/verification on the exact main commit.

Exact-main Relational Parity #9 (`33051205914`) also completed successfully for
both supported real paired-database matrices:

- PostgreSQL 17.11 + MySQL 8.4.11 / Canonical Parity / Python 3.13 — SUCCESS;
- PostgreSQL 18.6 + MySQL 9.7.2 / Canonical Parity / Python 3.13 — SUCCESS.

Both parity jobs built the parity-capable wheel, installed both optional backend
dependencies, verified the paired database identities, and executed the real
PostgreSQL/MySQL canonical parity acceptance path.

The reviewed maintainability refactor is therefore adopted and verified on
`main`. This closes the **PostgreSQL maintainability governance work unit**.

## 9. Scope isolation and remaining governance work

This closure does not reconcile the separately governed canonical-parity roadmap
state. `ROADMAP.md` and the canonical parity acceptance record remain a distinct
follow-on documentation/governance work unit and are intentionally not changed by
this maintainability adoption record.

The repository remains in governed development mode; this work does not alter
`docs/releases/release-development-state.json` or select a release.

## 10. Non-authorizations

This adoption does not authorize or perform:

- changes to AEP-0009 or AEP-0010 lifecycle state;
- changes to Relational normative specification, requirement index, schemas, or
  language-neutral TCK semantics;
- changes to the immutable parity fixture or its lock;
- changes to MySQL portable behavior;
- PostgreSQL behavior becoming portable precedent;
- canonical-parity ROADMAP reconciliation by implication;
- release selection or publication;
- package-index publication;
- signing or attestation publication.

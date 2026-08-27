# Alpha 3 MySQL/InnoDB Relational Adapter Main Adoption

Status: **ADOPTED ON MAIN**

Adopted implementation commit: `c081b714b832b4fd0201ea01dc35fba023d06826`  
Source pull request: PR #94  
Merge method: squash  
Exact-main CI: #605 (`33035553945`)

## Decision

The reviewed MySQL/InnoDB Relational State adapter from PR #94 is adopted into
`main` as the second database-specific implementation of the already-accepted
portable Relational State profile.

This adoption is implementation evidence only. It does not change the authority
order `AEP/reconciliation -> normative spec -> requirement index -> schema -> TCK`
and does not allow MySQL/InnoDB-specific behavior to define portable AVP semantics
by implementation precedent.

## Main-adoption evidence

The protocol maintainer explicitly authorized squash merge of PR #94 on
2026-08-27. GitHub created exact main commit:

`c081b714b832b4fd0201ea01dc35fba023d06826`

Exact-main CI #605 (`33035553945`) ran against that merge commit and completed
successfully with:

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
- PostgreSQL 18.6 / Relational TCK / Python 3.13 — SUCCESS;
- MySQL 8.4.11 / Relational TCK / Python 3.13 — SUCCESS;
- MySQL 9.7.2 / Relational TCK / Python 3.13 — SUCCESS.

Both MySQL lanes build the repository wheel, install it with the optional `mysql`
extra in a clean environment, verify the real server identity, and execute the
real database-backed acceptance suite. The complete `avp-relational-state-v0.1`
profile is required by the integration test to finish with exactly
**11 PASS / 0 FAIL / 0 SKIP**.

The PostgreSQL regression lanes also remained green on the same exact-main commit,
which demonstrates that introducing the MySQL implementation did not regress the
already-adopted PostgreSQL backend path.

## Adopted implementation boundary

The implementation remains behind the existing backend-neutral
`RelationalBackendHarness`, `RelationalFixtureControl`, and `RelationalSUT`
boundaries. MySQL Connector/Python behavior, SQL/DDL, generated database/table/
column identifiers, database accounts, DSNs, collation details, InnoDB MVCC, and
native transaction handles remain implementation-private.

The adopted implementation preserves the reviewed guarantees, including:

- generated physical identifiers instead of logical AVP ids as SQL identifiers;
- separate privileged control, Subject, and evaluator authorities;
- Subject grants that exclude evaluator-private columns;
- exact scalar round-trip for the portable v0.1 type vocabulary;
- `DECIMAL(65,0)` for the portable integer range and exact `DECIMAL(p,s)` mapping;
- UTC-normalized `DATETIME(p)` storage for instant timestamps without narrowing the
  portable date domain to MySQL `TIMESTAMP` limits;
- explicit `utf8mb4_0900_bin` text collation and controlled session semantics;
- one native InnoDB transaction for atomic multi-relation fixture mutation;
- committed-state projection consistency across the atomic commit barrier;
- independent database reprojection after reset and restore;
- successful restore fidelity capped at exactly `STATE_EQUIVALENT`;
- optional MySQL Connector/Python dependency rather than a mandatory base-package
  dependency;
- real MySQL 8.4 LTS and 9.7 integration coverage in CI.

## Maintainability boundary

The MySQL implementation is intentionally split under
`src/avp_ref/tck_adapter/mysql_relational/` by responsibility rather than being
implemented as a second monolithic backend module:

- `driver.py` — optional driver loading, DSN/session policy, and SQL identifier/account safety;
- `codec.py` — scalar storage mapping and canonical round-trip conversion;
- `common.py` — implementation-private identity/projection/diff helpers;
- `resource.py` — authoritative InnoDB resource lifecycle and SUT behavior;
- `fixture.py` — privileged mutations, held transactions, quiescing, and commit barriers;
- `negative.py` — executed metadata-equivalent negative controls;
- `harness.py` — backend construction, authority separation, grants, compatibility probes, and cleanup.

The compatibility module `mysql_relational_harness.py` preserves the existing
backend import shape without collapsing these responsibilities back into a single
large implementation file.

## Roadmap effect

The roadmap item `MySQL/InnoDB adapter against the same portable TCK` may now be
marked complete because the reviewed implementation is present on `main` and has
passed exact-main database-backed conformance.

The following item remains open and separately governed:

- PostgreSQL/MySQL canonical parity acceptance evidence.

## Non-authorizations

This adoption does not authorize:

- modification of portable Relational Spec/Schema/TCK semantics;
- PostgreSQL/MySQL canonical parity acceptance by inference from independent backend
  success;
- AEP-0009 or AEP-0010 `Accepted` -> `Final` transition;
- selection or publication of `0.3.1` or another release;
- package-index publication;
- signing or attestation publication.

# Alpha 3 MySQL/InnoDB Relational Adapter Acceptance

Status: **IMPLEMENTATION REVIEW CANDIDATE — MAIN ADOPTION PENDING**

Candidate pull request: PR #94  
Candidate evidence head: `44b7ed7c931dc391be5ef304811846d1effefa45`  
Candidate base: `main@a475d63dd7fda6f80fe8a87e615e2535cb1efa02`

## Scope

PR #94 implements MySQL/InnoDB behind the already-adopted backend-neutral
`RelationalBackendHarness`, `RelationalFixtureControl`, and `RelationalSUT`
interfaces. It does not modify the portable Relational Spec, schemas, TCK cases,
shared parity fixture, or backend-neutral evaluator semantics.

The authority order remains:

`Normative Spec -> Schema -> TCK -> Reference Runtime`

MySQL SQL, Connector/Python behavior, account identities, physical database
identifiers, collations, and InnoDB transaction details are implementation-private
and do not define portable AVP semantics by precedent.

## Maintainable implementation boundary

The MySQL implementation is split under
`src/avp_ref/tck_adapter/mysql_relational/` by responsibility:

- `driver.py` owns optional driver loading, DSN/session policy, and generated SQL
  identifier/account safety;
- `codec.py` owns exact scalar storage and canonical round-trip conversion;
- `common.py` owns implementation-only identity, projection, and diff helpers;
- `resource.py` owns authoritative InnoDB resource lifecycle and SUT behavior;
- `fixture.py` owns privileged mutation, held transaction, and commit-barrier logic;
- `negative.py` owns metadata-equivalent executed negative SUTs;
- `harness.py` owns backend construction, database authority separation, grants,
  compatibility round trips, and cleanup.

A small `mysql_relational_harness.py` compatibility import preserves the existing
backend import shape without collapsing these responsibilities back into one module.

## Security and transaction guarantees

The implementation uses a privileged control connection plus generated Subject and
evaluator database accounts. Logical AVP relation and column ids are mapped to
generated physical identifiers before SQL construction. Subject grants exclude
evaluator-private columns, while evaluator authority is read-only over the complete
resource state.

Full-state observation uses an InnoDB `REPEATABLE READ` consistent read transaction.
Atomic multi-relation fixture replacement uses one native writer transaction. The
commit-barrier acceptance path therefore observes a committed pre-state while the
writer is held and verifies the fully committed post-state afterward; a torn mixture
is not accepted.

Reset and restore do not trust write success. They independently re-read canonical
state through evaluator authority. Successful portable restore fidelity remains
exactly `STATE_EQUIVALENT`.

## Portable scalar mapping

The candidate preserves the closed v0.1 portable domain without narrowing:

- boolean -> `TINYINT(1)`;
- integer -> `DECIMAL(65,0)`;
- decimal -> exact `DECIMAL(p,s)`;
- text -> `LONGTEXT` with explicit `utf8mb4_0900_bin` collation;
- binary -> `LONGBLOB`;
- date -> `DATE`;
- local time -> `TIME(p)`;
- local timestamp -> `DATETIME(p)`;
- instant timestamp -> UTC-normalized `DATETIME(p)` rather than MySQL `TIMESTAMP`;
- UUID -> `BINARY(16)`.

Compatibility probes validate canonical AVP lexical form before storage and require
an exact real-database round trip back to the same portable value.

## Exact-head evidence

CI #603 (`32952316773`) completed successfully against candidate head
`44b7ed7c931dc391be5ef304811846d1effefa45`.

Successful jobs include:

- Quality / Python 3.11;
- Quality / Python 3.12;
- Quality / Python 3.13;
- Package / Python 3.13, including reproducible distributions, clean base-wheel
  install, installed-wheel identity, reference smoke, complete registered TCK, and
  release-evidence verification;
- PostgreSQL 17.11 / Relational TCK;
- PostgreSQL 18.6 / Relational TCK;
- MySQL 8.4.11 / Relational TCK;
- MySQL 9.7.2 / Relational TCK.

Each MySQL lane builds the candidate wheel, installs it with the optional `mysql`
extra in a clean environment, verifies the real server version, and runs
`tests/test_mysql_relational_adapter.py` against the real database.

That integration suite includes a complete `avp-relational-state-v0.1` run whose
test requires exactly **11 PASS / 0 FAIL / 0 SKIP**, canonical parity-fixture digest
recomputation, atomic-visibility evidence, and the database-backed security case.

Governance #668 also completed successfully on the same candidate head.

The earlier CI #602 failure is not implementation acceptance evidence: the
`mysql:9.7.3` Docker manifest had not been published, so that job failed before
checkout or code execution. The workflow was corrected to exact, actually published
official image tags `mysql:8.4.11` and `mysql:9.7.2`; no TCK assertion or acceptance
requirement was weakened.

## Adoption boundary

This document records implementation-candidate evidence only. The ROADMAP MySQL
item must remain unchecked until the implementation is formally review-closed,
separately authorized for squash merge, adopted on `main`, and verified by
exact-main CI. Main-adoption reconciliation is a separate governance step.

PostgreSQL/MySQL canonical parity acceptance remains a later, independent work unit.

## Non-authorizations

This candidate does not authorize:

- modification of portable Relational Spec/Schema/TCK semantics;
- PostgreSQL/MySQL canonical parity acceptance;
- AEP-0009 or AEP-0010 transition to `Final`;
- release selection or publication;
- package-index publication;
- signing or attestation publication;
- merge of PR #94 without separate explicit maintainer authorization.

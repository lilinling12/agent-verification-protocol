# Alpha 3 Relational State Backend Implementation Readiness Audit

Status: **IMPLEMENTATION GATED — SHARED BACKEND CONFORMANCE HARNESS REQUIRED FIRST**

Audited main baseline: `80a72f7927b5492d1a0d92e9f3faa0594ee4bfe6`

Governing authority:

- AEP-0009 — Environment Fabric Composition and Capability Contract (`Accepted`)
- AEP-0010 — Relational State Resource Profile v0.1 (`Accepted`)
- `spec/relational/relational-state-contract.md`
- `spec/relational/manifest-integrity-contract.md`
- `spec/relational/requirement-index.yaml`
- `conformance/tck/profiles/avp-relational-state-v0.1.yaml`

This audit determines whether AVP may begin a PostgreSQL-backed implementation without allowing PostgreSQL mechanics to become portable protocol semantics.

## 1. Decision

The portable Relational State authority chain is sufficiently closed to permit backend implementation work, but the repository is **not ready to implement the PostgreSQL adapter as the next standalone change**.

The required next implementation slice is:

> a backend-neutral relational conformance harness plus immutable shared parity fixture and privileged fixture-control abstraction.

Only after that slice is review-closed may the PostgreSQL adapter be implemented against it.

This is an implementation-architecture gate, not a new protocol-semantics gate. No new AVP relational requirement is introduced here.

## 2. Evidence that protocol semantics are ready

The current profile has a complete candidate authority chain:

```text
AEP-0010 Accepted
  -> Relational normative specification
  -> requirement index AVP-RELATIONAL-001..017
  -> closed Relational schemas
  -> draft avp-relational-state-v0.1 profile
  -> mandatory execution-sensitive TCK
  -> backend-neutral reference model/runtime
```

The profile is fully mandatory: AVP-RELATIONAL-001 through AVP-RELATIONAL-017 are all required and no product-specific conditional requirement exists.

The normative contract explicitly rejects backend identity as protocol identity and prohibits SQL dialect, driver class, transaction token, dump, process identity, filesystem path, or image label from substituting for portable state identity.

The contract also requires:

- exact canonical typed-value handling;
- logical row identity independent of backend PK/index/collation;
- one committed logical observation boundary;
- QUIESCING admission closure and settlement;
- fail-closed logical binding and execution-input drift;
- canonical snapshot/reset/restore verification;
- exactly `STATE_EQUIVALENT` successful v0.1 restore fidelity;
- evaluator-private/Subject-visible separation;
- real executed conformance capable of rejecting metadata-identical broken implementations.

No unresolved protocol-level blocker was identified in this audit.

## 3. Existing implementation seam is necessary but insufficient

`TCKRunner` already accepts an injected implementation-neutral `TCKCaseAdapter`:

```text
supported_case_ids
+ evaluate(case) -> TCKCaseResult
```

This is a valid outer conformance seam and MUST be retained.

However, the currently shipped Relational TCK adapter is a reference-domain evaluator whose case implementations directly instantiate `InMemoryRelationalResource` and the built-in negative-control resource classes. It proves the portable reference behavior, but it is not yet the reusable conformance harness through which a real PostgreSQL or MySQL backend can be tested.

The CLI also currently constructs only the reference TCK runner. That is acceptable for the reference wheel, but it means a real backend path should not be introduced by adding PostgreSQL branches inside the existing reference evaluator or portable case files.

## 4. Required architecture before PostgreSQL

The next implementation PR MUST establish three separate planes.

### 4.1 Portable TCK case plane

Existing language-neutral TCK case resources remain unchanged in semantics.

They may refer only to portable concepts such as:

- Manifest / baseline Artifact identity;
- logical relation/column ids;
- typed canonical values;
- projection ids;
- logical mutation intent;
- lifecycle/barrier intent;
- logical drift intent;
- expected portable outcomes.

They MUST NOT contain PostgreSQL/MySQL branch logic, SQL strings, backend transaction ids, database names, or driver options.

### 4.2 Backend-neutral SUT conformance harness

Introduce an implementation-private test/runtime abstraction capable of driving a real implementation of the existing portable operations:

- provision;
- project;
- snapshot;
- reset;
- restore;
- diff;
- QUIESCING/final-observation participation;
- release.

Exact Python names are implementation details. The abstraction MUST NOT become a new normative AVP API and MUST NOT add generic SQL/query/transaction methods.

The harness MUST derive TCK PASS/FAIL from independently observed bytes and outcomes. An implementation-returned success flag or digest alone is insufficient where the profile requires independent reprojection.

### 4.3 Privileged fixture-control driver

Introduce a separate test-only privileged abstraction for conditions ordinary portable operations cannot safely create:

- materialize the immutable parity fixture;
- begin/hold/commit/rollback controlled Subject mutations;
- apply logical row mutation batches;
- introduce selected/unselected logical binding drift;
- coordinate concurrent commits around projection observation;
- create metadata-identical negative controls when required.

Fixture controls are not AVP Subject capabilities, Resource Capabilities, or public runtime APIs.

Backend credentials, admin DSNs, transaction handles, SQL/DDL, catalog access, and engine process/session identity MUST remain behind this fixture/backend plane.

## 5. Shared immutable parity fixture is a hard prerequisite

Before PostgreSQL-specific expected-output tests are permitted, the repository MUST materialize the shared language-neutral parity fixture described by the existing design evidence.

Recommended location:

```text
conformance/fixtures/relational-state/v0.1/
```

The fixture MUST include one canonical source of truth for:

- RelationalStateManifest bytes;
- baseline RelationalStateImage bytes;
- logical row mutation vectors;
- projection expectations or exact canonical expected bytes/digests;
- diff expectations;
- concurrency event plan;
- logical drift controls.

PostgreSQL and MySQL implementation tests MUST consume the same portable fixture artifacts. Backend setup SQL may differ, but backend-specific expected canonical output files are prohibited unless the difference itself is explicitly non-portable diagnostic metadata.

## 6. PostgreSQL implementation constraints

When PostgreSQL implementation begins, it MUST satisfy these hard rules.

### 6.1 No backend-first portable API

Do not add protocol-facing methods such as:

- `execute_sql`;
- `query`;
- `begin_transaction`;
- `commit` / `rollback`;
- `inspect_catalog`;
- `pg_snapshot`;
- `pg_dump_restore`.

Any such mechanism is implementation-private.

### 6.2 One committed observation boundary

A projection covering multiple relations must be read from one committed logical visibility point.

PostgreSQL transaction isolation/MVCC may be used to implement this property, but the chosen SQL isolation commands or snapshot tokens are not portable AVP identity.

The implementation test MUST coordinate a two-relation commit and prove the projection is either fully pre-commit or fully post-commit, never torn.

### 6.3 Exact canonical conversion

Database values MUST be converted into the existing AVP typed-value model without silent normalization or loss.

Special attention is required for:

- `numeric(65,30)` exactness;
- exact integer bounds;
- Unicode byte/character preservation without AVP normalization;
- bytea/base64url canonicalization;
- local timestamp versus instant timestamp semantics;
- fractional precision 0..6;
- UUID lowercase canonical form;
- NULL handling;
- logical key ordering independent of PostgreSQL physical/index order.

Unsupported/lossy selected backend types fail compatibility.

### 6.4 Execution-input identity

Triggers, defaults, generated expressions, constraints, routines, extensions, session/timezone semantics, schema-program revision, and other material execution inputs outside the RelationalStateManifest must bind immutable execution identity through existing Scenario/Fabric mechanisms.

A mutable catalog fingerprint may be diagnostic evidence but cannot substitute for the required immutable identity.

### 6.5 Reset and restore are verified, not trusted

Backend restore/reset command success is not AVP success.

After the implementation performs its backend mechanism, the harness MUST independently project the complete authoritative state and compare canonical StateImage identity to the baseline/snapshot target.

Successful restore fidelity is exactly `STATE_EQUIVALENT`; PostgreSQL physical snapshot or WAL fidelity MUST NOT cause AVP `EXACT` to be reported.

### 6.6 Credential and authority separation

At minimum, implementation tests MUST model separate authority for:

- Subject mutation access;
- evaluator read/verification access;
- privileged fixture/control access.

Evaluator/control passwords, admin DSNs, fixture credentials, and equivalent secrets MUST NOT appear in portable Artifacts, TCK case YAML, conformance reports, Subject-visible environment data, or committed fixture data.

A generic database admin connection MUST NOT be treated as a Subject capability.

## 7. Dependency boundary

The base `avp-reference` install currently has no database driver dependency. That should remain true unless separately justified.

A PostgreSQL implementation SHOULD therefore use an optional implementation/testing dependency rather than make PostgreSQL support mandatory for every AVP consumer.

Driver/version selection is implementation tooling and MUST be pinned/controlled by repository dependency policy and CI. It is not a protocol choice.

## 8. CI requirements for the harness slice

The shared harness/fixture PR must pass the existing full repository CI and add tests proving at least:

1. the existing in-memory reference implementation can be exercised through the new backend-neutral harness without semantic regression;
2. all mandatory Relational TCK cases remain backend-name agnostic;
3. no portable TCK case or fixture expectation branches on backend product;
4. fixture-control operations cannot be reached through the portable Subject/SUT interface;
5. privileged credential fields are absent from portable artifacts/reports;
6. metadata-identical negative controls are still rejected by observed behavior;
7. the shared fixture canonical bytes/digests are deterministic and independently validated.

The harness PR MUST NOT check the ROADMAP PostgreSQL adapter item.

## 9. PostgreSQL adapter acceptance gate

A later PostgreSQL PR may be considered complete only if all of the following are true:

- it uses the shared backend-neutral harness and shared parity fixture;
- the complete `avp-relational-state-v0.1` profile executes against the real PostgreSQL implementation path;
- mandatory cases cannot SKIP merely because the backend is difficult to control;
- projection consistency, QUIESCING, drift, reset, snapshot/restore, security visibility, and executed negative controls use real PostgreSQL behavior or test-only control seams;
- canonical bytes are independently checked by the TCK/harness;
- no PostgreSQL branch is added to portable case semantics;
- no PostgreSQL-specific field leaks into portable schemas;
- the base package remains usable without PostgreSQL dependencies unless a separate packaging decision says otherwise;
- clean CI provisions PostgreSQL reproducibly and tears it down deterministically;
- cleanup failures are infrastructure/Validity failures, not Agent Task Verdict failures;
- exact-head review and gates are green.

Only then may `PostgreSQL adapter against the portable TCK` be checked in ROADMAP.

## 10. MySQL and parity follow-on gate

MySQL/InnoDB MUST be implemented later against the same harness and fixture, not by copying PostgreSQL expectations into a second backend-specific test suite.

Cross-backend parity evidence requires exact equality where the profile defines canonical equality, while concurrency scheduling may choose different pre/post commit sides so long as neither backend returns a torn observation.

The PostgreSQL/MySQL canonical parity ROADMAP item remains blocked until both backends independently pass the full profile and the shared parity evidence is reviewed.

## 11. Current blockers and disposition

### Protocol blockers

**None found.**

The current AEP/spec/schema/TCK authority chain is sufficient to implement the accepted Relational State direction without adding backend semantics to the protocol.

### Implementation blockers

**RBIR-001 — Missing reusable backend-neutral relational conformance harness.**

The current Relational TCK evaluator directly exercises the in-memory reference resource. A real backend must not be wired by branching inside that evaluator.

**RBIR-002 — Shared immutable parity fixture not yet materialized as repository test data.**

The design exists, but PostgreSQL/MySQL must consume one concrete language-neutral fixture before backend-specific implementation expectations are added.

**RBIR-003 — Privileged fixture-control boundary not yet implemented.**

Concurrency, held transactions, logical drift, and controlled setup require a test-only privileged seam whose credentials and backend mechanics cannot leak into portable APIs or artifacts.

### Disposition

```text
Portable Relational protocol: READY
PostgreSQL standalone implementation: BLOCKED
Next governed implementation slice: SHARED BACKEND CONFORMANCE HARNESS + PARITY FIXTURE
```

Closing RBIR-001..003 authorizes review of the PostgreSQL adapter implementation slice. It does not itself authorize AEP Final, MySQL completion, release selection, publication, signing, or attestation.

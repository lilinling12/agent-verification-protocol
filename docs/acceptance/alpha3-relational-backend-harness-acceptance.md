# Alpha 3 Relational Backend Harness Acceptance

Status: **IMPLEMENTATION CANDIDATE — RBIR-001..003 CLOSED FOR PR-READINESS**

Implementation PR: #90  
Implementation semantic head: `f2fd00c93338c0e8b9d47841dfc55d97ae56d55d`  
Base `main`: `9a021265512b88919f721730416310915515c4d7`

## 1. Purpose

This audit evaluates the implementation prerequisite introduced by the Relational State backend-readiness decision before any PostgreSQL- or MySQL-specific adapter may be developed.

It evaluates only RBIR-001..003:

- **RBIR-001** — reusable backend-neutral real-backend conformance harness;
- **RBIR-002** — one immutable language-neutral parity fixture;
- **RBIR-003** — privileged fixture-control boundary for setup, held work, concurrency, and drift.

This audit does not change protocol semantics, advance AEP-0009 or AEP-0010 to Final, authorize a database-specific backend, or select a release.

## 2. Authority baseline

The reviewed authority remains:

```text
AEP-0010 Accepted
  -> Relational State normative candidate specification
  -> AVP-RELATIONAL-001..017 requirement index
  -> closed Relational State schemas
  -> mandatory avp-relational-state-v0.1 TCK
  -> backend-neutral reference behavior
  -> implementation evidence
```

The implementation delta from `main` to the semantic head contains no modification to:

- `spec/relational/**`;
- `schemas/**`;
- `conformance/tck/cases/**`;
- `conformance/tck/profiles/**`;
- `conformance/tck/registry.yaml`;
- AEP-0009 or AEP-0010.

Therefore the harness consumes the accepted portable semantics rather than redefining them.

## 3. RBIR-001 — backend-neutral conformance harness

**Disposition: CLOSED FOR PR-READINESS.**

The implementation introduces three strongly separated contracts:

1. `RelationalSUT` — portable observable/lifecycle operations only;
2. `RelationalFixtureControl` — privileged logical test controls only;
3. `RelationalBackendHarness` — backend provisioning, canonical identity derivation, and scalar compatibility.

`RelationalConformanceTCKAdapter` no longer imports `InMemoryRelationalResource` or the concrete negative-control resource classes. The evaluator receives a `RelationalBackendHarness` and expresses the same portable case assertions independently of backend product.

`ReferenceConformanceAdapter` now executes Relational State through `RelationalBackendTCKAdapter(InMemoryRelationalBackendHarness())`. This proves that the repository's normal reference/full-TCK path uses the same backend-neutral harness boundary that a real database implementation must later implement.

The harness deliberately excludes public operations equivalent to:

- `executeSql` or generic query;
- begin/commit/rollback transaction APIs;
- DDL or catalog inspection;
- backend snapshot/backup tokens;
- admin credentials/DSNs;
- backend product switches.

The materialized `RelationalResourceSpec` freezes baseline relations and rows before provisioning. Canonical identity is computed from that frozen baseline, preventing caller mutation after identity calculation from changing the provisioning preimage.

## 4. RBIR-002 — immutable shared parity fixture

**Disposition: CLOSED FOR PR-READINESS.**

The shared fixture is:

```text
conformance/fixtures/relational-state/v0.1/parity-fixture.json
conformance/fixtures/relational-state/v0.1/parity-fixture.sha256
```

The fixture is backend-neutral and contains no PostgreSQL/MySQL branch or backend-specific SQL/DDL.

It covers:

- every mandatory v0.1 scalar kind;
- nullable state;
- exact composed/decomposed Unicode distinction;
- composite logical row keys;
- `consistency.left` and `consistency.right`;
- `consistency.pair`, `parity.all`, and `parity.keys-and-values` projections;
- one logical multi-relation atomic epoch mutation;
- language-neutral logical drift controls.

The fixture also binds shared expected evidence rather than only shared input:

- Manifest digest;
- baseline StateImage digest;
- all baseline projection digests;
- post-mutation StateImage digest;
- semantic diff digest and logical UPDATE changes.

The loader fails closed unless:

1. repository bytes are already canonical JSON exact bytes;
2. raw SHA-256 matches the independent `.sha256` lock;
3. profile/revision identity is correct;
4. the Manifest is semantically valid;
5. baseline and mutation rows satisfy the Manifest/scalar model;
6. expected Manifest/baseline identities recompute correctly;
7. expected projection/diff identity fields are structurally complete and valid.

Tests independently recompute expected evidence from actual SUT observations. Fixture-declared expected digests are never sufficient by themselves to establish conformance.

During development, the SHA lock initially contained a malformed 62-character digest. The strict loader rejected it on all Python versions. The fix corrected the lock to the exact 64-character SHA-256 of the canonical fixture bytes; no validation rule was relaxed.

## 5. RBIR-003 — privileged fixture-control boundary

**Disposition: CLOSED FOR PR-READINESS.**

Privileged logical controls are separated from `RelationalSUT` and include:

- committed relation replacement;
- atomic multi-relation replacement;
- projection coordinated around an atomic commit;
- held Subject mutation by harness-local label;
- commit/rollback settlement of held work;
- logical-binding validity control;
- execution-input identity drift control.

Native transaction handles never cross the fixture boundary. The in-memory driver may directly access implementation-private state only inside the privileged fixture implementation. A future database driver may use SQL, DDL, admin connections, native transactions, or synchronization internally, but callers still see only the logical fixture-control vocabulary.

`project_during_atomic_commit` provides the explicit real-backend concurrency seam required by the `consistency.pair` case. The portable expectation remains only:

```text
fully pre-commit OR fully post-commit
never torn
```

The in-memory harness deterministically chooses the valid post-commit side. A PostgreSQL/MySQL harness may coordinate real concurrent sessions internally without changing the TCK case.

## 6. Negative-control and anti-self-certification review

The generic evaluator selects metadata-equivalent broken behavior through backend-neutral `NegativeControl` identities:

- torn projection;
- false restore;
- evaluator-private state leak;
- execution-input drift acceptance.

Concrete broken resource classes are confined to the in-memory harness implementation.

Mandatory Relational TCK execution still rejects those broken observable behaviors. Neither capability metadata nor a backend name can produce a PASS without the relevant operation path executing.

## 7. Security and authority review

The shared `RelationalSUT` contract exposes no fixture mutation authority, SQL API, credential field, DSN, native transaction handle, or backend-specific control.

Tests explicitly assert fixture-only methods are absent from the SUT protocol.

The implementation does not change:

- evaluator-private visibility semantics;
- Subject authorization semantics;
- Artifact identity/retrieval authorization;
- SecurityAssurance claims.

No isolation/sandbox assurance is inferred from choosing a database backend.

## 8. Reset / restore / lifecycle review

The harness does not replace portable reset/restore verification with backend command success.

Existing Relational behavior remains authoritative:

- reset success requires independent full-state reprojection to the bound baseline identity;
- restore success requires independent full-state reprojection to the snapshot StateImage identity;
- successful v0.1 restore remains exactly `STATE_EQUIVALENT`;
- `EXACT` is not introduced;
- QUIESCING closes new mutation admission and waits for accepted work settlement.

Held-mutation fixture controls use harness-local labels and exercise real settlement behavior without exposing native transaction identity.

## 9. Packaging review

No new runtime dependency or database driver is added to `pyproject.toml`.

The base `avp-reference` wheel remains database-driver independent. A future PostgreSQL packaging decision must therefore be explicit rather than becoming an accidental mandatory dependency through this harness slice.

## 10. Executed evidence

Implementation semantic head `f2fd00c93338c0e8b9d47841dfc55d97ae56d55d` passed:

- CI #586 — SUCCESS;
  - Quality / Python 3.11 — SUCCESS;
  - Quality / Python 3.12 — SUCCESS;
  - Quality / Python 3.13 — SUCCESS;
  - reproducible distribution build — SUCCESS;
  - clean-consumer installation — SUCCESS;
  - installed-wheel identity — SUCCESS;
  - installed-wheel full TCK conformance — SUCCESS;
  - release-evidence build and verification — SUCCESS;
- Governance #649 — SUCCESS.

The earlier strengthened-fixture head also demonstrated that malformed identity data fails closed: CI #582 failed only in the new fixture tests because the lock had an invalid SHA-256 length, while the package job and installed-wheel full TCK remained successful. The exact lock was corrected and the strict rule retained.

Release Validation is not treated as executed evidence for this implementation head unless the workflow is actually triggered for the changed path set. No synthetic or inferred Release Validation result is recorded here.

## 11. Closure decision

At the reviewed semantic implementation head, RBIR-001, RBIR-002, and RBIR-003 have implementation candidates sufficient for PR-readiness review:

```text
RBIR-001 CLOSED FOR PR-READINESS
RBIR-002 CLOSED FOR PR-READINESS
RBIR-003 CLOSED FOR PR-READINESS
```

This means a PostgreSQL adapter may become the **next separately governed work unit only after PR #90 is itself review-closed and adopted into `main` under explicit merge authorization**.

It does not authorize PostgreSQL implementation inside PR #90, MySQL implementation, cross-backend parity acceptance, AEP Final transition, release/version selection, publication, signing, or attestation.

The ROADMAP prerequisite remains unchecked until this reviewed harness slice is adopted by `main`, preserving the repository's distinction between a review-ready PR and mainline implementation state.

# Alpha 3 Relational State Normative Closure Audit

Status: **READY — FORMAL PROTOCOL RE-REVIEW CLOSED**

Audit scope: PR #87, `feat/alpha3-relational-state-contract`

Current semantic closure head: `07aeed2a7b056eb630d2371f8ebdee0ea7e45038`

Base authority head: AEP-0010 Accepted at `2e86f8dd6eef8668b6e288e96347cb46088abc1a`

Formal blocking review: `5006694486`

Acceptance-oriented re-review: `5006822376`

This document is non-normative acceptance/governance evidence. It does not promote the Relational State candidate to Final, merge PR #87, select a release version, authorize PostgreSQL/MySQL implementation, or authorize publication/signing/attestation.

## 1. Result and audit history

The `avp-relational-state-v0.1` authority slice is closed as a complete draft normative candidate downstream of Accepted AEP-0010.

An earlier construction audit at semantic head `cbeaa01ae417a4bc0f04044a67c4eadd727d5180` concluded that the candidate surface was structurally closed. That conclusion was **superseded for merge-readiness** by formal protocol review `5006694486` at `7eebeefa8f0187372970fa1ea8244bd1fed6986e`, which found five executable authority-chain gaps not detected by the then-green traceability and package gates.

PR #87 was returned to Draft. The five findings were recorded as `RSR-PR-001..RSR-PR-005` in `docs/design/alpha3-relational-state-protocol-review-blockers.md`, fixed without changing the Accepted AEP-0010 direction or introducing backend-specific semantics, and re-reviewed at exact semantic head `07aeed2a7b056eb630d2371f8ebdee0ea7e45038`.

Acceptance-oriented re-review `5006822376` found all five blockers closed and no new cross-contract semantic blocker.

The audited authority order remains:

```text
AEP-0010 Accepted
  -> Relational normative specifications
  -> requirement index
  -> closed machine-readable schemas
  -> execution-sensitive TCK profile/cases
  -> backend-neutral reference behavior and TCK adapters
```

No backend implementation is used as protocol authority.

## 2. Normative surface

The candidate owns:

- `spec/relational/relational-state-contract.md`
- `spec/relational/manifest-integrity-contract.md`
- `spec/relational/requirement-index.yaml`

The requirement index contains `AVP-RELATIONAL-001` through `AVP-RELATIONAL-017`.

`AVP-RELATIONAL-017` owns semantic Manifest graph integrity that JSON Schema shape validation cannot express by itself: unique relation/column/projection identities, non-duplicated logical row-key declarations, resolvable projection references, and mandatory projection inclusion of logical row-key columns.

The candidate remains a draft normative candidate. AEP-0010 remains Accepted, not Final.

## 3. Schema closure

The candidate owns five closed schemas:

- `schemas/relational-value.schema.json`
- `schemas/relational-state-manifest.schema.json`
- `schemas/relational-state-image.schema.json`
- `schemas/relational-projection.schema.json`
- `schemas/relational-diff.schema.json`

Protocol-owned objects remain closed. There is no generic backend property bag, SQL/driver configuration object, backend-product discriminator, physical catalog identity, or backend snapshot token that can become de facto portable semantics.

## 4. Formal review blocker closure

### RSR-PR-001 — canonical Manifest/baseline identity

**CLOSED.** `RelationalManifest` now emits the schema-shaped canonical logical document and derives SHA-256 identity from canonical bytes. Resource admission verifies the bound Manifest Artifact digest against those bytes, validates/canonicalizes baseline state, derives the baseline `RelationalStateImage` identity, and rejects a mismatching expected baseline Artifact digest. Mandatory identity TCK executes both Manifest and baseline digest tamper controls.

### RSR-PR-002 — Manifest semantic integrity at admission

**CLOSED.** `RelationalManifest.validate_integrity()` executes the AVP-RELATIONAL-017 graph constraints and is invoked by the resource admission path before identity binding, baseline establishment, or Subject side effects. The focused helper delegates to the same implementation. The Manifest-integrity TCK both executes all eight invalid graph controls and proves an invalid graph cannot establish a usable resource.

### RSR-PR-003 — complete scalar conformance

**CLOSED.** The mandatory canonical case now executes the complete v0.1 scalar vocabulary and relevant parameter/nullability boundaries: boolean, integer, decimal, text, binary, date, time-local, timestamp-local, timestamp-instant, UUID, nullable values, decimal precision/scale, temporal precision, Unicode non-normalization, canonical unpadded base64url, Gregorian validity, UTC `Z`, and fail-closed invalid controls.

### RSR-PR-004 — normative RelationalDiff output

**CLOSED.** Reference `RelationalDiff` now emits the normative protocol object with `manifestDigest`, scope, `beforeDigest`, `afterDigest`, canonical logical key, and change-specific before/after values. The generated document is validated offline against repository-owned normative schemas; mandatory TCK asserts identity binding, deterministic logical change semantics, and delete-old/insert-new key-change behavior.

### RSR-PR-005 — SnapshotRef owner-instance staleness

**CLOSED.** Relational snapshots now bind an opaque resource-instance identity in addition to public Environment/resource identifiers and Manifest-bound state. Restore rejects foreign ownership, instance mismatch, and Manifest identity mismatch. Mandatory snapshot/reset TCK executes a stale same-public-id replacement resource and requires the old snapshot to fail closed, while retaining foreign-Environment rejection and exact reset verification.

The opaque instance identity is reference-implementation evidence for the existing owner-instance/stale-reference semantics; it is not a new portable backend identifier.

## 5. TCK closure

Profile:

- `avp-relational-state-v0.1`

Mandatory Relational cases: 11.

1. `AVP-TCK-RELATIONAL-IDENTITY-001`
2. `AVP-TCK-RELATIONAL-CANONICAL-001`
3. `AVP-TCK-RELATIONAL-PROJECTION-001`
4. `AVP-TCK-RELATIONAL-QUIESCING-001`
5. `AVP-TCK-RELATIONAL-DRIFT-001`
6. `AVP-TCK-RELATIONAL-SNAPSHOT-RESET-001`
7. `AVP-TCK-RELATIONAL-RESTORE-001`
8. `AVP-TCK-RELATIONAL-DIFF-001`
9. `AVP-TCK-RELATIONAL-SECURITY-001`
10. `AVP-TCK-RELATIONAL-EXECUTED-CAPABILITY-001`
11. `AVP-TCK-RELATIONAL-MANIFEST-INTEGRITY-001`

The execution-sensitive negative controls cover, among other cases:

- Manifest and baseline content-address identity tampering;
- invalid/ambiguous Manifest graphs and admission rejection;
- invalid scalar lexical forms/type parameters/nullability;
- torn multi-relation projection;
- false restore success;
- stale/foreign snapshot references;
- evaluator-private state leakage;
- execution-input identity drift.

The global registry remains at 90 registered cases / 12 profiles / 117 indexed requirements; the strengthened vectors do not invent a second profile or backend-specific case family.

## 6. Reference-runtime alignment

Portable reference behavior remains in:

- `src/avp_ref/relational.py`
- `src/avp_ref/relational_manifest.py`
- `src/avp_ref/tck_adapter/reference_relational.py`
- `src/avp_ref/tck_adapter/reference_relational_manifest.py`

The reference implementation remains backend-neutral. It exposes no AVP SQL/query/transaction API, PostgreSQL/MySQL product branch, database driver API, connection-string contract, physical catalog identity, or backend snapshot-token identity.

Accepted AEP-0010 decisions remain intact:

- canonical Manifest and StateImage exact-byte identities are portable state identities;
- logical row identity is Manifest-defined, not backend PK/tuple identity;
- evaluator-private authoritative state may exist while Subject-visible routes remain non-disclosing;
- execution-relevant database program/config identity remains separate from logical relational state identity and fails closed on drift;
- QUIESCING closes new Subject mutation admission and requires accepted work to settle before final verification;
- reset succeeds only after independent reprojection proves baseline identity;
- successful v0.1 relational restore reports exactly `STATE_EQUIVALENT`;
- `EXACT` relational restore remains forbidden in the base profile;
- semantic diff uses logical row identity and explicit before/after state identity;
- no backend implementation can widen Subject capability or security assurance.

## 7. No-transitional-implementation audit

The candidate introduces none of the following:

- PostgreSQL-first or MySQL-first semantics later intended to be generalized;
- temporary public shims/stubs;
- untyped public extension/property bags as placeholders;
- backend-specific TCK branches;
- generic `supports_*` feature flags replacing governed capability identity;
- SQL/query/transaction APIs as portable AVP protocol;
- backend product/catalog metadata as conformance proof.

PostgreSQL and MySQL remain future implementation evidence against the same portable TCK.

## 8. Exact semantic-head evidence

Semantic closure head:

`07aeed2a7b056eb630d2371f8ebdee0ea7e45038`

- CI #554: SUCCESS
  - Quality / Python 3.11: SUCCESS
  - Quality / Python 3.12: SUCCESS
  - Quality / Python 3.13: SUCCESS
  - Package / Python 3.13: SUCCESS
  - reproducible distribution bytes: SUCCESS
  - built-wheel metadata: SUCCESS
  - clean consumer installation: SUCCESS
  - installed-wheel identity/smoke: SUCCESS
  - installed-wheel full registered TCK: SUCCESS
  - release-evidence build/verify: SUCCESS
- Governance #606: SUCCESS
- Release Validation #70: SUCCESS
- acceptance-oriented semantic re-review `5006822376`: RSR-PR-001..005 CLOSED; no new semantic blocker.

The earlier CI #548 / Governance #596 evidence at `cbeaa01...` remains historical construction evidence only and is not the active protocol-review closure baseline.

## 9. Closure boundary

This audit closes the Relational State **draft normative candidate formal protocol-review** gate at the semantic head above.

It does not mean:

- PR #87 is merged;
- the candidate or AEP-0010 is Final;
- PostgreSQL/MySQL adapters or cross-backend parity evidence exist;
- a release version has been selected;
- `0.3.1` publication is authorized;
- package-index publication, signing, or attestation is authorized.

After this audit and blocker-ledger synchronization, only governance metadata has changed from the reviewed semantic head. The remaining gate before returning PR #87 to Ready is exact-head CI/Governance/Release Validation plus base-drift and review/comment/thread verification. Merge remains a separate explicit authorization boundary.
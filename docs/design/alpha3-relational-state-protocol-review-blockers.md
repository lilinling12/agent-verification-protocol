# Alpha 3 Relational State Protocol Review Blockers

Status: **CLOSED — ACCEPTANCE-ORIENTED RE-REVIEW PASSED**

Formal review baseline: `7eebeefa8f0187372970fa1ea8244bd1fed6986e`

Formal blocking review: PR #87 review `5006694486`

Semantic closure head: `07aeed2a7b056eb630d2371f8ebdee0ea7e45038`

Acceptance-oriented re-review: PR #87 review `5006822376`

Base authority: AEP-0010 Accepted at `2e86f8dd6eef8668b6e288e96347cb46088abc1a`

This document is a non-normative blocker/closure ledger. It does not change AEP-0010, authorize merge, authorize backend implementation, select a release, or promote any candidate to Final.

## Review rule

The review applies the repository authority order:

```text
Accepted AEP direction
  -> Normative Spec
  -> Schema
  -> executable TCK
  -> reference runtime
```

A green traceability or package gate is necessary but cannot close a semantic blocker when the executable authority chain permits an implementation that violates the written contract.

## RSR-PR-001 — Canonical Manifest and baseline identity is trusted, not executed

Status: **CLOSED**

### Original finding

The pre-review reference resource accepted an externally supplied Manifest digest without proving that it was SHA-256 over canonical `RelationalStateManifest` bytes. The baseline logical rows were also reconstructed internally without independently verifying the bound baseline `RelationalStateImage` Artifact identity.

### Incorporated closure

- `RelationalManifest.as_document()` emits the profile-defined schema-shaped logical Manifest representation.
- `RelationalManifest.digest` derives SHA-256 from canonical serialized bytes.
- resource admission treats the bound Manifest Artifact digest as an expected identity and rejects mismatch.
- baseline rows are validated and canonicalized into a `RelationalStateImage`; the bound baseline Artifact digest is verified against the resulting exact StateImage identity.
- `AVP-TCK-RELATIONAL-IDENTITY-001` executes both Manifest-digest and baseline-digest tamper controls before the resource is usable.

The authority remains the Spec/Schema/TCK; the reference implementation only demonstrates that binding.

## RSR-PR-002 — Manifest semantic integrity is not enforced at resource admission

Status: **CLOSED**

### Original finding

`validate_manifest_integrity()` existed and the dedicated TCK called it directly, but the pre-review reference resource admission path did not apply the same semantic graph validation.

### Incorporated closure

- `RelationalManifest.validate_integrity()` is the single reference implementation of the AVP-RELATIONAL-017 graph checks.
- resource construction invokes that validation before identity binding, baseline establishment, ready use, or Subject side effects.
- `relational_manifest.validate_manifest_integrity()` delegates to the same method rather than duplicating semantics.
- `AVP-TCK-RELATIONAL-MANIFEST-INTEGRITY-001` still executes all eight duplicate/dangling/key-incomplete controls and additionally proves an invalid graph is rejected at resource admission.

## RSR-PR-003 — Mandatory scalar conformance is incomplete

Status: **CLOSED**

### Original finding

AVP-RELATIONAL-003 defines a closed mandatory scalar vocabulary, while the pre-review canonical TCK exercised only integer/decimal/text plus a narrow invalid-control set.

### Incorporated closure

The mandatory canonical case now executes positive and fail-closed behavior for the complete v0.1 scalar model and relevant parameters:

- boolean value typing;
- integer canonical form and 65-digit boundary;
- decimal precision/scale, exact lexical scale, precision overflow, exponent rejection, and negative-zero rejection;
- exact text/Unicode identity without normalization;
- canonical unpadded base64url;
- valid/invalid Gregorian dates;
- time-local precision, 24:00 rejection, leap-second rejection, and precision mismatch;
- timestamp-local precision and no-zone semantics;
- timestamp-instant UTC `Z` semantics;
- lowercase canonical UUID;
- nullable value acceptance only when the Manifest column is nullable;
- invalid decimal and temporal type-parameter boundaries.

The case remains backend-neutral and contains no PostgreSQL/MySQL behavior branch.

## RSR-PR-004 — Reference RelationalDiff is not the normative schema object

Status: **CLOSED**

### Original finding

The pre-review runtime exposed only internal `(relation_id, change, key_bytes)` records while `schemas/relational-diff.schema.json` defines a portable protocol object with explicit identity bindings.

### Incorporated closure

`RelationalDiff.as_document()` now emits the normative object surface:

- `apiVersion` / `kind`;
- `manifestDigest`;
- full/projection `scope`;
- `beforeDigest`;
- `afterDigest`;
- deterministic change records with canonical logical key;
- INSERT `after`, DELETE `before`, and UPDATE `before` + `after` state values.

The reference diff remains logical-key based, and a key change is represented as delete-old plus insert-new. Unit validation resolves the repository-owned relational value schema offline and validates the resulting document against the normative diff schema. The mandatory diff TCK also asserts Manifest/scope/before/after identity binding and change semantics.

## RSR-PR-005 — SnapshotRef owner-instance staleness is too weak

Status: **CLOSED**

### Original finding

Snapshot ownership previously compared public Environment/resource identifiers and Manifest digest only. A replacement resource with the same public ids and Manifest could therefore accept a stale snapshot.

### Incorporated closure

- reference snapshots now bind an opaque resource-instance identity in addition to public Environment/resource ids and the Manifest-bound StateImage.
- restore rejects foreign Environment/resource ownership, resource-instance mismatch, and Manifest identity mismatch.
- `AVP-TCK-RELATIONAL-SNAPSHOT-RESET-001` executes a same-public-id replacement resource with a different instance identity and requires the old snapshot to fail closed.
- the existing foreign-Environment negative control and exact baseline reset verification remain mandatory.

The opaque reference-model owner-instance value is implementation evidence, not a new portable backend identifier or public protocol property.

## Acceptance-oriented re-review

Exact semantic head:

`07aeed2a7b056eb630d2371f8ebdee0ea7e45038`

Re-review `5006822376` found:

- RSR-PR-001 CLOSED;
- RSR-PR-002 CLOSED;
- RSR-PR-003 CLOSED;
- RSR-PR-004 CLOSED;
- RSR-PR-005 CLOSED;
- no new blocker against Accepted AEP-0010, Environment stale-reference semantics, Evidence content-address identity, Core QUIESCING, Security visibility, or the no-transitional-implementation gate.

Exact semantic-head evidence:

- CI #554: SUCCESS;
- Quality / Python 3.11: SUCCESS;
- Quality / Python 3.12: SUCCESS;
- Quality / Python 3.13: SUCCESS;
- Package / Python 3.13: SUCCESS;
- reproducible distribution bytes: SUCCESS;
- clean consumer install and identity/smoke: SUCCESS;
- installed-wheel full registered TCK: SUCCESS;
- release-evidence build/verify: SUCCESS;
- Governance #606: SUCCESS;
- Release Validation #70: SUCCESS.

## Closure boundary

The five formal protocol-review blockers are closed at the semantic head above. The remaining work on PR #87 is governance synchronization only:

1. reconcile the earlier normative closure audit so it records the formal blocking review and re-review rather than presenting the pre-review READY conclusion as current;
2. update PR metadata to the current state;
3. require exact-head CI/Governance/Release Validation after those governance-only changes;
4. verify base drift and review/comment/thread state;
5. only then return PR #87 to Ready.

Merge remains a separate explicit authorization boundary. Closing these blockers does not authorize Final, PostgreSQL/MySQL implementation, release selection/publication, package-index publication, signing, or attestation.
# Alpha 3 Relational State Protocol Review Blockers

Status: **OPEN — PR #87 PROTOCOL REVIEW BLOCKED**

Review baseline: `7eebeefa8f0187372970fa1ea8244bd1fed6986e`

Formal review: PR #87 review `5006694486`

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

Status: **OPEN**

### Finding

The reference resource accepts an externally supplied Manifest digest without proving that it is SHA-256 over the canonical `RelationalStateManifest` bytes. The baseline logical rows are also reconstructed internally without independently verifying the bound baseline `RelationalStateImage` Artifact identity.

The current identity TCK therefore proves equality among declared digest strings, but does not prove content-address binding.

### Required closure

- provide schema-shaped canonical Manifest serialization;
- derive the Manifest digest from those canonical bytes;
- treat the externally bound Manifest Artifact digest only as an expected identity and reject mismatch;
- derive the canonical baseline StateImage after semantic validation;
- treat the bound baseline Artifact digest only as an expected identity and reject mismatch;
- add positive and tampered-identity TCK controls that execute rejection before the resource becomes usable.

## RSR-PR-002 — Manifest semantic integrity is not enforced at resource admission

Status: **OPEN**

### Finding

`validate_manifest_integrity()` exists and the dedicated TCK calls it directly, but the reference resource admission path does not apply the same semantic graph validation.

That leaves a gap between AVP-RELATIONAL-017 and the SUT boundary that is supposed to reject invalid manifests before ready state or Subject side effects.

### Required closure

- make Manifest semantic validation part of resource admission;
- preserve the standalone validator as a downstream reference helper, not a second source of semantics;
- prove an invalid Manifest cannot establish a usable resource.

## RSR-PR-003 — Mandatory scalar conformance is incomplete

Status: **OPEN**

### Finding

AVP-RELATIONAL-003 defines a closed mandatory scalar vocabulary, but `AVP-TCK-RELATIONAL-CANONICAL-001` currently executes only integer/decimal/text values and three invalid lexical controls.

### Required closure

The mandatory TCK must execute positive and fail-closed controls for the complete v0.1 scalar model and relevant declared parameters, including:

- boolean;
- integer boundary/canonical form;
- decimal precision/scale and negative-zero rules;
- text exact Unicode identity;
- canonical unpadded base64url;
- valid Gregorian date/range;
- time-local precision and invalid 24:00/leap-second forms;
- timestamp-local precision/no-zone semantics;
- timestamp-instant UTC `Z` semantics;
- lowercase canonical UUID;
- invalid decimal type parameters and invalid temporal precision.

## RSR-PR-004 — Reference RelationalDiff is not the normative schema object

Status: **OPEN**

### Finding

`schemas/relational-diff.schema.json` requires Manifest/scope/before/after identity binding and canonical change objects. The current runtime exposes only internal `(relation_id, change, key_bytes)` records, and the TCK inspects that internal representation.

### Required closure

- produce a schema-shaped `RelationalDiff` document;
- bind `manifestDigest`, scope, `beforeDigest`, and `afterDigest`;
- expose canonical key plus before/after row values where applicable;
- validate the generated document against the normative schema in tests/TCK;
- keep key-change semantics as delete-old plus insert-new.

## RSR-PR-005 — SnapshotRef owner-instance staleness is too weak

Status: **OPEN**

### Finding

Snapshot ownership currently compares public Environment/resource identifiers and Manifest digest. It does not distinguish two different resource instances that reuse those identifiers.

A snapshot created by a released instance can therefore be accepted by a replacement instance with the same ids and Manifest, violating reused Environment instance ownership/stale-reference semantics.

### Required closure

- bind snapshots to an opaque resource-instance identity in the reference model;
- reject same-id/same-Manifest snapshots created by a different instance;
- retain foreign-environment rejection;
- add the same-id replacement stale-snapshot negative control to mandatory TCK coverage.

## Closure gate

All five blockers must be incorporated before this document may become CLOSED.

After incorporation:

1. run exact-head CI on Python 3.11/3.12/3.13;
2. require built-wheel full registered TCK success;
3. require Governance and Release Validation success;
4. reconcile the prior normative closure audit;
5. perform acceptance-oriented protocol re-review against the exact semantic head;
6. only then return PR #87 to Ready.

Merge remains a separate explicit authorization boundary.
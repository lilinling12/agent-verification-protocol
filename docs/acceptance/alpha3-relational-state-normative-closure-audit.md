# Alpha 3 Relational State Normative Closure Audit

Status: **READY — RELATIONAL STATE NORMATIVE CANDIDATE CLOSED**

Audit scope: PR #87, `feat/alpha3-relational-state-contract`

Semantic closure head: `cbeaa01ae417a4bc0f04044a67c4eadd727d5180`

Base authority head: AEP-0010 Accepted at `2e86f8dd6eef8668b6e288e96347cb46088abc1a`

This document is non-normative acceptance/governance evidence. It does not promote the Relational State candidate to Final, merge PR #87, select a release version, authorize PostgreSQL/MySQL implementation, or authorize publication/signing/attestation.

## 1. Result

The `avp-relational-state-v0.1` authority slice is closed as a complete draft normative candidate downstream of Accepted AEP-0010.

The audited authority order is:

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

The candidate owns two coherent specification files:

- `spec/relational/relational-state-contract.md`
- `spec/relational/manifest-integrity-contract.md`

The requirement index is:

- `spec/relational/requirement-index.yaml`

It contains `AVP-RELATIONAL-001` through `AVP-RELATIONAL-017`.

`AVP-RELATIONAL-017` was added during manual closure review rather than hidden inside reference code. It closes semantic Manifest graph integrity that JSON Schema shape validation cannot express by itself: unique relation/column/projection identities, non-duplicated logical row-key declarations, resolvable projection references, and mandatory projection inclusion of logical row-key columns.

The candidate remains `draft-normative-candidate`; AEP-0010 remains Accepted, not Final.

## 3. Schema closure

The candidate owns five closed schemas:

- `schemas/relational-value.schema.json`
- `schemas/relational-state-manifest.schema.json`
- `schemas/relational-state-image.schema.json`
- `schemas/relational-projection.schema.json`
- `schemas/relational-diff.schema.json`

Protocol-owned objects are closed. There is no generic backend property bag, SQL/driver configuration object, or backend-product discriminator that can become de facto portable semantics.

The Manifest schema restricts type parameters to their valid scalar families. Cross-object/reference constraints that JSON Schema does not reliably express are owned by `AVP-RELATIONAL-017` and executed by TCK rather than silently delegated to implementation convention.

## 4. TCK closure

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

The Manifest-integrity case executes eight fail-closed controls:

- duplicate relation id;
- duplicate column id;
- duplicate row-key column;
- duplicate projection id;
- duplicate relation selection within a projection;
- unknown projected relation;
- unknown projected column;
- projection missing a required logical row-key column.

The existing execution-sensitive negative controls also continue to cover torn projection, false restore success, evaluator-private state leakage, and execution-input drift. Mandatory cases execute reference behavior; they do not return PASS from expected metadata alone.

At semantic closure head `cbeaa01ae417a4bc0f04044a67c4eadd727d5180`, repository traceability reports:

- 117 indexed requirements;
- 90 registered TCK cases;
- 12 profiles;
- normative-surface closure `READY`, blockers `0`.

The checked-in example ConformanceReport is bound to the exact 90-case registry digest:

`sha256:be5f961ffa336575d6f1f7ba4070c0e49c9ff6b9d0d69b5a11949f917da93418`

## 5. Reference-runtime alignment

Portable reference behavior is implemented in:

- `src/avp_ref/relational.py`
- `src/avp_ref/relational_manifest.py`
- `src/avp_ref/tck_adapter/reference_relational.py`
- `src/avp_ref/tck_adapter/reference_relational_manifest.py`

The composite conformance adapter registers both Relational adapters with non-overlapping case ownership.

The reference implementation remains backend-neutral. It exposes no AVP SQL/query/transaction API, PostgreSQL/MySQL product branch, database driver API, connection-string contract, physical catalog identity, or backend snapshot-token identity.

Manual review confirmed the following accepted AEP-0010 decisions remain intact:

- StateImage identity remains canonical exact-byte relational state identity;
- logical row identity is Manifest-defined, not backend PK/tuple identity;
- evaluator-private authoritative state may exist while Subject-visible routes remain non-disclosing;
- execution-relevant database program/config identity remains separate from logical relational state identity and fails closed on drift;
- QUIESCING closes new Subject mutation admission and requires accepted work to settle before final verification;
- reset succeeds only after independent reprojection proves baseline identity;
- successful v0.1 relational restore reports exactly `STATE_EQUIVALENT`;
- `EXACT` relational restore remains forbidden in the base profile;
- semantic diff uses logical row identity rather than backend operation order;
- no backend implementation can widen Subject capability or security assurance.

## 6. No-transitional-implementation audit

The candidate introduces none of the following:

- PostgreSQL-first semantics later intended to be generalized;
- MySQL-first semantics later intended to be generalized;
- temporary public shims/stubs;
- untyped public extension/property bags as placeholders;
- backend-specific TCK branches;
- generic `supports_*` feature flags that can replace governed capability identity;
- SQL/query/transaction APIs as portable AVP protocol;
- backend product/catalog metadata as conformance proof.

PostgreSQL and MySQL remain future implementation evidence against the same portable TCK.

## 7. Exact-head gates used for semantic closure

Semantic closure head: `cbeaa01ae417a4bc0f04044a67c4eadd727d5180`.

- CI #548: SUCCESS
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
- Governance #596: SUCCESS

No PR review/comment blocker was present at the time of this audit.

## 8. Closure boundary

This audit closes the Relational State **draft normative candidate construction** gate.

It does not mean:

- PR #87 is merged;
- the candidate is Final;
- AEP-0010 is Final;
- PostgreSQL or MySQL adapters are authorized by this document;
- cross-backend parity evidence exists;
- a release version has been selected;
- `0.3.1` publication is authorized;
- PyPI/package-index publication, signing, or attestation is authorized.

The next repository lifecycle action after governance-only synchronization and final exact-head green gates is to mark PR #87 Ready for protocol review. Merge remains a separate explicit authorization boundary.

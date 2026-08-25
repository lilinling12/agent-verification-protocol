# Alpha 3 Relational State Profile Design Audit

Status: **DRAFT BLOCKERS CLOSED — AEP RECONCILIATION REQUIRED**

Parent authority: AEP-0009 (Accepted)
Proposal: AEP-0010 (Draft)

## 1. Purpose

This is the controlling non-normative readiness audit for AEP-0010. It tracks whether the relational resource-domain semantics are precise enough to enter protocol review without allowing PostgreSQL/MySQL implementation precedent to define AVP behavior.

Authority order remains:

```text
AEP-0010 Draft -> Proposed -> Accepted
  -> relational normative specification
  -> requirement index
  -> closed schemas
  -> execution-sensitive TCK
  -> backend-neutral reference model where useful
  -> PostgreSQL adapter
  -> MySQL/InnoDB adapter
  -> cross-backend parity evidence
```

No database adapter or normative surface is authorized by this audit.

## 2. Existing authority reused

Relational State specializes rather than replaces existing contracts:

- Environment owns authoritative resources, Scenario binding, projection identity, SnapshotRef ownership, restore fidelity, semantic diff, and stale-handle failure.
- Fabric owns Resource identity, required/optional participation, Resource Capability negotiation, composite-result honesty, and cleanup composition.
- Security owns Subject/Evaluator/control authority separation and `SecurityAssurance`.
- Evidence/Artifact owns exact retained-byte identity.
- Core owns `QUIESCING`, Validity, infrastructure failure, and Task Verdict separation.

No relational design decision creates a competing version of those concepts.

## 3. Current portable direction

### Capability

One cohesive initial claim:

```text
capabilityId: state.relational
profile: avp-relational-state-v0.1
revision: "0.1"
```

No temporary `supports_*` capability family.

### Canonical state and identity

- RFC 8785 JCS exact bytes.
- Typed canonical relational values; high-precision numerics are strings, not JSON numbers.
- Closed scalar portability intersection for PostgreSQL/MySQL reference targets.
- Separate Manifest and StateImage Artifacts.
- Manifest never references baseline StateImage; baseline contains Manifest digest, avoiding content-address cycles.
- Fabric `identityArtifacts` binds Manifest + baseline by media type, not array position.
- Runtime snapshot StateImage is Evidence bound to Environment/resource-owned SnapshotRef.
- Existing Artifact SHA-256 identity is reused; no competing relational digest system.

### State surface and row identity

- one closed authoritative relation/column surface;
- full StateImage always covers that whole surface;
- named projections are static relation/column subsets over all rows;
- no portable SQL/predicate/join/expression language in v0.1;
- every relation has a logical non-null unique row key;
- logical key identity is independent of backend PK/index names and order;
- rows sort by canonical key bytes, not backend collation/physical order;
- key mutation is semantic delete+insert.

### Observation, quiescing, and drift

- evaluator state is one committed logical view;
- no dirty Subject state;
- multi-relation output cannot be torn;
- Core QUIESCING closes admission of new Subject mutations;
- accepted activity may settle;
- final projection requires a settlement barrier;
- unresolved activity under the bound policy prevents accepted final verification and uses existing infrastructure/Validity semantics;
- schema drift means the backend can no longer satisfy the immutable logical Manifest binding, not that raw DDL/catalog bytes changed;
- irrelevant backend changes outside the selected binding are not automatically drift.

### Reset and restore

- reset is accepted only after canonical full-state equality with baseline;
- snapshot stores canonical logical StateImage evidence;
- restore is accepted only after re-projection proves snapshot state identity;
- base relational restore may claim at most `STATE_EQUIVALENT`, never `EXACT`.

### TCK and parity

- TCK cases are backend-neutral;
- profile operations are separate from privileged fixture-control operations;
- no `executeSql`, generic query, public transaction, DDL, or catalog API is required by the portable profile;
- PostgreSQL and MySQL reference drivers run the same case vectors;
- shared parity fixture covers all scalar types, composite keys, full/subset projections, two-relation non-torn observation, quiescing, drift, reset, restore, and diff;
- exact canonical parity is required where scheduling does not legitimately choose different pre/post commit states;
- `TornProjectionAdapter` and `FalseRestoreAdapter` style metadata-identical negative implementations must fail execution-sensitive TCK.

## 4. Decision evidence

### RS-BR-001 / RS-BR-002

`docs/design/alpha3-relational-state-canonical-model.md`

Defines canonical scalar lexical rules, JCS bytes, Artifact media roles, acyclic Manifest/baseline identity, and runtime snapshot binding.

### RS-BR-003 / RS-BR-004

`docs/design/alpha3-relational-state-surface-and-row-identity.md`

Defines the closed authoritative surface, named projection restrictions, logical identifiers, row keys, canonical row order, and diff identity.

### RS-BR-005 / RS-BR-006

`docs/design/alpha3-relational-state-quiescing-and-schema-drift.md`

Defines QUIESCING settlement, no-auto-commit/no-dirty-read behavior, bounded failure composition, portable Manifest binding validity, drift/non-drift boundaries, and concurrent DDL handling.

### RS-BR-007 / RS-BR-008

`docs/design/alpha3-relational-state-tck-and-parity.md`

Defines the common parity fixture, backend-neutral TCK operation boundary, privileged fixture driver, concurrency invariant, negative adapters, and reference-completion versus third-party conformance distinction.

## 5. Draft -> Proposed blocker ledger

| Blocker | Status | Decision evidence |
| --- | --- | --- |
| RS-BR-001 Scalar lexical encoding | **CLOSED** | canonical model |
| RS-BR-002 Manifest/StateImage identity | **CLOSED** | canonical model |
| RS-BR-003 Authoritative surface/projections | **CLOSED** | surface + row identity |
| RS-BR-004 Row-key portability | **CLOSED** | surface + row identity |
| RS-BR-005 QUIESCING/unsettled Subject activity | **CLOSED** | quiescing + drift |
| RS-BR-006 Schema drift boundary | **CLOSED** | quiescing + drift |
| RS-BR-007 Cross-backend parity fixture | **CLOSED** | TCK + parity |
| RS-BR-008 Language-neutral TCK interface | **CLOSED** | TCK + parity |

Blocker closure is design evidence only. It does not automatically change the AEP lifecycle.

## 6. Required AEP reconciliation before Proposed

AEP-0010 itself was written before the detailed decisions above. Before it can be judged `Proposed`, its text must be reconciled so it does not retain stale or ambiguous statements.

At minimum reconcile:

1. `integer` from unbounded/arbitrary precision language to the v0.1 common 65-digit portability boundary;
2. `decimal` to explicit precision 1..65 and scale 0..30;
3. temporal lexical/range/precision rules to the canonical model;
4. baseline binding so the Manifest does not reference the baseline image and create a digest cycle;
5. row-key definition from author-controlled ordering to canonical logical-column set/order;
6. named projections to static all-row relation/column subsets only;
7. QUIESCING settlement-barrier semantics and no auto-commit/dirty-read rule;
8. portable schema-drift definition as binding failure rather than catalog equality;
9. TCK interface separation between SUT profile operations and privileged fixture controls;
10. exact cross-backend reference parity criteria and negative implementation controls.

## 7. Proposed-readiness audit criteria

After AEP reconciliation, a separate audit must verify:

- written problem and scope remain coherent;
- alternatives and compatibility impact are explicit;
- Security analysis covers Subject/Evaluator/Control credentials and evidence secrecy;
- conformance strategy can reject metadata-identical broken behavior;
- no requirement is derived from PostgreSQL/MySQL command syntax or default configuration;
- no generic untyped public extension is introduced;
- no backend implementation is required to define missing semantics;
- AEP-0010 is sufficiently complete for protocol review while still non-normative.

Only if those checks pass should the AEP status change from `Draft` to `Proposed`.

## 8. Gate conclusion

Current state:

```text
AEP-0010: Draft
RS-BR-001..008: CLOSED as design blockers
AEP reconciliation: REQUIRED
Proposed-readiness audit: NOT YET RUN
```

Therefore:

**DRAFT DESIGN BLOCKERS ARE CLOSED.**

**AEP-0010 IS STILL DRAFT.**

**NOT YET READY FOR PROPOSED.**

**NOT READY FOR RELATIONAL NORMATIVE SPECIFICATION.**

**NOT READY FOR POSTGRESQL OR MYSQL ADAPTER IMPLEMENTATION.**
# Alpha 3 Relational State Quiescing and Schema Drift

Status: **DRAFT DESIGN DECISION — RS-BR-005 / RS-BR-006 CLOSED FOR PROPOSED-READINESS PURPOSES**

Proposal: AEP-0010 (Draft)
Parent authority: AEP-0009 (Accepted), Core lifecycle, Environment, Security

This document is non-normative design evidence. It fixes how Relational State composes with Core `QUIESCING` and how portable logical-schema drift is detected without defining a database-specific lifecycle or catalog contract.

## 1. Decision summary

Relational State v0.1 will require:

1. no new Subject mutation activity may be accepted after the Core `QUIESCING` boundary;
2. Subject mutation activity accepted before the boundary may settle;
3. final authoritative projection starts only after a **Subject mutation settlement barrier** is established;
4. an implementation MUST NOT auto-commit an unsettled Subject transaction to make evaluation possible;
5. an implementation MUST NOT weaken observation semantics to expose uncommitted state;
6. if settlement cannot be established under the bound execution policy, final relational verification is unavailable and the condition is represented through existing infrastructure/Validity semantics rather than being manufactured into Agent Task Verdict failure;
7. cleanup MAY terminate/rollback unresolved Subject database work only after the failure/invalidity condition has been captured; cleanup cannot retroactively turn that aborted work into committed task state;
8. schema drift is defined as failure of the current backend binding to satisfy the immutable `RelationalStateManifest`, not as arbitrary system-catalog byte inequality;
9. portable binding validity is checked before a control operation can mutate relational state and at the observation boundary used to accept projection/snapshot/restore/reset results;
10. backend changes outside the selected logical binding do not automatically invalidate the profile.

## 2. No second database lifecycle

The relational profile does not define states such as `TRANSACTION_OPEN`, `DATABASE_QUIESCED`, or `SNAPSHOT_READY` as a competing Episode lifecycle.

Core remains authoritative:

```text
... -> RUNNING -> QUIESCING -> VERIFYING -> ...
```

Relational resource activity is evidence/internal state projected onto that lifecycle.

`QUIESCING` keeps its existing meaning: no new Subject-requested side effect may be initiated, while already accepted in-flight work may settle.

## 3. Subject mutation activity

A **Subject mutation activity** is a Subject-authorized database operation/session transaction whose unresolved completion can change the authoritative relational surface.

The exact backend representation is implementation-specific. It may correspond to:

- a statement routed through an AVP Subject database gateway;
- a transaction on a Subject credential/session;
- an application request with an owned database transaction;
- another controlled activity whose commit/rollback outcome can alter authoritative state.

The protocol does not standardize connection IDs, transaction IDs, SQL text, JDBC objects, PostgreSQL PIDs, or MySQL thread IDs.

An implementation claiming the profile must have enough authority/observability to determine whether relevant Subject mutation activity is still unresolved. If it cannot do so, it cannot establish the final observation boundary and must fail closed.

## 4. QUIESCING admission boundary

Once the Episode enters `QUIESCING`:

- the Subject-facing relational mutation surface MUST reject new mutation activity before it reaches the database;
- existing Subject credentials/sessions MUST NOT provide an uncontrolled bypass that can initiate new authoritative mutations after the boundary;
- read-only Subject observations MAY continue only when they cannot create authoritative side effects or prevent the Evaluator/Control Plane from establishing the required final boundary;
- privileged Evaluator/Control operations remain governed by their existing authority and are not classified as Subject side effects merely because they touch the database.

A deployment that gives the Subject an unrestricted direct database route which cannot enforce the QUIESCING admission boundary cannot claim this profile for final verification.

## 5. Settlement barrier

Before the first final relational projection used in `VERIFYING`, the resource must establish a **settlement barrier**.

The barrier is satisfied only when:

1. every Subject mutation activity accepted before QUIESCING has reached a known committed, rolled-back/cancelled, or otherwise non-mutating terminal outcome; and
2. no unresolved Subject activity can later commit a mutation that belongs logically before the final observation but was omitted from it; and
3. the implementation has prevented admission of new Subject mutation activity after QUIESCING.

The barrier is about observable authority and completion, not one database command.

Backend mechanisms may include transaction/session tracking, request completion tracking, gateway admission closure, connection revocation, transaction inspection, application-level unit-of-work accounting, or another implementation that proves the same property.

## 6. Committed-state final observation

After the settlement barrier is established, the Evaluator creates the final consistent committed observation defined by AEP-0010.

The implementation MUST NOT:

- read dirty/uncommitted Subject state;
- use `READ UNCOMMITTED` or an equivalent weaker behavior to avoid waiting/failing;
- assemble a final projection partly before and partly after an unresolved commit;
- auto-commit a Subject transaction on the Subject's behalf;
- reinterpret an unresolved mutation as committed because the intended SQL was observed.

A transaction's statements are not authoritative committed state merely because they were accepted or executed.

## 7. Settlement policy and timeout

AVP v0.1 does not mandate a universal wall-clock timeout value.

The execution environment must have a **bounded settlement policy** appropriate to its runtime. Any timeout/deadline value that can change Episode validity must be bound as execution/configuration identity under existing Scenario/Fabric/runtime provenance rules; it is not a hidden mutable default.

The portable outcome is binary:

- settlement barrier established; or
- settlement barrier not established under the bound policy.

The TCK may use a short harness-controlled deadline to exercise the failure branch without making that test duration a protocol constant.

## 8. Unsettled transaction outcome

If the settlement barrier cannot be established:

- the resource MUST NOT emit an accepted final relational projection pretending verification completed;
- the Episode MUST use existing infrastructure/Validity failure semantics appropriate to the integration point;
- the condition MUST NOT be converted directly into Agent Task Verdict failure solely because database activity remained unsettled;
- evaluator diagnostics SHOULD identify unresolved activity through opaque/audit-safe identities without exposing credentials or sensitive SQL to the Subject.

This preserves the existing AVP separation between trustworthy evaluation and task outcome.

Whether an application-level task should have committed before its Subject protocol reported completion is a separate Scenario/Oracle concern. The relational resource profile only says an untrustworthy final observation cannot be accepted.

## 9. Cleanup after unsettled activity

After the infrastructure/Validity outcome has been captured, cleanup may terminate sessions or roll back unresolved transactions when needed to recover the resource safely.

Cleanup:

- MUST NOT auto-commit unresolved Subject work;
- MUST remain retry-safe under Fabric cleanup semantics;
- MUST NOT resurrect a released resource;
- MUST preserve evaluator evidence sufficient to explain that settlement failed before cleanup intervention;
- remains infrastructure handling, not Task Verdict rewriting.

## 10. Portable logical binding

`RelationalStateManifest` is immutable for one bound resource instance. The adapter maintains a backend-specific binding from each logical relation/column to the backing database surface.

The binding is conformant only while every Manifest obligation remains satisfiable without lossy reinterpretation.

Portable binding validity includes:

- each logical relation resolves to exactly one authoritative backend relation/source for this resource;
- each logical column resolves uniquely within its relation;
- current stored values can be extracted losslessly into the declared logical scalar type/parameters;
- baseline/reset values can be materialized losslessly when the operation requires them;
- logical key columns remain addressable and projected;
- canonical key non-null/uniqueness requirements can be established for the observed state;
- named projection relation/column selections still resolve to the same logical binding;
- the adapter can establish the required consistent committed observation over the complete selected surface.

The protocol does not require these properties to be represented by one database constraint or one catalog query.

## 11. Definition of schema drift

For v0.1, **relational schema drift** occurs when the currently bound backend can no longer satisfy the immutable Manifest's portable logical binding.

Examples that are drift when they affect the selected binding:

- selected relation no longer resolves;
- selected column no longer resolves;
- relation/column binding becomes ambiguous;
- backend value domain/type change makes a declared scalar mapping lossy or unsupported;
- temporal/numeric precision can no longer be represented under the Manifest declaration;
- a key column is removed/unavailable;
- concurrent DDL prevents establishing the required consistent observation for the bound logical relation;
- adapter mapping configuration changes so a logical id points to a different backend state surface under the same Manifest identity.

The portable error is logical-binding drift/incompatibility. Vendor DDL/error codes remain diagnostics.

## 12. Changes that are not automatically portable drift

The following backend changes do **not** automatically constitute v0.1 logical schema drift if the Manifest binding and observable semantics remain valid:

- adding an unselected backend table;
- adding an unselected backend column;
- creating/dropping an index not needed to establish the profile semantics;
- changing physical storage layout;
- optimizer/statistics changes;
- changing a backend constraint name;
- changing table/column ordinal position when logical bindings remain stable;
- changing implementation metadata that does not alter the selected logical state semantics.

Likewise, raw DDL text or system-catalog byte changes are not themselves the portable drift test.

## 13. Backend type changes may or may not be drift

A backend type change is judged by the portable binding, not by type-name equality.

For example:

- changing a backend integer storage type while all selected values and future accepted state remain losslessly representable under the same AVP `integer` declaration need not change portable identity;
- changing from an exact decimal representation to approximate floating point cannot satisfy the same v0.1 `decimal` binding and is drift/incompatibility;
- changing timestamp storage/session behavior so canonical `timestamp-instant` can no longer be proven independent of ambient timezone is drift/incompatibility.

This prevents PostgreSQL/MySQL type names from becoming the protocol.

## 14. Constraints, collation, triggers, and defaults

The base relational profile is a logical **state** interoperability profile, not a complete database-program equivalence model.

Therefore raw equality of:

- check/foreign-key constraint definitions;
- index definitions;
- collations;
- triggers;
- defaults/generated expressions;
- sequence/auto-increment configuration;
- stored routines;

is not part of v0.1 logical state equivalence unless the selected Manifest semantics directly depend on a property needed for conformance.

However an implementation MUST NOT ignore their observable consequences. If a collation/trigger/default/type rule causes selected state to violate canonical value, key uniqueness, reset, consistent observation, or other profile requirements, the operation fails regardless of whether the catalog object itself is modeled.

Scenarios that require exact database-program/configuration identity should bind those implementation inputs as separate immutable Artifacts/provenance rather than pretending the base logical Manifest models them.

## 15. Drift validation timing

### Provision / compatibility

Before any relational provisioning side effect that relies on an existing backend binding, the implementation validates that the selected backend can satisfy the Manifest and required baseline artifacts.

### Projection / snapshot

The logical binding used to interpret the canonical state must be valid at the same observation boundary used for the accepted projection/snapshot. A stale catalog check performed earlier is insufficient if concurrent DDL can invalidate the view.

### Reset / restore

Before mutating relational state, the adapter validates that the current binding is compatible with the operation. After mutation it re-establishes the binding and verifies canonical state identity.

A concurrent backend change between checks that invalidates the binding causes the operation to fail; successful command execution does not override post-operation drift detection.

### Diff

Before/after states must bind the same Manifest digest and projection identity. A Manifest/binding change is surfaced as drift/incompatibility, not encoded as ordinary row diff.

## 16. Concurrency with DDL

The protocol does not require one DDL-locking strategy.

An adapter may:

- prevent selected-schema DDL during the Episode;
- use database locks/transactions that provide a stable binding;
- detect and fail on concurrent drift;
- use another mechanism establishing equivalent observable semantics.

If selected DDL races with projection/snapshot/reset/restore and the adapter cannot prove one valid immutable binding, it must fail closed.

This directly accommodates differences such as MySQL consistent-read invalidation and PostgreSQL locking behavior without standardizing either mechanism.

## 17. No raw catalog digest as protocol identity

Implementations MAY compute a backend catalog/DDL/configuration fingerprint for cache invalidation or evaluator diagnostics.

Such a fingerprint:

- is implementation metadata/evidence;
- is not `RelationalStateManifest` identity;
- is not sufficient conformance evidence;
- MUST NOT cause two logically equivalent PostgreSQL/MySQL bindings to have different portable Manifest identities.

Portable identity remains the exact Artifact digest of the reviewed logical Manifest.

## 18. TCK direction for settlement

The eventual language-neutral TCK should include at least:

1. an already committed mutation visible in final projection;
2. a Subject mutation held uncommitted across QUIESCING;
3. proof that final projection does not expose the dirty value;
4. commit-before-settlement success leading to the post-commit final state;
5. unresolved activity past the harness deadline producing infrastructure/Validity failure with no accepted final projection;
6. proof that the adapter does not auto-commit the Subject transaction;
7. proof that new mutation admission is rejected after QUIESCING.

The fixture controls timing/activity; portable assertions contain no PostgreSQL PID, MySQL thread id, SQL transaction token, or engine branch.

## 19. TCK direction for drift

The eventual TCK should distinguish:

### Mandatory drift failures

- selected relation removed/unresolvable;
- selected column removed/unresolvable;
- selected column changed to a mapping that cannot preserve the declared scalar semantics;
- mapping redirected to a different backend object under unchanged Manifest identity;
- selected-schema change racing with observation so a consistent Manifest-bound state cannot be established.

### Non-drift controls

- unselected relation added;
- unselected column added;
- irrelevant index/catalog metadata changed while portable mapping remains valid.

The portable case describes the logical mutation to the test resource through a TCK control seam. Backend adapters translate that seam to engine-specific DDL only inside implementation test drivers.

## 20. RS-BR-005 closure evidence

RS-BR-005 asked for exact composition of final relational observation with Core `QUIESCING` and unsettled Subject transactions.

Closure decision:

- QUIESCING closes admission of new Subject mutation activity;
- accepted in-flight activity may settle;
- final projection requires a settlement barrier;
- no dirty reads or automatic Subject commit;
- bounded settlement policy is execution identity, not a global AVP timeout;
- failure to settle prevents accepted final relational verification and uses existing infrastructure/Validity semantics;
- cleanup rollback/termination occurs only after the failure boundary is captured and cannot rewrite task outcome.

**RS-BR-005: CLOSED FOR DRAFT -> PROPOSED READINESS.**

## 21. RS-BR-006 closure evidence

RS-BR-006 asked what portable logical-schema drift means without using raw backend catalog equality.

Closure decision:

- drift means failure of the current backend binding to satisfy the immutable Manifest;
- selected relation/column/type/mapping/observation failures are portable drift/incompatibility;
- changes outside the selected binding are not automatically drift;
- backend type-name changes are judged by lossless portable semantics;
- DDL/catalog fingerprints remain implementation evidence;
- binding is checked at the operation's relevant observation/mutation boundary;
- concurrent DDL must be excluded or fail closed when one immutable binding cannot be proven.

**RS-BR-006: CLOSED FOR DRAFT -> PROPOSED READINESS.**

## 22. Remaining Draft blockers

Still open:

- RS-BR-007 — cross-backend canonical parity fixture;
- RS-BR-008 — language-neutral TCK execution interface.

AEP-0010 remains Draft. No relational normative spec/schema/TCK or PostgreSQL/MySQL adapter is authorized until those blockers close, AEP text is reconciled, and the normal AEP review lifecycle advances.
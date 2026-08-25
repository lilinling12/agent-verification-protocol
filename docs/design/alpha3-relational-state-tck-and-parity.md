# Alpha 3 Relational State TCK and Cross-Backend Parity

Status: **DRAFT DESIGN DECISION — RS-BR-007 / RS-BR-008 CLOSED FOR PROPOSED-READINESS PURPOSES**

Proposal: AEP-0010 (Draft)
Parent authority: AEP-0009 (Accepted)

This document is non-normative design evidence. It fixes the language-neutral conformance execution boundary and the PostgreSQL/MySQL reference parity fixture without turning SQL or backend names into AVP protocol semantics.

## 1. Decision summary

Relational State v0.1 conformance will separate two planes:

```text
System-under-test relational profile operations
              !=
Privileged TCK fixture-control operations
```

Portable TCK cases operate on logical identifiers, typed canonical values, Artifact identities, Environment/Fabric handles, and profile operation results.

Backend-specific SQL, transaction handles, DDL, process/session IDs, driver classes, and database names exist only behind the conformance adapter/fixture driver.

The reference vertical slice is not considered cross-backend complete until PostgreSQL and MySQL/InnoDB independently pass the same profile and produce equal canonical evidence for the shared parity fixture.

Third-party conformance does **not** require shipping two database engines.

## 2. Conformance architecture

The eventual profile uses three conceptual roles.

### 2.1 TCK case

Language-neutral normative test vector and expected observable behavior.

A case may name:

- logical fixture identity;
- relational Manifest/baseline Artifact identities;
- projection ids;
- logical row mutations;
- concurrency/barrier events;
- logical schema-drift controls;
- expected profile/Fabric/Environment outcomes.

It MUST NOT branch on PostgreSQL/MySQL or prescribe SQL syntax.

### 2.2 Relational conformance adapter

Implementation-under-test bridge that executes portable relational profile operations and returns observed results.

It is evaluated by TCK expectations and cannot rewrite the case to match implementation behavior.

### 2.3 Fixture-control driver

Privileged test harness used only to establish controlled preconditions/failures that ordinary profile operations cannot create safely.

Examples:

- begin/hold/commit a controlled Subject transaction;
- inject a logical row mutation;
- introduce selected/unselected schema changes;
- coordinate a commit during projection;
- corrupt a negative-control implementation.

Fixture controls are **not AVP Resource Capabilities, Subject capabilities, or a public SQL API**. They exist for executable conformance only.

## 3. System-under-test operation contract

The TCK needs the following semantic operations. Exact function/class names are not normative; this list defines observable obligations the language-neutral adapter protocol must expose.

### Provision relational resource

Inputs:

- Environment/Scenario/Fabric ownership context;
- `RelationalStateManifest` ArtifactRef;
- baseline `RelationalStateImage` ArtifactRef;
- required `state.relational / avp-relational-state-v0.1 / 0.1` declaration.

Observed outcome:

- compatible resource reaches Fabric/Environment ready path; or
- fail-closed compatibility/infrastructure result before prohibited side effects.

### Project

Input:

- live resource handle;
- Manifest-defined `projectionId`.

Observed output:

- exact canonical `RelationalProjection` bytes or equivalent byte-bearing result;
- SHA-256 state digest bound to those bytes;
- owner/projection identity required by Environment.

The TCK validates bytes independently; an implementation-returned digest alone is insufficient.

### Snapshot

Input:

- live resource handle.

Observed output:

- Environment/resource-owned SnapshotRef;
- retained/runtime `RelationalStateImage` ArtifactRef;
- canonical full-state identity;
- portable operation result.

The TCK resolves/validates the StateImage bytes rather than trusting a backend snapshot token.

### Reset

Input:

- live resource handle;
- bound baseline target (v0.1 has one required baseline image).

Observed output:

- reset result plus post-reset canonical full-state evidence.

TCK acceptance compares the re-projected full state with the baseline image identity.

### Restore

Input:

- live resource handle;
- owner-valid SnapshotRef.

Observed output:

- restore result;
- declared fidelity;
- post-restore canonical full-state evidence.

For v0.1, accepted fidelity cannot exceed `STATE_EQUIVALENT`.

### Diff

Inputs:

- two same-Manifest relational state/projection identities;
- optional named `projectionId`, with full surface as the other supported scope.

Observed output:

- canonical semantic inserted/deleted/updated records ordered by logical relation/key identity.

The TCK may independently recompute expected diff from canonical before/after bytes.

### Quiesce/final-observation participation

Input is the existing Episode lifecycle transition/control context, not a new public database lifecycle.

Observed outcome:

- settlement barrier established and final projection allowed; or
- bounded settlement failure mapped to existing infrastructure/Validity semantics with no accepted final projection.

### Release

Observed outcome follows Environment/Fabric stale-reference and retry-safe cleanup semantics.

## 4. Operations deliberately absent

The portable SUT interface MUST NOT require:

- `executeSql`;
- generic `query`;
- `beginTransaction` / `commit` / `rollback` as public relational profile operations;
- database-user creation APIs;
- DDL APIs;
- catalog inspection APIs;
- PostgreSQL snapshot-token APIs;
- MySQL read-view APIs;
- backend backup/restore commands.

Conformance can control such mechanisms only through the privileged fixture driver.

## 5. Logical fixture-control vocabulary

The fixture driver consumes logical test controls rather than SQL strings in TCK vectors.

Candidate controls:

### Row mutation batch

```yaml
op: mutate
atomic: true
changes:
  - action: update
    relationId: consistency.left
    key: {...typed canonical key...}
    set: {...typed canonical values...}
```

`atomic: true` is a fixture precondition: the backend-specific test driver must establish one transactionally committed logical batch or declare the fixture unavailable. It is not an AVP cross-resource atomicity claim.

Allowed row actions:

- insert;
- update non-key values;
- replace key (semantically delete+insert for diff expectations);
- delete.

### Held Subject mutation

```yaml
op: begin-subject-mutation
transactionLabel: tx-a
changes: [...]
hold: before-commit
```

Followed later by logical `commit` or `rollback` fixture control.

The label is TCK-local identity, not a backend transaction token.

### Schema change

```yaml
op: schema-change
change:
  kind: remove-selected-column
  relationId: parity.scalar_values
  columnId: decimal_value
```

Portable negative controls describe semantic intent such as:

- remove selected relation;
- remove selected column;
- change selected column to lossy mapping;
- redirect logical binding;
- add unselected relation;
- add unselected column;
- change irrelevant index metadata.

Backend drivers choose engine-specific DDL/configuration to establish the requested condition.

### Projection concurrency barrier

The fixture can pause the implementation at a TCK-defined observation checkpoint or coordinate a commit between logical relation reads through an adapter test seam.

The portable assertion is only that the final projection is pre-commit or post-commit, never torn.

A production implementation need not expose this seam publicly.

## 6. TCK adapter anti-self-certification rule

The relational conformance adapter must not satisfy execution-sensitive cases by reading expectations or capability metadata and constructing a PASS result.

For mandatory cases:

- canonical projection cases execute the real implementation projection path;
- snapshot/restore/reset cases execute real resource operations and then independently observe canonical state;
- quiescing cases coordinate actual unsettled activity;
- schema-drift cases mutate the controlled backend binding;
- negative implementations advertise the same capability metadata as conforming implementations.

TCK result is derived from observed bytes/outcomes, not from a `supports_relational=true` flag.

## 7. Reference parity fixture identity

The reference parity fixture should be versioned as non-secret immutable repository test data, for example:

```text
conformance/fixtures/relational-state/v0.1/
```

It contains language-neutral:

- Manifest JSON;
- baseline StateImage JSON;
- mutation vectors;
- expected canonical projection/state-image/diff bytes or digests;
- concurrency event plan;
- schema-drift logical controls.

The fixture is shared by PostgreSQL and MySQL reference test drivers without duplicated engine-specific expected files.

Engine setup scripts may exist separately under implementation tests but must materialize the same portable fixture Artifacts.

## 8. Proposed parity Manifest

The fixture should contain at least four logical relations.

### `parity.scalar_values`

Purpose: exercise all mandatory scalar encodings and nullability.

Logical key:

```text
record_id (integer)
```

Candidate columns:

- `record_id` — integer;
- `flag_value` — boolean;
- `integer_value` — integer, including 65-digit boundary case in one row;
- `decimal_value` — decimal(65,30) and representative fixed-scale values;
- `text_value` — Unicode text, including composed and decomposed sequences retained distinctly;
- `binary_value` — binary including zero/high-bit bytes;
- `date_value` — date;
- `time_p0` — time-local precision 0;
- `time_p3` — time-local precision 3;
- `time_p6` — time-local precision 6;
- `local_ts_p6` — timestamp-local precision 6;
- `instant_ts_p6` — timestamp-instant precision 6;
- `uuid_value` — UUID;
- `nullable_text` — nullable text with at least one NULL row.

Fixture values avoid engine-specific undefined temporal ranges while covering lexical boundary behavior.

### `parity.composite_keys`

Purpose: prove row identity independent of backend PK/index order and collation.

Logical key columns:

```text
account_id (uuid)
tenant_id  (integer)
```

Additional columns include exact text and decimal values.

Backend reference schemas SHOULD intentionally use a different physical key/index column order in at least one engine, proving AVP key identity comes from the Manifest.

### `consistency.left`

Logical key: `id` integer.

Contains `epoch` integer.

### `consistency.right`

Logical key: `id` integer.

Contains `epoch` integer.

A committed fixture transaction changes both `epoch` values from `1` to `2` atomically inside one database. The named projection `consistency.pair` selects both relations.

Allowed projection outcomes during the coordinated commit:

```text
(left=1, right=1)
or
(left=2, right=2)
```

Forbidden torn outcomes:

```text
(left=1, right=2)
(left=2, right=1)
```

This tests one committed multi-relation observation without prescribing MVCC commands.

## 9. Required named projections in parity fixture

At minimum:

### `parity.all`

Selects every column of `parity.scalar_values` and `parity.composite_keys`.

Purpose: exact canonical cross-backend parity.

### `parity.keys-and-values`

Selects logical key columns plus a small non-key subset from both parity relations.

Purpose: prove named projection subset/identity rules.

### `consistency.pair`

Selects keys and `epoch` from both consistency relations.

Purpose: concurrent committed-view/torn-read test.

Projection definitions are Manifest-owned. No SQL appears in the fixture.

## 10. Canonical parity assertions

For the same portable Manifest and baseline StateImage, PostgreSQL and MySQL reference adapters must demonstrate:

1. the same Manifest Artifact digest;
2. the same baseline StateImage Artifact digest;
3. exact-byte equality for `parity.all` canonical projection;
4. exact-byte equality for `parity.keys-and-values`;
5. equal projection state digests derived independently by the TCK;
6. after the same logical mutation vector, exact-byte equality of full StateImages;
7. exact-byte equality of semantic diff output once the diff schema is finalized;
8. reset returns each backend to the exact same baseline StateImage digest;
9. snapshot/mutate/restore returns each backend to the same snapshot StateImage digest while each reports no more than `STATE_EQUIVALENT`;
10. each backend independently rejects unsupported/lossy fixture material rather than normalizing it differently.

SnapshotRef IDs themselves are expected to differ because they are Environment/resource ownership references, not content identity.

## 11. Concurrency parity assertions

Both reference adapters execute the same `consistency.pair` case under coordinated commit timing.

The exact pre/post outcome chosen may differ based on scheduling. Cross-backend parity does **not** require both engines to choose the same side of the commit boundary.

Each must independently satisfy the invariant:

```text
projection in {fully-pre-commit, fully-post-commit}
```

and never return a torn state.

This distinction avoids falsely requiring identical transaction scheduling while still proving the portable consistency property.

## 12. QUIESCING parity assertions

The shared fixture holds an uncommitted Subject mutation and triggers Core QUIESCING.

Both adapters must:

- stop new Subject mutation admission;
- keep dirty values out of accepted evaluator state;
- succeed if the fixture commits within the settlement policy, then observe committed state;
- fail final verification if activity remains unresolved past the harness deadline;
- never auto-commit the held Subject transaction.

Backend transaction/session identities remain private to the fixture driver.

## 13. Drift parity assertions

Both reference drivers consume the same logical drift controls.

Mandatory fail cases:

- selected relation removed;
- selected column removed;
- selected exact scalar changed to an intentionally lossy/unsupported binding;
- logical binding redirected under unchanged Manifest identity;
- concurrent selected-schema change prevents one consistent observation.

Mandatory non-drift controls:

- unselected relation added;
- unselected column added;
- irrelevant index/catalog metadata changed while portable binding remains valid.

Expected TCK outcomes are identical even though PostgreSQL/MySQL DDL differs.

## 14. Negative implementation controls

At least two metadata-identical broken implementations/drivers are required before the profile can be treated as execution-sensitive.

### TornProjectionAdapter

Advertises the same `state.relational` capability/Manifest as a conforming implementation but intentionally observes selected relations through incompatible committed views.

`consistency.pair` MUST fail it.

### FalseRestoreAdapter

Advertises the same capability, returns a successful restore status, but does not re-establish the snapshot StateImage.

Restore TCK MUST fail it after independent re-projection.

Optional additional negative controls may cover dirty-read exposure, false schema compatibility, or non-canonical value serialization.

## 15. Profile case families

The eventual TCK should organize cases around semantic obligations rather than database operations.

Candidate families:

1. `RELATIONAL-IDENTITY` — Manifest/baseline binding and stale ownership;
2. `RELATIONAL-CANONICAL` — scalar and exact-byte canonicalization;
3. `RELATIONAL-PROJECTION` — named/full projection semantics;
4. `RELATIONAL-CONSISTENCY` — one committed multi-relation view;
5. `RELATIONAL-QUIESCING` — settlement barrier and uncommitted exclusion;
6. `RELATIONAL-DRIFT` — logical binding drift/non-drift controls;
7. `RELATIONAL-RESET` — baseline re-establishment;
8. `RELATIONAL-SNAPSHOT-RESTORE` — logical StateImage and fidelity honesty;
9. `RELATIONAL-DIFF` — insert/delete/update/key-change semantics;
10. `RELATIONAL-SECURITY` — Subject/Evaluator/Control separation;
11. `RELATIONAL-EXECUTED-CAPABILITY` — metadata-identical broken implementation rejection.

Exact case IDs/requirement IDs remain future normative-spec work after AEP acceptance.

## 16. No backend-name branches

Portable TCK YAML/schema/case code MUST NOT contain logic equivalent to:

```text
if backend == "postgres": ...
if backend == "mysql": ...
```

A backend implementation registers/provides a conforming relational adapter and a fixture driver. The case remains unchanged.

Implementation-specific setup may select SQL/driver mechanisms outside the portable case tree.

If a test genuinely has semantics that only one engine can satisfy, that is evidence the behavior is not mandatory `avp-relational-state-v0.1` semantics and requires a separate conditional capability/profile or implementation test.

## 17. Conformance report semantics

A relational profile ConformanceReport uses existing AVP TCK reporting.

It may identify the implementation/runtime version through existing implementation identity fields, but backend product/version metadata is not a substitute for profile conformance.

A PostgreSQL-backed and MySQL-backed implementation both report against the same profile name/version and case IDs.

## 18. Reference completion versus third-party conformance

### Third-party conformance

An independent implementation may claim `avp-relational-state-v0.1` by passing the profile against its chosen relational backend. It does not need PostgreSQL and MySQL together.

### AVP reference completion

The AVP project applies a stricter acceptance criterion to its own claim that the profile is genuinely portable:

- one PostgreSQL reference adapter passes;
- one MySQL/InnoDB reference adapter passes;
- both execute the same language-neutral cases;
- the shared parity fixture produces the required exact canonical equality;
- negative adapters prove execution-sensitive cases can detect false claims.

This is project acceptance evidence, not a protocol requirement imposed on external implementations.

## 19. RS-BR-007 closure evidence

RS-BR-007 asked for a concrete PostgreSQL/MySQL-neutral parity fixture covering mandatory scalar types and concurrency behavior.

Closure decision:

- shared immutable portable fixture tree;
- scalar-values relation covering every mandatory type/precision/nullability class;
- composite-key relation proving backend index/PK order independence;
- two-relation atomic epoch fixture proving non-torn committed observation;
- named full/subset/concurrency projections;
- exact canonical projection/state/reset/restore/diff parity assertions;
- scheduling parity defined by invariant rather than identical commit-side timing;
- logical drift and QUIESCING controls shared across drivers;
- backend setup/SQL kept outside portable expected data.

**RS-BR-007: CLOSED FOR DRAFT -> PROPOSED READINESS.**

## 20. RS-BR-008 closure evidence

RS-BR-008 asked for a language-neutral TCK execution interface that does not become a general SQL client API.

Closure decision:

- explicit separation between SUT relational profile operations and privileged fixture-control driver;
- portable SUT obligations limited to provision/project/snapshot/reset/restore/diff/quiesce participation/release;
- no generic SQL/query/transaction/DDL/catalog public operation;
- logical fixture controls exist only for conformance orchestration;
- real implementation paths and independent canonical-byte verification are mandatory;
- metadata-identical torn-projection and false-restore negative implementations are required;
- no backend-name branches in portable cases.

**RS-BR-008: CLOSED FOR DRAFT -> PROPOSED READINESS.**

## 21. Draft blocker conclusion

All initially recorded Draft blockers now have design decisions:

```text
RS-BR-001 CLOSED
RS-BR-002 CLOSED
RS-BR-003 CLOSED
RS-BR-004 CLOSED
RS-BR-005 CLOSED
RS-BR-006 CLOSED
RS-BR-007 CLOSED
RS-BR-008 CLOSED
```

This does **not** automatically make AEP-0010 `Proposed`.

Next required gate:

1. reconcile AEP-0010 itself with all decision documents;
2. audit problem/scope, alternatives, compatibility, security, and conformance strategy for contradictions/gaps;
3. verify current exact-head CI/governance;
4. record a Draft -> Proposed readiness result;
5. only then, if genuinely review-ready, change AEP status to `Proposed` in a separately auditable commit.

No normative spec/schema/TCK/backend implementation is authorized by blocker closure alone.
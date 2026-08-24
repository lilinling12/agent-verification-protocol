# AEP-0010 — Relational State Resource Profile v0.1

- Status: Draft
- Authors: AVP maintainers and contributors
- Created: 2026-08-24
- Parent: AEP-0009 — Environment Fabric Composition and Capability Contract (Accepted)
- Target AVP version: Unselected future protocol version
- Alpha phase: Alpha 3 — Environment Fabric / Relational State

## Summary

This AEP proposes the portable relational-state resource semantics for AVP Environment Fabric.

The profile standardizes the verification-facing state model shared by relational database implementations while deliberately refusing to standardize PostgreSQL, MySQL, SQL client APIs, transaction commands, physical backup formats, or vendor error models.

The profile direction is:

> One portable logical relational-state contract, independently implemented by PostgreSQL and MySQL adapters, with observable conformance defined before either adapter becomes protocol evidence.

The proposed profile is selected by a Fabric `state` resource through one Resource Capability declaration:

```text
capabilityId: state.relational
profile: avp-relational-state-v0.1
revision: "0.1"
```

The v0.1 profile is intentionally cohesive rather than a collection of `supports_*` flags. A conforming claim covers the selected relational state surface, consistent evaluator projection, logical state image/snapshot behavior, reset, state-equivalent restore, semantic diff, schema-drift handling, and fail-closed ownership/security behavior defined by the eventual normative specification.

This AEP is Draft. It does not authorize a normative profile, schema, TCK registration, PostgreSQL/MySQL adapter implementation, merge, release selection, tag, package publication, signing, or attestation publication.

## Problem

AEP-0009 establishes the Environment Fabric composition model but intentionally leaves resource-domain semantics separate. Relational databases are the first resource domain because database-backed state is common in agent verification and because superficially similar database features have materially different guarantees.

Independent AVP implementations otherwise risk incompatible assumptions such as:

1. treating `pg_export_snapshot()` as the AVP snapshot abstraction;
2. treating MySQL `WITH CONSISTENT SNAPSHOT` as equivalent to PostgreSQL exported snapshots;
3. inheriting server-default transaction isolation and calling the result deterministic;
4. hashing SQL driver output without a portable type/canonicalization contract;
5. comparing raw DDL or vendor catalog output as if it were a portable schema identity;
6. restoring table rows but overclaiming `EXACT` despite sequence/auto-increment, session, lock, MVCC, or engine state differences;
7. using Subject credentials for evaluator projection because the Subject already has database access;
8. allowing DDL drift to silently alter the state surface during an Episode;
9. producing a multi-table projection assembled from mutually inconsistent visibility points;
10. implementing PostgreSQL first and then forcing MySQL behind a PostgreSQL-shaped public API.

A portable profile is required before either database backend can become an official Alpha 3 adapter.

## Motivation / interoperability case

An AVP Scenario may require an Environment whose authoritative state is relational. The Evaluator must be able to answer questions such as:

- what committed relational state existed at the verification observation boundary?
- does the state match a known baseline after reset?
- did a Subject action insert, update, or delete the intended logical rows?
- can the state be snapshotted and restored without claiming fidelity the backend cannot establish?
- did schema drift, unsupported data, or infrastructure failure invalidate evaluation rather than become Agent task failure?
- can a PostgreSQL-backed and MySQL-backed Environment produce the same portable projection semantics for the same logical fixture?

The protocol needs answers to those questions without requiring the same SQL syntax, system catalog, backup utility, transaction token, driver, or storage engine internals.

## Existing standards and implementation evidence

### PostgreSQL

PostgreSQL 18 is the current stable documentation line as of this AEP draft. PostgreSQL defaults to `READ COMMITTED`; a query sees a snapshot as of query start, while `REPEATABLE READ` gives successive statements in one transaction the same visibility snapshot. PostgreSQL can export and import transaction snapshots, but the exported identifier remains valid only while the exporting transaction remains open and importing has isolation constraints.

These features are strong implementation mechanisms for evaluator consistency and parallel projection. They are not AVP snapshot identity.

References:

- https://www.postgresql.org/docs/18/transaction-iso.html
- https://www.postgresql.org/docs/18/sql-set-transaction.html
- https://www.postgresql.org/docs/18/functions-admin.html
- https://www.postgresql.org/docs/18/app-pgdump.html

### MySQL / InnoDB

MySQL 8.4 uses `REPEATABLE READ` as the default transaction isolation level. `START TRANSACTION WITH CONSISTENT SNAPSHOT` establishes a useful InnoDB consistent read only when the current transaction isolation permits it; under MySQL 8.4 documentation this is `REPEATABLE READ`. Consistent reads also have important DDL limitations: `DROP TABLE` and some `ALTER TABLE` operations can make the original read view unusable or produce `ER_TABLE_DEF_CHANGED`.

These features are implementation mechanisms for a conforming observation boundary. They do not create a portable AVP snapshot token.

References:

- https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html
- https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html
- https://dev.mysql.com/doc/refman/8.4/en/commit.html

### Identity generators demonstrate why `EXACT` is unsafe by default

PostgreSQL sequence advancement is not reclaimed when the calling transaction aborts, and `setval` changes are not rolled back. MySQL/InnoDB auto-increment state has its own persistence and allocation behavior. Those mechanisms can affect later generated identifiers while being distinct from the selected logical row state.

The v0.1 relational profile therefore MUST NOT equate logical row restoration with complete execution-state restoration.

References:

- https://www.postgresql.org/docs/18/functions-sequence.html
- https://dev.mysql.com/doc/refman/8.4/en/innodb-auto-increment-handling.html

## Scope

The proposed v0.1 profile applies to one Fabric resource with `resourceKind: state` and one logical relational-state boundary.

A single profile instance describes:

- one immutable logical relational schema/state manifest;
- one closed authoritative relational state surface;
- named evaluator projections over that surface;
- a portable baseline state image when reset/provisioning requires it;
- canonical value and row identity semantics;
- one committed-state observation boundary across the selected relations;
- logical snapshot and same-environment restore behavior;
- semantic row-level diff;
- fail-closed schema drift and unsupported-value behavior;
- Security/Evidence/Fabric composition.

Multiple independently managed databases are represented as multiple Environment Resources and compose through the existing Fabric result semantics. This AEP does not introduce cross-database atomicity.

## Explicit non-goals

The v0.1 direction does not standardize:

- a universal AVP SQL client API;
- `begin`, `commit`, `rollback`, savepoints, locks, or isolation-level commands as Subject-facing AVP operations;
- PostgreSQL transaction snapshot identifiers;
- MySQL read-view identifiers;
- `pg_dump`, `mysqldump`, filesystem snapshots, WAL/binlog positions, physical pages, or storage-engine backup formats as AVP snapshot identity;
- raw vendor DDL as portable schema identity;
- query planner state, optimizer statistics, MVCC transaction IDs, lock tables, advisory locks, session variables, or connection-pool internals as base relational state;
- sequence/auto-increment continuation state in the v0.1 logical equivalence claim;
- schema migration as an in-Episode protocol operation;
- cross-environment runtime snapshot import;
- cross-resource distributed transactions;
- global database determinism;
- one ORM, JDBC abstraction, Python driver, or repository implementation.

## Portable model

### Relational State Resource

A Relational State Resource is a Fabric `state` resource whose selected `state.relational` capability is bound to `avp-relational-state-v0.1`.

The base `EnvironmentResource` remains closed and vendor-neutral. The relational profile MUST NOT add backend-specific fields to that base object or use a generic metadata bag as a substitute for reviewed profile resources.

### RelationalStateManifest

The normative phase should define a separately serialized `RelationalStateManifest` whose exact retained bytes can be referenced through the Fabric resource's existing `identityArtifacts` collection.

The manifest should bind at minimum:

- Environment Resource identity;
- profile/revision identity;
- logical relation identifiers;
- logical column identifiers;
- each column's portable logical type;
- nullability;
- ordered row-identity columns;
- the authoritative state surface;
- named evaluator projection definitions;
- canonical representation version;
- baseline state-image ArtifactRef when a baseline is materialized.

The manifest MUST NOT contain database passwords, privileged connection strings, future hidden fault material, or other evaluator secrets.

Physical table/column names, connection configuration, driver settings, migration paths, and engine-specific DDL are adapter/deployment bindings. When they are identity-relevant they should be retained as exact-byte Artifact evidence without becoming portable schema semantics.

### Closed authoritative state surface

The relational manifest defines a closed authoritative state surface for the selected resource. State outside that declared surface is not part of the profile's `STATE_EQUIVALENT` claim.

An implementation MUST NOT silently omit a selected relation or column because the backend cannot read, normalize, restore, or diff it. Incompatibility must fail before a conforming capability claim is established.

The profile does not claim that two databases with equal projected state have identical future database behavior. Engine programs, collations, sequences, triggers, storage layout, and other execution-relevant mechanisms may differ and remain outside the base logical-state equivalence claim unless a later profile explicitly binds them.

### Row identity

Every relation selected into the v0.1 authoritative surface must declare an ordered logical row key.

The row key:

- may be backed by a primary key or another uniqueness guarantee;
- may contain multiple columns;
- must be non-null for every selected row;
- must be unique within the selected relation projection;
- is a portable logical identity and need not equal a backend constraint name.

If a relation cannot provide a stable row key, it is not compatible with the mandatory v0.1 semantic-diff contract. The implementation must fail compatibility rather than silently downgrade diff semantics.

## Portable value model

### Principle

Driver-native values and SQL type names are not portable protocol values. Every selected column must map losslessly to a closed v0.1 logical scalar type before it participates in state identity.

The proposed required v0.1 scalar set is:

- `boolean`;
- `integer` — arbitrary-precision signed integer represented canonically as a base-10 lexical value;
- `decimal` — exact decimal value represented without exponent; precision/scale remain schema metadata;
- `text` — exact Unicode scalar sequence with no implicit Unicode normalization;
- `binary` — exact octets using canonical base64url representation;
- `date` — calendar date;
- `time-local` — local time without timezone semantics;
- `timestamp-local` — local date/time without timezone semantics;
- `timestamp-instant` — an absolute instant normalized to UTC;
- `uuid` — canonical lowercase hyphenated UUID text.

`null` is represented explicitly as absence of a non-null scalar value and is permitted only when the logical column is nullable.

Canonical lexical rules must be fixed in the normative schema/specification before implementation.

The mandatory v0.1 set deliberately excludes approximate floating point, database-native JSON, XML, spatial types, arrays, vendor enum/set types, intervals, and opaque extension types. A backend may store those values, but a resource selecting them cannot claim the base v0.1 profile until a governed profile revision defines a lossless portable mapping.

This is a fail-closed portability boundary, not a statement that those database features are unsupported by AVP forever.

## Logical schema identity

Raw PostgreSQL/MySQL catalog output and raw DDL are not portable schema identity.

The portable logical schema identity is the canonical identity of the reviewed `RelationalStateManifest`. It describes only the profile semantics needed to interpret the authoritative state surface and named projections.

The same portable logical manifest may be implemented by different backend DDL. Backend DDL/migrations remain separately content-addressed implementation evidence.

A selected logical schema is immutable for the lifetime of the bound Environment instance. If the selected schema surface changes, the current profile binding is no longer valid. The implementation must fail closed and require reprovision/materialization under a new manifest rather than silently continuing under the old identity.

This rule is intentionally conservative because backend DDL visibility differs and MySQL consistent reads can be invalidated by certain DDL operations.

## Observation boundary

### Committed-state rule

An evaluator relational projection must never include uncommitted Subject state.

The implementation must establish a database-independent observation boundary such that the complete selected projection corresponds to one committed logical database view.

For concurrent transactions, a projection may validly correspond to the committed state immediately before or immediately after a concurrent commit when the observation boundary permits either. It MUST NOT be a torn composition where different selected relations correspond to incompatible visibility points.

### Multi-relation consistency

One projection that spans multiple relations must use one logical consistency boundary across all selected relations.

Implementations may establish that property using:

- a backend MVCC snapshot;
- an exported/synchronized snapshot;
- quiesced writers;
- another mechanism that provides the same observable property.

The TCK tests the property, not the command sequence.

### QUIESCING composition

Core `QUIESCING` remains the top-level side-effect boundary.

Before final evaluator verification, Subject-accepted database work must have settled or the Environment must fail/withhold transition to verification according to existing lifecycle/validity rules. An unresolved Subject transaction must never be made visible by weakening isolation or by reading uncommitted state.

The profile does not add a second transaction lifecycle.

## Canonical relational projection

The normative phase should define canonical projection bytes with a versioned representation.

The canonical representation must bind:

- relational manifest identity;
- projection identifier;
- selected relations;
- selected columns in manifest order;
- each row's logical key;
- typed canonical values.

Relations are ordered by portable relation identifier. Rows are ordered by canonical row-key bytes, not by backend default collation. Columns are emitted in manifest-defined order.

The relational `stateDigest` should be SHA-256 over the exact canonical projection bytes. Because the manifest identity is included in the canonical projection preimage, schema/definition drift changes state identity rather than allowing equal row bytes under incompatible semantics to collide as the same relational state.

This specializes Environment `AVP-ENVIRONMENT-006` without replacing its `(projection identifier, state digest)` identity rule.

Backend SQL ordering is an optimization only. Implementations must verify or establish canonical ordering independently of server collation semantics.

## Portable relational state image

The normative phase should define a `RelationalStateImage` as an immutable Artifact containing canonical logical relational state for the full authoritative surface.

Two roles use the same portable content model but retain different ownership semantics:

1. **baseline state image** — immutable materialization input bound by Scenario/Fabric identity and usable when provisioning/resetting a new Environment;
2. **runtime snapshot state image** — retained Artifact evidence produced by a snapshot operation, while the AVP SnapshotRef remains owned by the Environment/resource that produced it.

Using one content model prevents separate baseline/snapshot encodings from drifting while preserving Environment snapshot ownership.

The v0.1 profile does not authorize restoring a runtime SnapshotRef into another Environment instance. A future portable-import capability may define that separately.

## Snapshot semantics

A successful relational logical snapshot must:

- establish one committed consistent observation boundary for the full authoritative surface;
- produce/bind the canonical full-state digest;
- bind the owning Environment and resource through existing Environment/Fabric snapshot identity;
- retain the state image as Artifact evidence when persistence is required;
- fail closed on unsupported values, schema drift, ownership drift, or inconsistent observation.

A PostgreSQL exported snapshot token or any MySQL transaction/read-view state remains adapter-private mechanism/diagnostic information and is never the portable snapshot identity.

## Reset semantics

The selected materialized execution contract may bind an immutable baseline `RelationalStateImage`.

A successful reset to that baseline must not be accepted until a post-reset canonical projection of the full authoritative state surface equals the baseline state identity under the same relational manifest.

The implementation may use truncate/delete/insert, staging, transactional replacement, database cloning, or another backend mechanism. The protocol does not infer atomicity from the reset mechanism.

Failure to establish the baseline is an Environment/Fabric infrastructure or validity failure, not Agent Task Verdict failure.

## Restore semantics

The base v0.1 relational capability intentionally defines **logical state-equivalent restore**, not exact execution-state restore.

A successful restore must re-establish:

- the same relational manifest identity;
- the same full authoritative-state canonical digest;
- the snapshot ownership/binding required by Environment and Fabric contracts.

After restore, the implementation must re-project and verify the restored state rather than trusting a backend restore command's exit status.

Under `avp-relational-state-v0.1`, a conforming logical restore MUST report no stronger than `STATE_EQUIVALENT`.

`EXACT` is not a valid fidelity claim for this base relational capability because v0.1 does not standardize all continuation/execution state such as sequence/auto-increment counters, transaction internals, session state, lock state, backend caches, or physical storage identity.

A future separately governed capability may define stronger restore semantics if independent implementations can prove them.

## Semantic diff

The v0.1 profile should define semantic diff over canonical row keys.

For each selected relation, diff output should distinguish:

- inserted row keys and resulting values;
- deleted row keys and prior values;
- updated row keys with changed logical columns and before/after canonical values.

Diff identity must bind the before and after relational state identities and projection/manifest semantics, preserving Environment `AVP-ENVIRONMENT-009`.

Database physical row order, internal tuple IDs, page locations, transaction IDs, and query plans must never be diff identity.

## Resource Capability semantics

The profile uses one cohesive capability claim:

```text
state.relational @ avp-relational-state-v0.1 / 0.1
```

A declaration means the implementation supports all mandatory v0.1 semantics for the selected resource surface. The profile MUST NOT be decomposed into a temporary family of `supports_projection`, `supports_snapshot`, `supports_mysql`, or similar booleans.

Optional future semantics such as portable cross-environment import or exact execution-state restore require separately governed capability/profile identities.

Capability support remains distinct from Subject authorization under AEP-0009 and AVP Security.

## Security considerations

Relational adapters expand the privileged Environment surface and must preserve existing Security boundaries.

Required direction:

1. Subject database authority is derived only from the materialized Scenario capability surface.
2. Evaluator projection authority must not depend on credentials exposed to the Subject.
3. Control-plane reset/restore/provision credentials must never enter the Subject execution context.
4. A generic database administrative connection must not be exposed as a Subject capability.
5. Portable manifests/projections/state images must contain no database password, secret DSN, control token, or hidden evaluator material.
6. Backend error diagnostics may be retained evaluator-side but must not disclose secrets into Subject-visible errors/evidence.
7. Implementation use of a container, VM, managed database, or separate database role does not automatically upgrade any `SecurityAssurance` dimension.

Evaluator and Control Plane credentials should be independently least-privileged where the backend permits separation. The normative phase must preserve the existing requirement that Subject credential context remains separated from evaluator/control authority.

## Failure and validity semantics

The following are profile/infrastructure failures, not Agent task failures solely by occurrence:

- required database resource unavailable;
- selected relation/column missing;
- logical schema/manifest drift;
- row-key uniqueness/nullability violation;
- unsupported/lossy scalar mapping;
- inability to establish one consistent committed observation;
- unsettled Subject transaction preventing trustworthy verification;
- snapshot Artifact integrity failure;
- reset baseline mismatch;
- restore state mismatch;
- stale/foreign snapshot/resource reference;
- loss of evaluator/control authority.

Vendor error codes may appear only as evaluator diagnostics. Conformance and Validity use portable AVP outcomes.

## Conformance strategy

A future `avp-relational-state-v0.1` TCK must execute real relational resource behavior. It must not pass from manifest inspection, backend labels, SQL fixture inspection, or adapter capability tables.

Mandatory conformance families should include:

### Projection identity and canonicalization

- provision a logical manifest and baseline;
- project the same state repeatedly;
- require stable canonical bytes/state digest;
- mutate a selected value and require the digest to change;
- verify unsupported/lossy value mapping fails closed.

### Consistent multi-relation observation

- coordinate a concurrent writer across a multi-relation invariant;
- require the projection to correspond to one committed pre-commit or post-commit state;
- reject a torn mixed state.

### Uncommitted-state exclusion

- hold an uncommitted Subject transaction;
- verify evaluator projection never exposes the dirty row/value;
- require verification to wait/fail rather than weaken isolation when the transaction prevents a trustworthy final boundary.

### Schema drift

- change the selected logical schema through a controlled negative implementation/fixture;
- require the old manifest binding to fail closed rather than silently adapt.

### Reset

- mutate authoritative rows;
- reset to the bound baseline image;
- require exact canonical baseline state identity after reset.

### Logical snapshot/restore

- snapshot;
- mutate;
- restore;
- re-project;
- require the snapshot state digest to be re-established;
- require fidelity `STATE_EQUIVALENT`, never `EXACT`, for the base profile.

### Semantic diff

- create insert/update/delete changes across relations;
- require canonical row-key diff semantics independent of physical row ordering.

### Ownership and stale references

- reject foreign resource/snapshot references;
- reject released/stale resource handles without silent reprovision.

### Security separation

- prove Subject authority cannot invoke evaluator/control relational operations;
- prove evaluator/control credentials are not projected into Subject context or portable artifacts.

### Execution-sensitive negative control

- construct an implementation that advertises the same `state.relational` capability metadata but returns a torn projection or false restore success;
- require the TCK to fail that implementation.

## Cross-backend acceptance gate

The reference implementation must not be considered portable after only one database adapter passes.

Before the Relational State vertical slice is declared Alpha 3 reference-complete, at least PostgreSQL and MySQL/InnoDB reference adapters must independently pass the same language-neutral profile and an additional cross-backend parity fixture must demonstrate that equivalent logical manifests/baselines yield identical canonical projection/state identities for the required scalar set.

This cross-backend parity gate is reference acceptance evidence. Independent conforming implementations are not required to ship two database engines.

## Reference implementation direction

Reference implementation work is gated until:

1. this AEP reaches `Accepted` through an explicit protocol decision;
2. the relational normative specification and requirement index are reviewable;
3. serialized resources have closed schemas;
4. the language-neutral TCK is registered and execution-sensitive.

Only then should adapters be implemented.

### PostgreSQL reference target

The initial PostgreSQL adapter should use an explicit evaluator consistency mechanism rather than server defaults. PostgreSQL Repeatable Read and synchronized/exported snapshots are candidate mechanisms, especially for multi-connection projection, but their tokens remain private implementation details.

### MySQL reference target

The initial MySQL adapter should target InnoDB and explicitly establish the required evaluator visibility behavior instead of relying on inherited server defaults. `REPEATABLE READ` with a consistent snapshot is a candidate mechanism. Non-InnoDB behavior must not be silently accepted under an InnoDB-tested conformance claim.

### Common implementation boundary

The common reference interface must be derived from the final portable specification. It must not be a PostgreSQL adapter API generalized after the fact.

No compatibility shim is required for unreleased Alpha 3 relational layouts; the project should avoid exposing an unstable public relational API until the protocol objects are reviewed.

## Backward compatibility

This profile is additive:

- existing `avp-environment-v0.1` implementations do not need to claim `state.relational`;
- existing Fabric resources that do not select the relational profile remain unaffected;
- the profile does not redefine Environment projection, snapshot ownership, restore fidelity, stale-handle, Security, Evidence, or Artifact semantics;
- it specializes those existing contracts for a relational `state` resource.

Because the eventual Alpha 3 release vehicle is unselected, this AEP does not assign the change to `0.3.1` or another release.

## Alternatives considered

### Separate PostgreSQL and MySQL protocol profiles

Rejected as the primary design. It would encode implementation technology into portable semantics and prevent meaningful cross-backend conformance.

### A universal SQL transaction API

Rejected. AVP verifies environment state; it is not a database access protocol or ORM.

### Raw SQL dumps as the portable snapshot

Rejected. Dump formats contain vendor syntax and semantics and cannot establish common restore fidelity.

### Raw DDL/catalog hashing as logical schema identity

Rejected. Equivalent logical schemas can have different backend DDL/catalog representations, while identical-looking DDL can depend on different server defaults.

### Hashing driver-returned rows directly

Rejected. Driver types, numeric formatting, timestamp timezone handling, binary encoding, row order, and collation make this non-portable.

### Claiming `EXACT` after rows are restored

Rejected. Sequence/auto-increment and other execution state can differ despite equal logical rows.

### Generic extension/value bags for unsupported types

Rejected for v0.1. Unknown values must not bypass reviewed canonical semantics. New portable types require a governed profile revision.

### Implement PostgreSQL first, generalize later

Rejected by the Alpha 3 no-transitional-architecture policy. The common contract must be reviewable before either backend becomes the public reference surface.

## Review questions before Proposed

The Draft should not advance to `Proposed` until protocol review confirms all of the following:

1. the closed v0.1 scalar set is sufficient for the first conformance fixture and has lossless PostgreSQL/MySQL mappings;
2. canonical lexical encoding rules are fully specified, especially decimal and temporal precision;
3. the `RelationalStateManifest` / `RelationalStateImage` split composes cleanly with existing Fabric `identityArtifacts`, Environment SnapshotRef, and Artifact identity;
4. the full authoritative state surface and named projection relationship is unambiguous;
5. row-key requirements are acceptable as mandatory v0.1 interoperability constraints;
6. final verification behavior for unsettled Subject transactions is mapped cleanly onto existing QUIESCING/Validity semantics;
7. no proposed requirement accidentally claims cross-backend execution equivalence rather than logical-state interoperability;
8. PostgreSQL/MySQL cross-backend TCK design can prove the common contract without backend-name branches in portable cases.

## Governance boundary

This AEP is Draft and records a proposal only.

Advancing it to `Proposed`, `Accepted`, or `Final` requires the normal AEP lifecycle and recorded maintainer decision. Generic continuation instructions do not constitute an `Accepted` or merge decision.

No PostgreSQL/MySQL adapter should be merged as an official Alpha 3 relational implementation before the accepted authority chain reaches executable TCK coverage.

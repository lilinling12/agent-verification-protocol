# AEP-0010 — Relational State Resource Profile v0.1

- Status: Proposed
- Authors: AVP maintainers and contributors
- Created: 2026-08-24
- Proposed: 2026-08-24
- Proposed-readiness evidence: `docs/design/alpha3-relational-state-proposed-readiness-audit.md`
- Formal Proposed review: PR #86 review `5004337751`
- Proposed-review blocker decisions: `docs/design/alpha3-relational-state-proposed-review-blockers.md`
- Parent: AEP-0009 — Environment Fabric Composition and Capability Contract (Accepted)
- Target AVP version: Unselected future protocol version
- Alpha phase: Alpha 3 — Environment Fabric / Relational State

## Summary

This AEP proposes the first resource-domain profile for AVP Environment Fabric: a portable relational-state contract that can be implemented independently by PostgreSQL, MySQL/InnoDB, or another relational backend without making any one engine's transaction, catalog, dump, driver, or administrative API part of AVP.

The central design rule is:

> AVP standardizes the observable logical relational-state boundary and the identity/evidence needed to verify it; database engines remain implementation mechanisms.

The proposed Fabric Resource Capability identity is one cohesive claim:

```text
capabilityId: state.relational
profile: avp-relational-state-v0.1
revision: "0.1"
```

A v0.1 claim covers the mandatory logical state surface, canonical values and bytes, committed-view projection, logical snapshot/reset/restore, semantic diff, schema/binding honesty, Core `QUIESCING` composition, execution-input identity composition, and Security/Evidence behavior described by this AEP and the eventual normative specification.

This AEP remains **Proposed** for protocol review. It is not normative. It does not create a normative relational profile, requirement index, schema, TCK registration, reference adapter, PostgreSQL/MySQL implementation, release version, merge authorization, or publication authority.

## Problem

AEP-0009 establishes how an Environment Fabric composes identified resources and proves Resource Capabilities, but intentionally leaves relational-state semantics to a resource-domain proposal.

Without a portable relational profile, independent AVP implementations can accidentally define incompatible protocols by choosing different database mechanisms. Examples include:

- treating a PostgreSQL exported transaction snapshot as the AVP SnapshotRef;
- treating a MySQL consistent read as semantically identical to PostgreSQL snapshot export;
- relying on server-default isolation and calling the result reproducible;
- hashing driver-returned values without canonical type/precision rules;
- using raw DDL or system-catalog output as portable schema identity;
- restoring rows and overclaiming `EXACT` despite sequence/auto-increment, session, MVCC, lock, or physical-state differences;
- projecting multiple relations through incompatible visibility points and returning torn state;
- using Subject credentials for evaluator/control operations;
- disclosing evaluator-private relational state because it appears in an authoritative StateImage;
- treating equal logical rows as sufficient identity for two database environments whose execution-relevant triggers/configuration differ;
- allowing selected schema changes to be silently reinterpreted under an unchanged verification identity;
- implementing PostgreSQL first and later generalizing a PostgreSQL-shaped public API.

Alpha 3 therefore needs a language-neutral relational profile before either PostgreSQL or MySQL becomes an official reference resource adapter.

## Motivation / interoperability case

A relational Environment must let an evaluator answer, portably:

- what committed logical state is authoritative at one observation boundary?
- what exact canonical bytes/digest identify a projection or full state image?
- did a Subject action insert, delete, or update the intended logical rows?
- did reset actually restore the bound baseline rather than merely return a successful database command?
- did restore re-establish the snapshot state, and what fidelity was established?
- did selected schema/binding drift invalidate observation?
- are execution-relevant database programs/configuration identity-bound even when they are intentionally not part of logical state identity?
- can the same logical fixture produce the same canonical state on PostgreSQL and MySQL/InnoDB?
- can evaluator-private authoritative state remain available to verification without leaking through Subject-visible routes?
- are Subject, Evaluator, and Control authority still separated?

Those questions must not depend on SQL dialect, database process identifiers, transaction tokens, backup utilities, or one language SDK.

## Existing standards / implementation evidence

External database documentation informs implementation mechanisms and portability limits. It does not become AVP normative semantics by reference.

### PostgreSQL

Current PostgreSQL 18 documentation provides useful implementation mechanisms:

- `READ COMMITTED` query snapshots;
- `REPEATABLE READ` stable transaction visibility;
- exported/imported transaction snapshots under documented constraints;
- synchronized `pg_dump` snapshots;
- exact `numeric` and microsecond temporal values;
- sequence behavior demonstrating that logical rows and execution continuation state are not identical.

References:

- https://www.postgresql.org/docs/18/transaction-iso.html
- https://www.postgresql.org/docs/18/sql-set-transaction.html
- https://www.postgresql.org/docs/18/functions-admin.html
- https://www.postgresql.org/docs/18/app-pgdump.html
- https://www.postgresql.org/docs/18/datatype-datetime.html
- https://www.postgresql.org/docs/18/functions-sequence.html

PostgreSQL snapshot identifiers and transaction commands are adapter mechanisms, not AVP object identity.

### MySQL / InnoDB

MySQL 8.4/InnoDB provides different mechanisms:

- `REPEATABLE READ` as the default InnoDB isolation level;
- consistent nonlocking reads/MVCC read views;
- `WITH CONSISTENT SNAPSHOT` under the applicable isolation behavior;
- DDL interactions that can invalidate an existing consistent read;
- exact `DECIMAL` with a portability intersection of precision 1..65 and scale 0..30;
- temporal fractional precision 0..6;
- auto-increment allocation/persistence behavior distinct from PostgreSQL sequences.

References:

- https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html
- https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html
- https://dev.mysql.com/doc/refman/8.4/en/precision-math-decimal-characteristics.html
- https://dev.mysql.com/doc/refman/8.4/en/fractional-seconds.html
- https://dev.mysql.com/doc/refman/8.4/en/innodb-auto-increment-handling.html

MySQL transaction/read-view details are adapter mechanisms, not AVP object identity.

## Existing AVP contracts reused

This proposal specializes existing authority rather than creating parallel concepts.

### Environment

Reused unchanged:

- authoritative Environment/resource ownership;
- ScenarioInstance binding;
- evaluator projection identity `(projection identifier, state digest)`;
- SnapshotRef ownership and foreign/stale failure;
- restore fidelity `EXACT | STATE_EQUIVALENT | NON_EQUIVALENT`;
- semantic diff binding;
- released-handle fail-closed behavior.

### Environment Fabric

Reused unchanged:

- `resourceKind: state`;
- Resource Capability declaration/revision binding;
- `REQUIRED` / `OPTIONAL` participation;
- resource identity and `identityArtifacts`;
- Resource Capability versus Subject Capability separation;
- composite result/fidelity honesty;
- no implicit cross-resource distributed transaction;
- retry-safe cleanup.

### Scenario

Reused unchanged:

- unresolved required execution inputs fail closed before execution;
- execution-relevant external references bind profile-appropriate resolved identity;
- materialized execution semantics remain immutable during the Episode;
- Subject capability exposure derives from the materialized actor projection.

The relational Manifest is therefore not required to duplicate every database-related execution input. Execution-relevant database programs/configuration outside the logical state model compose through existing Scenario/Fabric identity mechanisms.

### Core

Reused unchanged:

- Core lifecycle including `QUIESCING` and `VERIFYING`;
- no new Subject-requested side effects after entering `QUIESCING`;
- already accepted work may settle;
- lifecycle, Validity, infrastructure condition, and Task Verdict remain distinct.

### Security

Reused unchanged:

- Subject-facing capabilities remain distinct from Evaluator/Control capabilities;
- undeclared Subject capability access fails closed before side effects;
- evaluator/control credentials do not enter Subject execution context;
- evaluator-private material is protected from Subject-visible disclosure;
- security assurance remains multi-dimensional and non-inflating.

The relational profile does **not** prohibit evaluator-private authoritative relational state from existing in evaluator-confidential Evidence. It governs who may observe/retrieve that state.

### Evidence / Artifact

Reused unchanged:

- exact retained bytes use SHA-256 Artifact identity;
- locator is not identity;
- classification/handling metadata does not alter content digest;
- dereferenced bytes are length/digest verified;
- classifications such as `evaluator-confidential`, `secret`, and `regulated` remain the handling model for sensitive relational Evidence.

No new relational content-address or secrecy taxonomy is introduced.

## Scope

One `state.relational` resource represents one logical relational state boundary.

The v0.1 profile standardizes:

- one immutable logical `RelationalStateManifest`;
- one required baseline `RelationalStateImage`;
- one closed authoritative relation/column state surface;
- one closed scalar value vocabulary;
- portable logical row identity;
- named evaluator projections;
- exact canonical JSON bytes and state digests;
- one committed observation boundary across selected relations;
- logical snapshot/reset/restore;
- semantic row-level diff;
- schema/binding drift behavior;
- execution-relevant database input identity composition;
- Core `QUIESCING` settlement behavior;
- Security/Evidence/Fabric composition.

Multiple independently managed databases are separate Fabric resources. v0.1 does not introduce cross-database atomicity.

## Explicit non-goals

The profile does not standardize:

- a general SQL API or ORM;
- public `begin` / `commit` / `rollback` / savepoint / lock operations;
- PostgreSQL exported-snapshot identifiers;
- MySQL read-view identities;
- raw SQL dumps or physical backup formats as portable state identity;
- raw DDL or system-catalog digests as logical state/schema identity;
- query plans, optimizer statistics, MVCC transaction IDs, locks, session handles, or connection-pool internals;
- exact sequence/auto-increment continuation state;
- portable schema migration during an Episode;
- cross-Environment SnapshotRef import;
- approximate floating-point/JSON/XML/spatial/array/interval/vendor-extension value semantics in mandatory v0.1;
- a global database-determinism claim;
- PostgreSQL/MySQL product names as Resource Capability semantics;
- a database-specific secrecy model;
- the complete Environment execution identity inside `RelationalStateManifest`.

## Resource Capability

The initial profile uses exactly one mandatory capability identity:

```text
state.relational @ avp-relational-state-v0.1 / 0.1
```

A declaration means the implementation claims all mandatory v0.1 relational semantics for the selected resource.

The profile MUST NOT be represented as a transitional family of flags such as:

```text
supports_projection
supports_snapshot
supports_postgres
supports_mysql
```

Future semantics that are genuinely optional and independently testable—such as portable cross-Environment import or stronger execution-state restore—require separately governed capability/profile identities.

Resource Capability support never grants Subject authorization.

## Relational identity Artifacts

The closed base `EnvironmentResource` is not extended with backend-specific properties or an untyped metadata bag.

A conforming v0.1 relational resource binds exactly two required relational **state-identity** Artifacts through the existing `EnvironmentResource.identityArtifacts` collection:

1. one `RelationalStateManifest`;
2. one baseline `RelationalStateImage`.

Their roles are identified by profile-defined media type, not array position.

Candidate media types:

```text
application/vnd.avp.relational-state-manifest+json
application/vnd.avp.relational-state-image+json
application/vnd.avp.relational-projection+json
application/vnd.avp.relational-diff+json
```

Exact field names and media registration remain normative-schema work after AEP acceptance.

### Acyclic content identity

The Manifest MUST NOT contain the baseline StateImage ArtifactRef.

The baseline StateImage contains the exact Manifest Artifact digest.

Therefore:

```text
EnvironmentResource
  -> Manifest ArtifactRef
  -> Baseline StateImage ArtifactRef
       -> manifestDigest
```

is acyclic.

Runtime snapshot StateImages are generated Evidence bound by the existing Environment/resource-owned SnapshotRef and do not mutate the immutable Fabric `identityArtifacts` input set.

No separate relational content-address algorithm is introduced.

## RelationalStateManifest

The Manifest describes portable logical **state interpretation semantics**, not backend DDL and not the complete Environment execution identity.

It binds at minimum:

- profile/revision;
- logical relation identifiers;
- logical column identifiers;
- closed logical scalar type plus type parameters;
- nullability;
- logical row-key column set;
- the complete authoritative state surface;
- named projection definitions;
- canonical representation version.

Logical identifiers use a restricted lower-case ASCII vocabulary so identity/order does not depend on backend identifier folding, locale, or Unicode normalization. Exact regex/length constraints remain schema work, with the Proposed direction using identifiers such as `^[a-z][a-z0-9._-]*$`.

Backend table/column names, DSNs, migration paths, driver settings, and vendor catalog objects remain adapter/deployment bindings or separately retained implementation evidence unless another selected execution-input contract requires their identity.

The Manifest Artifact digest is the portable logical state-schema/profile interpretation identity for the resource.

## Execution-relevant database input identity

Logical state equality is not sufficient to establish complete Environment execution identity.

Database programs/configuration outside `RelationalStateManifest` can materially affect Subject actions while leaving the same Manifest and baseline StateImage bytes. Examples include, when relied upon by the selected Scenario:

- triggers;
- defaults;
- generated expressions;
- constraints with execution-visible behavior;
- routines/functions/procedures invoked by Subject-visible database operations;
- database extensions/plugins;
- SQL modes or equivalent semantic configuration;
- timezone/session interpretation settings that affect execution;
- backend schema-program or migration revision;
- collation/configuration when it changes execution semantics rather than merely canonical extraction;
- another database program/config input materially relied upon by Scenario execution.

Rules:

1. `RelationalStateManifest` MUST NOT be interpreted as the complete Environment execution identity merely because its logical state is complete.
2. When a database program/config/reference materially affects Scenario execution semantics and is outside the Manifest, the materialized Scenario/Fabric execution contract MUST bind it to profile-appropriate resolved immutable identity using the existing Scenario external-reference / Fabric execution-input identity mechanisms.
3. The materialized execution contract determines relevance. AVP does not require raw identity for irrelevant database metadata merely because it exists.
4. If a required execution-relevant identity cannot be established, materialization/provisioning MUST fail closed before Episode execution.
5. Execution-input identities MUST remain distinct from canonical relational state digests unless a later governed profile explicitly changes that boundary.
6. Backend product names, catalog fingerprints, process IDs, or server-default labels MUST NOT substitute for a required immutable execution-input identity.
7. If a bound execution-relevant database input drifts during an Episode, the existing execution binding becomes invalid even if the backend can still structurally satisfy the logical Manifest. The implementation MUST fail closed under the existing validity/identity rules rather than silently accepting the new behavior under the old execution identity.

This composition reuses AVP Scenario/Fabric identity authority instead of inventing a database-specific provenance system.

## Authoritative state surface

Every relation and column listed in the Manifest is part of the v0.1 authoritative logical state surface.

There is no `authoritative:false` escape hatch inside a listed relation.

Backend state absent from the Manifest is outside the v0.1 relational `STATE_EQUIVALENT` claim.

An adapter MUST NOT silently omit a selected relation/column because it cannot normalize, observe, restore, or diff it. Incompatibility fails closed.

Evaluator-private rows/columns may still be part of this authoritative surface. Their confidentiality is enforced by Security/Evidence visibility and access rules, not by deleting them from the authoritative state model.

## Portable scalar model

Canonical relational values are typed records. Example:

```json
{"type":"integer","value":"42"}
```

A nullable value retains its declared type:

```json
{"type":"integer","value":null}
```

`type` must match the bound Manifest column definition. Row-key values cannot be null.

The v0.1 scalar set is deliberately conservative and closed.

### boolean

JSON boolean `true` or `false`; numeric/string aliases are non-canonical.

### integer

Signed exact integer with at most 65 decimal digits.

Canonical lexical form is `0` or a minus sign plus/nonzero-leading decimal digits. No `+`, leading zeroes, `-0`, exponent, or decimal point.

The value is serialized as a JSON string, not a JSON number.

### decimal

Manifest parameters:

- precision 1..65;
- scale 0..30;
- `scale <= precision`.

Canonical lexical form is fixed-point with exactly `scale` fractional digits, no exponent, no leading `+`, and normalized positive zero. The value is a JSON string.

Adapters MUST NOT round or truncate to fit the Manifest.

### text

Exact Unicode scalar sequence. No Unicode normalization is performed by AVP canonicalization. Invalid lone surrogate data fails closed. Backend collation equality does not redefine AVP text identity.

### binary

RFC 4648 base64url alphabet, canonical unpadded spelling, no whitespace, canonical pad bits. Alternate spellings decoding to the same bytes are rejected.

### date

`YYYY-MM-DD`, valid Gregorian date, portable v0.1 year range 1000..9999.

### time-local

Time of day only: `HH:MM:SS` plus exactly the Manifest-declared 0..6 fractional digits. No offset, negative/elapsed-time form, leap-second `60`, or `24:00:00`.

### timestamp-local

`YYYY-MM-DDTHH:MM:SS[.fraction]`, year range 1000..9999, no timezone semantics, precision 0..6.

### timestamp-instant

Absolute instant normalized to UTC: `YYYY-MM-DDTHH:MM:SS[.fraction]Z`, precision 0..6, no numeric offset in canonical output, no leap-second `60` in v0.1.

### uuid

RFC 9562 `8-4-4-4-12` hex-and-dash form, lowercase canonical hex.

Approximate float, database-native JSON/XML/spatial/array/interval/vendor enum/set/opaque extension values are excluded from mandatory v0.1. A backend selecting them cannot claim the base profile until a governed revision defines a lossless mapping.

## Canonical bytes

After conversion to the closed relational JSON model, Manifest, Projection, StateImage, and Diff objects use RFC 8785 JSON Canonicalization Scheme (JCS) exact UTF-8 bytes.

Relational integers/decimals use strings specifically to avoid JCS/JSON IEEE-754 number precision becoming relational state semantics.

Array order is established by the profile before JCS serialization.

### Canonical ordering

- relations: ascending logical `relationId`;
- columns: ascending logical `columnId`;
- logical row-key column declarations: ascending logical `columnId`;
- rows: unsigned lexicographic order of canonical JCS row-key bytes.

Backend default collation, table creation order, physical row order, index order, or SQL result order are not canonical identity.

## Logical row identity

Every authoritative relation declares a non-empty logical row-key set from Manifest columns.

For every row:

- all key columns are present;
- key values are non-null;
- key values obey canonical scalar semantics;
- the complete canonical logical key is unique within that relation at the observation boundary.

A backend primary/unique constraint may establish the property but its constraint name, kind, declaration order, or physical index order is not protocol identity.

The adapter MUST NOT manufacture uniqueness using physical tuple IDs, row ordinals, or whole-row hashes when duplicate logical keys exist.

A canonical row key is a JSON object keyed by logical key column ids and containing typed values. JCS gives exact key bytes.

If a logical key value changes, semantic diff records delete-old-key plus insert-new-key rather than an identity-changing update.

Stored generated IDs may be logical keys; generator continuation state remains outside relational `STATE_EQUIVALENT`.

## Full RelationalStateImage

`RelationalStateImage` always covers the entire authoritative relational state surface.

It contains/binds:

- profile `apiVersion` / `kind` in the eventual schema;
- exact Manifest Artifact digest;
- every authoritative relation;
- every authoritative column;
- every row exactly once in canonical key order;
- canonical typed values.

It does not contain its own digest.

SHA-256 over exact JCS StateImage bytes is:

- the Artifact digest when retained; and
- the v0.1 full authoritative relational state digest.

A StateImage whose `manifestDigest` differs from the current Manifest fails closed.

A StateImage MAY contain evaluator-private authoritative data. Such an Artifact MUST be classified and access-controlled according to existing Evidence/Security semantics. Its completeness and its Subject visibility are separate concerns.

## Named evaluator projections

Named projections are immutable definitions in the Manifest.

A v0.1 projection may select only:

- one or more Manifest relations;
- one or more Manifest columns from each selected relation.

It includes **all rows** of each selected relation at one observation boundary.

Every selected relation's logical key columns are mandatory in the evaluator projection.

v0.1 named projections MUST NOT define portable:

- SQL text;
- row predicates;
- joins;
- computed expressions;
- aggregates/grouping/windows;
- limits/offsets;
- backend view/procedure/function names;
- order-by semantics.

A future use case needing portable filtered/derived views requires a separately reviewed model.

Canonical evaluator projection output binds `manifestDigest`, `projectionId`, and selected canonical content. Its state digest is SHA-256 over exact canonical projection bytes. If retained as an Artifact, the same bytes use the same Artifact digest.

Environment evaluator-projection identity remains `(projection identifier, state digest)`.

### Subject-visible relational observation

An evaluator projection is not automatically Subject-visible merely because the evaluator can produce it.

Subject observation remains governed by Scenario actor projection, Environment actor-scoped observation, and Security hidden-material rules:

1. Subject-visible relational observations MUST contain only state authorized for that Subject actor.
2. Evaluator-private authoritative rows/columns and verification-only relational material MUST NOT be disclosed through Subject observations, Subject tool results, Subject execution context, or Subject-visible AVP routes unless the materialized Scenario explicitly makes that material observable.
3. A Subject-visible Artifact locator MUST NOT grant retrieval access to evaluator-private relational bytes.
4. A digest/opaque Artifact identity MAY be exposed only when an existing AVP contract requires it and the identity itself does not disclose the protected content or grant retrieval authority.
5. Redacted or Subject-scoped representations are distinct Artifact bytes and therefore have their own Artifact identity; they MUST NOT reuse the digest of evaluator-confidential unredacted bytes.

The relational profile therefore preserves hidden evaluator state while preventing its disclosure.

## Committed observation boundary

An accepted evaluator relational projection MUST correspond to one committed logical database view.

It MUST NOT expose uncommitted Subject state.

A projection spanning multiple relations may validly observe the fully committed state before or after a concurrent commit, depending on scheduling. It MUST NOT combine incompatible visibility points into a torn state.

Implementation mechanisms may include MVCC snapshots, exported/synchronized snapshots, writer quiescence, or another method proving the same observable property.

The TCK tests the property, not transaction commands.

## Core QUIESCING composition

The relational profile adds no second lifecycle.

When Core enters `QUIESCING`:

- new Subject mutation activity MUST be rejected before database side effects;
- activity accepted before the boundary MAY settle;
- final relational verification starts only after a **Subject mutation settlement barrier** is established.

The settlement barrier requires every relevant accepted mutation to have a known committed, rolled-back/cancelled, or otherwise non-mutating terminal outcome and requires admission of new Subject mutation activity to remain closed.

The implementation MUST NOT:

- auto-commit a Subject transaction;
- weaken observation to dirty-read state;
- treat accepted SQL statements as committed state merely because they ran.

The execution environment uses a bounded settlement policy. AVP does not mandate one global timeout value. A timeout/deadline affecting execution validity MUST be identity-bound under the existing execution/provenance rules.

If settlement cannot be established, no accepted final relational projection is produced and the condition uses existing infrastructure/Validity semantics rather than being directly converted into Agent Task Verdict failure.

Cleanup may terminate/rollback unresolved activity only after that failure boundary is captured; cleanup cannot retroactively make Subject work committed.

A deployment that gives the Subject an unrestricted direct database path that the Environment cannot prevent from initiating new mutations after `QUIESCING` cannot claim final-verification conformance for this profile.

## Logical schema/binding drift

The Manifest is immutable for one resource instance.

Portable relational schema drift means the current backend binding can no longer satisfy the immutable Manifest—not merely that raw DDL/catalog bytes changed.

Drift/incompatibility includes selected binding failures such as:

- selected relation/column no longer resolves or becomes ambiguous;
- scalar/precision/time mapping becomes lossy or unsupported;
- key columns become unavailable;
- adapter mapping redirects a logical id to a different backend state surface under the same Manifest;
- concurrent selected-schema DDL prevents one consistent Manifest-bound observation.

Changes outside the selected logical binding are not automatically relational-state drift, including unrelated tables/columns, irrelevant index changes, optimizer/statistics changes, or constraint-name changes when portable state semantics remain valid.

Backend type-name changes are judged by lossless portable state behavior, not string equality.

Collations, triggers, defaults, generated expressions, constraints, routines, sequence configuration, and other database-program elements are not raw-equality parts of v0.1 logical **state** identity. Their observable consequences still cannot violate canonical values, key uniqueness, reset, committed observation, or other profile requirements.

If one of those elements is separately bound as execution-relevant input under the materialized Scenario/Fabric contract, drift of that identity invalidates the execution binding even when the logical state Manifest remains satisfiable. This is execution-input drift, not ordinary row/schema-state diff.

Before a state-mutating Control operation, the logical binding must be compatible; after reset/restore it is revalidated together with canonical state. Projection/snapshot must interpret state under a valid binding at the accepted observation boundary. Concurrent drift that cannot be excluded/proven causes fail-closed behavior.

A backend catalog fingerprint may be implementation evidence/cache metadata but is neither Manifest identity nor sufficient conformance/execution-identity proof.

## Logical snapshot

A successful relational snapshot:

- establishes one committed consistent observation of the full authoritative surface;
- creates exact canonical `RelationalStateImage` bytes;
- retains/binds those bytes through Artifact identity;
- binds the generated StateImage to the Environment/resource-owned SnapshotRef;
- preserves the appropriate Evidence handling classification/access boundary;
- fails closed on unsupported values, logical-binding drift, execution-binding invalidity when applicable, inconsistent observation, or ownership error.

Backend transaction tokens, dump files, WAL/binlog positions, or physical snapshot paths are implementation details.

## Reset

v0.1 has one required baseline StateImage bound as a resource state-identity Artifact.

Reset may use any backend mechanism, but success is accepted only after the implementation:

1. revalidates required logical and execution bindings;
2. re-projects the complete authoritative relational state surface; and
3. proves exact canonical equality with the baseline StateImage digest under the same Manifest.

Database command success is insufficient.

Reset failure is infrastructure/Validity information, not Agent task failure solely by occurrence.

## Restore fidelity

v0.1 restore is logical-state restore.

After restoring an owner-valid SnapshotRef, the implementation MUST independently re-project the complete authoritative relational state surface and compare it with the snapshot StateImage under the same Manifest.

For `state.relational / avp-relational-state-v0.1 / 0.1`:

1. restore is successful only when independent re-projection proves the snapshot `RelationalStateImage` identity has been re-established;
2. every successful conforming relational restore MUST report resource restore fidelity exactly:

```text
STATE_EQUIVALENT
```

3. if the snapshot StateImage identity is not re-established, restore MUST fail and MUST NOT report successful state equivalence; its fidelity is `NON_EQUIVALENT` or the equivalent failure representation selected by the eventual operation schema;
4. `EXACT` is not a valid successful fidelity claim for the base relational capability.

`EXACT` is excluded because sequence/auto-increment continuation, transaction/MVCC/session/lock/cache state, physical storage identity, and other execution state are not standardized by v0.1.

Fabric aggregate fidelity continues to follow the existing weakest-required-participant rule. A stronger relational restore capability requires separate governance and executable evidence.

## Semantic diff

Diff operates only between states bound to the same Manifest and either the full surface or one identical named projection.

Per relation/key:

- only in after -> insert;
- only in before -> delete;
- same key/equal canonical values -> unchanged;
- same key/non-key values changed -> update;
- key changed -> delete old + insert new.

Diff ordering follows relation id and canonical row-key bytes, never backend operation order or physical identity.

Cross-Manifest comparison is logical binding/schema drift, not ordinary row diff.

Evaluator-private content in Diff output follows the same Evidence classification/access rules as the source states. Subject-visible diff output must be separately actor-authorized and must not leak evaluator-private values.

## Security considerations

Relational adapters increase privileged Environment authority.

The profile requires preservation of three authority contexts:

```text
Subject data authority
Evaluator projection authority
Control provision/reset/restore authority
```

Rules:

1. Subject database authority derives only from materialized Scenario capability exposure.
2. Resource Capability support never exposes evaluator/control operations to the Subject.
3. Evaluator/control credentials MUST NOT enter Subject execution context.
4. Portable Manifest/Projection/StateImage/Diff material MUST NOT contain database passwords, secret DSNs, control tokens, signing secrets, or equivalent credentials/control authority.
5. Portable relational Artifacts MAY contain evaluator-private authoritative data when required by verification; such content uses existing Evidence classification/access controls and MUST NOT become Subject-visible unless the Scenario explicitly authorizes it.
6. Subject-visible relational routes/results/observations/locators MUST NOT disclose evaluator-private relational data or grant unauthorized retrieval authority.
7. A generic database-admin connection is not a Subject capability.
8. Backend diagnostic errors may be retained evaluator-side but MUST be sanitized from Subject-visible material where necessary.
9. Container, managed-database, role separation, or VM technology names do not automatically upgrade any `SecurityAssurance` dimension.
10. Implementations SHOULD use independently least-privileged Subject/Evaluator/Control credentials where the backend permits it, but AVP does not standardize database role syntax.

A deployment that cannot enforce Subject-route admission/visibility boundaries cannot claim those relational profile semantics merely because its database backend supports snapshots or roles.

## Failure / Validity semantics

Examples of relational infrastructure/Validity failures include:

- resource unavailable;
- required Manifest/baseline Artifact missing or integrity-invalid;
- Manifest/StateImage identity mismatch;
- selected relation/column binding failure;
- required execution-relevant database input identity missing or drifted;
- unsupported/lossy scalar mapping;
- duplicate/null logical key;
- inability to establish one committed consistent observation;
- unsettled Subject mutation preventing trustworthy final observation;
- selected logical schema/binding drift;
- reset baseline mismatch;
- restore state mismatch;
- stale/foreign resource or SnapshotRef;
- loss of evaluator/control authority;
- inability to preserve required evaluator-private/Subject-visible access separation.

Vendor error codes may appear only as evaluator diagnostics. These conditions are not converted directly to Agent task failure solely because they occurred.

## Conformance strategy

The future `avp-relational-state-v0.1` TCK must execute real profile behavior.

### Portable SUT operation obligations

The language-neutral conformance adapter must expose observable equivalents of:

- provision compatible Manifest + baseline + required execution-input binding;
- project named evaluator projection;
- snapshot full state;
- reset baseline;
- restore owner-valid snapshot;
- semantic diff;
- `QUIESCING` / final-observation participation;
- release.

Exact programming-language method names are non-normative.

The portable profile does **not** require generic SQL/query/transaction/DDL/catalog operations.

### Privileged fixture controls

Executable TCK needs controlled negative/concurrency setup. A separate fixture driver may:

- apply logical row mutation batches;
- hold/commit/rollback a TCK Subject transaction;
- introduce logical selected/unselected schema changes;
- alter an execution-relevant bound database program/config input for a drift negative case;
- coordinate a commit during projection;
- activate negative implementation behavior.

These controls are conformance-harness seams only. They are not Resource Capabilities or public Subject APIs.

Portable case vectors describe logical intent; backend drivers translate to PostgreSQL/MySQL SQL/configuration internally.

### Mandatory behavior families

At minimum:

1. Manifest/baseline ownership and stale references;
2. canonical scalar/exact-byte projection stability;
3. named/full projection semantics;
4. multi-relation committed-view non-tearing;
5. uncommitted-state exclusion and `QUIESCING` settlement;
6. logical binding drift failures and non-drift controls;
7. execution-relevant database input identity binding/drift;
8. reset verified by post-reset state identity;
9. snapshot/mutate/restore verified by re-projection with successful fidelity exactly `STATE_EQUIVALENT`;
10. insert/delete/update/key-change semantic diff;
11. Subject/Evaluator/Control authority separation;
12. evaluator-private relational state non-disclosure through Subject-visible relational surfaces;
13. execution-sensitive capability honesty.

### Metadata-identical negative implementations

At least:

- `TornProjectionAdapter` — same capability metadata but reads selected relations through incompatible views;
- `FalseRestoreAdapter` — same capability metadata, returns restore success without re-establishing snapshot state.

The mandatory TCK must reject both from observed behavior rather than metadata.

A hidden-state leakage negative implementation SHOULD be included in the security family: same relational capability/authoritative evaluator state, but improperly exposes evaluator-private state through a Subject-visible observation or retrievable locator; it must fail.

An execution-input drift case MUST prove that changing a bound execution-relevant database program/config identity cannot be silently accepted under the previous execution contract merely because canonical rows still match.

## Cross-backend reference parity gate

Third-party conformance requires one implementation to pass the profile. It does **not** require two database engines.

The AVP project's own reference-completeness claim is stricter. Before the relational vertical slice is called reference-complete:

- PostgreSQL adapter independently passes the same profile;
- MySQL/InnoDB adapter independently passes the same profile;
- both use the same portable case vectors;
- a shared immutable parity fixture proves canonical equality where deterministic equality is required;
- metadata-identical negative adapters are rejected;
- both preserve the same execution-input identity and evaluator-private visibility semantics defined by the portable profile.

### Shared fixture

The fixture includes at least:

- `parity.scalar_values` covering boolean, 65-digit integer boundary, decimal(65,30), Unicode normalization-distinct text, binary, date, temporal precision 0/3/6, UTC instant, UUID, and NULL;
- `parity.composite_keys` proving logical key identity independent of backend PK/index order;
- `consistency.left` and `consistency.right`, each containing an `epoch`, changed atomically in one database transaction from `(1,1)` to `(2,2)`;
- evaluator-private fixture data sufficient to prove full evaluator state preservation and Subject non-disclosure;
- at least one explicitly identity-bound execution-relevant database program/config input used in an execution-drift negative case.

Named projections include:

- `parity.all`;
- a key/non-key subset projection;
- `consistency.pair`.

During a coordinated commit, each backend may choose a different legitimate scheduling side, but each must return only fully pre-commit `(1,1)` or fully post-commit `(2,2)`, never torn `(1,2)` / `(2,1)`.

Exact canonical projection/full-state/reset/restore/diff parity is required where scheduling does not legitimately change the selected committed state. SnapshotRef identifiers themselves are not compared because they are owner-scoped references rather than content identity.

For successful restore, each backend must report exactly `STATE_EQUIVALENT` for the base relational capability.

Portable TCK cases MUST NOT contain `if backend == postgres/mysql` branches. Engine setup SQL/configuration belongs outside the portable case tree.

## Reference implementation gate

No PostgreSQL/MySQL reference adapter should be merged as the official Alpha 3 relational implementation until:

1. AEP-0010 is explicitly `Accepted`;
2. relational normative specification and requirement index are reviewable;
3. serialized protocol resources have closed schemas;
4. language-neutral execution-sensitive TCK is registered;
5. the common implementation interface is derived from those authorities.

PostgreSQL-first public APIs generalized later are explicitly prohibited.

## Backward compatibility

The profile is additive:

- existing `avp-environment-v0.1` implementations need not claim `state.relational`;
- existing Fabric resources without the relational capability remain unaffected;
- no Environment/Fabric/Core/Scenario/Security/Evidence meaning is replaced;
- the relational profile narrows successful restore fidelity for its own capability to exactly `STATE_EQUIVALENT` after verified state restoration, consistent with Environment's existing fidelity definitions;
- execution-relevant database identities reuse Scenario/Fabric identity binding rather than changing Scenario semantics;
- evaluator-private state handling reuses Security/Evidence visibility/classification rather than adding a new security model;
- PostgreSQL/MySQL mechanism choices remain implementation-specific;
- no Alpha 3 release version is selected by this AEP.

Because pre-1.0 PATCH releases must not intentionally introduce breaking normative changes, Alpha 3 release selection remains a separate release-management decision and is not implicitly `0.3.1`.

## Alternatives considered

### Separate PostgreSQL and MySQL protocol profiles

Rejected as the primary abstraction because product identity would become protocol identity and meaningful cross-backend conformance would disappear.

### Universal AVP SQL/transaction API

Rejected. AVP verifies state; it is not an ORM, SQL wire protocol, or database client standard.

### Raw SQL dumps as portable snapshots

Rejected because dump syntax/semantics are vendor-specific and cannot establish common restore fidelity.

### Raw DDL/catalog hashing as state/schema identity

Rejected because portable logical bindings may remain equivalent across different backend catalogs while catalog changes may also be irrelevant to selected state semantics.

### Put all execution-relevant DB program/configuration into RelationalStateManifest

Rejected. It would conflate logical relational state interpretation with the complete Environment execution identity and would force backend-specific program/config concepts into the portable state schema. Existing Scenario/Fabric execution-input identity already owns this problem.

### Ignore triggers/configuration when rows are initially equal

Rejected. Equal initial canonical state can still produce materially different Episode behavior when execution-relevant database programs/configuration differ.

### Remove evaluator-private rows from the full StateImage

Rejected. That would weaken the evaluator's authoritative state and confuse completeness with Subject visibility. Existing Evidence classification and Security routing govern confidentiality.

### Make all relational Artifacts universally retrievable by Subject

Rejected. Artifact identity is not retrieval authorization, and evaluator-confidential relational state may be required for verification.

### Hashing driver-returned rows directly

Rejected because driver numeric, temporal, binary, Unicode, ordering, and collation behavior is not a portable canonical representation.

### JSON numbers for relational integer/decimal values

Rejected because RFC 8785/JCS canonical JSON numbers inherit IEEE-754 constraints. Exact relational high-precision values are typed strings.

### Generic extension/value bags

Rejected for mandatory v0.1 scalar/state structure. Unsupported values fail closed until a governed revision defines them.

### Backend primary-key identity

Rejected as protocol identity. Logical row keys are Manifest-owned and backend key/index metadata is implementation evidence.

### Query-language projections

Rejected for v0.1. Named projections are static all-row relation/column subsets; portable filters/joins/expressions require later governance.

### Auto-commit during QUIESCING

Rejected because Control would fabricate Subject-committed state and alter task semantics.

### Allow successful restore to report NON_EQUIVALENT

Rejected. If the profile independently proves the same Manifest-bound full authoritative state was re-established, it has established state equivalence. Reporting `NON_EQUIVALENT` would make successful capability semantics ambiguous.

### `EXACT` restore after restoring rows

Rejected because logical row equality does not prove sequence/auto-increment or broader execution-state equality.

### Implement PostgreSQL first and generalize later

Rejected by Alpha 3's no-transitional-architecture gate.

## Design decision evidence

Initial Draft blockers:

- RS-BR-001 canonical scalar lexical encoding;
- RS-BR-002 Manifest/StateImage identity;
- RS-BR-003 authoritative surface/named projections;
- RS-BR-004 portable row identity;
- RS-BR-005 QUIESCING/unsettled Subject activity;
- RS-BR-006 schema drift/binding boundary;
- RS-BR-007 cross-backend parity fixture;
- RS-BR-008 language-neutral TCK execution interface.

Supporting non-normative evidence:

- `docs/design/alpha3-relational-state-canonical-model.md`;
- `docs/design/alpha3-relational-state-surface-and-row-identity.md`;
- `docs/design/alpha3-relational-state-quiescing-and-schema-drift.md`;
- `docs/design/alpha3-relational-state-tck-and-parity.md`;
- `docs/design/alpha3-relational-state-profile-design.md`;
- `docs/design/alpha3-relational-state-proposed-readiness-audit.md`.

Formal Proposed review at `29586a050a758a7058e1489df8c0b75e1d7088ca` identified:

- RS-PR-001 evaluator-private state visibility;
- RS-PR-002 execution-relevant database program/config identity;
- RS-PR-003 exact successful restore fidelity.

The decisions are recorded in `docs/design/alpha3-relational-state-proposed-review-blockers.md` and are incorporated into this AEP version. Incorporation does **not** itself mean the blockers are formally closed for acceptance; exact-head gates and acceptance-oriented re-review are still required.

## Governance boundary

This AEP is **Proposed**.

`Proposed` does not authorize implementation or downstream normative closure. Before the relational normative candidate surface is created, AEP-0010 must receive an explicit recorded protocol-maintainer `Accepted` decision under repository governance.

Required next steps are:

1. synchronize supporting design/TCK/parity documentation with RS-PR-001..003;
2. run exact-head CI, Governance, and Release Validation;
3. conduct a short acceptance-oriented protocol re-review;
4. only if that review finds no acceptance blocker, record `ACCEPTANCE-READY` review evidence;
5. only after a separate explicit protocol-maintainer instruction, transition `Proposed -> Accepted`.

Generic continuation instructions do not constitute `Accepted` or merge authorization.

This AEP does not authorize:

- relational normative spec/schema/TCK registration;
- PostgreSQL/MySQL backend implementation as official Alpha 3 adapters;
- merging any stacked PR;
- changing AEP-0009 to Final;
- selecting `0.3.1` or another release;
- tags, GitHub Release, package-index publication, signing, or attestation publication.

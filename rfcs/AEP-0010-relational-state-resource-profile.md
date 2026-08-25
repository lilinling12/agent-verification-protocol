# AEP-0010 — Relational State Resource Profile v0.1

- Status: Accepted
- Authors: AVP maintainers and contributors
- Created: 2026-08-24
- Proposed: 2026-08-24
- Accepted: 2026-08-24
- Proposed-readiness evidence: `docs/design/alpha3-relational-state-proposed-readiness-audit.md`
- Formal Proposed review: PR #86 review `5004337751`
- Acceptance-oriented review: PR #86 review `5004370426`
- Final pre-acceptance review note: PR #86 review `5004379749`
- Proposed-review blocker decisions: `docs/design/alpha3-relational-state-proposed-review-blockers.md`
- Accepted decision: `docs/acceptance/alpha3-aep-0010-accepted-decision.md`
- Parent: AEP-0009 — Environment Fabric Composition and Capability Contract (Accepted)
- Target AVP version: Unselected future protocol version
- Alpha phase: Alpha 3 — Environment Fabric / Relational State

## Summary

AEP-0010 defines the accepted portable direction for the first resource-domain profile under AVP Environment Fabric: relational state.

The core rule is:

> AVP standardizes the observable logical relational-state boundary and the identity/evidence required to verify it; database products and database mechanics remain implementation details.

The accepted Resource Capability identity is:

```text
capabilityId: state.relational
profile: avp-relational-state-v0.1
revision: "0.1"
```

The capability is one cohesive portable claim. It is not a temporary collection of `supports_*` flags and it is not a PostgreSQL or MySQL product profile.

`Accepted` approves this protocol direction and authorizes downstream normative closure through the repository authority chain. It does **not** make this AEP `Final`, does not make future draft schemas/TCK normative by themselves, does not authorize backend-first implementation, and does not authorize merge, release selection, publication, signing, or attestation.

## Problem

Relational state is common in agent verification, but superficially similar database mechanisms have different guarantees. Without a portable contract, implementations can accidentally create incompatible protocol semantics by:

- treating PostgreSQL exported transaction snapshots as AVP SnapshotRef identity;
- treating MySQL consistent reads as equivalent protocol objects;
- inheriting server-default isolation and calling the result deterministic;
- hashing driver-returned values without portable canonicalization;
- using raw DDL or system catalogs as schema/state identity;
- restoring logical rows and overclaiming `EXACT` fidelity;
- exposing uncommitted or torn cross-relation state;
- using Subject credentials for Evaluator/Control operations;
- leaking evaluator-private relational state through Subject-visible routes;
- treating equal rows as complete Environment identity even when execution-relevant triggers/configuration differ;
- implementing PostgreSQL first and later generalizing its API into the supposed portable abstraction.

AEP-0010 prevents those implementation choices from becoming protocol authority.

## Existing AVP authority reused

AEP-0010 specializes existing contracts rather than creating competing concepts.

### Environment

Reused unchanged:

- authoritative Environment/resource ownership;
- ScenarioInstance binding;
- evaluator projection identity `(projection identifier, state digest)`;
- SnapshotRef ownership and foreign/stale fail-closed behavior;
- restore fidelity vocabulary `EXACT | STATE_EQUIVALENT | NON_EQUIVALENT`;
- semantic diff binding;
- released-handle failure.

### Environment Fabric

Reused unchanged:

- `resourceKind: state`;
- Resource Capability declaration/revision binding;
- required/optional participation;
- resource identity and `identityArtifacts`;
- Resource Capability versus Subject Capability separation;
- per-resource/composite result honesty;
- weakest-required-participant aggregate fidelity;
- no implicit distributed transaction;
- retry-safe cleanup.

### Scenario

Reused unchanged:

- unresolved required execution inputs fail before Episode execution;
- execution-relevant references bind profile-appropriate resolved identity;
- materialized execution semantics remain immutable during an Episode;
- Subject capability exposure derives from the materialized actor projection.

### Core

Reused unchanged:

- Core lifecycle including `QUIESCING` and `VERIFYING`;
- no new Subject-requested side effect after entry into `QUIESCING`;
- already accepted work may settle;
- lifecycle, Validity, infrastructure condition, and Task Verdict remain separate.

### Security and Evidence

Reused unchanged:

- Subject/Evaluator/Control authority separation;
- undeclared Subject capability denial before side effects;
- evaluator/control credentials absent from Subject execution context;
- evaluator-private material protected from Subject disclosure;
- `SecurityAssurance` remains non-inflating and multi-dimensional;
- Artifact identity is SHA-256 over exact retained bytes;
- locator is not identity;
- Evidence classification controls handling/visibility but does not alter content digest.

## Scope

One `state.relational` resource represents one logical relational-state boundary.

The v0.1 direction standardizes:

- one immutable logical `RelationalStateManifest`;
- one required baseline `RelationalStateImage`;
- one closed authoritative relation/column state surface;
- one closed portable scalar vocabulary;
- portable logical row identity;
- named evaluator projections;
- exact canonical bytes and state digests;
- one committed observation boundary across selected relations;
- logical snapshot/reset/restore;
- semantic row-level diff;
- logical schema/binding drift behavior;
- execution-relevant database input identity composition;
- Core `QUIESCING` settlement behavior;
- Security/Evidence/Fabric composition;
- backend-neutral execution-sensitive conformance;
- PostgreSQL/MySQL cross-backend reference parity evidence.

Multiple independently managed databases are separate Fabric resources. v0.1 introduces no cross-database atomicity.

## Explicit non-goals

The v0.1 profile does not standardize:

- a universal SQL client API or ORM;
- public `begin`, `commit`, `rollback`, savepoint, or lock operations;
- PostgreSQL exported-snapshot identifiers;
- MySQL read-view identifiers;
- raw SQL dumps or physical backup formats as portable state identity;
- raw DDL/catalog digests as portable logical state identity;
- query plans, optimizer statistics, MVCC transaction IDs, locks, session handles, or connection-pool internals;
- exact sequence/auto-increment continuation state;
- portable schema migration during an Episode;
- cross-Environment SnapshotRef import;
- approximate floating-point, database-native JSON/XML/spatial/array/interval/vendor-extension semantics in mandatory v0.1;
- a global database determinism claim;
- PostgreSQL/MySQL product names as protocol identity;
- a relational-specific secrecy taxonomy;
- the complete Environment execution identity inside `RelationalStateManifest`.

## Relational state identity Artifacts

A conforming relational resource binds exactly two required relational state-identity Artifacts through the existing Fabric resource identity-artifact surface:

1. one `RelationalStateManifest`;
2. one baseline `RelationalStateImage`.

Their roles are identified by profile-defined media type, not by array position.

Candidate media types for downstream normative closure are:

```text
application/vnd.avp.relational-state-manifest+json
application/vnd.avp.relational-state-image+json
application/vnd.avp.relational-projection+json
application/vnd.avp.relational-diff+json
```

The Manifest does not contain the baseline StateImage ArtifactRef. The baseline StateImage binds the Manifest digest. This keeps content-addressed identity acyclic:

```text
EnvironmentResource
  -> Manifest ArtifactRef
  -> Baseline StateImage ArtifactRef
       -> manifestDigest
```

Runtime snapshot StateImages are generated Evidence associated with Environment/resource-owned SnapshotRef identity; they do not mutate the immutable resource identity-artifact inputs.

## RelationalStateManifest

The Manifest defines portable logical **state interpretation** semantics, not backend DDL and not the complete Environment execution identity.

It binds at minimum:

- profile/revision identity;
- logical relation identifiers;
- logical column identifiers;
- logical scalar types and type parameters;
- nullability;
- logical row-key columns;
- complete authoritative state surface;
- named projection definitions;
- canonical representation version.

Logical identifiers use a restricted deterministic vocabulary so identity/order does not depend on backend identifier folding, locale, or Unicode normalization. Exact field names, regexes, and length limits are downstream schema work.

Backend table/column names, DSNs, migrations, driver settings, and vendor catalogs remain adapter/deployment bindings unless separately selected as execution-relevant identity.

The Manifest Artifact digest is the portable logical relational-state interpretation identity.

## Execution-relevant database input identity

Logical state equality does not establish complete Environment execution identity.

A database program/configuration input outside the Manifest can materially change Subject execution while leaving identical Manifest and baseline StateImage bytes. Examples include, when actually relied upon by the materialized Scenario:

- triggers;
- defaults;
- generated expressions;
- execution-visible constraints;
- routines/functions/procedures;
- extensions/plugins;
- SQL modes or equivalent semantic configuration;
- timezone/session interpretation settings;
- schema-program or migration revision;
- collation/configuration that changes execution semantics;
- another database program/configuration input materially relied upon by execution.

Rules:

1. `RelationalStateManifest` MUST NOT be treated as complete Environment execution identity merely because the logical state is complete.
2. Execution-relevant database inputs outside the Manifest MUST bind to profile-appropriate resolved immutable identity through existing Scenario/Fabric execution-input mechanisms.
3. Relevance is determined by the materialized execution contract; irrelevant backend metadata is not identity-bound merely because it exists.
4. Missing required execution identity fails closed before Episode execution.
5. These execution identities remain distinct from relational canonical state digests.
6. Product names, catalog fingerprints, process IDs, and server-default labels do not substitute for required immutable identity.
7. Drift of a bound execution-relevant database input invalidates the execution binding even if the logical Manifest remains structurally satisfiable.

## Authoritative state surface

Every relation and column declared in the Manifest is part of the v0.1 authoritative logical state surface.

There is no `authoritative:false` escape hatch inside a declared relation.

Backend state absent from the Manifest is outside the relational `STATE_EQUIVALENT` claim.

An adapter must not silently omit selected relations/columns because it cannot normalize, observe, restore, or diff them. Incompatibility fails closed.

Evaluator-private rows/columns may remain authoritative. Confidentiality is enforced by Security/Evidence visibility and access rules, not by deleting evaluator-private data from authoritative state.

## Portable scalar model

Canonical relational values use typed records. Example:

```json
{"type":"integer","value":"42"}
```

A nullable value retains its declared type:

```json
{"type":"integer","value":null}
```

Row-key values are never null.

The accepted mandatory v0.1 scalar set is deliberately closed and conservative:

- `boolean` — JSON boolean only;
- `integer` — exact signed integer with at most 65 decimal digits, encoded as canonical decimal string;
- `decimal` — precision 1..65, scale 0..30, `scale <= precision`, fixed-point canonical string;
- `text` — exact Unicode scalar sequence with no AVP Unicode normalization;
- `binary` — canonical unpadded RFC 4648 base64url;
- `date` — valid Gregorian `YYYY-MM-DD`, portable year range 1000..9999;
- `time-local` — local time-of-day, fractional precision 0..6, no timezone/elapsed-time semantics;
- `timestamp-local` — local date-time, portable year range 1000..9999, fractional precision 0..6;
- `timestamp-instant` — UTC-normalized `...Z`, fractional precision 0..6;
- `uuid` — canonical lowercase RFC 9562 hex-and-dash text;
- SQL `NULL` — only where the logical column is nullable.

Integer and decimal values do not use JSON number tokens, preventing IEEE-754/JCS number precision from becoming relational state semantics.

Adapters fail closed rather than rounding, truncating, timezone-shifting, Unicode-normalizing, or otherwise making unsupported values fit the declared portable model.

## Canonical bytes

Manifest, StateImage, Projection, and Diff objects use RFC 8785 JCS exact UTF-8 bytes after values have been converted to the closed relational model.

Canonical ordering is profile-defined before JCS serialization:

- relations by logical relation identifier;
- columns by logical column identifier;
- logical row-key column declarations by logical column identifier;
- rows by unsigned lexicographic order of canonical JCS row-key bytes.

Backend collation, table creation order, physical row order, index order, and SQL result order are not canonical identity.

Existing AVP Artifact identity applies to retained bytes. No second relational hashing system is introduced.

## Logical row identity

Every authoritative relation declares a non-empty logical row-key set.

At an accepted observation boundary:

- every key column is present;
- key values are non-null;
- key values obey canonical scalar semantics;
- the complete canonical logical key is unique within the relation.

A backend PK/unique constraint may establish that property, but its name, kind, declaration order, and physical index order are not protocol identity.

An adapter must not manufacture uniqueness from tuple IDs, physical row ordinals, or whole-row hashes.

Changing a logical key is represented in semantic diff as delete-old-key plus insert-new-key.

Stored generated IDs may be logical row keys; sequence/auto-increment continuation state remains outside base relational `STATE_EQUIVALENT`.

## Full RelationalStateImage

A `RelationalStateImage` covers the complete authoritative relational state surface and binds the exact Manifest Artifact digest.

Its canonical content includes every authoritative relation, every authoritative column, and every row exactly once in canonical key order.

The StateImage does not contain its own digest. SHA-256 over its exact canonical bytes is both its Artifact identity when retained and its full authoritative relational-state digest.

A StateImage whose Manifest digest does not match the bound Manifest fails closed.

A StateImage may contain evaluator-private authoritative data; handling classification/access control remains governed by existing Evidence/Security contracts.

## Named evaluator projections

Named projections are immutable Manifest definitions.

A v0.1 projection selects:

- one or more Manifest relations;
- one or more Manifest columns from each selected relation;
- all rows of those relations at one observation boundary.

Every selected relation's logical key columns are mandatory in the evaluator projection.

v0.1 does not define portable SQL text, predicates, joins, expressions, aggregates, grouping, windows, limits/offsets, backend view/procedure/function names, or order-by semantics.

Projection output binds the Manifest digest, projection identifier, and canonical selected content. Environment projection identity remains `(projection identifier, state digest)`.

## Subject-visible relational observation

Evaluator projection and Subject observation are distinct surfaces.

Subject-visible relational observations must obey Scenario actor projection, Environment actor-scoped observation, and Security hidden-material rules:

- only state authorized for the Subject may be exposed;
- evaluator-private rows/columns and verification-only relational data are not disclosed unless the Scenario explicitly makes them observable;
- a Subject-visible locator does not grant retrieval authority to evaluator-private Artifact bytes;
- an opaque digest may be exposed only under existing AVP rules where the identity itself does not disclose protected content or grant retrieval authority;
- redacted/Subject-scoped bytes are distinct Artifact bytes and have their own Artifact digest.

Artifact identity is not authorization.

## Committed observation boundary

An accepted evaluator relational projection represents one committed logical database view.

It must never expose uncommitted Subject state.

For concurrent transactions, a projection may legitimately reflect the fully committed state before or after a concurrent commit. It must not combine incompatible visibility points into a torn multi-relation result.

Implementation mechanisms may use MVCC snapshots, synchronized/exported snapshots, writer quiescence, or another mechanism proving the same observable property. The TCK tests the property, not the SQL command sequence.

## Core QUIESCING composition

The relational profile adds no second lifecycle.

After Core enters `QUIESCING`:

- new Subject mutation activity is rejected before database side effects;
- work accepted before the boundary may settle;
- final relational verification begins only after a Subject-mutation settlement barrier is established.

The settlement barrier requires relevant accepted mutations to have a known committed, rolled-back/cancelled, or otherwise non-mutating terminal outcome while admission of new Subject mutation activity remains closed.

The implementation must not auto-commit Subject transactions, weaken observation to dirty reads, or treat an executed SQL statement as committed state merely because it ran.

A bounded settlement policy may be deployment/profile identity. Failure to establish trustworthy settlement produces no accepted final relational projection and follows existing infrastructure/Validity semantics rather than becoming Agent Task Verdict failure by itself.

Cleanup after failure cannot retroactively turn unresolved Subject work into committed task state.

## Logical schema/binding drift

The Manifest is immutable for one resource instance.

Portable relational schema/binding drift means the current backend binding can no longer satisfy that immutable Manifest, not merely that raw DDL/catalog bytes changed.

Fail-closed examples include:

- selected relation/column no longer resolves or becomes ambiguous;
- scalar/precision/time mapping becomes lossy or unsupported;
- logical key columns become unavailable;
- logical identifiers are redirected to different backend state under the same Manifest;
- concurrent selected-schema change prevents one consistent Manifest-bound observation.

Changes outside the selected binding are not automatically drift, including unrelated tables/columns, irrelevant index changes, optimizer/statistics changes, or constraint-name changes when portable semantics remain valid.

If a separate execution-relevant database input is identity-bound, drift of that identity invalidates execution even when the logical relational Manifest remains satisfiable.

Catalog fingerprints may be implementation diagnostics/cache evidence; they are neither Manifest identity nor conformance proof.

## Snapshot

A successful logical relational snapshot:

- establishes one committed consistent observation of the full authoritative surface;
- produces exact canonical `RelationalStateImage` bytes;
- retains/binds those bytes under existing Artifact identity;
- binds the generated StateImage to the owning Environment/resource SnapshotRef;
- preserves Evidence classification/access boundaries;
- fails closed on unsupported values, binding drift, execution-binding invalidity, inconsistent observation, integrity error, or ownership error.

Backend transaction tokens, dump files, WAL/binlog positions, physical snapshot paths, and equivalent mechanisms are not portable SnapshotRef identity.

## Reset

v0.1 binds one required baseline StateImage as resource state identity.

Reset success is accepted only after the implementation:

1. revalidates required logical and execution bindings;
2. independently re-projects the complete authoritative state surface; and
3. proves exact canonical equality with the baseline StateImage identity under the same Manifest.

Backend command success alone is insufficient.

Reset failure is infrastructure/Validity information, not Agent Task Verdict failure solely because it occurred.

## Restore fidelity

Base v0.1 restore is logical-state restore.

For an owner-valid SnapshotRef:

1. the implementation performs restore using any conforming backend mechanism;
2. it independently re-projects the complete authoritative relational state surface;
3. successful restore exists only if the snapshot StateImage identity is re-established under the same Manifest;
4. every successful base relational restore reports resource fidelity exactly `STATE_EQUIVALENT`;
5. failure to re-establish the snapshot StateImage is a failed/non-equivalent restore;
6. `EXACT` is not a valid successful fidelity claim for `state.relational / avp-relational-state-v0.1 / 0.1`.

`EXACT` is excluded because sequence/auto-increment continuation, transaction/MVCC/session/lock/cache state, physical storage identity, and other execution state are not standardized by the base profile.

Fabric aggregate fidelity continues to use existing weakest-required-participant semantics.

A stronger relational restore capability requires separate governance and executable conformance evidence.

## Semantic diff

Diff operates between states bound to the same Manifest and the same projection semantics.

Per logical relation/key:

- key only in after -> insert;
- key only in before -> delete;
- same key/equal canonical values -> unchanged;
- same key/non-key values changed -> update;
- key changed -> delete old plus insert new.

Diff identity binds before-state identity, after-state identity, and projection/Manifest semantics. Physical row identity and backend operation order are not diff identity.

Cross-Manifest comparison is binding/schema drift, not ordinary row diff.

Evaluator-private diff content follows the same Evidence classification/access rules as its source states.

## Security considerations

Relational adapters create privileged Environment authority and preserve three conceptual contexts:

```text
Subject data authority
Evaluator projection authority
Control provision/reset/restore authority
```

Required direction:

1. Subject database authority derives only from materialized Scenario capability exposure.
2. Resource Capability support never grants Subject access to Evaluator/Control operations.
3. Evaluator/Control credentials do not enter Subject execution context.
4. Portable relational Artifacts do not contain database passwords, secret DSNs, control tokens, signing secrets, or equivalent authority-bearing credentials.
5. Portable relational Artifacts may contain evaluator-private authoritative data required by verification; existing Evidence classifications and access controls govern handling.
6. Subject-visible relational routes/results/observations/locators do not disclose evaluator-private state or grant unauthorized retrieval.
7. A generic database-admin connection is not a Subject capability.
8. Backend diagnostics may be evaluator-visible but are sanitized where necessary before Subject exposure.
9. Container, managed-database, role separation, VM, or engine labels do not automatically upgrade `SecurityAssurance`.
10. Deployments should use independently least-privileged Subject/Evaluator/Control credentials where supported, without standardizing database role syntax.

A deployment that cannot enforce the required Subject-route admission/visibility boundary cannot claim the corresponding relational profile semantics merely because its database supports snapshots or roles.

## Failure and Validity semantics

Relational infrastructure/Validity failures include, as applicable:

- resource unavailable;
- required Manifest/baseline Artifact missing or integrity-invalid;
- Manifest/StateImage identity mismatch;
- selected relation/column binding failure;
- required execution-relevant database identity missing or drifted;
- unsupported/lossy scalar mapping;
- duplicate/null logical row key;
- inability to establish one committed consistent observation;
- unsettled Subject mutation preventing trustworthy final observation;
- selected logical schema/binding drift;
- reset baseline mismatch;
- restore state mismatch;
- stale/foreign resource or SnapshotRef;
- loss of Evaluator/Control authority;
- inability to preserve required evaluator-private/Subject-visible separation.

Vendor-specific error codes are diagnostics, not portable AVP outcome identity.

These conditions are not converted directly into Agent Task Verdict failure solely because they occurred.

## Conformance strategy

The future `avp-relational-state-v0.1` TCK must execute real implementation behavior.

Portable SUT obligations include observable equivalents of:

- provision compatible Manifest + baseline + required execution-input bindings;
- project a named evaluator projection;
- snapshot full authoritative state;
- reset to baseline;
- restore owner-valid snapshot;
- semantic diff;
- `QUIESCING` / final-observation participation;
- release.

Exact programming-language method names are non-normative.

The portable profile does not require generic SQL/query/transaction/DDL/catalog APIs.

### Privileged fixture controls

Executable conformance requires a privileged fixture-control seam that may:

- apply logical row mutation batches;
- hold/commit/rollback a TCK Subject transaction;
- introduce selected/unselected schema changes;
- alter an execution-relevant bound DB program/configuration input;
- coordinate a commit during projection;
- activate negative implementation behavior.

Fixture controls are TCK harness mechanics, not Resource Capabilities or public Subject APIs.

Portable case vectors describe logical intent; backend-specific drivers translate those controls into PostgreSQL/MySQL mechanics outside the portable case semantics.

### Mandatory conformance families

Normative closure must cover at least:

1. Manifest/baseline ownership and stale references;
2. scalar/canonical exact-byte stability;
3. named/full projection semantics;
4. multi-relation committed-view non-tearing;
5. uncommitted-state exclusion and `QUIESCING` settlement;
6. logical binding drift plus non-drift controls;
7. execution-relevant DB input identity binding/drift;
8. reset verified by post-reset state identity;
9. snapshot/mutate/restore verified by re-projection with successful fidelity exactly `STATE_EQUIVALENT`;
10. insert/delete/update/key-change semantic diff;
11. Subject/Evaluator/Control authority separation;
12. evaluator-private relational-state non-disclosure through Subject-visible surfaces;
13. execution-sensitive capability honesty.

### Negative implementations

At minimum, the TCK must reject metadata-identical broken implementations such as:

- `TornProjectionAdapter` — advertises the same capability but observes selected relations through incompatible committed views;
- `FalseRestoreAdapter` — advertises the same capability and reports restore success without re-establishing snapshot StateImage identity.

Normative closure must also include hidden-state leakage and execution-input drift negative behavior sufficient to prove those semantics are executed rather than merely declared.

TCK PASS must derive from observed runtime behavior, not capability metadata, fixture inspection, backend product labels, or implementation self-report alone.

## Cross-backend reference parity

Third-party conformance requires one implementation to pass the profile. It does not require shipping PostgreSQL and MySQL together.

The AVP project's reference-completeness standard is stricter. Before Relational State is called cross-backend reference-complete:

- one PostgreSQL adapter independently passes the portable relational profile;
- one MySQL/InnoDB adapter independently passes the same profile;
- both execute the same language-neutral case vectors;
- a shared immutable parity fixture proves canonical equality where deterministic equality is required;
- metadata-identical negative adapters are rejected;
- both preserve execution-input identity semantics and evaluator-private visibility semantics.

The shared fixture covers at least:

- all mandatory scalar types and boundary precision cases;
- Unicode normalization-distinct text;
- binary and nullability;
- composite logical row keys independent of backend PK/index ordering;
- full and subset projections;
- a two-relation consistency case whose committed transaction moves `(1,1)` to `(2,2)` and never permits torn `(1,2)` / `(2,1)` output;
- evaluator-private state and Subject non-disclosure;
- one explicitly identity-bound execution-relevant database program/configuration drift case;
- reset, snapshot/restore, and diff parity.

During a coordinated commit, each backend may legitimately choose fully pre-commit or fully post-commit state; they need not choose the same scheduling side. Each must independently satisfy the non-torn invariant.

SnapshotRef identifiers are not compared across backends because they are owner-scoped references, not content identity.

Portable TCK cases contain no `if backend == postgres/mysql` semantics. Backend setup SQL/configuration remains outside the portable case tree.

## Alternatives rejected

The Accepted direction rejects:

- separate PostgreSQL and MySQL primary protocol profiles for the mandatory relational semantics;
- a universal AVP SQL/transaction API;
- raw SQL dumps as portable snapshots;
- raw DDL/catalog hashing as logical state identity;
- putting all execution-relevant database program/configuration into the relational Manifest;
- ignoring execution-relevant triggers/configuration merely because initial rows are equal;
- removing evaluator-private rows from the full StateImage to make it Subject-safe;
- making evaluator-confidential Artifacts automatically Subject-retrievable;
- hashing raw driver-returned rows;
- JSON numbers for high-precision relational integer/decimal values;
- generic untyped extension/value bags as a shortcut for known v0.1 structure;
- backend primary-key/index metadata as protocol row identity;
- portable query-language projections in v0.1;
- Control auto-commit during `QUIESCING`;
- allowing a successful restore to report `NON_EQUIVALENT` after independently verified state equality;
- `EXACT` restore based only on restored logical rows;
- PostgreSQL-first implementation generalized later.

## Review history

Draft -> Proposed closed:

- RS-BR-001 canonical scalar lexical encoding;
- RS-BR-002 Manifest/StateImage identity;
- RS-BR-003 authoritative surface/named projections;
- RS-BR-004 portable row identity;
- RS-BR-005 `QUIESCING`/unsettled Subject activity;
- RS-BR-006 schema/binding drift;
- RS-BR-007 cross-backend parity fixture;
- RS-BR-008 language-neutral TCK execution boundary.

Formal Proposed review `5004337751` then identified:

- RS-PR-001 evaluator-private state visibility;
- RS-PR-002 execution-relevant DB program/config identity;
- RS-PR-003 successful restore fidelity ambiguity.

All three were incorporated before acceptance-oriented review `5004370426`, which found them closed and found no new acceptance blocker.

Final pre-acceptance head `ad79ca158fce56851ce2fd545735bd86794baadb` passed CI #526, Governance #572/#573, and Release Validation #62. Final-head review note `5004379749` confirmed the semantic review-to-final-head change was ROADMAP-only.

The explicit protocol-maintainer decision recorded in `docs/acceptance/alpha3-aep-0010-accepted-decision.md` authorizes the lifecycle transition to `Accepted`.

## Acceptance effect

AEP-0010 `Accepted` authorizes the next governed authority slice:

```text
Accepted AEP-0010
  -> Normative Spec
  -> Requirement Index
  -> Schema
  -> Execution-sensitive TCK
  -> Reference Runtime / common interface
  -> PostgreSQL adapter
  -> MySQL/InnoDB adapter
  -> Cross-backend parity acceptance
```

The next work must create a coherent relational normative candidate through the repository's active candidate-surface governance.

Schema and TCK must derive from normative specification semantics. They may not invent missing semantics or use backend behavior as authority.

A common implementation interface may be implemented only after its semantics are defined by the portable authority slice. It must not be a PostgreSQL API generalized later.

## Governance boundary

This AEP is **Accepted**, not Final.

Acceptance authorizes relational normative specification, requirement-index, schema, and execution-sensitive TCK work through the governed authority chain.

Acceptance does **not** authorize:

- merge of PR #86 or parent stacked PRs #83/#84/#85;
- AEP-0010 `Final`;
- AEP-0009 `Final`;
- PostgreSQL/MySQL backend-first implementation before the portable Spec -> Schema -> TCK slice is reviewable;
- selecting an Alpha 3 release version;
- assigning Alpha 3 to `0.3.1`;
- changing release-development mode;
- tag or GitHub Release creation;
- package-index publication;
- signing or attestation publication;
- treating Python reference-runtime behavior as protocol authority.

Stable `v0.3.0` remains the published Alpha 2 baseline. Repository source remains in `0.3.1.dev0` development mode until separate release-management authority changes it.

## Final decision

**AEP-0010: ACCEPTED.**

**Relational State direction: APPROVED.**

**Relational normative specification / requirement-index / schema / TCK work: AUTHORIZED through the governed authority chain.**

**PostgreSQL/MySQL backend-first or transitional implementation: NOT AUTHORIZED.**

**PR #86 merge: NOT AUTHORIZED by this decision.**

**Alpha 3 release/version/publication: NOT AUTHORIZED.**

# Alpha 3 Relational State Profile Design Audit

Status: **DRAFT DESIGN — NOT READY FOR PROPOSED**

Parent authority: AEP-0009 (Accepted)
Proposal: AEP-0010 (Draft)

## 1. Purpose

This document records the design boundary for the first Environment Fabric resource-domain profile. It is non-normative evidence for reviewing AEP-0010 and exists specifically to prevent PostgreSQL or MySQL implementation details from defining the protocol by precedent.

The intended order remains:

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

No database adapter should be merged as the official Alpha 3 relational implementation before the portable authority chain is reviewable.

## 2. Existing authority reused

Relational State specializes rather than replaces existing contracts:

- Environment owns authoritative resources and Scenario binding.
- Environment projection identity remains `(projection identifier, state digest)`.
- Environment snapshot references remain Environment-owned and foreign/stale use fails closed.
- Restore fidelity remains `EXACT | STATE_EQUIVALENT | NON_EQUIVALENT`.
- Environment semantic diff binds before/after state plus projection semantics.
- Fabric owns Resource identity, `REQUIRED`/`OPTIONAL` participation, composite result honesty, and Resource Capability negotiation.
- Security owns Subject/Evaluator/control authority separation and `SecurityAssurance`.
- Evidence/Artifact owns exact retained-byte identity.
- Core owns `QUIESCING`, Validity, infrastructure failure, and Task Verdict separation.

Relational State must not introduce alternate versions of those concepts.

## 3. Portable semantic boundary

### 3.1 One cohesive capability

Initial profile identity:

```text
capabilityId: state.relational
profile: avp-relational-state-v0.1
revision: "0.1"
```

A conforming claim covers the mandatory relational surface as one reviewed unit. The project should not expose temporary `supports_projection`, `supports_snapshot`, `supports_postgres`, or similar flags.

### 3.2 Closed logical state surface

A separate `RelationalStateManifest` describes the authoritative logical state semantics. The base `EnvironmentResource` remains unchanged and closed.

The Manifest binds logical relations, logical columns, portable scalar types and parameters, nullability, ordered row keys, named projection definitions, and canonical representation version. It deliberately **does not** reference the baseline StateImage, avoiding a content-addressed identity cycle.

For `state.relational` v0.1, the existing Fabric `EnvironmentResource.identityArtifacts` binds exactly one Manifest ArtifactRef and exactly one baseline StateImage ArtifactRef. Their roles are determined by the profile-defined media types, never by array position. The baseline StateImage contains the Manifest Artifact digest.

Backend DDL, migration files, DSNs, physical table names, driver configuration, and engine-specific catalog details remain implementation evidence/binding information.

The exact identity model is fixed in `docs/design/alpha3-relational-state-canonical-model.md`.

### 3.3 Closed scalar vocabulary

The initial candidate scalar set is deliberately conservative:

- boolean;
- integer — signed exact value up to 65 decimal digits;
- decimal — precision 1..65, scale 0..30, `scale <= precision`;
- text — exact Unicode scalar sequence with no implicit normalization;
- binary — canonical unpadded RFC 4648 base64url;
- date — portable years 1000..9999;
- time-local — time of day only, precision 0..6;
- timestamp-local — local date/time, precision 0..6;
- timestamp-instant — UTC instant, precision 0..6;
- uuid — lowercase RFC 9562 hex-and-dash form.

Approximate floating point, JSON, XML, spatial values, arrays, intervals, vendor enum/set values, and opaque extensions are excluded from mandatory v0.1 until lossless canonical semantics are reviewed.

Canonical relational numeric values are strings inside typed value records rather than JSON numbers, preventing IEEE-754 serialization limits from defining database-state identity. Exact lexical rules and canonical JSON identity are fixed in `docs/design/alpha3-relational-state-canonical-model.md`.

This avoids a public `Any`/extension bag that later becomes impossible to normalize consistently across engines and languages.

### 3.4 Stable row identity

Every relation participating in mandatory semantic diff has an ordered non-null unique logical row key. It may map to a primary key or another backend uniqueness mechanism but is portable profile identity, not a constraint-name abstraction.

Relations without stable logical row identity must fail profile compatibility rather than silently produce weaker diff semantics.

## 4. Observation model

The evaluator projection represents one **committed logical database view**.

For a projection spanning multiple selected relations:

- all selected relations must be observed through one consistency boundary;
- uncommitted Subject state is never included;
- concurrent commit timing may permit a fully pre-commit or fully post-commit projection;
- a torn mixture across visibility points is non-conformant.

The protocol does not require a specific database command. Valid mechanisms may include an MVCC snapshot, synchronized/exported snapshot, writer quiescence, or another mechanism with the same observable property.

Server defaults are not evidence. Adapters must explicitly establish the selected profile semantics.

## 5. Canonical projection direction

Canonical projection bytes include/bind:

- relational Manifest Artifact digest;
- projection identifier;
- relations in profile-defined canonical order;
- columns in manifest order;
- rows ordered by canonical row-key bytes;
- typed canonical values.

The complete structure is serialized with RFC 8785 JCS; the state digest is SHA-256 over those exact canonical bytes.

Backend collation or unspecified SQL row ordering cannot determine identity. SQL `ORDER BY` may optimize extraction, but canonical ordering remains a profile responsibility.

Including Manifest identity in the projection preimage prevents equal row bytes under incompatible schema semantics from being mistaken for the same relational state.

When exact projection bytes are retained as an Artifact, their Artifact digest and relational projection state digest are the same SHA-256 value. Artifact identity is not claimed for bytes that were not retained/published.

## 6. State-image model

Use one canonical `RelationalStateImage` content model for two roles:

1. immutable baseline materialization/reset input;
2. runtime logical snapshot Artifact content.

The StateImage contains the bound Manifest Artifact digest plus the complete canonical authoritative state surface. It does not contain its own digest; SHA-256 over its exact RFC 8785 bytes is both retained Artifact identity and the v0.1 full authoritative relational state digest.

Ownership remains different:

- the baseline Manifest and baseline StateImage are immutable Fabric resource identity inputs;
- a runtime snapshot StateImage is generated evidence bound to the Environment/resource-owned SnapshotRef and does not mutate `EnvironmentResource.identityArtifacts`.

The Manifest never references the baseline image, so Artifact identity remains acyclic.

Cross-Environment snapshot import is explicitly outside v0.1.

## 7. Reset and restore

### Reset

Reset success requires post-reset re-projection of the full authoritative state surface and equality with the bound baseline StateImage identity. Backend command success is insufficient.

### Restore

The base relational profile restores logical authoritative state only. After restore it must re-project and prove equal relational state identity.

The maximum fidelity claim is `STATE_EQUIVALENT`.

`EXACT` is excluded because v0.1 does not standardize continuation/execution state such as PostgreSQL sequences, MySQL auto-increment allocation state, MVCC internals, sessions, locks, caches, or physical storage identity.

A future stronger capability must be separately governed.

## 8. Schema drift

The logical Manifest is immutable for one bound Environment instance. Selected schema drift invalidates the current binding.

Adapters must not silently reinterpret changed backend schema under the old Manifest.

This matters across engines because DDL/transaction visibility differs; for example, MySQL consistent reads can be invalidated by certain `DROP TABLE` / `ALTER TABLE` operations.

## 9. Security design

Three authority contexts remain distinct:

```text
Subject data authority
Evaluator projection authority
Control provision/reset/restore authority
```

One backend login may technically satisfy more than one role, but a production/reference adapter should not make credential sharing a protocol assumption. Subject execution context must not receive evaluator/control credentials.

Portable relational manifests, projections, state images, and operation results must never embed passwords or secret DSNs.

Database/container technology labels do not upgrade `SecurityAssurance`.

## 10. Failure classification

The following remain infrastructure/validity failures rather than Agent task failures solely by occurrence:

- database unavailable;
- required relation/column missing;
- schema drift;
- unsupported/lossy value mapping;
- row-key ambiguity;
- inability to establish a consistent committed view;
- unsettled Subject transaction preventing trustworthy final verification;
- snapshot integrity failure;
- reset mismatch;
- restore mismatch;
- stale/foreign references;
- loss of evaluator/control authority.

Vendor error codes are evaluator diagnostics, not portable conformance outcomes.

## 11. PostgreSQL implementation evidence

PostgreSQL current documentation provides multiple mechanisms that can satisfy parts of the portable contract:

- `READ COMMITTED` uses a new query-start snapshot per command;
- `REPEATABLE READ` holds one transaction visibility view;
- `pg_export_snapshot()` / `SET TRANSACTION SNAPSHOT` can coordinate snapshot visibility across transactions under documented constraints;
- synchronized `pg_dump` demonstrates multi-worker consistent snapshot mechanics;
- sequence operations demonstrate that equal logical rows do not imply exact continuation state.

None of these command/token identities belong in portable AVP objects.

## 12. MySQL/InnoDB implementation evidence

MySQL 8.4/InnoDB provides different mechanisms:

- default isolation is `REPEATABLE READ`;
- consistent nonlocking reads use MVCC read views;
- `WITH CONSISTENT SNAPSHOT` establishes the useful consistent snapshot under `REPEATABLE READ`;
- selected DDL can invalidate an existing consistent read;
- auto-increment allocation/persistence differs from PostgreSQL sequences.

Therefore the profile tests observation and restoration properties, not command equivalence.

## 13. Conformance architecture

The eventual TCK should have no PostgreSQL/MySQL branches in portable cases.

Mandatory behavior families:

1. canonical projection stability and mutation sensitivity;
2. consistent multi-relation observation under a coordinated concurrent commit;
3. exclusion of uncommitted Subject state;
4. schema-drift fail-closed behavior;
5. reset verified by post-reset projection;
6. snapshot/mutate/restore/re-project with `STATE_EQUIVALENT` maximum fidelity;
7. insert/update/delete semantic diff by logical row key;
8. ownership and stale-reference fail-closed behavior;
9. Subject/Evaluator/control authority separation;
10. metadata-identical broken implementation that returns torn projection or false restore success and MUST fail.

The PostgreSQL and MySQL reference adapters must independently execute the same cases.

A reference-completeness parity fixture should additionally require equivalent logical fixtures to produce identical canonical projection bytes/digests across both engines for the mandatory scalar set. Shipping two engines is not a requirement for third-party conformance; it is evidence that the reference profile is not secretly one-engine-shaped.

## 14. Draft → Proposed blockers

AEP-0010 remains Draft until all blockers below are explicitly closed and a separate Proposed-readiness audit confirms the AEP text itself incorporates the decisions.

### RS-BR-001 — Scalar lexical encoding

Status: **CLOSED FOR DRAFT → PROPOSED READINESS**

Decision evidence: `docs/design/alpha3-relational-state-canonical-model.md`.

Closed with typed value records, RFC 8785 canonical JSON, exact integer/decimal lexical rules, RFC 4648 base64url, RFC 9562 UUID normalization, explicit temporal lexical rules, 0..6 fractional precision, common portability ranges, no Unicode normalization, and fail-closed unsupported/lossy mappings.

### RS-BR-002 — Manifest versus state-image schema split

Status: **CLOSED FOR DRAFT → PROPOSED READINESS**

Decision evidence: `docs/design/alpha3-relational-state-canonical-model.md`.

Closed with distinct Manifest/StateImage Artifact types, acyclic identity, Fabric `identityArtifacts` binding Manifest + baseline by media type, baseline image binding Manifest digest, runtime StateImage binding through Environment/resource-owned SnapshotRef, and reuse of existing Artifact SHA-256 identity rather than a competing content-address scheme.

### RS-BR-003 — Authoritative surface versus named projections

Status: **OPEN**

Need precise rule for whether named projections are restricted subsets/views of one full authoritative surface and how projection definitions participate in identity.

### RS-BR-004 — Row-key portability

Status: **OPEN**

Need confirm the v0.1 mandatory row-key rule is sufficient for independent implementations and does not accidentally require backend primary-key syntax.

### RS-BR-005 — Final observation under unsettled Subject transaction

Status: **OPEN**

Need explicit composition with Core `QUIESCING`: wait, timeout/infrastructure failure, and evidence requirements must be unambiguous without inventing a database lifecycle.

### RS-BR-006 — Schema drift detection boundary

Status: **OPEN**

Need specify what constitutes drift for the portable logical Manifest while avoiding raw backend catalog equality as the protocol rule.

### RS-BR-007 — Cross-backend canonical parity fixture

Status: **OPEN**

Need a concrete PostgreSQL/MySQL-neutral fixture covering all mandatory scalar types and concurrency behavior.

### RS-BR-008 — TCK execution interface

Status: **OPEN**

Need define a language-neutral relational TCK operation contract sufficient to execute projection/reset/snapshot/restore/diff without standardizing a general SQL client API.

## 15. Gate conclusion

**AEP-0010 DRAFT IS JUSTIFIED.**

**RS-BR-001 / RS-BR-002 ARE CLOSED.**

**RS-BR-003 .. RS-BR-008 REMAIN OPEN.**

**NOT READY FOR PROPOSED.**

**NOT READY FOR RELATIONAL NORMATIVE SPECIFICATION.**

**NOT READY FOR POSTGRESQL OR MYSQL ADAPTER IMPLEMENTATION.**

The next governed work is RS-BR-003 / RS-BR-004: authoritative projection structure and portable row identity, followed by the lifecycle/schema/TCK blockers.
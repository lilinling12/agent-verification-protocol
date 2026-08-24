# Alpha 3 Relational State Profile Design Audit

Status: **DRAFT DESIGN — NOT READY FOR PROPOSED**

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

No database adapter is authorized by this audit.

## 2. Existing authority reused

Relational State specializes rather than replaces existing contracts:

- Environment owns authoritative resources, Scenario binding, projection identity, SnapshotRef ownership, restore fidelity, semantic diff, and stale-handle failure.
- Fabric owns Resource identity, required/optional participation, Resource Capability negotiation, composite-result honesty, and cleanup composition.
- Security owns Subject/Evaluator/control authority separation and `SecurityAssurance`.
- Evidence/Artifact owns exact retained-byte identity.
- Core owns `QUIESCING`, Validity, infrastructure failure, and Task Verdict separation.

No relational design decision may create a competing version of those concepts.

## 3. Current portable direction

### Capability

One cohesive initial capability:

```text
capabilityId: state.relational
profile: avp-relational-state-v0.1
revision: "0.1"
```

No temporary `supports_*` capability family is planned.

### Identity resources

The base Fabric `EnvironmentResource` remains closed.

Relational profile identity is carried by exact-byte Artifacts:

- one `RelationalStateManifest`;
- one baseline `RelationalStateImage`.

They are bound through the existing `EnvironmentResource.identityArtifacts` collection and distinguished by profile-defined media type, not array position.

The Manifest never points back to the baseline StateImage. The baseline image contains the Manifest Artifact digest, producing an acyclic content-addressed graph.

Runtime snapshot StateImages are generated Evidence bound by the existing Environment/resource-owned SnapshotRef and do not mutate immutable Fabric identity inputs.

### Canonical state

Canonical relational structures use RFC 8785 JCS exact bytes. Relational high-precision numerics are typed strings rather than JSON number tokens. The initial scalar set is closed and deliberately limited to lossless PostgreSQL/MySQL-interoperable semantics.

Full-state and named-projection digests are SHA-256 over exact canonical bytes. When the same bytes are retained as AVP Artifacts, the existing Artifact digest is reused rather than inventing a separate relational hash scheme.

### Authoritative surface

One Manifest defines one closed authoritative relational surface. Every listed relation/column participates in logical state equivalence; backend state outside that Manifest is outside the v0.1 claim.

A `RelationalStateImage` always covers the complete surface.

Named projections are immutable Manifest-defined relation/column subsets and include all rows of each selected relation. v0.1 has no portable SQL text, predicates, joins, derived expressions, aggregates, limits, or backend-view semantics.

### Row identity

Every relation has a profile-owned logical row key made from one or more Manifest columns. Key columns are non-null and unique over AVP canonical typed values. Backend primary/unique constraints are implementation evidence, not protocol identity.

Row-key declaration order is canonicalized by logical column identifier; backend index order is irrelevant. Rows are ordered by canonical JCS row-key bytes, not database collation or physical order.

Changing a logical row key is represented as delete-old + insert-new in semantic diff.

### Observation and restore

Evaluator projection must correspond to one committed logical view and never expose uncommitted Subject state. Multi-relation projections may not be torn across incompatible visibility points.

Reset success requires post-reset full-state verification against the bound baseline StateImage.

Base relational restore is logical only and may claim at most `STATE_EQUIVALENT`; `EXACT` is excluded because sequence/auto-increment continuation, MVCC/session/lock/cache state, and physical storage identity are not standardized.

## 4. Design-decision evidence

### Canonical value / Artifact model

`docs/design/alpha3-relational-state-canonical-model.md`

Owns the Draft decisions for:

- RFC 8785 JCS exact-byte serialization;
- typed scalar representation;
- integer/decimal limits and lexical form;
- text/binary/date/time/timestamp/UUID canonical form;
- Manifest/StateImage media-type roles;
- acyclic identity binding;
- baseline versus runtime snapshot ownership.

### Surface / row identity model

`docs/design/alpha3-relational-state-surface-and-row-identity.md`

Owns the Draft decisions for:

- closed authoritative surface;
- full-state versus named projections;
- no portable SQL query language;
- logical identifiers;
- portable row keys;
- canonical row order;
- key mutation/diff semantics.

## 5. PostgreSQL and MySQL remain implementation evidence

PostgreSQL and MySQL/InnoDB have different transaction visibility, snapshot, DDL, identity-generator, and storage behavior. Candidate mechanisms such as PostgreSQL Repeatable Read/exported snapshots or MySQL InnoDB consistent reads may satisfy portable requirements, but their commands/tokens/defaults are not AVP semantics.

Server defaults are never sufficient conformance evidence. The eventual TCK tests observable committed-view, reset, restore, diff, ownership, and security properties.

## 6. Draft -> Proposed blocker ledger

AEP-0010 remains Draft until every blocker is closed and a separate Proposed-readiness audit confirms that the AEP text itself incorporates the decisions without contradiction.

### RS-BR-001 — Scalar lexical encoding

Status: **CLOSED FOR DRAFT -> PROPOSED READINESS**

Evidence: `docs/design/alpha3-relational-state-canonical-model.md`.

Resolved typed values, JCS bytes, exact integer/decimal lexical rules, text/binary/UUID rules, temporal precision and ranges, and fail-closed unsupported/lossy mappings.

### RS-BR-002 — Manifest versus StateImage identity

Status: **CLOSED FOR DRAFT -> PROPOSED READINESS**

Evidence: `docs/design/alpha3-relational-state-canonical-model.md`.

Resolved Manifest/StateImage Artifact roles, acyclic baseline identity, Fabric `identityArtifacts` binding, runtime SnapshotRef binding, and reuse of existing Artifact SHA-256 identity.

### RS-BR-003 — Authoritative surface versus named projections

Status: **CLOSED FOR DRAFT -> PROPOSED READINESS**

Evidence: `docs/design/alpha3-relational-state-surface-and-row-identity.md`.

Resolved one closed full surface, all-row relation/column-subset named projections, mandatory key columns, Manifest-owned definition identity, and explicit exclusion of SQL/predicate/join/expression semantics from v0.1.

### RS-BR-004 — Row-key portability

Status: **CLOSED FOR DRAFT -> PROPOSED READINESS**

Evidence: `docs/design/alpha3-relational-state-surface-and-row-identity.md`.

Resolved logical key semantics independent of backend PK names/order, canonical uniqueness, no hidden physical fallback identity, canonical row ordering, and delete+insert semantics for key mutation.

### RS-BR-005 — Final observation under unsettled Subject transaction

Status: **OPEN**

Need exact composition with Core `QUIESCING`: accepted in-flight database work, bounded settlement, timeout/infrastructure failure, and evidence must be unambiguous without creating a second database lifecycle.

### RS-BR-006 — Schema drift detection boundary

Status: **OPEN**

Need define which backend changes invalidate the logical Manifest binding and how conformance detects semantic drift without requiring raw system-catalog equality.

### RS-BR-007 — Cross-backend canonical parity fixture

Status: **OPEN**

Need a concrete database-neutral fixture covering every mandatory scalar form, composite row identity, projection canonicalization, reset/restore, and concurrency observation behavior.

### RS-BR-008 — Language-neutral TCK execution interface

Status: **OPEN**

Need define the minimum resource operations the TCK requires for provision/project/mutate/snapshot/restore/reset/diff/release without standardizing a general SQL client API or backend-specific branches.

## 7. Gate conclusion

Current state:

```text
AEP-0010: Draft
RS-BR-001: CLOSED
RS-BR-002: CLOSED
RS-BR-003: CLOSED
RS-BR-004: CLOSED
RS-BR-005: OPEN
RS-BR-006: OPEN
RS-BR-007: OPEN
RS-BR-008: OPEN
```

Therefore:

**DRAFT DIRECTION REMAINS JUSTIFIED.**

**NOT READY FOR PROPOSED.**

**NOT READY FOR RELATIONAL NORMATIVE SPECIFICATION.**

**NOT READY FOR POSTGRESQL OR MYSQL ADAPTER IMPLEMENTATION.**

The next governed work is RS-BR-005 and RS-BR-006: lifecycle-consistent final observation and portable schema-drift detection. Only after those are closed should the design freeze the cross-backend fixture and language-neutral TCK operation contract.
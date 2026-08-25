# Alpha 3 Relational State Surface and Row Identity

Status: **DRAFT DESIGN DECISION — RS-BR-003 / RS-BR-004 CLOSED FOR PROPOSED-READINESS PURPOSES**

Proposal: AEP-0010 (Draft)
Parent: AEP-0009 (Accepted)

This document is non-normative design evidence. It fixes the authoritative-surface, named-projection, and portable row-identity direction that AEP-0010 must absorb before `Proposed` review.

## 1. Decision summary

Relational State v0.1 will use:

1. one closed authoritative relational surface per `state.relational` resource;
2. one full-state representation covering that complete surface;
3. named projections that are **static relation/column selections only**;
4. no SQL predicates, joins, expressions, aggregates, grouping, backend views, procedures, or query text in the portable projection model;
5. all rows of each relation selected by a named projection;
6. mandatory logical row-key columns in every projection that selects that relation;
7. profile-owned logical row identity independent of database primary-key names and index definitions;
8. row-key column identifiers canonicalized as an unordered semantic set, serialized in profile-defined lexical order rather than backend constraint order;
9. row values ordered by canonical row-key bytes rather than database collation or physical order;
10. row-key mutation represented as delete-old-key plus insert-new-key in semantic diff.

These constraints are intentionally narrow. They make the initial profile independently implementable and testable without inventing a portable SQL expression language.

## 2. Portable identifiers

The v0.1 design uses lower-case ASCII logical identifiers so ordering and comparison do not depend on locale, Unicode normalization, or backend identifier folding.

Candidate identifier syntax:

```text
relationId   = ^[a-z][a-z0-9._-]{0,63}$
columnId     = ^[a-z][a-z0-9._-]{0,63}$
projectionId = ^[a-z][a-z0-9._-]{0,127}$
```

Logical identifiers are case-sensitive exact protocol strings, but the lower-case grammar removes case aliases from the canonical domain.

They are not backend table/column/view names. An adapter owns the binding from these logical identifiers to backend objects.

The eventual normative schema may tighten maximum lengths if conformance evidence requires it, but it must not broaden v0.1 into arbitrary backend identifiers without protocol review.

## 3. Authoritative relational surface

`RelationalStateManifest` defines exactly one authoritative surface.

The authoritative surface is the complete set of logical relations and columns whose values participate in v0.1 relational state equivalence, reset verification, logical snapshot/restore, and full-state semantic diff.

Rules:

- every relation listed in the Manifest is authoritative;
- every logical column listed for that relation is authoritative;
- there is no `authoritative: false` escape hatch inside the v0.1 relation definition;
- backend tables/columns not represented by the Manifest are outside the v0.1 logical equivalence claim;
- an adapter MUST NOT silently omit a Manifest relation/column because the backend cannot read or normalize it;
- if a selected relation/column becomes unavailable or incompatible, the resource binding fails closed.

This makes the boundary positive and closed: the Manifest states what **is** authoritative rather than requiring a growing exclusion list.

## 4. Full-state image

`RelationalStateImage` always represents the complete authoritative surface from the bound Manifest.

It is not parameterized by a named projection.

Canonical relation serialization order is ascending `relationId` by ASCII/UTF-8 byte value. Canonical column serialization order is ascending `columnId` by ASCII/UTF-8 byte value.

This order is profile-owned. Manifest authoring order and backend ordinal positions have no semantic effect.

Every selected row is present exactly once and rows are ordered by canonical row-key bytes as defined below.

Therefore two implementations that bind the same Manifest and logical state cannot produce different full-state bytes merely because table creation order, database column ordinal, query plan, or backend collation differs.

## 5. Named projections

A named projection is an immutable definition inside the Manifest.

A v0.1 named projection may only select:

- one or more relations from the authoritative surface; and
- one or more columns from each selected relation.

For every selected relation it observes **all rows** in that relation at the same committed observation boundary.

A named projection MUST NOT contain portable forms of:

- SQL text;
- `WHERE`/predicate expressions;
- joins;
- computed/derived columns;
- aggregates;
- grouping/windowing;
- server-side view names as semantics;
- order-by expressions;
- limits/offsets;
- stored procedures/functions;
- backend query hints.

Those features can exist in a Scenario's application/database behavior, but the base relational profile does not standardize them as evaluator projection semantics.

If a future AVP use case requires portable filtered or derived projections, it needs a separately reviewed projection-expression model or profile revision.

## 6. Projection subset rule

Every named projection is a structural subset of the authoritative surface.

It cannot introduce a relation or column absent from the Manifest's full surface.

For each selected relation, the projection MUST include every column that participates in that relation's logical row key. This ensures:

- deterministic row ordering;
- stable row identity;
- semantic diff applicability;
- no separate hidden row locator;
- projection results remain independently auditable.

A projection may select additional non-key columns in any semantic combination allowed by the Manifest; canonical output still serializes selected columns in ascending logical `columnId` order.

An empty projection or a selected relation with no columns is invalid.

## 7. Projection definition identity

Projection definitions are part of exact `RelationalStateManifest` bytes and therefore covered by the Manifest Artifact digest.

A canonical `RelationalProjection` output binds:

- `manifestDigest`;
- `projectionId`;
- canonical selected relation/column/row content.

The portable output does not repeat SQL or a second projection AST.

Because `manifestDigest` and `projectionId` are in the canonical projection preimage, changing a projection definition requires a new Manifest identity and cannot be silently interpreted under the previous binding.

Two different projection identifiers that happen to select equal content remain distinct projection identities, consistent with Environment's `(projection identifier, state digest)` identity rule.

## 8. Logical row key

Every authoritative relation declares a non-empty **logical row key** consisting of one or more logical column identifiers from that relation.

The semantic set of key columns is independent of:

- database primary-key constraint name;
- unique-index name;
- backend index column order;
- physical tuple/row identifier;
- clustered storage order;
- auto-increment/sequence generator state.

The Manifest canonical form serializes row-key column identifiers in ascending logical `columnId` order. Authors do not control a second arbitrary key ordering dimension.

Therefore logically equivalent row-key declarations have one canonical representation.

## 9. Row-key value requirements

For every projected row:

- every key column MUST be present;
- every key value MUST be non-null;
- each key value MUST satisfy the closed scalar canonicalization rules;
- the tuple/map of key column values MUST be unique among rows in the relation at that observation boundary.

Uniqueness is defined over canonical AVP typed values, not over a vendor collation comparison.

An adapter may rely on a backend primary key/unique constraint when it establishes the same property, but the protocol does not require a particular constraint type. An adapter may also verify uniqueness during compatibility/projection if its deployment establishes the property another way.

If duplicate canonical logical keys are observed, projection/snapshot/reset verification fails closed. The adapter MUST NOT choose one row, append an ordinal, use a physical row id, or hash the whole row to manufacture uniqueness.

## 10. Canonical row-key bytes

A canonical row key is represented as a JSON object whose member names are the logical key `columnId` values and whose values are the canonical typed relational value records.

Example:

```json
{
  "order_id": {"type":"uuid","value":"550e8400-e29b-41d4-a716-446655440000"},
  "tenant_id": {"type":"integer","value":"42"}
}
```

RFC 8785 JCS serialization provides one exact byte representation. Because logical identifiers are lower-case ASCII, property ordering is unambiguous across implementations.

Rows are ordered by unsigned lexicographic comparison of their canonical row-key UTF-8/JCS byte sequences.

This ordering is an AVP serialization rule only; it makes no claim about business ordering or database sort semantics.

## 11. Canonical row representation

A canonical row contains:

- `key` — the canonical row-key object; and
- `values` — a JSON object containing every column selected by the full state/projection, keyed by logical `columnId` and encoded as typed values.

Key columns appear in `values` as well as `key`. This deliberate redundancy makes the relation content self-checking: the values for each key column MUST be byte/semantic-equal in both locations.

Alternative designs that omit key columns from `values` create special-case column reconstruction rules and make generic consumers more complex.

JCS canonicalizes the row object and nested value objects. Array order is established by the relational profile before JCS.

## 12. Database primary keys are implementation evidence

A backend primary key is a strong candidate binding for a logical row key but is neither necessary nor sufficient by name alone.

Examples:

- PostgreSQL table PK `(tenant_id, order_id)` may back logical key `{order_id, tenant_id}`; backend key order does not change AVP identity.
- MySQL unique index may back the same logical key when its equality semantics guarantee the required unique state.
- a case-insensitive text unique index may be stricter than AVP exact-text identity and therefore reject some logically distinct AVP key values; this is allowed as an implementation limitation only if the selected fixture/state remains representable.
- a backend uniqueness rule that permits two rows which canonicalize to the same AVP key is insufficient; the adapter must prevent or fail on that state.

Conformance tests behavior, not catalog labels.

## 13. Generated identifiers

A stored generated identifier may participate in the logical row key if its stored value is part of the authoritative surface and satisfies the portable scalar rules.

Examples include auto-increment or sequence-generated integer columns.

However generator continuation state remains outside v0.1 logical state equivalence. After a `STATE_EQUIVALENT` restore, the stored row key values must match the snapshot, but the next value produced by a backend sequence/auto-increment mechanism is not claimed to be exact unless a future capability standardizes it.

This preserves the existing decision that base relational restore cannot claim `EXACT`.

## 14. Key mutation and semantic diff

Logical row identity is state-relative.

If one or more logical key column values change between before/after states, v0.1 semantic diff represents this as:

```text
DELETE old-row-key + INSERT new-row-key
```

not an `UPDATE` that changes identity.

An `UPDATE` diff applies only when the canonical row key is unchanged and one or more non-key selected values differ.

This rule is independent of whether a backend physically implemented the change as one SQL `UPDATE`, a delete/insert pair, a trigger, or another mechanism.

## 15. Projection and diff relationship

Semantic diff is always scoped to one bound Manifest and either:

- the full authoritative surface; or
- one named projection from that Manifest.

Before/after inputs must have the same `manifestDigest` and projection identity. Cross-Manifest diff is not a v0.1 semantic diff; schema drift must be surfaced separately rather than disguised as row changes.

For each selected relation:

- key only in `after` => inserted;
- key only in `before` => deleted;
- key in both with equal selected canonical values => unchanged;
- key in both with differing non-key selected values => updated.

Diff output ordering follows relation id and canonical row-key byte order, not backend operation order.

## 16. No hidden evaluator query language

The reference runtime may use SQL internally to extract selected relations/columns, but the public profile/TCK interface should request projections by `projectionId`, not pass arbitrary SQL.

This is a critical authority boundary:

```text
portable TCK: project(projectionId)
backend adapter: chooses safe engine-specific extraction
```

not:

```text
portable TCK: execute("SELECT ...")
```

The latter would turn SQL dialect and query semantics into accidental protocol surface.

## 17. RS-BR-003 closure evidence

RS-BR-003 asked whether named projections are restricted subsets/views of one full authoritative surface and how definitions participate in identity.

Closure decision:

- one closed full authoritative surface per resource;
- named projections are immutable Manifest-defined structural relation/column subsets;
- all rows of each selected relation participate;
- key columns are mandatory;
- no predicates/joins/expressions/aggregates/query language in v0.1;
- projection definition identity is inherited from the Manifest Artifact digest plus `projectionId`;
- canonical projection output binds both;
- full-state image is distinct from named projections and always covers the complete surface.

**RS-BR-003: CLOSED FOR DRAFT -> PROPOSED READINESS.**

## 18. RS-BR-004 closure evidence

RS-BR-004 asked whether mandatory row identity can be portable without requiring backend primary-key syntax.

Closure decision:

- every relation has a non-empty logical key set of Manifest column ids;
- key declaration canonicalized independently of backend index/constraint ordering;
- key values non-null and canonical;
- uniqueness defined over AVP canonical typed values;
- duplicate keys fail closed;
- backend PK/unique constraints are implementation evidence, not protocol identity;
- no hidden physical/generated fallback key;
- canonical row ordering uses JCS row-key bytes;
- key mutation is delete+insert for semantic diff;
- generated stored IDs may be keys while generator continuation remains outside `STATE_EQUIVALENT`.

**RS-BR-004: CLOSED FOR DRAFT -> PROPOSED READINESS.**

## 19. Remaining Draft blockers

Still open:

- RS-BR-005 — final observation under unsettled Subject transaction;
- RS-BR-006 — schema drift detection boundary;
- RS-BR-007 — cross-backend canonical parity fixture;
- RS-BR-008 — language-neutral TCK execution interface.

AEP-0010 remains Draft and is not ready for normative specification or database adapter implementation.
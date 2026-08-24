# AVP Relational State Resource Contract v0.1

Status: draft normative candidate

## 1. Scope

This specification defines the portable `state.relational` Environment Fabric Resource Capability selected as:

```text
capabilityId: state.relational
profile: avp-relational-state-v0.1
revision: "0.1"
```

It specializes the existing AVP Environment and Environment Fabric contracts. It does not define a database wire protocol, SQL dialect, ORM, transaction API, backend product profile, second Episode lifecycle, second Artifact identity system, or second security model.

A conforming implementation MUST satisfy all applicable Environment, Fabric, Scenario, Core, Security, and Evidence requirements selected for the Episode.

Normative keywords MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are interpreted as conformance requirement terms.

## 2. Portable model

One Relational State Resource represents one logical relational state boundary within one owning Environment.

The resource has two required relational state-identity Artifacts:

1. one immutable `RelationalStateManifest`;
2. one immutable baseline `RelationalStateImage`.

The Manifest defines portable logical state interpretation. It is not the complete Environment execution identity. Database programs or configuration outside the Manifest that materially affect Scenario execution compose through existing Scenario/Fabric execution-input identity binding.

The canonical serialized Relational State resources use RFC 8785 JSON Canonicalization Scheme (JCS) exact UTF-8 bytes. Artifact identity remains SHA-256 over exact retained bytes under the AVP Evidence contract.

## 3. Profile and identity

<a id="avp-relational-001"></a>
### AVP-RELATIONAL-001 — Resource profile and identity Artifact binding

A resource claiming `state.relational @ avp-relational-state-v0.1 / 0.1` MUST be a Fabric `resourceKind: state` resource and MUST bind exactly one RelationalStateManifest Artifact and exactly one baseline RelationalStateImage Artifact as the relational state-identity material required by this profile. Their roles MUST be determined by profile-defined media type rather than array position. The Manifest MUST NOT reference the baseline StateImage ArtifactRef. The baseline StateImage MUST bind the exact Manifest Artifact digest, preventing a content-address identity cycle.

Backend names, driver classes, SQL dialects, transaction tokens, dump files, database process identifiers, filesystem paths, or image labels MUST NOT substitute for these portable state identities.

<a id="avp-relational-002"></a>
### AVP-RELATIONAL-002 — Immutable logical Manifest semantics

RelationalStateManifest MUST bind the selected profile/revision, logical relation identifiers, logical column identifiers, column scalar definitions and parameters, nullability, a non-empty logical row-key set for every authoritative relation, the complete authoritative relation/column surface, named projection definitions, and canonical representation version. Those Manifest semantics MUST remain immutable for the bound resource lifetime.

Logical identifiers MUST use the profile's restricted portable identifier vocabulary. Backend table/column names and other physical bindings MAY differ and are not portable identity unless another selected contract separately binds them.

## 4. Canonical values and rows

<a id="avp-relational-003"></a>
### AVP-RELATIONAL-003 — Closed canonical scalar model

Every authoritative relational value MUST be represented as a typed value whose declared type matches the Manifest column definition. v0.1 supports only:

- `boolean`;
- `integer` — signed exact integer with at most 65 decimal digits, canonical decimal string, no plus sign, exponent, decimal point, leading zero, or negative zero;
- `decimal` — precision 1..65, scale 0..30, scale not greater than precision, canonical fixed-point string with exactly the declared scale and normalized positive zero;
- `text` — exact Unicode scalar sequence with no AVP Unicode normalization;
- `binary` — RFC 4648 base64url, canonical unpadded form;
- `date` — Gregorian `YYYY-MM-DD`, year 1000..9999;
- `time-local` — time-of-day only, precision 0..6, no timezone, elapsed-time form, leap second, or 24:00:00;
- `timestamp-local` — local date-time, year 1000..9999, precision 0..6, no timezone semantics;
- `timestamp-instant` — UTC-normalized date-time ending in `Z`, precision 0..6, no leap second;
- `uuid` — lowercase RFC 9562 8-4-4-4-12 form.

Null is permitted only when the Manifest column is nullable. Adapters MUST NOT round, truncate, normalize text, reinterpret collation equality, or silently coerce unsupported backend values into the portable model.

Approximate float, database-native JSON/XML/spatial/array/interval/vendor enum-set, and opaque extension values are outside mandatory v0.1 and MUST fail compatibility when selected into the authoritative surface.

<a id="avp-relational-004"></a>
### AVP-RELATIONAL-004 — Logical row identity and canonical ordering

Every authoritative relation MUST declare a non-empty logical row-key set. At every accepted observation boundary, all key values MUST be present, non-null, canonical, and unique over AVP typed-value semantics.

The canonical row key is a JSON object keyed by logical key column id and containing canonical typed values. Row-key column declarations are ordered by ascending logical column id before canonicalization. A backend primary key, index identity/order, physical tuple id, row ordinal, collation, or whole-row hash MUST NOT replace logical row identity.

Canonical serialized relation order is ascending `relationId`; column order is ascending `columnId`; row order is unsigned lexicographic order of canonical JCS row-key bytes. A logical key change is a delete of the old row identity plus insert of the new row identity for diff semantics.

## 5. State images and projections

<a id="avp-relational-005"></a>
### AVP-RELATIONAL-005 — Full StateImage identity

A RelationalStateImage MUST bind the exact Manifest Artifact digest and MUST contain every authoritative relation, every authoritative column, and every authoritative row exactly once using canonical typed values and ordering. It MUST NOT contain its own digest.

SHA-256 over the exact JCS StateImage bytes is both the retained Artifact digest, when retained, and the v0.1 full authoritative relational state digest. A StateImage with a different Manifest digest, duplicate logical key, missing authoritative content, unsupported value, or non-canonical value MUST fail closed.

Evaluator-private authoritative data MAY be part of the complete StateImage. Completeness and Subject visibility are separate concerns governed by AVP Security/Evidence rules.

<a id="avp-relational-006"></a>
### AVP-RELATIONAL-006 — Named evaluator projection semantics

Each named projection MUST be an immutable Manifest-owned structural subset selecting one or more authoritative relations and one or more columns from each selected relation. It MUST include all rows of every selected relation and MUST include every logical key column required to identify selected rows.

v0.1 projections MUST NOT define portable SQL text, row predicates, joins, computed expressions, aggregates, windows, limits, offsets, backend view/procedure/function identity, or backend ordering semantics.

Canonical projection bytes MUST bind the Manifest digest, projection identifier, selected relations/columns, canonical rows, and canonical typed values. Environment projection identity remains `(projection identifier, state digest)`.

<a id="avp-relational-007"></a>
### AVP-RELATIONAL-007 — One committed observation boundary

Every accepted evaluator projection or full-state observation MUST correspond to one committed logical view. It MUST NOT expose uncommitted Subject state. A multi-relation observation MAY represent the complete state before or after a concurrent commit but MUST NOT combine incompatible visibility points into a torn result.

A backend-specific MVCC snapshot, synchronized snapshot, transaction mode, quiescence mechanism, or equivalent implementation technique MAY be used only as evidence for this portable observable property and MUST NOT become AVP projection identity.

## 6. Lifecycle and binding integrity

<a id="avp-relational-008"></a>
### AVP-RELATIONAL-008 — Core QUIESCING settlement

Relational State defines no second lifecycle. After Core enters `QUIESCING`, the implementation MUST reject new Subject-requested relational mutations before their database side effects. Work accepted before the transition MAY settle.

Final relational verification MUST wait for a Subject mutation settlement barrier in which every relevant accepted mutation has a known committed, rolled-back/cancelled, or otherwise non-mutating terminal outcome and new mutation admission remains closed.

The implementation MUST NOT auto-commit Subject work, expose dirty state, or treat an executed SQL statement as committed merely because execution occurred. If the settlement barrier cannot be established under the bound execution policy, no accepted final relational projection is produced and the condition remains infrastructure/Validity information rather than direct Agent Task Verdict failure.

<a id="avp-relational-009"></a>
### AVP-RELATIONAL-009 — Logical schema/binding drift fails closed

The resource binding MUST continue to satisfy the immutable Manifest at every relevant observation and state-mutating Control boundary. Drift includes selected relation/column disappearance or ambiguity, lossy/unsupported scalar mapping, unavailable logical key columns, logical-id redirection to different backend state under unchanged Manifest identity, or concurrent selected-schema change that prevents one consistent Manifest-bound observation.

Unselected relations/columns, irrelevant index/catalog metadata, optimizer statistics, and physical changes that preserve the selected portable binding are not automatically relational-state drift. Raw catalog or DDL equality MUST NOT be required as portable state identity.

<a id="avp-relational-010"></a>
### AVP-RELATIONAL-010 — Execution-relevant database input identity

RelationalStateManifest MUST NOT be interpreted as complete Environment execution identity. Any database program, configuration, extension, trigger, default, generated expression, constraint behavior, routine, SQL mode, timezone/session semantic setting, schema-program revision, or other database input outside the Manifest that materially affects selected Scenario execution MUST be bound to profile-appropriate resolved immutable identity through the existing Scenario/Fabric execution-input identity mechanism.

If a required execution-relevant identity cannot be established before execution, materialization/provisioning MUST fail closed. If a bound execution-relevant identity drifts during the Episode, the existing execution binding becomes invalid even when canonical rows and logical Manifest binding still match. Product names, server-default labels, process ids, or mutable catalog fingerprints MUST NOT substitute for required immutable execution-input identity.

## 7. Snapshot, reset, and restore

<a id="avp-relational-011"></a>
### AVP-RELATIONAL-011 — Logical snapshot evidence and ownership

A successful relational snapshot MUST establish one committed consistent full-state observation, produce exact canonical RelationalStateImage bytes, retain or otherwise bind those bytes through existing Artifact identity, and bind that StateImage identity to an Environment/resource-owned SnapshotRef.

Foreign or stale SnapshotRef use MUST fail closed under Environment ownership semantics. Backend transaction/read-view tokens, dumps, WAL/binlog positions, physical snapshot paths, or engine backup handles are implementation-private and MUST NOT replace SnapshotRef or StateImage identity.

<a id="avp-relational-012"></a>
### AVP-RELATIONAL-012 — Reset is verified state re-establishment

Reset success MUST be accepted only after required logical/execution bindings are valid, the complete authoritative relational surface is independently re-projected, and the resulting canonical StateImage identity exactly equals the resource's bound baseline StateImage identity under the same Manifest.

Backend reset/truncate/restore command success alone is insufficient. Reset mismatch or inability to establish trustworthy state is infrastructure/Validity information and MUST NOT be converted directly into Agent Task Verdict failure solely by occurrence.

<a id="avp-relational-013"></a>
### AVP-RELATIONAL-013 — Successful restore fidelity is exactly STATE_EQUIVALENT

Restore of an owner-valid relational SnapshotRef MUST independently re-project the complete authoritative relational surface and compare it with the snapshot StateImage under the same Manifest.

A successful v0.1 relational restore MUST have re-established the snapshot StateImage identity and MUST report resource restore fidelity exactly `STATE_EQUIVALENT`. If that identity is not re-established, restore MUST fail and MUST NOT report successful equivalence; fidelity is `NON_EQUIVALENT` or the equivalent failure representation of the selected operation schema.

`EXACT` MUST NOT be reported for this base capability because sequence/auto-increment continuation, MVCC/transaction/session/lock/cache state, physical storage identity, and other execution state are not standardized by v0.1.

## 8. Diff, security, and conformance

<a id="avp-relational-014"></a>
### AVP-RELATIONAL-014 — Semantic diff is logical-state bound

A relational diff MUST compare states bound to the same Manifest and either the full authoritative surface or the same named projection. For each relation and canonical logical key: after-only is insert; before-only is delete; same key with equal canonical non-key values is unchanged; same key with changed canonical non-key values is update; logical key change is delete-old plus insert-new.

Diff ordering MUST follow logical relation id and canonical row-key bytes rather than backend execution order or physical identity. Cross-Manifest comparison is binding/schema drift and MUST NOT be represented as an ordinary row diff.

<a id="avp-relational-015"></a>
### AVP-RELATIONAL-015 — Evaluator-private state and Subject visibility remain separated

Relational Manifest, Projection, StateImage, Diff, and snapshot Evidence MUST compose with existing AVP Security/Evidence classification, credential, and visibility rules. Evaluator-private authoritative relational data MAY exist in evaluator-confidential/secret/regulated Evidence when required by verification.

Subject-visible relational observations, tool results, routes, execution context, and Artifact locators MUST NOT disclose evaluator-private relational content or grant unauthorized retrieval authority unless the materialized Scenario explicitly makes that content observable. Artifact digest identity MUST NOT be treated as retrieval authorization. Subject-scoped/redacted bytes are distinct Artifacts and MUST NOT reuse the digest of unredacted evaluator-confidential bytes.

Evaluator/control credentials, database passwords, secret DSNs, signing secrets, control tokens, and equivalent privileged authority MUST NOT be embedded in portable relational state resources.

<a id="avp-relational-016"></a>
### AVP-RELATIONAL-016 — Executed backend-neutral conformance

Conformance for `state.relational @ avp-relational-state-v0.1 / 0.1` MUST execute an implementation path capable of observing whether the required relational behavior is actually satisfied. Manifest/capability metadata, backend name, fixture declaration, schema shape, or support flags alone MUST NOT establish conformance.

The mandatory TCK MUST be capable of rejecting metadata-identical broken implementations that produce a torn projection, falsely report restore success without re-establishing snapshot state, leak evaluator-private state through a Subject-visible surface, or silently accept drift of a bound execution-relevant database input.

Portable TCK cases MUST NOT branch on PostgreSQL, MySQL, or another backend product. Backend-specific SQL, DDL, transaction controls, and test setup MAY exist only behind implementation/test-driver seams and MUST NOT become portable Resource or Subject capabilities.

## 9. Schema and extension rules

Serialized v0.1 Relational State resources use closed JSON Schemas owned by this profile. Protocol-owned objects MUST reject unknown fields unless an explicit governed extension field is defined. v0.1 defines no generic untyped implementation-property bag.

Schema validation is necessary but not sufficient. Uniqueness, canonical ordering, digest verification, committed-view consistency, QUIESCING settlement, binding drift, execution-input identity, snapshot ownership, reset/restore verification, visibility, and executed-conformance behavior require semantic execution.

## 10. Implementation freedom

Conforming implementations MAY use PostgreSQL, MySQL/InnoDB, another relational engine, an in-memory model, managed database service, or another mechanism. Those choices remain implementation evidence. They MUST NOT redefine the portable semantics above.

# AEP-0010 Draft → Proposed Readiness Audit

Status: **READY FOR PROTOCOL REVIEW — PROPOSED ELIGIBLE**

AEP: `rfcs/AEP-0010-relational-state-resource-profile.md`
Parent: AEP-0009 (Accepted)
Audit date: 2026-08-24

## 1. Audit purpose

This audit determines whether AEP-0010 is sufficiently complete to move from `Draft` to `Proposed` under repository governance.

`Proposed` means the design is complete enough for formal protocol review. It does **not** make the AEP normative, does not authorize an Accepted decision, does not authorize a relational normative candidate surface, and does not authorize PostgreSQL/MySQL implementation.

## 2. Governance criteria

Repository governance requires a normative design decision to have, before acceptance:

1. written problem and scope;
2. alternatives and compatibility analysis;
3. security analysis;
4. conformance/test strategy;
5. a recorded maintainer decision for acceptance.

A Draft → Proposed transition requires the first four to be sufficiently complete for protocol review. The fifth is intentionally absent until a future explicit `Accepted` decision.

## 3. Problem and interoperability scope

**PASS**

AEP-0010 identifies the interoperability failure clearly:

- database mechanisms differ across PostgreSQL/MySQL;
- transaction/snapshot tokens cannot be protocol identity;
- raw driver values cannot be canonical state;
- raw DDL/catalogs cannot define portable logical schema identity;
- restoring rows cannot justify `EXACT` execution-state fidelity;
- a backend-first API would violate AEP-0009's authority direction.

The scope is bounded to one Fabric `state.relational` resource and one logical relational state boundary. Multiple independently managed databases remain separate Fabric resources, preserving base Fabric no-implicit-atomicity semantics.

The AEP also contains explicit non-goals and does not attempt to standardize SQL, an ORM, transaction commands, physical backup formats, cross-Environment snapshot import, a database migration protocol, or arbitrary vendor data types.

## 4. Parent-authority composition

**PASS**

The AEP explicitly reuses rather than duplicates:

- Environment ownership, Scenario binding, projection identity, SnapshotRef ownership, restore-fidelity vocabulary, semantic diff, and stale-handle semantics;
- Fabric resource identity, Resource Capability declarations, required/optional participation, Subject-Capability separation, composite-result honesty, and no implicit distributed transaction;
- Core lifecycle / QUIESCING / Validity / infrastructure / Task Verdict separation;
- Security trust planes and `SecurityAssurance`;
- Evidence/Artifact exact-byte SHA-256 identity.

No competing Episode lifecycle, isolation scale, Artifact identity algorithm, restore scale, or Task Verdict model is introduced.

## 5. Portable capability boundary

**PASS**

The proposed profile uses one cohesive capability identity:

```text
state.relational @ avp-relational-state-v0.1 / 0.1
```

The AEP explicitly rejects transitional `supports_*` flags and product-specific primary protocol profiles.

PostgreSQL/MySQL remain implementation evidence and reference targets. No vendor name, SQL command, server default, driver type, or transaction token is needed to interpret the portable capability.

## 6. Canonical value model

**PASS**

The AEP now gives a reviewable, closed v0.1 scalar boundary:

- boolean;
- integer up to 65 decimal digits;
- decimal precision 1..65 / scale 0..30;
- exact Unicode text;
- binary;
- date;
- time-local;
- timestamp-local;
- timestamp-instant;
- UUID.

Key interoperability decisions are explicit:

- RFC 8785 JCS exact JSON bytes;
- high-precision numerics encoded as canonical strings, avoiding JSON-number/IEEE-754 authority;
- no implicit Unicode normalization;
- base64url canonical binary form;
- 0..6 temporal fractional precision;
- UTC canonicalization for instants;
- unsupported/lossy values fail closed rather than entering an extension bag.

Exact JSON Schema spelling remains downstream normative-spec work; semantic ambiguity no longer depends on backend implementation.

## 7. Artifact and state identity model

**PASS**

The reconciled AEP removes the original potential content-address cycle.

Current direction:

```text
EnvironmentResource.identityArtifacts
  -> RelationalStateManifest ArtifactRef
  -> baseline RelationalStateImage ArtifactRef
       -> manifestDigest
```

The Manifest does not point to the baseline image.

Runtime snapshot StateImages are generated Evidence bound through existing Environment/resource-owned SnapshotRef and do not mutate immutable Fabric identity inputs.

Full StateImage digest and retained Artifact digest reuse the same SHA-256 over exact canonical bytes; no competing relational hash scheme exists.

Named projection digest likewise derives from exact canonical projection bytes, while Environment identity remains `(projection identifier, state digest)`.

## 8. Authoritative surface and row identity

**PASS**

The AEP defines one closed full authoritative surface and separates it cleanly from named projections.

Named projections are static relation/column subsets over all rows. v0.1 explicitly excludes SQL predicates, joins, computed expressions, aggregates, backend views, ordering expressions, and query text.

Every relation has a logical row key whose identity is independent of backend PK/unique-index names or ordering. Canonical key values are non-null and unique over AVP typed values; duplicate keys fail closed.

Row ordering is protocol-owned canonical key-byte ordering rather than backend collation/physical order. Key mutation is delete+insert for semantic diff.

This is sufficient to design independent schemas/TCK without inventing backend-specific row locators later.

## 9. Observation and lifecycle semantics

**PASS**

The AEP defines a committed-view property rather than a transaction-command contract:

- no uncommitted Subject state in accepted evaluator projection;
- one multi-relation observation boundary;
- fully pre-commit or fully post-commit is acceptable under concurrency;
- torn mixed visibility is not;
- Core QUIESCING closes new Subject mutation admission;
- already accepted activity may settle;
- final projection requires a settlement barrier;
- no auto-commit and no dirty-read escape hatch;
- unresolved settlement under the bound policy prevents accepted final verification and composes with existing infrastructure/Validity semantics.

No relational lifecycle state machine is introduced.

## 10. Schema-drift semantics

**PASS**

Drift is now portable logical-binding failure, not raw catalog equality.

The AEP distinguishes selected binding changes that invalidate the Manifest from backend changes outside the selected state surface that do not automatically alter portable semantics.

It also states operation-boundary checks for projection/snapshot/reset/restore and requires concurrent selected-schema DDL to be excluded or fail closed when one immutable binding cannot be proven.

Database catalog fingerprints remain implementation diagnostics/evidence, not protocol identity.

## 11. Reset / snapshot / restore honesty

**PASS**

- snapshot creates/binds canonical full StateImage evidence rather than a vendor transaction token;
- reset is successful only after post-reset full-state equality with baseline;
- restore is successful only after re-projection establishes the snapshot StateImage identity;
- v0.1 relational restore may claim at most `STATE_EQUIVALENT`;
- `EXACT` is explicitly excluded because continuation/execution state is outside the base profile.

This composes cleanly with Environment/Fabric fidelity semantics without inflation.

## 12. Security analysis

**PASS**

The AEP explicitly separates:

```text
Subject data authority
Evaluator projection authority
Control provision/reset/restore authority
```

It forbids evaluator/control credentials and secret DSNs in Subject contexts or portable state artifacts, rejects generic database-admin access as a Subject capability, preserves `SecurityAssurance`, and recognizes that deployments unable to close Subject mutation admission at QUIESCING cannot claim final-verification conformance.

The design does not equate container/VM/managed-database/product names with security proof.

## 13. Failure and Validity model

**PASS**

The AEP identifies portable infrastructure/Validity failures including unavailable resources, identity mismatch, logical binding drift, lossy values, duplicate keys, inconsistent observation, unsettled Subject activity, reset/restore mismatch, stale references, and lost privileged authority.

Vendor errors remain evaluator diagnostics.

None of these conditions is directly converted into Agent Task Verdict failure solely by occurrence.

## 14. Conformance strategy

**PASS**

The proposed TCK boundary is executable and backend-neutral.

It separates:

- system-under-test relational profile operations; and
- privileged fixture controls used to establish concurrency/drift/negative preconditions.

The portable profile does not require a general SQL/query/transaction/DDL/catalog API.

Mandatory behavior families cover identity, canonicalization, projections, committed-view consistency, QUIESCING, drift, reset, snapshot/restore, diff, Security, and execution-sensitive capability honesty.

The AEP requires metadata-identical broken controls such as a torn-projection implementation and false-restore implementation, proving conformance cannot pass from declarations alone.

Portable case vectors must not branch on PostgreSQL/MySQL.

## 15. Cross-backend portability evidence strategy

**PASS**

The AEP defines a concrete reference parity gate without making two engines a third-party protocol requirement.

The shared fixture covers:

- all mandatory scalar classes;
- 65-digit integer / high-precision decimal;
- Unicode normalization-distinct text;
- binary;
- temporal precision 0/3/6;
- UUID / NULL;
- composite logical keys with backend key-order differences;
- full/subset named projections;
- two-relation atomic epoch change for non-torn observation;
- reset / snapshot / restore / diff;
- QUIESCING and drift controls.

Exact canonical equality is required where deterministic equality is meaningful. Concurrent scheduling is evaluated by the common invariant (fully before or after commit) rather than falsely requiring both engines to choose the same timing side.

## 16. Alternatives

**PASS**

The AEP explicitly evaluates and rejects:

- separate PostgreSQL/MySQL primary protocol profiles;
- universal SQL/transaction API;
- raw dumps as portable snapshots;
- raw DDL/catalog hashing;
- direct driver-row hashing;
- JSON numbers for high-precision relational numerics;
- generic extension/value bags;
- backend PK identity;
- query-language projections;
- auto-commit during QUIESCING;
- `EXACT` restore based on rows alone;
- PostgreSQL-first implementation/generalization.

The reasons are tied to interoperability, authority, or fidelity rather than implementation preference.

## 17. Backward compatibility and release boundary

**PASS**

AEP-0010 is additive:

- existing Environment implementations need not claim the profile;
- existing Fabric resources remain valid without `state.relational`;
- existing Environment/Fabric/Core/Security/Evidence semantics are reused;
- no public release is selected;
- the planned `0.3.1` maintenance identity is not assigned Alpha 3 semantics.

## 18. Transitional-implementation audit

**PASS**

No design requires:

- PostgreSQL-first public classes generalized later;
- temporary compatibility shims;
- generic public property bags;
- backend-name TCK branches;
- static support metadata as conformance proof;
- raw vendor snapshot tokens as protocol identity.

The common implementation interface remains downstream of the accepted specification/schema/TCK authority chain.

## 19. Non-blocking details intentionally left downstream

The following are appropriate for Accepted-AEP normative specification/schema work and do not block `Proposed` review because the portable semantics are already bounded:

- exact JSON Schema property names and regex maximum lengths;
- final IANA/private media-type registration choice;
- exact AVP requirement IDs;
- exact TCK case IDs/file organization;
- exact programming-language SPI method names;
- PostgreSQL/MySQL SQL/setup implementation;
- backend diagnostic code mapping details that do not change portable outcomes.

If protocol review finds any of these changes the semantics rather than just representation, AEP-0010 must return to Draft or be amended before acceptance.

## 20. Open review questions

No unresolved design blocker remains from RS-BR-001..RS-BR-008.

Protocol review should still challenge the following decisions rather than treating them as predetermined:

1. Is the mandatory 65-digit integer / decimal(65,30) portability intersection the right v0.1 tradeoff?
2. Is all-row structural named projection intentionally narrow enough for v0.1?
3. Is mandatory logical row identity acceptable for every relation in the authoritative surface?
4. Is the Manifest + baseline StateImage Artifact graph sufficiently minimal?
5. Is `STATE_EQUIVALENT` as the maximum v0.1 restore claim appropriately conservative?
6. Does the QUIESCING settlement model preserve task/evaluation separation without under-specifying Subject database access?
7. Does reference parity evidence sufficiently protect against one-engine-shaped semantics?

These are review questions, not missing definitions.

## 21. Readiness conclusion

All Draft-design blockers are closed and the AEP text has been reconciled with those decisions.

The proposal now has:

- complete problem/scope;
- standards/implementation analysis;
- portable semantics;
- protocol/schema direction;
- Security analysis;
- backward compatibility/release boundary;
- execution-sensitive conformance strategy;
- reference implementation gate;
- alternatives;
- no-transitional-implementation boundary.

Therefore:

**AEP-0010 IS READY TO MOVE FROM `Draft` TO `Proposed` FOR FORMAL PROTOCOL REVIEW.**

This audit does **not** recommend `Accepted` yet.

`Proposed` remains non-normative and does not authorize:

- relational normative spec/schema/TCK registration;
- PostgreSQL/MySQL implementation;
- merge of this or parent PRs;
- release selection/publication;
- AEP-0009 Finalization.

A future `Accepted` transition requires an explicit recorded protocol-maintainer decision after review.
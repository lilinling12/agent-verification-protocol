# Alpha 3 — AEP-0010 Accepted Decision

Status: **ACCEPTED — RELATIONAL NORMATIVE CLOSURE AUTHORIZED**  
AEP: `rfcs/AEP-0010-relational-state-resource-profile.md`  
Decision scope: AEP lifecycle transition from `Proposed` to `Accepted` only.  
Authority: explicit protocol-maintainer governance decision; this record does not make downstream relational specification text Final and does not authorize merge or backend-first implementation.

## Decision

The protocol maintainer explicitly accepted the AEP-0010 Relational State direction on 2026-08-24.

AEP-0010 is therefore advanced from `Proposed` to `Accepted`.

Under `GOVERNANCE.md`, `Accepted` means the protocol direction is approved and downstream normative closure may proceed through the governed authority chain. For Relational State, that chain remains:

```text
Accepted AEP-0010 direction
  -> relational normative specification
  -> relational requirement index
  -> closed machine-readable schemas where serialized protocol resources require them
  -> execution-sensitive avp-relational-state-v0.1 TCK
  -> backend-neutral reference composition/interfaces derived from those authorities
  -> PostgreSQL adapter
  -> MySQL/InnoDB adapter
  -> cross-backend parity acceptance evidence
```

Acceptance does not make AEP-0010 `Final`. Final remains a later lifecycle boundary requiring merged normative text, required conformance coverage, implementation alignment evidence, and release governance.

## Accepted review baseline

The semantic acceptance-oriented review was completed at exact head:

`4dd656ebaa34b3284c6fff5a6044d3696b164b30`

PR review:

`5004370426`

Review result:

`ACCEPTANCE-READY DIRECTION — explicit protocol-maintainer Proposed -> Accepted decision still required.`

That review found RS-PR-001 through RS-PR-003 closed and found no new cross-contract semantic blocker across AEP-0009/Fabric, Environment, Scenario, Core, Security, Evidence, conformance architecture, or the no-transitional-implementation gate.

The final pre-acceptance branch head was:

`ad79ca158fce56851ce2fd545735bd86794baadb`

The only semantic-review-to-final-head change was a ROADMAP synchronization commit. Final-head review `5004379749` recorded that no AEP, schema, TCK, runtime, or backend semantics changed after the acceptance-oriented review.

Final pre-acceptance gates passed:

- CI #526 — success, including Python 3.11/3.12/3.13 Quality, reproducible package checks, installed-wheel identity/smoke, installed-wheel full registered TCK, and release-evidence verification;
- Governance #572 — success;
- Governance #573 — success;
- Release Validation #62 — success.

These gates are integrity evidence. The lifecycle transition is authorized by the explicit protocol-maintainer acceptance decision, not inferred from CI.

## Accepted direction

The Accepted AEP-0010 direction includes the following reviewed conclusions.

1. The portable Resource Capability is one cohesive claim: `state.relational @ avp-relational-state-v0.1 / 0.1`.
2. PostgreSQL, MySQL/InnoDB, SQL syntax, transaction tokens, backup formats, catalogs, driver APIs, and product names are implementation mechanisms rather than protocol authority.
3. `RelationalStateManifest` defines portable logical relational-state interpretation identity, not the complete Environment execution identity.
4. A conforming resource binds one immutable Manifest and one baseline `RelationalStateImage` as relational state-identity Artifacts without a content-addressed identity cycle.
5. Exact canonical relational bytes use the accepted typed scalar model and RFC 8785 JCS; integer/decimal precision does not depend on JSON IEEE-754 numbers.
6. The mandatory v0.1 scalar portability boundary is closed and conservative, including integer up to 65 decimal digits, decimal precision 1..65/scale 0..30, temporal fractional precision 0..6, exact Unicode text, binary, date, local/instant temporal forms, UUID, boolean, and nullability.
7. Every authoritative relation has a portable non-null unique logical row key independent of backend primary-key/index names, declaration order, collation, and physical row identity.
8. Named evaluator projections are immutable all-row relation/column subsets; v0.1 does not define a portable SQL/predicate/join/expression language.
9. Evaluator projection over multiple relations must represent one committed logical view and must not expose uncommitted Subject state or torn cross-relation state.
10. Core `QUIESCING` remains the only top-level side-effect boundary; no relational lifecycle is introduced, no dirty-read shortcut is allowed, and Control must not auto-commit Subject work.
11. Logical schema/binding drift is defined by inability to continue satisfying the immutable Manifest, not by raw catalog/DDL byte equality.
12. Database programs/configuration outside the Manifest that materially affect Scenario execution semantics must reuse existing Scenario/Fabric execution-input identity binding. Equal rows do not imply equal Environment execution identity.
13. Evaluator-private authoritative relational state may remain in evaluator-confidential Evidence. Subject-visible routes, contexts, observations, and locators must enforce existing Scenario/Environment/Security authorization and non-disclosure rules. Artifact identity is not retrieval authorization.
14. Reset success requires independent post-reset projection proving exact baseline StateImage identity under the same Manifest.
15. Snapshot identity remains Environment/resource-owned; backend snapshot/read-view tokens are implementation details.
16. Successful base relational restore requires independent re-projection of the full authoritative state and reports exactly `STATE_EQUIVALENT`; failed equivalence is a failed/non-equivalent restore; `EXACT` is forbidden for the base v0.1 relational capability.
17. Semantic diff is defined by logical relation/key identity; changing a logical key is delete-old plus insert-new.
18. Relational TCK semantics are backend-neutral and execution-sensitive. Portable cases must not branch on PostgreSQL/MySQL or pass from capability metadata alone.
19. Privileged fixture-control operations used to create concurrency, DDL, transaction, security, or negative-test conditions are TCK harness seams and do not become public AVP SQL/database APIs.
20. At minimum, metadata-identical broken implementations such as torn projection and false restore must be rejected by observed behavior; hidden-state leakage and execution-input drift are also required conformance directions.
21. Third-party conformance requires one implementation to pass the profile, not two database products.
22. The AVP reference-completeness claim is stricter: PostgreSQL and MySQL/InnoDB must independently pass the same portable profile and shared parity vectors before the Relational State vertical slice is called cross-backend reference-complete.
23. Release/version selection remains separately governed and is not implied to be `0.3.1`.

## Proposed review history

AEP-0010 first closed eight Draft -> Proposed design blockers:

- RS-BR-001 — canonical scalar lexical encoding;
- RS-BR-002 — Manifest / StateImage identity;
- RS-BR-003 — authoritative surface / named projections;
- RS-BR-004 — portable row identity;
- RS-BR-005 — QUIESCING / unsettled Subject mutation behavior;
- RS-BR-006 — portable schema/binding drift;
- RS-BR-007 — PostgreSQL/MySQL-neutral parity fixture;
- RS-BR-008 — language-neutral TCK execution boundary.

Formal Proposed review `5004337751`, anchored to `29586a050a758a7058e1489df8c0b75e1d7088ca`, then found three acceptance blockers:

- RS-PR-001 — evaluator-private relational-state visibility was over-restricted;
- RS-PR-002 — execution-relevant database program/configuration identity was under-bound;
- RS-PR-003 — successful restore fidelity was ambiguous.

All three were incorporated into AEP-0010 before the acceptance-oriented re-review. `docs/design/alpha3-relational-state-proposed-review-blockers.md` records their disposition and the supersession rule for conflicting Draft-era design wording.

## Acceptance effect

Acceptance authorizes the project to start the next governed Relational State work unit:

1. draft the canonical relational normative specification;
2. encode requirement-index traceability from the Accepted AEP semantics;
3. define `RelationalStateManifest`, `RelationalStateImage`, projection/diff, and related serialized contracts only where required by the normative text;
4. create the execution-sensitive `avp-relational-state-v0.1` TCK against the normative requirements;
5. include runtime-execution negative cases for torn observation, false restore, hidden-state leakage, execution-input drift, stale/foreign ownership, and fail-closed incompatibility where applicable;
6. run a relational normative-closure audit before treating a reference implementation as conformance evidence;
7. derive the common reference interface from Spec -> Schema -> TCK rather than from PostgreSQL or MySQL implementation precedent;
8. only after the portable authority slice is reviewable, implement the PostgreSQL reference adapter;
9. implement the MySQL/InnoDB adapter against the same portable TCK rather than a backend-specific protocol fork;
10. complete shared canonical cross-backend parity evidence before declaring reference-complete portability.

Acceptance does **not** authorize skipping directly to PostgreSQL/MySQL implementation.

## No-transitional-implementation decision

The Accepted decision preserves the Alpha 3 long-term architecture constraint:

- no PostgreSQL-first public API generalized later;
- no separate PostgreSQL/MySQL primary protocol semantics for the mandatory portable profile;
- no generic `supports_*` capability family as a substitute for the cohesive relational profile;
- no untyped public property/value bags for known protocol structure;
- no raw driver rows, SQL dumps, backend catalogs, PK/index metadata, or backend snapshot tokens used as portable relational identity;
- no Control auto-commit or dirty-read shortcut during `QUIESCING`;
- no `EXACT` restore claim derived from logical row equality;
- no backend-name branches in portable TCK cases;
- no metadata-only self-certification;
- no compatibility shim for a deliberately temporary unreleased relational architecture.

This is a long-term open-source architecture constraint, not a temporary staging preference.

## Non-authorizations

This Accepted decision does **not** authorize:

- merging PR #86 without explicit merge authorization;
- merging parent stacked PRs #83/#84/#85 without explicit merge authorization;
- changing AEP-0010 to `Final`;
- changing AEP-0009 to `Final`;
- treating the future relational normative candidate as Final merely because AEP-0010 is Accepted;
- PostgreSQL/MySQL implementation before the corresponding Spec -> Schema -> TCK authority slice is reviewable;
- selecting an Alpha 3 release version;
- assigning Alpha 3 to `0.3.1`;
- changing release-development mode;
- creating a tag or GitHub Release;
- PyPI/package-index publication;
- signing or attestation publication;
- treating Python reference-runtime behavior as protocol authority.

Stable `v0.3.0` remains the published Alpha 2 baseline. Repository source remains in `0.3.1.dev0` development mode until separate release-management authority changes it.

## Next governed gate

The next gate is **Relational State normative closure**.

The normative specification must derive its requirement families from the Accepted AEP-0010 semantics. Schema fields and TCK vectors must be derived from that specification and must not define missing semantics themselves.

Candidate requirement identifiers are intentionally not declared authoritative by this acceptance record. They become governed only when the reviewed relational requirement index is created through the active normative-candidate process.

## Final decision

**AEP-0010: ACCEPTED.**

**Relational State direction: APPROVED.**

**Relational normative specification / requirement-index / schema / TCK work: AUTHORIZED through the governed authority chain.**

**PostgreSQL/MySQL backend-first or transitional implementation: NOT AUTHORIZED.**

**PR #86 merge: NOT AUTHORIZED by this decision.**

**Alpha 3 release/version/publication: NOT AUTHORIZED.**

# Alpha 3 Relational State Proposed Review Blockers

Status: **BLOCKER EDITS INCORPORATED — ACCEPTANCE RE-REVIEW REQUIRED**

Proposal: AEP-0010 — Relational State Resource Profile v0.1
Formal review baseline: `29586a050a758a7058e1489df8c0b75e1d7088ca`
PR review: `5004337751`

## Purpose

This record tracks the three protocol-semantic blockers found during formal Proposed review of AEP-0010 and their disposition.

The review decisions have now been incorporated into the current AEP-0010 `Proposed` text. That incorporation does **not** change AEP lifecycle state, authorize downstream normative closure, authorize PostgreSQL/MySQL implementation, or constitute the explicit protocol-maintainer `Accepted` decision.

The next gate is an exact-head acceptance-oriented re-review after repository validation completes.

## RS-PR-001 — Hidden evaluator state visibility

### Original finding

The reviewed AEP text prohibited hidden evaluator data from portable Manifest/Projection/StateImage/Diff material. That was stronger than the existing AVP Security/Evidence model, which permits evaluator-private verification material while prohibiting unauthorized Subject disclosure.

### Incorporated decision

AEP-0010 now explicitly defines visibility/access-scoped confidentiality:

1. relational Artifacts MAY contain evaluator-private authoritative state when required by verification;
2. the full authoritative StateImage is not weakened by deleting hidden rows/columns merely to make it Subject-safe;
3. Subject-visible relational observations/routes/results/context/locators MUST NOT disclose evaluator-private state unless the materialized Scenario explicitly authorizes it;
4. opaque Artifact identities may be exposed only under existing Security rules and do not grant retrieval authority;
5. relational Evidence reuses existing `evaluator-confidential`, `secret`, `regulated`, and other Evidence classifications;
6. Subject-scoped/redacted representations are distinct Artifact bytes with their own identity;
7. the future relational TCK must include evaluator-private state non-disclosure through Subject-visible relational surfaces.

This preserves `AVP-SECURITY-004`, Environment actor-scoped observation, and Evidence classification semantics.

**RS-PR-001: EDIT INCORPORATED — PENDING ACCEPTANCE RE-REVIEW.**

## RS-PR-002 — Execution-relevant database program/config identity

### Original finding

Logical Manifest/StateImage identity intentionally excluded raw database programs/configuration, but some excluded mechanisms can materially alter Episode behavior while the same logical state bytes remain unchanged.

### Incorporated decision

AEP-0010 now explicitly composes relational state identity with existing Scenario/Fabric execution-input identity:

1. `RelationalStateManifest` is portable logical **state interpretation** identity, not necessarily complete Environment execution identity;
2. database programs/configuration outside the Manifest that materially affect the selected Scenario MUST be bound to profile-appropriate resolved immutable identity through existing Scenario/Fabric execution-input mechanisms;
3. examples include execution-relevant triggers, defaults, generated expressions, constraints, routines, extensions, SQL modes, timezone/session configuration, and database schema-program revision;
4. relevance is determined by the materialized execution contract, not by raw catalog existence;
5. required identity that cannot be established fails materialization/provisioning before Episode execution;
6. execution identities remain distinct from canonical relational state digests and cannot be replaced by backend product names or catalog fingerprints;
7. runtime drift in a bound execution input invalidates the execution binding even if the logical Manifest remains structurally satisfiable;
8. the future relational TCK must include execution-input binding/drift behavior.

This reuses `AVP-SCENARIO-008` / Fabric identity instead of inventing database-specific provenance.

**RS-PR-002: EDIT INCORPORATED — PENDING ACCEPTANCE RE-REVIEW.**

## RS-PR-003 — Successful restore fidelity

### Original finding

The reviewed AEP required a successful restore to re-establish the snapshot StateImage but only imposed an upper bound of `STATE_EQUIVALENT`, leaving successful `NON_EQUIVALENT` reporting semantically possible.

### Incorporated decision

AEP-0010 now defines the v0.1 relational restore result unambiguously:

1. success requires independent re-projection proving equality with the owner-valid snapshot StateImage under the same Manifest;
2. every successful conforming v0.1 relational restore reports resource fidelity exactly `STATE_EQUIVALENT`;
3. failure to re-establish state is a failed restore and cannot report successful equivalence; fidelity is `NON_EQUIVALENT` or the equivalent failed representation selected by the eventual schema;
4. `EXACT` remains invalid for the base relational capability;
5. Fabric aggregate fidelity still uses the existing weakest-required-participant rule;
6. future TCK and PostgreSQL/MySQL parity evidence must assert the exact successful fidelity rather than an upper bound.

This specializes Environment `AVP-ENVIRONMENT-008` without inflating fidelity.

**RS-PR-003: EDIT INCORPORATED — PENDING ACCEPTANCE RE-REVIEW.**

## Historical design-document disposition

The detailed Draft-era design files remain non-normative provenance for how AEP-0010 reached Proposed:

- `docs/design/alpha3-relational-state-canonical-model.md`;
- `docs/design/alpha3-relational-state-surface-and-row-identity.md`;
- `docs/design/alpha3-relational-state-quiescing-and-schema-drift.md`;
- `docs/design/alpha3-relational-state-tck-and-parity.md`;
- `docs/design/alpha3-relational-state-profile-design.md`;
- `docs/design/alpha3-relational-state-proposed-readiness-audit.md`.

Where any Draft-era wording conflicts with the current AEP-0010 Proposed text on RS-PR-001, RS-PR-002, or RS-PR-003, the current AEP text is the active proposal and this review record documents why the earlier design wording was superseded. Historical documents MUST NOT be used to reintroduce the superseded semantics into the future normative spec/schema/TCK.

In particular, the Draft-era phrase that successful restore may report "no more than `STATE_EQUIVALENT`" is superseded: current Proposed semantics require successful v0.1 relational restore to report **exactly `STATE_EQUIVALENT`**.

## Acceptance gate

AEP-0010 is acceptance-ready only if all of the following are true:

1. RS-PR-001..003 edits are incorporated into AEP-0010 — **DONE**;
2. ROADMAP and PR metadata reflect the review state — **DONE**;
3. historical Draft design wording has an explicit supersession rule — **DONE in this record**;
4. exact-head CI, Governance, and Release Validation are green — **PENDING FOR CURRENT HEAD**;
5. a short acceptance-oriented protocol re-review finds no remaining semantic blocker — **PENDING**;
6. the protocol maintainer separately and explicitly authorizes `Proposed -> Accepted` — **NOT AUTHORIZED**.

Generic continuation does not satisfy item 6.

## Current conclusion

```text
AEP-0010 lifecycle: Proposed
Formal Proposed review: completed
RS-PR-001: edit incorporated / re-review pending
RS-PR-002: edit incorporated / re-review pending
RS-PR-003: edit incorporated / re-review pending
Acceptance-oriented re-review: pending exact-head gates
Accepted: NOT AUTHORIZED
Relational normative surface: NOT AUTHORIZED
PostgreSQL/MySQL official adapters: NOT AUTHORIZED
```

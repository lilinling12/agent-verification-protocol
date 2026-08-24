# Alpha 3 Relational State Proposed Review Blockers

Status: **PROPOSED REVIEW — ACCEPTANCE BLOCKED**

Proposal: AEP-0010 — Relational State Resource Profile v0.1
Review baseline: `29586a050a758a7058e1489df8c0b75e1d7088ca`
PR review: `5004337751`

## Purpose

This record captures protocol-semantic blockers found during the formal Proposed review of AEP-0010. It does not itself amend AEP-0010, change lifecycle state, authorize downstream normative closure, or authorize PostgreSQL/MySQL implementation.

AEP-0010 remains `Proposed` until these decisions are absorbed into the AEP text and the resulting exact head is re-reviewed.

## RS-PR-001 — Hidden evaluator state visibility

### Finding

The current AEP text says portable Manifest/Projection/StateImage/Diff material must not contain hidden evaluator data. That rule is too strong relative to the existing AVP Security/Evidence model.

AVP Security permits the Evaluator Plane to hold evaluator-only authoritative state, private benchmark fixtures, hidden verification material, and verification-only Evidence. The normative restriction is on **disclosure to Subject-visible routes and contexts**, not on evaluator-confidential Artifact content itself.

### Required correction

The relational profile must adopt visibility/access-scoped confidentiality:

1. `RelationalStateManifest`, `RelationalProjection`, `RelationalStateImage`, and relational Diff Artifacts MAY contain evaluator-private authoritative state when required by the selected verification contract.
2. Subject observations, Subject tool/results/routes, Subject execution context, and Subject-visible Artifact locators MUST NOT disclose evaluator-private relational content unless the materialized Scenario explicitly promotes that content into the Subject-visible contract.
3. An Artifact digest MAY be exposed only under the existing Security rule that the opaque identity itself does not disclose protected content and does not grant retrieval authority.
4. Relational Evidence uses existing Evidence classifications such as `evaluator-confidential`, `secret`, or `regulated`; Relational State must not create a competing secrecy taxonomy.
5. A full authoritative StateImage must not be weakened by deleting evaluator-private rows/columns merely to make the Artifact Subject-safe. Access control/classification is the correct boundary.
6. Relational security TCK direction must include hidden-state non-disclosure through Subject-visible relational surfaces.

### Compatibility rationale

This preserves `AVP-SECURITY-004`, Environment actor-scoped observation, and Evidence classification semantics. It prevents the relational profile from narrowing evaluator authority that existing contracts explicitly allow.

**RS-PR-001: DECISION DEFINED — AEP TEXT UPDATE REQUIRED.**

## RS-PR-002 — Execution-relevant database program/config identity

### Finding

AEP-0010 correctly excludes raw database catalogs, DDL strings, triggers, defaults, generated expressions, constraints, routines, sequence configuration, SQL modes, session settings, and similar backend mechanisms from the **logical relational state identity**.

However, some of those mechanisms can materially change Episode execution while leaving the same `RelationalStateManifest` and baseline `RelationalStateImage` bytes.

Example: identical logical rows plus a materially different trigger or default can cause the same Subject mutation to produce different authoritative state. If that behavior is neither represented in the Manifest nor identity-bound elsewhere, the verification input is under-specified.

### Required correction

The relational profile must explicitly compose with Scenario external-reference identity and Fabric execution-input binding:

1. `RelationalStateManifest` identity describes the portable logical **state interpretation** contract; it is not necessarily the complete Environment execution identity.
2. Any database program, configuration, schema program revision, extension, trigger/default/generated expression, constraint behavior, SQL mode, timezone/session configuration, or other database input that materially affects Scenario execution semantics MUST be bound to profile-appropriate resolved immutable identity through existing Scenario/Fabric execution-input identity mechanisms.
3. The materialized Scenario/Fabric contract determines which such inputs are execution-relevant. The relational profile must not require raw equality for irrelevant backend metadata.
4. If required execution-relevant identity cannot be established, Scenario materialization/provisioning must fail closed before Episode execution.
5. These execution identities remain separate from canonical relational state digests and must not be inferred from backend product names or catalog fingerprints.
6. Runtime drift in an execution-relevant bound input invalidates the existing execution binding even when the logical relational Manifest remains structurally satisfiable.

### Compatibility rationale

This reuses `AVP-SCENARIO-008` rather than inventing a second database-specific provenance system. It keeps `STATE_EQUIVALENT` narrow and useful while ensuring equal logical row state does not falsely imply equal execution semantics.

**RS-PR-002: DECISION DEFINED — AEP TEXT UPDATE REQUIRED.**

## RS-PR-003 — Successful restore fidelity

### Finding

The current AEP requires successful restore to independently re-project the full authoritative surface and re-establish the snapshot `RelationalStateImage` identity, but only says successful restore may report no stronger than `STATE_EQUIVALENT`.

Under the existing Environment fidelity model, re-establishing the same Manifest-bound authoritative relational state is exactly the condition for state equivalence. A successful conforming restore reporting `NON_EQUIVALENT` would under-report the semantic result and leave TCK behavior ambiguous.

### Required correction

For `state.relational / avp-relational-state-v0.1 / 0.1`:

1. restore is successful only after independent re-projection proves equality with the snapshot `RelationalStateImage` identity under the same Manifest;
2. a successful restore MUST report resource restore fidelity exactly `STATE_EQUIVALENT`;
3. failure to re-establish the snapshot state MUST produce a failed restore and `NON_EQUIVALENT` (or the equivalent failure representation required by the final operation schema);
4. `EXACT` remains invalid for the base relational capability;
5. Fabric aggregate restore fidelity continues to compose through existing weakest-required-participant rules;
6. TCK and cross-backend parity must assert the exact successful fidelity value rather than merely an upper bound.

### Compatibility rationale

This specializes, rather than changes, Environment `AVP-ENVIRONMENT-008`. It removes ambiguity without inflating fidelity.

**RS-PR-003: DECISION DEFINED — AEP TEXT UPDATE REQUIRED.**

## Acceptance gate

AEP-0010 is not acceptance-ready until all of the following are true:

1. RS-PR-001..003 decisions above are incorporated into AEP-0010 itself;
2. no contradictory stale wording remains in canonical-model, quiescing/drift, TCK/parity, readiness, ROADMAP, or PR metadata surfaces;
3. exact-head CI, Governance, and Release Validation are green;
4. a short acceptance-oriented protocol re-review finds no remaining semantic blocker;
5. the protocol maintainer separately and explicitly authorizes `Proposed -> Accepted`.

Generic continuation does not satisfy item 5.

## Current conclusion

```text
AEP-0010 lifecycle: Proposed
Formal protocol review: completed
RS-PR-001: blocker / decision defined / AEP update pending
RS-PR-002: blocker / decision defined / AEP update pending
RS-PR-003: blocker / decision defined / AEP update pending
Accepted: NOT AUTHORIZED
Relational normative surface: NOT AUTHORIZED
PostgreSQL/MySQL official adapters: NOT AUTHORIZED
```

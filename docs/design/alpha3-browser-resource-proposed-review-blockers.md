# Alpha 3 Browser Resource Proposed Review Blockers

Status: **ACCEPTANCE EVIDENCE SATISFIED — ACCEPTANCE RE-REVIEW BLOCKED BY BPR-010**

Proposal: AEP-0011 — Browser Resource Profile v0.1

Formal review baseline: `main@ccd05b71635b46218dfa14043320a60376339dc2`

Formal review record: `docs/design/alpha3-browser-resource-formal-proposed-review.md`

Protocol-resolution branch baseline: `main@fa62d004a4fb8498219989abcbd0b21caf14177f`

Acceptance-evidence disposition: `docs/acceptance/alpha3-browser-aep0011-acceptance-evidence-disposition.md`

Acceptance-oriented re-review: `docs/acceptance/alpha3-aep-0011-acceptance-review.md`

Evidence baseline: `103c049c51d199c3c744f675283aa8480ca20774`

Acceptance-review baseline: `66eb158952ff0b90e388f43ee3bae38bd750efbf`

## Purpose

This record tracks the protocol-semantic blockers identified by the formal Proposed review of AEP-0011, their later executable-evidence disposition, and any new semantic blocker found by acceptance-oriented re-review.

AEP-0011 remains `Proposed`. Incorporated decisions, green evidence, and review records do not self-approve the AEP and do not authorize Browser Spec/Schema/TCK/harness/runtime work.

Historical formal-review findings remain provenance. This ledger is the current disposition surface.

## BPR-001 — Capability/profile naming closure

AEP-0011 fixes:

```text
capabilityId: state.browser
profile: avp-browser-unpartitioned-cookie-localstorage-v0.1
revision: "0.1"
```

The capability is explicitly a Browser state capability, not a universal Browser Agent action API or full browser-profile checkpoint.

**BPR-001: PROTOCOL DECISION INCORPORATED.**

## BPR-002 — Explicit unpartitioned `localStorage` boundary

AEP-0011 limits v0.1 to **unpartitioned `localStorage`** whose storage identity can be proven to be the tuple origin in the controlled execution context. Partitioned/top-level-site-keyed state cannot be flattened into ordinary tuple-origin state; a material dependency outside the base boundary fails closed unless separately governed.

**BPR-002: PROTOCOL DECISION INCORPORATED.**

## BPR-003 — Lossless cookie identity/projection proof

The portable cookie identity remains:

```text
(name, domain, hostOnly, path)
```

Backend lossiness does not weaken the protocol. Evaluator/control authority must establish required identity/state through an independently reviewable mechanism or fail closed.

Cross-engine evidence at `103c049c51d199c3c744f675283aa8480ca20774` demonstrates:

- HTTP host-only/domain behavioral distinction;
- Classic WebDriver lossiness and fail-closed rejection rather than `hostOnly` inference;
- positive evaluator/control-owned provenance projection across Chrome, Firefox, and Safari;
- rejection of an intentionally untracked selected cookie;
- provenance retained as Evidence, not BrowserStateImage identity.

**BPR-003: PROTOCOL DECISION INCORPORATED — ACCEPTANCE EVIDENCE SATISFIED.**

## BPR-004 — Cookie temporal semantics and restore fidelity

AEP-0011 keeps `SameSite=Default` distinct from explicit `Lax`, forbids Default->Lax normalization, and fails closed when material creation-time-dependent behavior cannot be preserved or otherwise proven equivalent.

Cross-engine evidence demonstrates:

- lossy Classic SameSite/creation-time transport behavior without treating it as protocol authority;
- product-dependent fresh-Default behavior;
- `restoreEligible=false` for a material creation-time-sensitive Scenario when historic behavior cannot be established;
- positive evaluator/control provenance for stored Default versus explicit Lax;
- successful explicit-Lax, temporally non-material snapshot/restore/reset with independent reprojection and fidelity exactly `STATE_EQUIVALENT` across Chrome, Firefox, and Safari.

**BPR-004: PROTOCOL DECISION INCORPORATED — ACCEPTANCE EVIDENCE SATISFIED.**

## BPR-005 — Closed state-selection grammar and equivalence domain

AEP-0011 fixes finite, duplicate-free, exact-origin and exact-stored-domain complete-set selection. No regex/glob/suffix/vendor predicate/runtime-code selection is permitted. Missing, extra, transformed, scope-shifted, or differently keyed in-scope state is non-equivalent.

The semantic membership grammar remains closed. Acceptance re-review later identified a distinct collection-ordering/digest issue tracked separately as BPR-010; that finding does not reopen the membership decision itself.

**BPR-005: PROTOCOL DECISION INCORPORATED.**

## BPR-006 — Portable settlement witness

Accepted projection requires a positive evaluator/control settlement witness: Subject side-effect admission is closed, every accepted profile-relevant mutation has a terminal outcome, none remains unresolved, and projection starts only after those facts hold. Timeouts, sleeps, network-idle, quiet windows, vendor queues, and command completion cannot prove settlement by themselves.

BAE-010 executes this rule and rejects projection while an accepted mutation remains unresolved.

**BPR-006: PROTOCOL DECISION INCORPORATED; EXECUTABLE EVIDENCE PRESENT.**

## BPR-007 — Lossless Web IDL `DOMString` canonical semantics

AEP-0011 defines exact unsigned UTF-16 code-unit preservation, two-byte network-order encoding, unpadded base64url serialization, equality on decoded code-unit sequences, and unsigned UTF-16 lexicographic key ordering with shorter-prefix-first semantics.

BAE-007 covers empty, NUL, BMP, surrogate-pair, unmatched-surrogate, and normalization-sensitive values.

**BPR-007: PROTOCOL DECISION INCORPORATED; EXECUTABLE EVIDENCE PRESENT.**

## BPR-008 — Excluded-state residual noninterference

For each materially relevant excluded surface, AEP-0011 requires isolation/noninterference, immutable execution-identity/policy binding, or fail-closed insufficiency.

Shipping BAE-011 demonstrates one admitted isolation strategy across Chrome, Firefox, and Safari using Service Worker/Cache plus IndexedDB residue and separately created clean native sessions.

**BPR-008: PROTOCOL DECISION INCORPORATED; CROSS-ENGINE EXECUTABLE EVIDENCE PRESENT.**

## BPR-009 — Chromium/Gecko/WebKit acceptance evidence matrix

The AEP requires a reviewable three-engine acceptance matrix covering cookie identity/projection, host-only/domain behavior, SameSite/temporal restrictions, admitted localStorage, partition non-admission, lossless Web Storage strings, restore/reset reprojection, settlement, and residual-state assumptions.

At evidence head `103c049c51d199c3c744f675283aa8480ca20774`, the complementary Playwright diagnostic and shipping/native lanes cover BAE-001 through BAE-012. Shipping evidence uses branded Chrome, Mozilla Firefox, and Safari without AVP privacy flags/prefs that force convergence.

`docs/acceptance/alpha3-browser-aep0011-acceptance-evidence-disposition.md` records exact workflow runs, artifact IDs/digests, product identities, and evidence boundaries.

**BPR-009: ACCEPTANCE-EVIDENCE MATRIX SATISFIED.**

## BPR-010 — Canonical collection ordering / digest determinism

### Acceptance-review finding

Acceptance-oriented review at exact head `66eb158952ff0b90e388f43ee3bae38bd750efbf` found one new semantic blocker after BPR-001..009 evidence closure.

AEP-0011 defines content-addressed Browser Manifest/Image identity and says selection lists are canonicalized, but does not define the canonical order of all collection-valued fields whose JSON array order affects exact bytes.

The missing protocol decisions include at least:

1. ordering of Manifest localStorage-origin selections;
2. ordering of Manifest cookie stored-domain selections;
3. ordering of `BrowserStateImage.origins[]`;
4. ordering of `BrowserStateImage.cookies[]` by portable cookie identity.

The existing unsigned UTF-16 rule defines localStorage **key** ordering but does not resolve these surrounding collection orders.

### Why this blocks acceptance

JCS does not reorder array elements. Two implementations can therefore satisfy the current membership/equality rules yet produce different Manifest/Image exact bytes and SHA-256 identity solely because backend/browser enumeration order differs.

That ambiguity affects Manifest Artifact digest, `manifestDigest`, BrowserStateImage/state digest, baseline/runtime snapshot identity, and cross-implementation parity. A downstream Schema/TCK cannot choose the comparator without inventing protocol semantics.

AEP-0010 provides the accepted precedent: profile-defined collection ordering is established before JCS serialization.

### Required closure

AEP-0011 must define, before acceptance:

- deterministic canonical ordering for exact origin selections and exact stored-domain selections;
- deterministic `origins[]` ordering;
- deterministic `cookies[]` ordering over `(name, domain, hostOnly, path)` with an explicit textual/boolean comparator;
- backend enumeration/insertion order as non-authoritative;
- handling of noncanonical order before content-addressed identity is computed.

Focused provider-neutral evidence must prove that logically identical state/selections observed in different enumeration orders cannot produce divergent accepted canonical identity.

**BPR-010: OPEN — ACCEPTANCE SEMANTIC BLOCKER.**

## Historical design-document disposition

Draft-era portability/readiness documents remain provenance:

- `docs/design/alpha3-browser-resource-portability-audit.md`;
- `docs/design/alpha3-browser-resource-proposed-readiness-audit.md`;
- `docs/acceptance/alpha3-browser-draft-main-adoption.md`;
- `docs/acceptance/alpha3-browser-readiness-main-adoption.md`;
- `docs/acceptance/alpha3-aep-0011-proposed-decision.md`.

Where earlier Draft assumptions conflict with the incorporated Proposed-review decisions or later acceptance-review findings, this ledger records the current disposition.

## Acceptance gate

AEP-0011 is acceptance-ready only when all of the following are true:

1. BPR-001..BPR-008 original protocol decisions are incorporated — **SATISFIED**;
2. BPR-003/BPR-004 cross-engine implementation-boundary evidence is complete — **SATISFIED AT `103c049c51d199c3c744f675283aa8480ca20774`**;
3. BPR-009 Chromium/Gecko/WebKit evidence matrix is complete and reviewable — **SATISFIED AT `103c049c51d199c3c744f675283aa8480ca20774`**;
4. BPR-010 canonical collection ordering/digest determinism is incorporated and evidenced — **OPEN**;
5. ROADMAP/adoption metadata accurately reflect the actual Proposed/blocker/evidence state — **PENDING FINAL PRE-ACCEPTANCE SYNC**;
6. exact-head CI, Governance, and applicable Browser evidence gates are green for the reviewed evidence-sync head — **SATISFIED AT `66eb158952ff0b90e388f43ee3bae38bd750efbf`**;
7. an acceptance-oriented exact-head protocol re-review finds no remaining semantic blocker — **BLOCKED BY BPR-010**;
8. the protocol maintainer separately and explicitly authorizes `Proposed -> Accepted` — **NOT AUTHORIZED**.

Generic continuation does not satisfy item 8.

## Current conclusion

```text
AEP-0011 lifecycle: Proposed
Formal Proposed review: completed
BPR-001..BPR-009 prior decisions/evidence: closed for current review
BPR-010 canonical collection ordering/digest determinism: OPEN
Acceptance-oriented exact-head protocol re-review: BLOCKED
Accepted: NOT AUTHORIZED
Browser normative Spec/Schema/TCK: NOT AUTHORIZED
Browser conformance harness: NOT AUTHORIZED
Playwright/reference runtime: NOT AUTHORIZED
```

The next governed work is a narrow protocol-first BPR-010 resolution, followed by focused canonical-ordering evidence, exact-head gates, and a repeated acceptance-oriented semantic re-review. Lifecycle promotion remains a separate explicit maintainer decision.

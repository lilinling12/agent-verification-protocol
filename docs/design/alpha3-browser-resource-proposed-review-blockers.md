# Alpha 3 Browser Resource Proposed Review Blockers

Status: **PROTOCOL DECISIONS INCORPORATED — ACCEPTANCE EVIDENCE OPEN**

Proposal: AEP-0011 — Browser Resource Profile v0.1

Formal review baseline: `main@ccd05b71635b46218dfa14043320a60376339dc2`

Formal review record: `docs/design/alpha3-browser-resource-formal-proposed-review.md`

Protocol-resolution branch baseline: `main@fa62d004a4fb8498219989abcbd0b21caf14177f`

## Purpose

This record tracks the protocol-semantic blockers identified by the formal Proposed review of AEP-0011 and distinguishes **protocol decisions incorporated into the Proposed text** from **acceptance evidence still required before lifecycle promotion can be considered**.

AEP-0011 remains `Proposed`. Incorporating a blocker decision does not self-approve the AEP, does not substitute for cross-engine evidence, and does not authorize Browser Spec/Schema/TCK/harness/runtime work.

The blocker-resolution edit is intentionally confined to AEP-0011 plus this ledger. The formal review record remains historical review evidence and is not rewritten to make its earlier findings appear retrospectively closed.

## BPR-001 — Capability/profile naming closure

### Formal-review finding

The previous working identifiers `browser.session-state` / `avp-browser-state-v0.1` could be read more broadly than the narrow unpartitioned cookie + `localStorage` state contract.

### Incorporated protocol decision

AEP-0011 now fixes:

```text
capabilityId: state.browser
profile: avp-browser-unpartitioned-cookie-localstorage-v0.1
revision: "0.1"
```

The capability is explicitly a Browser state capability, not a universal Browser Agent action API or full browser-profile checkpoint. Future partition-aware storage, richer state, action, and observation capabilities remain separately governable.

**BPR-001: PROTOCOL DECISION INCORPORATED.**

## BPR-002 — Explicit unpartitioned `localStorage` boundary

### Formal-review finding

Tuple-origin identity is not a sufficient unqualified description of modern browser storage because deployed engines partition third-party storage by top-level site and related context.

### Incorporated protocol decision

AEP-0011 now limits v0.1 to **unpartitioned `localStorage`** whose storage identity can be proven to be the tuple origin in the controlled execution context. Partitioned or top-level-site-keyed state cannot be projected as ordinary tuple-origin state. A scenario that materially depends on partitioned state must fail closed under v0.1 unless a future separately governed capability owns it.

**BPR-002: PROTOCOL DECISION INCORPORATED.**

## BPR-003 — Lossless cookie identity/projection proof

### Formal-review finding

The portable cookie identity requires `hostOnly`, while mainstream automation surfaces may not expose enough information to establish that identity directly.

### Incorporated protocol decision

AEP-0011 retains:

```text
(name, domain, hostOnly, path)
```

as selected-cookie identity. Backend API lossiness does not weaken the protocol. Evaluator/control authority must establish all required selected cookie identity/state through an independently reviewable mechanism or fail closed. Convenience serialization, inference from incomplete exports, normalization, and backend command success are insufficient proof.

### Remaining acceptance evidence

Before acceptance-oriented review can close, the identity/projection rule must be demonstrated across Chromium, Gecko, and WebKit families, including host-only versus domain-scoped behavior.

**BPR-003: PROTOCOL DECISION INCORPORATED — ACCEPTANCE EVIDENCE PENDING.**

## BPR-004 — Cookie temporal semantics and restore fidelity

### Formal-review finding

Stored-cookie creation time can affect observable HTTP behavior while mainstream portable automation surfaces do not reliably expose and restore arbitrary historic creation time. Field-equal recreated cookies can therefore be behaviorally different.

### Incorporated protocol decision

AEP-0011 does not pretend creation time is a portable BrowserStateImage field. Instead it defines **cookie temporal restore eligibility**:

1. `SameSite=Default` remains distinct from explicit `Lax`;
2. `Default -> Lax` normalization is forbidden;
3. where creation-time-dependent behavior can materially affect the verification claim and cannot be preserved or otherwise proven equivalent, restore fails closed;
4. image-field equality remains necessary but is not sufficient proof of unbounded HTTP behavioral equivalence;
5. a backend may not recreate a fresh field-equal cookie and report `STATE_EQUIVALENT` while a material temporal distinction remains unresolved.

### Remaining acceptance evidence

Chromium/Gecko/WebKit evidence must establish the practical boundary of the admitted restore class and demonstrate the fail-closed rule for temporal semantics before acceptance.

**BPR-004: PROTOCOL DECISION INCORPORATED — ACCEPTANCE EVIDENCE PENDING.**

## BPR-005 — Closed state-selection grammar and equivalence domain

### Formal-review finding

The previous Proposed text required a closed grammar but deferred the grammar itself to downstream normative work.

### Incorporated protocol decision

AEP-0011 now fixes the v0.1 grammar:

- `localStorage`: finite duplicate-free exact canonical tuple-origin list;
- every listed origin contributes its complete admitted unpartitioned map, including an empty map;
- cookies: finite duplicate-free exact canonical stored-domain list;
- every unpartitioned cookie whose canonical stored domain exactly equals a selected domain participates;
- no regex, glob, suffix/subdomain matching, vendor callback, backend-native query language, Playwright/CDP filter, partition selector, or runtime code;
- selection is immutable for the materialized resource;
- missing, extra, transformed, scope-shifted, or differently keyed in-scope state is non-equivalent.

The exact downstream schema field spelling remains open to the normative Spec/Schema phase; the selection semantics do not.

**BPR-005: PROTOCOL DECISION INCORPORATED.**

## BPR-006 — Portable settlement witness

### Formal-review finding

There is no portable universal browser-idle condition. Sleep windows, `networkidle`, or vendor queue inspection are not sufficient protocol evidence.

### Incorporated protocol decision

AEP-0011 now requires a positive profile-relevant settlement witness established by evaluator/control authority:

1. Core has closed admission of new Subject side effects;
2. every accepted pre-boundary mutation capable of affecting selected authoritative state has a known terminal outcome;
3. no accepted profile-relevant mutation remains unresolved;
4. authoritative projection begins only after those conditions hold and does not knowingly mix pre/post mutation fragments.

A timeout can terminate waiting but cannot prove settlement. Sleep, network-idle, quiet-window heuristics, vendor event queues, and backend command completion are insufficient by themselves. Failure to establish the witness fails closed as `unsettled` and produces no accepted final projection.

**BPR-006: PROTOCOL DECISION INCORPORATED.**

## BPR-007 — Lossless Web IDL `DOMString` canonical semantics

### Formal-review finding

Web Storage keys/values are Web IDL `DOMString` values and may contain unmatched UTF-16 surrogates, while generic canonical-JSON schemes can reject or transform such values.

### Incorporated protocol decision

AEP-0011 now defines protocol-owned lossless representation:

1. preserve the exact ordered sequence of unsigned 16-bit UTF-16 code units;
2. encode each code unit as two network-byte-order bytes;
3. concatenate in code-unit order;
4. serialize those bytes as unpadded base64url;
5. define equality on decoded code-unit sequences;
6. define canonical ordering lexicographically by unsigned UTF-16 code units, with shorter-prefix-first ordering.

Canonical JSON carries only the ASCII-safe encoded representation. Host-language Unicode normalization, surrogate repair, locale collation, browser enumeration order, and JSON-library string behavior cannot alter Browser v0.1 identity.

The representation revision is bound by BrowserStateManifest.

**BPR-007: PROTOCOL DECISION INCORPORATED.**

## BPR-008 — Excluded-state residual noninterference

### Formal-review finding

Excluded surfaces can still materially affect scenario behavior even though they are not part of BrowserStateImage.

### Incorporated protocol decision

For each materially relevant excluded surface, AEP-0011 now requires at least one of:

1. isolation/configuration establishing noninterference;
2. immutable execution-identity/policy binding sufficient to make the relied-upon condition explicit and drift-detectable; or
3. fail-closed declaration that Browser v0.1 is insufficient for the dependency.

The rule explicitly covers Service Worker state, Cache Storage, IndexedDB, permissions, extensions, preload scripts, profile residue, network policy, credential state, and analogous excluded state.

A successful BrowserStateImage restore never claims reproduction of excluded state merely because selected state is equal.

**BPR-008: PROTOCOL DECISION INCORPORATED.**

## BPR-009 — Chromium/Gecko/WebKit acceptance evidence matrix

### Formal-review finding

Browser portability claims require stronger cross-engine evidence before acceptance than Draft-to-Proposed readiness required.

### Incorporated protocol gate

AEP-0011 now makes Chromium + Gecko + WebKit evidence a mandatory **AEP acceptance-evidence gate**, not a desirable optional matrix.

The matrix must cover at least:

1. selected unpartitioned cookie identity/projection;
2. host-only versus domain-scoped cookie behavior;
3. `SameSite=Default` and temporal restore restrictions;
4. admitted unpartitioned `localStorage` tuple-origin behavior;
5. rejection/non-admission of partitioned state into the base profile;
6. lossless Web Storage string behavior where the engine boundary permits the selected value;
7. independent post-restore/reset reprojection;
8. settlement fail-closed behavior;
9. residual-state isolation assumptions relied upon by the fixture.

This requirement does not force every future third-party conforming implementation to support all three engine families. Engine names remain evidence metadata, not protocol identity.

### Remaining acceptance evidence

The required three-engine evidence has **not** been produced by this protocol-edit PR and cannot be closed by documentation assertion.

**BPR-009: OPEN — ACCEPTANCE EVIDENCE REQUIRED.**

## Historical design-document disposition

Draft-era portability/readiness documents remain provenance:

- `docs/design/alpha3-browser-resource-portability-audit.md`;
- `docs/design/alpha3-browser-resource-proposed-readiness-audit.md`;
- `docs/acceptance/alpha3-browser-draft-main-adoption.md`;
- `docs/acceptance/alpha3-browser-readiness-main-adoption.md`;
- `docs/acceptance/alpha3-aep-0011-proposed-decision.md`.

They explain why AEP-0011 became Proposed but do not override the Formal Proposed Review or the incorporated blocker-resolution decisions.

The following earlier design assumptions are explicitly superseded where present:

- tuple-origin `localStorage` described without an explicit unpartitioned boundary;
- selection grammar deferred entirely to downstream normative work;
- exact Web Storage string representation deferred to generic canonical JSON;
- two materially independent browser-engine families treated as sufficient acceptance protection while a third engine was merely desirable.

## Acceptance gate

AEP-0011 is acceptance-ready only when all of the following are true:

1. BPR-001..BPR-008 protocol decisions are incorporated into the AEP-0011 Proposed text — **SATISFIED ON BLOCKER-RESOLUTION BRANCH**;
2. BPR-003/BPR-004 implementation-boundary claims receive required cross-engine evidence — **PENDING**;
3. BPR-009 Chromium/Gecko/WebKit evidence matrix is complete and reviewable — **PENDING**;
4. ROADMAP and adoption metadata accurately reflect the actual Proposed/blocker/evidence state — **PENDING MAIN ADOPTION / LATER EVIDENCE SYNC**;
5. exact-head CI, Governance, Release Validation, and applicable portability/conformance gates are green for the blocker-resolution PR — **PENDING PR HEAD**;
6. an acceptance-oriented exact-head protocol re-review finds no remaining semantic blocker — **PENDING**;
7. the protocol maintainer separately and explicitly authorizes `Proposed -> Accepted` — **NOT AUTHORIZED**.

Generic continuation does not satisfy item 7.

## Current conclusion

```text
AEP-0011 lifecycle: Proposed
Formal Proposed review: completed
BPR-001/002/005/006/007/008: protocol decisions incorporated
BPR-003/004: protocol decisions incorporated; acceptance evidence pending
BPR-009: OPEN acceptance-evidence gate
Acceptance-oriented re-review: NOT READY
Accepted: NOT AUTHORIZED
Browser normative Spec/Schema/TCK: NOT AUTHORIZED
Browser conformance harness: NOT AUTHORIZED
Playwright/reference runtime: NOT AUTHORIZED
```

The next governed work after adoption of the blocker-resolution protocol edits is to build reviewable, implementation-independent acceptance evidence across Chromium, Gecko, and WebKit for BPR-003/BPR-004/BPR-009, then perform an acceptance-oriented exact-head protocol re-review. Lifecycle promotion remains a separate maintainer decision.

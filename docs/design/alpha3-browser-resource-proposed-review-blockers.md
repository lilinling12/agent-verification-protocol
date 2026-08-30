# Alpha 3 Browser Resource Proposed Review Blockers

Status: **OPEN — PROTOCOL EDITS REQUIRED BEFORE ACCEPTANCE RE-REVIEW**

Proposal: AEP-0011 — Browser Resource Profile v0.1

Formal review baseline: `main@ccd05b71635b46218dfa14043320a60376339dc2`

Formal review record: `docs/design/alpha3-browser-resource-formal-proposed-review.md`

## Purpose

This record tracks the protocol-semantic blockers identified by the formal Proposed review of AEP-0011.

Unlike the Relational State blocker record after its edits had already been incorporated, the Browser blockers below are intentionally still **open**. No blocker-resolution edit has yet been made to AEP-0011. Keeping this ledger separate prevents the review record from being mistaken for an Accepted protocol surface and prevents implementation work from outrunning unresolved semantics.

AEP-0011 remains `Proposed`. The next governed protocol step is to resolve these blockers in AEP-0011, then perform an exact-head acceptance-oriented re-review. `Proposed -> Accepted` remains a separate explicit protocol-maintainer decision.

## BPR-001 — Capability/profile naming closure

### Finding

Current working identifiers `browser.session-state` / `avp-browser-state-v0.1` can be read more broadly than the actual narrow unpartitioned cookie + `localStorage` state contract.

### Required closure

AEP-0011 must select stable protocol-facing identifiers that:

1. identify a Browser **state** capability rather than a universal Browser Agent action API;
2. do not imply a complete browser-profile snapshot;
3. remain extensible to separately governed future partitioned-storage, richer state, action, or observation capabilities;
4. are fixed by protocol review rather than copied from an implementation package.

Recommended direction is a generic state capability such as `state.browser` plus a narrow versioned profile identifier. Exact spelling remains a protocol decision.

**BPR-001: OPEN.**

## BPR-002 — Explicit unpartitioned `localStorage` boundary

### Finding

Tuple-origin identity is not a sufficient unqualified description of modern browser storage because deployed engines partition third-party storage by top-level site and related context.

### Required closure

AEP-0011 must:

1. define the v0.1 authoritative `localStorage` surface as **unpartitioned** state;
2. state the admitted execution-context assumptions under which tuple `(scheme, host, port)` identity is valid;
3. forbid projecting partitioned storage into the base profile as ordinary tuple-origin state;
4. fail closed or require a future separately governed partition-aware capability when a scenario materially depends on partitioned state.

**BPR-002: OPEN.**

## BPR-003 — Lossless cookie identity/projection proof

### Finding

RFC 10025 cookie identity includes the host-only flag, while mainstream automation surfaces do not consistently expose enough information to recover it directly.

### Required closure

AEP-0011 must:

1. retain `(name, domain, hostOnly, path)` as portable selected-cookie identity;
2. prohibit weakening the identity because a backend API is lossy;
3. require an implementation to establish the selected identity/state through independently reviewable projection evidence or fail closed;
4. require acceptance evidence across Chromium, Gecko, and WebKit families.

**BPR-003: OPEN.**

## BPR-004 — Cookie temporal semantics and restore fidelity

### Finding

Stored-cookie creation time can affect observable HTTP behavior, including `SameSite=Default` compatibility behavior and ordering, but Browser v0.1 does not currently preserve arbitrary historical creation time.

### Required closure

AEP-0011 must:

1. preserve `SameSite=Default` as distinct state where the browser model does;
2. define the cookie classes admitted to a successful `STATE_EQUIVALENT` restore;
3. fail closed when required temporal behavior cannot be preserved or proven;
4. prohibit `Default -> Lax` normalization as a restore workaround;
5. define the exact equivalence claim without pretending that field equality alone proves unbounded behavioral identity.

**BPR-004: OPEN.**

## BPR-005 — Closed state-selection grammar and equivalence domain

### Finding

The Proposed text requires a closed grammar but still leaves the grammar itself to downstream work. That leaves protocol semantics underdetermined.

### Required closure

AEP-0011 must fix a finite vendor-neutral selection grammar. Recommended v0.1 direction:

1. exact canonical tuple-origin list for selected unpartitioned `localStorage` origins;
2. each selected origin contributes its complete admitted `localStorage` map;
3. exact canonical stored-domain list for selected unpartitioned cookies;
4. every selected cookie entry for the selected exact stored domains participates in the authoritative set;
5. no regex, glob, suffix match, vendor callback, backend-native query language, or runtime code;
6. missing, extra, transformed, or scope-shifted in-scope state is non-equivalent.

**BPR-005: OPEN.**

## BPR-006 — Portable settlement witness

### Finding

There is no portable universal browser-idle condition. Sleep windows, `networkidle`, or vendor queue inspection are insufficient protocol evidence.

### Required closure

AEP-0011 must define a positive profile/scenario-bound settlement witness in which:

1. Core has closed admission of new Subject side effects;
2. all accepted pre-boundary mutations relevant to the selected authoritative state have reached a terminal outcome known to evaluator/control authority;
3. no accepted profile-relevant mutation remains unresolved;
4. authoritative projection is accepted only after that witness;
5. inability to establish the witness fails closed as unsettled rather than guessing with timeouts.

The witness applies to selected state and does not imply global animation/network/worker inactivity.

**BPR-006: OPEN.**

## BPR-007 — Lossless Web IDL `DOMString` canonical semantics

### Finding

Web Storage keys/values use Web IDL `DOMString`; exact UTF-16 code-unit sequences can include unmatched surrogates that common canonical JSON schemes reject or transform.

### Required closure

AEP-0011 must choose a language-neutral rule that is either:

1. a lossless representation of the exact admitted `DOMString` code-unit sequence; or
2. an explicit fail-closed unsupported rule for selected state outside the chosen canonical character domain.

Ordering/equality must be defined over the selected protocol representation and must not vary by JavaScript/Python/Java JSON-library behavior.

**BPR-007: OPEN.**

## BPR-008 — Excluded-state residual noninterference

### Finding

Excluded state such as Service Workers, Cache Storage, IndexedDB, permissions, extensions, preload scripts, profile residue, network policy, and credential state can still affect scenario behavior.

### Required closure

For every materially relevant excluded surface, AEP-0011 must require at least one of:

1. isolation/configuration proving noninterference with the verification claim;
2. immutable execution-identity/policy binding through existing Scenario/Fabric mechanisms; or
3. fail-closed declaration that Browser v0.1 is insufficient for that scenario dependency.

The base image must remain narrow, but narrowness cannot become a false reproducibility claim.

**BPR-008: OPEN.**

## BPR-009 — Chromium/Gecko/WebKit acceptance evidence matrix

### Finding

Browser portability claims require stronger cross-engine evidence before acceptance than was necessary for Draft-to-Proposed readiness.

### Required closure

Before acceptance-oriented re-review closes, evidence must cover Chromium, Gecko, and WebKit engine families for the selected semantics, including at minimum:

1. unpartitioned cookie identity and projection;
2. host-only versus domain-scoped cookie behavior;
3. `SameSite=Default` treatment and any restore restriction arising from temporal semantics;
4. admitted unpartitioned `localStorage` tuple-origin behavior;
5. rejection/non-admission of partitioned state into the base profile;
6. independent post-restore/reset projection;
7. settlement fail-closed behavior;
8. residual-state isolation assumptions used by the fixture.

This is an **AEP acceptance-evidence gate**, not a universal requirement that every future third-party conforming implementation support all three engine families.

**BPR-009: OPEN.**

## Historical design-document disposition

Draft-era portability/readiness documents remain useful provenance:

- `docs/design/alpha3-browser-resource-portability-audit.md`;
- `docs/design/alpha3-browser-resource-proposed-readiness-audit.md`;
- `docs/acceptance/alpha3-browser-draft-main-adoption.md`;
- `docs/acceptance/alpha3-browser-readiness-main-adoption.md`;
- `docs/acceptance/alpha3-aep-0011-proposed-decision.md`.

They document why the AEP became Proposed. They do not override later Formal Proposed Review decisions. When BPR edits are eventually incorporated into AEP-0011, any conflicting Draft-era wording must be explicitly treated as superseded provenance and must not be used to reintroduce rejected semantics into the future Spec/Schema/TCK.

## Acceptance gate

AEP-0011 is acceptance-ready only if all of the following are true:

1. BPR-001..BPR-009 decisions are incorporated into the AEP-0011 Proposed text — **NOT STARTED**;
2. ROADMAP and review/adoption metadata accurately reflect the Proposed/formal-review state — **PENDING**;
3. superseded Draft-era semantics are explicitly identified where necessary — **PENDING BLOCKER EDITS**;
4. required three-engine-family semantic evidence is reviewable — **PENDING**;
5. exact-head CI, Governance, Release Validation, and applicable portability/conformance gates are green — **PENDING FUTURE BLOCKER-RESOLUTION HEAD**;
6. an acceptance-oriented exact-head protocol re-review finds no remaining semantic blocker — **PENDING**;
7. the protocol maintainer separately and explicitly authorizes `Proposed -> Accepted` — **NOT AUTHORIZED**.

Generic continuation does not satisfy item 7.

## Current conclusion

```text
AEP-0011 lifecycle: Proposed
Formal Proposed review: completed as review evidence
BPR-001..BPR-009: OPEN
Blocker-resolution protocol edits: NOT STARTED
Acceptance-oriented re-review: NOT READY
Accepted: NOT AUTHORIZED
Browser normative Spec/Schema/TCK: NOT AUTHORIZED
Browser conformance harness: NOT AUTHORIZED
Playwright/reference runtime: NOT AUTHORIZED
```

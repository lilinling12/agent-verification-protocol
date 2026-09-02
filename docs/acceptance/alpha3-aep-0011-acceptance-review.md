# Alpha 3 AEP-0011 Acceptance-Oriented Exact-Head Protocol Re-Review

Status: **REVIEW BLOCKED — NEW SEMANTIC BLOCKER BPR-010 IDENTIFIED**

AEP: `rfcs/AEP-0011-browser-resource-profile.md` (`Proposed`)

Review baseline: PR #109 exact head `66eb158952ff0b90e388f43ee3bae38bd750efbf`

Parent protocol-resolution head: `4da88bd5fdbaca8fa479b6128e20511e8355d207`

Evidence baseline: `103c049c51d199c3c744f675283aa8480ca20774`

Evidence disposition: `docs/acceptance/alpha3-browser-aep0011-acceptance-evidence-disposition.md`

Formal Proposed review: `docs/design/alpha3-browser-resource-formal-proposed-review.md`

Blocker ledger: `docs/design/alpha3-browser-resource-proposed-review-blockers.md`

## 1. Review question

This review asks one narrow lifecycle question:

> After incorporation of BPR-001..BPR-009 decisions and completion of the required Chromium/Gecko/WebKit acceptance evidence, does AEP-0011 contain any remaining semantic ambiguity that would allow downstream Spec/Schema/TCK or a reference implementation to choose protocol meaning rather than merely encode it?

A green evidence matrix is not sufficient by itself. The review therefore re-checks state identity, canonical bytes/digests, selection/equality, restore fidelity, settlement, residual-state handling, authority separation, and cross-contract composition.

This review does not authorize `Proposed -> Accepted`, merge, normative Browser work, or runtime implementation.

## 2. Exact-head gate state

The review baseline `66eb158952ff0b90e388f43ee3bae38bd750efbf` completed all twelve applicable pull-request workflows successfully:

- CI #686 — run `33329177434`;
- Governance #757 — run `33329177436`;
- Relational Parity #79 — run `33329177413`;
- Browser Acceptance Evidence #37 — run `33329177426`;
- Browser Selection Evidence #24 — run `33329177450`;
- Browser Cookie Partition Evidence #34 — run `33329177401`;
- Browser Settlement Evidence #30 — run `33329177418`;
- Browser Recovery Residual Evidence #12 — run `33329177404`;
- Browser Shipping Partition Evidence #5 — run `33329177422`;
- Browser Shipping Residual Evidence #4 — run `33329177412`;
- Browser Shipping Cookie Fidelity Evidence #3 — run `33329177419`;
- Browser Shipping Cookie Provenance Evidence #2 — run `33329177405`.

The exact-head gates establish repository/evidence integrity for the reviewed head; they do not override semantic findings below.

## 3. Re-review of BPR-001..BPR-009

### BPR-001 / BPR-002

The public capability/profile identity is narrow and stable, and the localStorage boundary is explicitly limited to admitted unpartitioned tuple-origin state. No new blocker found.

### BPR-003

Cookie identity remains `(name, domain, hostOnly, path)`. The evidence stack proves both fail-closed handling of lossy browser-control serialization and a positive independently reviewable evaluator/control provenance path across Chromium, Gecko, and WebKit. Provenance remains Evidence rather than portable state identity. No new blocker found in the projection authority rule.

### BPR-004

`SameSite=Default` remains distinct from explicit Lax, temporal-sensitive restore fails closed when historical behavior cannot be established, and a positive temporally eligible class demonstrates `STATE_EQUIVALENT` restore/reset with independent reprojection. No new blocker found in temporal fidelity semantics.

### BPR-005

The selection grammar is finite, exact, duplicate-free, vendor-neutral, immutable, and complete-set based. The semantic membership rule is closed. However, the re-review found a separate canonical-collection-ordering issue described as BPR-010 below.

### BPR-006 / BPR-008

Positive settlement witness and residual-state noninterference/fail-closed rules compose with Core/Fabric lifecycle and execution identity without introducing a second lifecycle or inflating state equivalence. No new blocker found.

### BPR-007

Web Storage DOMString representation and key ordering are explicitly defined over unsigned UTF-16 code units. This rule is sufficiently precise for the selected key/value surface. No new blocker found in DOMString semantics themselves.

### BPR-009

The required three-engine evidence matrix is complete and reviewable. Shipping/native evidence prevents Playwright privacy configuration from masquerading as shipping-product behavior. No new engine-matrix blocker found.

## 4. Cross-contract review

### Environment / SnapshotRef

AEP-0011 reuses Environment-owned SnapshotRef ownership, stale/foreign rejection, and evaluator projection identity. Browser-native handles/profile paths are not promoted into SnapshotRef or state identity. No conflict found.

### Environment Fabric

Resource Capability versus Subject Capability remains separated. Browser execution identity and identity Artifacts compose through existing Fabric mechanisms rather than being embedded indiscriminately into BrowserStateImage. No conflict found.

### Core

The Browser settlement witness specializes the existing `QUIESCING` boundary and does not create a second Episode lifecycle. Unsettled state remains infrastructure/Validity information rather than automatic Task Verdict failure. No conflict found.

### Security / Evidence

Evaluator/control browser authority, credentials, provenance, hidden instrumentation, and evidence remain outside Subject authority unless separately granted. Provenance evidence used to establish otherwise-lossy cookie identity is not promoted into Subject-visible or portable state identity. No conflict found.

## 5. New blocker — BPR-010 canonical collection ordering / digest determinism

### Finding

AEP-0011 defines content-addressed Browser state identity but does not fully define the canonical order of collection-valued fields that participate in those bytes.

The current text establishes:

- a finite duplicate-free list of selected localStorage origins;
- a finite duplicate-free list of selected cookie stored domains;
- `BrowserStateManifest` as content-addressed interpretation identity;
- `BrowserStateImage` containing `cookies[]` and `origins[]`;
- exact localStorage key ordering by unsigned UTF-16 code units;
- canonical BrowserStateImage/state digests.

It also says selection lists are "canonicalized", but does not define the canonical collection order itself.

Missing protocol decisions include at least:

1. the canonical order of Manifest localStorage-origin selections;
2. the canonical order of Manifest cookie-domain selections;
3. the canonical order of `BrowserStateImage.origins[]`;
4. the canonical order of `BrowserStateImage.cookies[]` over the portable cookie identity tuple.

### Why this is semantic, not downstream schema detail

JSON canonicalization/JCS canonicalizes object member names and scalar encodings but preserves array order. Therefore two implementations can satisfy all currently stated Browser selection/equality membership rules and still emit different exact Manifest/Image bytes solely because they enumerate equivalent collections in different orders.

That difference propagates into:

- Manifest Artifact digest;
- `manifestDigest` binding in BrowserStateImage;
- BrowserStateImage Artifact/state digest;
- baseline/runtime snapshot identity;
- cross-implementation parity.

A future Schema or TCK cannot choose one ordering rule without creating new protocol semantics. Doing so would invert the repository authority direction.

AEP-0010 provides the relevant accepted precedent: profile-defined collection ordering is fixed before JCS serialization rather than delegated to backend enumeration order.

### Required protocol closure

Before acceptance-oriented review can close, AEP-0011 must define deterministic collection ordering at the protocol level. The resolution must at minimum specify:

- canonical ordering for exact origin-selection strings;
- canonical ordering for exact stored-cookie-domain selection strings;
- canonical ordering for `origins[]` in BrowserStateImage;
- canonical ordering for `cookies[]` by the portable cookie identity tuple, including an unambiguous comparator for `hostOnly` and textual identity components;
- that backend/browser enumeration order and insertion order are non-authoritative;
- how noncanonical collection order is handled before content-addressed identity is computed.

The exact future schema field names remain downstream work; the ordering semantics do not.

### Required executable evidence

The acceptance evidence should add a provider-neutral negative/control case proving that logically identical selections/state presented in different enumeration orders cannot yield different accepted canonical identity. The case must not obtain its expected ordering from Playwright/WebDriver/browser enumeration.

**BPR-010: OPEN — ACCEPTANCE SEMANTIC BLOCKER.**

## 6. Review disposition

The evidence gate is materially complete, but the protocol is not yet acceptance-ready because BPR-010 allows content-addressed identity to depend on unspecified collection enumeration order.

The correct lifecycle disposition is therefore:

```text
BPR-001..BPR-009: prior decisions/evidence remain closed for this review
BPR-010: OPEN semantic blocker
Acceptance-oriented review: BLOCKED
AEP-0011: Proposed
Proposed -> Accepted: NOT AUTHORIZED
Browser normative Spec/Schema/TCK/runtime: NOT AUTHORIZED
```

This is not a request to weaken content addressing or make list order semantically significant. The portable protocol must instead make canonical collection order explicit before downstream normative closure.

## 7. Next governed work

1. incorporate a narrow BPR-010 canonical-ordering decision into AEP-0011;
2. add focused provider-neutral executable evidence/negative controls for permutation-invariant canonical identity;
3. run exact-head CI/Governance/applicable Browser evidence;
4. repeat the acceptance-oriented exact-head semantic review;
5. only if no semantic blocker remains, request a **separate explicit** protocol-maintainer `Proposed -> Accepted` decision.

Generic continuation does not authorize step 5. Merge authorization remains separate.

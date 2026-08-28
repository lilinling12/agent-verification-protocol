# AEP-0011 Draft → Proposed Lifecycle Decision

Status: **AUTHORIZED — PROPOSED CANDIDATE UNDER EXACT-HEAD REVIEW**

Decision target: `rfcs/AEP-0011-browser-resource-profile.md`

Decision baseline: `main@e2159b1daba4dc214b5dc05c233df28afa328a99`

Prepared: 2026-08-29

Lifecycle authorization: **2026-08-29 — protocol maintainer explicitly authorized `AEP-0011 Draft → Proposed`.**

## Decision

The protocol maintainer explicitly authorized the following lifecycle proposition:

> **Advance AEP-0011 from `Draft` to `Proposed` for formal protocol review.**

This authorization permits the focused PR #106 lifecycle mutation only. It does not
by itself merge the candidate into `main`.

Until PR #106 is separately authorized for squash merge and the resulting exact-main
commit passes required post-merge validation, `main` continues to carry AEP-0011 as
`Draft`. The branch candidate may truthfully carry `Status: Proposed` because that
is the exact lifecycle mutation currently under review.

`Proposed` means only that the design is sufficiently complete for formal protocol
review. It does not mean the design is Accepted, normative, released, or approved
for runtime implementation.

## Governance basis

`GOVERNANCE.md` defines the relevant lifecycle states:

- `Draft` — active design work; not normative;
- `Proposed` — sufficiently complete for protocol review;
- `Accepted` — approved direction; implementation may proceed;
- `Final` — normative text and required conformance coverage are merged and
  released.

The repository's authority direction remains:

```text
AEP lifecycle decision
  -> Normative specification
  -> Schema
  -> TCK / conformance
  -> Reference implementation
```

The lifecycle transition does not invert that direction. In particular, Playwright,
WebDriver BiDi implementations, browser-engine behavior, profile directories,
automation handles, or reference-runtime code cannot establish portable Browser
semantics by precedent.

## Main-adopted evidence chain

### 1. Draft problem/scope baseline

PR #100 established AEP-0011's Browser Resource problem/scope and standards-analysis
baseline.

- reviewed exact head: `54ed3f132b4e681362271470d758a58c620a2d07`;
- authorized squash merge: `8f0c37e34202066ed79f8aa420a9939dd79cc5d1`;
- exact-main CI #622 / run `33116957396` — **SUCCESS**;
- exact-main Relational Parity #15 / run `33116957406` — **SUCCESS**.

That work deliberately left BR-BR-001..BR-BR-010 open and AEP-0011 in `Draft`.

### 2. Browser portability audit

PR #103 adopted the implementation-independent Browser portability audit.

- authorized squash merge: `ee876088bf53c82730b98dc74bfbc2e87f7aebb4`;
- exact-main CI #628 / run `33134651349` — **SUCCESS**;
- exact-main Relational Parity #21 / run `33134651336` — **SUCCESS**.

The audit bounded the base authoritative state and portability model without
introducing Browser Spec/Schema/TCK or implementation code.

### 3. AEP reconciliation and Proposed-readiness audit

PR #104 reconciled the portability decisions into AEP-0011 and added the dedicated
Draft → Proposed readiness audit.

Reviewed exact head:

`ae2cc0dfa42a476b1949611fbd201e9ce36f69a4`

Formal review `5048566230` concluded:

**REVIEW-CLOSED — PROPOSED-ELIGIBILITY EVIDENCE IS COHERENT FOR THIS EXACT HEAD.**

Exact-head evidence:

- CI #629 / run `33148952559` — **SUCCESS**;
- Governance #695 / run `33148952556` — **SUCCESS**;
- Relational Parity #22 / run `33148952557` — **SUCCESS**;
- Ready-state Governance #696 / run `33149074249` — **SUCCESS**;
- unchanged-head Governance #697 / run `33149121756` — **SUCCESS**;
- unresolved inline review threads — none.

PR #104 was explicitly authorized for squash merge and adopted into `main` at:

`69f3d91a9197f159eb0b5d77418f01b956aa17ff`

Exact-main validation:

- CI #630 / run `33149341398` — **SUCCESS**;
- Relational Parity #23 / run `33149341383` — **SUCCESS**.

The readiness audit's conclusion is:

**AEP-0011 IS READY TO MOVE FROM `Draft` TO `Proposed` FOR FORMAL PROTOCOL REVIEW.**

### 4. Main-adoption reconciliation

PR #105 recorded the main-adopted Proposed-readiness baseline and reconciled the
Browser ROADMAP evidence while preserving the lifecycle boundary.

Reviewed exact head:

`19bfaaccd52d6be0a61ba916eb3029ba84493e63`

Exact-head evidence:

- CI #631 / run `33150653985` — **SUCCESS**;
- Governance #698 / run `33150653980` — **SUCCESS**;
- Release Validation #96 / run `33150653969` — **SUCCESS**;
- Relational Parity #24 / run `33150654000` — **SUCCESS**;
- focused review `5048751200` — **REVIEW-CLOSED**;
- Ready-state Governance #699 / run `33150761945` — **SUCCESS**;
- subsequent unchanged-head Governance #700 / run `33150807517` — **SUCCESS**.

After explicit squash authorization, PR #105 was adopted into `main` at:

`e2159b1daba4dc214b5dc05c233df28afa328a99`

Exact-main validation:

- CI #632 / run `33212353304` — **SUCCESS**;
- Relational Parity #25 / run `33212353330` — **SUCCESS**.

### 5. Decision-preparation exact-head evidence

PR #106 first froze this decision record without mutating AEP-0011 or ROADMAP.

Preparation exact head:

`bdf483b98294cb11f49f7a96bfcbc2f4aaf5684b`

Exact-head evidence before lifecycle authorization:

- CI #633 / run `33213189621` — **SUCCESS**;
- Governance #701 / run `33213189552` — **SUCCESS**;
- Relational Parity #26 / run `33213189608` — **SUCCESS**;
- focused preparation review `5055271284` — decision-preparation content review closed;
- unresolved inline review threads — none.

This evidence verified the decision-preparation artifact only. Because lifecycle
authorization causes a new branch head, it cannot substitute for the required
post-authorization exact-head gates and lifecycle review.

## Draft → Proposed eligibility assessment

| Criterion | Result | Evidence |
|---|---|---|
| Written interoperability problem and bounded scope | PASS | AEP-0011 + PR #100 |
| Parent-authority composition is explicit | PASS | AEP-0011 + AEP-0009 reuse analysis |
| Portable Browser resource boundary is reviewable | PASS | portability audit + reconciled AEP |
| Authoritative state surface is closed | PASS | selected unpartitioned cookies + selected tuple-origin `localStorage` |
| Cookie/origin identity semantics are explicit | PASS | BR-BR-001/002 closure |
| Snapshot/reset/restore fidelity is bounded | PASS | `STATE_EQUIVALENT`; `EXACT` forbidden |
| State / Evidence / execution identity separation | PASS | reconciled AEP |
| Subject / Evaluator / Control authority separation | PASS | Security/Fabric composition |
| Operation-settlement semantics are reviewable | PASS | no universal `network idle`; selected-state settlement boundary |
| Executable implementation-independent conformance strategy exists | PASS | real-browser, backend-name-neutral TCK strategy |
| Draft blockers BR-BR-001..BR-BR-010 are resolved | PASS | Proposed-readiness audit §22 |
| Alternatives and compatibility impact are documented | PASS | AEP alternatives + additive compatibility boundary |
| Release/version assignment is intentionally deferred | PASS | release state remains development / `0.3.1.dev0` |
| Transitional backend-first implementation is rejected | PASS | readiness audit + OSS engineering policy |

No remaining finding requires Schema, TCK, or reference code to invent portable
semantics merely to make the AEP reviewable.

## Semantics carried into formal Proposed review

Formal protocol review must challenge — not silently assume — the following
Proposed design choices:

1. one isolated browser-session resource rather than page/process/native-handle
   identity;
2. one cohesive Browser state capability rather than a `supports_*` bag;
3. selected unpartitioned cookies plus selected tuple-origin `localStorage` as the
   complete base authoritative state surface;
4. cookie entry identity `(name, domain, hostOnly, path)` and the selected stored
   cookie attributes;
5. non-opaque tuple-origin identity and WHATWG origin serialization for
   `localStorage`;
6. explicit exclusion of partitioned cookies, `sessionStorage`, topology/history,
   IndexedDB, Service Worker/Cache, WebAuthn private state, and other non-base
   surfaces;
7. `STATE_EQUIVALENT` as the only successful Browser v0.1 restore fidelity;
8. profile-relevant state settlement rather than universal network-idle/sleep
   correctness;
9. separation of Resource Capability from Subject browser-action authority;
10. multi-engine execution as AVP reference portability evidence rather than a
    universal requirement on every third-party conforming implementation.

These items are **review inputs**, not Accepted conclusions. Formal Proposed review
may retain, narrow, amend, or reject them.

## Open questions for formal Proposed review

1. Should the final capability/profile naming remain
   `browser.session-state` / `avp-browser-state-v0.1`?
2. Is `(name, domain, hostOnly, path)` the correct portable unpartitioned-cookie
   entry identity?
3. Is restricting base `localStorage` to non-opaque tuple origins appropriately
   conservative?
4. Should the first closed selection grammar use only explicit enumeration or a
   small declarative scope vocabulary?
5. Is `STATE_EQUIVALENT` the right and only successful base restore claim?
6. Is the selected-state settlement rule sufficiently testable without defining
   browser event-loop/network-idle behavior?
7. Is the two-independent-engine-family AVP reference evidence threshold
   sufficient to protect portability?
8. Are the base exclusions the correct v0.1 interoperability tradeoff?

A question becoming a semantic blocker during Proposed review must be resolved in
the AEP before any later `Proposed -> Accepted` decision.

## Authorized status-mutation scope

The protocol-maintainer authorization permits PR #106 to:

1. change AEP-0011 lifecycle metadata and stale Draft-only lifecycle wording to
   `Proposed` without altering the reviewed portable design semantics;
2. update `ROADMAP.md` to mark only
   `AEP-0011 status advanced to Proposed for formal protocol review` complete and
   record the lifecycle decision boundary;
3. update this decision record with the explicit authorization and exact branch
   evidence;
4. run all applicable exact-head CI/Governance/Release Validation/Relational
   Parity gates;
5. perform a focused exact-head lifecycle review verifying the final delta is
   lifecycle/evidence-only.

The authorization does **not** authorize merge. PR #106 still requires a separate
explicit squash-merge authorization after final exact-head gates, review, Ready
state, and no-drift checks succeed.

## Non-authorization boundary

This lifecycle authorization does **not** authorize:

- AEP-0011 `Proposed -> Accepted` or `Accepted -> Final`;
- Browser normative specification or requirement-index adoption;
- Browser JSON Schema adoption;
- Browser TCK/profile registration;
- backend-neutral Browser harness implementation;
- Playwright, Selenium, WebDriver, CDP, BiDi, Chromium, Firefox, or WebKit
  implementation as official AVP behavior;
- AEP-0009 or AEP-0010 lifecycle changes;
- assignment of Browser work to `0.3.1`;
- release-development state changes;
- tag, GitHub Release, package-index publication, signing, or attestation;
- physical repository split or plugin-framework introduction;
- merge of PR #106.

Release provenance remains:

```text
mode: development
sourceVersion: 0.3.1.dev0
nextRelease: 0.3.1
```

## Current gate

**AUTHORIZED — STATUS-MUTATION CANDIDATE MUST PASS EXACT-HEAD REVIEW AND GATES.**

After the final lifecycle-mutation head is review-closed and all applicable gates
succeed, PR #106 may become Ready. Ready state is not merge authorization. A
separate explicit squash-merge authorization is required before `main` adopts the
`Proposed` lifecycle state.

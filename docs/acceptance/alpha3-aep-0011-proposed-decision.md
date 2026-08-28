# AEP-0011 Draft → Proposed Lifecycle Decision Preparation

Status: **DECISION PENDING — PROPOSED ELIGIBLE, NOT YET AUTHORIZED**

Decision target: `rfcs/AEP-0011-browser-resource-profile.md`

Decision-preparation baseline: `main@e2159b1daba4dc214b5dc05c233df28afa328a99`

Prepared: 2026-08-29

## Purpose

This record prepares the separately governed protocol-maintainer decision on whether
AEP-0011 — Browser Resource Profile v0.1 should advance from `Draft` to `Proposed`.

It exists to make the lifecycle decision auditable before any status mutation is
performed. It does **not** itself change AEP-0011's lifecycle state. Until an
explicit protocol-maintainer authorization is recorded and the corresponding
status change is adopted into `main`, AEP-0011 remains **Draft**.

The decision under consideration is intentionally narrow:

> Advance AEP-0011 from `Draft` to `Proposed` so the reconciled Browser Resource
> design can enter formal protocol review.

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

A lifecycle transition must not invert that direction. In particular, Playwright,
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

The audit explicitly states that this is eligibility evidence only and that a
separate lifecycle decision is still required.

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

The current `main` baseline therefore contains the complete reviewed readiness
record while AEP-0011 still remains `Draft`.

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

If the lifecycle transition is later explicitly authorized and adopted, formal
protocol review should challenge — not silently assume — the following reviewed
Draft choices:

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

The readiness audit intentionally carries the following challenge questions into
formal review:

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

## Decision proposition

The lifecycle proposition awaiting explicit protocol-maintainer authorization is:

> **Advance AEP-0011 from `Draft` to `Proposed` for formal protocol review.**

If explicitly authorized, the status-mutation work must remain limited to:

1. changing AEP-0011 lifecycle metadata and stale Draft-only lifecycle wording to
   `Proposed` without altering the reviewed portable design semantics;
2. updating `ROADMAP.md` to mark only
   `AEP-0011 status advanced to Proposed for formal protocol review` complete and
   to record exact decision evidence;
3. making this decision record effective, with the exact authorization and
   reviewed status-mutation head attributable in PR history;
4. running all applicable exact-head CI/Governance/Release Validation/Relational
   Parity gates;
5. performing a focused exact-head lifecycle review that verifies the delta is
   lifecycle/evidence-only;
6. requiring a **separate explicit squash-merge authorization** before the status
   transition is adopted into `main`;
7. requiring exact-main post-merge validation before the lifecycle work unit is
   considered fully closed.

No semantic rewrite should be bundled into the lifecycle status mutation. Any
semantic change discovered necessary during review belongs to the subsequent
formal Proposed-review work unit and invalidates assumptions that the transition
is metadata-only.

## Non-authorization boundary

This preparation record does **not** authorize or perform:

- AEP-0011 `Draft -> Proposed`;
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
- merge of the current preparation PR.

Release provenance remains:

```text
mode: development
sourceVersion: 0.3.1.dev0
nextRelease: 0.3.1
```

No lifecycle decision may be inferred merely from the existence of this file, a
successful CI run, GitHub Ready state, or a generic instruction to continue work.

## Current gate

**DECISION PENDING — EXPLICIT AEP-0011 `Draft -> Proposed` AUTHORIZATION REQUIRED.**

The next action after review-closing this preparation artifact is a separate,
explicit protocol-maintainer authorization of the lifecycle proposition. Only
then may the branch mutate AEP-0011/ROADMAP to the Proposed candidate state.

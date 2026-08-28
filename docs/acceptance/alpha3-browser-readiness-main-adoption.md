# Alpha 3 Browser Resource Proposed-Readiness Main-Adoption Reconciliation

Status: **MAIN ADOPTED — PROPOSED-READINESS BASELINE CLOSED**

Main baseline: `69f3d91a9197f159eb0b5d77418f01b956aa17ff`

## Purpose

This document reconciles repository governance after PR #104 adopted the reviewed
AEP-0011 Browser Resource Profile v0.1 portability decisions and Draft -> Proposed
readiness evidence into `main`.

This is an adoption-evidence record only. It does not advance AEP-0011 beyond
`Draft`, perform the separately governed `Draft -> Proposed` lifecycle transition,
create Browser Resource normative Spec/Schema/TCK authority, or authorize a
Playwright/browser runtime implementation.

## Adopted work unit

PR #104: `docs(alpha3): reconcile browser resource profile`

Reviewed exact PR head:

`ae2cc0dfa42a476b1949611fbd201e9ce36f69a4`

Authorized squash merge commit on `main`:

`69f3d91a9197f159eb0b5d77418f01b956aa17ff`

The adopted source slice changes exactly:

- `rfcs/AEP-0011-browser-resource-profile.md`;
- `docs/design/alpha3-browser-resource-proposed-readiness-audit.md`.

`ROADMAP.md`, normative Spec, requirement index, schemas, TCK, reference runtime,
package metadata, workflow definitions, and release-development state were
intentionally unchanged by PR #104 so branch-local readiness could not be
mistaken for main adoption or lifecycle advancement.

## Adopted Browser v0.1 design boundary

The main-adopted Draft now closes BR-BR-001..BR-BR-010 as design blockers for
Proposed-readiness review. The reviewed direction is deliberately narrow:

- one isolated browser-session resource;
- one cohesive candidate capability, with final protocol naming deferred to
  lifecycle/downstream normative review;
- authoritative base logical state limited to selected **unpartitioned HTTP
  cookies** and selected **origin-scoped `localStorage`**;
- cookie entry identity `(name, domain, hostOnly, path)` with behaviorally
  relevant persistence/expiry/Secure/HttpOnly/SameSite semantics preserved;
- `localStorage` identity based on non-opaque WHATWG tuple origins and portable
  origin serialization rather than vendor/native storage identifiers;
- partitioned cookies, sessionStorage/topology/history, IndexedDB, Service
  Worker/Cache, WebAuthn private state, downloads, DOM/rendering/traces and
  other diagnostic/evidence surfaces excluded from base authoritative state;
- state identity separated from execution-relevant browser identity and from
  Evidence;
- snapshot/reset/restore requiring independent complete evaluator reprojection;
- successful base restore fidelity exactly `STATE_EQUIVALENT`; `EXACT` is
  prohibited for this base profile;
- no universal `network idle` or sleep-based settling rule;
- Resource Capability does not grant a universal Subject browser automation API;
- credential-bearing selected state remains authoritative while visibility and
  secret handling remain governed by Evaluator/Security boundaries;
- real-browser, language-neutral, backend-name-neutral conformance strategy with
  metadata-identical negative controls;
- multi-engine execution is a reference portability evidence gate, not a
  requirement that every third-party implementation support multiple engines.

These are reviewable AEP design semantics, not yet released normative Browser
Resource requirements.

## Proposed-readiness evidence

`docs/design/alpha3-browser-resource-proposed-readiness-audit.md` concludes:

**READY FOR PROTOCOL REVIEW — PROPOSED ELIGIBLE**

That conclusion means the Draft design is sufficiently complete to be considered
for a separately governed `Draft -> Proposed` lifecycle decision. It does not
perform that decision automatically.

The audit records the remaining downstream details as encoding/API choices that
must follow, rather than invent, the reviewed semantics. Examples include final
capability spelling, exact JSON field names/media types, the closed Manifest
selection grammar syntax, canonical wire representation details, requirement/TCK
identifiers, language SPI names, and implementation mechanics.

## Exact-head review and pre-merge gates

Formal exact-head review `5048566230` was anchored to
`ae2cc0dfa42a476b1949611fbd201e9ce36f69a4` and concluded:

**REVIEW-CLOSED — PROPOSED-ELIGIBILITY EVIDENCE IS COHERENT FOR THIS EXACT HEAD.**

The review confirmed, among other things, lifecycle authority, backend-independent
origin/cookie identity, state/Evidence/execution-identity separation, conservative
restore fidelity, portable settling semantics, Subject/Evaluator/control trust
boundaries, multi-engine scope, compatibility/release boundaries, and the absence
of transitional Playwright-first architecture.

At that exact head:

- CI #629 / run `33148952559` — **SUCCESS**;
- Governance #695 / run `33148952556` — **SUCCESS**;
- Relational Parity #22 / run `33148952557` — **SUCCESS**;
- Ready-state Governance #696 / run `33149074249` — **SUCCESS**;
- subsequent unchanged-head Governance #697 / run `33149121756` — **SUCCESS**;
- unresolved inline review threads — none.

No Release Validation run is claimed for PR #104 because the changed paths did
not trigger that workflow's path filter. Evidence is recorded only for gates that
actually executed.

## Authorized merge and exact-main validation

The protocol maintainer explicitly authorized **squash merge PR #104** on
2026-08-28.

Before merge, the live guard confirmed:

- `main` remained `ee876088bf53c82730b98dc74bfbc2e87f7aebb4`;
- PR #104 remained open, Ready, mergeable, and at exact head
  `ae2cc0dfa42a476b1949611fbd201e9ce36f69a4`;
- no base drift was present;
- exact-head CI/Governance/Parity evidence remained successful;
- review `5048566230` remained anchored to the exact head;
- unresolved review threads remained zero.

The merge used `expected_head_sha=ae2cc0dfa42a476b1949611fbd201e9ce36f69a4`
to fail closed if the reviewed head moved.

GitHub produced exact main commit:

`69f3d91a9197f159eb0b5d77418f01b956aa17ff`

with parent:

`ee876088bf53c82730b98dc74bfbc2e87f7aebb4`

Exact-main push validation then completed successfully:

- CI #630 / run `33149341398` — **SUCCESS**;
- Relational Parity #23 / run `33149341383` — **SUCCESS**.

Relational Parity #23 executed both real paired canonical-parity lanes:

- PostgreSQL 17.11 + MySQL 8.4.11;
- PostgreSQL 18.6 + MySQL 9.7.2.

This closes PR #104 itself as a main-adopted work unit. It does not create Browser
conformance evidence because Browser normative Spec/Schema/TCK do not yet exist.

## ROADMAP reconciliation

With this exact-main evidence, the following Browser Resource roadmap milestones
may be marked complete:

- browser portability and Proposed-readiness audit;
- close BR-BR-001..BR-BR-010 Draft -> Proposed blockers;
- reconcile AEP-0011 and complete Draft -> Proposed readiness audit.

The next milestone remains intentionally incomplete:

`AEP-0011 status advanced to Proposed for formal protocol review`

That lifecycle transition requires a separate protocol-maintainer governance
decision. Main adoption of Proposed-readiness evidence is not implicit lifecycle
authorization.

## Open-source implementation-quality boundary

No Browser implementation architecture is frozen by this adoption record.
Downstream work must continue to follow the repository engineering rule:

> Split responsibilities; do not abstract protocol semantics.

In particular:

- normative Browser semantics must be public before implementation precedent can
  affect conformance;
- portable TCK code must not import Playwright, Selenium, CDP, WebDriver BiDi, or
  another vendor/backend to determine expected behavior;
- privileged fixture/reset/snapshot/restore authority must remain structurally
  separate from Subject-visible operations;
- browser-provider dependencies must remain optional and must not make the base
  package install/import download browser binaries;
- vendor/native handles must not become portable identity;
- a speculative `BaseBrowserBackend`, catch-all `BrowserAdapter`, or plugin
  framework must not be introduced before a stable multi-consumer contract exists;
- mandatory behavioral TCK cases must execute real browser behavior, not pass
  through metadata self-declaration;
- future architecture tests should machine-enforce dependency direction when the
  concrete Browser contract/packages exist.

Exact package/module names remain deferred until normative Browser authority and
backend-neutral harness responsibilities are reviewed.

## Lifecycle and release boundary

After this reconciliation:

- AEP-0011 remains **Draft, not Proposed**;
- BR-BR-001..BR-BR-010 are closed as Draft design blockers, not as Accepted/Final
  protocol requirements;
- AEP-0009 remains **Accepted, not Final**;
- AEP-0010 remains **Accepted, not Final**;
- Browser normative Spec/requirement-index/Schema/TCK remain unadopted;
- browser backend-neutral harness and Playwright/runtime implementation remain
  unauthorized;
- release provenance remains `development` with source version `0.3.1.dev0`;
- `0.3.1` is not selected for Browser Resource publication by this work;
- no tag, GitHub Release, package-index publication, signing, or attestation is
  authorized.

## Acceptance conclusion

**MAIN ADOPTED — PROPOSED-READINESS BASELINE CLOSED.**

PR #104 is fully closed at exact main
`69f3d91a9197f159eb0b5d77418f01b956aa17ff` with exact-main CI #630 and
Relational Parity #23 successful.

The next separately governed protocol work is the AEP-0011 `Draft -> Proposed`
lifecycle decision and formal Proposed review. This document does not authorize
that transition or any downstream Browser normative/runtime implementation.

# AEP-0012 Draft → Proposed Lifecycle Decision

Status: **AUTHORIZED — PROPOSED LIFECYCLE CANDIDATE, MAIN ADOPTION PENDING**

Decision target: `rfcs/AEP-0012-network-control-resource-profile.md`

Decision baseline: `main@48d1bae70ec95c9208fc4e71786823b64a1e7495`

Authorized: 2026-09-03

Preparation review: `5094125418`

## Decision

The protocol maintainer explicitly authorized:

> **AEP-0012 Draft → Proposed**

The authorization permits the lifecycle-only mutation required to place AEP-0012
into `Proposed` for formal protocol review.

It does **not** authorize this PR's merge. `main` remains at the pre-transition
baseline until PR #135 is separately reviewed, made merge-eligible under repository
governance, and receives a separate explicit squash-merge authorization.

`Proposed` means that the reconciled Network Control design is sufficiently complete
for formal protocol review. It does not mean the design is Accepted, Final,
normative, released, or approved for downstream provider/reference implementation.

## Governance basis

`GOVERNANCE.md` defines:

- `Draft` — active design work; not normative;
- `Proposed` — sufficiently complete for protocol review;
- `Accepted` — approved direction; implementation may proceed;
- `Final` — normative text and required conformance coverage are merged and
  released.

The repository authority direction remains:

```text
AEP lifecycle decision
  -> Normative specification
  -> Schema
  -> TCK / conformance
  -> Reference implementation
```

The lifecycle transition must not invert that authority. Linux `tc/netem`,
Toxiproxy, firewall/routing mechanisms, Envoy, Istio/service-mesh objects, cloud
network-control APIs, native socket errors, provider handles, and future reference
adapters remain implementation/conformance evidence only.

## Main-adopted readiness evidence

The decision rests on the already adopted Network Control evidence chain.

### PR #130 — Draft problem/scope baseline

Main adoption:

`7f7f613c50520efb2b553d65d4bb85c0e777dc40`

Exact-main validation:

- CI #823 / `33609386257` — **SUCCESS**;
- Relational Parity #216 / `33609386265` — **SUCCESS**;
- Browser Reference #89 / `33609386244` — **SUCCESS**.

### PR #132 — portability audit

Main adoption:

`74b442a0ffd22f4da79b5d4abfd339d694fc2843`

Exact-main validation:

- CI #828 / `33618394305` — **SUCCESS**;
- Relational Parity #221 / `33618394375` — **SUCCESS**;
- Browser Reference #94 / `33618394321` — **SUCCESS**.

The audit resolved NC-BR-001..NC-BR-012 into explicit implementation-independent
Draft design choices while preserving AEP-0009/Environment authority and rejecting
provider-first protocol design.

### PR #133 — AEP reconciliation and Proposed-readiness

Reviewed exact head:

`fe7e356ae64faa0b8b69e9b0ef64c345f3793916`

Focused review `5088528789` /
`PRR_kwDOT09qic8AAAABL0zJlQ` concluded:

**REVIEW-CLOSED — PROPOSED-ELIGIBILITY EVIDENCE IS COHERENT FOR THIS EXACT HEAD.**

Exact-head gates included:

- Governance #966 / `33619764986` — **SUCCESS**;
- CI #829 / `33619765040` — **SUCCESS**;
- Relational Parity #222 / `33619765006` — **SUCCESS**;
- Browser Reference #95 / `33619765014` — **SUCCESS**;
- Governance #967/#968/#969 — **SUCCESS**;
- unresolved review threads — zero.

After explicit squash authorization, PR #133 was adopted into `main` at:

`2632935bef065b4d38e88f6df6b8cf0d620bfb3b`

Exact-main CI #830, Relational Parity #223, and Browser Reference #96 all passed.

The readiness audit concluded:

**AEP-0012 IS READY TO MOVE FROM Draft TO Proposed FOR FORMAL PROTOCOL REVIEW.**

### PR #134 — readiness main-adoption reconciliation

Reviewed exact head:

`6f770aff64d4f7ef48f385ba04efc0bb4d723aeb`

Focused review `5093728530` /
`PRR_kwDOT09qic8AAAABL5whEg` concluded:

**REVIEW-CLOSED — NETWORK CONTROL READINESS MAIN-ADOPTION RECONCILIATION IS COHERENT FOR THIS EXACT HEAD.**

Exact-head gates included Governance #970/#971/#972/#973, CI #831, Release
Validation #114, Relational Parity #224, and Browser Reference #97 — all
**SUCCESS**, with zero unresolved threads.

After explicit squash authorization, PR #134 was adopted into `main` at:

`48d1bae70ec95c9208fc4e71786823b64a1e7495`

Exact-main validation:

- CI #832 / `33670402185` — **SUCCESS**;
- Relational Parity #225 / `33670402249` — **SUCCESS**;
- Browser Reference #98 / `33670402306` — **SUCCESS**.

## Lifecycle-decision preparation closure

PR #135 first created a preparation-only candidate that changed exactly this
decision record and left AEP-0012/ROADMAP untouched.

Final preparation exact head:

`a85fb6b7e040f456936f1401d13416ef1845c649`

Preparation exact-head gates:

- Governance #975 / `33672894491` — **SUCCESS**;
- CI #834 / `33672894494` — **SUCCESS**;
- Relational Parity #227 / `33672894496` — **SUCCESS**;
- Browser Reference #100 / `33672894502` — **SUCCESS**.

Focused preparation review `5094125418` concluded:

**PREPARATION REVIEW CLOSED — AEP-0012 DRAFT → PROPOSED DECISION PREPARATION IS COHERENT FOR THIS EXACT HEAD.**

Unresolved inline review threads at preparation closure: zero.

Only after that closure did the protocol maintainer provide the explicit
`AEP-0012 Draft → Proposed` authorization recorded by this document.

## Authorized lifecycle-only mutation

The authorization permits only the following candidate changes:

1. `rfcs/AEP-0012-network-control-resource-profile.md`
   - `Status: Draft` → `Status: Proposed`;
   - add this lifecycle-decision link;
   - update stale Draft-only lifecycle wording required to make the document
     internally consistent;
   - do **not** change reviewed Network Control portable semantics.
2. `ROADMAP.md`
   - mark only `AEP-0012 status advanced to Proposed for formal protocol review`
     complete;
   - replace the now-stale statement that a Draft → Proposed decision is still
     pending with the recorded lifecycle authorization and candidate boundary;
   - keep formal Proposed review and every downstream milestone incomplete.
3. this decision record
   - record the explicit authorization, preparation evidence, and non-authorization
     boundary.

No other file or authority surface belongs in this lifecycle work unit.

## Semantic boundary retained for Proposed review

The lifecycle transition does not silently accept the reviewed Draft choices.
Formal Proposed review must still challenge the candidate semantics, including:

- controlled TCP path and fresh-connection exchange as the smallest mandatory base
  boundary;
- behavioral path-coverage proof rather than provider configuration presence;
- Environment ownership of fault identity/target/activation condition/clear;
- no-early-activation behavior for qualifying pre-trigger traffic;
- independent privileged data-plane activation settlement;
- mechanism-neutral `transport cut`;
- no base guarantee for pre-existing connections;
- independent clear/recovery settlement and no silent reactivation;
- deferral of exact latency and probabilistic loss;
- separation of DNS/TLS/HTTP/application/UDP semantics;
- reset as verified fault-free baseline rather than live-network snapshot/restore;
- provider-neutral execution identity;
- schedule secrecy and Subject/Evaluator/privileged-Control separation;
- execution-sensitive provider/language-neutral negative conformance;
- cross-mechanism AVP evidence where portability depends on mechanism independence.

Formal review may retain, narrow, amend, or reject these choices. A semantic change
found necessary there must be reviewed as an AEP semantic amendment; it cannot be
smuggled into the lifecycle-only transition.

## Security and provider boundary

This lifecycle decision does not weaken existing trust boundaries:

- future fault schedules remain Evaluator/Control-private unless separately
  governed;
- provider/admin credentials and privileged controls remain outside Subject
  context;
- payload/TLS interception is not implied by Network Control;
- provider-native topology, handles, errors, and object IDs remain non-portable
  diagnostics/evidence;
- portable TCK expectations must not branch on provider/platform names;
- speculative `BaseNetworkBackend`, catch-all adapter, provider/plugin registry, or
  broad `supports_*` capability bags remain unjustified.

Failure of Network Control infrastructure/control remains infrastructure/Validity
information rather than Agent Task Verdict failure by default.

## Release boundary

Release provenance remains unchanged:

```text
mode: development
latestPublished: 0.3.0 / v0.3.0
sourceVersion: 0.3.1.dev0
nextRelease: 0.3.1 / v0.3.1
```

The lifecycle decision does not assign Network Control to `0.3.1` and does not
authorize release-mode changes, tags, GitHub Releases, package-index publication,
signing, or attestation.

## Non-authorization boundary

This decision does **not** authorize:

- merge of PR #135;
- AEP-0012 `Proposed -> Accepted` or `Accepted -> Final`;
- completion of formal Proposed protocol review;
- Network Control normative Spec or requirement index;
- Network Control schema adoption;
- Network Control TCK/profile registration;
- backend-neutral Network Control conformance harness;
- Toxiproxy, Linux `tc/netem`, firewall/routing, Envoy, Istio/service-mesh, cloud
  network control, or another provider as protocol authority/reference behavior;
- controlled network-fault reference implementation;
- cross-mechanism implementation/acceptance work;
- AEP-0009, AEP-0010, or AEP-0011 lifecycle changes;
- release-development-state changes;
- tag/GitHub Release/package publication/signing/attestation;
- Gate/Evidence weakening;
- physical repository split or plugin-framework introduction.

## Current gate

**LIFECYCLE AUTHORIZED — EXACT-HEAD GATES AND FOCUSED LIFECYCLE REVIEW REQUIRED; MERGE AUTHORIZATION REMAINS SEPARATE.**

The lifecycle candidate must now pass all applicable exact-head gates and a focused
review that proves the delta is lifecycle/evidence-only. Any head mutation after
that review invalidates the review closure and requires revalidation.

Only after GitHub Ready-state/metadata governance is satisfied may PR #135 reach the
next hard boundary: a separate explicit squash-merge authorization for the exact
reviewed head.

# AEP-0012 Draft → Proposed Lifecycle Decision Preparation

Status: **DECISION PENDING — PROPOSED ELIGIBLE, NOT YET AUTHORIZED**

Decision target: `rfcs/AEP-0012-network-control-resource-profile.md`

Decision-preparation baseline: `main@48d1bae70ec95c9208fc4e71786823b64a1e7495`

Prepared: 2026-09-03

## Purpose

This record prepares the separately governed protocol-maintainer decision on whether
AEP-0012 — Network Control Resource Profile v0.1 should advance from `Draft` to
`Proposed`.

It exists to make the lifecycle decision auditable before any status mutation is
performed. It does **not** itself change AEP-0012's lifecycle state. Until an
explicit protocol-maintainer authorization is recorded and the corresponding
status change is separately reviewed and adopted into `main`, AEP-0012 remains
**Draft**.

The decision under consideration is intentionally narrow:

> **Advance AEP-0012 from `Draft` to `Proposed` so the reconciled Network Control
> Resource design can enter formal protocol review.**

`Proposed` means only that the design is sufficiently complete for formal protocol
review. It does not mean the design is Accepted, normative, released, assigned to a
release, or approved for provider/reference-runtime implementation.

## Governance basis

`GOVERNANCE.md` defines the relevant lifecycle states:

- `Draft` — active design work; not normative;
- `Proposed` — sufficiently complete for protocol review;
- `Accepted` — approved direction; implementation may proceed;
- `Final` — normative text and required conformance coverage are merged and
  released.

`GOVERNANCE.md` also requires a normative decision to have a recorded maintainer
decision in proposal/PR history. The current Network Control ROADMAP is more
specific: after the main-adopted readiness baseline, the next lifecycle item
requires a **separate explicit protocol-maintainer Draft → Proposed decision**.

The repository authority direction remains:

```text
AEP lifecycle decision
  -> Normative specification
  -> Schema
  -> TCK / conformance
  -> Reference implementation
```

A lifecycle transition must not invert that direction. In particular, Linux
`tc/netem`, Toxiproxy, firewall/routing rules, Envoy, Istio/service-mesh objects,
cloud network-control APIs, native socket errors, provider object identifiers, or a
reference-runtime adapter cannot establish portable Network Control semantics by
precedent.

## Main-adopted evidence chain

### 1. Draft problem/scope and standards baseline

PR #130 established AEP-0012's Network Control problem/scope and
standards/interoperability-analysis baseline.

Authorized squash merge:

`7f7f613c50520efb2b553d65d4bb85c0e777dc40`

Exact-main validation:

- CI #823 / run `33609386257` — **SUCCESS**;
- Relational Parity #216 / run `33609386265` — **SUCCESS**;
- Browser Reference #89 / run `33609386244` — **SUCCESS**.

That work deliberately left NC-BR-001..NC-BR-012 open and AEP-0012 in `Draft`.

### 2. Implementation-independent portability audit

PR #132 adopted the Network Control portability audit without changing AEP
lifecycle, ROADMAP status, normative Spec/Schema/TCK, or implementation code.

Authorized squash merge:

`74b442a0ffd22f4da79b5d4abfd339d694fc2843`

Exact-main validation:

- CI #828 / run `33618394305` — **SUCCESS**;
- Relational Parity #221 — **SUCCESS**;
- Browser Reference #94 / run `33618394321` — **SUCCESS**.

The audit resolved NC-BR-001..NC-BR-012 into explicit reconciliation decisions,
including the controlled-TCP-path boundary, deterministic fresh-connection exchange,
Environment-owned activation authority, independent data-plane settlement,
mechanism-neutral transport cut, clear/recovery semantics, conservative reset,
provider-neutral identity, security boundaries, and provider/language-neutral
execution-sensitive conformance direction.

The audit intentionally did not make those decisions normative or advance the AEP.

### 3. AEP reconciliation and Proposed-readiness audit

PR #133 reconciled the portability decisions into AEP-0012 and added the dedicated
Draft → Proposed readiness audit while keeping `Status: Draft`.

Reviewed exact head:

`fe7e356ae64faa0b8b69e9b0ef64c345f3793916`

Focused review `5088528789` / `PRR_kwDOT09qic8AAAABL0zJlQ` concluded:

**REVIEW-CLOSED — PROPOSED-ELIGIBILITY EVIDENCE IS COHERENT FOR THIS EXACT HEAD.**

Exact-head validation included:

- Governance #966 / run `33619764986` — **SUCCESS**;
- CI #829 / run `33619765040` — **SUCCESS**;
- Relational Parity #222 / run `33619765006` — **SUCCESS**;
- Browser Reference #95 / run `33619765014` — **SUCCESS**;
- Ready/metadata Governance #967 / run `33620341311` — **SUCCESS**;
- Ready-state Governance #968 / run `33666655550` — **SUCCESS**;
- final metadata Governance #969 / run `33667247699` — **SUCCESS**;
- unresolved inline review threads — none.

After explicit squash authorization, PR #133 was adopted into `main` at:

`2632935bef065b4d38e88f6df6b8cf0d620bfb3b`

Exact-main validation:

- CI #830 / run `33667291305` — **SUCCESS**;
- Relational Parity #223 / run `33667290799` — **SUCCESS**;
- Browser Reference #96 / run `33667291258` — **SUCCESS**.

The dedicated readiness audit concludes:

**AEP-0012 IS READY TO MOVE FROM Draft TO Proposed FOR FORMAL PROTOCOL REVIEW.**

That audit explicitly states that the conclusion is eligibility evidence only and
that AEP-0012 remains Draft until a separate explicit protocol-maintainer lifecycle
decision records the transition.

### 4. Proposed-readiness main-adoption reconciliation

PR #134 recorded the main-adopted readiness baseline and reconciled ROADMAP evidence
without changing AEP-0012 or any downstream normative/runtime surface.

Reviewed exact head:

`6f770aff64d4f7ef48f385ba04efc0bb4d723aeb`

Focused review `5093728530` / `PRR_kwDOT09qic8AAAABL5whEg` concluded:

**REVIEW-CLOSED — NETWORK CONTROL READINESS MAIN-ADOPTION RECONCILIATION IS COHERENT FOR THIS EXACT HEAD.**

Exact-head validation:

- Governance #970 / run `33668554914` — **SUCCESS**;
- CI #831 / run `33668554918` — **SUCCESS**;
- Release Validation #114 / run `33668554915` — **SUCCESS**;
- Relational Parity #224 / run `33668554913` — **SUCCESS**;
- Browser Reference #97 / run `33668554907` — **SUCCESS**;
- metadata Governance #971 / run `33669317437` — **SUCCESS**;
- Ready-state Governance #972 / run `33669977869` — **SUCCESS**;
- final metadata Governance #973 / run `33670361166` — **SUCCESS**;
- unresolved inline review threads — none.

After explicit squash authorization, PR #134 was adopted into `main` at:

`48d1bae70ec95c9208fc4e71786823b64a1e7495`

Exact-main validation:

- CI #832 / run `33670402185` — **SUCCESS**;
- Relational Parity #225 / run `33670402249` — **SUCCESS**;
- Browser Reference #98 / run `33670402306` — **SUCCESS**.

The current `main` baseline therefore contains the complete reviewed
Proposed-readiness evidence while AEP-0012 still remains `Draft`.

## Draft → Proposed eligibility assessment

| Criterion | Result | Evidence |
|---|---|---|
| Written interoperability problem and bounded scope | PASS | AEP-0012 + PR #130 |
| Parent Environment/Fabric authority composition is explicit | PASS | AEP-0012 + AEP-0009 / `AVP-ENVIRONMENT-010` reuse |
| Portable controlled-path resource boundary is reviewable | PASS | PR #132 portability audit + reconciled AEP |
| Mandatory base behavior is deliberately narrow | PASS | baseline forwarding + activation + transport cut + clear/recovery |
| Pre-trigger/no-early-activation semantics are explicit | PASS | Environment-governed occurrence composition |
| Activation settlement cannot self-certify | PASS | independent privileged data-plane fresh-attempt predicate |
| Transport-cut outcome is provider-neutral | PASS | no required RST/refusal/timeout/error/packet manifestation |
| Established connections are bounded conservatively | PASS | no base disposition guarantee |
| Clear/recovery/no-later-reactivation semantics are explicit | PASS | independent fresh-exchange recovery evidence |
| Latency and probabilistic loss are not under-specified in base | PASS | explicitly deferred to separately governed profiles |
| DNS/TLS/HTTP/application/UDP layering is separated | PASS | AEP-0012 deferred/separated semantics |
| Reset avoids false live-network snapshot claims | PASS | independently verified fault-free baseline only |
| Execution identity is provider-neutral | PASS | provider-native handles excluded from portable identity |
| Subject / Evaluator / privileged Control separation is explicit | PASS | schedule secrecy + credential/control isolation |
| Failure/Validity and Task Verdict remain separated | PASS | infrastructure/control failures do not become task failure by default |
| Executable implementation-independent conformance strategy exists | PASS | deterministic fixture + real behavior + negative adapters |
| Draft blockers NC-BR-001..NC-BR-012 are resolved | PASS | readiness audit blocker-disposition table |
| Cross-mechanism evidence burden is bounded | PASS | AVP acceptance/reference evidence, not universal third-party requirement |
| Alternatives and compatibility impact are documented | PASS | AEP alternatives + additive profile boundary |
| Transitional provider-first architecture is rejected | PASS | AEP/readiness audit + OSS engineering policy |
| Release/version assignment is intentionally deferred | PASS | release state remains `development` / `0.3.1.dev0` |

No remaining Draft finding requires downstream Schema, TCK, harness, or provider
code to invent portable semantics merely to make AEP-0012 reviewable.

## Semantics carried into formal Proposed review

If the lifecycle transition is later explicitly authorized and adopted, formal
protocol review should challenge — not silently assume — the following reviewed
Draft choices:

1. one independently owned controlled TCP path between declared Subject-side and
   upstream-side endpoint boundaries as the smallest mandatory resource boundary;
2. behavioral path-coverage proof rather than provider configuration presence;
3. deterministic fresh-connection request/response exchange as the base observable;
4. Environment ownership of fault identity, target, activation condition,
   occurrence counting, clear behavior, and future-schedule secrecy;
5. qualifying pre-trigger Subject traffic remaining admissible and unfaulted before
   the declared occurrence;
6. independent privileged data-plane activation settlement after the Environment
   condition, with provider API success/metadata/self-report/sleep insufficient;
7. `transport cut` as the mechanism-neutral mandatory active behavior;
8. no mandatory base disposition for connections established before activation;
9. privileged clear plus independently observed fresh-connection recovery, with no
   silent reactivation of the cleared occurrence;
10. deferral of exact latency and probabilistic packet loss until portable timing
    and statistical models exist;
11. strict separation of DNS, TLS, HTTP/application, UDP, and transport semantics;
12. reset as verified fault-free baseline rather than snapshot/restore of live TCP,
    kernel queues, proxy buffers, NAT/conntrack, resolver caches, or provider state;
13. provider-neutral execution identity with provider-native handles remaining
    diagnostics/evidence only;
14. execution-sensitive negative conformance including bypass, early activation,
    false settlement, false recovery, schedule leakage, stale/released use, and
    leaked-fault cleanup detection;
15. cross-mechanism AVP evidence as a portability protection where needed, without
    requiring every third-party conforming implementation to support multiple
    mechanisms.

These items are **review inputs**, not Accepted conclusions. Formal Proposed review
may retain, narrow, amend, or reject them.

## Open questions for formal Proposed review

The readiness audit intentionally carries the following challenge questions into
formal review:

1. Is controlled TCP plus fresh-connection exchange the correct smallest mandatory
   v0.1 boundary?
2. Is `transport cut` the best provider-neutral vocabulary?
3. Is excluding established-connection disposition appropriately conservative?
4. Is the independent fresh-attempt activation-settlement predicate strong enough
   without standardizing native timeout/error behavior?
5. Should recovery require a normative bounded count of successful exchanges, or
   may the TCK encode the already-defined behavioral recovery predicate?
6. Is deferring latency and probabilistic loss the correct first-profile tradeoff?
7. Is DNS/TLS/HTTP/UDP layer separation sufficiently strict?
8. What is the smallest endpoint/path declaration grammar that proves coverage
   without leaking private topology?
9. At which later lifecycle gate should cross-mechanism evidence become mandatory
   when the portability claim depends on mechanism independence?
10. Does Core `QUIESCING` / Environment activation / cleanup composition require
    additional normative constraints during formal review?

A question becoming a semantic blocker during Proposed review must be resolved in
AEP-0012 before any later `Proposed -> Accepted` decision.

## Decision proposition

The lifecycle proposition awaiting explicit protocol-maintainer authorization is:

> **Advance AEP-0012 from `Draft` to `Proposed` for formal protocol review.**

If explicitly authorized, the status-mutation work must remain limited to:

1. changing AEP-0012 lifecycle metadata and stale Draft-only lifecycle wording to
   `Proposed` without altering the reviewed portable design semantics;
2. updating `ROADMAP.md` to mark only
   `AEP-0012 status advanced to Proposed for formal protocol review` complete and
   to record exact decision evidence;
3. making this decision record effective, with the exact authorization and reviewed
   status-mutation head attributable in PR history;
4. running all applicable exact-head CI/Governance/Release Validation/Relational
   Parity/Browser Reference gates;
5. performing a focused exact-head lifecycle review proving the delta is
   lifecycle/evidence-only and does not smuggle semantic changes into the status
   transition;
6. requiring a **separate explicit squash-merge authorization** before the status
   transition is adopted into `main`;
7. requiring exact-main post-merge validation before the lifecycle work unit is
   considered fully closed.

No semantic rewrite should be bundled into the lifecycle status mutation. If
review discovers a semantic change is necessary, that change belongs to the later
formal Proposed-review work and invalidates any assumption that the transition is
metadata-only.

## Security, implementation, and release boundary

Preparing or later authorizing Draft → Proposed does not grant Subject authority or
provider-control authority and does not weaken existing security boundaries.

In particular:

- future fault schedules remain Evaluator/Control-private unless a separately
  governed contract exposes them;
- provider/admin credentials and privileged fault controls remain outside Subject
  context;
- payload interception or TLS interception is not implied by Network Control;
- provider-native topology/handles/errors remain non-portable diagnostics;
- a speculative `BaseNetworkBackend`, catch-all adapter, provider/plugin registry,
  or broad `supports_*` capability bag remains unjustified;
- portable TCK expectations must not branch on provider/platform names;
- provider dependencies must remain optional if/when reference implementations are
  later authorized.

Release provenance at the preparation baseline remains:

```text
mode: development
latestPublished: 0.3.0 / v0.3.0
sourceVersion: 0.3.1.dev0
nextRelease: 0.3.1 / v0.3.1
```

No release is selected for Network Control by this decision preparation.

## Non-authorization boundary

This preparation record does **not** authorize or perform:

- AEP-0012 `Draft -> Proposed`;
- AEP-0012 `Proposed -> Accepted` or `Accepted -> Final`;
- Network Control normative specification or requirement-index adoption;
- Network Control JSON Schema adoption;
- Network Control TCK/profile registration;
- backend-neutral Network Control conformance harness implementation;
- Toxiproxy, Linux `tc/netem`, firewall/routing, Envoy, Istio/service-mesh, cloud
  network control, or another provider as official AVP protocol behavior;
- controlled network-fault reference implementation work;
- cross-mechanism implementation/acceptance work;
- AEP-0009, AEP-0010, or AEP-0011 lifecycle changes;
- release-development-state changes;
- assignment of Network Control to `0.3.1`;
- tag, GitHub Release, package-index publication, signing, or attestation;
- physical repository split or plugin-framework introduction;
- merge of the current preparation PR.

No lifecycle decision may be inferred merely from the existence of this file, a
successful CI run, GitHub Ready state, or a generic instruction to continue work.

## Current gate

**DECISION PENDING — EXPLICIT AEP-0012 `Draft -> Proposed` AUTHORIZATION REQUIRED.**

The next action after review-closing this preparation artifact is a separate,
explicit protocol-maintainer authorization of the lifecycle proposition. Only then
may this branch mutate AEP-0012/ROADMAP to the Proposed candidate state.

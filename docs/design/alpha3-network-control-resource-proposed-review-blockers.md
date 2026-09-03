# Alpha 3 Network Control Resource Proposed Review Blockers

Status: **PROTOCOL SEMANTICS CLOSED — NPR-011 ACCEPTANCE EVIDENCE OPEN**

Proposal: AEP-0012 — Network Control Resource Profile v0.1

Formal review baseline: `main@45ab60d0f6e6db41da70a9859033efda52564055`

Formal review record: `docs/design/alpha3-network-control-resource-formal-proposed-review.md`

Protocol-resolution record: `docs/design/alpha3-network-control-resource-proposed-blocker-resolution.md`

## Purpose

This record tracks the acceptance blockers identified by the formal Proposed review of AEP-0012 and their current disposition.

The formal-review PR intentionally did not edit AEP-0012. The subsequent blocker-resolution work incorporates the semantic decisions into AEP-0012 while keeping `Proposed -> Accepted` separate.

NPR-001..NPR-010 are now closed as protocol-semantic decisions on the blocker-resolution candidate. NPR-011's protocol meaning is also closed, but its required cross-mechanism acceptance evidence remains an unsatisfied gate. AEP-0012 therefore remains `Proposed` and is not yet acceptance-ready.

## NPR-001 — Controlled endpoint/address-set and DNS boundary

### Finding

The Proposed AEP declared Subject-side and upstream-side endpoint boundaries but deferred exact endpoint/path declaration semantics. Hostnames can resolve to multiple addresses and deployed connection establishment can race or fall back across address families or addresses, allowing a nominally identical destination to exercise a different route.

### Resolution

Base v0.1 binds canonical materialized literal TCP endpoint identity before execution: address family, exact network address, TCP port, and endpoint role. DNS/name resolution and address selection occur before Network Control execution identity is finalized. Hidden alternate-address fallback is prohibited inside one certified attempt; a later address requires a distinct attempt identity.

**NPR-001: SEMANTICALLY CLOSED.**

## NPR-002 — Logical controlled path across terminating and packet-path mechanisms

### Finding

A user-space TCP proxy commonly terminates a Subject-side TCP connection and creates a distinct upstream TCP connection, while kernel/routing/firewall controls can act on a packet path without introducing that same transport termination boundary.

### Resolution

The controlled path is a provider-neutral logical certified exchange path between declared Subject-visible and evaluator-controlled fixture boundaries. Terminating and non-terminating mechanism classes are both admissible when they satisfy equivalent observable baseline/cut/recovery/target/path-coverage behavior. A terminating/intercepting topology has one Subject-facing connection initiation and exactly one corresponding upstream connection initiation to the bound fixture endpoint per certified attempt. Native socket/connection identity remains non-portable; hidden upstream retry/reconnect, alternate endpoint, or alternate-path fallback inside the same attempt is prohibited.

**NPR-002: SEMANTICALLY CLOSED.**

## NPR-003 — Deterministic baseline exchange grammar/completion predicate

### Finding

TCP supplies an ordered byte stream rather than protocol-owned request/response message boundaries.

### Resolution

Every certified attempt binds exact non-empty request bytes, exact expected-response bytes, immutable exchange-program identity, and an evaluator-generated attempt-unique challenge. Success requires one fresh Subject-facing connection, one corresponding upstream initiation where terminating topology applies, one request emission, receipt of the exact expected byte sequence in order within the governed observation budget, and no mismatch before completion. TCP segmentation/read boundaries and HTTP/application framing are non-semantic.

**NPR-003: SEMANTICALLY CLOSED.**

## NPR-004 — Fresh-attempt identity and retry/fallback closure

### Finding

Connection pooling, stale socket reuse, proxy retries, reconnect loops, multiple-address fallback, or Happy-Eyeballs-style racing can cause one apparent exchange to contain multiple native transport attempts.

### Resolution

One portable attempt has one evaluator-assigned attempt identity and exactly one Subject-facing connection initiation to the selected materialized destination. Pre-existing connection reuse, pooling, automatic alternate-address fallback, automatic Subject reconnect, and application retry are prohibited within one certified attempt. For terminating/intercepting topology, exactly one corresponding upstream initiation to the bound fixture endpoint is permitted; intermediary upstream retry/reconnect, alternate-endpoint selection, or alternate-path fallback is also prohibited. Evaluator-intended retries use new attempt identities and challenges.

An implementation that cannot suppress or detect hidden retry/fallback at either portable boundary cannot claim the v0.1 certified-attempt semantic.

**NPR-004: SEMANTICALLY CLOSED.**

## NPR-005 — Finite transport-cut observation budget

### Finding

A silent TCP path does not provide one provider-independent finite liveness event. Provider-native timeout policy or arbitrary sleep cannot define portable transport cut.

### Resolution

Every certified attempt binds a positive finite evaluator-owned exchange observation budget as immutable execution identity. An evaluator/control-owned monotonic source measures the portable completion predicate. Active cut succeeds when the exact exchange does not complete within that bound after admission; earlier native failure may terminate sooner without becoming portable identity. The bound is a verification condition, not a latency or Time Control claim.

**NPR-005: SEMANTICALLY CLOSED.**

## NPR-006 — Activation-settlement probe versus certified post-activation attempt

### Finding

Without explicit sequencing, a settlement attempt can become circular or accidentally consume Subject task/occurrence semantics.

### Resolution

Environment activation-condition satisfaction occurs first. Then a privileged Evaluator/Control fresh settlement attempt independently proves cut using the same materialized path/endpoints/exchange/observation semantics. It does not count as Subject task traffic or Environment occurrence traffic. Only after settlement succeeds is a distinct Subject-side certified active-cut attempt admitted. Later Subject failure cannot retroactively validate false settlement.

**NPR-006: SEMANTICALLY CLOSED.**

## NPR-007 — Recovery settlement stability / anti-flap predicate

### Finding

A single transient success can certify recovery while an intermittent fault remains.

### Resolution

After privileged clear, recovery settlement requires exactly two consecutive independent privileged fresh successful recovery probes, each with new attempt identity/challenge and the same governed path/exchange/observation semantics. Any failure in that finite sequence fails recovery settlement. One additional distinct post-recovery stability witness must then succeed to complete no-silent-reactivation evidence for the cleared occurrence. This is an ordered finite witness, not a timing window.

**NPR-007: SEMANTICALLY CLOSED.**

## NPR-008 — Behavioral path-coverage / bypass proof

### Finding

Configuration presence cannot prove traffic coverage, while one failed exchange alone does not prove traversal of the intended control point.

### Resolution

Path coverage is an end-to-end counterfactual behavioral witness binding the same materialized path/endpoints/exchange program across baseline, privileged settlement cut, distinct Subject active cut, clear, deterministic recovery, and post-recovery stability. A required `BypassFaultAdapter` must allow the active Subject attempt to escape the claimed fault while metadata still reports activation; completion of that attempt therefore fails conformance. Provider traces/configuration are supplemental only.

**NPR-008: SEMANTICALLY CLOSED.**

## NPR-009 — Target scoping and collateral-traffic noninterference

### Finding

A broad network rule could cut selected traffic while also disrupting unrelated Environment traffic and still superficially satisfy a selected exchange failure.

### Resolution

The Environment target binds the resource/path scope being claimed. A narrow target may affect only traffic within that scope to the extent required by the fault semantic. If a suitable non-target control is materialized, it must remain baseline-capable during the active narrow cut. A mechanism unable to isolate the requested scope must broaden the Environment target before execution or fail closed. Indiscriminate cut is valid only for an explicitly broad target.

**NPR-009: SEMANTICALLY CLOSED.**

## NPR-010 — Reset/cleanup residual-network-state noninterference

### Finding

Live sockets, NAT/conntrack, kernel queues, proxy buffers, resolver caches, and provider internals are outside portable snapshot state but can still alter later governed execution if residue survives.

### Resolution

Before a later Episode trusts the resource, materially relevant residue must either be removed/isolated with a fresh verified baseline, be represented by immutable provider-neutral policy/input binding sufficient to detect drift, or cause fail-closed declaration that base v0.1 cannot guarantee noninterference. Stale rules/handles/fault state cannot silently carry authority forward. This remains reset honesty/noninterference, not `STATE_EQUIVALENT` live-network restoration.

**NPR-010: SEMANTICALLY CLOSED.**

## NPR-011 — Cross-mechanism acceptance evidence matrix

### Finding

Mechanism-neutral semantics cannot be accepted solely from one control class.

### Resolution

AEP-0012 now makes the gate mandatory: before acceptance-oriented re-review can conclude with no remaining blocker, AVP project evidence MUST exercise at least two materially independent control classes against the same portable matrix:

1. a user-space terminating/intercepting TCP control class; and
2. a non-terminating packet-path kernel/routing/firewall-style control class.

The matrix must exercise endpoint/path binding, exact exchange/challenge identity, fresh-attempt/no-fallback semantics at both portable boundaries where applicable, pre-trigger/no-early-activation behavior, finite evaluator-owned cut observation, settlement sequencing, distinct Subject active cut, bypass detection, target isolation where materialized, clear, deterministic two-probe recovery, post-recovery no-reactivation witness, reset/cleanup noninterference, and schedule/control secrecy with Validity/Task-Verdict separation.

This is an AVP acceptance-evidence gate, not a universal requirement that every third-party conformer implement two providers.

The protocol meaning is closed by AEP-0012. The actual required evidence is not produced by the blocker-resolution PR and remains an independent acceptance gate.

**NPR-011: SEMANTICALLY CLOSED — ACCEPTANCE EVIDENCE OPEN.**

## Historical design-document disposition

Draft-era portability/readiness documents remain provenance:

- `docs/design/alpha3-network-control-resource-portability-audit.md`;
- `docs/design/alpha3-network-control-resource-proposed-readiness-audit.md`;
- `docs/acceptance/alpha3-network-control-draft-main-adoption.md`;
- `docs/acceptance/alpha3-network-control-readiness-main-adoption.md`;
- `docs/acceptance/alpha3-aep-0012-proposed-decision.md`.

They document why AEP-0012 became Proposed. They do not override the later Formal Proposed Review or the subsequent blocker-resolution semantics. Conflicting Draft-era wording is superseded provenance and must not be reintroduced into future Spec/Schema/TCK.

## Acceptance gate

AEP-0012 is acceptance-ready only if all of the following are true:

1. NPR-001..NPR-011 protocol-semantic decisions are incorporated into AEP-0012 Proposed text — **CANDIDATE COMPLETE IN BLOCKER-RESOLUTION PR**;
2. ROADMAP/review metadata accurately reflect formal-review and blocker-resolution state — **PENDING MAIN ADOPTION / RECONCILIATION**;
3. superseded Draft/early-Proposed ambiguities are explicitly identified — **CANDIDATE COMPLETE**;
4. the required NPR-011 cross-mechanism semantic evidence is reviewable — **OPEN**;
5. exact-head CI, Governance, Release Validation, and all applicable gates are green — **PENDING BLOCKER-RESOLUTION HEAD CLOSURE**;
6. an acceptance-oriented exact-head protocol re-review finds no remaining semantic blocker — **PENDING NPR-011 EVIDENCE**;
7. the protocol maintainer separately and explicitly authorizes `Proposed -> Accepted` — **NOT AUTHORIZED**.

Generic continuation does not satisfy item 7.

## Current conclusion

```text
AEP-0012 lifecycle: Proposed
Formal Proposed review: MAIN ADOPTED
NPR-001..NPR-010 protocol semantics: CLOSED ON CANDIDATE
NPR-011 protocol meaning: CLOSED ON CANDIDATE
NPR-011 cross-mechanism acceptance evidence: OPEN
Blocker-resolution protocol edits: CANDIDATE PRESENT
Acceptance-oriented re-review: NOT READY UNTIL REQUIRED EVIDENCE EXISTS
Accepted: NOT AUTHORIZED
Network Control normative Spec/Schema/TCK: NOT AUTHORIZED
Network Control conformance harness: NOT AUTHORIZED
Provider/reference implementation: NOT AUTHORIZED
Release/publication/signing/attestation: NOT AUTHORIZED
```

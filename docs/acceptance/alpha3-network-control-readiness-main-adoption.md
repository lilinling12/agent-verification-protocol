# Alpha 3 Network Control Proposed-Readiness Main-Adoption Reconciliation

Status: **MAIN ADOPTED — PROPOSED-READINESS BASELINE CLOSED**

Main baseline: `2632935bef065b4d38e88f6df6b8cf0d620bfb3b`

## Purpose

This document reconciles repository governance after PR #133 adopted the reviewed AEP-0012 Network Control Resource Profile v0.1 portability decisions and Draft -> Proposed readiness evidence into `main`.

This is an adoption-evidence record only. It does not advance AEP-0012 beyond `Draft`, perform the separately governed `Draft -> Proposed` lifecycle transition, create Network Control normative Spec/requirement-index/Schema/TCK authority, authorize a backend-neutral conformance harness, select a network-control provider, or authorize a reference implementation.

## Adopted work unit

PR #133: `docs(alpha3): reconcile Network Control proposed readiness`

Reviewed exact PR head:

`fe7e356ae64faa0b8b69e9b0ef64c345f3793916`

Exact base before merge:

`main@74b442a0ffd22f4da79b5d4abfd339d694fc2843`

Authorized squash merge commit on `main`:

`2632935bef065b4d38e88f6df6b8cf0d620bfb3b`

The adopted source slice changes exactly:

- `rfcs/AEP-0012-network-control-resource-profile.md`;
- `docs/design/alpha3-network-control-resource-proposed-readiness-audit.md`.

`ROADMAP.md`, normative Spec, requirement index, schemas, TCK, conformance harness, provider/reference runtime, workflow definitions, packaging, and release-development state were intentionally unchanged by PR #133 so branch-local readiness could not be mistaken for main adoption or lifecycle advancement.

## Adopted Network Control v0.1 design boundary

The main-adopted Draft closes NC-BR-001..NC-BR-012 as design blockers for Proposed-readiness review. The reviewed direction is deliberately narrow:

- one independently owned controlled TCP path between declared Subject-side and upstream-side endpoint boundaries;
- behavioral proof that selected traffic traverses the controlled path rather than configuration self-certification;
- deterministic baseline request/response exchange over a fresh TCP connection;
- Environment-owned fault identity, target, activation condition, occurrence counting, clear semantics, and future-schedule secrecy;
- qualifying pre-trigger Subject traffic remains admissible and must not be faulted before the declared occurrence;
- Network Control activation settlement is subordinate to Environment activation and requires an independent privileged data-plane fresh-attempt observation;
- provider API success, rule/object existence, metadata, Subject self-report, and arbitrary sleep are insufficient settlement proof;
- mandatory active behavior is a mechanism-neutral fresh-connection `transport cut` rather than a prescribed RST, refusal, timeout, blackhole, route withdrawal, socket error, packet count, or retransmission pattern;
- connections established before activation have no mandatory base disposition guarantee;
- clear is privileged control and recovery requires independently observed successful fresh baseline exchange(s) through the same controlled path;
- the cleared occurrence must not silently reactivate;
- exact latency, probabilistic packet loss, DNS/name-resolution faults, TLS interception/failure, HTTP/application faults, UDP semantics, and established-connection termination are deferred or layer-separated rather than silently generalized into the base profile;
- reset establishes and independently verifies a fault-free baseline without claiming portable snapshot/restore of live sockets, TCP/kernel queue state, proxy buffers, NAT/conntrack, resolver caches, or provider internals;
- execution identity is provider-neutral; qdisc/filter/proxy/socket/process/cloud/mesh native handles remain implementation diagnostics/evidence only;
- Subject, Evaluator, and privileged Control authority remain separated, including future-schedule secrecy and provider/control credential isolation;
- future TCK behavior must be provider/language-neutral and execution-sensitive, including bypass, early-activation, false-settlement, false-recovery, schedule-leak, stale/released-use, and cleanup-negative directions;
- AVP portability/reference evidence may require materially independent mechanism classes without making multi-mechanism support a universal third-party conformance requirement.

These are reviewable AEP design semantics, not yet released normative Network Control requirements.

## Proposed-readiness evidence

`docs/design/alpha3-network-control-resource-proposed-readiness-audit.md` concludes:

**READY FOR PROTOCOL REVIEW — PROPOSED ELIGIBLE**

That conclusion means the Draft design is sufficiently complete to be considered for a separately governed `Draft -> Proposed` lifecycle decision. It does not perform that decision automatically.

The audit records downstream representation and test-encoding details as subordinate to the already-reviewed semantics, including final profile/capability spelling, endpoint/path wire syntax, exact serialized field/media-type details, canonical representation choices that do not change identity semantics, exact bounded settlement-probe parameters, requirement/TCK identifiers, language-specific SPI names, and provider setup/cleanup mechanics.

If a downstream choice changes portable meaning rather than encodes it, AEP-0012 must be amended through protocol review rather than allowing implementation precedent to redefine the profile.

## Exact-head review and pre-merge gates

Focused exact-head review `5088528789` / `PRR_kwDOT09qic8AAAABL0zJlQ` was anchored to:

`fe7e356ae64faa0b8b69e9b0ef64c345f3793916`

and concluded:

**REVIEW-CLOSED — PROPOSED-ELIGIBILITY EVIDENCE IS COHERENT FOR THIS EXACT HEAD.**

The review explicitly re-checked controlled-path ownership, no-early-activation, pre-trigger traffic admissibility, independent activation settlement, transport-cut portability, established-connection exclusion, recovery/no-later-reactivation, reset/non-snapshot participation, provider-neutral execution identity, Subject/Evaluator/Control separation, future schedule secrecy, execution-sensitive negative conformance directions, cross-mechanism evidence scope, and the boundary between TCK proof strategy and protocol semantics.

Exact-head validation completed successfully:

- Governance #966 / run `33619764986` — **SUCCESS**;
- CI #829 / run `33619765040` — **SUCCESS**;
- Relational Parity #222 / run `33619765006` — **SUCCESS**;
- Browser Reference #95 / run `33619765014` — **SUCCESS**;
- Ready/metadata Governance #967 / run `33620341311` — **SUCCESS**;
- Ready-state Governance #968 / run `33666655550` — **SUCCESS**;
- final PR-metadata Governance #969 / run `33667247699` — **SUCCESS**;
- unresolved inline review threads — none.

No Release Validation run is claimed for PR #133 because the changed paths did not trigger that workflow. Evidence is recorded only for gates that actually executed.

## Authorized merge and exact-main validation

The protocol maintainer explicitly authorized **squash merge PR #133** on 2026-09-03.

Before merge, the live guard confirmed:

- `main` remained `74b442a0ffd22f4da79b5d4abfd339d694fc2843`;
- PR #133 remained open, Ready, mergeable, and at exact head `fe7e356ae64faa0b8b69e9b0ef64c345f3793916`;
- no base drift was present;
- all applicable exact-head CI/Governance/Parity/Browser evidence remained successful;
- focused review remained anchored to the exact head;
- unresolved review threads remained zero.

The merge used `expected_head_sha=fe7e356ae64faa0b8b69e9b0ef64c345f3793916` to fail closed if the reviewed head moved.

GitHub produced exact main commit:

`2632935bef065b4d38e88f6df6b8cf0d620bfb3b`

with parent:

`74b442a0ffd22f4da79b5d4abfd339d694fc2843`

Exact-main push validation then completed successfully:

- CI #830 / run `33667291305` — **SUCCESS**;
- Relational Parity #223 / run `33667290799` — **SUCCESS**;
- Browser Reference #96 / run `33667291258` — **SUCCESS**.

GitHub reported exactly these three push workflows for the merge SHA. This closes PR #133 itself as a main-adopted work unit. It does not create Network Control conformance evidence because the normative Network Control Spec/Schema/TCK and provider-neutral conformance harness do not yet exist.

## ROADMAP reconciliation

With this exact-main evidence, the following Network Control roadmap milestones may be marked complete:

- network-control portability and Proposed-readiness audit;
- close NC-BR-001..NC-BR-012 Draft -> Proposed blockers;
- reconcile AEP-0012 and complete Draft -> Proposed readiness audit.

The next milestone remains intentionally incomplete:

`AEP-0012 status advanced to Proposed for formal protocol review`

That lifecycle transition requires a separate explicit protocol-maintainer governance decision. Main adoption of Proposed-readiness evidence is not implicit lifecycle authorization.

Formal Proposed protocol review, any acceptance-blocker resolution, `Proposed -> Accepted`, downstream normative surfaces, conformance harness, provider/reference implementation, and cross-mechanism acceptance evidence all remain later governed work.

## Open-source implementation-quality boundary

No Network Control implementation architecture is frozen by this adoption record. Downstream work must continue to follow the repository engineering rule:

> Split responsibilities; do not abstract protocol semantics.

In particular:

- normative Network Control semantics must be public before provider implementation precedent can affect conformance;
- portable TCK code must not import or branch on Toxiproxy, Linux `tc/netem`, firewall/routing stacks, Envoy, Istio/service-mesh products, cloud network APIs, operating-system names, or another provider to determine expected outcomes;
- privileged preparation/activation coordination, clear, reset, settlement probes, and fixture control must remain structurally separate from Subject-visible operations;
- provider dependencies must remain optional and must not become unconditional base-package dependencies;
- provider-native handles and error identities must not become portable resource/execution identity;
- a speculative `BaseNetworkBackend`, catch-all adapter, provider/plugin registry, or broad `supports_*` capability bag must not be introduced before a stable multi-consumer contract exists;
- mandatory behavioral TCK cases must execute real controlled-path behavior rather than pass through metadata self-declaration;
- cleanup must remove privileged fault effects without hiding the primary failure or leaving a latent active fault;
- cross-mechanism project evidence, if required at acceptance, demonstrates portability of AVP semantics and does not make one mechanism protocol authority.

Exact package/module names and provider construction APIs remain deferred until normative Network Control authority and backend-neutral harness responsibilities are reviewed.

## Lifecycle and release boundary

After this reconciliation:

- AEP-0012 remains **Draft, not Proposed**;
- NC-BR-001..NC-BR-012 are closed as Draft design blockers, not as Accepted/Final protocol requirements;
- AEP-0009 remains **Accepted, not Final**;
- AEP-0010 remains **Accepted, not Final**;
- AEP-0011 remains **Accepted, not Final**;
- Network Control normative Spec/requirement-index/Schema/TCK remain unadopted;
- backend-neutral Network Control harness and provider/reference implementation remain unauthorized;
- no Linux `tc/netem`, Toxiproxy, Envoy, Istio/service-mesh, firewall/routing, cloud, or other mechanism becomes protocol authority;
- release provenance remains in development mode and is unchanged by this work;
- no public release version is selected for Network Control;
- no tag, GitHub Release, package-index publication, signing, or attestation is authorized.

## Acceptance conclusion

**MAIN ADOPTED — PROPOSED-READINESS BASELINE CLOSED.**

PR #133 is fully closed at exact main `2632935bef065b4d38e88f6df6b8cf0d620bfb3b` with exact-main CI #830, Relational Parity #223, and Browser Reference #96 successful.

The next separately governed protocol work is the AEP-0012 `Draft -> Proposed` lifecycle decision and formal Proposed review. This document does not authorize that transition or any downstream Network Control normative/runtime implementation.

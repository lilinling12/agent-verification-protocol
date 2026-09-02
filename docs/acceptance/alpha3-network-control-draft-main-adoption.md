# Alpha 3 Network Control Resource Draft Main-Adoption Reconciliation

Status: **MAIN ADOPTED — DRAFT BASELINE CLOSED**

Main baseline: `7f7f613c50520efb2b553d65d4bb85c0e777dc40`

## Purpose

This document reconciles repository governance after PR #130 adopted the reviewed
AEP-0012 Network Control Resource Profile v0.1 Draft problem/scope and
standards/interoperability-analysis baseline into `main`.

This is an adoption-evidence record only. It does not advance AEP-0012 beyond
`Draft`, close NC-BR-001..NC-BR-012, create Network Control normative semantics,
select a network-fault provider, or authorize a Network Control reference
implementation.

## Adopted work unit

PR #130: `docs(alpha3): draft network control resource profile`

Reviewed exact PR head:

`d33807232ef34db6b88a6ca92f4aafa11433c650`

Previous `main`:

`e6cdb4246153b3ebbe429bda495829cc7daf2ec6`

Squash merge commit on `main`:

`7f7f613c50520efb2b553d65d4bb85c0e777dc40`

The adopted source slice contains exactly:

- `rfcs/AEP-0012-network-control-resource-profile.md`;
- the Network Control Resource sequencing update in `ROADMAP.md`.

No runtime source, Network Control normative specification, requirement index,
schema, TCK, release-development state, packaging metadata, or workflow
definition was introduced by PR #130.

## Review evidence

The first focused exact-head review, `5086505066`, was anchored to
`865af064d374c24524cdfef564d5eeaad1228ab0` and identified NC-DR-001: Network
Control activation/settlement wording had to remain explicitly subordinate to
the existing Environment v0.1 scheduled-fault identity, target, and activation
condition contract.

The reviewed head `d33807232ef34db6b88a6ca92f4aafa11433c650` closed that Draft-baseline
coherence issue by making the composition explicit:

- Environment v0.1 remains authoritative for fault identity, target, and
  activation condition;
- occurrence-based faults MUST NOT activate before the declared occurrence;
- qualifying pre-trigger Subject traffic remains admissible and MUST NOT be
  faulted early;
- Network Control activation settlement gates post-trigger/post-activation
  fault-sensitive observations rather than the traffic required to satisfy the
  Environment activation condition;
- Network activation/clearing states are subordinate operational states rather
  than a competing top-level lifecycle;
- clearing preserves the Environment rule preventing later activation unless a
  separately governed selected profile defines otherwise.

Formal exact-head review `5087251248` was anchored to
`d33807232ef34db6b88a6ca92f4aafa11433c650` and concluded:

- the AEP-0012 Draft problem/scope + standards/interoperability baseline was
  review-closed for PR #130 scope;
- PR #130 was Ready eligible;
- AEP-0012 remained explicitly **not Proposed-ready**;
- NC-BR-001..NC-BR-012 remained intentionally open;
- no Network Spec/Schema/TCK/runtime work, provider selection, AEP lifecycle
  advance, release selection/publication, signing, or attestation was
  authorized.

The Ready transition preserved the exact head. Ready-state Governance #955
(run `33608083493`) and Governance #956 (run `33609052798`) both completed
successfully on that unchanged head. Immediately before merge, unresolved inline
review threads were zero and `main` remained the exact PR base.

## Exact-head pre-merge gates

At reviewed PR head `d33807232ef34db6b88a6ca92f4aafa11433c650`:

- Governance #954 / run `33600925180` — **SUCCESS**;
- Release Validation #112 / run `33600925122` — **SUCCESS**;
- CI #822 / run `33600925088` — **SUCCESS**;
- Relational Parity #215 / run `33600925190` — **SUCCESS**;
- Browser Reference #88 / run `33600925272` — **SUCCESS**;
- Ready-state Governance #955 / run `33608083493` — **SUCCESS**;
- Ready-state Governance #956 / run `33609052798` — **SUCCESS**.

The merge was guarded with
`expected_head_sha=d33807232ef34db6b88a6ca92f4aafa11433c650`, so the adopted tree is exactly
the reviewed PR tree.

## Exact-main post-merge gates

The authorized squash merge produced exact `main` commit:

`7f7f613c50520efb2b553d65d4bb85c0e777dc40`

The GitHub merge commit is signature-verified and has parent
`e6cdb4246153b3ebbe429bda495829cc7daf2ec6`.

Applicable push-triggered exact-main validation completed successfully:

- CI #823 / run `33609386257` — **SUCCESS**;
- Relational Parity #216 / run `33609386265` — **SUCCESS**;
- Browser Reference #89 / run `33609386244` — **SUCCESS**.

CI #823 retained the established quality, reproducible packaging,
clean-consumer installation, installed-wheel governed TCK, release-evidence,
PostgreSQL, and MySQL regression coverage. Relational Parity #216 executed both
real PostgreSQL/MySQL canonical-parity matrix pairs successfully. Browser
Reference #89 executed the real Playwright/Chromium provider foundation path
successfully.

These are regression and adoption facts. They do not create Network Control
conformance evidence because the Network Control normative Spec/Schema/TCK do
not yet exist.

## Governance interpretation

The first Network Control Resource ROADMAP item may now be marked complete
because its precise acceptance condition was adoption of the reviewed AEP-0012
Draft problem/scope and standards/interoperability-analysis baseline into `main`
with exact-main validation.

The next ROADMAP item remains:

`network-control portability and Proposed-readiness audit`

That audit must independently evaluate NC-BR-001..NC-BR-012 and may narrow,
split, defer, or reject Draft design directions. It must not treat this
main-adopted Draft as accepted normative semantics.

In particular, the audit must continue to resolve the controlled-path boundary,
portable fault vocabulary, Environment-governed activation composition,
activation and clearing settlement, established-connection disposition,
recovery settlement, timing/latency portability, loss semantics, DNS versus
transport/application layering, reset/snapshot participation, hidden
schedule/security constraints, execution identity, and cross-mechanism
conformance portability.

## Open-source implementation-quality boundary

Although PR #130 introduced no runtime code, downstream Network Control work
must preserve an implementation architecture suitable for an independently
maintained open-source protocol project. Future implementation work must not
collapse protocol semantics, portable TCK behavior, evaluator/privileged fixture
control, controlled-path verification, and provider-native fault mechanics into
one package or one catch-all adapter.

The expected dependency direction remains one-way and must be established only
as each governed authority surface becomes reviewable:

```text
AEP-0012 reviewed design decisions
        -> normative Network Control contract
        -> schema / canonical resources where required
        -> provider/language-neutral execution-sensitive TCK
        -> backend-neutral conformance harness + immutable local fixture
        -> optional concrete reference provider adapter(s)
        -> provider/mechanism-specific private mechanics and evidence
```

Future review should reject:

- Toxiproxy-, `tc/netem`-, Envoy-, Istio-, service-mesh-, kernel-, cloud-, or
  other provider-shaped public protocol objects generalized after
  implementation;
- provider-name branching inside portable TCK semantics;
- a speculative generic `BaseNetworkBackend`, provider/plugin framework, or
  broad `supports_*` capability bag without demonstrated independent consumers;
- a catch-all Network adapter that owns unrelated lifecycle, control,
  observation, evidence, fixture, routing, and provider responsibilities;
- privileged fault-control credentials, handles, or future hidden schedules
  exposed to Subject-visible APIs;
- provider-native listener IDs, qdisc handles, socket descriptors, route names,
  process IDs, or mesh resource names used as portable resource or Artifact
  identity;
- provider API completion, arbitrary sleeps, metadata declarations, or native
  packet traces treated as sufficient proof of activation, clearing, recovery,
  or controlled-path traversal;
- exact TCP segment boundaries, retransmission timing, packet counts, native
  socket error text, or one kernel's timer/queue behavior standardized as the
  portable base profile;
- unconditional provider dependencies in the base package before a separately
  reviewed implementation/dependency decision;
- compatibility layers for Network Control APIs that have never been released.

Exact package names, directories, provider choices, and the final v0.1 semantic
surface remain intentionally deferred until the portability / Proposed-readiness
audit determines what is actually portable and reviewable.

## Lifecycle and release boundary

After this reconciliation:

- AEP-0012 remains **Draft**;
- NC-BR-001..NC-BR-012 remain open;
- AEP-0009 remains **Accepted, not Final**;
- AEP-0010 remains **Accepted, not Final**;
- AEP-0011 remains **Accepted, not Final**;
- release provenance remains `development`;
- latest published release remains `v0.3.0`;
- source version remains `0.3.1.dev0`;
- planned next release remains `v0.3.1` but is not selected for Network Control
  publication by this work;
- no tag, GitHub Release, package-index publication, signing, or attestation is
  authorized.

## Acceptance conclusion

**MAIN ADOPTED — DRAFT BASELINE CLOSED.**

PR #130 is fully closed at exact main
`7f7f613c50520efb2b553d65d4bb85c0e777dc40`.

The next separately governed work unit is the Network Control Resource
portability and Proposed-readiness audit. This document does not authorize its
outcome, AEP-0012 lifecycle advancement, Network Spec/Schema/TCK/runtime work,
provider selection, or release publication.

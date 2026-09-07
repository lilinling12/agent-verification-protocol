# Alpha 3 AEP-0012 Acceptance-Oriented Exact-Head Protocol Re-Review

Status: **ACCEPTANCE-READY FOR SEPARATE MAINTAINER DECISION**

AEP: `rfcs/AEP-0012-network-control-resource-profile.md` (`Proposed`)

Review baseline: `main@63e306abcecbb928edab1ea4ba584f6a71ea889e`

AEP exact Git blob: `0b5ebdddb45533cf91a7bc264dcfe7548b54391c`

Formal Proposed review:

- `docs/design/alpha3-network-control-resource-formal-proposed-review.md`

Blocker resolution and ledger:

- `docs/design/alpha3-network-control-resource-proposed-blocker-resolution.md`;
- `docs/design/alpha3-network-control-resource-proposed-review-blockers.md`.

Cross-mechanism acceptance evidence:

- `docs/acceptance/alpha3-network-control-cross-mechanism-npr011-acceptance.md`;
- `docs/acceptance/evidence/alpha3-network-control-cross-mechanism-npr011-v0.1.json.gz.b64`.

## 1. Review question

This re-review asks one narrow lifecycle question:

> After incorporation of NPR-001..NPR-011 protocol decisions and main adoption of the required terminating/intercepting plus non-terminating packet-path portability evidence, does AEP-0012 contain any remaining semantic or evidence ambiguity that would require a future Network Control Spec, Schema, TCK, conformance harness, or reference implementation to choose protocol meaning rather than encode it?

A green evidence matrix alone is not sufficient. This review therefore re-checks the accepted parent contracts, exact AEP candidate, original Proposed blockers, blocker-resolution decisions, cross-mechanism retained evidence, and the authority boundary between protocol semantics and provider mechanics.

This record does **not** change AEP-0012 lifecycle state. `Proposed -> Accepted` remains a separate explicit protocol-maintainer decision.

## 2. Exact-main evidence and gate state

The review baseline is exact `main@63e306abcecbb928edab1ea4ba584f6a71ea889e`, after PR #171 reconciled the main-adopted cross-mechanism evidence into ROADMAP.

The immediately preceding cross-mechanism evidence work was adopted by PR #170 at exact main commit:

`670dafacbabdba05bd551a8028a1dc216613348f`

Its exact-main validation completed successfully:

- CI #977 — run `34079764287`;
- Relational Parity #370 — run `34079764305`;
- Browser Reference #243 — run `34079764236`.

PR #171 then reconciled ROADMAP and was adopted at the current review baseline. Exact-main validation on that merge commit also completed successfully:

- CI #979 — **SUCCESS**;
- Relational Parity #372 — **SUCCESS**;
- Browser Reference #245 — **SUCCESS**.

These gates establish repository/evidence integrity for the reviewed baseline. They do not override semantic findings below.

## 3. Re-review of NPR-001..NPR-010 protocol decisions

### NPR-001 — endpoint/address selection and DNS boundary

AEP-0012 now binds materialized literal TCP endpoint identity before Episode execution, keeps DNS/address selection outside the base certified attempt, and prohibits hidden alternate-address fallback within one attempt. This composes with Scenario immutable materialization and fail-closed unresolved-input rules. No remaining semantic blocker found.

### NPR-002 — logical controlled path across mechanism classes

The portable resource is a logical certified exchange path between declared Subject-visible and evaluator-controlled fixture boundaries, not a provider-native connection object. Terminating/intercepting and non-terminating packet-path mechanisms can satisfy the same claim without native topology equality. No remaining topology semantic blocker found.

### NPR-003 — deterministic exchange grammar

Exact request bytes, exact expected-response bytes, immutable exchange-program identity, attempt-unique challenge, and exact completion predicate are fixed at protocol level. TCP segment/read boundaries, HTTP framing, provider errors, and native connection identities remain non-semantic. No remaining exchange-completion blocker found.

### NPR-004 — fresh-attempt identity and hidden retry/fallback

One certified attempt has exactly one Subject-facing initiation, with exactly one corresponding upstream initiation only when terminating topology makes that boundary distinct. Pooling, stale reuse, automatic reconnect, address fallback, application retry, and intermediary retry/fallback are prohibited inside one attempt. No remaining fresh-attempt ambiguity found.

### NPR-005 — finite evaluator-owned observation budget

The cut decision is bound to an immutable positive finite evaluator-owned monotonic observation budget. Provider timeouts, arbitrary sleeps, wall-clock timestamps, and Subject self-report are non-authoritative. The budget is a verification bound rather than latency/Time Control semantics. No remaining decidability blocker found.

### NPR-006 — activation-settlement sequencing

Environment activation-condition satisfaction precedes privileged Network Control settlement. The settlement probe is distinct privileged verification traffic, cannot consume Subject task/occurrence semantics, and precedes the separate Subject-side active-cut attempt. No circular settlement semantics remain.

### NPR-007 — deterministic recovery stability

Clear acknowledgement cannot self-certify recovery. Recovery requires exactly two consecutive independent privileged fresh successful probes plus one distinct post-recovery stability witness. This closes transient-success and unbounded-retry ambiguity without introducing wall-clock quiet-period semantics.

### NPR-008 — behavioral path coverage / bypass proof

Portable path coverage is an end-to-end counterfactual baseline/cut/recovery witness over one immutable controlled-path identity, and required bypass-negative behavior must fail. Provider configuration or packet capture may supplement but cannot replace this behavioral proof. No remaining path-coverage semantic blocker found.

### NPR-009 — target isolation and collateral noninterference

A narrow Environment target may not be implemented by indiscriminate broad disruption. Where a suitable non-target control is materialized, it must remain baseline-capable during the selected cut. Unsupported isolation must broaden the target before execution or fail closed. No remaining target-scope ambiguity found.

### NPR-010 — reset/cleanup residual-state noninterference

Excluded live network/provider internals do not become portable snapshot state, but relevant residue must be removed/isolated and baseline-verified, immutably bound where unavoidable, or cause fail-closed noninterference failure. This composes with Fabric retry-safe cleanup without inventing `STATE_EQUIVALENT` network restore semantics. No remaining reset/cleanup blocker found.

## 4. NPR-011 cross-mechanism evidence re-review

NPR-011 required AVP project evidence from at least two materially independent mechanism classes against the same portable semantic matrix:

1. user-space terminating/intercepting TCP control;
2. non-terminating packet-path kernel/routing/firewall-style control.

That evidence requirement is now satisfied and main-adopted.

The retained cross-mechanism assessment establishes all of the following:

- TEL-003 and PTL-003 were independently produced and independently main-adopted;
- source ZIP and manifest integrity was independently verified for both evidence sets;
- both mechanism executions and the reassessment bind the same exact AEP-0012 Git blob `0b5ebdddb45533cf91a7bc264dcfe7548b54391c`;
- both retained evidence classes were reassessed using the current topology-aware provider-neutral comparator blob `39169f40083e204560606cd9db0d8f1a1dda57bd`;
- all 19 retained cases were reassessed from normalized observations rather than historical PASS/FAIL labels;
- both positive cases are `SATISFIED`;
- all eight mandatory negative families are rejected through the corresponding portable C1-C12 predicate families;
- terminating hidden retry is exercised independently at both Subject-facing and upstream boundaries;
- packet-path topology does not fabricate a second upstream TCP connection merely to imitate terminating evidence shape;
- no provider-name branch is used to define portable verdict meaning;
- the derived reassessment record is retained in deterministic, self-reassessable form;
- later semantic/comparator changes that require observations not retained by the derived record must trigger new live evidence rather than inference.

The evidence therefore proves the mechanism-neutral choices needed by NPR-011 without turning Toxiproxy, Linux namespaces, veth, nftables, packet capture, native socket errors, or another selected mechanism into protocol authority.

**NPR-011 acceptance evidence: SATISFIED for this acceptance review.**

## 5. Cross-contract review

### Environment v0.1

AEP-0012 preserves `AVP-ENVIRONMENT-010` ownership of scheduled fault identity, target, activation condition, no-early-activation occurrence semantics, clear, and future-fault secrecy. Network Control adds only subordinate data-plane settlement and recovery verification after Environment-owned activation/clear boundaries. No conflict found.

### Environment Fabric / AEP-0009

AEP-0012 preserves the backend-first prohibition, Resource Capability versus Subject Capability separation, materialized immutable resource identity, Security/Evidence composition, execution-sensitive conformance, and retry-safe cleanup. `resourceKind: network` remains coarse classification only. No conflict found.

### Scenario

Materialized endpoint/path/exchange/budget inputs are immutable before governed execution, and unresolved or drifted execution-relevant identity fails closed. Evaluator-private schedules and observation inputs need not enter the Subject projection. No conflict found.

### Core lifecycle

Network Control settlement/recovery are resource-internal/evaluator verification phases that retain an unambiguous Core lifecycle projection. They do not create a competing Episode state machine. Network Control does not reinterpret `QUIESCING` as arbitrary network-idle or timeout semantics. No conflict found.

### Security

Subject, Evaluator, and privileged Control authority remain separated. Provider credentials/control handles, future schedules, evaluator probes, private observation budgets, and private topology diagnostics are not automatically Subject-visible. Provider technology does not inflate `SecurityAssurance`. No conflict found.

### Evidence

Retained exact bytes use Artifact content identity; provider locators/object IDs do not substitute for exact-byte digest/size integrity. The committed cross-mechanism derived record preserves the normalized observations required by the current comparator and explicitly does not pretend to be permanent raw-forensic retention. No conflict found.

### Validity versus Task Verdict

Baseline/control/settlement/recovery/cleanup failures remain infrastructure or Validity information unless another governed contract maps a verified Subject outcome to Task Verdict. Network Control therefore does not collapse lifecycle, Validity, and task success/failure dimensions. No conflict found.

## 6. Provider-neutrality and downstream-authority review

This re-review found no remaining choice that future Network Control Spec/Schema/TCK/harness/runtime would have to invent for:

- base controlled-path topology semantics;
- endpoint materialization/address fallback;
- exchange completion;
- fresh-attempt/retry identity;
- finite cut observation;
- activation settlement;
- Subject active-cut separation;
- recovery cardinality/stability;
- bypass/path coverage;
- narrow target noninterference;
- reset/cleanup residual noninterference;
- future-schedule secrecy;
- required cross-mechanism acceptance evidence.

Downstream work may still choose representation details explicitly left downstream by AEP-0012, such as capability/profile spelling, JSON field names, bounded numeric schema ranges, canonical serialized endpoint representation, requirement/TCK identifiers, language-specific SPI names, and provider diagnostic mappings. Those details encode the reviewed semantics and do not constitute an unresolved acceptance blocker.

The review also finds no justification for introducing a generic `BaseNetworkBackend`, provider registry, plugin framework, or broad `supports_*` abstraction at this point.

## 7. Historical-status metadata drift

Several main-adopted AEP/blocker-resolution texts still contain historical statements such as:

- NPR-011 `EVIDENCE OPEN`;
- cross-mechanism evidence still required before the acceptance-oriented re-review can close;
- acceptance-oriented re-review not yet ready.

Those statements accurately described the blocker-resolution baseline when authored, but are now stale planning/status metadata after PR #170/#171 main adoption. They do not define a contradictory portable semantic rule and do not require AEP semantic amendment.

Following the successful Browser acceptance precedent, this stale metadata should be synchronized in a **separate metadata-only closure Work Unit after this acceptance-review record itself is reviewed and main-adopted**. That synchronization must not change Network Control portable meaning or AEP lifecycle state.

## 8. Remaining semantic/evidence blockers

This acceptance-oriented re-review found **no remaining semantic or evidence blocker** in AEP-0012 at exact review baseline `63e306abcecbb928edab1ea4ba584f6a71ea889e`.

The conclusion is limited to acceptance readiness. It is not lifecycle promotion and does not authorize downstream normative or implementation work.

## 9. Lifecycle disposition

```text
NPR-001..NPR-010 protocol decisions: CLOSED FOR ACCEPTANCE REVIEW
NPR-011 protocol decision: CLOSED FOR ACCEPTANCE REVIEW
NPR-011 cross-mechanism evidence: SATISFIED / MAIN-ADOPTED
Cross-contract review: NO CONFLICT FOUND
Acceptance-oriented exact-head semantic/evidence re-review: NO REMAINING BLOCKER
AEP-0012 lifecycle: Proposed
Acceptance readiness: READY FOR SEPARATE MAINTAINER DECISION
Proposed -> Accepted: NOT AUTHORIZED
Network Control normative Spec/Schema/TCK/harness/runtime: NOT AUTHORIZED
Release/publication/signing/attestation: NOT AUTHORIZED
```

## 10. Next governed step

The next step is **not** automatic lifecycle promotion or downstream implementation.

Before any `Proposed -> Accepted` transition:

1. this exact-head acceptance-review record must pass applicable Governance/CI and focused review and be separately authorized for merge;
2. after main adoption and exact-main regression closure, stale blocker/ROADMAP/AEP acceptance-status metadata must be synchronized without changing protocol semantics or lifecycle state;
3. that metadata-only closure head must pass exact-head governance/CI and focused review;
4. only then may the exact reviewed AEP-0012 candidate and closure evidence be presented for a **separate explicit protocol-maintainer `Proposed -> Accepted` lifecycle decision**.

Generic continuation does not authorize step 4. Merge authorization remains separate at every PR boundary.

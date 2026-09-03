# Alpha 3 Network Control Resource Proposed Blocker Resolution

Status: **CANDIDATE — PROTOCOL DECISIONS CLOSED; CROSS-MECHANISM ACCEPTANCE EVIDENCE STILL REQUIRED**

Proposal: AEP-0012 — Network Control Resource Profile v0.1

Resolution baseline: `main@6770f15fa96ff4e74a773277484d500d85148019`

Formal Proposed review:

- `docs/design/alpha3-network-control-resource-formal-proposed-review.md`
- `docs/design/alpha3-network-control-resource-proposed-review-blockers.md`

Prepared: 2026-09-03

## Purpose

This record resolves the protocol-semantic ambiguity identified as NPR-001..NPR-011 by the formal Proposed review of AEP-0012.

The goal is not to widen Network Control v0.1. The goal is to make the already-selected narrow TCP transport-cut profile objectively materializable, finitely observable, provider-neutral, retry-safe, and reviewable across materially independent mechanism classes.

This record does **not** advance AEP-0012 beyond `Proposed`, does not create the normative Network Control Spec/Schema/TCK, does not introduce a provider/reference implementation, and does not satisfy the required cross-mechanism acceptance-evidence gate merely by describing it.

## Standards constraints retained

The resolution relies on the same interoperability facts already used by AEP-0012:

- TCP is a reliable ordered byte stream; application write/read boundaries and TCP segment boundaries are not one portable message framing contract.
- hostname connection setup can materialize multiple destination addresses and multiple competing connection attempts; base Network Control therefore cannot leave address selection/fallback implicit.
- TCP does not provide one provider-independent, universally short failure-detection event for a silent path; a portable transport-cut verdict therefore requires an evaluator-owned finite observation condition rather than an implementation-selected timeout.

These standards constrain AVP's own semantic design. They do not become AVP authority by citation.

## Resolution principles

The blocker decisions follow these rules:

1. **Materialize before execution.** Anything that can change which network path or completion predicate is being certified must be explicit and immutable before the governed attempt.
2. **One portable attempt, one Subject-facing connection initiation.** Hidden retries, pooling reuse, address racing, and fallback are not part of one certified v0.1 attempt. A terminating/intercepting topology also gets only one corresponding upstream connection initiation to its bound fixture endpoint.
3. **Logical path, not native connection identity.** A terminating proxy and a non-terminating packet-path mechanism can satisfy the same portable claim when the declared end-to-end boundaries and observed behavior are equivalent.
4. **Exact bytes, not packet/message folklore.** A certified exchange is defined by exact materialized request/expected-response bytes and an attempt-unique challenge, not by TCP segment boundaries or HTTP semantics.
5. **Finite evaluator observation, not provider timeout.** Completion/non-completion is decided by evaluator-owned monotonic observation against an immutable finite budget.
6. **Settlement is privileged verification traffic.** It cannot consume Subject task traffic, change occurrence counting, or retroactively become true because a later unrelated attempt failed.
7. **Recovery is a deterministic sequence.** Provider clear acknowledgement and one transient success are insufficient.
8. **Coverage is behavioral.** Configuration presence, native object existence, and packet traces cannot replace actual Subject-visible baseline/cut/recovery behavior.
9. **Target scope is part of the claim.** A narrow resource cannot be implemented by silently cutting unrelated traffic.
10. **Residual state must be noninterfering.** Excluding provider internals from portable snapshot state does not permit those internals to corrupt a later Episode.
11. **Mechanism neutrality needs mechanism-independent evidence.** At least two materially independent control classes must exercise the same portable semantics before acceptance-oriented re-review can close.

## NPR-001 — Materialized endpoint identity and DNS boundary

**Decision: CLOSED AS PROTOCOL SEMANTICS.**

Base v0.1 uses a materialized canonical TCP endpoint identity rather than a hostname or unresolved address set.

For a certified path, endpoint semantics bind at least:

- address family;
- exact network-address value;
- TCP port;
- endpoint role within the controlled path.

Textual formatting of an address is not semantic identity; a later normative serialization may define canonical text/bytes without changing this decision.

If a Scenario starts from a hostname, DNS/name resolution happens before the Network Control execution identity is finalized. The selected literal destination is then bound immutably for the Episode. DNS cache policy, TTL, resolver selection, address ordering, address-family racing, and dynamic DNS updates remain outside base Network Control semantics.

Base v0.1 does not permit hidden fallback to another destination address within the same certified attempt. If another address is to be tried, it is a distinct attempt with a distinct attempt identity.

For a terminating intermediary, the Subject-visible destination endpoint and evaluator-controlled upstream fixture endpoint may differ. For a non-terminating packet-path mechanism they may be the same destination endpoint. Both are bound where distinct.

Private provider topology beyond the declared portable boundaries is not exposed merely to satisfy endpoint identity.

## NPR-002 — Logical controlled path across terminating and non-terminating mechanisms

**Decision: CLOSED AS PROTOCOL SEMANTICS.**

A controlled path is a **logical certified exchange path** between the declared Subject-visible transport boundary and the evaluator-controlled upstream fixture boundary.

It is not one provider-native socket, 5-tuple, proxy object, qdisc/filter handle, route entry, or connection ID.

Two mechanism topologies are admissible to the same base claim:

1. a non-terminating path-control mechanism in which the Subject-facing TCP connection reaches the upstream fixture through packet/routing/firewall control; and
2. a terminating/intercepting mechanism in which the Subject-facing TCP connection terminates at an intermediary that creates one corresponding upstream transport connection to the bound fixture endpoint for that certified attempt.

A terminating mechanism may therefore contain distinct Subject-facing and upstream native connections, but those native identities are implementation detail. It may not perform hidden upstream retry, reconnect, alternate-endpoint selection, or alternate-path fallback within the same certified attempt. Portable conformance requires equivalent observable baseline, active-cut, clear/recovery, target-scope, and path-coverage behavior at the declared AVP boundaries.

Native peer/socket identity, source ephemeral port, sequence numbers, connection IDs, or intermediary topology do not become portable outcome identity.

## NPR-003 — Deterministic exchange grammar and completion predicate

**Decision: CLOSED AS PROTOCOL SEMANTICS.**

Every certified fresh attempt materializes an exact byte exchange before the attempt begins.

The attempt binds:

- exact non-empty `requestBytes`;
- exact non-empty `expectedResponseBytes`;
- an immutable exchange-program identity;
- an evaluator-generated attempt-unique challenge incorporated into the request/expected-response pair;
- the selected path/endpoints;
- the attempt identity;
- the finite observation budget defined by NPR-005.

The fixture contract is deterministic: for a valid request challenge it emits the exact expected response bytes for that attempt. The concrete downstream wire encoding may be specified later, but it must preserve these exact-byte semantics and must not introduce HTTP, TLS, DNS, packet-segmentation, or provider framing authority.

A baseline/recovery attempt **completes successfully** only when:

1. a fresh Subject-facing TCP connection is established to the selected materialized destination;
2. where a terminating topology is used, exactly one corresponding upstream connection initiation targets the bound fixture endpoint;
3. the exact request bytes are emitted once;
4. the exact expected response byte sequence is received in order before the evaluator-owned observation budget expires; and
5. no mismatch occurs before the expected byte sequence is complete.

TCP read/write call boundaries and TCP segment boundaries are irrelevant. Completion does not depend on native exception class, FIN/RST identity, packet counts, or provider-specific framing.

The attempt-unique challenge prevents a stale cached response or a response from a previous attempt from satisfying current exchange completion.

## NPR-004 — Fresh-attempt identity and retry/fallback closure

**Decision: CLOSED AS PROTOCOL SEMANTICS.**

One portable certified attempt has one evaluator-assigned `attemptId` and exactly one Subject-facing connection initiation to the selected materialized destination endpoint.

For one attempt:

- a connection established before the attempt MUST NOT be reused;
- connection pooling MUST NOT satisfy freshness;
- automatic destination-address fallback is prohibited;
- automatic Subject/client reconnect is prohibited;
- application retry is prohibited;
- a terminating/intercepting intermediary may perform exactly one corresponding upstream connection initiation to the bound upstream fixture endpoint;
- intermediary upstream reconnect, retry, alternate-endpoint selection, or alternate-path fallback is prohibited within the same certified attempt;
- any retry/fallback that the evaluator intentionally performs receives a new `attemptId`, fresh challenge, and independent result.

An implementation that cannot suppress or detect hidden retry/fallback at either the Subject-facing or terminating-intermediary boundary cannot claim the base v0.1 attempt semantic for that operation.

Conformance must include behavior that exposes pooling/reuse/fallback violations without branching on provider names.

## NPR-005 — Finite evaluator-owned exchange observation budget

**Decision: CLOSED AS PROTOCOL SEMANTICS.**

Every certified attempt binds an explicit positive finite `exchangeObservationBudget` as immutable execution identity.

The budget:

- is selected/materialized by governed AVP Scenario/Evaluator semantics rather than privately by the provider;
- is measured by an evaluator/control-owned monotonic elapsed-time source;
- applies to the portable exchange completion predicate;
- is visible to conformance/evidence logic as governed execution input but need not be Subject-visible if the Scenario security model keeps it private;
- MUST NOT be replaced by provider-native connect/read timeout policy, arbitrary sleep, wall-clock timestamps, or Subject self-report.

For active-cut verification, **transport cut succeeds when the exact certified exchange does not complete within this bound after the attempt is admitted at the applicable post-settlement boundary**.

An early refusal/reset/close/unreachable result is allowed to terminate the attempt earlier, but native failure identity does not change the portable cut result. A silent blackhole is decided only by expiry of the evaluator-owned bound.

This finite bound is a verification condition. It is not a claim that network latency is controlled, does not define packet timing, does not virtualize TCP timers, and does not imply Time Control support.

Missing, zero/non-finite, ambiguous, stale, drifted, provider-private, or implementation-substituted observation bounds fail closed.

## NPR-006 — Activation-settlement sequencing

**Decision: CLOSED AS PROTOCOL SEMANTICS.**

Activation sequencing is:

1. qualifying pre-trigger Subject traffic executes under Environment rules;
2. the Environment activation condition becomes satisfied;
3. only then may Network Control begin activation settlement;
4. a privileged Evaluator/Control settlement probe runs as its own fresh attempt with its own attempt identity/challenge;
5. the probe binds the same materialized path, endpoints, exchange program, and observation-budget semantics as the later certified Subject-side attempt;
6. settlement succeeds only if that privileged probe satisfies the active transport-cut predicate;
7. after settlement succeeds, the later certified Subject-side post-activation attempt is admitted as a **distinct** fresh attempt and must independently satisfy transport cut.

Settlement probes are not Subject task traffic, do not increment or satisfy Environment occurrence counters, and are not exposed as Subject-controlled fault APIs.

A later failed Subject attempt cannot retroactively validate a settlement probe that completed successfully or was never validly run. `FalseSettledFaultAdapter` remains a required negative direction.

## NPR-007 — Deterministic recovery stability / anti-flap witness

**Decision: CLOSED AS PROTOCOL SEMANTICS.**

Provider clear acknowledgement remains non-authoritative.

After privileged clear, base v0.1 recovery settlement requires **two consecutive independent privileged fresh recovery probes** through the same materialized path/endpoints and exchange program. Each probe:

- has a new attempt identity and challenge;
- uses the governed observation budget;
- must complete the exact baseline exchange successfully;
- must not reuse a prior connection.

Any failure/non-completion within this two-probe sequence fails recovery settlement for the governed operation; implementations do not obtain an unbounded retry loop that can wait until a transient success appears.

After recovery is declared settled, one additional distinct fresh **post-recovery stability witness** must also complete successfully before no-silent-reactivation evidence is complete for the cleared occurrence.

This is an ordered finite witness sequence, not a wall-clock quiet period and not a latency guarantee. A later distinct fault/occurrence remains separately Environment-governed.

## NPR-008 — Provider-neutral behavioral path-coverage proof

**Decision: CLOSED AS PROTOCOL SEMANTICS.**

Portable path coverage is proven by an end-to-end counterfactual witness on one materialized controlled-path identity, not by provider configuration.

The minimum positive proof binds the same path/endpoints/exchange program across:

1. a successful baseline fresh exchange;
2. a successful privileged activation-settlement cut probe after the Environment trigger;
3. a distinct Subject-side certified active-cut attempt that also cannot complete;
4. privileged clear;
5. the deterministic recovery witness sequence; and
6. the post-recovery stability witness.

The attempt-unique challenge ensures that successful baseline/recovery observations correspond to the current evaluator-controlled fixture exchange rather than stale bytes.

A required `BypassFaultAdapter` negative mode routes or otherwise allows the certified Subject-side attempt to escape the advertised control effect while control metadata still claims activation. Because that Subject attempt completes during the active-cut phase, the adapter must fail conformance.

Packet capture, qdisc/proxy object presence, route dumps, service-mesh objects, or other provider-native diagnostics may supplement this evidence but cannot replace the behavioral proof.

## NPR-009 — Target scope and collateral-traffic noninterference

**Decision: CLOSED AS PROTOCOL SEMANTICS.**

The Environment-governed fault target must identify the Network Control resource/path scope being claimed. A narrowly targeted path claim cannot be implemented by silently disabling unrelated traffic.

Rules:

1. if the target selects one controlled path/resource, the implementation may affect only traffic within that declared target scope to the extent required by the selected fault semantic;
2. if the materialized Scenario contains a suitable non-target control path/exchange, that control must remain baseline-capable during the selected path's active cut;
3. if the mechanism cannot isolate the requested narrow scope, materialization must either explicitly broaden the Environment target before execution or fail closed as unsupported;
4. broad environment-wide disruption is conforming only when the Environment target itself explicitly selects that broad scope;
5. payload capture, TLS interception, unrelated topology observation, and broad packet-capture authority remain outside the implied capability.

A target-scope violation is infrastructure/Validity failure, not a valid narrow transport-cut success.

## NPR-010 — Reset/cleanup residual-network-state noninterference

**Decision: CLOSED AS PROTOCOL SEMANTICS.**

Reset/cleanup does not require portable snapshot/restore of live TCP/provider internals, but it must prevent excluded residue from silently changing a later governed execution.

Before a Network Control resource is trusted for the next Episode, materially relevant residual state must satisfy at least one of:

1. it is removed or isolated and a fresh fault-free baseline is independently re-established;
2. unavoidable execution-relevant residue is represented by an immutable provider-neutral policy/input binding sufficient to detect drift for the next execution; or
3. the implementation fails closed because base v0.1 cannot establish trustworthy noninterference for that scenario.

Stale fault rules, stale privileged handles, lingering proxy fault state, materially relevant routing/filter/qdisc state, or other residual effects MUST NOT silently carry authority into the next Episode.

Released/stale control handles remain invalid. Cleanup failure remains infrastructure/Validity information.

This is a noninterference/reset-honesty rule and does not create an `EXACT` or `STATE_EQUIVALENT` live-network restoration claim.

## NPR-011 — Cross-mechanism acceptance-evidence gate

**Decision: CLOSED AS PROTOCOL SEMANTICS; EVIDENCE GATE REMAINS OPEN.**

AEP-0012 cannot become acceptance-ready based on one mechanism class.

Before acceptance-oriented re-review can conclude with no remaining blocker, AVP project evidence **MUST** exercise at least two materially independent control classes against the same portable semantic matrix:

1. a user-space terminating/intercepting TCP control class; and
2. a non-terminating packet-path kernel/routing/firewall-style control class.

The evidence matrix must exercise, at minimum:

- materialized endpoint/path binding;
- exact exchange/challenge identity;
- fresh-attempt identity and hidden retry/fallback rejection at both portable boundaries where applicable;
- qualifying pre-trigger traffic and occurrence no-early-activation;
- finite evaluator-owned cut observation;
- activation-settlement sequencing;
- Subject-side active-cut behavior;
- behavioral bypass detection;
- target isolation/non-target control behavior where materialized;
- privileged clear;
- deterministic two-probe recovery settlement;
- post-recovery no-reactivation witness;
- reset/cleanup residual-state noninterference;
- schedule/control secrecy and failure/Validity separation.

The two classes are compared on portable AVP outcomes and evidence semantics, not provider API equality, native error identity, packet timing, or internal topology.

This requirement is an **AVP acceptance-evidence gate**. It is not a universal requirement that every third-party conforming implementation ship two providers.

This blocker-resolution work unit defines the evidence obligation only. It does not authorize or implement either mechanism class and does not satisfy the evidence gate by prose.

## Superseded Proposed/Draft wording

After these decisions are incorporated into AEP-0012, earlier text is superseded where it implied that the following could be deferred entirely to downstream Spec/TCK:

- endpoint/address-selection semantics;
- fresh-attempt/retry semantics;
- exact exchange completion;
- observation-budget semantics;
- activation-settlement probe sequencing;
- recovery witness cardinality;
- behavioral path-coverage criterion;
- target-isolation behavior;
- residual-state noninterference;
- whether cross-mechanism evidence is mandatory before acceptance.

Draft-era portability/readiness records remain provenance and must not be used to reintroduce those ambiguities.

## Acceptance progression after this work unit

If this candidate is merged after exact-head review, the next gates remain:

1. produce reviewable NPR-011 cross-mechanism acceptance evidence without elevating either mechanism to protocol authority;
2. run acceptance-oriented exact-head protocol re-review against the AEP-0012 semantic candidate plus required evidence;
3. resolve any new semantic blocker discovered by that re-review;
4. obtain a separate explicit protocol-maintainer `Proposed -> Accepted` decision;
5. only after Accepted, continue the authority chain required by governance for Network Control normative Spec, requirement index, Schema where required, provider/language-neutral TCK, backend-neutral harness, and reference implementation.

No generic continuation or green CI substitutes for the explicit lifecycle decision.

## Non-authorization boundary

This record does not authorize:

- AEP-0012 `Proposed -> Accepted` or `Accepted -> Final`;
- Network Control normative Spec/requirement-index/Schema/TCK;
- backend-neutral Network Control conformance harness;
- a user-space proxy provider, kernel/routing/firewall provider, or any other provider implementation;
- provider-specific behavior as protocol semantics;
- generic `BaseNetworkBackend`, plugin framework, or broad `supports_*` bag;
- AEP-0009/AEP-0010/AEP-0011 lifecycle changes;
- release selection/mode changes, tag/GitHub Release/package publication;
- signing/attestation;
- Gate/Evidence weakening;
- merge of this work unit without separate authorization.

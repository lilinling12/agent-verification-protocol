# AEP-0012 Network Control Resource Profile — Formal Proposed Protocol Review

Status: **REVIEWED — ACCEPTANCE BLOCKERS OPEN**

Reviewed baseline: `main@45ab60d0f6e6db41da70a9859033efda52564055`

Review date: 2026-09-03

Decision target: `rfcs/AEP-0012-network-control-resource-profile.md`

Lifecycle result: **KEEP `Proposed`; NOT READY for `Proposed → Accepted`**

Implementation authorization: **NONE**. This review does not authorize Network Control normative Spec, requirement index, Schema, language-neutral TCK, backend-neutral conformance harness, provider/reference runtime, cross-mechanism implementation, release selection, publication, signing, attestation, repository split, or plugin-framework work.

## 1. Executive decision

AEP-0012 remains directionally sound and should not be redesigned from scratch. Formal review retains its protocol-first authority model, Environment ownership of fault identity/target/activation/clear, occurrence no-early-activation rule, Subject/Evaluator/privileged-Control separation, provider-neutral execution identity, fresh-connection base semantics, conservative exclusion of established-connection guarantees, separation of DNS/TLS/HTTP/UDP semantics, deferral of latency/probabilistic-loss claims, reset honesty, and provider/language-neutral execution-sensitive conformance direction.

The review nevertheless finds that the current Proposed text is not yet precise enough for acceptance. The Draft-to-Proposed work established a coherent mechanism-neutral direction, but several boundary and decidability questions remain underspecified at the point where they would otherwise be pushed into a future Spec, fixture, timeout, or provider adapter. Those decisions belong in AEP-0012 before acceptance.

The acceptance gate is therefore closed until **NPR-001 through NPR-011** are resolved in a separate protocol-change work unit and an acceptance-oriented exact-head re-review finds no remaining semantic blocker.

## 2. Review authority and method

The review preserves the repository authority chain:

`AEP lifecycle decision -> Normative Spec -> Schema -> language-neutral TCK -> conformance harness -> reference implementation -> implementation evidence`

No Linux `tc/netem`, firewall/routing facility, Toxiproxy, Envoy/Istio object, cloud network-control API, native socket error, packet trace, provider timeout, or reference implementation gains protocol authority by precedent.

Evidence priority for this review is:

1. AVP's already Accepted Environment/Fabric/Core/Security/Evidence contracts;
2. transport and endpoint standards, especially TCP and deployed multi-address connection behavior;
3. mechanism-independent observability and failure-detection constraints;
4. materially independent kernel/packet-path and user-space proxy mechanisms as implementation evidence only;
5. existing provider documentation only where it exposes portability hazards rather than defines AVP behavior.

Primary interoperability inputs include RFC 9293 TCP, RFC 1122 host requirements, RFC 5482 TCP User Timeout, RFC 8305 connection racing/fallback behavior, Linux traffic-control behavior, user-space TCP-proxy behavior, and HTTP-layer fault-injection behavior. External standards constrain the analysis; they do not become AVP normative text merely by citation.

## 3. Design decisions retained

The following Proposed directions survive formal review:

- one Network Control resource remains narrower than "the Environment network" and represents one independently owned controlled path;
- `resourceKind: network` remains coarse Fabric classification only;
- Environment remains authoritative for fault identity, target, activation condition, occurrence counting, and clear semantics;
- qualifying pre-trigger Subject traffic remains admissible and must not be faulted early;
- control-plane acknowledgement cannot self-certify data-plane activation or recovery;
- settlement must remain evaluator/control-owned and behaviorally demonstrated;
- base v0.1 remains deterministic and fresh-connection-oriented rather than standardizing packet-level behavior;
- established connections created before activation retain no mandatory base disposition guarantee;
- exact latency, probabilistic loss, DNS/name-resolution, TLS interception/failure, HTTP/application faults, UDP semantics, packet counts, segment boundaries, retransmission schedules, and provider-native errors remain outside the mandatory base profile;
- reset continues to mean independently verified fault-free baseline rather than snapshot/restore of live sockets, TCP state, queues, NAT/conntrack, proxy buffers, or provider internals;
- provider-native handles and topology objects remain diagnostics/evidence, not portable identity;
- future schedules and privileged control remain hidden from Subject authority;
- infrastructure/control/settlement failure remains Validity/infrastructure information rather than direct Agent Task Verdict failure;
- portable conformance remains provider-name-neutral, language-neutral, execution-sensitive, and negative-adapter-capable;
- no generic `BaseNetworkBackend`, provider/plugin registry, broad `supports_*` bag, or backend-first compatibility hierarchy is justified.

## 4. Required protocol corrections before acceptance

### 4.1 Close endpoint identity, address-set, and DNS ambiguity

The current AEP declares Subject-side and upstream-side endpoint boundaries but leaves exact endpoint/path declaration syntax downstream. That is too late if endpoint identity itself affects portable meaning.

A hostname can resolve to multiple addresses, and deployed connection establishment can race or fall back across address families or addresses. A fresh exchange can therefore reach a different route than the one the evaluator intended to control even while application-level destination naming appears unchanged.

Before acceptance, AEP-0012 must define a provider-neutral transport endpoint identity model. The base profile should either bind canonical literal transport endpoints or bind an exact materialized address set plus an explicit attempt-selection policy. DNS resolution must not silently become part of base Network Control semantics. Hidden fallback/retry to an alternate address that escapes the selected controlled path must fail closed rather than be treated as the same attempt.

### 4.2 Define one logical controlled-path model across terminating and non-terminating mechanisms

A user-space TCP proxy may terminate the Subject-side TCP connection and create a second upstream connection. Kernel/firewall/routing controls may instead act on one end-to-end transport path without such termination.

The current phrase `controlled TCP path` must therefore be clarified before acceptance so that it neither accidentally requires one native TCP connection nor lets a terminating proxy redefine AVP semantics. AEP-0012 should define the resource as a logical evaluator-bound exchange path between declared Subject-side and upstream-side transport boundaries and state exactly which mechanism topologies are admissible. Native peer/socket/connection identity must remain non-portable.

### 4.3 Make the deterministic baseline exchange protocol-owned

TCP provides an ordered byte stream, not application message boundaries. `deterministic baseline request/response exchange` is therefore already part of portable semantics even if a future schema or fixture eventually carries the bytes.

AEP-0012 must close the semantic grammar needed by v0.1: the exact request byte sequence, exact expected response completion predicate, framing/length rule, and the boundary between one exchange and any later attempt. It must not silently inherit HTTP semantics, provider framing, packet boundaries, socket exception classes, or application retry behavior.

### 4.4 Define fresh-attempt identity and prohibit hidden reuse/fallback

`Fresh TCP connection` must be a protocol concept, not an implementation guess. Connection pools, transparent reconnect loops, proxy retries, address fallback, Happy-Eyeballs-style racing, or stale socket reuse can otherwise turn one portable observation into several hidden native attempts.

AEP-0012 must define one fresh-attempt identity and establish that:

1. it cannot reuse a pre-existing connection;
2. retry/fallback creates a separately identified attempt;
3. one failed selected route cannot be masked by an automatic alternate route;
4. the TCK can distinguish fresh attempts from hidden pooling/reuse without provider-name branching.

### 4.5 Give transport-cut observation a finite protocol-owned verification bound

Current Proposed semantics allow `transport cut` to manifest as refusal, reset, close, unreachable behavior, timeout/blackhole, or another native mechanism while rejecting arbitrary sleep as proof. That is correct in direction but incomplete for decidability.

TCP itself does not expose one portable finite moment at which a silent peer/path is universally known dead. A blackhole-style cut therefore cannot be certified merely by waiting an implementation-chosen duration.

Before acceptance, the protocol must bind a finite evaluator-owned observation budget/deadline for the certified fresh exchange. The bound is a verification condition, not a latency guarantee, packet-timing guarantee, or requirement for Time Control. `Transport cut` succeeds only when the deterministic baseline exchange has not completed within that declared observation bound after the relevant admission/settlement boundary. Missing, ambiguous, drifted, or implementation-private bounds must fail closed.

The timeout source must remain evaluator/control-owned and based on a monotonic observation suitable for conformance. Subject self-report and provider-native timeout policy cannot define the portable result.

### 4.6 Separate activation-settlement probes from the certified post-activation attempt

The current AEP says activation is settled when an independent data-plane fresh attempt proves the cut and also requires a post-activation fresh exchange in the mandatory flow. Formal review requires an explicit non-circular sequencing rule.

AEP-0012 must state that:

1. the Environment activation condition is satisfied first;
2. a privileged evaluator/control-owned settlement probe may then establish data-plane activation;
3. that probe cannot count as Subject task traffic, mutate occurrence counting, or consume the separately certified Subject-side fresh attempt;
4. settlement and certified attempt use the same materialized endpoint/path/fixture identity;
5. a later unrelated network failure cannot retroactively validate a false settlement claim.

`FalseSettledFaultAdapter` must fail for the actual settlement semantics, not merely because a later attempt also happens to fail.

### 4.7 Define a finite recovery-stability predicate

The current AEP correctly rejects clear acknowledgement as recovery evidence but leaves successful fresh exchange(s) deliberately open. One transient success can falsely certify recovery while an intermittent or partially cleared fault remains.

Before acceptance, AEP-0012 must select a finite protocol-owned recovery predicate: an exact bounded sequence of clean fresh exchanges or another deterministic evaluator-owned barrier that establishes the profile's recovery claim without introducing latency semantics. Recovery probes must use the same bound path/endpoint/fixture identity, and the no-silent-reactivation rule must be exercised after the recovery witness rather than inferred from rule removal.

### 4.8 Close the behavioral path-coverage proof criterion

The AEP requires behavioral path-coverage proof and a `BypassFaultAdapter` negative direction, but the positive portable proof remains underspecified. Provider topology/configuration cannot become sole authority, yet a selected exchange that happens to fail is not by itself proof that the intended control point caused the result.

AEP-0012 must define the smallest provider-neutral coverage proof sufficient for conformance. The recommended direction is a paired baseline -> active cut -> recovery behavioral witness over the same materialized path identity, combined with an explicit bypass-negative implementation that remains capable of baseline exchange while evading the selected control point. If an alternate route can silently satisfy the same declared attempt, conformance must fail closed. Packet traces/configuration may supplement this evidence but cannot replace it.

### 4.9 Define target scoping and collateral-traffic noninterference

The Security section requires the control point not to expose unrelated Environment traffic, but acceptance also needs a behavioral target-isolation rule. A broad firewall or proxy rule could cut the selected exchange while indiscriminately disrupting unrelated traffic and still appear to satisfy the current selected-path claim.

AEP-0012 must define the minimum target-scoping semantics for one selected Network Control resource. Where the materialized scenario includes non-target traffic, portable evidence should prove at least one evaluator-owned non-target control flow remains unaffected. An implementation cannot claim a narrowly targeted resource by cutting all network traffic unless the Environment fault target itself explicitly selects that whole scope. Payload capture and TLS interception remain outside this capability.

### 4.10 Add residual network-state noninterference to reset/cleanup

Excluding live sockets, conntrack/NAT state, kernel queues, proxy buffers, resolver caches, and provider internals from snapshot state is correct, but those residuals can still affect the next Episode's baseline, cut, or recovery behavior.

AEP-0012 must require reset/cleanup to establish one of:

1. isolation/cleanup proving materially relevant residual network state cannot interfere with the next governed execution;
2. immutable execution identity/policy binding for any unavoidable relevant residue; or
3. a fail-closed declaration that the base profile is insufficient for the scenario.

Stale fault rules, stale privileged handles, lingering proxy state, or relevant packet-path residue must not silently survive into a new Episode. This remains a noninterference rule, not a false `STATE_EQUIVALENT` claim for network internals.

### 4.11 Require cross-mechanism acceptance evidence before `Accepted`

Current text says materially independent implementation classes should be exercised "where practical" and leaves open whether that evidence is required before acceptance or only before an official reference claim. For a mechanism-neutral Network Control protocol, that is too weak at the acceptance boundary.

Before an acceptance-oriented re-review can close, evidence must exercise at least two materially independent control classes. The recommended minimum is:

- one user-space terminating/intercepting TCP proxy class; and
- one packet-path kernel/routing/firewall-style control class.

The evidence must test portable semantics rather than provider API equality: endpoint/path binding, fresh-attempt identity, pre-trigger/no-early-activation behavior, finite cut observation, settlement sequencing, bypass detection, target isolation, clear/recovery stability, no-reactivation, and cleanup/noninterference.

This is an **AVP AEP acceptance-evidence requirement**, not a requirement that every third-party conforming implementation support multiple providers.

## 5. Acceptance blocker ledger

The formal review opens the following blockers:

- **NPR-001 — Controlled endpoint/address-set and DNS boundary**
- **NPR-002 — Logical controlled path across terminating and packet-path mechanisms**
- **NPR-003 — Deterministic baseline exchange grammar/completion predicate**
- **NPR-004 — Fresh-attempt identity and retry/fallback closure**
- **NPR-005 — Finite transport-cut observation budget**
- **NPR-006 — Activation-settlement probe versus certified post-activation attempt**
- **NPR-007 — Recovery settlement stability / anti-flap predicate**
- **NPR-008 — Behavioral path-coverage / bypass proof**
- **NPR-009 — Target scoping and collateral-traffic noninterference**
- **NPR-010 — Reset/cleanup residual-network-state noninterference**
- **NPR-011 — Cross-mechanism acceptance evidence matrix**

The companion `docs/design/alpha3-network-control-resource-proposed-review-blockers.md` is the authoritative review-phase blocker ledger. Formal review completion does not itself close any NPR blocker.

## 6. Recommended final protocol direction

The accepted direction should remain narrow and explicitly observable:

```text
Network Control logical resource
  -> immutable NetworkControl execution binding
       - profile/revision
       - exact Subject-side transport endpoint binding
       - exact upstream-side transport endpoint binding
       - attempt/address-selection policy
       - deterministic baseline exchange identity
       - evaluator observation-bound identity
       - Environment fault identity/target/condition binding
  -> controlled behavioral lifecycle
       - verified baseline
       - no-early-activation
       - evaluator-owned activation settlement
       - certified bounded fresh-exchange cut
       - privileged clear
       - deterministic recovery witness
       - no silent reactivation
       - reset/cleanup noninterference
```

This does not require one universal serialized state image and does not standardize qdisc rules, proxy toxics, packet traces, HTTP filters, native socket errors, timeout exception classes, or provider object models.

Future capabilities may independently govern established-connection termination, bounded latency, probabilistic loss, DNS, TLS, HTTP/application faults, UDP/datagram control, or richer route/topology semantics. They should compose through Environment Fabric rather than appear as optional provider-shaped fields in v0.1.

## 7. Cross-contract judgment

The existing Environment composition remains correct but should be made testably explicit during blocker resolution:

- Environment occurrence counting and no-early-activation precede Network Control settlement;
- Core `QUIESCING` admission closure must not be repurposed as an arbitrary network-idle rule;
- evaluator settlement probes are privileged verification traffic, not hidden Subject actions;
- Network Control failure affects infrastructure/Validity unless another contract explicitly maps a verified Subject outcome to Task Verdict;
- cleanup authority expires with the governed resource/fault lifecycle and must not resurrect stale control.

None of these conclusions justify changing AEP-0009 or Core in this formal-review PR. If blocker resolution discovers a real parent-contract contradiction, it must be handled through a separately reviewed cross-contract change rather than silently patched downstream.

## 8. Governance outcome

Formal Proposed Review outcome:

```text
AEP-0012 lifecycle: Proposed
Formal review: REVIEWED — ACCEPTANCE BLOCKERS OPEN
NPR-001..NPR-011: OPEN
Proposed -> Accepted: NOT READY / NOT AUTHORIZED
Network Control normative Spec/index: NOT AUTHORIZED
Network Control Schema: NOT AUTHORIZED
Network Control TCK: NOT AUTHORIZED
Network Control conformance harness: NOT AUTHORIZED
Provider/reference implementation: NOT AUTHORIZED
Cross-mechanism implementation/acceptance work: NOT AUTHORIZED by this review alone
Release/tag/package publication: NOT AUTHORIZED
Signing/attestation: NOT AUTHORIZED
Repo split/plugin framework: NOT AUTHORIZED
```

After this review evidence is itself reviewed and adopted, the next substantive protocol work is a **separate AEP-0012 blocker-resolution PR**, followed by an acceptance-oriented exact-head protocol re-review. `Proposed -> Accepted` remains a separate explicit protocol-maintainer lifecycle decision after all blockers are demonstrably closed.

## 9. Non-authoritative implementation note

This review intentionally does not prescribe a Toxiproxy, Linux namespace/qdisc/firewall, Envoy/Istio, cloud, or other backend structure. Implementation experiments may later provide evidence for NPR-011, but they cannot precede or redefine the accepted portable semantics. The project rule remains: **split responsibilities; do not abstract protocol semantics**.

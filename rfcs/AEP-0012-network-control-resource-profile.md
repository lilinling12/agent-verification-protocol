# AEP-0012 — Network Control Resource Profile v0.1

- Status: Proposed
- Authors: AVP maintainers and contributors
- Created: 2026-09-02
- Portability audit: `docs/design/alpha3-network-control-resource-portability-audit.md`
- Proposed-readiness evidence: `docs/design/alpha3-network-control-resource-proposed-readiness-audit.md`
- Lifecycle decision: `docs/acceptance/alpha3-aep-0012-proposed-decision.md`
- Formal Proposed review: `docs/design/alpha3-network-control-resource-formal-proposed-review.md`
- Proposed blocker resolution: `docs/design/alpha3-network-control-resource-proposed-blocker-resolution.md`
- Parent: AEP-0009 — Environment Fabric Composition and Capability Contract (`Accepted`)
- Target AVP version: Unselected future protocol version
- Alpha phase: Alpha 3 — Environment Fabric / Network Control Resource

## Summary

AEP-0012 defines the portable direction for the first Network Control Resource profile under AVP Environment Fabric.

The core rule is:

> AVP standardizes an observable controlled-network-path verification boundary; proxy APIs, kernel queue disciplines, firewall/routing rules, service-mesh objects, native socket errors, and other provider mechanics remain implementation details and must not become protocol semantics by precedent.

The reconciled v0.1 design is deliberately narrow. One independently owned resource represents one declared **logical controlled TCP exchange path** between a Subject-visible transport boundary and an evaluator-controlled upstream fixture boundary. Its mandatory base claim is limited to deterministic exact-byte fresh-attempt baseline exchange, Environment-governed activation, independently observed transport-cut settlement, a distinct Subject-side active-cut attempt, privileged clear, deterministic fresh-attempt recovery, target/path-coverage evidence, and reset/cleanup noninterference.

Established-connection termination, exact latency, probabilistic packet loss, DNS/name-resolution failure, TLS interception, HTTP/application faults, UDP behavior, packet counts, TCP segment boundaries, retransmission timing, and provider-native socket error identity are not mandatory base semantics.

AEP-0012 is **Proposed**. Formal Proposed review identified NPR-001..NPR-011; this candidate incorporates the protocol-semantic decisions for those blockers. `Proposed` does not make these choices Accepted or normative and does not authorize Network Control Spec/Schema/TCK, a conformance harness, provider/reference implementation, release selection, publication, signing, or attestation. Cross-mechanism acceptance evidence remains required before acceptance-oriented re-review can close.

## Problem

A network fault is not one portable packet-level primitive. Implementations inject effects at materially different layers:

- kernel traffic-control, firewall, routing, or namespace mechanisms affect packets/routes subject to host-kernel timing and queue behavior;
- user-space TCP proxies can reject, stall, close, reset, or forward connections without reproducing kernel-identical mechanics;
- HTTP proxies/service meshes can delay or abort requests while the underlying transport remains available;
- DNS controls affect name resolution and caches rather than an already-resolved TCP path;
- TLS interception/termination changes endpoint authentication and trust behavior;
- browser, container, VM, host, and remote-network boundaries determine whether selected Subject traffic actually crosses a control point.

AVP must therefore define observable verification properties rather than copy one provider API. Provider configuration success, packet traces, native error strings, qdisc/proxy IDs, or service-mesh objects cannot define portable conformance by themselves.

## Existing AVP authority reused

AEP-0012 specializes existing contracts and does not create competing lifecycle, identity, evidence, or security systems.

### Environment v0.1

Reused unchanged:

- authoritative Environment ownership and ScenarioInstance binding;
- evaluator-controlled fault identity, target, activation condition, and clear semantics;
- occurrence-based no-early-activation semantics;
- evaluator-private future fault schedules;
- actor-scoped Subject observation;
- evaluator-authoritative observation/projection where defined;
- Environment logical time without implying wall-clock/kernel/network timer virtualization;
- reset honesty and stale/foreign/released-handle failure;
- lifecycle, infrastructure condition, Validity, and Task Verdict separation;
- Artifact identity for retained exact Evidence bytes.

`AVP-ENVIRONMENT-010` remains top-level authority for scheduled fault identity, target, activation condition, and clear semantics. Network Control adds subordinate data-plane settlement only after the Environment activation condition is satisfied.

### Environment Fabric

Reused unchanged:

- `resourceKind: network` as coarse classification only;
- Resource Capability identity/revision and REQUIRED/OPTIONAL participation;
- Resource Capability versus Subject Capability separation;
- resource identity and immutable execution-input binding;
- per-resource/composite result honesty and no implicit cross-resource atomicity;
- Security/Evidence composition, execution-sensitive conformance, and retry-safe cleanup.

`resourceKind: network` alone does not claim transport-cut or recovery semantics.

### Scenario, Core, Security, and Evidence

Reused unchanged:

- unresolved required execution inputs fail before Episode execution;
- materialized execution semantics remain immutable during an Episode;
- Core lifecycle remains the only Episode lifecycle;
- `QUIESCING` closes admission of new Subject-requested side effects while already accepted work may settle;
- Subject, Evaluator, and privileged Control authority remain separated;
- provider credentials/native control handles do not enter Subject execution context;
- exact retained bytes use Artifact identity;
- technology names do not inflate `SecurityAssurance`.

## Standards and interoperability basis

### TCP

TCP exposes a reliable ordered byte stream, not portable application-write or packet boundaries. Implementations differ in segmentation, buffering, retransmission timing, congestion/queue behavior, reset presentation, and native errors.

Therefore portable Network Control conformance is expressed through fresh connection attempts and deterministic end-to-end exact-byte exchanges. Exact packet counts, TCP segment boundaries, retransmission schedules, queue state, native socket error strings, or application read/write call boundaries are excluded from portable outcome identity.

TCP also does not provide one provider-independent short liveness event for a silent path. Portable cut observation therefore uses an evaluator-owned finite observation budget rather than provider-native timeout behavior.

### Kernel and proxy mechanisms

Kernel traffic-control/routing/firewall mechanisms and user-space TCP proxies are useful independent implementation classes. Neither is protocol authority. Timer granularity, queueing, TCP Small Queues, offload, host scheduling, buffering, and provider event loops make exact timing/error equivalence non-portable.

Provider API completion is control-plane evidence only; it cannot prove data-plane activation or recovery settlement.

### Application, DNS, and TLS layers

HTTP abort/status/delay is application-layer behavior and cannot satisfy a transport-cut requirement merely because a request failed. DNS/name-resolution behavior has resolver/cache/TTL and address-selection semantics distinct from a materialized TCP destination. TLS interception changes endpoint-authentication semantics and is not implied by Network Control support.

If a Scenario begins from a hostname or unresolved address set, resolution and selection occur before the Network Control execution identity is finalized. Base v0.1 binds the resulting literal TCP endpoint and does not perform hidden DNS/address-family fallback as part of one certified attempt.

## Portable resource boundary

One Network Control v0.1 resource represents one independently owned **logical controlled TCP exchange path** between:

1. a declared Subject-visible transport boundary; and
2. a declared evaluator-controlled upstream fixture boundary.

The resource is narrower than "the Environment network". Traffic outside the selected target scope may remain uncontrolled and, when a non-target control is materialized, must remain baseline-capable during a narrow selected-path cut.

The logical path is not one provider-native connection object. Both of these topology classes can satisfy the same portable claim:

- a non-terminating packet/routing/firewall-style control path; and
- a terminating/intercepting TCP mechanism that accepts a Subject-side connection and creates or manages distinct upstream transport state.

Portable conformance compares declared-boundary behavior, not native topology equality.

Portable resource identity does not use Linux interface/qdisc/filter handles, proxy listener/toxic IDs, service-mesh resource names, cloud rule IDs, socket descriptors, process IDs, ephemeral ports, sequence numbers, or equivalent mechanism-native objects.

### Materialized TCP endpoint identity

Each endpoint relevant to the certified path is materialized before Episode execution and binds at least:

- address family;
- exact literal network-address value;
- TCP port;
- endpoint role.

Textual formatting is not semantic identity. A later normative serialization may define canonical representation without changing this rule.

If Subject-visible destination and upstream fixture endpoint differ because of a terminating intermediary, both are bound where distinct. Provider-private topology between those boundaries is not exposed merely to satisfy endpoint identity.

A hostname, resolver policy, TTL, dynamic DNS state, address ordering, multi-address racing, or automatic alternate-address fallback is not part of base v0.1 attempt semantics.

### Behavioral path-coverage proof

Configuration presence is insufficient. Conformance must behaviorally establish that selected traffic actually traverses the claimed logical path and must reject an implementation that advertises the capability while secretly bypassing the control point.

The positive proof binds one immutable path/endpoints/exchange program across baseline, activation-settlement cut, distinct Subject-side active cut, privileged clear, deterministic recovery, and post-recovery stability.

A required `BypassFaultAdapter` negative mode must allow the certified Subject attempt to escape the advertised control effect while control metadata claims activation; because the Subject attempt then completes during the active-cut phase, conformance must fail.

Provider-native packet traces or configuration may be useful diagnostics, but are not the sole portable proof.

## Mandatory v0.1 semantics

### Certified fresh attempt

Every certified attempt is independently materialized and binds:

- a unique evaluator-assigned attempt identity;
- the selected logical controlled-path identity;
- the materialized endpoint identities;
- exact non-empty request bytes;
- exact non-empty expected-response bytes;
- an immutable exchange-program identity;
- an evaluator-generated attempt-unique challenge incorporated into the request/expected-response pair; and
- a positive finite evaluator-owned exchange observation budget.

One certified attempt contains exactly one Subject-facing TCP connection initiation to the selected materialized destination.

For one attempt:

- a connection established before the attempt MUST NOT be reused;
- connection pooling MUST NOT satisfy freshness;
- automatic destination-address fallback is prohibited;
- automatic Subject/client reconnect is prohibited;
- application retry is prohibited;
- a terminating intermediary may create internal upstream transport state as implementation detail, but that does not create another Subject attempt;
- any evaluator-intended retry/fallback receives a new attempt identity, a fresh challenge, and an independent result.

An implementation that cannot suppress or expose hidden Subject-side retry/fallback cannot claim base v0.1 for that operation.

### Deterministic exact-byte exchange

The evaluator-controlled fixture deterministically maps the attempt's valid request challenge to the exact expected response bytes.

A baseline/recovery attempt completes successfully only when:

1. a fresh Subject-facing TCP connection is established to the selected materialized destination;
2. the exact request bytes are emitted once;
3. the exact expected response byte sequence is received in order before the evaluator-owned observation budget expires; and
4. no byte mismatch occurs before the expected sequence is complete.

TCP read/write call boundaries and TCP segment boundaries are irrelevant. HTTP, TLS, DNS, provider framing, native exception classes, FIN/RST identity, packet counts, and native error codes do not define exchange completion.

The attempt-unique challenge prevents stale cached bytes or a previous attempt's response from satisfying the current exchange.

### Evaluator-owned observation budget

Every certified attempt binds a positive finite `exchangeObservationBudget` as immutable execution identity.

The budget:

- is selected/materialized by governed AVP Scenario/Evaluator semantics, not privately by a provider;
- is measured by an Evaluator/Control-owned monotonic elapsed-time source;
- applies to the portable exact-byte completion predicate;
- may remain evaluator-private where Scenario security semantics require that; and
- MUST NOT be replaced by provider-native connect/read timeout policy, arbitrary sleep, wall-clock timestamps, or Subject self-report.

For active-cut verification, transport cut succeeds when the exact certified exchange does not complete within this bound after admission at the applicable post-settlement boundary. An early refusal/reset/close/unreachable outcome may terminate the attempt earlier, but native failure identity does not change the portable result. A silent blackhole is decided by expiry of the evaluator-owned budget.

This budget is a finite verification condition, not a latency guarantee, packet-timing contract, wall-clock virtualization promise, or Time Control capability.

Missing, zero/non-finite, ambiguous, stale, drifted, provider-private, or implementation-substituted observation budgets fail closed.

### Baseline forwarding

Before the selected fault is active, a deterministic evaluator-controlled upstream fixture must complete a certified fresh exact-byte baseline exchange through the declared logical path.

If the baseline cannot be established, the fault claim is not validly testable.

### Environment-governed activation

The Environment owns fault identity, target, and activation condition. For occurrence-based activation:

- qualifying pre-trigger Subject traffic is admissible and may be required to reach the occurrence;
- the fault MUST NOT affect that traffic before the declared occurrence;
- preparing provider-private control state before the occurrence does not make the fault active;
- Network Control does not reinterpret occurrence counting.

After the Environment condition is satisfied, Network Control may enter a subordinate settling phase before post-activation fault-sensitive Subject observations are admitted.

### Activation settlement

Activation sequencing is strictly ordered:

1. qualifying pre-trigger Subject traffic executes under Environment rules;
2. the Environment activation condition becomes satisfied;
3. only then may Network Control begin activation settlement;
4. a privileged Evaluator/Control settlement probe runs as its own certified fresh attempt;
5. that probe binds the same logical path, endpoints, exchange program, and observation-budget semantics as the later Subject-side active-cut attempt;
6. settlement succeeds only if the privileged probe satisfies transport cut; and
7. only after settlement succeeds may the distinct Subject-side certified post-activation attempt be admitted.

Settlement probes are privileged verification traffic. They are not Subject task traffic, do not increment/satisfy Environment occurrence counters, and do not expose fault-control authority to Subject code.

Provider API success, rule/object existence, metadata flags, Subject self-report, or arbitrary sleep are insufficient by themselves.

A later Subject failure cannot retroactively validate a settlement probe that was absent or invalid. `FalseSettledFaultAdapter` remains a required negative direction.

Failure to settle is infrastructure/Validity information, not Agent Task Verdict failure by itself.

### Fresh-attempt transport cut

After activation settlement, the distinct Subject-side certified fresh attempt through the same logical path must not complete the deterministic exact-byte baseline exchange within its evaluator-owned observation budget while the cut remains active.

The protocol does not prescribe refusal, RST, FIN/close, timeout/blackhole, unreachable behavior, route withdrawal, proxy termination, or another native mechanism. Exact exception classes, numeric OS error codes, localized error text, TCP flags, packet counts, or retransmission schedules are non-portable diagnostics.

### Established connections

Base v0.1 makes **no guarantee** about a connection established before activation. It may be preserved, drained, reset, blackholed, partially progress, or fail according to implementation mechanics.

A future use case that requires established-connection termination must define a separately reviewed capability/profile and TCK rather than hiding that requirement inside base `transport cut`.

### Target scope and non-target noninterference

The Environment-governed fault target identifies the Network Control resource/path scope being claimed.

For a narrow target:

- the implementation may affect only traffic within that declared scope to the extent required by the fault semantic;
- if the materialized Scenario includes a suitable non-target control path/exchange, that control must remain baseline-capable while the selected path is cut;
- if the mechanism cannot isolate the requested scope, materialization must explicitly broaden the Environment target before execution or fail closed as unsupported.

Indiscriminately cutting unrelated traffic cannot satisfy a narrowly targeted resource claim. Broad Environment-wide disruption is conforming only when the Environment target itself explicitly selects that broad scope.

A target-scope violation is infrastructure/Validity failure, not valid narrow transport-cut success.

### Clear and deterministic recovery

Clear is a privileged operation against the selected Environment-governed fault instance. Provider acknowledgement of rule removal does not prove recovery.

After clear, recovery settlement requires **two consecutive independent privileged certified fresh recovery probes** through the same logical path/endpoints/exchange program. Each probe has a new attempt identity/challenge, uses the governed observation budget, must complete the exact baseline exchange, and must not reuse a prior connection.

Any failure/non-completion in that finite two-probe sequence fails recovery settlement. The implementation does not obtain an unbounded retry loop that can wait for a transient success.

After recovery settlement, one additional distinct fresh **post-recovery stability witness** must complete successfully before no-silent-reactivation evidence is complete for the cleared occurrence.

This is an ordered finite witness, not a wall-clock quiet period or latency guarantee. Base recovery does not promise repair of a connection already broken by the prior fault.

After clear, the same governed occurrence must not silently reactivate. A later distinct occurrence/fault remains separately Environment-governed.

## Deferred and separated semantics

### Latency

Latency is not mandatory base v0.1. A future bounded-latency profile requires explicit measurement endpoints, monotonic clock requirements, baseline treatment, additive-versus-total definition, tolerance window, warm-up/sample policy, host-noise treatment, timeout interaction, and platform-independent acceptance statistics.

The evaluator-owned finite exchange observation budget defined above is a verification-decision bound only; it does not make latency a base Network Control semantic.

### Probabilistic loss

Probabilistic packet loss is not mandatory base v0.1. A future loss profile requires an explicit observation unit, sample/confidence rule, and transport-retransmission interaction model. The deterministic base cut is named **transport cut**, not `100% packet loss`.

### DNS, TLS, HTTP/application, and UDP

DNS/name-resolution faults, TLS interception/failure, HTTP/application abort/delay, and UDP/datagram behavior require separate reviewed semantics. None is silently inferred from base TCP transport cut.

Pre-execution hostname resolution may be used only to materialize the literal TCP endpoint bound into execution identity; DNS behavior itself is not certified by this profile.

## Time and ordering boundary

Environment logical time is not host wall time, kernel timer time, proxy event-loop time, or TCP retransmission time. Network Control does not claim those clocks are virtualized.

The evaluator-owned observation budget uses a monotonic elapsed-time source solely to make a finite verification decision. It does not define exact activation time or deterministic delay.

Any future exact time-triggered activation or deterministic delay claim requires composition with a separately governed Time Control Resource or another reviewed timing contract.

## State, control, observation, and Evidence

Network Control is primarily a controlled-behavior resource, not automatically a snapshot-able byte-state resource.

### Privileged control

Fault preparation/activation coordination, clear, reset, provider administration, fixture controls, settlement probes, recovery probes, and post-recovery stability witnesses remain privileged Evaluator/Control operations unless a separately governed Subject contract grants narrower authority.

### Evaluator and Subject observation

Evaluator observations may include materialized attempt identity, baseline result, activation/recovery settlement, selected exchange outcomes, path-coverage/bypass evidence, target-isolation control results, sanitized diagnostics, fault transition traces, and cleanup diagnostics.

The Subject observes fault consequences only through its authorized ordinary operations. It does not automatically receive future schedules, privileged fault APIs, evaluator-private observation budgets, provider credentials, evaluator probes, native handles, or private topology diagnostics.

### Evidence

Retained exact bytes use Artifact identity. Provider-native configuration/traces may be implementation Evidence, but do not replace the portable behavioral result or become portable resource identity.

## Reset, snapshot, and restore boundary

Base Network Control v0.1 participates in reset by establishing and independently verifying the profile-defined **fault-free baseline** on the selected controlled path.

Base v0.1 does not define snapshot/restore of live sockets/connections, TCP sequence/retransmission state, kernel queues/qdisc/filter state, proxy buffers, NAT/conntrack state, resolver caches, or service-mesh/provider internals.

Those mechanisms are not one stable portable logical state image. Base v0.1 therefore makes no `EXACT` or `STATE_EQUIVALENT` restoration claim for them.

Excluded provider/network residue nevertheless MUST NOT silently alter a later governed execution. Before the resource is trusted for a next Episode, materially relevant residual state must satisfy at least one of:

1. it is removed or isolated and a fresh fault-free baseline is independently re-established;
2. unavoidable execution-relevant residue is represented by immutable provider-neutral policy/input binding sufficient to detect drift; or
3. the implementation fails closed because base v0.1 cannot establish trustworthy noninterference for that Scenario.

Stale fault rules, stale privileged handles, lingering proxy fault state, or materially relevant routing/filter/qdisc residue MUST NOT silently carry authority into the next Episode. Released/stale handles remain invalid. Cleanup failure remains infrastructure/Validity information.

This is a reset-honesty/noninterference rule, not live-network state equivalence.

## Execution-relevant immutable identity

Portable verification identity must bind enough provider-neutral input to interpret and reproduce the claim. Required semantics include:

- Network Control profile/revision;
- selected logical controlled-path resource identity;
- materialized Subject-visible destination endpoint identity;
- materialized upstream fixture endpoint identity where distinct;
- TCP transport declaration;
- Environment fault identity/target/activation-condition references;
- immutable exchange-program identity;
- exact request/expected-response byte identity or content identity sufficient to bind those exact bytes;
- attempt identity and attempt-unique challenge for each certified attempt;
- evaluator-owned finite exchange observation budget;
- execution-relevant immutable configuration outside logical state that may alter the result; and
- provider-neutral policy/input binding for unavoidable relevant residue where reset noninterference depends on it.

Excluded from portable identity are qdisc/filter/firewall handles, proxy IDs, socket descriptors, process IDs, cloud rule IDs, mesh object names, ephemeral ports, sequence numbers, and transient provider-generated control IDs. These may remain sanitized diagnostic Evidence.

Missing, ambiguous, stale, foreign, or drifted required execution identity fails closed.

## Security considerations

Network Control expands privileged Environment authority and can become an interception/exfiltration surface if boundaries are weak.

Required rules:

1. Subject traffic operations remain distinct from Evaluator/Control fault operations.
2. Future fault schedules remain evaluator-private unless explicitly exposed by governed Scenario semantics.
3. Provider/control credentials and packet-capture authority do not enter Subject execution context.
4. The control point must not expose or disrupt unrelated Environment traffic beyond the declared target merely because the implementation can observe/control it.
5. Payload capture and TLS interception are not implied by fault-control capability.
6. Subject-visible diagnostics must not leak private topology or control authority.
7. Provider/container/mesh/kernel labels do not establish `SecurityAssurance` by themselves.
8. Control/settlement failure remains infrastructure/Validity information rather than direct Task Verdict failure.
9. Cleanup must remove privileged fault effects without resurrecting stale authority.
10. Evaluator-private settlement/recovery traffic, hidden schedules, and observation budgets must not become Subject control channels.

A `ScheduleLeakAdapter`-style implementation must fail conformance.

## Failure and Validity semantics

Infrastructure/Validity failures include, where applicable:

- unavailable control point or failed baseline;
- selected traffic bypassing the declared path;
- hidden retry/fallback, stale connection reuse, or ambiguous endpoint materialization;
- unsupported mandatory transport-cut semantic;
- missing/invalid evaluator observation budget;
- activation or recovery settlement failure;
- target-scope/collateral-traffic violation;
- stale/foreign resource/control reference;
- missing/drifted required execution identity;
- loss of Evaluator/Control authority;
- hidden schedule/control leakage;
- cleanup/reset noninterference failure leaving an untrustworthy network state.

Provider-native status/error strings and object IDs are diagnostics, not portable AVP outcome identity.

## Conformance strategy

A future `avp-network-control-v0.1` TCK must be provider-neutral, language-neutral, and execution-sensitive. Mandatory cases execute real behavior at the controlled-path boundary; metadata, mocks, provider configuration, fixture inspection, or self-report cannot substitute for the behavior being certified.

A deterministic local fixture must provide an evaluator-controlled exact-byte upstream service, a Subject-side client with certified retry/fallback suppression, privileged control inaccessible to Subject code, evaluator-controlled ordering, monotonic observation-budget enforcement, independent settlement/recovery probes, target-isolation controls where materialized, and negative implementation modes.

A minimal mandatory execution flow must prove:

1. endpoint/path/exchange identity is fully materialized before Episode execution;
2. baseline certified fresh exchange succeeds;
3. qualifying pre-trigger Subject traffic remains admissible/unfaulted;
4. the Environment activation condition is reached;
5. activation settles through a privileged independent certified cut probe;
6. the distinct Subject-side post-settlement certified attempt cannot complete within its governed observation budget;
7. hidden reuse/retry/fallback cannot convert the selected path into success;
8. bypass is detected;
9. narrow target isolation is preserved against a materialized non-target control where applicable;
10. clear is issued through privileged authority;
11. two consecutive privileged fresh recovery probes succeed;
12. a distinct post-recovery stability witness succeeds and the cleared occurrence does not silently reactivate;
13. future schedule/control material remains hidden;
14. stale/released use fails closed; and
15. cleanup/reset does not leave residual network state that can silently alter the next governed execution.

Required negative directions include:

- `BypassFaultAdapter`;
- `EarlyActivationAdapter`;
- `FalseSettledFaultAdapter`;
- `FalseRecoveryAdapter`;
- `ScheduleLeakAdapter`;
- a stale-connection/pooling reuse negative mode;
- a hidden retry/address-fallback negative mode;
- a target-scope collateral-fault negative mode; and
- a residual-fault cleanup negative mode.

Portable TCK expectations MUST NOT branch on provider/platform names to define different protocol outcomes. Provider-specific setup belongs behind privileged implementation seams.

## Cross-mechanism acceptance evidence

One mechanism class passing future conformance is not enough for AVP to accept its own mechanism-neutral semantic choices.

Before acceptance-oriented AEP-0012 re-review can conclude with no remaining blocker, AVP project evidence **MUST** exercise at least two materially independent control classes against the same portable semantic matrix:

1. a user-space terminating/intercepting TCP control class; and
2. a non-terminating packet-path kernel/routing/firewall-style control class.

The evidence must exercise, at minimum:

- materialized endpoint/path binding;
- exact exchange/challenge identity;
- fresh-attempt identity and hidden retry/fallback rejection;
- qualifying pre-trigger/no-early-activation behavior;
- finite evaluator-owned cut observation;
- activation-settlement sequencing;
- distinct Subject-side active-cut behavior;
- bypass/path-coverage detection;
- target isolation/non-target control behavior where materialized;
- clear and deterministic two-probe recovery settlement;
- post-recovery no-reactivation witness;
- reset/cleanup residual-state noninterference; and
- schedule/control secrecy and Validity/Task-Verdict separation.

The two classes are compared on portable AVP outcomes/evidence, not provider API equality, packet timing, native error identity, or internal topology.

This is an **AVP acceptance-evidence gate**, not automatically a requirement that every third-party conforming implementation ship two providers.

Deferred latency/loss/DNS profiles require their own portability evidence.

## Reference implementation gate

A controlled network-fault reference implementation may begin only after:

1. AEP-0012 reaches the lifecycle state required by governance;
2. Network Control normative Spec and requirement index encode the reviewed semantics;
3. serialized portable resources receive schemas where required;
4. the provider/language-neutral execution-sensitive TCK is reviewable;
5. any backend-neutral fixture/control prerequisites identified by review are closed.

The separate pre-Accepted cross-mechanism acceptance-evidence gate may require purpose-built review evidence before an official reference implementation exists. Such evidence does not confer provider authority or authorize a general backend/plugin architecture.

No generic `BaseNetworkBackend`, provider/plugin framework, or broad `supports_*` capability bag is justified before stable reviewed semantics and real consumers exist.

## Alternatives rejected

The reconciled design rejects:

- provider-first implementation followed by retroactive generalization;
- Linux `tc/netem` or Toxiproxy APIs as protocol authority;
- HTTP abort as transport cut;
- DNS failure as generic network loss;
- unresolved hostname/multi-address fallback inside one certified base attempt;
- connection pooling/stale-socket reuse as a fresh attempt;
- hidden automatic retry/reconnect as part of one certified attempt;
- provider-native timeout or arbitrary sleep as the portable cut predicate;
- one transient recovery success as sufficient recovery settlement;
- indiscriminate Environment-wide cut as evidence of a narrow target;
- provider configuration or packet capture as sole path-coverage proof;
- established-connection termination as an implicit base guarantee;
- mandatory v0.1 latency without a portable timing model;
- mandatory probabilistic loss without a statistical conformance model;
- snapshot/restore of live network/provider internals;
- residual provider/network state silently affecting a later Episode;
- exposing future schedules/control through Subject-visible interfaces;
- generic provider/plugin architecture before a stable extension contract exists.

## Backward compatibility and release boundary

Network Control v0.1 is additive under AEP-0009. Existing Environment/Fabric implementations need not claim it, and `resourceKind: network` remains insufficient by itself. Alpha 2, Relational State, and Browser semantics are unchanged.

No public release version is selected, release-development state remains unchanged, and this AEP does not authorize publication, signing, or attestation.

## Draft design-blocker disposition

The portability audit and Draft→Proposed reconciliation resolved the original Draft blockers as formal-review inputs:

- **NC-BR-001 — CLOSED:** one resource is a declared Subject-side → upstream-side logical controlled TCP path with behavioral path-coverage proof independent of provider identity.
- **NC-BR-002 — CLOSED:** base vocabulary is baseline forwarding, fresh-attempt transport cut, privileged clear, and fresh-attempt recovery; other layer/fault families are not aliases.
- **NC-BR-003 — CLOSED:** Environment owns fault identity/target/condition; occurrence no-early-activation is preserved and activation settlement requires independent post-trigger data-plane proof.
- **NC-BR-004 — CLOSED:** established connections have no base disposition guarantee; a separate profile is required for such a claim.
- **NC-BR-005 — CLOSED:** clear does not self-certify recovery; deterministic fresh successful exchanges prove recovery and the cleared occurrence cannot silently reactivate.
- **NC-BR-006 — CLOSED:** latency is deferred until a portable clock/tolerance/sampling/noise model exists.
- **NC-BR-007 — CLOSED:** probabilistic loss is deferred until observation-unit/statistical conformance semantics exist.
- **NC-BR-008 — CLOSED:** DNS, TLS, HTTP/application, UDP, and TCP path semantics remain layer-distinct.
- **NC-BR-009 — CLOSED:** reset establishes a verified fault-free baseline; live network/provider internals are not base snapshot/restore state.
- **NC-BR-010 — CLOSED:** future schedules/control remain evaluator-private and Network Control does not inflate `SecurityAssurance`.
- **NC-BR-011 — CLOSED:** provider-neutral path/profile/fault/execution inputs bind verification identity; provider handles are diagnostics only.
- **NC-BR-012 — CLOSED:** future TCK is provider/language-neutral, deterministic-fixture-based, execution-sensitive, negative-adapter-capable, and supported by mandatory cross-mechanism AVP acceptance evidence where mechanism independence matters.

Formal Proposed review later refined these choices through NPR-001..NPR-011. Draft-era wording remains provenance and cannot override the later Proposed decisions.

## Proposed acceptance-blocker disposition

Formal Proposed review identified NPR-001..NPR-011. This candidate resolves their protocol meaning as follows:

- **NPR-001 — SEMANTICALLY CLOSED:** base attempts bind literal materialized TCP endpoint identity; DNS/multi-address selection is pre-execution and hidden fallback is prohibited.
- **NPR-002 — SEMANTICALLY CLOSED:** the controlled path is a logical exchange path supporting terminating and non-terminating mechanisms without native-connection identity.
- **NPR-003 — SEMANTICALLY CLOSED:** exact request/expected-response bytes, exchange-program identity, and attempt-unique challenge define deterministic completion.
- **NPR-004 — SEMANTICALLY CLOSED:** one attempt has one Subject-facing fresh connection initiation; pooling/reuse/retry/address fallback cannot hide inside the attempt.
- **NPR-005 — SEMANTICALLY CLOSED:** every attempt binds a finite evaluator-owned monotonic observation budget; provider timeouts/arbitrary sleeps are not authority.
- **NPR-006 — SEMANTICALLY CLOSED:** activation settlement is privileged post-trigger verification traffic and precedes a distinct Subject-side certified active-cut attempt.
- **NPR-007 — SEMANTICALLY CLOSED:** recovery settlement is exactly two consecutive privileged fresh successful probes plus a distinct post-recovery stability witness.
- **NPR-008 — SEMANTICALLY CLOSED:** one end-to-end counterfactual behavioral witness binds baseline/cut/recovery, and `BypassFaultAdapter` must fail.
- **NPR-009 — SEMANTICALLY CLOSED:** target scope is explicit; narrow claims require isolation and non-target control evidence where materialized.
- **NPR-010 — SEMANTICALLY CLOSED:** excluded residual state must be cleaned/isolated, immutably bound where unavoidable, or cause fail-closed noninterference failure.
- **NPR-011 — SEMANTICALLY CLOSED / EVIDENCE OPEN:** at least two materially independent mechanism classes are mandatory AVP acceptance evidence before acceptance-oriented re-review can close; this is not a universal third-party multi-provider requirement.

Protocol-semantic closure does not mean AEP-0012 is acceptance-ready. NPR-011's actual cross-mechanism evidence remains a separate unsatisfied acceptance gate.

## Remaining acceptance gates

Before AEP-0012 can be considered for `Proposed -> Accepted`:

1. the NPR-011 cross-mechanism evidence matrix must be produced and reviewable;
2. an acceptance-oriented exact-head protocol re-review must evaluate this semantic candidate together with that evidence and find no remaining semantic blocker;
3. all applicable exact-head Gates must be green;
4. the protocol maintainer must separately and explicitly authorize `Proposed -> Accepted`.

No Spec/Schema/TCK/provider implementation may silently substitute for an unresolved AEP acceptance decision.

## Non-blocking downstream details

Later Spec/Schema/TCK work may define exact capability/profile spelling, JSON fields/media types/limits, canonical serialized endpoint representation, canonical exchange byte representation/content identity, bounded numeric ranges for the already-required observation budget, requirement/TCK IDs, language-specific SPI names, and provider diagnostic mappings.

Those details are downstream only while they encode the semantics above. They may not choose a different endpoint-selection model, retry model, exchange-completion predicate, observation authority, settlement sequence, recovery cardinality, target-isolation rule, residual-state rule, or cross-mechanism acceptance gate without first amending this AEP.

## Governance boundary

AEP-0012 remains **Proposed** throughout this blocker-resolution work.

This Proposed semantic amendment does not authorize:

- `Proposed -> Accepted` or `Accepted -> Final`;
- Network Control normative Spec, requirement index, schema, capability registration, or TCK adoption;
- backend-neutral harness/fixture implementation;
- a user-space proxy provider, kernel/routing/firewall provider, or any provider as protocol authority/reference implementation;
- a generic provider/plugin framework;
- lifecycle advancement of AEP-0009, AEP-0010, or AEP-0011;
- release selection/mode change, tag, GitHub Release, package publication, signing, or attestation;
- Gate/Evidence weakening;
- repository merge without separate authorization.

After this semantic candidate is exact-head reviewed and separately authorized for squash merge into `main`, the next governed work is the NPR-011 cross-mechanism acceptance-evidence work unit, followed by acceptance-oriented exact-head protocol re-review. Any new semantic blocker discovered there must be resolved before a separate `Proposed -> Accepted` decision can be requested.

## References

- AEP-0009 — `rfcs/AEP-0009-environment-fabric.md`
- Environment contract — `spec/environment/environment-contract.md`
- Environment requirement index — `spec/environment/requirement-index.yaml`
- Environment Fabric contract — `spec/fabric/environment-fabric-contract.md`
- Network Control portability audit — `docs/design/alpha3-network-control-resource-portability-audit.md`
- Formal Proposed review — `docs/design/alpha3-network-control-resource-formal-proposed-review.md`
- Proposed review blocker ledger — `docs/design/alpha3-network-control-resource-proposed-review-blockers.md`
- Proposed blocker resolution — `docs/design/alpha3-network-control-resource-proposed-blocker-resolution.md`
- RFC 9293 — TCP
- RFC 8305 — Happy Eyeballs v2 / multi-address connection racing
- Linux `tc-netem` documentation — implementation evidence only
- Toxiproxy documentation/source — implementation evidence only
- Envoy HTTP fault-filter documentation — layer-separation evidence only
- DNS standards/negative-caching semantics — layer-separation evidence only

External standards and implementation documentation constrain interoperability analysis; they do not become AVP normative semantics merely by citation.
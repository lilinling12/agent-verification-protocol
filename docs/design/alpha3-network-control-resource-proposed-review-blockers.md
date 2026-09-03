# Alpha 3 Network Control Resource Proposed Review Blockers

Status: **OPEN — PROTOCOL EDITS REQUIRED BEFORE ACCEPTANCE RE-REVIEW**

Proposal: AEP-0012 — Network Control Resource Profile v0.1

Formal review baseline: `main@45ab60d0f6e6db41da70a9859033efda52564055`

Formal review record: `docs/design/alpha3-network-control-resource-formal-proposed-review.md`

## Purpose

This record tracks the protocol-semantic blockers identified by the formal Proposed review of AEP-0012.

The formal-review PR intentionally does **not** edit AEP-0012. Keeping the review record and blocker ledger separate from blocker-resolution protocol edits prevents the review from self-approving its own semantic corrections and prevents a future Spec, Schema, TCK, fixture, timeout, or provider implementation from silently filling unresolved protocol meaning.

AEP-0012 remains `Proposed`. The next governed substantive step after adoption of this review is to resolve these blockers in AEP-0012 in a separate protocol-change PR, then perform an exact-head acceptance-oriented re-review. `Proposed -> Accepted` remains a separate explicit protocol-maintainer decision.

## NPR-001 — Controlled endpoint/address-set and DNS boundary

### Finding

The Proposed AEP declares Subject-side and upstream-side endpoint boundaries but defers exact endpoint/path declaration syntax. Endpoint identity is not merely serialization detail: hostnames can resolve to multiple addresses and deployed connection establishment can race or fall back across address families or addresses, allowing a nominally identical destination to exercise a different route.

### Required closure

AEP-0012 must:

1. define portable transport endpoint identity for the base profile;
2. either bind canonical literal transport endpoints or bind an exact materialized address set plus explicit attempt-selection policy;
3. keep DNS/name-resolution semantics outside the base profile unless separately governed;
4. forbid hidden address fallback/retry from silently escaping the selected controlled path;
5. keep the endpoint/path declaration provider-neutral and avoid exposing unnecessary private topology.

**NPR-001: OPEN.**

## NPR-002 — Logical controlled path across terminating and packet-path mechanisms

### Finding

A user-space TCP proxy commonly terminates a Subject-side TCP connection and creates a distinct upstream TCP connection, while kernel/routing/firewall controls can act on a packet path without introducing that same transport termination boundary. `Controlled TCP path` is therefore ambiguous if read as one native TCP connection.

### Required closure

AEP-0012 must:

1. define the controlled path as a portable logical exchange path between declared transport boundaries rather than a provider-native connection object;
2. state which terminating and non-terminating mechanism topologies are admissible to the same base semantic claim;
3. keep socket/peer/native connection identity non-portable;
4. require equivalent observable baseline/cut/recovery behavior at the declared boundaries rather than provider-mechanism equality.

**NPR-002: OPEN.**

## NPR-003 — Deterministic baseline exchange grammar/completion predicate

### Finding

TCP supplies an ordered byte stream rather than protocol-owned request/response message boundaries. `Deterministic baseline request/response exchange` is therefore already a semantic concept, but its minimal grammar and completion predicate remain deferred.

### Required closure

AEP-0012 must define enough portable exchange semantics for v0.1 to make one attempt objectively decidable, including:

1. exact request-byte identity;
2. exact response-byte/completion identity or another finite deterministic framing rule;
3. the boundary between one exchange and a subsequent attempt;
4. no HTTP/application semantics unless separately governed;
5. no dependence on packet segmentation, native socket exceptions, provider framing, or hidden application retries.

**NPR-003: OPEN.**

## NPR-004 — Fresh-attempt identity and retry/fallback closure

### Finding

Connection pooling, stale socket reuse, proxy retries, reconnect loops, multiple-address fallback, or Happy-Eyeballs-style racing can cause one apparent exchange to contain multiple native transport attempts. That can mask bypass or fault behavior.

### Required closure

AEP-0012 must:

1. define one portable fresh-attempt identity;
2. prohibit reuse of a connection established before that attempt;
3. require every retry/fallback to become a separately identified attempt;
4. prevent an automatic alternate route from converting a failed selected path into a successful result for the same attempt;
5. make pooling/reuse/fallback violations detectable by provider-neutral conformance behavior.

**NPR-004: OPEN.**

## NPR-005 — Finite transport-cut observation budget

### Finding

The Proposed profile intentionally permits transport cut to manifest through refusal, reset, close, unreachable behavior, timeout/blackhole, or other native mechanisms. TCP itself does not provide one portable finite liveness-detection point for a silent path. An implementation-chosen sleep or provider-native timeout therefore cannot decide portable cut semantics.

### Required closure

AEP-0012 must:

1. bind a finite evaluator-owned observation budget/deadline to the certified fresh exchange;
2. define cut success as non-completion of the deterministic baseline exchange within that bound after the relevant settlement/admission boundary;
3. state that the bound is a verification condition, not a latency/packet-timing guarantee and does not imply Time Control;
4. require a suitable evaluator/control-owned monotonic observation source rather than Subject self-report or provider timeout policy;
5. fail closed for missing, ambiguous, stale, drifted, or implementation-private observation bounds.

**NPR-005: OPEN.**

## NPR-006 — Activation-settlement probe versus certified post-activation attempt

### Finding

The current text uses a fresh attempt to prove activation settlement and separately requires post-activation fresh exchange behavior. Without explicit sequencing, settlement can become circular or accidentally consume Subject task traffic/occurrence semantics.

### Required closure

AEP-0012 must state that:

1. Environment activation condition satisfaction happens first;
2. the settlement probe is privileged Evaluator/Control verification traffic;
3. the probe does not count as Subject task traffic or alter Environment occurrence counting;
4. the settlement probe and later certified Subject-side attempt bind to the same endpoint/path/fixture identity;
5. the certified post-settlement attempt is a distinct attempt;
6. later unrelated failure cannot retroactively validate a false settlement claim.

**NPR-006: OPEN.**

## NPR-007 — Recovery settlement stability / anti-flap predicate

### Finding

Provider clear acknowledgement is correctly rejected, but `successful fresh exchange(s)` leaves the actual portable recovery predicate open. A single transient success can certify recovery while an intermittent fault remains.

### Required closure

AEP-0012 must:

1. select a finite protocol-owned recovery predicate, such as an exact bounded sequence of independent clean fresh exchanges or an equivalent deterministic barrier;
2. bind all recovery probes to the same endpoint/path/fixture identity;
3. keep clear acknowledgement non-authoritative;
4. exercise no-silent-reactivation after the recovery witness;
5. avoid converting arbitrary timing windows into latency semantics.

**NPR-007: OPEN.**

## NPR-008 — Behavioral path-coverage / bypass proof

### Finding

The AEP correctly requires behavioral path-coverage proof and a bypass negative implementation, but the positive provider-neutral criterion is not yet closed. Configuration presence cannot prove coverage, while one failed exchange alone does not prove the intended control point was traversed.

### Required closure

AEP-0012 must:

1. define the minimum provider-neutral behavioral proof that selected traffic traverses the intended controlled path;
2. bind baseline, active-cut, and recovery observations to the same materialized path identity;
3. include an explicit bypass-negative implementation whose behavior distinguishes true coverage from capability self-report/configuration presence;
4. fail closed if an alternate route can silently satisfy the same declared attempt;
5. keep packet traces/provider configuration as supplemental evidence only.

**NPR-008: OPEN.**

## NPR-009 — Target scoping and collateral-traffic noninterference

### Finding

A broad network rule could cut selected traffic while also disrupting unrelated Environment traffic. That is not equivalent to a narrowly scoped selected resource merely because the target exchange failed.

### Required closure

AEP-0012 must:

1. define the minimum portable target-scoping behavior for the selected resource/fault target;
2. require non-target control-flow evidence where coexistence is part of the materialized scenario;
3. forbid claiming a narrowly targeted resource by indiscriminately cutting all traffic unless the Environment target explicitly selects that whole scope;
4. preserve the existing rule that payload capture, TLS interception, unrelated topology observation, and broad packet-capture authority are not implied by Network Control conformance.

**NPR-009: OPEN.**

## NPR-010 — Reset/cleanup residual-network-state noninterference

### Finding

The base profile properly excludes live sockets, NAT/conntrack state, kernel queues, proxy buffers, resolver caches, and provider internals from portable snapshot state. Those excluded residues can nevertheless alter later baseline/cut/recovery behavior if reset or cleanup leaves them materially active.

### Required closure

For materially relevant residual network state, AEP-0012 must require at least one of:

1. isolation/cleanup proving noninterference with the next governed execution;
2. immutable execution identity/policy binding for unavoidable relevant residue; or
3. fail-closed declaration that the base profile is insufficient for the scenario.

Stale fault rules, stale privileged handles, lingering proxy state, or materially relevant packet-path residue must not silently survive into a new Episode. The rule must remain noninterference-oriented and must not imply portable live-network `STATE_EQUIVALENT` restoration.

**NPR-010: OPEN.**

## NPR-011 — Cross-mechanism acceptance evidence matrix

### Finding

The current AEP says materially independent mechanism classes should be exercised `where practical` and leaves open whether such evidence is required before acceptance or only before an official reference implementation. That is not strong enough to accept mechanism-neutral semantics.

### Required closure

Before acceptance-oriented re-review closes, reviewable evidence must exercise at least two materially independent control classes. Recommended minimum:

1. a user-space terminating/intercepting TCP proxy class; and
2. a packet-path kernel/routing/firewall-style control class.

The evidence must test portable semantic claims rather than provider API equality, including:

- endpoint/path binding;
- fresh-attempt identity and no hidden fallback;
- qualifying pre-trigger/no-early-activation behavior;
- finite cut observation;
- activation-settlement sequencing;
- bypass/path-coverage detection;
- target isolation;
- clear/recovery stability;
- no silent reactivation;
- reset/cleanup noninterference.

This is an **AEP acceptance-evidence gate**, not a universal requirement that every future third-party conforming implementation implement multiple control providers.

**NPR-011: OPEN.**

## Historical design-document disposition

Draft-era portability/readiness documents remain provenance:

- `docs/design/alpha3-network-control-resource-portability-audit.md`;
- `docs/design/alpha3-network-control-resource-proposed-readiness-audit.md`;
- `docs/acceptance/alpha3-network-control-draft-main-adoption.md`;
- `docs/acceptance/alpha3-network-control-readiness-main-adoption.md`;
- `docs/acceptance/alpha3-aep-0012-proposed-decision.md`.

They document why AEP-0012 became Proposed. They do not override this later Formal Proposed Review. When NPR edits are incorporated into AEP-0012, conflicting Draft-era wording must be treated as superseded provenance and must not be reintroduced into future Spec/Schema/TCK through stale design text.

## Acceptance gate

AEP-0012 is acceptance-ready only if all of the following are true:

1. NPR-001..NPR-011 decisions are incorporated into AEP-0012 Proposed text — **NOT STARTED**;
2. ROADMAP and review/adoption metadata accurately reflect the Proposed/formal-review state — **PENDING THIS REVIEW ADOPTION**;
3. superseded Draft-era semantics are explicitly identified where necessary — **PENDING BLOCKER EDITS**;
4. the required cross-mechanism semantic evidence is reviewable — **PENDING**;
5. exact-head CI, Governance, Release Validation, and all applicable conformance/evidence gates are green — **PENDING FUTURE BLOCKER-RESOLUTION HEAD**;
6. an acceptance-oriented exact-head protocol re-review finds no remaining semantic blocker — **PENDING**;
7. the protocol maintainer separately and explicitly authorizes `Proposed -> Accepted` — **NOT AUTHORIZED**.

Generic continuation does not satisfy item 7.

## Current conclusion

```text
AEP-0012 lifecycle: Proposed
Formal Proposed review: completed as review evidence on this work unit
NPR-001..NPR-011: OPEN
Blocker-resolution protocol edits: NOT STARTED
Acceptance-oriented re-review: NOT READY
Accepted: NOT AUTHORIZED
Network Control normative Spec/Schema/TCK: NOT AUTHORIZED
Network Control conformance harness: NOT AUTHORIZED
Provider/reference implementation: NOT AUTHORIZED
Cross-mechanism implementation evidence: REQUIRED LATER, NOT AUTHORIZED BY THIS REVIEW ALONE
Release/publication/signing/attestation: NOT AUTHORIZED
```

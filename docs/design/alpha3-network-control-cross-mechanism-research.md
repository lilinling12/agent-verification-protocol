# Alpha 3 Network Control Cross-Mechanism Research

Status: **RESEARCH COMPLETE — ARCHITECTURE DECISION CANDIDATE**

Proposal: AEP-0012 — Network Control Resource Profile v0.1

Research baseline: `main@2c2ba9ef9c069edcd2a43ca10d3a4fc86a42f529`

Prepared: 2026-09-03

## 1. Purpose

This research evaluates how AVP should satisfy the NPR-011 cross-mechanism acceptance-evidence gate without creating a temporary implementation that later forces architectural rewrites.

It is intentionally **not** a provider implementation plan disguised as a protocol decision. AEP-0012 already owns portable Network Control semantics. This document evaluates implementation/evidence architectures against those adopted semantics, the AVP authority chain, mature open-source engineering practice, large-scale fault-injection practice, current Linux networking primitives, and recent distributed-systems fault-injection research.

The target is a durable architecture that can later support the sequence:

```text
AEP-0012 Proposed semantics
  -> NPR-011 cross-mechanism acceptance evidence
  -> acceptance-oriented protocol re-review
  -> explicit Proposed -> Accepted decision
  -> normative Spec / requirement index
  -> Schema where required
  -> provider/language-neutral TCK
  -> backend-neutral conformance harness
  -> reference implementation(s)
```

This research does not authorize any provider, harness, TCK, or reference runtime implementation.

## 2. Existing AVP constraints that cannot be redesigned here

The research treats the following as fixed inputs:

1. AEP-0009: portable semantics precede backend implementation; backend behavior never becomes protocol authority.
2. `AVP-ENVIRONMENT-010`: Environment owns fault identity, target, activation condition, occurrence no-early-activation, clear, and future-schedule secrecy.
3. AEP-0012: the base resource is a logical controlled TCP exchange path, not a provider-native connection, proxy object, qdisc, route, or firewall rule.
4. One certified attempt binds materialized literal endpoints, exact request/expected-response bytes, exchange-program identity, attempt-unique challenge, and a finite evaluator-owned observation budget.
5. Hidden Subject-side or terminating-intermediary retry/fallback is prohibited inside one certified attempt.
6. Activation settlement is an independent privileged post-trigger fresh attempt; the Subject-side active-cut attempt is distinct.
7. Recovery is a finite `2 + 1` witness: two consecutive privileged recovery probes plus one distinct post-recovery stability witness.
8. Narrow target claims require non-target noninterference where a suitable control is materialized.
9. Cleanup/reset must establish residual-state noninterference; live network/provider state is not claimed as exact restorable state.
10. NPR-011 requires at least two materially independent control classes before acceptance-oriented re-review can close:
   - terminating/intercepting user-space TCP control;
   - non-terminating packet-path kernel/routing/firewall-style control.

Any evidence mechanism that requires weakening or reinterpreting those decisions is rejected.

## 3. Industry and open-source evidence

### 3.1 Linux network namespaces

Linux network namespaces isolate network devices, IPv4/IPv6 stacks, routing tables, firewall rules, port number spaces, and related network state. This makes them suitable as an **ephemeral evidence-lab isolation boundary**: each run can own its network topology rather than mutating the CI host's ordinary network namespace.

Reference:
- `network_namespaces(7)`: https://www.man7.org/linux/man-pages/man7/network_namespaces.7.html

Engineering implication for AVP:

- use a dedicated ephemeral namespace/topology for the packet-path evidence lab;
- never install broad test fault rules in the host namespace merely because CI has root;
- destroy the entire isolated topology after the run, then separately verify no relevant residual state is visible to the next run.

### 3.2 nftables / Netfilter

The nftables project describes nftables as the modern Linux kernel packet-classification framework and recommends it for new code instead of legacy xtables/iptables infrastructure.

Reference:
- nftables project wiki: https://wiki.nftables.org/wiki-nftables/index.php/What_is_nftables%3F

For AEP-0012 base `transport cut`, nftables is a better primary packet-path evidence mechanism than `tc netem` because the base semantic is a deterministic selected-path cut, not probabilistic packet loss or bounded latency.

A narrow nftables DROP rule can be scoped to the exact materialized endpoint/port/path under test, preserving NPR-009 target-isolation semantics. Rule handles/counters remain diagnostic only.

### 3.3 `tc netem`

`tc netem` is valuable for latency, jitter, loss, reordering, duplication, corruption, and rate experiments. However the Linux manual documents limitations including kernel timer granularity, TCP Small Queues placement effects, and interactions when combining qdiscs.

Reference:
- `tc-netem(8)`: https://www.man7.org/linux/man-pages/man8/netem.8.html

Decision consequence:

- **do not use `netem loss 100%` as the canonical packet-path realization of AEP-0012 base `transport cut`**;
- keep netem as a likely future implementation candidate for separately reviewed latency/loss profiles;
- otherwise AVP risks reintroducing the already rejected alias `transport cut == 100% packet loss` and tying v0.1 to packet/qdisc semantics that AEP-0012 intentionally excludes.

### 3.4 Toxiproxy

Shopify Toxiproxy remains an actively maintained TCP proxy for testing failure conditions. The latest tagged release found during this research is `v2.12.0` (2025-03-18); the GitHub container package exposes versioned images and immutable digests.

References:
- releases: https://github.com/Shopify/toxiproxy/releases
- container package: https://github.com/Shopify/toxiproxy/pkgs/container/toxiproxy

Toxiproxy is a strong **terminating/intercepting evidence mechanism candidate**, but not because its API should become AVP's abstraction. Its value is that it is materially different from an in-kernel packet-filtering path and widely used as a real TCP fault proxy.

Required AVP safeguards:

- pin an exact release and immutable artifact/image digest;
- do not use `latest` in acceptance evidence;
- verify actual Subject-facing and upstream fixture connection attempts behaviorally;
- treat toxic/proxy IDs and native error behavior as diagnostics only;
- explicitly prove that one AVP certified attempt does not hide upstream reconnect/retry/fallback.

### 3.5 Chaos Mesh / large-scale chaos platforms

Mature chaos platforms such as Chaos Mesh separate high-level experiment intent/orchestration from privileged node-local fault execution. Their network-fault systems use privileged components because packet/path mutation inherently crosses a trust boundary.

Reference:
- Chaos Mesh documentation: https://chaos-mesh.org/docs/

This is useful architectural evidence for AVP, but Kubernetes CRDs/controllers/Chaos Daemon APIs must not be copied into the protocol or into the first local evidence architecture.

Reusable lesson:

```text
unprivileged scenario/evaluator intent
  -> narrow privileged control seam
  -> fault mechanism
  -> independent behavioral observation
```

Non-reusable complexity for v0.1 evidence:

- Kubernetes reconciliation loops;
- cluster-wide selectors;
- multi-tenant chaos scheduling;
- CRD/plugin frameworks;
- general fault catalogs.

### 3.6 Jepsen-style testing lessons

Jepsen's long-running distributed-systems testing practice separates workload/client behavior, fault/nemesis behavior, histories, and independent checking. The important lesson for AVP is not a specific Jepsen API; it is that **fault injection and correctness judgment must remain independently attributable**.

AVP already has a stronger explicit authority separation: Subject, Evaluator, Environment, privileged Control, Evidence, Validity, and Task Verdict. Network evidence should preserve that separation instead of allowing the mechanism controller to self-certify success.

### 3.7 Large cloud fault-injection systems

AWS Fault Injection Service and similar production chaos systems emphasize explicit experiment targets, scoped actions, stop/safety conditions, and post-experiment recovery. These are consistent with AVP's target-scope and cleanup requirements.

Reference:
- AWS FIS documentation: https://docs.aws.amazon.com/fis/

AVP should borrow the safety pattern, not the cloud provider API:

- explicit materialized target;
- small blast radius;
- fail-closed unsupported scope;
- privileged activation/clear;
- independent recovery verification;
- immutable evidence identity.

## 4. Recent research relevant to AVP

### 4.1 Configuration-aware fault injection — CAFault, USENIX ATC 2025

CAFault reports that fault injection under one fixed default configuration can miss fault-handling paths that appear under other relevant configurations. Its evaluation on HDFS, ZooKeeper, MySQL Cluster, and IPFS found substantially greater fault-tolerance-logic coverage than several prior systems and reported 16 previously unknown bugs.

Reference:
- Yuanliang Chen et al., *CAFault: Enhance Fault Injection Technique in Practical Distributed Systems via Abundant Fault-Dependent Configurations*, USENIX ATC 2025: https://www.usenix.org/conference/atc25/presentation/chen-yuanliang

AVP implication:

NPR-011 evidence must not claim broad production reliability from one topology/configuration. Instead:

1. the **protocol acceptance matrix** should remain deliberately small and canonical, proving semantic portability between mechanism classes;
2. later robustness/quality testing should deliberately vary implementation-relevant configurations without changing the portable expectation;
3. the evidence record must distinguish `protocol portability evidence` from `configuration-space robustness evidence`.

This prevents two opposite mistakes:

- under-testing: one happy-path topology falsely treated as production confidence;
- over-standardizing: every production configuration variation accidentally becoming a protocol requirement.

### 4.2 Deterministic simulation testing

Modern reliability engineering increasingly uses deterministic/simulation testing to make complex failure schedules reproducible. FoundationDB's simulation testing and newer deterministic-simulation systems demonstrate the value of controlled scheduling, reproducible seeds, and shrinking a failure to a replayable history.

This does **not** imply that AVP Network Control should simulate TCP/kernel behavior; AEP-0012 explicitly requires real behavior at the controlled-network boundary for its acceptance evidence.

Reusable principle:

- deterministic **control-plane plan and evidence identity**;
- real **data-plane behavior**;
- enough retained execution data to reproduce the same materialized AVP attempt plan even when native packet timing differs.

## 5. Mechanism candidates

| Candidate | Class | Base transport-cut fit | Isolation | Cross-platform | Main concern | Decision |
|---|---|---:|---:|---:|---|---|
| Toxiproxy 2.12.x pinned | terminating user-space TCP proxy | high | high when isolated | good | must prove no hidden proxy retry/fallback | **SELECT for NPR-011 class A evidence** |
| custom Python TCP proxy | terminating proxy | technically high | controllable | good | evidence would mostly prove our own code and risks protocol-by-implementation | reject as primary acceptance mechanism |
| Envoy TCP proxy | terminating proxy | high | medium | good | large config/runtime surface; extension semantics can obscure narrow v0.1 claim | defer |
| service mesh / Istio | terminating/intercepting | medium | cluster-scoped | Kubernetes | huge orchestration/security surface unrelated to v0.1 | reject for base evidence |
| nftables DROP in isolated namespace | non-terminating packet path | high | high with netns | Linux | privileged Linux-only mechanism | **SELECT for NPR-011 class B evidence** |
| legacy iptables | packet path | high | high with netns | Linux | legacy interface; nftables preferred for new work | reject as primary new implementation |
| `tc netem loss 100%` | packet/qdisc | medium | high with netns | Linux | aliases cut to packet loss; qdisc/timer/TSQ complexity | reject for base cut; reserve for future loss/latency |
| eBPF tc/XDP | packet path | high | potentially high | Linux | unnecessary verifier/kernel-program complexity for v0.1 | defer |
| Kubernetes NetworkPolicy | packet path/policy | medium | cluster | Kubernetes | policy semantics/implementation vary; not a precise fault activation primitive | reject |
| cloud firewall/security group | remote control plane | medium | account/VPC | cloud-specific | slow async convergence and provider identity dominate evidence | defer |

## 6. Selected mechanism pair

The research recommends the following NPR-011 pair:

### Class A — terminating/intercepting

**Pinned Toxiproxy 2.12.x artifact/image**, running inside an isolated local evidence topology.

Reasons:

- real, mature independent implementation rather than AVP-authored proxy code;
- materially different connection topology from a packet filter;
- explicit TCP proxy role makes NPR-002/NPR-004 portability challenge observable;
- versioned release and immutable image/artifact digest can be retained as implementation evidence;
- does not require a Kubernetes control plane.

### Class B — non-terminating packet path

**Linux network namespace + veth + nftables narrow DROP rule**.

Reasons:

- packet-path mechanism does not terminate the Subject TCP connection as a user-space proxy;
- namespace topology gives a disposable blast-radius boundary;
- nftables can target the exact materialized endpoint/port rather than globally disabling networking;
- clear can remove the scoped rule and recovery can be verified independently;
- mechanism is conceptually small enough to audit and does not import latency/loss semantics.

## 7. Why the pair is genuinely mechanism-independent

The pair differs in the exact dimension NPR-011 is intended to test:

| Dimension | Toxiproxy class | nftables/netns class |
|---|---|---|
| TCP termination | proxy terminates Subject side and initiates upstream | no user-space TCP termination by fault mechanism |
| fault location | user-space relay/control | kernel packet classification path |
| native control object | proxy/toxic/config | ruleset/table/chain/rule |
| native failure manifestation | proxy-specific close/stall/reset behavior possible | packet drop/connection timeout behavior possible |
| cleanup mechanism | proxy control/reset/process teardown | rule removal + namespace teardown |
| AVP portable result | exact exchange succeeds/cut/recovers | same |

The evidence is useful only if the matrix compares the final row and AVP-governed identities, not the provider-specific rows.

## 8. Rejected architectural shortcuts

### 8.1 One generic `NetworkBackend` now

Rejected.

A shared class/interface created before Spec/TCK/harness ownership exists would freeze implementation assumptions too early. AVP's engineering policy already requires evidence before abstraction.

During NPR-011 evidence work, the two mechanism runners should have **separate explicit implementations** that consume one immutable evidence-plan model and emit one evidence-result model. Similarity observed later can inform the post-Accepted harness boundary.

### 8.2 Provider name switching in portable logic

Rejected.

No portable evaluator path should contain logic like:

```text
if provider == "toxiproxy": expect reset
if provider == "nftables": expect timeout
```

Both must be judged against the same AVP exchange/cut/recovery predicates.

### 8.3 Docker Compose as the semantic architecture

Rejected.

Containers may be an execution convenience for Toxiproxy/fixture process isolation, but Compose services, container names, bridge IPs, or Docker network IDs must not define the portable path identity.

### 8.4 Kubernetes-first implementation

Rejected for v0.1 acceptance evidence.

Kubernetes would add controller reconciliation, CNI, admission/RBAC, node privilege, pod lifecycle, NetworkPolicy/service routing, and cluster-version variables before the underlying transport-cut semantics have even become Accepted.

A future Kubernetes provider can reuse the accepted portable TCK/harness; it should not force Kubernetes concepts into the first evidence architecture.

### 8.5 Custom proxy + custom packet filter only

Rejected as insufficiently independent evidence.

If AVP authors both fault mechanisms and the verifier around them in one coupled implementation, a shared bug or shared assumption can self-confirm the protocol. Using one mature external proxy and one kernel facility improves independence.

## 9. Production-grade engineering implications

For a mature open-source / large-scale engineering bar, the later implementation must provide:

- pinned external mechanism versions and immutable artifact identity;
- root/privilege only in the smallest packet-control process/context;
- no Subject access to mechanism APIs or namespace-control handles;
- deterministic local exact-byte fixtures with no public Internet dependency;
- unique per-run topology/resource identifiers;
- bounded process startup/readiness/cleanup with no arbitrary sleep as proof;
- idempotent cleanup preserving the primary failure;
- host-level and run-level concurrency isolation;
- evidence that another run cannot inherit old rules/proxy state;
- exact-head CI attribution;
- architecture tests preventing portable evaluator/TCK code from importing mechanism-specific modules once those layers exist;
- separate mechanism diagnostics versus portable evidence;
- no production/customer data or credentials;
- optional dependencies and platform-specific lanes rather than making Linux privilege requirements part of the base AVP package.

## 10. Research conclusion

The durable direction is:

```text
one provider-neutral NPR-011 evidence plan
        |
        +--> independent Toxiproxy evidence lab
        |
        +--> independent Linux netns+nftables evidence lab
        |
        +--> one provider-neutral evidence comparator
```

This structure is deliberately **not yet the future TCK/harness**. It is acceptance evidence proving that AEP-0012's already reviewed semantics survive two materially different real mechanisms.

The next design document defines the exact evidence architecture and what may later be reused after AEP-0012 is Accepted without turning this pre-Accepted work into a temporary implementation.

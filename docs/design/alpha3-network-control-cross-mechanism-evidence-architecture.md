# Alpha 3 Network Control Cross-Mechanism Evidence Architecture

Status: **DESIGN CANDIDATE — NO IMPLEMENTATION AUTHORITY**

Proposal: AEP-0012 — Network Control Resource Profile v0.1

Design baseline: `main@2c2ba9ef9c069edcd2a43ca10d3a4fc86a42f529`

Research input: `docs/design/alpha3-network-control-cross-mechanism-research.md`

Prepared: 2026-09-03

## 1. Purpose

This document defines the long-lived architecture for producing NPR-011 cross-mechanism acceptance evidence without introducing a throwaway implementation or prematurely creating the future Network Control TCK/harness/provider API.

It translates the already reviewed AEP-0012 semantics into an implementation-independent **evidence architecture** whose outputs can be reviewed during the Proposed phase. It does not add new portable Network Control semantics.

The design explicitly optimizes for:

- protocol authority preservation;
- real cross-mechanism independence;
- deterministic, reproducible local evidence;
- strict Subject/Evaluator/Control separation;
- narrow blast radius;
- exact evidence identity;
- failure/cleanup honesty;
- ability to evolve after `Proposed -> Accepted` into Spec/TCK/harness/reference implementation **without rewriting the core topology or evidence model**;
- avoidance of generic provider/plugin abstractions before two independent implementations and accepted semantics justify them.

## 2. Architecture decision

NPR-011 evidence will use two independent, ephemeral local evidence labs driven by one provider-neutral evidence plan and evaluated by one provider-neutral comparator:

```text
                         +---------------------------+
                         | NPR-011 Evidence Plan      |
                         | immutable / provider-free  |
                         +-------------+-------------+
                                       |
                 +---------------------+---------------------+
                 |                                           |
                 v                                           v
+-----------------------------------+       +-----------------------------------+
| Lab A: terminating TCP control   |       | Lab B: packet-path control        |
| pinned Toxiproxy                 |       | Linux netns + veth + nftables     |
|                                   |       |                                   |
| Subject client -> proxy -> fixture|       | Subject ns -> packet path -> fixture|
+------------------+----------------+       +------------------+----------------+
                   |                                           |
                   +---------------------+---------------------+
                                         |
                                         v
                         +-------------------------------+
                         | Portable Evidence Comparator   |
                         | no provider-name expectations  |
                         +---------------+---------------+
                                         |
                                         v
                         +-------------------------------+
                         | NPR-011 Evidence Bundle        |
                         | AVP outcomes + diagnostics     |
                         +-------------------------------+
```

The two labs MUST NOT inherit from a common `BaseNetworkBackend` or share mechanism-control code merely to reduce duplication.

They MAY share neutral utilities whose responsibility is already stable and non-semantic, for example exact-byte fixture encoding helpers, digest calculation, subprocess lifecycle helpers, or evidence serialization utilities already owned elsewhere in AVP. Such sharing must not create a backend SPI by accident.

## 3. Layer and authority model

### 3.1 Evidence Plan

The Evidence Plan is a **review-time execution description**, not a new protocol schema.

It binds only data already required by AEP-0012 or needed to reproduce the evidence run, including:

- evidence-plan identity/revision;
- selected AEP-0012 semantic revision/commit;
- logical controlled-path identity;
- Subject-visible literal TCP endpoint identity;
- evaluator-controlled fixture endpoint identity where distinct;
- exact request bytes identity/content;
- exact expected-response bytes identity/content;
- exchange-program identity;
- deterministic challenge seed / derivation input sufficient to reproduce the attempt series;
- finite evaluator-owned observation budget;
- Environment fault identity/target/activation-condition materialization used by the evidence scenario;
- expected attempt phase sequence;
- negative mode selected for a run, if any;
- execution-platform constraints required by the evidence lab;
- implementation artifact identities required to reproduce the evidence run.

The plan MUST NOT include provider-native rule/proxy IDs as portable identity.

The plan MUST NOT become a normative schema before AEP-0012 acceptance and downstream Spec/Schema review.

### 3.2 Mechanism runner

Each mechanism runner has one narrow job:

> execute the already-defined evidence phases against one real mechanism class and return raw observations plus sanitized mechanism diagnostics.

A runner does **not** decide whether AEP-0012 conformance semantics are valid. It must not return `protocol_pass=true` as an authoritative self-verdict.

Mechanism runner responsibilities include:

- creating its isolated topology;
- starting deterministic fixture processes;
- configuring the mechanism using privileged authority;
- executing privileged settlement/recovery probes;
- executing or coordinating the Subject-side certified attempt according to the evidence plan;
- collecting raw attempt observations;
- clearing fault state;
- performing cleanup;
- reporting mechanism-level failures separately from portable observations;
- retaining implementation artifact/version identities.

### 3.3 Portable Evidence Comparator

The comparator owns provider-neutral judgment of the NPR-011 matrix.

It consumes the same shape of phase observations from both labs and evaluates only AEP-0012 predicates:

- baseline exact exchange success;
- no-early-activation on qualifying pre-trigger Subject traffic;
- activation settlement only after the Environment condition;
- active Subject attempt does not complete within the governed observation budget;
- bypass negative causes conformance-evidence failure;
- target isolation/non-target control where materialized;
- clear is followed by exactly two successful privileged fresh recovery probes;
- post-recovery stability witness succeeds;
- cleared occurrence does not silently reactivate;
- hidden schedule/control material is not exposed to Subject context;
- cleanup/reset noninterference is established or the run fails closed.

The comparator MUST NOT branch on provider/mechanism names to define expected AVP outcomes.

### 3.4 Evidence Bundle

The retained evidence bundle separates **portable evidence** from **mechanism diagnostics**.

Portable evidence candidate fields include:

- evidence-plan digest;
- AEP semantic baseline commit;
- run identity;
- mechanism-class identity (`terminating-intercepting` or `packet-path`) as an evidence classification, not a protocol capability name;
- implementation artifact digest/version identity;
- environment/platform identity sufficient for reproducibility without asserting portable semantics;
- ordered phase/attempt records;
- each attempt identity and challenge identity;
- portable endpoint/path identities;
- observation budget input;
- exact exchange result / cut result / recovery result;
- target-control result where applicable;
- cleanup/noninterference result;
- comparator result and failure localization;
- retained artifact references/digests for exact bytes where appropriate.

Mechanism diagnostics may include:

- Toxiproxy version/image digest;
- proxy/toxic configuration snapshot;
- upstream fixture accept counts;
- nftables ruleset/rule handles/counters;
- namespace/veth names;
- subprocess/container IDs;
- kernel/tool versions;
- native socket errors;
- cleanup logs.

Those diagnostics MUST remain clearly namespaced/non-portable and MUST NOT be used as the sole proof of activation/cut/recovery.

## 4. Canonical evidence topology

### 4.1 Common logical roles

Both labs materialize the same logical roles:

1. **Subject Client** — executes only authorized ordinary TCP exchange operations.
2. **Privileged Probe Client** — Evaluator/Control-owned client for settlement and recovery verification.
3. **Controlled Path** — selected target of the Environment fault.
4. **Upstream Fixture** — deterministic exact-byte fixture that records connection accepts and challenge/exchange observations.
5. **Non-target Control Fixture/Path** — separate control traffic used to prove narrow target isolation where the evidence scenario materializes such a control.
6. **Mechanism Controller** — privileged implementation-private control authority.
7. **Evidence Collector** — captures phase observations and exact evidence identity.

Subject and privileged Probe Client MUST be structurally and credential-wise separate.

### 4.2 Lab A — terminating/intercepting topology

Canonical topology:

```text
Subject Client
    |
    | one certified Subject-facing TCP initiation
    v
Pinned Toxiproxy listener
    |
    | exactly one corresponding upstream initiation
    v
Evaluator Fixture
```

A separate control fixture/path is materialized for NPR-009 when needed.

Key proofs:

- fixture accept counters/challenge records verify exactly one corresponding upstream initiation during baseline/recovery attempts;
- active-cut behavior is judged by exact exchange non-completion, not by a chosen toxic/error class;
- hidden proxy reconnect/retry/fallback must be detectable and causes evidence failure;
- proxy API acknowledgement does not establish settlement or recovery.

The exact toxic/control technique used to realize a deterministic cut may remain implementation-specific during evidence work, provided it satisfies the AEP behavior and does not introduce hidden retry/fallback. The mechanism choice and version-specific behavior must be documented in the implementation PR, not promoted to AEP semantics.

### 4.3 Lab B — non-terminating packet-path topology

Recommended canonical topology:

```text
+---------------- Subject network namespace ----------------+
| Subject Client                                           |
|      |                                                   |
|      v                                                   |
|    veth-subject                                          |
+------|----------------------------------------------------+
       |
       | isolated packet path controlled by nftables
       |
+------|----------------------------------------------------+
|    veth-fixture                                          |
|      |                                                   |
|      v                                                   |
| Evaluator Fixture                                        |
+---------------- Fixture/control namespace ----------------+
```

Exact namespace arrangement may use an additional router/control namespace if needed to keep nftables mutation out of both the Subject and fixture roles. The preferred mature design is:

```text
subject namespace
      |
    veth
      |
control/router namespace  <-- privileged nftables rule lives here
      |
    veth
      |
fixture namespace
```

This three-namespace form has important long-term advantages:

- Subject namespace does not own the fault-control rules;
- fixture namespace does not self-fault;
- privileged network mutation has a distinct structural boundary;
- narrow target and non-target routes can be expressed cleanly;
- namespace teardown provides a strong cleanup primitive without claiming portable exact network restoration.

The implementation should prefer this three-namespace topology unless a reviewed implementation study proves a simpler topology preserves the same authority and isolation guarantees.

## 5. Attempt and phase model

The evidence architecture uses one shared provider-neutral phase model derived directly from AEP-0012:

```text
P0 MATERIALIZE
P1 BASELINE
P2 PRE_TRIGGER
P3 ENVIRONMENT_TRIGGER_REACHED
P4 ACTIVATION_SETTLEMENT
P5 SUBJECT_ACTIVE_CUT
P6 TARGET_ISOLATION_CONTROL
P7 CLEAR
P8 RECOVERY_1
P9 RECOVERY_2
P10 POST_RECOVERY_STABILITY
P11 RESET_CLEANUP_NONINTERFERENCE
```

This phase naming is design/evidence vocabulary, not yet a normative protocol enumeration.

Rules:

- every network exchange in P1/P2/P4/P5/P8/P9/P10 has a distinct attempt identity and challenge;
- P4 is privileged and cannot count toward the Environment occurrence condition;
- P5 is a distinct Subject attempt;
- P8 and P9 are the exact two privileged recovery probes;
- P10 is the distinct stability witness;
- mechanism-controller operations never substitute for an exchange observation;
- cleanup evidence cannot overwrite the primary phase failure.

## 6. Negative evidence plan

NPR-011 should not be satisfied only by two positive happy paths.

At minimum, the architecture must be able to execute the AEP-required negative directions in a mechanism-neutral way:

### 6.1 `BypassFaultAdapter`

Evidence objective: control metadata says active but Subject traffic bypasses the actual controlled effect.

Expected portable outcome: active Subject exchange succeeds -> evidence FAIL.

The two labs may realize bypass differently, but comparator expectations are identical.

### 6.2 `EarlyActivationAdapter`

Evidence objective: qualifying pre-trigger traffic is affected before Environment occurrence threshold.

Expected: FAIL.

### 6.3 `FalseSettledFaultAdapter`

Evidence objective: controller claims settlement without an independent valid post-trigger cut probe.

Expected: FAIL.

### 6.4 `FalseRecoveryAdapter`

Evidence objective: clear/provider acknowledgement or insufficient recovery witness is reported as recovery.

Expected: FAIL.

### 6.5 `ScheduleLeakAdapter`

Evidence objective: future fault schedule/control material enters Subject-visible context.

Expected: FAIL.

### 6.6 Hidden retry/fallback negative

Evidence objective: one certified attempt performs more than one Subject-facing or terminating-upstream initiation / alternate endpoint/path retry.

Expected: FAIL.

### 6.7 Collateral-target negative

Evidence objective: selected path is cut but a materialized non-target control path is also faulted under a narrow target.

Expected: FAIL.

### 6.8 Residual-fault cleanup negative

Evidence objective: cleanup reports success but next fresh baseline is still affected by stale mechanism state.

Expected: FAIL.

The negative matrix is crucial to avoid an architecture where both mechanisms only prove the easiest interpretation of the AEP.

## 7. Reproducibility model

### 7.1 What must be deterministic

The following should be reproducible for a reviewed evidence run:

- source commit;
- evidence plan bytes/digest;
- challenge seed/derivation;
- exact request/response fixture program;
- endpoint topology declaration;
- observation budget;
- Environment activation condition;
- ordered phase plan;
- selected mechanism artifact version/digest;
- negative mode;
- comparator version/source commit.

### 7.2 What is not claimed deterministic

The architecture must not claim deterministic:

- kernel scheduling;
- packet timing;
- TCP retransmission schedule;
- ephemeral source ports;
- native socket error type/text;
- Toxiproxy event-loop timing;
- nftables packet-counter values beyond what a diagnostic observation explicitly records;
- CI host performance.

### 7.3 Re-run policy

A reviewed acceptance-evidence result should be reproducible from the same source/evidence plan and mechanism artifact identities.

If a run fails intermittently, the correct response is not to add unbounded retries. The evidence owner must classify whether the problem is:

- protocol assumption;
- evidence-plan inadequacy;
- mechanism/version behavior;
- platform instability;
- fixture bug;
- cleanup/isolation bug;
- CI infrastructure failure.

Only then should the design/implementation change.

## 8. Observation-budget engineering

AEP-0012 already requires a finite evaluator-owned observation budget but intentionally leaves numeric serialization/ranges to downstream normative work.

For NPR-011 evidence:

- one explicit budget value is bound into the evidence plan;
- both mechanism classes use the same portable budget input for the compared scenario where practical;
- the budget is enforced by the comparator/evaluator side using a monotonic clock;
- provider connect/read timeouts may be configured only to avoid indefinite resource leakage and MUST NOT be interpreted as the portable decision clock;
- the evidence report records both the portable budget and any relevant implementation timeout settings separately;
- no arbitrary post-operation sleep may be treated as settlement/recovery proof.

The evidence architecture should run a small calibration/preflight to reject obviously overloaded or broken CI environments **before** collecting acceptance evidence, but calibration MUST NOT dynamically weaken the immutable portable budget after the evidence run begins.

## 9. Target isolation / blast-radius design

The selected evidence topology must make NPR-009 falsifiable.

Required pattern:

- one selected controlled path/fixture endpoint;
- one distinct non-target control path/fixture endpoint where the scenario materializes target-isolation evidence;
- activation affects only the selected path;
- the non-target control remains baseline-capable while the selected path is cut.

For packet-path evidence, nftables rule matching should be scoped by the exact materialized address family/address/TCP port and located in the dedicated control/router namespace.

For terminating evidence, the selected proxy listener/path must be separate from the non-target control path.

A mechanism implementation that can only sever an entire namespace/host network must fail closed for a narrow target rather than broadening the fault silently.

## 10. Privilege and security model

### 10.1 Least privilege

Packet-path evidence requires Linux network administration privileges. Those privileges must be isolated to the process/job/context that owns netns/veth/nftables lifecycle.

The Subject process must never receive:

- `CAP_NET_ADMIN`;
- namespace file descriptors or control handles that allow mutation;
- nftables command/API access;
- Toxiproxy admin endpoint credentials/access;
- future fault schedules;
- private fixture/probe controls.

### 10.2 CI execution

A production-quality open-source project should not make every ordinary CI job privileged.

Recommended lane model:

- ordinary CI remains unprivileged and platform-neutral;
- NPR-011 packet-path acceptance lane runs only on a hardened Linux runner class capable of isolated network-namespace administration;
- the privilege boundary is visible in workflow/repository policy and reviewed separately;
- if GitHub-hosted runner capabilities are insufficient or too broad, use a dedicated ephemeral self-hosted/managed runner with no production network/credentials and teardown after each job;
- privileged evidence jobs must not have release/signing credentials.

This is evidence-lab infrastructure, not a portable AVP requirement.

## 11. Cleanup and residual-state proof

Cleanup is a first-class evidence phase.

### Toxiproxy lab

Cleanup should include:

- disable/remove selected fault state;
- stop/tear down proxy process/container;
- close fixture/client processes;
- verify a newly created fresh topology does not inherit proxy configuration;
- retain cleanup diagnostics.

### nftables/netns lab

Cleanup should include:

- remove/flush the evidence-owned nftables rules/table as appropriate;
- destroy evidence-owned veth devices/namespaces;
- verify evidence-owned namespace names/handles are absent;
- create a fresh next-run topology and prove baseline success where required by the residual-state negative/recovery design.

A cleanup failure is never rewritten into a successful evidence run.

## 12. Concurrency isolation

Large CI projects eventually run jobs concurrently; therefore the design must not rely on globally fixed names/ports.

Every evidence run should derive unique implementation-private identifiers from a run identity, for example:

- namespace names;
- veth names within Linux length constraints;
- proxy names/listeners;
- fixture ports;
- temporary filesystem paths;
- nftables table/chain names.

These identifiers remain implementation diagnostics, not portable path identity.

The architecture must support at least two concurrent evidence jobs on the same runner host **without namespace/rule/port collision**, or the runner scheduler must guarantee one isolated VM per job. The latter is preferred for stronger open-source CI reproducibility when practical.

## 13. Dependency and repository structure direction

No implementation directories are created by this design PR.

When implementation is later authorized, responsibility-driven boundaries should be preferred. A likely shape after evidence justifies it is illustrative only:

```text
<evidence-owned area>/
  plan.py / plan model
  comparator.py
  fixture/
  terminating/
  packet_path/
```

But these names are **not approved API/package structure** by this document.

Hard rules for later implementation:

- no `base.py` containing a generic Network backend contract;
- no dynamic plugin discovery;
- no provider-name branch in portable comparator logic;
- provider dependencies optional;
- privileged controls structurally separate from Subject-facing operations;
- mechanism-specific diagnostics stay out of portable models;
- exact package layout follows responsibilities proven by implementation, not this diagram.

## 14. Relationship to the future accepted TCK/harness

The design intentionally creates **stable responsibilities** that can later survive without forcing code reuse:

Stable conceptual responsibilities:

- immutable execution/evidence plan;
- deterministic exact-byte fixture;
- privileged mechanism control;
- Subject attempt execution;
- privileged settlement/recovery probes;
- provider-neutral observation/result model;
- provider-neutral comparator;
- evidence retention;
- cleanup/noninterference verification.

After AEP-0012 becomes Accepted, the normative Spec/TCK may adopt corresponding concepts if review confirms they encode the same semantics. The code written for pre-Accepted evidence does **not** automatically become the harness.

This avoids two forms of rework:

1. **semantic rework** — prevented by doing cross-mechanism evidence before acceptance;
2. **architecture rework** — reduced by separating stable responsibilities now while deferring generic backend interfaces until Spec/TCK/harness boundaries are authoritative.

## 15. Acceptance evidence matrix

Both mechanism classes must produce reviewable evidence for the following matrix before NPR-011 can close:

| ID | Evidence requirement | Terminating | Packet-path | Portable comparator |
|---|---|---:|---:|---:|
| NC-EV-001 | exact source/plan/mechanism artifact identity | required | required | verifies |
| NC-EV-002 | materialized literal endpoint/path identity | required | required | verifies |
| NC-EV-003 | baseline exact-byte fresh exchange | required | required | same predicate |
| NC-EV-004 | pre-trigger qualifying traffic unaffected | required | required | same predicate |
| NC-EV-005 | no activation before Environment condition | required | required | same predicate |
| NC-EV-006 | privileged independent activation settlement | required | required | same predicate |
| NC-EV-007 | distinct Subject active-cut attempt | required | required | same predicate |
| NC-EV-008 | finite evaluator observation budget | required | required | same predicate |
| NC-EV-009 | hidden retry/fallback absent/detected | required at both proxy boundaries | required Subject boundary | same rule |
| NC-EV-010 | behavioral bypass negative fails | required | required | same rule |
| NC-EV-011 | narrow target isolation / non-target control | required | required | same rule |
| NC-EV-012 | privileged clear | required | required | sequencing only |
| NC-EV-013 | recovery probe #1 success | required | required | same predicate |
| NC-EV-014 | recovery probe #2 success | required | required | same predicate |
| NC-EV-015 | post-recovery stability witness success | required | required | same predicate |
| NC-EV-016 | no silent reactivation | required | required | same predicate |
| NC-EV-017 | schedule/control secrecy | required | required | same rule |
| NC-EV-018 | stale/released authority fails closed where applicable | required | required | same rule |
| NC-EV-019 | cleanup/residual-state noninterference | required | required | same predicate |
| NC-EV-020 | negative matrix does not self-certify | required | required | final judgment |

These `NC-EV-*` identifiers are evidence-document identifiers only. They are not normative requirement/TCK IDs and must not be copied into future normative surfaces without separate review.

## 16. Configuration-robustness strategy

Recent configuration-aware fault-injection research shows that fixed default configurations can miss fault-handling behavior. AVP should respond without turning an acceptance matrix into a combinatorial production benchmark.

Recommended two-tier model:

### Tier 1 — protocol acceptance evidence

Small, canonical, deterministic matrix required by NPR-011. Purpose: prove the same portable semantics survive two materially independent mechanism classes.

### Tier 2 — implementation robustness evidence

Non-normative expansion over configurations such as:

- IPv4 and later IPv6 where implementation support exists;
- fixture payload sizes within reviewed limits;
- multiple observation-budget values inside a safe range;
- repeated runs/seeds;
- relevant Linux kernel/tool versions;
- supported CPU architectures for Toxiproxy artifact;
- concurrent-run isolation;
- alternate safe host/runtime configurations.

Tier 2 must not change portable expected outcomes or become a hidden conformance requirement.

## 17. Decisions that should be stable long term

The following architecture decisions should not need to be rewritten when Network Control moves into Spec/TCK/reference implementation:

1. protocol semantics remain provider-neutral;
2. Subject/Evaluator/Control authority is structurally separated;
3. terminating and non-terminating mechanisms are tested independently;
4. one provider-neutral plan drives both mechanism evidence runs;
5. one provider-neutral comparator judges both mechanisms;
6. exact-byte local fixture behavior is deterministic and public;
7. mechanism diagnostics and portable evidence are distinct;
8. artifact/version identity is pinned and retained;
9. packet-path privilege is isolated to an ephemeral evidence lab;
10. cleanup/noninterference is verified, not assumed;
11. provider abstractions/plugins wait until accepted semantics and multiple real consumers justify them;
12. Kubernetes/cloud-scale orchestration remains an optional future implementation concern rather than v0.1 architecture authority.

## 18. What remains intentionally undecided

To avoid premature freezing, this design does not yet choose:

- future normative capability/profile identifier spelling;
- normative JSON field names/schema;
- TCK requirement IDs;
- final Python package/module names;
- a public provider SPI;
- dynamic provider discovery;
- exact Toxiproxy toxic/control configuration;
- exact nftables table/chain syntax;
- exact CI runner provider;
- future latency/loss mechanism architecture;
- Kubernetes/cloud provider architecture.

Those are decided only when their owning governance layer is authorized.

## 19. Required next work units

This design deliberately prevents implementation from being bundled into the research decision.

The governed sequence should be:

### Work unit A — research / architecture adoption

- review this research and evidence architecture;
- correct ROADMAP state/order;
- no runtime/provider implementation.

### Work unit B — evidence fixture/plan/comparator design closure

Before mechanism code, review exact non-normative evidence-plan/result representations, fixture challenge grammar, attempt counters, negative-mode assembly, and retained artifact model. This may include executable tests for pure provider-neutral evidence logic only if separately authorized and if doing so does not create a future normative TCK by precedent.

### Work unit C — terminating evidence lab

Implement the pinned Toxiproxy class against the reviewed evidence architecture. Review its one-upstream-initiation proof, security, cleanup, packaging, and evidence output.

### Work unit D — packet-path evidence lab

Implement Linux netns/veth/nftables against the same reviewed evidence architecture. Review privilege isolation, target scoping, cleanup, and evidence output.

### Work unit E — cross-mechanism evidence execution

Run both classes against the same canonical matrix, retain exact evidence, compare provider-neutral results, and close NPR-011 only if the evidence is coherent.

### Work unit F — acceptance-oriented protocol re-review

Review AEP-0012 together with NPR-011 evidence. Any new semantic blocker returns to AEP amendment; implementation is not allowed to override the AEP.

### Work unit G — explicit lifecycle decision

Request separate protocol-maintainer authorization for `AEP-0012 Proposed -> Accepted` only after re-review closure.

Only after Accepted does the normal normative chain proceed.

## 20. Non-authorization boundary

This architecture document does not authorize:

- any provider/runtime implementation;
- adding Toxiproxy, nftables wrappers, containers, or privileged workflows to the repository;
- a generic Network backend/provider abstraction;
- Network Control Spec/requirement-index/Schema/TCK/harness;
- `Proposed -> Accepted` or `Accepted -> Final`;
- release selection/publication/signing/attestation;
- weakening AEP-0012 to fit one mechanism;
- treating the selected mechanism pair as mandatory third-party implementation technology.

The pair is selected solely to produce AVP project acceptance evidence for mechanism-neutral semantics.

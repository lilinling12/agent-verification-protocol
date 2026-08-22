# Alpha 3 Environment Fabric Architecture

Status: **Design baseline — non-normative**  
Governing proposal: `rfcs/AEP-0009-environment-fabric.md`  
Baseline: `main@cdf56cf8e8d747f26b5438086ece3fb4cd489f31`

## 1. Purpose

This document defines the engineering architecture proposed for AVP Alpha 3 Environment Fabric. It is intentionally non-normative: portable semantics belong in AEP/specification text, schemas encode those semantics, TCK proves conformance, and reference code implements them.

The design is optimized for an open-source protocol ecosystem in which independent implementations must be possible without cloning the Python reference runtime or the maintainers' infrastructure.

The architecture therefore rejects transitional implementation strategies. No backend-specific implementation is allowed to become a public AVP abstraction with a promise that it will be generalized later.

## 2. Starting point: what already exists

Environment v0.1 already establishes the protocol foundation that Alpha 3 must preserve:

- authoritative mutable Environment ownership;
- immutable ScenarioInstance binding;
- reset target honesty and fail-closed behavior;
- environment-scoped deterministic/monotonic logical time within an unreverted lineage;
- actor-scoped Subject observation;
- evaluator-authoritative projections and stable digests;
- snapshot ownership and state binding;
- `EXACT`, `STATE_EQUIVALENT`, and `NON_EQUIVALENT` restore-fidelity honesty;
- semantic diff identity;
- fault occurrence/clear semantics composed with Security fault secrecy;
- released/stale handle fail-closed behavior.

Alpha 3 is not a rewrite of this contract. It is the composition layer required to apply those semantics to realistic multi-resource environments.

Historical `docs/design/alpha-v0.1/07-environment-fabric.md` is provenance-only. Its useful architectural intent is retained where compatible, but several earlier concepts have already been superseded:

- a standalone ordinal `IsolationLevel` is replaced by the current multi-dimensional `SecurityAssurance` contract;
- separate Snapshot/Chaos top-level profiles have been reconciled into Environment v0.1 and Security composition;
- Python adapter classes and runtime manifests remain implementation evidence, not protocol authority.

## 3. Architecture goals

Alpha 3 must make these properties possible for independent implementations:

1. compose multiple Environment resources without coupling AVP to one product stack;
2. discover only capabilities that have portable, testable semantics;
3. bind Environment/resource configuration and retained state to stable verification identity;
4. coordinate reset/snapshot/restore/fault/time operations without falsely claiming distributed atomicity;
5. distinguish controlled determinism from uncontrolled external nondeterminism;
6. preserve privileged Evaluator/Control Plane separation from the untrusted Subject;
7. generate Evidence sufficient to explain infrastructure behavior and restore validity;
8. execute real backend behavior in profile TCK rather than self-certifying from metadata;
9. keep conformance practical for open-source independent implementations;
10. allow PostgreSQL, MySQL, Playwright, OCI runtimes, proxies, and microVMs to be replaced by other implementations without changing AVP semantics.

## 4. Explicit non-goals

Alpha 3 does not standardize:

- a cloud control plane or hosted provisioning service;
- Kubernetes, Docker, containerd, PostgreSQL, MySQL, Playwright, Toxiproxy, Envoy, `netem`, Firecracker, Kata, or another product API;
- a universal SQL dialect;
- a distributed transaction coordinator;
- one universal database isolation level;
- one universal browser-state serialization;
- packet-for-packet deterministic networking;
- universal wall-clock virtualization;
- a global deterministic boolean;
- a security isolation score;
- a VM/container implementation as a prerequisite for base AVP conformance;
- release/version selection for Alpha 3.

## 5. Layered architecture

```text
+------------------------------------------------------------------+
| Scenario / Episode / Evaluator                                   |
+-------------------------------+----------------------------------+
                                |
                    portable requirements
                                v
+------------------------------------------------------------------+
| Environment Fabric Contract                                     |
|                                                                  |
|  Resource inventory  Capability contracts  Composition identity |
|  Operation coordination  Evidence binding  Cleanup/failure      |
+-----+----------------+----------------+--------------+------------+
      |                |                |              |
      v                v                v              v
+-----------+    +-----------+    +-----------+   +-----------+
| State     |    | Browser   |    | Network   |   | Time      |
| Profile   |    | Profile   |    | Profile   |   | Profile   |
+-----------+    +-----------+    +-----------+   +-----------+
      |                |                |              |
      +----------------+--------+-------+--------------+
                                |
                                v
                         +--------------+
                         | Compute      |
                         | Profile/OCI  |
                         +--------------+
                                |
                    non-normative adapters
                                v
+------------------------------------------------------------------+
| Reference / independent implementations                          |
| PostgreSQL | MySQL | Playwright | netem/proxy | OCI | microVM    |
+------------------------------------------------------------------+
```

The profile layer is semantic, not vendor-oriented. One profile may have multiple independent backend implementations.

## 6. Core composition objects

### 6.1 EnvironmentFabricManifest

The Fabric needs one portable immutable description of the resources that participate in an Environment instance. The exact schema will be designed after AEP-0009 review.

Conceptually it should contain:

```yaml
apiVersion: avp.environment/vNext
kind: EnvironmentFabricManifest
environmentRef: ...
scenarioInstanceDigest: sha256:...
resources:
  - resourceId: primary-database
    resourceKind: state
    capabilities: [...]
    identity: {...}
  - resourceId: subject-browser
    resourceKind: browser
    capabilities: [...]
    identity: {...}
```

This is intentionally schematic, not a schema proposal.

Rules for the future schema:

- no vendor-specific required fields in the base resource structure;
- namespaced extensions for implementation metadata;
- no secrets in portable/Subject-visible representations;
- deterministic/canonical representation rules only if required for a protocol digest;
- retained bytes use AVP Artifact identity rather than inventing another hash model;
- resource membership and Scenario binding must be immutable for the lifetime of the bound Fabric instance.

### 6.2 EnvironmentResource

A resource is independently identifiable and lifecycle-controlled within the Fabric.

Resource kinds are deliberately coarse. `state` is preferable to `postgres`; `browser` is preferable to `playwright`; `compute` is preferable to `docker`.

Vendor identity may still matter for reproducibility. It belongs under profile-defined immutable identity material or namespaced implementation metadata, not in the semantic kind.

### 6.3 CapabilitySet

Capability discovery must have one consistent mechanism across domains.

Rejected design:

```python
supports_snapshot: bool
supports_browser_storage: bool
supports_network_faults: bool
supports_virtual_clock: bool
...
```

Required direction:

```text
resource -> declared namespaced capability identifiers
capability identifier -> normative contract + schema + TCK cases
```

A capability is meaningful only when conformance obligations exist for it.

## 7. Operation model

The Fabric Control Plane coordinates operations against resources. It does not pretend heterogeneous resources share one transactional primitive.

Every multi-resource operation follows three rules:

1. **explicit target set** — know which resources are required to participate;
2. **per-resource result** — retain success/failure/fidelity per target;
3. **honest aggregate result** — aggregate success/fidelity cannot exceed component evidence.

### 7.1 Provision

Provisioning executes under Core `PROVISIONING`.

A required resource is ready only after:

- identity is established;
- ownership/Scenario binding is valid;
- required capabilities have been checked;
- privileged credentials/control channels are established outside Subject context;
- profile preconditions are satisfied.

A Fabric cannot enter `READY` while a required resource is silently degraded.

### 7.2 Reset

Reset is a state-establishment operation, not merely a cleanup command.

A resource must demonstrate the requested target state according to the applicable profile. A command returning exit code 0 is not sufficient evidence if the post-reset authoritative projection does not establish the target.

### 7.3 Snapshot

A composite snapshot is a manifest of bound resource snapshot results.

It is not assumed atomic across resources.

Potential future stronger capability:

```text
fabric.snapshot.coordinated-consistency
```

Such a capability must not exist until precise consistency semantics and TCK evidence are designed.

### 7.4 Restore

Restore validation is state/evidence based.

The minimum aggregate fidelity rule is:

```text
aggregate fidelity <= every required component's demonstrated fidelity
```

No implementation may upgrade `STATE_EQUIVALENT` to `EXACT` because the underlying backend happens to use a filesystem or VM snapshot.

### 7.5 Faults

Faults remain Environment operations governed by existing fault secrecy.

The Fabric adds routing: a scheduled fault identifies a resource/control point and a portable fault capability. Backend-specific parameters are interpreted only by the selected profile/adapter.

### 7.6 Time

Environment logical time remains distinct from physical clocks.

Alpha 3 time control must explicitly distinguish:

- Environment logical time;
- host wall clock;
- process monotonic clock;
- browser-observed wall/performance clocks;
- database/server clock;
- external service clocks.

An adapter may control some and not others. Claims must describe the actual controlled surface.

### 7.7 Release and cleanup

Cleanup must be idempotent at the protocol-observable level.

Calling cleanup again after successful release should not resurrect or mutate a resource. Stale handles must fail closed.

If cleanup fails and leaves privileged infrastructure in an uncertain state, the result is infrastructure health/validity information. It is never transformed into an Agent Task Verdict.

## 8. Relational state profile design

### 8.1 Portable scope

A relational state profile should standardize what the Evaluator can observe and verify, not database engine internals.

Portable concepts likely include:

- selected logical database/schema identity;
- projection specification;
- stable representation/digest for projected state;
- reset target binding;
- snapshot ownership/reference;
- restore fidelity;
- semantic diff;
- declared transaction/isolation behavior only when needed by a Scenario and testable portably.

### 8.2 PostgreSQL and MySQL are not semantically identical

PostgreSQL Repeatable Read provides a stable transaction view and supports exported/imported snapshots across transactions under documented constraints. MySQL/InnoDB has its own consistent-read and isolation behavior, with `REPEATABLE READ` as the default in MySQL 8.4.

These mechanisms are valuable implementation evidence, but Alpha 3 must not pretend identical engine commands imply identical semantics.

Therefore:

- adapter-specific snapshot tokens remain implementation detail unless retained as evaluator diagnostics;
- portable snapshot identity is AVP-owned and projection/evidence-bound;
- the TCK compares observable state semantics, not SQL command sequences;
- schema normalization must be explicit—collations, generated columns, sequences/auto-increment, timezone/session variables, engine-specific metadata, and extension objects cannot be silently ignored if the selected projection claims them.

### 8.3 No universal SQL transaction abstraction

Do not introduce a generic AVP `begin/commit/rollback` database API as the primary state profile. AVP is verifying environment state, not replacing database clients.

Transaction controls may exist as adapter capabilities when a Scenario requires them, but the protocol-level contract should remain about observable verification behavior.

## 9. Browser profile design

### 9.1 Isolation unit

The preferred portable unit is an isolated browser session/context, not a globally shared browser process.

Playwright BrowserContext is strong implementation evidence: non-persistent contexts provide isolated sessions, and context storage state can include cookies/local storage/IndexedDB and newer credential material depending on options.

AVP should define the portable session/state semantics without depending on Playwright object names.

### 9.2 State surfaces are explicit

Browser state cannot be represented as one opaque `storageState` claim.

The profile must classify surfaces such as:

- cookies;
- local storage;
- IndexedDB;
- session-only state where observable;
- service workers;
- caches;
- virtual WebAuthn/passkeys if enabled;
- downloads;
- uploaded file effects;
- pages/tabs/popups;
- cross-origin storage boundaries.

Each profile version must say which surfaces participate in snapshot/restore and which are explicitly excluded.

### 9.3 Evidence surfaces

Potential portable Evidence includes:

- DOM projection;
- accessibility-tree projection where stable enough for the profile;
- screenshot Artifact;
- browser/network event trace;
- console/page error events;
- download Artifact;
- resource identity and browser engine/version.

Screenshots and traces are Evidence, not automatically authoritative state.

### 9.4 Replay honesty

Browser execution is influenced by layout, fonts, GPU/headless mode, browser build, service workers, remote content, timing, random IDs, and external services.

Alpha 3 must never claim browser replay is globally deterministic because navigation steps were repeated.

## 10. Network fault profile design

### 10.1 Semantic fault model

Initial portable candidates:

- bounded added latency;
- connection refusal/disconnect;
- bounded packet/message loss where the control point can establish it;
- DNS resolution failure;
- HTTP-level response failure only in an application-layer profile, not mislabeled as packet loss.

The profile must distinguish layer and control point.

### 10.2 Implementation mechanisms

Possible adapters:

- Linux `tc-netem`;
- Toxiproxy-style connection proxies;
- Envoy fault filters;
- mitmproxy/application-level interception;
- container/network-namespace controls.

`netem` demonstrates why the portable contract must be conservative: its own documentation notes kernel timer granularity and TCP queue behavior can affect delay/rate/reordering results.

Therefore the TCK should test bounded observable semantics, not demand identical packet timelines across hosts.

### 10.3 TLS and secrets

TLS interception is not a default network-fault requirement. It changes trust boundaries and credential handling.

If an implementation performs TLS termination/interception, corresponding credential/security implications require explicit assurance and Evidence handling.

## 11. Time-control profile design

### 11.1 Clock taxonomy

A future time profile must model controlled clocks explicitly rather than exposing one `now()` override.

Potential semantic operations:

- read controlled wall time;
- freeze controlled wall time;
- advance controlled wall time;
- execute/synchronize controlled timers;
- observe monotonic ordering guarantees.

### 11.2 Cross-process coordination

A virtual clock service is only credible if each participating process/runtime is actually bound to it.

For example, advancing an AVP clock does not change:

- PostgreSQL `now()` unless the database is instrumented/controlled accordingly;
- browser `Date.now()` unless the browser profile binds it;
- TLS certificate validation performed by an uncontrolled runtime;
- remote API server clocks;
- kernel scheduling time.

The profile must permit partial controlled surfaces and forbid global claims when these remain real-time dependencies.

## 12. Compute/OCI profile design

### 12.1 Reuse OCI

OCI already specifies container image structure, content-addressed descriptors/configuration, runtime configuration, and runtime lifecycle. AVP should bind to those standards instead of defining another container format.

A compute resource may bind:

- immutable image manifest/config descriptors;
- runtime-spec version;
- platform/architecture identity;
- execution configuration relevant to verification;
- resource limits where they affect Scenario validity;
- filesystem/mount/network policy identity;
- runtime implementation metadata as non-normative provenance.

### 12.2 AVP-specific responsibility

OCI does not define AVP Scenario binding, Evaluator/Subject trust outcome, Environment projection/snapshot semantics, Evidence classification, or conformance result semantics. Those remain AVP responsibilities.

### 12.3 Container security honesty

A container is not a security-assurance level.

A deployment using containers may still report:

```text
process: not-claimed
network: not-claimed
tenant: not-claimed
sandbox: not-claimed
```

unless evidence verifies those SecurityAssurance dimensions.

## 13. microVM experiment

microVMs remain a separate experiment rather than a mandatory Alpha 3 dependency.

Research questions:

- can a portable compute contract describe both OCI/shared-kernel and VM-backed implementations without hiding material isolation differences?
- what host/kernel/CPU/device identity is needed for meaningful snapshot replay?
- can snapshot restore be tested on public CI reliably?
- what does migration between host CPU models do to fidelity claims?
- can an independent implementation run the relevant TCK without specialized cloud infrastructure?

Only after those questions have evidence should a normative microVM capability be proposed.

## 14. Security architecture

### 14.1 Planes

```text
Subject Agent Plane
  | only Scenario-granted capability routes
  v
Environment resource data/action surfaces

-------------------------------- trust boundary ----------------------------

Evaluator Plane        Control Plane
  projections           provision/release
  evidence              reset/snapshot/restore
  oracle access         fault/time control
  confidential data     privileged credentials
```

The Subject must never receive a generic Fabric control handle.

### 14.2 Credentials

Each backend should use a credential context designed for least privilege.

Examples:

- Subject database credentials permit only Scenario-granted data operations;
- Evaluator projection credentials may be read-only but broader;
- Control credentials for reset/snapshot are separate and never injected into Subject compute;
- proxy/root/network namespace authority remains Control Plane only;
- container runtime socket access is never exposed to Subject merely because the Subject itself runs in a container.

### 14.3 Host escape and privileged infrastructure

Reference adapters that require root, Docker socket, network namespace mutation, KVM, or other host privilege must execute in deliberately isolated CI/deployment contexts.

Such privileges are implementation/deployment requirements, not AVP protocol capabilities exposed to the Subject.

## 15. Failure and validity model

Backend errors must be normalized before protocol interpretation.

```text
backend error/exit/status
        |
        v
resource operation result + evaluator diagnostics
        |
        v
Environment/Fabric validity or infrastructure classification
        |
        +----X----> never directly becomes Agent Task Verdict
```

The architecture should define stable machine-readable Fabric cause codes only for distinctions that independent implementations can preserve. Vendor error codes stay namespaced diagnostics.

## 16. Conformance architecture

### 16.1 Base Fabric TCK

The base profile should test composition semantics with a real adapter interface, including negative implementations.

Proposed mandatory cases:

| Case | Purpose |
|---|---|
| Fabric lifecycle | provision required resources, bind ownership, release, stale-use rejection |
| Capability honesty | undeclared capability fails closed; declared capability executes real operation |
| Resource identity | membership/resource identity stable and Scenario-bound |
| Multi-resource result | required target results complete; no silent partial success |
| Composite snapshot | ownership + immutable composition identity |
| Snapshot tamper/foreign | reject substituted/foreign resource snapshot |
| Restore fidelity | no aggregate fidelity inflation |
| Cleanup | retry-safe cleanup; leak/failure reported as infrastructure condition |

### 16.2 Domain TCK profiles

Profiles are registered separately:

```text
base Fabric composition
  + relational-state capability
  + browser capability
  + network-fault capability
  + time-control capability
  + compute capability
```

An implementation runs the mandatory base profile when it claims Environment Fabric. Domain profiles are mandatory only for claimed capabilities.

### 16.3 Real execution requirement

Every execution-sensitive TCK case must invoke the real adapter operation.

Forbidden conformance logic:

```python
if capability in implementation.capabilities:
    return PASS
```

Required logic:

```text
claim capability
 -> invoke behavior
 -> observe state/evidence/side effect
 -> compare with authoritative vector/contract
 -> PASS or FAIL
```

Negative adapter fixtures should deliberately retain the same capability declaration while corrupting runtime behavior. If the TCK still passes, the case is invalid.

### 16.4 CI tiers

The long-term CI model should distinguish semantic cost, not create temporary APIs:

**Tier A — portable package/conformance**
- base Fabric protocol resource/schema validation;
- language-neutral TCK vectors;
- reference composition behavior that requires no privileged external backend.

**Tier B — real backend integration**
- pinned PostgreSQL versions;
- pinned MySQL versions;
- pinned Playwright/browser versions;
- network-fault backend on supported Linux runners;
- OCI compute runtime on supported Linux runners.

**Tier C — experimental assurance**
- microVM/KVM experiments;
- privileged host isolation tests;
- architecture-specific snapshot tests.

Tier C does not gate ordinary base Fabric conformance until the capability becomes portable and governed.

No tier is a disposable architecture. The same protocol contracts and adapters remain the long-term design; the tiers only control test infrastructure cost.

## 17. Backend identity and reproducibility

A verification run must record enough immutable backend identity to distinguish materially different execution environments.

Examples:

### Database
- engine family and exact version;
- selected extensions/plugins affecting semantics;
- schema/projection identity;
- relevant collation/timezone/config identity when selected by the profile.

### Browser
- browser engine;
- exact browser build/version;
- operating platform where relevant;
- selected context options;
- state-surface profile.

### Network
- portable fault contract;
- control point/layer;
- implementation/version metadata for diagnosis;
- host/kernel identity only when needed to interpret bounded behavior.

### Compute
- OCI image manifest digest, not mutable tag alone;
- OCI/runtime configuration identity;
- platform architecture;
- resource limit/policy identity selected by the profile.

These values support reproducibility but do not all need to be mandatory base fields. Each domain profile must separate normative identity inputs from diagnostic implementation metadata.

## 18. No-transitional-implementation policy

Alpha 3 adopts the following engineering rules from its first implementation PR.

### Forbidden

1. Implement PostgreSQL first with a PostgreSQL-shaped public API and promise a generic state adapter later.
2. Implement Playwright public models and later rename them into generic browser resources.
3. Add a generic `extras`/`dict[str, Any]` bag for fields that are already known to require portable semantics.
4. Scatter optional methods and `supports_*` flags through one giant adapter.
5. Keep old and new pre-release Environment APIs alive through compatibility shims with no released compatibility requirement.
6. Hard-code product names into TCK expectation semantics.
7. Treat the in-memory Python adapter as a semantic oracle.
8. Claim exact restore because a backend checkpoint operation succeeded without validating the resulting state.
9. Claim deterministic execution based on seed/logical time while uncontrolled real-time/network/browser dependencies remain.
10. Create an ordinal isolation score.
11. Surface Docker/containerd/KVM/root control endpoints to Subject code.
12. Ship TODO/stub protocol methods that return success or `NotImplemented` as an advertised capability.
13. Merge a backend as Alpha 3 production/reference support before its portable contract and execution-sensitive TCK are reviewable.

### Required instead

- decide portable semantics first;
- encode protocol resources in schemas before public runtime models depend on them;
- design conformance vectors before treating reference behavior as correct;
- use one capability registry model;
- use honest conditional capabilities;
- fail closed on unsupported/foreign/stale operations;
- maintain exact Evidence/resource identity;
- keep implementation metadata namespaced and non-authoritative;
- prefer removal/refactor of unreleased internal APIs over compatibility shims;
- merge only coherent domain slices that are complete from contract through TCK through reference implementation.

## 19. AEP decomposition policy

Do not create one AEP per adapter, and do not put all Alpha 3 semantics into AEP-0009.

Decision rule:

- **new portable semantics / trust boundary / compatibility contract** -> AEP required;
- **schema/TCK realization of an accepted AEP** -> governed normative PR, normally no new AEP;
- **additional vendor backend satisfying an existing profile** -> implementation PR, no AEP;
- **experimental mechanism with no portable claim** -> research/experimental area, no conformance claim.

Likely follow-up decisions:

1. relational state profile;
2. browser state/evidence profile;
3. network fault profile;
4. time-control profile;
5. OCI-aligned compute profile.

These may be separate AEPs if review finds substantive normative decisions; otherwise they may be profile specifications under AEP-0009's accepted composition model.

## 20. Implementation order

The correct sequence is deliberately different from the old roadmap's backend-only checklist.

### Gate 0 — Foundation design
- AEP-0009 Draft;
- architecture review;
- normative-gap matrix against Environment v0.1/Security/Evidence/Core;
- decide capability/resource identity vocabulary.

### Gate 1 — Fabric normative closure
- Fabric spec;
- requirement index;
- schema(s);
- base TCK vectors including negative adapters;
- acceptance audit that no Python behavior is the authority.

### Gate 2 — Relational state vertical slice
- relational profile semantics/schema/TCK;
- PostgreSQL adapter;
- MySQL adapter;
- cross-backend conformance proving the abstraction is not PostgreSQL-shaped.

### Gate 3 — Browser vertical slice
- browser profile;
- browser-state/evidence TCK;
- Playwright reference adapter;
- browser/version pinning and service-worker/cross-origin cases.

### Gate 4 — Network + time
- network-fault profile and real fault backend;
- time-control profile and explicitly bounded virtual-clock implementation;
- composition tests involving state/browser where practical.

### Gate 5 — OCI compute
- OCI-aligned compute profile;
- reference container runtime;
- image/config identity, resource limits, mount/network policy evidence;
- SecurityAssurance non-inflation tests.

### Gate 6 — microVM experiment
- implementation experiment;
- isolation/snapshot evidence;
- no portable conformance claim unless a later governance decision approves one.

## 21. Release boundary

The repository currently has `0.3.1.dev0` as a maintenance development identity with `0.3.1` as the next planned release target.

Alpha 3 protocol work must not silently consume that target. No design or implementation PR in this phase changes release mode or selects a release.

When enough Alpha 3 normative scope is known, release management must separately decide an appropriate pre-1.0 version under `docs/RELEASE_PROCESS.md`.

## 22. External standards and implementation evidence

The design intentionally composes with established mechanisms rather than cloning them:

- PostgreSQL transaction isolation and snapshot synchronization;
- MySQL/InnoDB isolation and consistent reads;
- Playwright BrowserContext isolation and storage-state APIs;
- Linux `tc-netem` fault mechanisms and documented limitations;
- OCI Runtime Specification for container configuration/execution/lifecycle;
- OCI Image Specification for image structure/content-addressed descriptors;
- Firecracker/Kata/other microVM implementations as isolation experiments.

These are engineering evidence and integration points. AVP semantics remain governed by AVP specification/TCK.

## 23. Definition of done for this architecture phase

The architecture phase is complete only when:

- AEP-0009 has received protocol review and its unresolved questions are recorded;
- every proposed Fabric semantic is classified as new, reused, or explicitly non-normative relative to Environment v0.1;
- SecurityAssurance/Evidence/Core duplication has been eliminated;
- base capability/resource identity semantics are precise enough to write schemas without vendor fields;
- TCK negative-case design is agreed before backend implementation;
- relational state design can be implemented by both PostgreSQL and MySQL without changing the base abstraction;
- browser design is not Playwright-object shaped;
- compute design is OCI-aligned without equating OCI compliance to AVP security assurance;
- no release-selection boundary has been crossed.

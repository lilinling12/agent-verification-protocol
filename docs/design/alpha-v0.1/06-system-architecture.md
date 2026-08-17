# 06 Agent Verification OS — System Architecture

> Version: Architecture Baseline v0.1  
> Date: 2026-08-11  
> Goal: production/reference architecture for AVP/AVS and the Agent Reliability platform.

## 1. Architectural Thesis

The system is not primarily a trace SaaS.

Its technical center is:

```text
Reproducible Environment
+ Verification Evidence
+ Experiment Orchestration
+ Replay
+ Reliability Statistics
+ Failure Intelligence
```

The architecture optimizes for:

- reproducibility;
- strong isolation;
- high Episode throughput;
- long-running workflows;
- multiple runtime types;
- content-addressed artifacts;
- open protocol conformance;
- private deployment;
- ecosystem adapters.

---

# 2. Logical Architecture

```text
                           ┌─────────────────────┐
                           │  Web / CLI / SDK    │
                           └──────────┬──────────┘
                                      │
                           ┌──────────▼──────────┐
                           │    API Gateway      │
                           └──────────┬──────────┘
                                      │
          ┌───────────────────────────┼────────────────────────────┐
          │                           │                            │
          ▼                           ▼                            ▼
┌──────────────────┐       ┌──────────────────┐         ┌──────────────────┐
│ Control Plane    │       │ Experiment Plane │         │ Registry Plane   │
│ project/auth     │       │ orchestrator     │         │ agent/env/spec   │
└────────┬─────────┘       └────────┬─────────┘         └────────┬─────────┘
         │                          │                            │
         └──────────────┬───────────┴────────────────────────────┘
                        ▼
               ┌─────────────────────┐
               │ Runtime Scheduler   │
               └──────────┬──────────┘
                          │
        ┌─────────────────┼───────────────────────────┐
        ▼                 ▼                           ▼
┌──────────────┐  ┌────────────────┐        ┌─────────────────┐
│ Container    │  │ Browser Runtime│        │ microVM / VM    │
│ API/DB/MCP   │  │ Playwright etc │        │ Desktop/CLI     │
└──────┬───────┘  └────────┬───────┘        └────────┬────────┘
       │                   │                          │
       └───────────────────┼──────────────────────────┘
                           ▼
                ┌─────────────────────┐
                │ Environment Fabric  │
                │ AVP Runtime Agent   │
                └───────┬─────────────┘
                        │
         ┌──────────────┼───────────────────┐
         ▼              ▼                   ▼
┌──────────────┐ ┌───────────────┐  ┌────────────────┐
│ State Ledger │ │ Trace Ingest  │  │ Snapshot Store │
└──────┬───────┘ └──────┬────────┘  └──────┬─────────┘
       │                │                  │
       └────────────────┼──────────────────┘
                        ▼
              ┌────────────────────┐
              │ Verification Plane │
              │ Oracle/Judge/Valid │
              └─────────┬──────────┘
                        ▼
              ┌────────────────────┐
              │ Reliability Engine │
              └─────────┬──────────┘
                        ▼
              ┌────────────────────┐
              │ Failure Intelligence│
              └─────────┬──────────┘
                        ▼
              ┌────────────────────┐
              │ Replay / Regression│
              └─────────┬──────────┘
                        ▼
              ┌────────────────────┐
              │ Release Gate       │
              └────────────────────┘
```

---

# 3. Physical Security Boundary

Most important deployment rule:

```text
Subject Runtime Network
≠
Evaluator Network
```

Recommended:

```text
Execution Namespace / VPC A
  subject Agent
  Agent-visible MCP tools
  browser
  user simulator

Verification Namespace / VPC B
  privileged state adapters
  oracles
  benchmark secrets
  judges
  evaluator credentials
```

Only controlled runtime mediators bridge these planes.

This is not cosmetic. It prevents the standard itself becoming an answer-key leak.

---

# 4. Core Services

## 4.1 Control Service

Responsibilities:

- workspaces/projects;
- RBAC;
- Agent registry;
- Environment registry;
- Scenario registry;
- release policies;
- API façade.

This is conventional infrastructure and not the strategic moat.

## 4.2 Experiment Orchestrator

Responsibilities:

```text
Experiment Matrix
→ Episode creation
→ runtime allocation
→ durable lifecycle
→ retries/timers
→ pause/resume
→ verification
→ aggregation
```

A memory-only job queue is insufficient because long-horizon Episodes may outlive workers.

Use a **durable workflow abstraction**. Build-vs-integrate: integrate a mature engine rather than make workflow persistence the moat.

## 4.3 Runtime Scheduler

Schedules isolated execution using:

```text
runtime profile
CPU/RAM/GPU
snapshot affinity
region
browser/OS requirement
security level
network policy
```

Output: runtime lease + AVP endpoint.

## 4.4 Environment Runtime Agent

Runs next to/inside each Environment.

Implements:

- health;
- reset;
- snapshot;
- restore;
- state projection;
- fault control;
- event emission.

---

# 5. Environment Runtime Tiers

There should not be one universal sandbox implementation.

## Tier 0 — Logical

Best for API/DB/MCP business agents.

Reset through:

- transaction rollback;
- fixture reload;
- logical event-store reset.

Characteristics: extremely fast, cheap, high throughput.

## Tier 1 — Container / Service

Best for multi-service applications and backend integration.

Reset through:

- container recreation;
- DB snapshot;
- volume snapshot;
- object-store namespace reset.

## Tier 2 — Browser

Best for web agents.

Uses:

- isolated browser contexts;
- storage-state bootstrap;
- backend snapshots;
- network proxy;
- DOM/accessibility/pixel adapters.

Browser-local state alone is not enough to claim full world-state replay.

## Tier 3 — microVM

Best for:

- coding/CLI agents;
- Linux computer use;
- stronger isolation;
- runtime checkpoints.

Firecracker-style full/diff snapshots are useful, but snapshot manifests must capture disk/network compatibility and external dependencies.

## Tier 4 — Full VM / Remote Lab

Best for:

- Windows/macOS desktop agents;
- heavyweight enterprise applications;
- hardware-specific environments.

---

# 6. Composite Snapshot Architecture

A snapshot is a manifest over independently versioned components:

```text
Composite Snapshot
├── runtime memory/state
├── volumes
├── database
├── object-store namespace
├── browser storage
├── virtual clock
├── API record/replay state
└── external dependency manifest
```

Possible mechanisms:

```text
logical fixture
database-native snapshot
CSI volume snapshot
volume-group snapshot
microVM snapshot
application checkpoint
external API record/replay
```

A Scenario chooses minimum fidelity needed for valid verification.

---

# 7. Browser Runtime

Reference design:

```text
Browser Worker
├── Playwright
├── isolated BrowserContext
├── optional screenshot/pixel stream
├── accessibility tree
├── DOM capture
├── storage-state snapshot
├── programmable network
└── backend State Adapter
```

The runtime should support:

```text
DOM agent
Accessibility agent
Vision agent
Hybrid agent
```

to prevent benchmark architecture bias.

Playwright-like BrowserContext isolation provides cheap clean sessions; authenticated state can be loaded/restored. Backend state should remain authoritative for transactional outcomes.

---

# 8. DB/API Runtime

For enterprise agents this is likely the highest-value runtime.

## State Adapter Contract

```text
project()
digest()
diff()
assert()
snapshot()
restore()
```

Adapters:

- PostgreSQL;
- MySQL;
- SQLite;
- document stores;
- event stores;
- custom domain APIs.

## Typed State Projection

Do not expose entire DBs to generic judges.

Use domain projections:

```text
OrderStateProjection
CalendarStateProjection
PaymentStateProjection
PatientStateProjection
```

Typed projections improve privacy and oracle stability.

---

# 9. MCP Runtime

MCP is the Agent-facing tool protocol.

```text
Subject Agent
    ↓ MCP
MCP Gateway
    ├── real MCP server
    ├── simulated MCP server
    ├── schema mutation proxy
    ├── fault proxy
    └── security injection proxy
```

Gateway records:

- discovery;
- schema identity;
- calls;
- results;
- errors;
- latency;
- server identity.

Privileged AVP evaluator methods stay on a separate endpoint/network.

---

# 10. A2A Runtime

For multi-agent tests:

```text
Agent A
   ↓ A2A
Agent B
   ↓
Shared Environment
```

Verification observes:

- delegation;
- artifacts/messages;
- authority handoff;
- shared-state mutations;
- duplicate/cyclic work;
- responsibility.

Opaque Agent internals are not required.

---

# 11. Virtual Clock

Core Environment service:

```text
now()
advance(duration)
schedule(event)
freeze()
unfreeze()
```

Use cases:

- booking cutoff;
- credential expiration;
- SLA;
- retry backoff;
- deadline;
- settlement;
- scheduled automation.

Applications may need injectable time providers for deterministic tests.

---

# 12. Network Fault Proxy

Support:

```text
delay
jitter
timeout
disconnect
bandwidth limit
packet loss
HTTP 429
HTTP 500
response corruption
partial response
stale response
duplicate response
out-of-order response
```

Every activated fault emits AVP lifecycle events.

---

# 13. Permission / Authority Simulator

First-class service:

```text
grant
revoke
expire
narrow
approve
invalidate
```

High-risk commits can reference an authority witness.

This enables tests like:

> approval was valid when read, but revoked before commit.

---

# 14. State Ledger

State Ledger stores:

```text
Episode
→ logical step
→ state digest
→ semantic delta
→ cause event
→ side effect
```

Recommended design:

- append-only event stream;
- materialized state-diff projections;
- immutable object artifacts;
- query index.

This is the basis of first-bad-step analysis and replay.

---

# 15. Trace Ingestion

Sources:

```text
OpenTelemetry OTLP
Agent SDK hooks
LangGraph instrumentation
existing observability exports
MCP gateway
browser runtime
environment runtime
custom AVP events
```

Canonical storage preserves source-native fields plus normalized AVP links.

Do not destroy raw provenance during normalization.

---

# 16. Storage Architecture

Use fit-for-purpose storage.

## Relational metadata store

Good for:

- workspace;
- Agent;
- Scenario;
- Experiment;
- release policy;
- permissions.

Recommended class: PostgreSQL-compatible relational DB.

## Analytical event store

Good for:

- high-volume Episode events;
- slices;
- latency/cost aggregations.

Recommended class: columnar analytical DB such as ClickHouse.

## Object store

S3-compatible for:

- screenshots;
- state projections;
- state diffs;
- raw tool results;
- snapshots;
- benchmark fixtures.

## Semantic index

Optional vector/index layer for failure clustering. Never source of truth.

---

# 17. Artifact Model

Everything large becomes immutable artifact:

```text
prompt
tool_result
screenshot
DOM
file
state_projection
state_diff
snapshot
oracle_output
judge_context
benchmark_fixture
replay_patch
```

Artifact fields:

```text
digest
size
media_type
classification
producer
created_at
retention
```

Content addressing enables deduplication and reproducibility.

---

# 18. Verification Engine

```text
Claim Router
  ├── State Oracle
  ├── Executable Test
  ├── Temporal Rule
  ├── Policy Engine
  ├── Schema Validator
  ├── Semantic Judge Router
  ├── Agentic Judge
  └── Human Review
```

## Oracle sandbox

Executable oracles receive only declared evidence and run without arbitrary production credentials/internet by default.

---

# 19. Temporal Rule Engine

Normalize trajectory rules into event automata/queries.

Example:

```text
verify_identity BEFORE refund.commit
```

becomes conceptually:

```text
on refund.commit:
  require preceding verify_identity(success=true)
```

Future AVP versions may standardize a limited temporal logic.

---

# 20. Judge Router

Route by claim type:

```text
state fact           → State Oracle
ordering             → Temporal Engine
schema validity      → Validator
semantic explanation → LLM Judge
complex artifact     → Agentic Judge
high-risk conflict   → Human
```

The router is more important than choosing one largest judge model.

---

# 21. Judge Reliability Lab

Stores:

```text
JudgeDefinition
JudgeVersion
GoldSet
CalibrationRun
ConfusionMatrix
ReliabilitySlice
CostProfile
```

A Judge change is itself a versioned release and should pass gates.

---

# 22. Reliability Engine

Input:

```text
Episode outcomes
paired identities
scenario clusters
seed families
infrastructure metadata
```

Output:

```text
success rate
Pass^k
Success@k
paired delta
confidence interval
effect size
variance components
slice analysis
power recommendation
```

Statistical computation should be an independent service/library, not UI logic.

---

# 23. Experiment Planner

High-value workflow:

User asks:

> Is Agent B at least 2pp better without safety regression?

Planner produces:

```text
paired design
required sample
repeat count
slice quota
stopping policy
```

Adaptive sampling can terminate obvious regressions early and allocate more budget to uncertain slices.

---

# 24. Failure Intelligence

Pipeline:

```text
Failure Episode
→ validity filter
→ first-error candidates
→ structured feature extraction
→ event-graph neighborhood
→ semantic representation
→ cluster
→ cluster label
→ Agent-version diff
→ RCA hypothesis
```

Invalid Environment/Eval runs must never be mixed into Agent failure clusters.

---

# 25. First-Bad-Step Localization

Signals include:

- first violated temporal constraint;
- first incorrect state transition;
- first stale observation use;
- first wrong target;
- first unsafe control decision;
- first metamorphic divergence.

Output is an analysis artifact referencing immutable trace events.

---

# 26. Failure Knowledge Graph

Nodes:

```text
FailurePattern
AgentComponent
Tool
SchemaField
EnvironmentCondition
ControlGate
RiskClass
Intervention
ScenarioFamily
```

Edges:

```text
OCCURS_WITH
CAUSED_BY_HYPOTHESIS
IMPROVED_BY
REGRESSED_AFTER
TRIGGERED_UNDER
AFFECTS
```

Counterfactual experiments strengthen edge confidence.

This graph is a long-term product/data moat.

---

# 27. Counterfactual Replay Engine

```text
Failure Episode
   ↓
Checkpoint before candidate first bad step
   ↓
Freeze declared controls
   ↓
Apply one intervention
   ↓
Replay N times
   ↓
Compare state/outcome/failure pattern
   ↓
Root-cause evidence grade
```

The engine records uncontrolled differences and MUST NOT overclaim causality.

---

# 28. Replay Cost Optimization

Long-horizon tests require:

- periodic checkpoints;
- checkpoints before state-changing actions;
- checkpoints before high-risk commits;
- suffix-only replay;
- deterministic result caching where valid;
- copy-on-write snapshots;
- adaptive replay count.

---

# 29. Production Miner

Privacy-aware pipeline:

```text
Production Trace
  ↓
risk-aware sampling
  ↓
PII redaction/tokenization
  ↓
failure/novelty detection
  ↓
Scenario reconstruction
  ↓
Environment binding
  ↓
Oracle candidate generation
  ↓
solvability validation
  ↓
Private Regression Suite
```

Production data MUST NOT automatically become public benchmark data.

---

# 30. Regression Generator

Inputs:

- validated incident;
- failure cluster;
- security finding;
- user correction;
- manual bug.

Outputs:

```text
minimal reproducer
boundary variants
metamorphic variants
chaos variants
security variants
```

Generated tests enter quarantine until validity/solvability checks pass.

---

# 31. Release Gate

Policy-as-code:

```yaml
require:
  state_success: ">= 0.95"
  pass_pow_5: ">= 0.80"
  critical_safety_failures: 0

regression:
  max_success_drop_pp: 1.0
  max_control_risk_increase: 0

validity:
  max_invalid_rate: 0.01

statistics:
  paired_ci_required: true
```

Gate output must include supporting evidence, not only boolean.

---

# 32. CLI / CI

Example:

```bash
avp experiment run \
  --benchmark enterprise-refunds@2026.08 \
  --baseline agent:v41 \
  --candidate agent:v42 \
  --gate release-policy.yaml
```

Integrations:

- GitHub Actions;
- GitLab CI;
- Jenkins;
- generic API/CLI.

---

# 33. SDK Strategy

Priority:

```text
Python
TypeScript
Java
Go
```

Schemas should generate models/validators where possible.

Handwritten SDK logic focuses on:

- adapters;
- runtime middleware;
- OTel instrumentation;
- local runner.

---

# 34. Technology Strategy

Do not force one language.

## Protocol/spec
Markdown + JSON Schema + OpenAPI + conformance fixtures.

## Control Plane
Java 21/Kotlin or Go are suitable. Enterprise-heavy domain logic can use Java/Kotlin very effectively.

## Runtime/Scheduler Agent
Go is attractive for Kubernetes/container/network daemons.

## Scenario/Eval Ecosystem
Python is mandatory because benchmark and AI research ecosystems are Python-heavy.

## Web
TypeScript/React.

Architecture quality comes from protocol boundaries, not language uniformity.

---

# 35. Durable Workflow

Required properties:

- durable timers;
- retries;
- child workflows;
- pause/resume;
- signals;
- idempotency;
- long-running execution.

Recommendation:

> integrate a mature workflow engine first; do not spend differentiation budget rebuilding durable workflow persistence.

---

# 36. Kubernetes Reference Deployment

```text
Management Cluster
  control plane
  registry
  UI
  metadata

Execution Clusters
  runtime scheduler
  episode workers
  browser pools
  microVM pools
  judge workers

Storage
  relational
  analytical
  object
```

Execution clusters may be regional/customer-private.

Kubernetes CSI volume snapshots and volume-group snapshots can support some service-state restoration, but AVP snapshot semantics remain above any single storage implementation.

---

# 37. Private Deployment

Enterprise must support:

```text
SaaS Control Plane
+
Customer-hosted Execution Plane
```

and optionally fully air-gapped mode.

Only configured metadata/summary may cross customer boundary.

---

# 38. Multi-Tenancy

Tenant isolation covers:

- compute runtime;
- snapshot storage;
- object artifacts;
- Judge context;
- secrets;
- network egress.

High-risk subject agents should not share runtime processes across tenants.

---

# 39. Snapshot Security

Snapshots may contain:

- session cookies;
- API tokens;
- secrets;
- customer data;
- memory-resident credentials.

Therefore:

- encrypt at rest;
- tenant-scoped keys;
- short-lived access;
- no public artifact URLs;
- retention;
- clone uniqueness controls;
- explicit classification.

---

# 40. Verification Platform SRE

Metrics:

```text
environment_valid_run_rate
reset_failure_rate
snapshot_restore_success
replay_equivalence_rate
trace_loss_rate
oracle_error_rate
judge_error_rate
episode_queue_latency
runtime_provision_latency
infra_variance
```

A failing Eval platform must not silently lower subject scores.

---

# 41. Scale Model

Example:

```text
500 scenarios
× 4 Agent variants
× 8 repetitions
= 16,000 Episodes
```

Need:

- fan-out/fan-in;
- backpressure;
- provider rate limits;
- quotas;
- sharding;
- adaptive stopping.

---

# 42. Cost Architecture

Separate:

```text
model cost
judge cost
browser runtime
VM runtime
storage
artifact bandwidth
external API
```

Optimize with:

- deterministic oracle first;
- semantic judge only when needed;
- suffix replay;
- artifact dedup;
- snapshot dedup;
- lower-cost workers for non-critical runs.

---

# 43. Build vs Integrate

## Build — strategic

```text
AVP protocol
AVS compiler
Environment abstraction
State Ledger semantics
Composite Snapshot Manifest
Oracle/evidence contract
Eval validity
Reliability engine
Failure Intelligence
Counterfactual Replay
Regression generation
Release Gate
```

## Integrate — commodity

```text
Kubernetes
container runtime
object storage
relational DB
analytical DB
Playwright
microVM technology
OpenTelemetry
model providers
durable workflow engine
OAuth/OIDC
```

---

# 44. Reference Repository

```text
agent-verification/
├── spec/
│   ├── avp/
│   ├── avs/
│   └── telemetry/
├── schemas/
├── openapi/
├── conformance/
├── examples/
├── sdk/
│   ├── python/
│   ├── typescript/
│   ├── java/
│   └── go/
├── adapters/
│   ├── mcp/
│   ├── a2a/
│   ├── otel/
│   ├── langgraph/
│   └── benchmarks/
├── runtime/
│   ├── api-db/
│   ├── browser/
│   ├── mcp/
│   └── microvm/
├── oracle/
├── cli/
└── platform/
```

Spec governance can later become independent of commercial implementation.

---

# 45. Open-Core Boundary

Recommended open source:

```text
AVP spec
AVS spec
schemas
conformance
local runner
SDKs
basic runtime adapters
public benchmark adapters
OTel integration
```

Commercial/enterprise:

```text
distributed orchestration
managed execution clusters
private Environment Fabric
snapshot infrastructure
Failure Knowledge Graph
counterfactual RCA
Production Miner
enterprise governance
benchmark network
```

This lets the protocol become trusted without giving away all operational moat.

---

# 46. First Complete Vertical Slice

Do not build “small features”. Build one complete verification loop:

```text
Commerce Refund Agent
+
MCP tools
+
MySQL/PostgreSQL state
+
virtual clock
+
state oracle
+
timeout fault
+
Pass^k
+
first-bad-step
+
snapshot replay
+
release gate
```

Then add Browser and microVM runtimes.

Principle:

> **narrow domain, complete verification loop — not broad UI, shallow Eval.**

---

# 47. Subsequent Slices

## Slice 2
Browser runtime + backend-state correlation + indirect injection + production trace import + mutation.

## Slice 3
microVM + long-horizon checkpointing + counterfactual planner + A2A/multi-agent + package registry.

## Slice 4
World Generator + policy compiler + auto-oracle candidates + failure graph + adaptive living benchmark + certification/network.

---

# 48. Architecture Decisions

1. **AVP sits above MCP/A2A and beside OpenTelemetry.**
2. **Agent Plane ≠ Evaluator Plane.**
3. **State/event/evidence are content-addressed.**
4. **Episode is the fundamental execution unit.**
5. **Environment fidelity is tiered.**
6. **Snapshot is composite and declares uncaptured dependencies.**
7. **Trace never requires private chain-of-thought.**
8. **High-confidence RCA requires replay evidence.**
9. **Protocol + SDK + conformance are open-source first.**
10. **Commercial moat is execution + reliability/failure data, not proprietary syntax.**

---

# 49. Reference Anchors

- MCP: https://modelcontextprotocol.io/specification/
- A2A: https://a2a-protocol.org/latest/
- OpenTelemetry: https://opentelemetry.io/docs/specs/semconv/
- OpenTelemetry GenAI: https://github.com/open-telemetry/semantic-conventions-genai
- CUBE: https://arxiv.org/abs/2603.15798
- Gymnasium: https://gymnasium.farama.org/api/env/
- Playwright Browser Contexts: https://playwright.dev/docs/browser-contexts
- Kubernetes Volume Snapshots: https://kubernetes.io/docs/concepts/storage/volume-snapshots/
- Firecracker Snapshotting: https://github.com/firecracker-microvm/firecracker/blob/main/docs/snapshotting/snapshot-support.md

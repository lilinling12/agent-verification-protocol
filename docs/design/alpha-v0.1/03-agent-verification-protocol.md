# 03 Agent Verification Protocol (AVP)

> Status: **Draft Standard v0.1.0**  
> Date: 2026-08-11  
> Intended track: independent open-source specification  
> Normative language: `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY` follow RFC 2119 / RFC 8174 when capitalized.

## 0. Abstract

**Agent Verification Protocol (AVP)** defines a vendor-neutral contract for executing, observing, verifying, replaying, and comparing AI agents in reproducible environments.

AVP does **not** define how an LLM is called, how an Agent internally reasons, how an Agent communicates with another Agent, how tools are described/invoked, or how generic telemetry is transported. Those concerns are already addressed by adjacent ecosystems such as MCP, A2A and OpenTelemetry.

AVP defines the missing verification layer:

```text
Scenario
  ↓
Environment Materialization
  ↓
Episode
  ↓
Observable Agent Interaction
  ↓
World State Transition
  ↓
Verification Evidence
  ↓
Verdict / Validity
  ↓
Snapshot / Replay / Counterfactual
```

The central design rule is:

> **The Agent Plane and the Evaluator Plane MUST be separated.**

The subject Agent MUST NOT receive privileged evaluator state, hidden oracle data, benchmark secrets, contamination canaries, or release-policy internals unless a Scenario explicitly defines them as Agent-visible data.

---

# 1. Motivation

Existing standards solve adjacent problems:

```text
MCP:
Agent / Host ↔ Tools, Resources, Prompts

A2A:
Agent ↔ Agent

OpenTelemetry:
System → Telemetry

Gym-style APIs:
Policy ↔ Environment loop

AVP:
Verification Orchestrator ↔ Reproducible Environment ↔ Evidence / Verdict
```

The AVP problem is not “Can an Agent call a tool?” but:

> **Can an independent evaluator prove what state changed, whether that change was authorized and correct, whether the run itself was valid, and whether the result can be reproduced?**

AVP therefore treats **environment state, evidence provenance, evaluation validity and replayability** as first-class protocol objects.

---

# 2. Design Goals

AVP SHALL optimize for:

1. **Framework neutrality** — test agents implemented with any framework/language through adapters.
2. **Transport neutrality** — semantics MUST NOT depend on a single RPC transport.
3. **Plane separation** — subject Agent and evaluator use distinct capabilities/credentials.
4. **Evidence-first verdicts** — verification results SHOULD reference machine-resolvable evidence.
5. **State-first verification** — authoritative state SHOULD outrank semantic judging when available.
6. **Multiple valid trajectories** — no single canonical path unless the path itself is the capability under test.
7. **Reproducibility** — exact identities and replay fidelity MUST be declared.
8. **Evaluation integrity** — invalid Eval MUST be separate from Agent failure.
9. **Long-horizon support** — Episodes MAY pause/resume and last hours or days.
10. **Composability** — complement MCP, A2A, OTel, OCI, JSON Schema and standard auth.

---

# 3. Non-Goals

AVP does not standardize:

- private chain-of-thought;
- model provider APIs;
- prompt management;
- Agent construction frameworks;
- a universal reward function;
- a universal single Agent score;
- training/RL;
- business-specific policy;
- benchmark ranking UI.

**AVP MUST NOT require hidden chain-of-thought collection.**

It MAY record explicit plans, explanations, action rationales or public intermediate artifacts intentionally emitted by the Agent, but conformance MUST NOT depend on private reasoning disclosure.

---

# 4. Core Terms

## AgentSystem

Complete subject under evaluation:

```text
Model
+ Instructions
+ Harness
+ Context Strategy
+ Memory
+ Retrieval
+ Tools
+ MCP Topology
+ Policies
+ Retry Logic
+ Permissions
```

## ScenarioTemplate

Parameterized program describing a family of tasks.

## ScenarioInstance

Immutable materialized template with generators, parameters, refs and seeds resolved.

## Environment

Stateful world in which actors execute.

## Actor

Entity capable of observing/acting: subject agent, user simulator, human, adversary, cooperating agent, system process.

## Episode

One bounded execution of one ScenarioInstance against one AgentSystem version in one materialized Environment.

## Experiment

Collection of Episodes organized to answer a comparative/reliability question.

## State

Authoritative or derived representation of Environment at a logical time.

## Observation

Information available to a specific Actor. Observation is not synonymous with State.

## Evidence

Immutable/content-addressed data supporting a verification claim.

## Oracle

Deterministic or bounded-nondeterministic evaluator operating from trusted evidence.

## Judge

Semantic evaluator, usually model-based or human.

## Snapshot

Restorable checkpoint representing Environment state plus required dependency identity.

## Replay

New Episode derived from a prior Episode/checkpoint.

## Counterfactual Replay

Replay with a declared controlled intervention.

## Evaluation Validity

Whether the Episode can produce a trustworthy conclusion about the Agent.

---

# 5. Four Logical Planes

```text
┌───────────────────────────────────────────────┐
│                Control Plane                  │
│ episode lifecycle / snapshot / replay / fault │
└───────────────────────────────────────────────┘
                         │
         ┌───────────────┴─────────────────┐
         ▼                                 ▼
┌────────────────────┐            ┌─────────────────────┐
│    Agent Plane     │            │   Evaluator Plane   │
│ MCP / A2A / HTTP   │            │ hidden state/oracle │
│ Browser / GUI      │            │ privileged evidence │
└────────────────────┘            └─────────────────────┘
         │                                 │
         └───────────────┬─────────────────┘
                         ▼
               ┌─────────────────┐
               │ Telemetry Plane │
               │ OTel + AVP refs │
               └─────────────────┘
```

## Agent Plane

Exposes only Scenario-permitted capabilities using MCP/A2A/HTTP/browser/shell/custom adapters.

## Evaluator Plane

Privileged operations: authoritative state, hidden policy, oracles, benchmark secrets, contamination inspection and private fixtures.

Evaluator credentials MUST NOT be available to the subject Agent.

## Control Plane

Owns lifecycle, snapshot/restore, fault injection, replay and verify.

## Telemetry Plane

SHOULD use OpenTelemetry. AVP adds verification-specific semantics and references, not a competing tracing system.

---

# 6. Conformance Profiles

Incremental adoption is required.

### `AVP-Core`
- capability discovery;
- ScenarioInstance identity;
- Episode lifecycle;
- immutable run manifest;
- event/evidence references;
- explicit validity.

### `AVP-Environment`
- reset;
- observation isolation;
- state digest;
- state diff.

### `AVP-Snapshot`
- snapshot;
- restore;
- compatibility declaration.

### `AVP-Verification`
- oracle execution;
- verification result;
- evidence contract;
- evaluator isolation.

### `AVP-Replay`
- replay;
- intervention manifest;
- replay equivalence report.

### `AVP-Chaos`
- fault catalog/schedule;
- activation lifecycle;
- rollback semantics.

### `AVP-Telemetry`
- AVP event schema;
- OTel correlation;
- state-event correlation.

Implementations MUST advertise supported profiles.

---

# 7. Capability Discovery

A compliant endpoint SHALL expose a capability document:

```json
{
  "protocol": "avp",
  "version": "0.1.0",
  "implementation": {
    "name": "example-runtime",
    "version": "2.4.1"
  },
  "profiles": [
    "AVP-Core",
    "AVP-Environment",
    "AVP-Snapshot",
    "AVP-Verification",
    "AVP-Replay"
  ],
  "features": {
    "virtual_clock": true,
    "multi_actor": true,
    "fault_injection": ["http", "mcp", "network", "permission"],
    "snapshot_modes": ["logical", "volume", "microvm"],
    "telemetry": ["opentelemetry", "avp-events"]
  }
}
```

Capabilities MUST be versioned and SHOULD be content-addressable.

---

# 8. Identity and Immutability

Every reproducible Episode SHALL bind immutable identities:

```text
scenario_instance_digest
agent_system_digest
environment_manifest_digest
oracle_bundle_digest
policy_bundle_digest
seed_bundle_digest
protocol_version
runtime_implementation_version
```

Where possible, use SHA-256 over canonical serialized content.

Mutable aliases such as:

```text
model = latest
prompt = production
toolset = current
policy = default
```

SHOULD resolve before execution. Episode manifests MUST record both `requested_ref` and `resolved_ref`.

---

# 9. Episode Lifecycle

```text
CREATED
  ↓
PROVISIONING
  ↓
READY
  ↓
RUNNING
  ├──→ PAUSED ──→ RUNNING
  ↓
QUIESCING
  ↓
VERIFYING
  ↓
COMPLETED
```

Terminal alternatives:

```text
ABORTED
INVALID
INFRA_FAILED
```

`COMPLETED` does not imply success:

```json
{
  "episode_state": "COMPLETED",
  "task_verdict": "FAIL",
  "evaluation_validity": "VALID"
}
```

Termination reasons MUST distinguish:

```text
goal_reported
agent_stop
user_stop
max_steps
max_wall_time
max_virtual_time
budget_exhausted
policy_block
safety_block
environment_terminal
infra_failure
orchestrator_abort
```

---

# 10. Episode Creation

```json
{
  "scenario_instance": {
    "uri": "avp://scenario/commerce/refund/instance/019..."
  },
  "agent": {
    "adapter": "http",
    "ref": "agent://refund-agent/v42"
  },
  "seed_bundle": {
    "scenario": "s-991",
    "environment": "e-221",
    "user": "u-119",
    "fault": "f-810",
    "agent_sampling": "a-177"
  },
  "execution": {
    "max_steps": 60,
    "wall_timeout_ms": 600000
  }
}
```

Episode creation MUST be idempotent when an `Idempotency-Key` is provided.

---

# 11. Reset Semantics

`reset` MUST establish a known initial state and return:

```json
{
  "episode_id": "ep_...",
  "snapshot_base": "snap_...",
  "state_digest": "sha256:...",
  "observation_refs": {
    "subject-agent": "artifact://..."
  },
  "validity_preflight": {
    "status": "VALID"
  }
}
```

Reset levels:

```text
logical    — fixtures/transactions
service    — DB/files/service snapshots
runtime    — VM/microVM/runtime checkpoint
composite  — coordinated mixed reset
```

The protocol standardizes semantics/evidence, not implementation technology.

---

# 12. Observation Isolation

`observe(actor_id)` MUST return only Actor-authorized information.

It MUST NOT expose:

- oracle expected values;
- hidden DB rows;
- future fault schedule;
- evaluator labels;
- contamination canaries;
- benchmark secrets.

---

# 13. Agent Actions

AVP does not require tools to be invoked through AVP. Actions may occur via MCP, A2A, HTTP, browser, shell or custom interfaces.

A conformant runtime SHOULD emit normalized action metadata:

```text
actor
action class
target
argument reference
authorization witness
result reference
state before/after when material
```

For irreversible/high-risk operations, implementations SHOULD support a **commit boundary event**.

---

# 14. State Model

AVP distinguishes:

```text
Physical State
Logical State
Visible State
Privileged State
Derived State
```

A runtime SHOULD expose scoped content-addressed state projections rather than requiring full-state serialization.

State diff example:

```json
{
  "from": "sha256:...",
  "to": "sha256:...",
  "changes": [
    {
      "entity": "refund:rf_123",
      "operation": "create",
      "fields": {
        "status": {"after": "completed"}
      }
    }
  ]
}
```

---

# 15. Snapshot Contract

Snapshot is first-class:

```json
{
  "snapshot_id": "snap_...",
  "mode": "composite",
  "logical_time": 17,
  "environment_digest": "sha256:...",
  "components": [
    {
      "kind": "database",
      "ref": "artifact://snap/db",
      "digest": "sha256:..."
    },
    {
      "kind": "browser-storage",
      "ref": "artifact://snap/browser",
      "digest": "sha256:..."
    }
  ],
  "consistency": "application-consistent",
  "compatibility": {
    "runtime": "example-runtime@2.x",
    "host_constraints": ["x86_64"]
  }
}
```

Snapshot consistency values:

```text
application-consistent
crash-consistent
best-effort
```

Uncaptured external dependencies MUST be declared.

---

# 16. Restore and Replay Equivalence

Restore SHALL report:

```json
{
  "restored": true,
  "state_digest": "sha256:...",
  "equivalence": {
    "level": "EXACT",
    "differences": []
  }
}
```

Levels:

```text
EXACT
STATE_EQUIVALENT
SEMANTICALLY_EQUIVALENT
BEST_EFFORT
NON_EQUIVALENT
```

Exact replay MUST NOT be claimed when material external state is uncontrolled.

---

# 17. Fault Injection

Generic fault envelope:

```yaml
id: fault-payment-timeout
type: transport.timeout
target:
  kind: tool
  name: payment.authorize
activation:
  after:
    event_type: tool.call
    occurrence: 1
duration:
  calls: 1
parameters:
  timeout_ms: 30000
rollback:
  mode: automatic
```

Required lifecycle events:

```text
fault.scheduled
fault.activated
fault.observed
fault.cleared
```

Fault visibility MUST be declared:

```text
hidden
observable
announced
```

---

# 18. Verification Contract

Verification is claim-based.

Each result MUST identify:

```text
claim
dimension
method
verdict
severity
evidence
evaluator version
confidence if probabilistic
```

Example:

```json
{
  "verification_id": "ver_...",
  "claim": "target refund completed",
  "dimension": "state.postcondition",
  "method": {
    "type": "state_oracle",
    "version": "refund-oracle@7"
  },
  "verdict": "PASS",
  "severity": "critical",
  "evidence": [
    "evidence://state/refund-rf123"
  ]
}
```

Method classes:

```text
state_oracle
executable_test
temporal_rule
policy_rule
schema_validator
semantic_judge
agentic_judge
human_adjudication
```

Deterministic critical failures MUST be able to veto semantic scores.

---

# 19. Verdict Model

Orthogonal verdicts:

## Task

```text
PASS
PARTIAL
FAIL
INCONCLUSIVE
```

## Evaluation Validity

```text
VALID
INVALID_TASK
INVALID_INITIAL_STATE
ENVIRONMENT_FAILURE
RESET_FAILURE
ORACLE_FAILURE
TRACE_INCOMPLETE
INFRA_CONFOUND
CONTAMINATED
UNKNOWN
```

## Safety

```text
PASS
FAIL
REVIEW
NOT_APPLICABLE
```

Platforms MAY compute aggregate scores but MUST preserve raw verdict dimensions.

---

# 20. Evidence Contract

Evidence SHOULD be immutable/content-addressed:

```json
{
  "evidence_id": "ev_...",
  "type": "state_projection",
  "uri": "artifact://...",
  "digest": "sha256:...",
  "created_by": "oracle:refund-state@7",
  "classification": "evaluator-confidential",
  "redaction": {
    "policy": "pii-v2"
  }
}
```

Suggested classifications:

```text
public
workspace
subject-visible
evaluator-confidential
secret
regulated
```

---

# 21. Evaluation Integrity

Preflight SHOULD verify:

- environment healthy;
- initial assertions;
- required tools;
- oracle executable;
- hidden data inaccessible to Agent Plane;
- seed materialization;
- snapshot restorable when required.

Postflight SHOULD verify:

- required telemetry complete;
- evaluator ran;
- state readable;
- contamination checks;
- infra anomalies.

If answer material reaches Agent-visible channels, validity SHOULD become `CONTAMINATED`.

---

# 22. Counterfactual Replay

Replay references a parent Episode:

```json
{
  "parent_episode_id": "ep_...",
  "checkpoint": "snap_step_16",
  "mode": "counterfactual",
  "interventions": [
    {
      "component": "tool_schema",
      "target": "refund.create.order_id",
      "change_ref": "artifact://intervention/schema-v2"
    }
  ],
  "hold_constant": [
    "scenario_instance",
    "environment_seed",
    "user_seed",
    "fault_seed"
  ]
}
```

Intervention classes:

```text
model
instructions
harness
memory
retrieval
tool_schema
tool_topology
policy
permission
context
fault
environment_data
user_behavior
```

Replay MUST report what could actually be held constant.

---

# 23. Multi-Agent and Human Support

Agents are Actors. Multi-agent communication SHOULD use A2A where applicable.

AVP verifies:

- delegation correctness;
- handoff boundaries;
- authority propagation;
- shared-state consistency;
- duplicate work;
- cyclic delegation.

Human events SHOULD distinguish:

```text
human.message
human.approval
human.rejection
human.override
human.annotation
human.adjudication
```

Approval used for durable effect SHOULD be referenceable as evidence.

---

# 24. Security Model

Possible malicious/compromised components include:

- subject Agent;
- MCP/tool server;
- webpage/file;
- user simulator;
- semantic Judge;
- benchmark artifact;
- runtime dependency.

Evaluator credentials MUST:

- use separate identity;
- be inaccessible to Agent processes;
- not be present in Agent env vars;
- not be reachable via Agent network path except explicit mediation.

Untrusted trace content MUST be treated as data, not Judge instructions.

Semantic judges SHOULD be read-only by default with restricted egress/tool access.

---

# 25. Privacy

AVP MUST permit data-handling modes:

```text
store_full
store_redacted
store_hash_only
store_reference_only
drop
```

Verification SHOULD work with evidence references when raw data cannot be centrally stored.

---

# 26. HTTP/JSON Reference Binding

Suggested endpoints:

```text
GET  /.well-known/avp
POST /v1/episodes
GET  /v1/episodes/{id}
POST /v1/episodes/{id}:start
POST /v1/episodes/{id}:pause
POST /v1/episodes/{id}:resume
POST /v1/episodes/{id}:terminate
POST /v1/episodes/{id}/snapshots
POST /v1/episodes/{id}:restore
POST /v1/episodes/{id}/faults
POST /v1/episodes/{id}:verify
POST /v1/episodes/{id}:replay
GET  /v1/episodes/{id}/events
GET  /v1/episodes/{id}/evidence
```

URI shapes are binding concerns; semantic operation names are normative.

---

# 27. Auth and Permissions

Production Control/Evaluator endpoints MUST use authenticated encrypted transport.

Recommended mechanisms:

- OAuth/OIDC;
- mTLS;
- workload identity.

Capability-style permissions:

```text
episode:create
episode:control
environment:observe
environment:privileged-read
snapshot:create
snapshot:restore
fault:inject
verification:run
evidence:read
replay:create
```

Subject Agent MUST NOT receive `environment:privileged-read`.

---

# 28. Versioning and Extensions

AVP uses semantic versions.

```text
PATCH — compatible corrections
MINOR — backward-compatible additions
MAJOR — breaking semantic change
```

Schema resources include `apiVersion` and `kind`.

Extensions MUST be namespaced:

```yaml
extensions:
  com.example.finance:
    settlement_window: T+1
```

Extensions MUST NOT redefine core semantics.

---

# 29. Package Model

A package MAY contain:

```text
avp.yaml
scenarios/
schemas/
oracles/
fixtures/
policies/
mutations/
adapters/
LICENSE
NOTICE
```

Manifest SHOULD record:

```text
name
version
license
authors
digests
supported_avp_versions
runtime_requirements
```

OCI-compatible artifact distribution is RECOMMENDED for runtime-heavy packages.

---

# 30. Conformance Testing

A standard is incomplete without conformance tests.

Required suites should cover:

### Core
- lifecycle state transitions;
- idempotency;
- invalid transition rejection;
- version negotiation.

### Isolation
Try to obtain hidden oracle state, canary, evaluator token or future fault schedule from Agent Plane. Expected: impossible.

### Snapshot
snapshot → mutate → restore → digest/equivalence.

### Evidence
Every critical verdict resolves to valid evidence.

### Replay
Replay declares correct equivalence.

### Invalid Eval
Broken oracle/environment produces `INVALID_*`, not Agent `FAIL`.

---

# 31. Standardization Roadmap

## Stage 0 — Internal Draft
Spec, schemas, reference runtime, conformance.

## Stage 1 — Open Source

```text
agent-verification-protocol/spec
agent-verification-protocol/schemas
agent-verification-protocol/conformance
agent-verification-protocol/sdk-python
agent-verification-protocol/sdk-typescript
agent-verification-protocol/sdk-java
agent-verification-protocol/sdk-go
```

## Stage 2 — Ecosystem adapters
MCP, A2A, OTel, LangGraph, major Agent SDKs, browser runtime, CUBE adapter.

## Stage 3 — Multi-vendor governance
Public technical steering process.

## Stage 4 — External standardization
Only after real multi-vendor adoption.

Premature formal standards-body work SHOULD be avoided.

---

# 32. Relationship to CUBE

CUBE is an important adjacent proposal for benchmark environment unification using MCP + Gym-like semantics.

AVP SHOULD interoperate:

```text
CUBE task/package/registry
      ↓ adapter
AVP Scenario/Package/Registry

CUBE reset/step/evaluate
      ↓ adapter
AVP Environment + Verification
```

AVP adds deployment-verification semantics:

- strict Agent/Evaluator plane separation;
- state/evidence identity;
- snapshot compatibility;
- fault injection;
- Eval validity;
- contamination;
- replay/counterfactual;
- release-grade verdicts.

If CUBE evolves equivalent semantics, AVP SHOULD seek convergence rather than fragmentation.

---

# 33. Relationship to OpenTelemetry

AVP MUST NOT invent a competing trace context.

Use OTel/W3C IDs where possible:

```text
trace_id
span_id
```

OpenTelemetry GenAI conventions already cover `invoke_agent`, `execute_tool`, `plan`, retrieval and memory operations.

AVP adds:

```text
environment state transitions
fault lifecycle
verification evidence
oracle verdict
evaluation validity
replay intervention
```

---

# 34. Relationship to MCP and A2A

MCP remains preferred for Agent↔Tool interaction. AVP does not add another tool-call protocol.

A2A remains appropriate for opaque Agent↔Agent collaboration.

Recommended architecture:

```text
Agent-visible interaction → MCP/A2A/API/Browser
Privileged verification   → separate AVP Evaluator Plane
```

---

# 35. Normative Core Summary

A conformant AVP system:

1. **MUST** identify exact Scenario, AgentSystem and Environment.
2. **MUST** separate Agent-visible and evaluator-privileged data.
3. **MUST** distinguish Agent failure from invalid Eval.
4. **MUST** preserve evidence references for critical verdicts.
5. **MUST NOT** require private chain-of-thought.
6. **SHOULD** use authoritative State when available.
7. **SHOULD** use OpenTelemetry for general tracing.
8. **SHOULD** use MCP/A2A instead of redefining tool/agent communication.
9. **SHOULD** use content-addressed manifests/artifacts.
10. **MUST** declare replay equivalence.
11. **MUST** version evaluators/oracles.
12. **SHOULD** make conformance independently testable.

---

# 36. Reference Anchors

- MCP: https://modelcontextprotocol.io/specification/
- A2A: https://a2a-protocol.org/latest/
- OpenTelemetry: https://opentelemetry.io/docs/specs/semconv/
- OpenTelemetry GenAI: https://github.com/open-telemetry/semantic-conventions-genai
- Gymnasium: https://gymnasium.farama.org/api/env/
- CUBE: https://arxiv.org/abs/2603.15798
- JSON Schema 2020-12: https://json-schema.org/draft/2020-12
- CloudEvents: https://cloudevents.io/

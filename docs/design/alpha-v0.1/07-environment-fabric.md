# 07 Environment Fabric Specification

> Status: Architecture / Protocol Draft v0.1  
> Parent: AVP v0.1  
> Scope: reproducible execution environments, state, isolation, fault injection and replay fidelity.

## 1. Purpose

Environment Fabric is the execution substrate that turns Agent evaluation from “output grading” into **stateful verification**.

Its responsibility is to make the following statement testable:

> Given a declared Scenario, AgentSystem, runtime manifest and seed bundle, the platform can establish a known world, expose only authorized observations/actions to the subject Agent, record authoritative state changes, inject controlled perturbations, and reproduce a prior checkpoint with an explicitly declared fidelity.

Environment Fabric is intentionally broader than a sandbox and narrower than a cloud platform.

It standardizes **verification semantics**, not a single virtualization technology.

---

# 2. Core Invariants

A conformant Environment implementation MUST preserve these invariants.

## E1 — Known Initial State

Before subject execution begins, all Scenario-critical initial assertions MUST be evaluated.

If they fail, the Episode is invalid.

## E2 — Visibility Separation

Agent-visible State and evaluator-privileged State MUST be logically and operationally separable.

## E3 — Authoritative State

For state-changing tasks, there MUST be at least one authoritative state source or an explicit declaration that authoritative state is unavailable.

## E4 — Reset Integrity

A successful reset MUST produce a state matching the declared initial-state equivalence class.

## E5 — Fault Accountability

Every injected fault MUST have a schedule, activation event and provenance.

## E6 — Replay Honesty

An implementation MUST NOT label a replay `EXACT` unless all Scenario-material state and dependency dimensions were restored or deterministically replayed.

## E7 — Infrastructure Manifest

Resource and runtime configuration are first-class experimental variables and MUST be recorded.

---

# 3. Environment Descriptor

```yaml
apiVersion: avp.spec/v0.1
kind: EnvironmentManifest

metadata:
  name: commerce-lab
  version: 4.2.0

runtime:
  profile: composite

components:
  - id: db
    kind: database
    engine: postgresql
    version: "18"
    fixture: fixture://commerce/v12

  - id: tools
    kind: mcp
    server: mcp://orders@3.1

  - id: browser
    kind: browser
    engine: chromium
    version: "..."
```

The immutable resolved descriptor is included in every Episode manifest.

---

# 4. Runtime Profiles

AVP defines semantic tiers, not required products.

## L0 — Logical Runtime

Target:

- API agents;
- database workflows;
- MCP agents;
- service agents.

Reset mechanisms:

- transaction rollback;
- fixture reload;
- event-store reset;
- namespace recreation.

Expected strengths:

- low startup latency;
- high throughput;
- deterministic state.

## L1 — Container / Service Runtime

Target:

- multi-service integration;
- backend applications;
- service meshes.

Reset mechanisms:

- container recreate;
- database snapshot;
- volume snapshot;
- object namespace reset.

## L2 — Browser Runtime

Target:

- browser/navigation agents;
- form automation;
- support/commerce web agents.

Required distinction:

```text
Browser-local state
≠
Application authoritative state
```

A browser runtime SHOULD correlate browser artifacts with backend State whenever state-changing verification matters.

## L3 — microVM Runtime

Target:

- coding agents;
- shell agents;
- Linux computer use;
- untrusted arbitrary code.

Properties:

- stronger isolation;
- checkpoint/restore;
- filesystem/process visibility.

## L4 — Full VM / Device Lab

Target:

- Windows/macOS desktop;
- native enterprise apps;
- device-specific workflows.

---

# 5. Resource Manifest

Every Episode MUST record resource methodology.

```yaml
resources:
  cpu:
    request: "4"
    limit: "8"
  memory:
    request: 8Gi
    limit: 24Gi
  disk:
    ephemeral: 40Gi
  gpu: null
  network:
    egress_mbps: 100
  concurrency_class: isolated
```

The distinction between guaranteed allocation and hard ceiling is normative.

The runtime SHOULD separately record:

```text
requested resources
reserved resources
hard limits
observed peak
throttling
OOM
preemption
node class
region
```

An infrastructure-induced failure MUST NOT silently become an Agent task failure.

---

# 6. Environment Health

Before an Episode starts:

```text
environment.health.preflight
```

checks MAY include:

- required process alive;
- database reachable;
- schema version correct;
- MCP capability list available;
- browser app healthy;
- fixture digest correct;
- evaluator path available;
- subject cannot reach evaluator secrets.

Health failure produces:

```text
ENVIRONMENT_FAILURE
```

or a more specific validity status.

---

# 7. State Adapter Interface

A state adapter is the bridge between raw runtime state and verification State.

Logical interface:

```text
describe()
project(projection_id)
digest(projection_id)
diff(from, to, projection_id)
assert(assertion)
snapshot()
restore(snapshot_ref)
```

Adapters SHOULD expose semantic entities rather than raw implementation-only details.

Example projection:

```json
{
  "projection": "commerce.refunds",
  "entities": [
    {
      "id": "refund:rf_991",
      "order_id": "order:123",
      "status": "completed",
      "amount": 88.00
    }
  ]
}
```

---

# 8. Projection Contracts

Each projection MUST define:

```text
projection_id
schema_version
visibility
source
freshness model
canonicalization method
digest method
```

Visibility:

```text
subject-visible
shared
evaluator-only
```

A semantic Judge SHOULD receive the narrowest projection needed for its rubric.

---

# 9. State Digest

Digest semantics MUST be deterministic for the same canonical projection.

Recommended:

```text
canonical JSON
→ SHA-256
```

For large worlds, Merkle roots MAY be used.

Digest equality means:

> equality under the projection's declared canonical semantics,

not necessarily byte-for-byte identity of the entire runtime.

---

# 10. State Diff

State Diff SHOULD include causal links:

```json
{
  "from": "sha256:S17",
  "to": "sha256:S18",
  "cause_event_id": "evt_tool_55",
  "changes": [
    {
      "entity": "order:123",
      "operation": "update",
      "fields": {
        "status": {
          "before": "PAID",
          "after": "REFUNDED"
        }
      }
    }
  ]
}
```

Diffs SHOULD distinguish:

```text
intended effect
collateral effect
system-maintenance effect
unknown effect
```

when domain adapters can classify them.

---

# 11. Commit Boundary

For high-risk actions, a runtime SHOULD emit `environment.commit`.

The commit boundary represents the point after which an effect is considered durable or externally observable.

Examples:

- funds transferred;
- record deleted;
- email sent;
- deployment activated;
- order refunded;
- permission revoked.

Commit event SHOULD contain:

```text
effect_id
effect_type
irreversibility
authority witness
state before
state after
```

---

# 12. Authority Witness

A State transition may require a witness:

```text
human approval
identity verification
policy decision
capability token
fresh object version
transaction authorization
```

Witnesses MUST be bound to scope and freshness.

```yaml
authority:
  witness_id: auth-77
  scope: refund:order-123
  issued_at: ...
  expires_at: ...
  binding_digest: sha256:...
```

This enables verification of stale authorization.

---

# 13. Reset

Reset has three phases:

```text
prepare
apply
verify
```

## Prepare

- stop/quiet workloads if required;
- detach external side effects;
- select fixture/snapshot.

## Apply

- restore components;
- reset clock;
- reset fault scheduler;
- reset actor simulators.

## Verify

- recompute initial State;
- run initial assertions;
- compare expected digest/equivalence;
- verify subject/evaluator isolation.

Only then is the Environment `READY`.

---

# 14. Reset Equivalence

A reset result declares:

```text
EXACT
STATE_EQUIVALENT
SEMANTICALLY_EQUIVALENT
NON_EQUIVALENT
```

A Scenario can define minimum acceptable reset equivalence.

Example:

```yaml
reset:
  minimum_equivalence: STATE_EQUIVALENT
```

---

# 15. Composite Snapshot Manifest

A snapshot is not a single VM file.

```yaml
snapshot:
  id: snap-88
  consistency: application-consistent
  logical_time: 42

  components:
    - kind: database
      ref: artifact://snap/db
      digest: sha256:...

    - kind: filesystem
      ref: artifact://snap/fs
      digest: sha256:...

    - kind: browser-storage
      ref: artifact://snap/browser
      digest: sha256:...

    - kind: runtime
      ref: artifact://snap/vm
      digest: sha256:...

    - kind: virtual-clock
      value: "2026-08-11T10:20:00+08:00"

  uncaptured:
    - kind: third-party-api
      name: external-shipping
```

---

# 16. Snapshot Consistency

Allowed core values:

```text
application-consistent
crash-consistent
best-effort
```

For composite snapshots, the implementation MUST explain whether components are mutually consistent.

Future versions MAY define distributed snapshot barriers.

---

# 17. External Dependency Control

External dependencies are classified:

```text
captured
simulated
record_replay
pinned
live_uncontrolled
```

A replay fidelity engine considers each dependency.

Example:

```yaml
external:
  maps-api:
    mode: record_replay
    recording_digest: sha256:...

  open-web:
    mode: live_uncontrolled
```

Open-web Tasks normally cannot claim exact replay.

---

# 18. Virtual Clock

Environment MAY offer a virtual clock.

Required semantics:

```text
now
freeze
advance
schedule
timezone
```

Clock mutations must be visible as Environment events.

Time-sensitive applications SHOULD accept injectable time providers in verification environments.

---

# 19. Network Control

Network policy supports:

```text
deny-by-default
allowlist
record
replay
shape
fault
```

The subject's network and evaluator's network MUST be independently configurable.

---

# 20. Fault Model

Core fault namespaces:

```text
transport.*
http.*
network.*
state.*
tool.*
mcp.*
permission.*
time.*
resource.*
browser.*
process.*
data.*
security.*
```

Fault definition:

```yaml
type: state.stale_projection
target: tool://order.get
activation:
  after:
    event: tool.call
    occurrence: 1
parameters:
  versions_behind: 1
visibility: hidden
recovery:
  automatic_after_calls: 1
```

---

# 21. Fault Determinism

Fault plans MUST bind:

```text
fault definition version
fault seed
activation condition
target identity
```

If activation is race-dependent, the Episode MUST record actual activation timing and may have lower replay fidelity.

---

# 22. Browser Environment

Reference capabilities:

```text
isolated context
DOM snapshot
accessibility snapshot
screenshot
storage state
cookies
downloads/uploads
network events
browser console
navigation history
```

The runtime MUST NOT assume DOM-only access; vision-only and hybrid Agents must be representable.

---

# 23. MCP Environment

MCP-facing layer SHOULD honor current MCP semantics rather than reimplement tool RPC.

AVP-specific gateway functions:

- identity/version capture;
- schema fingerprint;
- list cache metadata capture;
- fault injection;
- result mutation;
- permission enforcement;
- telemetry correlation.

The new stateless MCP core makes tool gateways easier to horizontally scale; AVP should exploit this without depending on a particular MCP deployment topology.

---

# 24. Multi-Agent Environment

Shared worlds require attribution.

Every mutation MUST identify its causal Actor when possible.

A shared Environment SHOULD support:

```text
actor-scoped observations
actor-scoped permissions
shared State
private State
handoff artifacts
delegation authority
```

---

# 25. User Simulator

User simulator is an Actor, not an Oracle.

It has:

```text
persona
hidden user state
behavior policy
seed
visibility rules
```

The evaluator MAY access hidden user state; subject Agents MUST NOT unless surfaced through interaction.

User simulator stochasticity must use a dedicated seed.

---

# 26. Environment Determinism Score

Instead of pretending an Environment is deterministic, AVP may report:

```text
replay_fidelity = [
  reset_equivalence,
  captured_dependency_fraction,
  nondeterministic_source_count,
  observed_state_match_rate
]
```

This is descriptive, not a universal scalar score.

---

# 27. Replay Preflight

Before replay:

- snapshot compatible?
- runtime version compatible?
- image digest available?
- external recordings available?
- model/provider semantics pinned?
- browser/runtime architecture compatible?

If materially incompatible, replay may continue as `BEST_EFFORT`, but not as exact.

---

# 28. Isolation Conformance

Conformance MUST actively attempt:

- evaluator endpoint discovery;
- environment-variable secret reading;
- metadata service access;
- hidden fixture access;
- oracle artifact guessing;
- future fault-schedule access.

The expected result is denial or absence.

---

# 29. Environment Failure Taxonomy

```text
PROVISION_FAILURE
RESET_FAILURE
HEALTH_FAILURE
SNAPSHOT_FAILURE
RESTORE_FAILURE
STATE_ADAPTER_FAILURE
TRACE_FAILURE
FAULT_ENGINE_FAILURE
RESOURCE_FAILURE
EXTERNAL_DEPENDENCY_FAILURE
ISOLATION_FAILURE
```

These belong to Eval validity, not subject Agent quality.

---

# 30. Environment KPIs

Platform-quality metrics:

```text
valid_episode_rate
reset_success_rate
snapshot_success_rate
restore_success_rate
state_projection_success
exact_replay_rate
state_equivalent_replay_rate
infra_failure_rate
trace_loss_rate
isolation_failure_rate
runtime_provision_p50/p95
```

---

# 31. Conformance Requirements

`AVP-Environment` implementations MUST:

1. establish and verify known initial state;
2. expose subject observations with visibility enforcement;
3. provide runtime/resource manifest;
4. distinguish infrastructure failure;
5. provide at least one state digest mechanism.

`AVP-Snapshot` additionally MUST:

1. create versioned snapshot manifests;
2. declare uncaptured dependencies;
3. restore and verify equivalence;
4. expose snapshot consistency.

`AVP-Chaos` additionally MUST:

1. expose versioned fault definitions;
2. emit activation lifecycle;
3. record actual applied fault;
4. separate fault-engine failure from Agent failure.

---

# 32. Reference Anchors

- Model Context Protocol current specification and authorization model.
- OpenTelemetry distributed tracing / GenAI semantic conventions.
- Playwright isolated browser contexts and storage state.
- Kubernetes CSI snapshot primitives.
- Firecracker snapshot/restore model.
- Anthropic 2026 infrastructure-noise findings for agentic evals.

The standard intentionally sits above these implementations.

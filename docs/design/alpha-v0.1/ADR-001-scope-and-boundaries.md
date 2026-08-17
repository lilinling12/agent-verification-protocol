# ADR-001 — AVP Scope, Naming and Standards Boundary

## Status
Accepted for v0.1 draft.

## Decision

Proposed standard name:

> **Agent Verification Protocol (AVP)**

Scenario language:

> **Agent Verification Scenario DSL (AVS)**

AVP owns:

```text
Scenario identity
Episode lifecycle
Environment verification lifecycle
State/evidence references
Snapshot/restore semantics
Evaluation validity
Fault injection semantics
Replay/counterfactual semantics
Verification verdict contract
```

AVP does not own:

```text
Agent↔Tool protocol        → MCP / existing APIs
Agent↔Agent protocol       → A2A / existing protocols
Distributed trace context → OpenTelemetry / W3C
Generic event transport    → CloudEvents if useful
Schema language            → JSON Schema
Container artifact format  → OCI where useful
```

## Security Decision

Evaluator Plane MUST be isolated from Agent Plane.

The subject must not inherit evaluator credentials or gain an RPC route that leaks oracle state, hidden benchmark data, future faults or answer-key material.

## Consequences

Positive:

- avoids protocol duplication;
- creates a clear verification category;
- makes existing benchmark/Agent ecosystems adaptable;
- reduces reward-hacking and leakage risk;
- permits future upstreaming of mature telemetry semantics to OpenTelemetry.

Negative:

- adapters are required;
- local developer UX must hide multi-plane complexity;
- distributed replay is harder than a monolithic benchmark process.

## CUBE Relationship

CUBE should be treated as a collaborator/adapter target, not automatically as a competitor. If its future standard absorbs equivalent verification semantics, convergence is preferred to fragmentation.

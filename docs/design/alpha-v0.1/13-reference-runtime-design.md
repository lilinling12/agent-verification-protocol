# 13 Reference Runtime Design

> Status: Implementation Baseline v0.1  
> Goal: define the smallest **complete** AVP implementation that proves protocol semantics end-to-end.

## 1. Reference Runtime Is Not the Commercial Platform

The Reference Runtime exists to answer:

> Can AVP be implemented by an independent team without relying on proprietary infrastructure?

It MUST therefore be:

- small enough to understand;
- deterministic by default;
- runnable locally;
- conformant to the public protocol;
- intentionally unoptimized;
- replaceable component-by-component.

It MUST NOT depend on commercial-only services.

---

## 2. First Reference World

The first world is a commerce/refund environment because it exercises:

```text
read tools
ambiguous target
state mutation
confirmation
collateral damage
false success
snapshot
replay
fault injection
```

State:

```text
customers
orders
refunds
permissions
virtual_clock
```

Tools:

```text
order.search
order.get
refund.create
customer.delete
```

Reference subjects:

```text
correct-agent
false-success-agent
wrong-target-agent
no-confirm-agent
loop-agent
```

The deterministic subjects exist for TCK validation, not as model benchmarks.

---

## 3. Process Model

Local mode:

```text
avp CLI
  │
  ▼
Reference Runtime
  ├── Episode Store
  ├── Commerce World
  ├── Event Recorder
  ├── Snapshot Manager
  ├── Oracle Engine
  └── Conformance Runner
```

HTTP mode:

```text
CLI / external verifier
       │
       ▼
AVP HTTP Binding
       │
       ▼
Reference Runtime Core
```

HTTP is an adapter. Core semantics are library-first.

---

## 4. Core Interfaces

```python
class Environment:
    reset()
    observe(actor_id)
    call_tool(actor_id, name, arguments)
    snapshot()
    restore(snapshot_id)
    project(projection_id)
    digest(projection_id)
    diff(before, after)

class Oracle:
    evaluate(claim, evidence) -> VerificationResult

class EpisodeRuntime:
    create()
    start()
    pause()
    resume()
    terminate()
    verify()
    replay()
```

---

## 5. Deterministic State

The reference world uses canonical JSON + SHA-256.

Every material mutation produces:

```text
state_before_digest
state_after_digest
semantic diff
cause event id
```

No Agent statement can directly mutate evaluator-only State.

---

## 6. Snapshot

Reference implementation starts with logical snapshots:

```text
deep copy canonical world
+ virtual clock
+ permission state
+ fault state
```

Snapshot artifact gets a digest.

This satisfies AVP-Snapshot semantics without pretending to be a VM snapshot.

---

## 7. Replay

Reference replay:

```text
restore snapshot
apply declared intervention
execute deterministic subject or external Agent
compare state/verdict
emit equivalence
```

Because the local world is fully captured, reference replay can usually claim:

```text
STATE_EQUIVALENT
```

`EXACT` is reserved for cases where every relevant execution source is deterministic.

---

## 8. Event Recorder

Append-only in memory/local JSONL for reference implementation.

Each event has:

```text
episode_id
sequence
event_type
plane
logical_time
payload
state refs
evidence refs
```

Optional OTel export maps event context to spans/events.

---

## 9. Agent Adapter

Reference runtime supports:

```text
callable adapter
HTTP callback adapter
MCP gateway adapter
```

The subject receives:

```text
task
Agent-visible observation
Agent-visible tools
```

It does not receive:

```text
oracle
hidden state
expected target
future fault schedule
```

---

## 10. Verification

First built-in Oracles:

```text
refund.completed
refund.no_collateral
customer.not_deleted
false_success
```

This is enough to validate the architecture.

---

## 11. Conformance Mode

The Reference Runtime MUST pass:

```text
AVP-Core
AVP-Environment
AVP-Snapshot
AVP-Verification
AVP-Replay
AVP-Telemetry
```

Chaos support can initially be limited to deterministic tool timeout/error injection.

---

## 12. Exit Criteria

Reference Runtime v0.1 is complete when:

1. local demo can show a false-success Agent;
2. State Oracle overrides Agent self-report;
3. snapshot/restore returns equivalent State;
4. replay can apply an intervention manifest;
5. event history links mutations to State digests;
6. TCK can intentionally break an Oracle and get `ORACLE_FAILURE`;
7. Agent Plane cannot read hidden evaluator State;
8. HTTP binding wraps the same core implementation.

---

## 13. Reference Implementation Language

Python is selected for v0.1 because:

- benchmark ecosystem is Python-heavy;
- fastest path to independent adapters;
- good JSON Schema / testing ecosystem;
- easy embedding in research workflows.

This is an implementation choice, not a protocol requirement.

A Java/Go implementation should be able to pass the exact same TCK.

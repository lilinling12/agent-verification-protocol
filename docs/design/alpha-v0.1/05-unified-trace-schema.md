# 05 Unified Trace & Verification Event Schema

> Status: Draft Standard v0.1.0  
> Parent: Agent Verification Protocol (AVP)  
> Principle: **Extend OpenTelemetry; do not replace it.**

## 0. Problem

Agent traces are fragmented across model calls, framework spans, tools, browser events, MCP calls, user messages, environment state changes, policy decisions and evaluator outputs.

A normal observability trace answers:

> what calls happened?

A verification trace must additionally answer:

> **what world state changed, what evidence supports the verdict, when a controlled fault was active, whether authority was valid, and where the first meaningful failure occurred.**

Therefore:

```text
Layer A — OpenTelemetry
distributed causality, spans, timing, GenAI/tool semantics

Layer B — AVP Verification Events
world state, faults, control gates, evidence, validity, replay
```

---

# 1. No Private Chain-of-Thought Requirement

This schema MUST NOT require private chain-of-thought.

It MAY record:

- explicit plans intentionally emitted;
- structured control decisions;
- tool selection;
- observations;
- public intermediate artifacts.

Use:

```text
agent.decision
agent.plan_artifact
agent.control_decision
```

rather than implying hidden internal reasoning.

---

# 2. OpenTelemetry Alignment

Implementations SHOULD preserve:

```text
trace_id
span_id
parent_span_id
```

OpenTelemetry GenAI conventions already model operations including:

```text
invoke_agent
invoke_workflow
execute_tool
plan
retrieval
memory operations
```

AVP events correlate with these spans rather than duplicating them.

---

# 3. AVP Event Envelope

```json
{
  "schema_version": "0.1.0",
  "event_id": "evt_019...",
  "event_type": "environment.state.changed",

  "experiment_id": "exp_...",
  "episode_id": "ep_...",

  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "parent_span_id": null,

  "sequence": 42,
  "logical_time": 21,
  "observed_at": "2026-08-11T10:00:01.123Z",

  "plane": "environment",
  "actor": {
    "id": "subject-agent",
    "type": "agent"
  },

  "payload": {},
  "evidence": [],
  "state": {},
  "security": {},
  "extensions": {}
}
```

---

# 4. Required Envelope Semantics

## `event_id`
Globally unique.

UUIDv7 or equivalent sortable IDs are RECOMMENDED.

## `event_type`
Low-cardinality namespaced event type.

## `episode_id`
Required for Episode-scoped events.

## `sequence`
Monotonic Episode-local sequence assigned by an authoritative recorder.

## `observed_at`
Wall-clock timestamp.

## `logical_time`
Environment logical time/step where available.

---

# 5. Plane

Core values:

```text
orchestrator
agent
environment
evaluator
user
security
external
```

Plane communicates trust boundary.

An Agent-plane claim MUST NOT become authoritative truth without validation.

---

# 6. Actor

```json
{
  "id": "subject-agent",
  "type": "agent",
  "role": "subject"
}
```

Suggested actor types:

```text
agent
human
user_simulator
adversary
service
orchestrator
oracle
judge
environment
```

---

# 7. Payload Indirection

Large/sensitive content SHOULD be stored by reference:

```json
{
  "payload_ref": {
    "uri": "artifact://tool-result/781",
    "digest": "sha256:...",
    "media_type": "application/json"
  }
}
```

This keeps event records small and privacy-aware.

---

# 8. State Correlation

State-changing events SHOULD contain:

```json
{
  "state": {
    "before": "sha256:...",
    "after": "sha256:...",
    "diff_ref": "artifact://state-diff/42"
  }
}
```

This is a core AVP extension beyond normal tracing.

---

# 9. Evidence References

```json
{
  "evidence": [
    {
      "id": "ev_...",
      "uri": "artifact://...",
      "digest": "sha256:...",
      "classification": "evaluator-confidential"
    }
  ]
}
```

Evidence is immutable from the completed Episode perspective.

---

# 10. Core Event Taxonomy

## Episode lifecycle

```text
episode.created
episode.provisioning.started
episode.ready
episode.started
episode.paused
episode.resumed
episode.quiescing
episode.verification.started
episode.completed
episode.aborted
episode.invalidated
```

## Agent

```text
agent.invocation.started
agent.invocation.completed
agent.decision
agent.control_decision
agent.plan_artifact.created
agent.stop
```

## User/Human

```text
user.message
human.message
human.approval
human.rejection
human.override
```

## Tool

Where OTel `execute_tool` spans exist, these may be derived:

```text
tool.discovered
tool.call
tool.result
tool.error
tool.retry
```

## Environment

```text
environment.reset.started
environment.reset.completed
environment.observation
environment.state.changed
environment.commit
environment.snapshot.created
environment.restore.completed
environment.health.changed
```

## Fault

```text
fault.scheduled
fault.activated
fault.observed
fault.cleared
```

## Authority/Policy

```text
policy.evaluated
authority.witness.created
authority.witness.invalidated
authorization.denied
```

## Verification

```text
oracle.started
oracle.completed
verification.claim.evaluated
judge.started
judge.completed
evaluation.validity.changed
```

## Security

```text
security.signal
security.policy_violation
security.prompt_injection.detected
security.data_exposure
```

## Contamination

```text
contamination.exposure
contamination.canary.triggered
```

## Replay

```text
replay.created
replay.checkpoint.restored
replay.intervention.applied
replay.completed
```

---

# 11. Control Decision

```json
{
  "event_type": "agent.control_decision",
  "payload": {
    "decision": "CONFIRM",
    "gate_id": "high-value-refund",
    "target": "refund:order_123"
  }
}
```

Core values:

```text
ACT
ASK
CONFIRM
REFUSE
RECOVER
STOP
```

This is an observable control choice, not hidden thought.

---

# 12. Environment Observation

```json
{
  "event_type": "environment.observation",
  "plane": "environment",
  "actor": {
    "id": "subject-agent",
    "type": "agent"
  },
  "payload": {
    "observation_id": "obs_18",
    "channel": "mcp",
    "artifact_ref": "artifact://obs/18"
  },
  "state": {
    "projection": "orders.public_view",
    "digest": "sha256:..."
  }
}
```

Observer identity is mandatory because different Actors may see different worlds.

---

# 13. State Changed

```json
{
  "event_type": "environment.state.changed",
  "payload": {
    "cause_event_id": "evt_tool_call_18",
    "changes": [
      {
        "entity": "refund:rf_123",
        "operation": "created"
      }
    ]
  },
  "state": {
    "before": "sha256:a",
    "after": "sha256:b",
    "diff_ref": "artifact://diff/18"
  }
}
```

This SHOULD be emitted by authoritative state adapters, not inferred only from Agent text.

---

# 14. Durable Commit

```json
{
  "event_type": "environment.commit",
  "payload": {
    "effect_id": "wire-transfer:tx_991",
    "effect_type": "financial.transfer",
    "irreversible": true,
    "authorization_witness": "evidence://approval/112",
    "witness_freshness": "valid"
  }
}
```

This supports testing authorization at the actual durability boundary.

---

# 15. Authority Witness

A witness explains why an action was permitted.

Possible witnesses:

- human approval;
- capability grant;
- policy decision;
- object-version witness;
- identity verification;
- transaction/branch token.

```json
{
  "event_type": "authority.witness.created",
  "payload": {
    "witness_id": "auth_...",
    "type": "human_approval",
    "scope": "refund:order_123",
    "valid_until": "2026-08-11T10:05:00Z",
    "binding_digest": "sha256:..."
  }
}
```

---

# 16. Fault Events

```json
{
  "event_type": "fault.activated",
  "payload": {
    "fault_id": "fault_1",
    "type": "transport.timeout",
    "target": "tool:order.get",
    "visibility": "hidden"
  }
}
```

Recovery metrics must condition on faults that actually activated.

---

# 17. Verification Claim

```json
{
  "event_type": "verification.claim.evaluated",
  "plane": "evaluator",
  "actor": {
    "id": "refund-state-oracle@7",
    "type": "oracle"
  },
  "payload": {
    "claim_id": "target-refunded",
    "dimension": "state.postcondition",
    "method": "state_oracle",
    "verdict": "PASS",
    "severity": "critical",
    "confidence": 1.0
  },
  "evidence": [
    {
      "id": "ev_state_881",
      "uri": "artifact://state/refund-rf123",
      "digest": "sha256:..."
    }
  ]
}
```

---

# 18. Judge Event

```json
{
  "event_type": "judge.completed",
  "payload": {
    "judge_id": "semantic-resolution",
    "judge_version": "4.1.2",
    "verdict": "PASS",
    "score": 0.88,
    "confidence": 0.77,
    "rubric": "rubric://resolution@4"
  }
}
```

Judge confidence MUST NOT be treated as calibrated probability unless calibration metadata says so.

---

# 19. Evaluation Validity

```json
{
  "event_type": "evaluation.validity.changed",
  "payload": {
    "from": "VALID",
    "to": "CONTAMINATED",
    "reason": "explicit_answer_exposure",
    "first_exposure_event": "evt_77"
  }
}
```

Late-discovered invalidity can invalidate a completed run without rewriting history.

---

# 20. Contamination Exposure

```json
{
  "event_type": "contamination.exposure",
  "payload": {
    "class": "EXPLICIT_ANSWER",
    "source": "web",
    "query_ref": "artifact://search/query/77",
    "content_ref": "artifact://search/page/77",
    "confidence": 0.98
  }
}
```

---

# 21. Replay Intervention

```json
{
  "event_type": "replay.intervention.applied",
  "payload": {
    "intervention_id": "int_3",
    "component": "tool_schema",
    "target": "refund.create.order_id",
    "before_digest": "sha256:old",
    "after_digest": "sha256:new",
    "declared_controlled": true
  }
}
```

---

# 22. First Bad Step

Failure localization is an annotation that references original immutable events:

```json
{
  "event_type": "verification.claim.evaluated",
  "payload": {
    "claim_id": "failure.first_bad_step",
    "classification": "stale_state_use",
    "target_event_id": "evt_17",
    "confidence": 0.91
  }
}
```

---

# 23. Immutability

Completed Episode events SHOULD be append-only.

Corrections SHOULD create new events:

```text
annotation.added
annotation.superseded
evaluation.validity.changed
```

rather than mutate history.

---

# 24. Ordering

Distributed wall clocks are insufficient.

Ordering uses:

1. authoritative Episode `sequence`;
2. OTel parent/child causality;
3. `logical_time`;
4. `observed_at`.

Consumers MUST NOT infer causality from timestamp alone.

---

# 25. Tamper-Evident Chain

High-assurance deployments MAY maintain:

```text
H_n = SHA256(H_(n-1) || canonical(event_n))
```

Final Episode manifest stores the chain root.

Optional in v0.1, recommended for regulated verification.

---

# 26. Privacy and Retention

Events MAY carry:

```json
{
  "security": {
    "classification": "regulated",
    "contains_pii": true,
    "redaction_policy": "pii-v3",
    "retention": "30d"
  }
}
```

Raw sensitive content belongs in controlled artifacts.

---

# 27. Trace Completeness

Episode postflight should calculate:

```json
{
  "required_event_types": [
    "episode.started",
    "environment.reset.completed",
    "episode.completed"
  ],
  "missing": [],
  "estimated_loss_rate": 0.0
}
```

If missing events make critical verification impossible, validity becomes `TRACE_INCOMPLETE`.

---

# 28. MCP Correlation

Keep native MCP data and OTel GenAI/MCP semantics where available.

```text
MCP call span
   ↕ trace/span ID
AVP action event
   ↕ cause_event_id
Environment State Delta
```

Do not duplicate complete MCP payloads into all events.

---

# 29. A2A Correlation

Suggested mappings:

```text
A2A task id      → external_task_id
A2A remote agent → actor_id
A2A artifact     → artifact_ref
```

AVP verifies collaboration without requiring opaque Agent internals.

---

# 30. Browser / Computer-Use Correlation

Possible artifacts/events:

```text
DOM/accessibility snapshot
screenshot
mouse/keyboard
URL/navigation
storage state
backend state delta
```

Screenshots should be artifacts, not embedded event bodies.

Transactional backend state should remain preferred truth when available.

---

# 31. Derived Metrics

The event model can derive:

```text
Tool Selection Accuracy
Argument Accuracy
Retry Count
Recovery Success
Post-success Over-action
Control Confusion Matrix
State Collateral Damage
Fault-conditioned Success
Prompt-injection ASR
First Bad Step Position
Time-to-Recovery
Cost per Successful Episode
```

Metrics need not themselves be stored as events.

---

# 32. AVP Attribute Namespace

Proposed experimental attributes:

```text
avp.episode.id
avp.experiment.id
avp.scenario.id
avp.scenario.digest
avp.environment.id
avp.environment.digest
avp.state.before.digest
avp.state.after.digest
avp.validity.status
avp.verification.claim_id
avp.verification.verdict
avp.fault.id
avp.replay.parent_episode_id
```

Low-cardinality values should be indexed. Raw high-cardinality content belongs in artifacts.

---

# 33. CloudEvents Compatibility

An AVP Event MAY be wrapped in CloudEvents:

```text
CloudEvents id      ← event_id
CloudEvents source  ← AVP producer
CloudEvents type    ← avp.<event_type>
CloudEvents subject ← episode_id
CloudEvents data    ← AVP event
```

This is an optional transport binding.

---

# 34. Example Timeline

```text
#001 episode.started

#002 environment.reset.completed
     state = S0

#003 user.message

#004 tool.call order.search
#005 tool.result
#006 environment.observation

#007 agent.control_decision ASK
#008 user.message

#009 tool.call order.get
#010 tool.result

#011 fault.activated stale_projection

#012 environment.observation
     observation based on S8

#013 agent.control_decision ACT
     ← candidate first bad step

#014 tool.call refund.create

#015 environment.commit
     state S9 → S10
     wrong target mutated

#016 agent.stop
#017 episode.verification.started

#018 verification.claim.evaluated
     target-refunded FAIL

#019 verification.claim.evaluated
     collateral-damage FAIL

#020 verification.claim.evaluated
     first_bad_step = #013

#021 episode.completed
```

This supports replay from the checkpoint before `#013`.

---

# 35. Conformance

A conformant AVP-Telemetry implementation:

1. MUST provide stable `episode_id`.
2. MUST preserve event ordering semantics.
3. MUST distinguish producer plane.
4. MUST NOT imply hidden chain-of-thought access.
5. MUST link state-changing actions to state digests when authoritative state exists.
6. MUST link critical verification claims to evidence.
7. MUST make telemetry incompleteness visible.
8. SHOULD correlate OTel trace/span identifiers.
9. SHOULD store large/sensitive payloads by reference.
10. SHOULD keep completed trace history append-only.

---

# 36. Upstream Strategy

If AVP becomes widely adopted, stable generic semantics SHOULD be proposed upstream to OpenTelemetry instead of maintaining a permanent competing telemetry namespace.

Potential future upstream areas:

```text
evaluation events
verification claim attributes
agent runtime safety signals
environment/state correlation
```

The AVP namespace remains experimental until semantics stabilize.

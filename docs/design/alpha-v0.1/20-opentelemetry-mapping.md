# 20 OpenTelemetry Mapping Specification

> Status: Adapter Draft v0.1  
> Target: OpenTelemetry GenAI Semantic Conventions dedicated repository.

## 1. Principle

AVP does not create a second distributed tracing ecosystem.

OpenTelemetry owns:

```text
trace context
span lifecycle
generic attributes/events
GenAI/Agent/Tool conventions
```

AVP owns:

```text
Scenario identity
Episode identity
Environment State/evidence
verification
faults
replay
evaluation validity
```

---

## 2. Current OTel Direction

Generative AI conventions have moved into a dedicated OpenTelemetry GenAI semantic-conventions repository.

It includes Agent and Tool span semantics.

AVP should track an explicit OTel GenAI schema URL/version rather than assuming core semconv version equals GenAI semconv version.

---

## 3. Span Correlation

AVP events contain:

```text
trace_id
span_id
parent_span_id
```

when a causal OTel span exists.

Do not synthesize fake parentage solely to make a prettier tree.

---

## 4. AVP Resource Attributes

Recommended low-cardinality resource attributes:

```text
avp.protocol.version
avp.runtime.implementation
avp.environment.kind
```

High-cardinality Episode data should usually be span/event attributes rather than resource attributes.

---

## 5. Episode Span

Optional root/coordination span:

```text
avp.episode
```

Attributes:

```text
avp.episode.id
avp.scenario.id
avp.scenario.digest
avp.agent.digest
avp.environment.digest
```

If an external trace already owns the root, Episode can be a linked span instead.

---

## 6. Agent Spans

Reuse OTel GenAI Agent spans such as agent invocation/workflow spans.

Add:

```text
avp.episode.id
avp.actor.id
```

Do not duplicate provider/model attributes already standardized.

---

## 7. Tool Spans

Reuse OTel execute-tool semantics.

AVP adds:

```text
avp.tool.schema.digest
avp.state.before.digest
avp.state.after.digest
avp.authority.witness.id
avp.fault.id
```

only when relevant.

---

## 8. State Change Events

State changes may be:

- OTel events attached to causal spans;
- AVP events exported as logs;
- records in State Ledger.

The authoritative State Ledger remains the verification source.

OTel export is observability/interoperability representation.

---

## 9. Verification Event

Where OTel GenAI evaluation events are suitable, map semantic Judge/evaluation results to them.

AVP-specific fields include:

```text
avp.verification.claim_id
avp.verification.dimension
avp.verification.verdict
avp.validity.status
avp.evidence.count
```

Evidence payload remains an artifact reference.

---

## 10. Fault Events

Fault activation should be attached to:

- target span when clear;
- Episode span otherwise.

Attributes:

```text
avp.fault.id
avp.fault.type
avp.fault.visibility
```

---

## 11. Replay

Replay trace links parent Episode:

```text
avp.replay.parent_episode_id
avp.replay.mode
avp.replay.intervention_digest
```

Use OTel Links where causal relationship is not parent-child.

---

## 12. Privacy

Do not enable content capture just for AVP.

Respect OTel/organization policies for:

```text
input messages
output messages
tool arguments/results
```

AVP can retain hashes/references without raw content.

---

## 13. Cardinality

Avoid high-cardinality metrics labels such as:

```text
episode_id
user_id
prompt text
tool arguments
```

Use traces/logs/artifacts for those.

Metrics should aggregate by controlled dimensions.

---

## 14. Upstream Strategy

AVP starts with experimental `avp.*` fields.

After multi-vendor usage, propose generic stable concepts upstream where appropriate.

Candidate areas:

```text
verification claim events
evaluation validity
environment/state correlation
fault-conditioned agent execution
```

Do not upstream AVP-specific product concepts prematurely.

---

## 15. Conformance

OTel adapter tests should ensure:

1. valid trace/span IDs preserved;
2. AVP Episode correlation present;
3. execute-tool spans not duplicated unnecessarily;
4. evidence content not accidentally injected into metrics;
5. high-cardinality fields excluded from metric labels;
6. replay uses links or explicit identifiers correctly.

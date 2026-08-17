# 19 MCP Adapter Specification

> Status: Adapter Draft v0.1  
> Target baseline: MCP specification `2026-07-28`.

## 1. Scope

AVP does not replace MCP.

The MCP Adapter gives AVP visibility/control around Agent-visible MCP traffic:

```text
Subject Agent
   ↓
AVP MCP Gateway
   ↓
MCP Server
```

while privileged evaluator APIs remain outside MCP subject reachability.

---

## 2. Current MCP Baseline

The `2026-07-28` MCP release uses a stateless protocol core.

Important implications for AVP:

- no protocol-level session dependency;
- requests are self-describing;
- `Mcp-Method` and `Mcp-Name` headers support routing/authorization;
- tool/resource/prompt lists can be cacheable;
- extensions carry long-running capabilities.

AVP adapter version must publish compatible MCP protocol versions.

---

## 3. Capture

For every call capture:

```text
MCP protocol version
client identity metadata
server identity
Mcp-Method
Mcp-Name
tool schema digest
arguments artifact
result artifact
latency
error
cache metadata where relevant
```

---

## 4. Tool Identity

Tool identity is not only a string name.

Use:

```text
server identity
+ tool name
+ schema digest
+ protocol version
```

This avoids collisions across aggregated MCP servers.

---

## 5. Schema Fingerprinting

On `tools/list` / discovery:

```text
canonical tool definition
→ digest
```

Episode manifest records the actual resolved schema set.

This is essential because tool description/schema changes can materially change Agent behavior.

---

## 6. Fault Injection

Adapter MAY inject:

```text
timeout
HTTP error
MCP error
malformed result
partial result
stale result
tool unavailable
schema change
description mutation
```

Injected result must emit AVP fault lifecycle events.

---

## 7. Security Mutation

Security tests can place prompt injection in:

```text
tool description
tool result
resource content
```

Such content is marked untrusted.

---

## 8. Authorization

Gateway can enforce:

```text
server allowlist
method allowlist
tool allowlist
Actor permissions
Scenario-specific denial
```

Header-based routing in current MCP makes many policies enforceable without parsing arbitrary payloads.

---

## 9. Cache Semantics

Because current MCP list results support cache hints, Adapter should record:

```text
ttl
cache scope
catalog digest
cache hit/miss when observable
```

A stale tool catalog can itself be a Scenario fault.

---

## 10. Long-Running MCP Work

MCP extensions may support long-running Tasks.

AVP treats them as subject actions with external task identity and observes:

```text
created
input required
progress
terminal
cancelled
```

where available.

---

## 11. MRTR / Confirmation

Multi-round-trip interactions can expose requests for missing information/confirmation.

AVP maps observable confirmation/input-required events to Control evaluation without redefining MCP semantics.

---

## 12. OTel Correlation

MCP Adapter should preserve or create OTel spans according to current GenAI/MCP semantic conventions, then attach AVP Episode/Scenario attributes.

---

## 13. Hidden Evaluator Rule

Never register:

```text
ground_truth.get
oracle.evaluate
benchmark.answer
future_faults.list
```

as subject-visible MCP tools.

Evaluator operations use separate AVP credentials/network.

---

## 14. Conformance Adapter Tests

- protocol-version capture;
- tool schema digest;
- multi-server name collision;
- timeout injection;
- hidden evaluator inaccessible;
- stale catalog mutation;
- malicious tool-result telemetry;
- OTel correlation.

# 14 AVP SDK Contract

> Status: SDK Draft v0.1  
> Goal: provide consistent developer semantics across Python, TypeScript, Java and Go.

## 1. SDK Layers

The SDK is split into:

```text
avp-models
avp-client
avp-runtime
avp-oracle
avp-adapter
avp-testing
```

Applications should not need the full runtime to submit an Experiment.

---

## 2. Core Portable Models

Generated from JSON Schema/OpenAPI where practical:

```text
AgentSystem
ScenarioTemplate
ScenarioInstance
EnvironmentManifest
EpisodeManifest
Snapshot
Event
Evidence
VerificationResult
ReliabilityReport
ReplayRequest
```

Generated models MUST preserve unknown namespaced extensions.

---

## 3. Client API

Conceptual API:

```python
client = AVPClient(endpoint=...)

episode = client.episodes.create(
    scenario_instance=...,
    agent=...
)

episode.start()
episode.wait()
report = episode.verify()
```

Async SDKs SHOULD provide native async APIs.

---

## 4. Runtime Provider API

```python
class EnvironmentProvider(Protocol):
    def capabilities(self) -> Capabilities: ...
    def provision(self, scenario) -> EnvironmentLease: ...
    def release(self, lease) -> None: ...
```

An EnvironmentLease exposes control/evaluator interfaces but subject capabilities separately.

---

## 5. Agent Adapter API

```python
class AgentAdapter(Protocol):
    def fingerprint(self) -> AgentSystemManifest: ...
    def run(self, task, capabilities, event_sink) -> AgentResult: ...
```

Adapters MUST NOT require private chain-of-thought.

---

## 6. Event Sink

```python
class EventSink(Protocol):
    def emit(self, event: AVPEvent) -> None: ...
```

SDK instrumentation should preserve existing OTel context when available.

---

## 7. Artifact API

```python
artifact = artifacts.put(
    bytes_or_stream,
    media_type="application/json",
    classification="evaluator-confidential"
)
```

Artifact clients SHOULD support streaming and content digest verification.

---

## 8. Oracle SDK

```python
class Oracle(Protocol):
    descriptor()
    evaluate(context) -> VerificationResult
```

Oracle SDK is detailed in `17-oracle-sdk.md`.

---

## 9. Scenario Compiler API

```python
instance = compiler.compile(
    template,
    seed_bundle=...
)
```

Compiler output MUST have no unresolved randomness.

---

## 10. Error Model

SDKs should share semantic errors:

```text
ProtocolError
ValidationError
InvalidStateTransition
CapabilityNotSupported
EnvironmentFailure
OracleFailure
ReplayNotSupported
ArtifactIntegrityError
AuthenticationError
AuthorizationError
```

Language-native exception hierarchies may vary.

---

## 11. Idempotency

SDK helpers should automatically generate or accept:

```text
Idempotency-Key
```

for create/control operations where the HTTP binding supports it.

---

## 12. Auth

SDK supports standard credential providers:

```text
static bearer
OAuth/OIDC
mTLS
workload identity
custom provider
```

Credentials are transport concern, never serialized into Scenario packages.

---

## 13. Version Negotiation

Client discovers:

```text
protocol version
profiles
extensions
```

It rejects or degrades features explicitly.

Silent semantic fallback is forbidden for verification-critical behavior.

---

## 14. Local Mode

SDK can target:

```text
remote AVP endpoint
embedded reference runtime
subprocess local runner
```

This is important for developer adoption.

---

## 15. Language Priorities

### Python
Reference + research ecosystem.

### TypeScript
Web/Node agents and developer tooling.

### Java
Enterprise platforms, Spring ecosystem, JVM Agent services.

### Go
Runtime/scheduler/infrastructure integrations.

---

## 16. Java Design Direction

Java SDK SHOULD expose immutable records/builders, e.g.:

```java
var episode = client.episodes().create(
    CreateEpisodeRequest.builder()
        .scenario(instanceRef)
        .agent(agentRef)
        .build()
);
```

Reactive support MAY be optional; blocking + CompletableFuture APIs are sufficient initially.

---

## 17. TypeScript Design Direction

Use discriminated unions for:

```text
event types
verdicts
validity
resource kinds
```

This makes schema evolution safer.

---

## 18. Go Design Direction

Keep runtime contracts interface-first and avoid reflection-heavy schema behavior.

---

## 19. Compatibility Matrix

Every SDK release publishes:

```text
SDK version
supported AVP protocol range
supported extensions
supported OTel mapping version
supported MCP/A2A adapter version
```

---

## 20. Conformance

Official SDKs run:

- schema fixtures;
- API compatibility;
- event round-trip;
- unknown extension preservation;
- protocol version negotiation.

SDK conformance is distinct from Runtime conformance.

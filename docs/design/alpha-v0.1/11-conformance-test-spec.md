# 11 AVP Conformance Test Specification

> Status: Draft v0.1  
> Goal: turn AVP from a document into an independently testable protocol.

## 1. Principle

A protocol becomes trustworthy when two independent implementations can prove they satisfy the same observable contract.

AVP therefore requires a public **Technology Compatibility / Conformance Kit**.

The kit tests:

```text
protocol semantics
security isolation
environment integrity
verification integrity
snapshot/replay
fault behavior
telemetry/evidence
statistical manifest integrity
```

It does not test whether a vendor's UI is good.

---

# 2. Conformance Artifact

A tested implementation emits:

```yaml
implementation:
  name: example-runtime
  version: 2.4.1
  commit: ...
  build_digest: sha256:...

protocol:
  version: 0.1.0
  profiles:
    - AVP-Core
    - AVP-Environment
    - AVP-Verification

results:
  passed: 118
  failed: 0
  skipped: 14

environment:
  conformance_suite: 0.1.0
  runtime_manifest: ...
```

---

# 3. Certification Profiles

Certification is profile-based.

Bad:

```text
AVP compliant = yes/no
```

Better:

```text
AVP-Core Certified
AVP-Environment Certified
AVP-Snapshot Certified
AVP-Verification Certified
AVP-Replay Certified
AVP-Chaos Certified
AVP-Telemetry Certified
```

A product cannot claim profiles it did not test.

---

# 4. Test Categories

## C0 — Schema

- capability descriptor valid;
- Scenario resources validate;
- events validate;
- unknown extensions preserved.

## C1 — Lifecycle

- valid transitions accepted;
- invalid transitions rejected;
- idempotent create;
- pause/resume;
- terminal behavior.

## C2 — Identity

- immutable digests stable;
- mutable aliases resolved;
- runtime version recorded.

## C3 — Environment

- reset produces expected initial State;
- initial failure becomes invalid Eval;
- State digest stable.

## C4 — Isolation

- subject cannot access evaluator secrets;
- subject cannot call privileged evaluator API;
- future fault schedule hidden;
- answer-key artifact hidden.

## C5 — Snapshot

- create;
- mutate;
- restore;
- compare equivalence;
- uncaptured dependency recorded.

## C6 — Fault

- scheduled;
- activated;
- observed;
- cleared;
- actual target matches definition.

## C7 — Verification

- Claim result links evidence;
- deterministic critical fail overrides semantic pass;
- Oracle crash becomes validity failure;
- semantic Judge cannot mutate subject world by default.

## C8 — Telemetry

- stable Episode ID;
- monotonic sequence;
- State event links;
- trace/span correlation;
- missing critical telemetry changes validity.

## C9 — Replay

- parent linkage;
- intervention manifest;
- held-constant declaration;
- replay equivalence.

## C10 — Contamination

- canary exposure detected;
- answer-key exposure invalidates;
- hidden metadata inaccessible.

## C11 — Resource/Infra

- resource request/limit recorded;
- infra failure separate;
- OOM classification captured.

---

# 5. Core Test IDs

Naming convention:

```text
AVP-<PROFILE>-<AREA>-NNN
```

Examples:

```text
AVP-CORE-LIFECYCLE-001
AVP-ENV-RESET-001
AVP-ENV-ISOLATION-003
AVP-SNAPSHOT-RESTORE-002
AVP-VERIFY-EVIDENCE-001
AVP-REPLAY-INTERVENTION-004
```

IDs never change meaning after publication.

---

# 6. Mandatory Core Cases

## AVP-CORE-LIFECYCLE-001

Create Episode.

Expected:

- 201;
- stable Episode ID;
- manifest digest;
- initial state CREATED/PROVISIONING.

## AVP-CORE-LIFECYCLE-002

Attempt illegal `COMPLETED → RUNNING`.

Expected:

- rejected;
- no history rewrite.

## AVP-CORE-IDEMPOTENCY-001

Repeat create with same Idempotency-Key.

Expected:

- same Episode identity or documented idempotent equivalent.

---

# 7. Reset Tests

## AVP-ENV-RESET-001

Given known fixture:

```text
customer.deleted = false
refund.count = 0
```

mutate State, reset.

Expected:

- initial assertions pass;
- State digest equals or meets declared equivalence.

## AVP-ENV-RESET-002

Provide broken fixture.

Expected:

```text
Episode validity = INVALID_INITIAL_STATE
```

not subject FAIL.

---

# 8. Isolation Red-Team Tests

The test kit MUST behave as an adversarial subject.

Attempts:

```text
GET evaluator endpoint
scan local network
read env vars
guess oracle artifact path
enumerate mounted files
ask MCP for hidden tools
inspect process args
read cloud metadata
```

Expected:

- denied/unavailable;
- attempt observable as security telemetry where applicable.

This test is one of the strongest reasons to have a conformance kit.

---

# 9. Snapshot Tests

## Exact logical snapshot

- snapshot S;
- mutate X;
- restore S;
- projection digest equals S.

## Uncontrolled external dependency

- declare live external service;
- restore local components;
- implementation MUST NOT claim `EXACT` unless external behavior is captured.

---

# 10. State/Evidence Tests

Create a task where Agent says:

> refund completed

but DB state has no refund.

Expected:

```text
Agent self-report: success claim
State Oracle: FAIL
Task: FAIL
False Success finding: true
```

---

# 11. Hard-vs-Soft Conflict

Test fixture:

```text
State Oracle: unauthorized transfer occurred
Semantic Judge: response quality 0.99
```

Expected:

```text
Critical safety/task verdict FAIL
```

A weighted average yielding PASS is non-conformant.

---

# 12. Oracle Failure

Force Oracle process crash.

Expected:

```text
validity = ORACLE_FAILURE
```

No subject failure score change unless an independent valid Oracle establishes failure.

---

# 13. Trace Completeness

Drop required Environment State event.

Expected:

```text
validity = TRACE_INCOMPLETE
```

for Claims depending on that event.

---

# 14. Fault Lifecycle

Schedule timeout on second call.

Expected event order:

```text
fault.scheduled
tool.call #1
tool.call #2
fault.activated
fault.observed
...
fault.cleared
```

If fault never activates, metrics cannot classify run as fault-conditioned.

---

# 15. Replay Intervention Test

Parent Episode:

- field `order_id` ambiguous;
- failure occurs.

Replay:

- restore checkpoint;
- apply schema intervention;
- preserve declared seed bundle.

Expected:

- intervention event;
- parent link;
- equivalence report;
- uncontrolled differences list.

Conformance does not require the Agent to improve; it requires honest replay semantics.

---

# 16. Contamination Test

Expose a canary through Agent-visible content.

Expected:

```text
contamination.exposure
evaluation.validity.changed → CONTAMINATED
```

Another test keeps canary evaluator-only.

Expected: Agent cannot obtain it.

---

# 17. Resource Manifest Test

Run a controlled memory-overuse subject.

Runtime must record:

```text
memory request
memory hard limit
observed peak if available
OOM event
classification
```

Conformance checks observability/classification, not a mandated memory value.

---

# 18. Golden Reference Runtime

The open-source project SHOULD ship a tiny deterministic reference world:

```text
refund-service
in-memory/SQLite DB
MCP tool server
state adapter
fault proxy
reference Oracle
```

It is not a benchmark; it exists to test protocol implementations.

---

# 19. Golden Subject Agents

Ship deliberately flawed agents:

```text
agent-correct
agent-false-success
agent-wrong-target
agent-no-confirm
agent-loop
agent-injection-following
```

Conformance expected outcomes are deterministic enough to validate the evaluator.

---

# 20. Golden Broken Evaluators

Also ship:

```text
oracle-crash
oracle-wrong-schema
trace-dropper
reset-corruptor
contamination-leaker
```

AVP must prove that its Eval-validity layer catches evaluator/runtime faults.

---

# 21. Conformance Runner

CLI:

```bash
avp-conformance run \
  --endpoint https://runtime.local \
  --profiles AVP-Core,AVP-Environment,AVP-Verification
```

Output:

```text
JUnit XML
JSON report
human-readable report
signed optional attestation
```

---

# 22. Test Manifest

Machine-readable case:

```yaml
id: AVP-VERIFY-EVIDENCE-001
profile: AVP-Verification
level: MUST
description: Critical claims resolve to evidence.
preconditions:
  - reference-world
steps:
  - create_episode
  - run_false_success_agent
  - verify
assertions:
  - path: verification.claims[refund.completed].evidence
    operator: not_empty
```

---

# 23. Version Compatibility

Conformance suite is versioned independently:

```text
Protocol 0.1.x
Conformance 0.1.y
```

Every release states supported protocol range.

Historical results remain tied to exact suite version.

---

# 24. Extensions

Vendors may publish extension conformance suites.

Namespace:

```text
org.vendor.feature/*
```

Extension suites cannot weaken core requirements.

---

# 25. Security Testing Safety

Conformance red-team tests must target only the supplied test Environment.

The kit must not scan arbitrary external networks.

A runtime provides a declared test CIDR/namespace boundary.

---

# 26. Statistical Reproducibility Test

The TCK should include a small repeated stochastic test to verify that the platform records:

```text
run count
seed bundle
validity
resource manifest
```

It does not certify a specific model success rate.

---

# 27. Cross-Implementation Test

Longer-term release criterion:

> A new AVP minor version is not considered ecosystem-ready until at least two independent implementations pass its Core TCK.

This prevents a standard that is accidentally coupled to one codebase.

---

# 28. Public Result Registry

Optional public registry fields:

```text
implementation
version
protocol profile
suite version
test date
result digest
source commit
attestation
```

Do not create paid “certification theater” before interoperability is mature.

---

# 29. Governance of Tests

Every normative protocol MUST/SHOULD should map to:

```text
one or more TCK cases
```

The spec repository should maintain a matrix:

```text
Requirement ID
→ Test ID
```

Untested MUST requirements are technical debt.

---

# 30. Exit Criteria for AVP v0.2

Before v0.2:

1. reference runtime passes Core/Environment/Verification;
2. second implementation passes Core;
3. isolation red-team suite exists;
4. broken-evaluator suite exists;
5. schemas are machine validated;
6. OpenAPI examples execute;
7. at least one MCP-based benchmark adapter runs end-to-end.

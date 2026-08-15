# AEP-0007: Subject Adapter Interoperability Contract v0.1

- Status: Proposed
- Date: 2026-08-15
- Scope: AVP Subject Adapter interoperability

## Motivation

AVP needs a portable boundary between the Runtime and the Agent System under verification. The existing Python SubjectAdapter, HTTP stepping transport, and in-process callable are useful reference implementations, but they must not become the protocol by accident.

The Subject Adapter contract therefore standardizes only evaluator-verifiable interaction semantics: adapter identity, Agent System binding, invocation input projection, evaluator-owned budgets, controlled Runtime capabilities, terminal outcome separation, fail-closed handle lifecycle, and isolation/transport claim honesty.

## Authority boundaries

AVP owns:
- binding a Subject Adapter to an Agent System identity;
- the evaluator-visible invocation envelope and budget semantics;
- the rule that Subject-visible task/context derives from the ScenarioInstance Subject projection;
- the controlled gateway through which Subject-side observation/tool/trace capabilities are exercised;
- terminal outcome and infrastructure-failure separation;
- adapter lifecycle and stale-handle behavior;
- machine-verifiable transport/isolation claims used by AVP.

Other domains remain authoritative for their own semantics:
- Scenario owns Subject-visible ScenarioInstance projection;
- Security owns capability authorization, hidden-material secrecy, credential boundaries, and assurance claims;
- Environment owns authoritative mutable state and observations;
- MCP owns Agent-to-tool protocol semantics where MCP is used;
- OpenTelemetry/W3C owns trace propagation semantics;
- Evidence/Oracle own evaluation evidence and verdict authority.

## Proposed portable requirements

- `AVP-SUBJECT-001` Adapter Identity Binding
- `AVP-SUBJECT-002` Agent System / Handle Binding
- `AVP-SUBJECT-003` Subject Projection Confidentiality
- `AVP-SUBJECT-004` Evaluator-Owned Invocation Budgets
- `AVP-SUBJECT-005` Controlled Capability Gateway
- `AVP-SUBJECT-006` Terminal Outcome Separation
- `AVP-SUBJECT-007` Protocol / Result Fail-Closed Validation
- `AVP-SUBJECT-008` Release and Stale-Handle Fail-Closed
- `AVP-SUBJECT-009` Transport and Isolation Claim Honesty

## Explicitly non-normative in v0.1

- Python `Protocol`, dataclass, enum, exception, or callable shapes;
- `/v1/avp/invoke`;
- `X-AVP-Subject-Version`;
- the reference HTTP `tool_call` / `completed` / `failed` stepping frames;
- synchronous versus asynchronous invocation;
- HTTP, subprocess, container, VM, RPC, SDK, or in-process transport choice;
- generated handle identifier format;
- exact span names or trace-header plumbing;
- reference Agent report formatting.

## Conformance direction

The portable TCK must exercise real adapter behavior rather than accept case-id-to-PASS implementations. Negative controls must cover Agent System substitution, evaluator-only material exposure, budget overrun, capability bypass, malformed terminal results, stale handles, and false isolation claims.

The reference in-process adapter may claim no process isolation. A future subprocess/container adapter may claim stronger assurance only when SecurityAssurance supports and verifies that claim.

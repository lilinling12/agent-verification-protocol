# AVP Subject Adapter Interoperability Contract v0.1

Status: Draft

This document defines the portable AVP boundary between the Runtime and the Agent System under verification. It does not standardize any particular Python API or transport wire format.

## 1. Authority and composition

The Subject Adapter mediates execution of the Agent System under verification. It MUST NOT become an alternate authority for Scenario visibility, Security authorization, Environment state, MCP tool semantics, OpenTelemetry propagation semantics, or Oracle/Evidence verdict semantics.

Scenario controls Subject-visible ScenarioInstance projection. Security controls capability and hidden-material boundaries. Environment controls authoritative state and observation. MCP controls Agent-to-tool protocol semantics where used. OpenTelemetry/W3C controls trace propagation semantics. Oracle/Evidence controls evaluation authority.

## 2. Normative requirements

### AVP-SUBJECT-001 — Adapter Identity Binding

A conforming Runtime MUST obtain a stable Subject Adapter description before execution and MUST bind the description identity to the Episode/manifest identity used for verification.

Changing execution-relevant adapter identity or configuration MUST NOT be silently treated as the same verified adapter configuration.

### AVP-SUBJECT-002 — Agent System / Handle Binding

Opening a Subject execution context MUST produce an opaque handle bound to the intended Agent System identity and owning adapter context.

A handle MUST NOT be accepted for a different Agent System, adapter owner, or execution context. Ownership mismatch MUST fail closed before Subject execution.

The portable contract does not define handle serialization or identifier format.

### AVP-SUBJECT-003 — Subject Projection Confidentiality

The Subject-visible task/context MUST be derived from the ScenarioInstance Subject projection and other explicitly Subject-visible Runtime capabilities.

Evaluator-only material, hidden Oracle inputs, future fault schedules, evaluator credentials, hidden reference answers, or other material excluded by Scenario/Security MUST NOT be exposed through the Subject Adapter invocation envelope or gateway.

### AVP-SUBJECT-004 — Evaluator-Owned Invocation Budgets

Invocation step and time/resource budgets supplied by the evaluator MUST be treated as upper bounds.

A Subject Adapter or Subject MUST NOT enlarge, reset, or silently ignore evaluator-owned budgets. Budget exhaustion MUST terminate or reject execution according to the declared failure semantics and MUST NOT be reported as successful Subject completion.

The exact clock source and scheduler are implementation-specific unless governed by another AVP profile.

### AVP-SUBJECT-005 — Controlled Capability Gateway

Capabilities exposed by the Subject Adapter API for Runtime observation, tool invocation, trace propagation, or other evaluator-controlled operations MUST be mediated by capabilities explicitly exposed by the Runtime for that Episode and actor.

The Subject Adapter MUST NOT provide a direct evaluator capability that bypasses Security policy, directly mutate Environment state outside authorized Environment/MCP paths, or independently manufacture stronger capability access through its adapter API.

This requirement is an API-boundary guarantee. It does not by itself claim that arbitrary same-process Subject code is contained from ambient process globals, operating-system resources, or other channels. Stronger containment claims remain governed by AVP SecurityAssurance.

The semantics of observation, tool execution, and propagation remain owned by Environment, MCP, Security, and OpenTelemetry as applicable.

### AVP-SUBJECT-006 — Terminal Outcome Separation

A conforming implementation MUST distinguish at least:

- successful Subject completion;
- explicit Subject execution failure;
- adapter transport failure;
- adapter protocol failure;
- invocation timeout;
- evaluator-owned budget exhaustion.

Infrastructure failures MUST NOT be silently converted into successful Subject completion or ordinary Agent task failure.

A Subject-completed report is Subject output, not authoritative task verdict or validity evidence.

### AVP-SUBJECT-007 — Protocol / Result Fail-Closed Validation

The Runtime or Adapter MUST validate terminal Subject results before accepting completion.

Malformed, contradictory, unsupported, foreign, or otherwise invalid result states MUST fail closed. A result that cannot be proven to represent valid successful completion MUST NOT be treated as successful completion.

Transport-specific frame names and schemas are non-normative in v0.1.

### AVP-SUBJECT-008 — Release and Stale-Handle Fail-Closed

After release, the Subject handle MUST no longer authorize invocation or another release as a valid live execution context.

Unknown, released, substituted, or stale handles MUST fail closed. Implementations MUST NOT revive released execution context implicitly.

### AVP-SUBJECT-009 — Transport and Isolation Claim Honesty

A Subject Adapter MUST describe transport/isolation properties without overstating assurance.

An in-process or same-process adapter MUST NOT claim process, network, tenant, container, VM, or equivalent isolation merely because access is mediated by an API object.

Any stronger isolation or security claim MUST compose with the AVP SecurityAssurance model and be backed by evidence appropriate to that claim.

## 3. Portable lifecycle

The portable lifecycle is abstract:

1. describe adapter identity and claims;
2. open a Subject execution context bound to one Agent System;
3. invoke with Subject-visible task/context and evaluator-owned budgets;
4. exercise only Runtime-exposed adapter capabilities during execution;
5. produce a valid terminal outcome or explicit failure;
6. release the execution context;
7. reject subsequent stale-handle use.

An implementation MAY realize this lifecycle through HTTP, RPC, subprocess, container, VM, SDK, in-process callable, or another transport, provided the normative semantics remain observable and conformant.

## 4. Non-normative reference behavior

The Python reference implementation currently exposes `SubjectAdapter.describe/open/invoke/release`, `SubjectSession.observe/call_tool/trace_headers`, an in-process callable adapter, and a synchronous HTTP JSON stepping adapter. These are reference witnesses only and are not the language-neutral protocol surface.

## 5. Conformance

A Subject v0.1 TCK profile MUST test real behavior and include negative controls for identity substitution, hidden-material leakage, budget overrun, unauthorized gateway capability use, invalid terminal results, stale handles, and false isolation claims. Conformance to this profile MUST NOT be presented as proof of stronger process or operating-system containment.

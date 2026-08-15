# Subject Adapter Reconciliation Decision 001

- Status: Proposed
- Date: 2026-08-15
- Scope: AVP Subject Adapter Interoperability Contract v0.1

## Decision

Promote the language-neutral verification boundary between Runtime and Subject while keeping concrete transport mechanics implementation-specific.

## Promoted semantics

1. Subject Adapter description participates in Episode/manifest identity.
2. A Subject handle is owned by one adapter session and bound to one Agent System identity.
3. Invocation input visible to the Subject is derived from the ScenarioInstance Subject projection and must not expose evaluator-only material.
4. Invocation budgets are evaluator-owned upper bounds and cannot be enlarged by the Subject Adapter or Subject.
5. Subject observation, tool access, and trace propagation occur only through Runtime-controlled capabilities; Security/MCP/Environment/OpenTelemetry retain authority for those domains.
6. Successful Subject completion is distinct from Subject execution failure and from adapter transport/protocol/timeout/budget infrastructure failures.
7. Malformed or contradictory adapter results fail closed and cannot be reclassified as successful task completion.
8. Released, foreign, or Agent-System-mismatched handles fail closed.
9. Transport and isolation claims must be honest; an in-process adapter cannot imply process, network, tenant, container, or VM isolation.

## Non-promoted implementation details

- Python SubjectAdapter/SubjectToolGateway Protocol classes;
- SubjectHandle/SubjectInvocation/SubjectResult dataclass representation;
- HTTP JSON stepping wire format;
- `/v1/avp/invoke` and `X-AVP-Subject-Version`;
- synchronous request loop;
- Python callable in-process adapter;
- UUID-derived handle IDs;
- urllib implementation;
- concrete trace-header injection mechanics.

## Existing implementation audit

The current Runtime already binds Subject adapter description into EpisodeManifest and invokes adapters through a Runtime-owned SubjectSession. The HTTP adapter enforces evaluator-owned step/deadline budgets and separates transport/protocol/execution/budget exceptions. The in-process adapter explicitly declares `isolation: none`.

However, these are implementation evidence only. Portable conformance must be established through a dedicated Subject TCK profile before the contract is promoted.

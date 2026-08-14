# Environment Contract Reconciliation Decision 001

- Status: Proposed
- Date: 2026-08-14
- Scope: AVP Environment v0.1

## Decision

Promote the language-neutral evaluator semantics of authoritative environment state into a dedicated Environment contract while keeping the current Python `EnvironmentAdapter`, in-memory world model, handle dataclasses, fault scheduler, and storage mechanics non-normative.

## Promoted semantics

- environment implementations own mutable authoritative resources;
- provisioned environments are bound to a ScenarioInstance identity;
- supported reset targets must be truthfully established or fail closed;
- logical time is environment-scoped and deterministic/monotonic within an unreverted lineage;
- Subject observation is actor-scoped and cannot expose evaluator-only state;
- evaluator projections are authoritative and digest-bound;
- snapshots are bound to their owning environment instance and state identity;
- restore equivalence is explicit and cannot be overstated;
- diffs bind before/after state identities and projection semantics;
- fault activation respects declared occurrence and Security fault secrecy;
- released/stale handles fail closed.

## Kept implementation-specific

- Python class and enum shapes;
- exact handle/snapshot identifier formats;
- in-memory data structures;
- diff representation algorithms;
- snapshot persistence format;
- wall-clock units;
- scheduler implementation;
- database/browser/container/VM adapter choices;
- adapter-specific fault parameter schemas.

## Cross-contract composition

Environment v0.1 composes with:

- Scenario: provisioning is bound to a materialized ScenarioInstance identity;
- Core: environment operations occur within Episode lifecycle and must fail closed on invalid control-plane operations;
- Evidence: projections, snapshots, digests, and diffs may become evaluator evidence but Environment does not redefine Artifact identity;
- Security: Subject observations and future fault schedules remain protected by the Security boundary;
- Oracle: Oracle access to authoritative projections remains evaluator-side and does not widen Subject capabilities.

## Reference implementation consequence

The existing Python Environment implementation is evidence of feasibility. Conformance must be established by language-neutral TCK vectors before any implementation behavior is treated as promoted protocol semantics.

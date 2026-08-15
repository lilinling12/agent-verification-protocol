# Alpha 2 AEP Acceptance Review

Status: DECISION RECORDED — AEP-0002 THROUGH AEP-0008 ACCEPTED

Decision date: 2026-08-16

The protocol maintainer explicitly approved AEP-0002 through AEP-0008 to move from `Proposed` to `Accepted` during the Alpha 2 readiness review. No AEP was approved to `Final`. This governance decision approves protocol direction only and does not authorize PR merge, tag creation, release publication, package publication, or Alpha 3 work.

Under `GOVERNANCE.md`, `Accepted` means the protocol direction is approved; `Final` remains reserved for normative text and required conformance coverage that have been merged and released.

## Decision rule

The acceptance decision was made only after confirming all of the following:

1. the protocol problem, scope, alternatives, compatibility impact, and security boundary are documented;
2. language-neutral normative semantics exist independently of the Python reference implementation;
3. portable conformance coverage exists for the indexed requirements;
4. reconciliation has no unresolved semantic contradiction for the Alpha 2 scope;
5. acceptance evidence demonstrates fail-closed behavior and assurance honesty where applicable;
6. the proposal does not claim release finality or implementation-specific mechanisms as protocol requirements.

`Accepted` is therefore a governance approval of direction, not a release certification and not permission to merge any pull request.

## Recorded decisions

### AEP-0002 — Security Boundary Contract

**Decision: Accepted.**

Evidence:
- six mandatory `AVP-SECURITY-*` requirements are registered in `avp-security-v0.1` with no conditional escape hatch;
- the Security reconciliation defines capability separation, deny-by-default behavior, evaluator credential/hidden-material secrecy, future-fault secrecy, and assurance honesty;
- the acceptance audit is recorded as passed in `docs/reconciliation/v0.1/matrices/security.yaml`;
- the Alpha 2 cross-profile Security Composition Review found no release-blocking authority/security contradiction;
- in-process/API mediation is explicitly not promoted into process, network, tenant, container, VM, or sandbox isolation claims.

Why not Final:
- Alpha 2 has not been released;
- the normative/conformance stack is not yet fully integrated into `main`;
- stronger deployment isolation remains outside the baseline contract.

### AEP-0003 — Scenario / ScenarioInstance Contract

**Decision: Accepted.**

Evidence:
- the Scenario reconciliation records complete language-neutral materialization, identity, immutability, projection, and reference semantics;
- `open_reconciliation: []`;
- all six mandatory `avp-scenario-v0.1` cases pass in the reference implementation;
- canonical identity uses RFC 8785 JCS + SHA-256 with fail-closed declared identity and resolver binding;
- packaged schema synchronization and built-wheel smoke are part of acceptance evidence;
- Security hidden-material and fault-secrecy semantics compose with Subject projection.

Why not Final:
- no Alpha 2 release exists;
- `Accepted` approves direction, while `Final` requires merged and released normative/conformance text.

### AEP-0004 — Environment Contract

**Decision: Accepted.**

Evidence:
- eleven indexed requirements are covered by seven mandatory portable Environment TCK cases;
- acceptance audit status is passed;
- mutable-state authority, Scenario binding, reset/time semantics, actor-scoped observation, snapshot ownership, restore fidelity, projection identity, diff identity, fault behavior, and stale-handle failure are language-neutral;
- restore fidelity is reported honestly as `STATE_EQUIVALENT` by the reference adapter rather than overstated as `EXACT`;
- implementation-specific storage, snapshot serialization, logical time units, and adapter technologies remain non-normative.

Why not Final:
- release has not occurred and final integrated-main validation is still pending.

### AEP-0005 — MCP Tools Interoperability Profile

**Decision: Accepted.**

Evidence:
- MCP remains the external wire-protocol authority; AVP only standardizes verification-relevant bindings and does not fork MCP semantics;
- eight requirements cover capability binding, verification identity, fail-closed validation, call/evidence binding, selected wire compatibility, outcome separation, and feature honesty;
- acceptance audit status is passed and the portable MCP profile passes 8/8;
- tool execution error is distinct from successful completion, while upstream failure is distinct from an MCP result;
- unsupported MRTR is explicitly unclaimed and fails closed rather than being flattened into success;
- MCP authorization/OAuth remains separate from Scenario capability policy.

Why not Final:
- normative/conformance content is not yet part of a released Alpha 2 baseline.

### AEP-0006 — OpenTelemetry Mapping Profile

**Decision: Accepted.**

Evidence:
- OpenTelemetry/W3C remain external authorities for tracing and propagation mechanics;
- eight requirements define AVP-owned correlation, outcome preservation, data minimization, completeness honesty, and Evidence composition;
- acceptance audit status is passed and all eight mandatory mapping TCK cases pass;
- telemetry cannot rewrite `TOOL_ERROR` or other non-success outcomes into success;
- root-span existence alone cannot prove mapping completeness;
- raw sensitive Subject/evaluator data is not required for conformance;
- telemetry remains observation/evidence and cannot override Oracle/state/verdict authority.

Why not Final:
- the profile is merged on the development line but Alpha 2 has not been released, and AEP lifecycle `Final` requires release.

### AEP-0007 — Subject Adapter Interoperability Contract

**Decision: Accepted.**

Evidence:
- nine indexed requirements are covered by seven mandatory portable TCK cases;
- acceptance audit status is passed;
- adapter/Agent/handle identity, Scenario Subject projection, evaluator-owned budgets, controlled Runtime capabilities, completion-vs-failure separation, result validation, stale handles, and assurance honesty are language-neutral;
- arbitrary evaluator-side Agent metadata is excluded from remote Subject payloads while stable Agent identity is preserved;
- unauthorized adapter-API capability access is denied before downstream routing;
- `SubjectResult` is completion-only and transport/protocol/timeout/budget/execution failures remain distinct;
- in-process transport explicitly claims `isolation: none`.

Why not Final:
- PR #31 is not yet merged into `main` and there is no Alpha 2 release.

### AEP-0008 — Artifact Trust / Attestation Contract

**Decision: Accepted.**

Evidence:
- nine indexed requirements are covered by eight portable cases: seven mandatory plus one conditional publication-authority case;
- acceptance audit status is passed;
- exact Artifact byte identity remains separate from attestation metadata;
- authentication, exact subject binding, authenticated signer identity, and evaluator trust policy remain distinct gates;
- unauthenticated signer hints are non-authoritative;
- malformed, unsupported, integrity, authentication, subject, identity, and policy failures remain fail-closed and machine-distinct;
- authentication failures cannot surface unauthenticated signer/type claims as authenticated result properties;
- same-process publisher privacy is not promoted into signing-authority isolation, and the conditional TCK fails if such unsupported assurance is declared;
- generic signing envelope, PKI, KMS, transparency, revocation, timestamp, registry transport, and domain predicate semantics remain upstream/deployment-owned.

Why not Final:
- PR #32 remains stacked and unmerged;
- no Alpha 2 release exists;
- optional production publication/signing implementations are not a prerequisite for accepting the protocol direction.

## Governance outcome

The protocol-maintainer decision is now recorded as:

> AEP-0002, AEP-0003, AEP-0004, AEP-0005, AEP-0006, AEP-0007, and AEP-0008 are `Accepted`. None is `Final`.

Each AEP records the acceptance date and the explicit boundary that acceptance does not authorize merge, tag, or release.

## Remaining Alpha 2 readiness work

The AEP governance blocker is closed. Alpha 2 RC readiness still depends on:

1. authorized integration of #31 and #32 into `main` in stack order;
2. retarget/rebase validation for stacked descendants after parent integration;
3. final integrated-main CI/Governance, clean built-wheel/conformance, drift, issue, and review-thread validation;
4. release preparation from a selected `main` commit only.

`Final` lifecycle transitions remain out of scope until the corresponding normative text and required conformance coverage are merged and an actual release completes.

# Alpha 3 — AEP-0009 Proposed Readiness Audit

Status: **BLOCKED — NOT READY TO ADVANCE TO PROPOSED**  
AEP: `rfcs/AEP-0009-environment-fabric.md`  
Audited head before this audit commit: `0621c8d5cbc1ae6b75a345990d6c16613b9e4207`  
Base `main`: `cdf56cf8e8d747f26b5438086ece3fb4cd489f31`  
Authority: non-normative governance/acceptance evidence.

## Purpose

This audit determines whether Draft AEP-0009 is sufficiently complete and internally consistent to advance to the AVP `Proposed` state under `GOVERNANCE.md`.

`Proposed` means the design is sufficiently complete for protocol review. It does **not** mean the direction is accepted, normative, ready for backend implementation, assigned to a release, or authorized for publication.

The audit intentionally evaluates the AEP against the current normative surfaces and the Alpha 3 design assets before any Environment Fabric specification, schema, TCK profile, or backend implementation is allowed to become authoritative.

## Live-state evidence at audit start

The repository state checked before recording this audit was:

- `main@cdf56cf8e8d747f26b5438086ece3fb4cd489f31`;
- Draft PR #83 head `0621c8d5cbc1ae6b75a345990d6c16613b9e4207`;
- PR #83 mergeable, with no review comments or discussion threads;
- CI #485: success;
- Governance #522: success;
- Release Validation #36: success.

The gate evidence proves the current design assets satisfy repository automation. It does not by itself prove protocol-review maturity.

## Authority reviewed

The audit reviewed AEP-0009 against:

- `GOVERNANCE.md`;
- `spec/environment/environment-contract.md` and `spec/environment/requirement-index.yaml`;
- `spec/core/episode-lifecycle.md` and `spec/core/requirement-index.yaml`;
- `spec/scenario/scenario-contract.md` and `spec/scenario/requirement-index.yaml`;
- `spec/security/security-boundary-contract.md` and `spec/security/requirement-index.yaml`;
- `spec/evidence/evidence-artifact-identity.md` and `spec/evidence/requirement-index.yaml`;
- `docs/design/alpha3-environment-fabric-architecture.md`;
- `docs/design/alpha3-environment-fabric-normative-gap-audit.md`.

The audit does not treat Python reference-runtime classes, backend products, or historical Alpha v0.1 design documents as normative authority.

## Governance prerequisites

A normative change requires a written problem/scope, alternatives and compatibility analysis, security analysis, conformance strategy, and a recorded maintainer decision.

AEP-0009 already contains substantive material for the first four categories:

| Governance prerequisite | Result | Evidence |
|---|---|---|
| Written problem and scope | PASS | Problem, compatibility baseline, design principles, proposed portable model, explicit exclusions. |
| Alternatives and compatibility | PASS | Alternatives A-E; additive compatibility with Environment v0.1; no release assignment. |
| Security analysis | PASS | Privileged control-plane separation, credential secrecy, fault secrecy, snapshot ownership/integrity, assurance non-inflation. |
| Conformance strategy | PASS WITH BLOCKERS BELOW | Base Fabric TCK direction, conditional profiles, negative same-metadata/broken-behavior implementation requirement. |
| Recorded maintainer decision | PENDING | The AEP remains Draft. This audit records why it must not yet advance. |

## AEP acceptance-criteria review

AEP-0009 defines ten criteria for moving beyond Draft. Their current status is:

### 1. No proposed semantic duplicates or weakens Environment v0.1

**PASS, subject to BR-002.**

The normative-gap audit correctly leaves single-Environment ownership, Scenario binding, reset, logical time, observation, projection, snapshot ownership, restore fidelity, diff, fault lifecycle, and stale-handle behavior under `AVP-ENVIRONMENT-001..011`.

The remaining Fabric surface is composition-specific rather than a parallel Environment contract.

### 2. No assurance semantic duplicates SecurityAssurance

**PASS.**

AEP-0009 rejects an ordinal Fabric isolation level and reuses the existing dimensional `SecurityAssurance` contract. Container or microVM technology names are explicitly forbidden from proving assurance.

### 3. Fabric identity composes cleanly with Evidence/Artifact identity

**PASS FOR PROPOSED MATURITY.**

The design distinguishes Resource Identifier from Artifact content identity, requires retained bytes to use existing Artifact exact-byte identity, and treats the Fabric Manifest as a protocol composition description rather than a replacement digest model.

Exact serialization/canonicalization remains correctly deferred to normative schema/spec work.

### 4. Core lifecycle projection remains unambiguous

**PASS.**

Fabric provisioning remains inside `PROVISIONING`; `QUIESCING` remains the existing side-effect boundary; cleanup/infrastructure conditions remain separate from Task Verdict; no second Episode state machine is introduced.

### 5. Resource/capability negotiation is language-neutral

**BLOCKED — BR-001 and BR-003.**

The architecture and normative-gap audit have converged on `Resource Capability`, but AEP-0009 still defines the central concept as `Fabric Capability`. In addition, the AEP does not yet make capability semantic revision/profile identity a required part of the declaration contract.

These are protocol vocabulary/identity issues, not implementation naming details.

### 6. Aggregate snapshot/restore semantics cannot overclaim atomicity or fidelity

**PASS.**

The AEP explicitly rejects implicit distributed atomicity, preserves per-resource results, and forbids aggregate restore fidelity stronger than all required participating resources can demonstrate.

The exact aggregation representation can remain future normative-spec work.

### 7. Security boundaries for privileged resource control are explicit

**PASS.**

Subject routes are kept separate from provision/reset/snapshot/restore/fault/time control; Evaluator/control credentials remain outside Subject context; future fault schedules remain private; privileged backend controls remain Control Plane concerns.

### 8. Mandatory vs conditional TCK boundaries are testable by independent implementations

**PASS WITH BR-004 CLARIFICATION REQUIRED.**

The base composition profile is separated from relational/browser/network/time/compute profiles, and domain suites become mandatory only when their capability/profile is claimed.

However, the authority that classifies a resource/capability as required versus optional must be stated explicitly enough that an implementation cannot downgrade a Scenario requirement based on backend availability.

### 9. Negative TCK design proves runtime execution rather than metadata self-certification

**PASS.**

The AEP requires negative implementations that advertise identical static capability metadata while violating actual runtime behavior, and requires such implementations to fail conformance.

This is aligned with the repository's existing execution-oriented TCK architecture.

### 10. Release/version selection remains a separate governance decision

**PASS.**

The AEP explicitly does not assign Alpha 3 to `0.3.1`, does not change release-development mode, and does not authorize tags, package-index publication, GitHub Release publication, or signing/attestation publication.

## Blocking findings

AEP-0009 MUST remain `Draft` until all findings below are resolved in the proposal/design assets and the resulting exact head passes repository gates.

### BR-001 — Capability vocabulary is internally inconsistent

**Severity:** Proposed-state blocker  
**Affected assets:** AEP-0009, normative-gap audit vocabulary.

The normative-gap audit correctly establishes two distinct concepts:

- **Resource Capability** — portable, conformance-bearing behavior supported by an Environment Resource implementation;
- **Subject Capability** — the operation/access surface authorized by the materialized actor capability projection.

AEP-0009 still defines a **Fabric Capability**. That term is broader and risks being read as a Fabric-global authorization or feature surface.

**Required resolution:**

- replace the proposed portable term `Fabric Capability` with `Resource Capability` wherever the resource-level support claim is meant;
- state explicitly that Resource Capability support never grants, expands, or substitutes for Subject Capability authorization;
- reserve any future Fabric-level capability term for a separately specified cross-resource semantic such as coordinated atomicity, rather than using it for ordinary resource support.

### BR-002 — Cleanup retry safety is an orphan proposed MUST

**Severity:** Proposed-state blocker  
**Affected assets:** AEP-0009, architecture baseline, normative-gap audit.

AEP-0009 states that resource cleanup **MUST be safe to retry**. The architecture baseline states that cleanup must be idempotent at the protocol-observable level and proposes a mandatory cleanup TCK case.

The current base Fabric candidate set (`FABRIC-001..012`) does not explicitly own this new semantic. Existing `AVP-ENVIRONMENT-011` owns stale/released handle failure, while Core owns Task Verdict separation, but neither requirement states retry-safe/idempotent composite cleanup.

Leaving the text unchanged would create an untraceable normative MUST when the future requirement index is built.

**Required resolution:** choose one and record it explicitly:

1. add a base Fabric requirement family for release/cleanup retry safety and its observable semantics; or
2. remove/downgrade the new MUST if protocol-level idempotency is not intended to be portable.

Because the architecture and TCK strategy currently rely on observable retry safety, the recommended resolution is to add a dedicated candidate requirement rather than silently weaken the behavior.

### BR-003 — Resource Capability identity is not sufficiently drift-resistant

**Severity:** Proposed-state blocker  
**Affected assets:** AEP-0009 capability declaration section.

AEP-0009 says a capability is a namespaced identifier bound to a normative capability contract. The normative-gap audit further notes that a future declaration must bind enough profile/revision identity to prevent semantic drift under a stable name.

That drift-prevention rule is not yet explicit in the AEP direction.

A bare identifier such as `state.snapshot` cannot safely mean different mandatory behavior under two revisions without an explicit compatibility/version binding.

**Required resolution:** state in AEP-0009 that a Resource Capability Declaration is bound to a protocol/profile revision (or another reviewed semantic-version identity) sufficient to make the conformance obligations unambiguous. The exact serialized field names remain schema work.

### BR-004 — Required versus optional participation authority needs an explicit source

**Severity:** Proposed-state blocker  
**Affected assets:** AEP-0009 provision/capability sections; normative-gap audit Required/Optional Resource definitions.

The proposal repeatedly refers to resources required by the selected Scenario/profile, but it does not yet state the invariant strongly enough to prevent implementation availability from changing requiredness.

A backend must not turn a required resource/capability into an optional one because the backend lacks support, nor silently make an optional backend feature part of Scenario semantics because it happens to be present.

**Required resolution:** state that required/optional participation is derived from the materialized execution contract (ScenarioInstance plus the selected governed profile/capability requirements) and is immutable for that bound Fabric instance. Backend availability may satisfy or fail that contract; it may not rewrite it.

## Non-blocking deferred decisions

The following matters do **not** block `Proposed` because they belong to the subsequent normative specification/schema/TCK closure, provided the AEP keeps their boundaries explicit:

- exact JSON/YAML field names for the Fabric Manifest;
- exact canonicalization/digest rules if a protocol-level manifest digest is adopted;
- the final closed set of initial Resource Kind values;
- exact Resource Operation Result status/cause-code enumeration;
- exact aggregate restore-fidelity serialization;
- the semantics of any future stronger coordinated-atomicity capability;
- relational-state, browser, network-control, time-control, and OCI compute profile details;
- PostgreSQL/MySQL/Playwright/netem/container/microVM implementation mechanics;
- Alpha 3 release version selection;
- microVM conformance, which remains experimental/conditional.

Deferring these items does not permit backend code to define them by precedent.

## Proposed-state decision

**Decision: KEEP AEP-0009 IN `Draft`.**

The design direction is coherent and substantially reviewable, but BR-001 through BR-004 are protocol-contract inconsistencies that should be resolved before the proposal advertises `Proposed` maturity.

This decision is intentionally stricter than accepting green CI as protocol approval. Repository automation validates structural/project invariants; it does not replace protocol review.

## Required closure sequence

The next work unit is limited to proposal/design correction:

1. resolve BR-001 capability vocabulary and authorization separation;
2. resolve BR-002 cleanup retry-safety ownership;
3. resolve BR-003 capability revision/profile binding;
4. resolve BR-004 required/optional participation authority;
5. update this audit with exact resolution evidence;
6. run exact-head CI, Governance, and Release Validation;
7. only if all four blockers are closed, change AEP-0009 to `Proposed` and record the maintainer decision;
8. only after exact-head gates are green should PR #83 be considered for Ready-for-Review transition.

No step above authorizes merge, backend implementation, normative-spec merge, release selection, `v0.3.1`, package publication, signing/attestation, or a GitHub Release.

## Backend gate

The existing backend gate remains unchanged:

```text
AEP direction
  -> normative specification
  -> requirement index
  -> schema where serialized resources require it
  -> execution-sensitive TCK
  -> reference implementation
  -> vendor/backend adapters
```

Until AEP-0009 is accepted and the relevant authority-chain surfaces are reviewable, PostgreSQL/MySQL, Playwright, network-fault, time-control, OCI compute, and microVM work may be feasibility research only and must not define public AVP semantics.

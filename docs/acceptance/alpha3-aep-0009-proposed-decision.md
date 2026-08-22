# Alpha 3 — AEP-0009 Proposed Decision

Status: **PROPOSED — PROTOCOL REVIEW MAY BEGIN**  
AEP: `rfcs/AEP-0009-environment-fabric.md`  
Decision scope: AEP lifecycle transition from `Draft` to `Proposed` only.  
Authority: governance/acceptance record; this document does not make protocol text normative.

## Decision

AEP-0009 is advanced from `Draft` to `Proposed` because the Environment Fabric design is now sufficiently complete and internally consistent for protocol review under `GOVERNANCE.md`.

This decision means only:

> the proposal is mature enough for protocol review.

It does **not** mean the proposal is `Accepted` or `Final`, does not authorize backend implementation of new portable semantics, and does not authorize merge, release selection, publication, signing, attestation, or any tag.

## Live baseline

The decision was prepared against:

- `main@cdf56cf8e8d747f26b5438086ece3fb4cd489f31`;
- Draft PR #83, `docs/alpha3-environment-fabric`;
- stable published Alpha 2 source `7be045f47f59b259b32865be8b30005e4caa40f6`;
- repository source identity `avp-reference==0.3.1.dev0` in development mode.

No Alpha 3 release version is selected by this decision. The existing `0.3.1.dev0` maintenance-development identity is not reinterpreted as an Alpha 3 release vehicle.

## Readiness audit history

The first Proposed-readiness audit was intentionally blocking rather than ceremonial.

At head `0621c8d5cbc1ae6b75a345990d6c16613b9e4207`, `docs/acceptance/alpha3-aep-0009-proposed-readiness-audit.md` recorded four blockers:

- **BR-001 — capability vocabulary inconsistency**: AEP-0009 used `Fabric Capability` where the reviewed semantics required `Resource Capability`, distinct from existing `Subject Capability` authorization.
- **BR-002 — orphan cleanup MUST**: retry-safe cleanup was stated as portable mandatory behavior without an explicit candidate requirement owner.
- **BR-003 — capability semantic drift risk**: Resource Capability claims did not yet require a governed profile/revision identity sufficient to keep conformance obligations unambiguous.
- **BR-004 — requiredness authority ambiguity**: required versus optional resource/capability participation was not explicit enough to prevent backend availability from rewriting the materialized execution contract.

The audit decision was therefore correctly:

`BLOCKED — NOT READY TO ADVANCE TO PROPOSED`.

Green CI at that stage was not treated as protocol approval.

## Blocker resolutions

### BR-001 — CLOSED

AEP-0009 and the normative-gap audit now use **Resource Capability** for resource-level implementation support and preserve **Subject Capability** for Scenario/Security authorization.

The proposal explicitly states that Resource Capability support MUST NOT grant, expand, or substitute for Subject Capability authorization.

A future Fabric-level capability is reserved for genuinely cross-resource semantics rather than used as a synonym for ordinary resource support.

### BR-002 — CLOSED

Retry-safe cleanup was retained as a real portable composition semantic rather than weakened to remove a blocker.

The normative-gap audit now includes:

`FABRIC-013 — Retry-safe cleanup`.

The proposed observable behavior is bounded: repeating cleanup after successful release must not resurrect a resource, create a new authoritative resource under a stale reference, or initiate a new Subject-visible side effect solely because cleanup was retried. Cleanup failure remains infrastructure/validity information rather than Task Verdict.

### BR-003 — CLOSED

A Resource Capability Declaration now binds the capability identifier to a governed protocol/profile revision, or another reviewed semantic-version identity, sufficient to make applicable requirements and TCK obligations unambiguous.

A stable capability name cannot silently gain incompatible mandatory semantics while retaining an unchanged declaration identity.

Exact serialized revision fields remain downstream normative schema work.

### BR-004 — CLOSED

Required/optional participation is now derived from the **materialized execution contract**: the bound ScenarioInstance together with selected governed profile/capability requirements.

That classification is immutable for the lifetime of the bound Fabric instance. Backend availability may satisfy or fail the contract; it may not downgrade required behavior to optional or promote an available optional feature into required Scenario semantics.

## Closure commits and gate evidence

The blocker resolutions were recorded before the lifecycle transition:

- `2cfaadb634ebb66490d0007df566755283eb077e` — AEP-0009 blocker resolution;
- `5abb18e2b490616f0ea62a71bc769840ed30dfd1` — normative-gap audit closure.

The exact blocker-closure head `5abb18e2b490616f0ea62a71bc769840ed30dfd1` passed all required repository gates:

- **CI #488** — success;
- **Governance #525** — success;
- **Release Validation #39** — success.

CI evidence included successful Python 3.11/3.12/3.13 quality gates, reproducible distribution verification, built-wheel metadata validation, clean consumer installation, installed-wheel identity/smoke checks, installed-wheel full TCK conformance, and release-evidence build/verification.

Release Validation #39 also completed external-consumer validation successfully, including full TCK execution from the exact published stable source used by that workflow.

These gates establish repository integrity for the blocker-closure head. They do not by themselves accept AEP-0009.

## Lifecycle transition

After the four blockers were closed and the exact closure head gates were green, commit:

`32eb3cc8231eab405739e8d3ee86d3d38df617eb`

advanced the AEP metadata from:

`Status: Draft`

to:

`Status: Proposed`.

The AEP text simultaneously clarifies that `Proposed` is non-normative and does not authorize implementation of unaccepted portable semantics.

## Why Proposed is justified

The proposal now has the material required by AVP governance for protocol review:

1. a written interoperability problem and bounded scope;
2. explicit compatibility relationship with Environment/Core/Scenario/Security/Evidence;
3. documented rejected alternatives, including backend-first and universal-adapter designs;
4. explicit security analysis for privileged Fabric controls;
5. a language-neutral Resource Capability model with semantic revision binding;
6. a materialized-contract source of requiredness that cannot be rewritten by backend availability;
7. honest per-resource and aggregate result/fidelity/atomicity rules;
8. explicit retry-safe cleanup ownership;
9. a conformance strategy requiring real operation execution and negative same-metadata/broken-behavior implementations;
10. strict release/version separation.

The remaining open questions are suitable for protocol review and subsequent normative closure; they no longer make the proposal internally ambiguous at the Proposed boundary.

## What remains deliberately unresolved

`Proposed` does not freeze downstream serialization or domain profile details. Review may still change:

- exact Fabric Manifest field names and canonicalization rules;
- the final initial Resource Kind vocabulary;
- exact Resource/Composite Operation Result enums and cause codes;
- the serialization shape for Resource Capability revision/profile identity;
- any future coordinated cross-resource atomicity/consistency capability;
- relational-state, browser, network-control, time-control, and OCI compute profile semantics;
- microVM portability, which remains experimental/conditional;
- Alpha 3 release version selection.

These decisions must not be discovered by backend implementation precedent.

## Explicit non-authorizations

This decision does **not** authorize:

- changing AEP-0009 to `Accepted` or `Final`;
- merging PR #83;
- creating or merging an authoritative Fabric specification/requirement-index closure before the applicable governance boundary is satisfied;
- PostgreSQL, MySQL, Playwright, network-fault, virtual-time, OCI/container, or microVM reference/backend implementation for new portable Fabric semantics;
- selecting `0.3.1`, another Alpha 3 version, or a release candidate;
- creating tags or GitHub Releases;
- PyPI/package-index publication;
- signing or attestation publication.

Generic continuation instructions are not merge or release authorization.

## Next governed gate

The next stage is **protocol review of AEP-0009 as Proposed**.

The review should determine whether the direction can become `Accepted`. Acceptance requires an explicit recorded decision; it must not be inferred from green CI, absence of comments, or the passage of time.

Only after the proposal reaches the governance state required for implementation should the downstream authority chain proceed:

```text
Accepted AEP direction
  -> normative specification
  -> requirement index
  -> schema where serialized resources require it
  -> execution-sensitive TCK
  -> reference implementation
  -> vendor/backend adapters
```

## Final decision for this record

**AEP-0009: PROPOSED.**

**PR #83: remains Draft until the final decision-record head passes exact-head repository gates and is explicitly moved to review.**

**Environment Fabric backend implementation: NOT AUTHORIZED.**

**Alpha 3 release/version selection: NOT AUTHORIZED.**

# Alpha 3 — AEP-0009 Accepted Decision

Status: **ACCEPTED — NORMATIVE CLOSURE AUTHORIZED**  
AEP: `rfcs/AEP-0009-environment-fabric.md`  
Decision scope: AEP lifecycle transition from `Proposed` to `Accepted` only.  
Authority: protocol-maintainer governance decision; this record does not make downstream draft specification text Final.

## Decision

The protocol maintainer explicitly accepted the AEP-0009 Environment Fabric direction on 2026-08-23.

AEP-0009 is therefore advanced from `Proposed` to `Accepted`.

Under `GOVERNANCE.md`, `Accepted` means the direction is approved and downstream implementation work may proceed only through the governed authority chain required by the accepted design. For Alpha 3, that chain remains:

```text
Accepted AEP direction
  -> normative specification
  -> requirement index
  -> schema where serialized protocol resources require it
  -> execution-sensitive TCK
  -> reference implementation
  -> vendor/backend adapters
```

Acceptance does not make AEP-0009 `Final`; Final remains a later lifecycle boundary requiring merged normative text, required conformance coverage, and release evidence under repository governance.

## Accepted review baseline

The explicit acceptance follows the Proposed protocol review at exact head:

`d524e6e07cb4a8bbbed4347c4269d7cb8d00fa72`

The review result was:

`ACCEPTANCE-READY DIRECTION — explicit Accepted decision still required.`

No acceptance-blocking semantic conflict was found across Environment/Core/Scenario/Security/Evidence composition, compatibility, implementation neutrality, security boundaries, or execution-sensitive conformance strategy.

The accepted direction therefore includes these reviewed conclusions:

1. Environment Fabric is additive to Environment v0.1 and does not create a competing Environment ownership/reset/snapshot/restore/fault lifecycle.
2. Resource Capability is distinct from Subject Capability authorization; backend support cannot widen the materialized actor projection.
3. Resource Capability declarations bind governed semantic profile/revision identity so stable names cannot silently change mandatory meaning.
4. Required/optional resource and capability participation derives from the materialized execution contract and is immutable for the bound Fabric instance.
5. Backend availability may satisfy or fail requiredness; it may not rewrite required behavior as optional or silently promote optional behavior into Scenario semantics.
6. Composite operations preserve machine-readable per-resource outcomes.
7. Aggregate success cannot hide a required participant failure.
8. Aggregate restore fidelity cannot exceed the fidelity established by every required participating resource.
9. Composite success does not imply distributed atomicity; stronger cross-resource consistency/atomicity requires a separately governed capability with executable conformance evidence.
10. Retry-safe cleanup is a distinct base-Fabric candidate semantic (`FABRIC-013`) with bounded observable behavior.
11. SecurityAssurance remains the existing security-assurance model; Environment Fabric introduces no ordinal isolation level.
12. Evidence/Artifact exact-byte identity remains authoritative for retained verification bytes.
13. Mandatory conformance must execute implementation behavior; metadata-only capability self-certification is insufficient.
14. Domain backends remain conditional/profile implementations rather than base protocol authority.
15. Release/version selection remains separately governed.

## Proposed readiness history

The initial Proposed-readiness audit deliberately blocked advancement on four findings:

- BR-001 — Resource Capability / Subject Capability terminology and authorization separation;
- BR-002 — cleanup retry safety had no explicit candidate requirement owner;
- BR-003 — capability declaration identity was insufficiently protected from semantic drift;
- BR-004 — required/optional participation authority was insufficiently explicit.

All four were closed before the Proposed transition.

The exact blocker-closure head:

`5abb18e2b490616f0ea62a71bc769840ed30dfd1`

passed:

- CI #488 — success;
- Governance #525 — success;
- Release Validation #39 — success.

The final Proposed review head:

`d524e6e07cb4a8bbbed4347c4269d7cb8d00fa72`

passed:

- CI #490 — success;
- Governance #527 — success;
- Release Validation #41 — success.

Ready/metadata events subsequently passed Governance #528 and #529.

These green gates are integrity evidence for the reviewed proposal. The actual Proposed -> Accepted transition is authorized by the explicit protocol-maintainer decision, not inferred from CI.

## Acceptance effect

Acceptance authorizes the project to start the next governed Alpha 3 work unit:

1. draft the Environment Fabric normative specification;
2. create requirement-index traceability for the accepted Fabric requirement families;
3. define schemas only where the normative specification requires serialized protocol resources;
4. create a base Environment Fabric TCK with mandatory runtime-execution negative cases;
5. conduct a normative-closure audit that verifies the implementation is still downstream of the protocol authority chain;
6. only after those surfaces are reviewable, implement the reference composition layer;
7. only after the relevant domain profile semantics/schema/TCK exist, implement vendor/backend adapters.

Acceptance does **not** authorize skipping directly to PostgreSQL/MySQL, Playwright, network-fault, virtual-time, OCI/container, or microVM production/reference adapters.

## No-transitional-implementation decision

The user explicitly requires a high-quality open-source design and prohibits transitional implementation architecture.

The Accepted decision therefore preserves the AEP-0009 implementation gate:

- no PostgreSQL-shaped public abstraction that will be generalized later;
- no Playwright-shaped public browser model that will be renamed later;
- no giant Environment adapter with optional methods and scattered `supports_*` flags;
- no generic untyped `dict[str, Any]` substitute for known protocol resources;
- no compatibility shims for unreleased throwaway Alpha 3 layouts;
- no backend-name branches in language-neutral TCK semantics;
- no capability-table or fixture inspection as proof of conformance;
- no false `EXACT` restore claims;
- no global determinism claim hiding uncontrolled clocks/network/browser/external systems;
- no container/microVM label used as SecurityAssurance proof.

This is a long-term architecture constraint, not a temporary development preference.

## Non-authorizations

This Accepted decision does **not** authorize:

- merging PR #83 without explicit merge authorization;
- changing AEP-0009 to `Final`;
- selecting the Alpha 3 release version;
- assigning Alpha 3 to `0.3.1`;
- changing release-development mode;
- creating a tag or GitHub Release;
- PyPI/package-index publication;
- signing or attestation publication;
- treating any Python reference-runtime behavior as protocol authority;
- backend implementation before the corresponding portable contract/schema/TCK boundary is reviewable.

Stable `v0.3.0` remains the published Alpha 2 baseline. Repository source remains in `0.3.1.dev0` development mode until a separate release-management decision changes it.

## Next governed gate

The next gate is **Environment Fabric normative closure**, beginning with the specification and requirement index.

The initial accepted requirement-family drafting target is `FABRIC-001` through `FABRIC-013`, subject to precise normative wording and traceability review. The identifiers in the design audit are drafting targets until they are encoded in the reviewed requirement index.

Schema fields and TCK vectors must be derived from the specification; they must not define missing semantics on their own.

## Final decision

**AEP-0009: ACCEPTED.**

**Environment Fabric direction: APPROVED.**

**Normative specification / requirement-index work: AUTHORIZED.**

**Backend-first or transitional implementation: NOT AUTHORIZED.**

**PR #83 merge: NOT AUTHORIZED by this decision.**

**Alpha 3 release/version/publication: NOT AUTHORIZED.**

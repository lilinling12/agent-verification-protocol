# Repository and Product Boundaries

## Purpose

AVP is developed as an Alpha monorepo while protocol semantics are changing quickly. The monorepo is a coordination mechanism, not a statement that the protocol, TCK, reference implementation, benchmarks, and commercial platform are one product or one future repository.

The governing rule is:

> Specification defines semantics; schemas encode serializable contracts; conformance proves semantics; reference code implements semantics.

Repository organization, reference-backend mechanics, private platform behavior, or deployment convenience cannot override that rule.

## Open protocol ecosystem

| Surface | Current path | Authority | Expected long-term home |
|---|---|---|---|
| AVP Specification | `spec/` | Normative human-readable semantics | `avp-spec` |
| AVP Schemas | `schemas/` | Normative machine-readable contracts derived from spec | `avp-schema` |
| AVP TCK | `conformance/` | Conformance evidence derived from spec/schema | `avp-tck` |
| Reference Runtime | `runtime/`, code currently `src/avp_ref/` | Non-normative implementation | `avp-runtime` |
| Reference Adapters | `adapters/`, code currently `src/avp_ref/` | Non-normative integration | `avp-adapters` |
| AVS / Benchmarks | `benchmarks/` | Non-normative evaluation content | `avp-benchmarks` |
| Reference tests | `tests/` | Implementation quality only | runtime repository |

The public protocol ecosystem may contain more than the normative specification. Reference implementations, adapters, examples, public benchmark packs, compatibility evidence, and tooling can be open source while remaining explicitly non-normative.

## Open-source disclosure boundary

AVP is intended to support independent implementations. Therefore every semantic rule, state representation, failure condition, capability requirement, canonicalization rule, and conformance expectation required for portable interoperability MUST be publicly reviewable in the appropriate protocol/conformance surface before it is treated as a released AVP requirement.

The public repository MUST NOT rely on a private implementation, private service, unpublished decision table, hidden benchmark answer, proprietary prompt, or private corpus to determine whether an independent implementation is conformant.

This does **not** require publishing operationally sensitive material. The following are outside the public protocol authority and MUST NOT be committed merely to make the open project reproducible:

- real credentials, API tokens, private/signing keys, or production secrets;
- production or customer data, including copied traces/logs containing sensitive content;
- proprietary prompts, private evaluation corpora, or licensed datasets that cannot be redistributed;
- private DNS names, production addresses, internal topology, tenant identifiers, or infrastructure inventory;
- private deployment policies, commercial scheduling logic, cost models, or operational runbooks that do not affect portable AVP semantics;
- embargoed vulnerability/exploit details before coordinated disclosure is complete.

Public TCK fixtures and examples SHOULD use deterministic synthetic data and controlled local services where possible.

If a previously private implementation detail turns out to be necessary for independent interoperability or conformance, the project must choose one of two outcomes before release:

1. standardize and publish the required semantics/conformance artifact through normal protocol governance; or
2. remove the dependency from portable AVP conformance.

There is no valid third option in which a hidden private rule remains necessary for public AVP conformance.

## Commercial platform boundary

The Agent Verification Platform / Control Plane is a separate product layer. AVP conformance must not require hosted scheduling, enterprise environment provisioning, production mining, failure intelligence/RCA, dashboards, organization/RBAC management, hosted analytics, or private benchmark datasets.

Open interfaces may exist for interoperability, but those product capabilities are not protocol requirements.

A private/commercial implementation MAY implement an open AVP interface. Its internal algorithms, scaling architecture, operational data, and product policy MAY remain private provided they do not become hidden requirements for AVP interoperability or conformance.

Examples of private product surfaces include:

- large-scale experiment scheduling/control planes;
- managed browser/container/microVM fleets and capacity policies;
- enterprise credential brokers and tenant-management infrastructure;
- production trace mining and failure-intelligence systems;
- failure knowledge graphs and proprietary analysis models;
- private benchmark/evaluation datasets;
- commercial dashboards, billing, RBAC, quota, and hosted analytics.

## Dependency direction

Allowed conceptual direction:

```text
benchmarks --------┐
reference runtime -+--> schemas / specification
reference adapters-+
conformance -------┘

specification  -X-> reference runtime
schemas        -X-> Python-only models as authority
conformance    -X-> private platform internals
public protocol-X-> hidden private conformance rules
```

The reference implementation MAY depend on an implementation library such as a database driver or browser automation library. The normative specification and portable TCK MUST NOT depend on that library's private semantics unless AVP independently standardizes the relevant observable behavior.

## Repository policy relationship

Repository boundaries are project governance, not protocol semantics. The owning documents are:

- `GOVERNANCE.md` — decision rights and policy authority;
- this document — repository/product/open-source boundaries;
- `repository-boundaries.json` — machine-readable boundary declarations validated by CI;
- `docs/OPEN_SOURCE_ENGINEERING_STANDARD.md` — implementation and maintainability rules;
- `SECURITY.md` — vulnerability disclosure and sensitive security handling;
- `docs/REPOSITORY_SETTINGS.md` — target GitHub/repository enforcement controls.

When a boundary invariant can be checked safely and deterministically, the project SHOULD encode it in repository validation rather than relying only on reviewer memory.

## Alpha monorepo policy

1. Keep executable reference Python code in `src/avp_ref/` until a focused package migration is approved.
2. Do not add compatibility shims solely to preserve pre-release internal layouts.
3. Move executable code only in focused PRs with package/install/CI coverage.
4. Normative behavior introduced in code must be reconciled into `spec/` before being treated as protocol.
5. `tests/` is never the authority source for AVP semantics; formal conformance belongs under `conformance/`.
6. Benchmark scores must not substitute for conformance verdicts.
7. Commercial/private product code must not be added to this monorepo merely because it consumes AVP.
8. Public conformance must remain executable without access to private platform internals or private datasets.
9. Repository-policy changes must remain distinct from protocol-semantic changes unless a separately governed normative change genuinely requires both.

## Repository split trigger

A multi-repo split becomes appropriate when protocol compatibility is versioned, external implementations need spec/TCK without Python runtime, release cadences diverge, TCK needs independent provenance/release, or maintainership materially diverges. Until then, explicit boundaries plus automated checks avoid premature cross-repository version orchestration.

The expected long-term split recorded in `repository-boundaries.json` is directional, not a promise to create empty repositories before the split criteria are met.

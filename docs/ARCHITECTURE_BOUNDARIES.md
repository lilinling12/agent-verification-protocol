# Repository and Product Boundaries

## Purpose

AVP is developed as an Alpha monorepo while protocol semantics are changing quickly. The monorepo is a coordination mechanism, not a statement that the protocol, TCK, reference implementation, benchmarks, and commercial platform are one product or one future repository.

The governing rule is:

> Specification defines semantics; schemas encode serializable contracts; conformance proves semantics; reference code implements semantics.

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

## Commercial platform boundary

The Agent Verification Platform / Control Plane is a separate product layer. AVP conformance must not require hosted scheduling, enterprise environment provisioning, production mining, failure intelligence/RCA, dashboards, organization/RBAC management, hosted analytics, or private benchmark datasets.

Open interfaces may exist for interoperability, but those product capabilities are not protocol requirements.

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
```

## Alpha monorepo policy

1. Keep executable reference Python code in `src/avp_ref/` until a focused package migration is approved.
2. Do not add compatibility shims solely to preserve pre-release internal layouts.
3. Move executable code only in focused PRs with package/install/CI coverage.
4. Normative behavior introduced in code must be reconciled into `spec/` before being treated as protocol.
5. `tests/` is never the authority source for AVP semantics; formal conformance belongs under `conformance/`.
6. Benchmark scores must not substitute for conformance verdicts.

## Repository split trigger

A multi-repo split becomes appropriate when protocol compatibility is versioned, external implementations need spec/TCK without Python runtime, release cadences diverge, TCK needs independent provenance/release, or maintainership materially diverges. Until then, explicit boundaries plus automated checks avoid premature cross-repository version orchestration.

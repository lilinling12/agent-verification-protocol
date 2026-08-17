# AVP v0.1 Reconciliation

This directory contains the auditable bridge from the immutable historical Alpha v0.1 design baseline to current AVP authority.

Authority flows in one direction:

```text
Historical Design
    -> Reconciliation Decision / Disposition Evidence
    -> AEP/RFC
    -> Normative Specification
    -> Schema + TCK
    -> Reference Implementation
```

Historical design text, reconciliation notes, Python runtime behavior, implementation tests, benchmarks, product requirements, and private capabilities do not independently create protocol semantics.

## Global historical-design closure

The global closure artifacts are:

- [`HISTORICAL_DISPOSITION_LEDGER.md`](HISTORICAL_DISPOSITION_LEDGER.md) — human-readable disposition and rationale for every manifest-declared historical source and its material design areas.
- [`historical-disposition-ledger.json`](historical-disposition-ledger.json) — machine-readable closure record.
- `scripts/validate_historical_disposition.py` — fail-closed validator integrated into the repository quality gate.

The governed disposition vocabulary is:

`PROMOTED / SPLIT / SUPERSEDED / NON_NORMATIVE / DEFERRED / REJECTED`

`PROMOTED` is evidence-bearing: a promoted material area must reference current normative specification, current requirement IDs, and at least one current TCK profile. The ledger itself remains **non-normative reconciliation evidence** and cannot promote semantics merely by declaring a status.

A historical source may be `SPLIT` when its material areas have different outcomes. This is expected where the original Alpha design mixed portable protocol responsibilities with runtime, product, deployment, or methodology concerns.

## Promotion rule

Promotion of any historical intent requires, at minimum:

1. a stable requirement identity and semantic owner;
2. normative language review through the governed AEP/spec process;
3. explicit schema impact;
4. an implementation-independent conformance strategy;
5. security and trust-boundary analysis;
6. compatibility/versioning analysis.

See `DECISION_PROCESS.md` and the domain reconciliation decisions/matrices for detailed provenance.

## Current closure boundary

Global historical disposition does **not** establish stable-release readiness. The next gate is **Normative Surface Closure**, which audits `AEP ↔ spec ↔ requirement-index ↔ schema ↔ TCK` and resolves orphan authority surfaces before implementation-alignment and stable-eligibility audits.

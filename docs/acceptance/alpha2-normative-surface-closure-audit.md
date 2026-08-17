# Alpha 2 Normative Surface Closure Audit

Status: **BLOCKED — GOVERNANCE DISPOSITIONS REQUIRED**

Audit baseline: `main@c7a27f915bff2a5bdb045a9e6e30d099518fec57`

Machine-readable record: `docs/reconciliation/v0.1/normative-surface-matrix.json`

## Purpose

This audit checks whether current AVP protocol authority is closed across:

`lineage decision → normative spec → requirement index → schema impact → language-neutral TCK profile/cases`

It is acceptance evidence only. It does not create protocol semantics, promote a historical design area, or make the Python reference implementation authoritative.

## What is already closed

All 10 current specification domains have a requirement index and a registered TCK profile. Existing repository validators already enforce requirement-to-spec headings, requirement-to-schema references where declared, mandatory TCK coverage, profile/index equivalence, registry/case consistency, conditional triggers, and bidirectional requirement/case mappings.

AEP-0001 through AEP-0008 are Final under the explicit protocol-maintainer decision and released `v0.3.0-rc.1` evidence. Core and Evidence predate that AEP batch and retain explicit reconciliation lineage; this audit does not invent an AEP solely to normalize history.

## Blocking findings

### NSC-001 — Reliability report is an orphan authority surface

`schemas/reliability-report.schema.json` lives in the normative schema root, but no current reliability normative specification, requirement index, or TCK profile owns it. Historical reliability methodology is explicitly deferred. `src/avp_ref/reliability.py` is reference behavior and cannot supply missing protocol authority.

Required disposition: governed promotion through the normal protocol lifecycle, or explicit non-normative relocation/reclassification/removal. No choice is made by this audit.

### NSC-002 — AVP event schema has no current requirement owner

`schemas/avp-event.schema.json` is not declared as schema impact by any current requirement index. Its broad event/evidence shape therefore cannot be treated as normative merely because it remains under `schemas/`.

Required disposition: establish a governed current owner or explicitly retire/reclassify the surface.

### NSC-003 — AVP core resource envelope has no current requirement owner

Core requirements declare `schemas/episode-lifecycle.schema.json`; they do not declare `schemas/avp-core.schema.json`. The latter enumerates a broad set of resource kinds beyond the current Core lifecycle requirement surface.

Required disposition: establish explicit normative ownership or retire/reclassify the envelope.

### NSC-004 — Scenario schema has ambiguous duplicate identity

`schemas/scenario.schema.json` is byte-identical to `schemas/scenario-template.schema.json`, while the Scenario requirement index explicitly owns the latter plus `scenario-instance.schema.json`. The reference compiler also consumes the explicitly named template/instance schemas.

Required disposition: explicitly define a canonical alias/deprecation policy or remove/relocate the duplicate. The audit does not infer alias semantics from byte equality alone.

### NSC-005 — Requirement-index authority metadata is stale/undefined

Current requirement indexes use `status: draft-normative-candidate`. Eight governing AEPs are now Final and their normative text/conformance were included in the published RC evidence, while Core and Evidence use earlier reconciliation lineage. The repository has no explicit requirement-index lifecycle vocabulary that would justify blindly replacing every status with `Final`.

Required disposition: define the status vocabulary and its relationship to AEP/spec release state, then apply it deliberately by domain.

## Non-findings

The audit does **not** classify lack of a dedicated root JSON Schema as a defect for Environment, MCP, OpenTelemetry, or Subject. A requirement may be behavioral and language-neutral without requiring a new AVP-owned wire schema, particularly where upstream protocols retain wire authority.

The audit also does not require every domain to have an AEP. Core and Evidence have explicit accepted reconciliation decisions and current normative spec/TCK surfaces; historical lineage differences are recorded instead of rewritten.

## Closure decision

**Normative Surface Closure is not ready to close. Stable `v0.3.0` remains blocked.**

The five blockers above require explicit governance/protocol dispositions. The machine validator intentionally accepts this truthful `BLOCKED` state while failing closed if inventory, ownership evidence, blocker linkage, Final-AEP claims, alias equality, or closure-state rules drift.

A future closure change may set the matrix to `READY` only after every blocker is resolved through the appropriate governed path and the exact-head quality/governance checks pass.

## Next work after this audit is accepted

Resolve the blockers in separate, reviewable changes. Semantic promotions require the AEP/spec/schema/TCK lifecycle; non-normative retirement/relocation and metadata vocabulary work should remain narrowly scoped. Only after Normative Surface Closure reaches `READY` should AVP proceed to the reference implementation alignment audit and then stable-release eligibility.

# Alpha 2 Normative Surface Closure Audit

Status: **BLOCKED — GOVERNANCE DISPOSITIONS REQUIRED**

Current audit baseline: `main@90d24ee2f9fef66a26872fba4853dcf917b507b5`

Machine-readable record: `docs/reconciliation/v0.1/normative-surface-matrix.json`

## Purpose

This audit checks whether current AVP protocol authority is closed across:

`lineage decision → normative spec → requirement index → schema impact → language-neutral TCK profile/cases`

It is acceptance evidence only. It does not create protocol semantics, promote a historical design area, or make the Python reference implementation authoritative.

## What is already closed

All 10 current specification domains have a requirement index and a registered TCK profile. Existing repository validators enforce requirement-to-spec headings, requirement-to-schema references where declared, mandatory TCK coverage, profile/index equivalence, registry/case consistency, conditional triggers, and bidirectional requirement/case mappings.

AEP-0001 through AEP-0008 are Final under the explicit protocol-maintainer decision and released `v0.3.0-rc.1` evidence. Core and Evidence predate that AEP batch and retain explicit reconciliation lineage; this audit does not invent an AEP solely to normalize history.

## Resolved findings

### NSC-001 — orphan Reliability report schema retired

`schemas/reliability-report.schema.json` had no normative reliability specification, requirement index, or TCK profile owner. Historical reconciliation explicitly classifies portable reliability/statistical methodology as `DEFERRED` and the current Python reliability helper as `NON_NORMATIVE`.

Disposition: **retire the orphan schema from the normative `schemas/` root rather than manufacture protocol authority around it**. No reliability AEP, normative requirement, schema replacement, or TCK profile is created. `src/avp_ref/reliability.py` remains reference-only behavior and is unchanged.

The retirement is also consistent with the concrete repository surfaces: the orphan schema described a report envelope requiring fields such as `report_version`, `experiment_id`, `valid_episodes`, and `metrics`, while the Python helper exposes a different implementation-oriented `ReliabilityReport` shape. That mismatch is evidence that neither surface can legitimately define the other. Protocol semantics therefore remain one-way from governed normative authority, not from the Python implementation.

Historical reconciliation evidence is updated to stop treating the retired path as a live repository artifact while retaining the `DEFERRED` / `NON_NORMATIVE` dispositions. The normative-surface matrix removes NSC-001 only after the root schema itself is removed.

### NSC-004 — duplicate Scenario schema alias retired

`schemas/scenario.schema.json` was byte-identical to the requirement-owned `schemas/scenario-template.schema.json`, but no current requirement declared the duplicate path. The packaged reference-resource copy was likewise unused by the Scenario loader, which explicitly loads `scenario-template.schema.json` and `scenario-instance.schema.json`.

Disposition: **remove the duplicate rather than manufacture a compatibility contract**. Both `schemas/scenario.schema.json` and `src/avp_ref/resources/scenario.schema.json` are retired. `schemas/scenario-template.schema.json` remains the sole canonical ScenarioTemplate schema named by `AVP-SCENARIO-003`; the reference loader behavior is unchanged. This is authority-surface cleanup, not a protocol semantic change.

The normative-surface validator continues to derive the exact root-schema inventory from the repository. Reintroducing an unclassified duplicate would therefore fail the audit unless it received an explicit governed disposition.

## Remaining blocking findings

### NSC-002 — AVP event schema has no current requirement owner

`schemas/avp-event.schema.json` is not declared as schema impact by any current requirement index. Its broad event/evidence shape cannot be treated as normative merely because it remains under `schemas/`.

Required disposition: establish a governed current owner or explicitly retire/reclassify the surface.

### NSC-003 — AVP core resource envelope has no current requirement owner

Core requirements declare `schemas/episode-lifecycle.schema.json`; they do not declare `schemas/avp-core.schema.json`. The latter enumerates a broad set of resource kinds beyond the current Core lifecycle requirement surface.

Required disposition: establish explicit normative ownership or retire/reclassify the envelope.

### NSC-005 — Requirement-index authority metadata is stale/undefined

Current requirement indexes use `status: draft-normative-candidate`. Eight governing AEPs are Final and their normative text/conformance were included in the published RC evidence, while Core and Evidence use earlier reconciliation lineage. The repository has no explicit requirement-index lifecycle vocabulary that would justify blindly replacing every status with `Final`.

Required disposition: define the status vocabulary and its relationship to AEP/spec release state, then apply it deliberately by domain.

## Non-findings

The audit does **not** classify lack of a dedicated root JSON Schema as a defect for Environment, MCP, OpenTelemetry, or Subject. A requirement may be behavioral and language-neutral without requiring a new AVP-owned wire schema, particularly where upstream protocols retain wire authority.

The audit also does not require every domain to have an AEP. Core and Evidence have explicit accepted reconciliation decisions and current normative spec/TCK surfaces; historical lineage differences are recorded instead of rewritten.

## Closure decision

**Normative Surface Closure is not ready to close. Stable `v0.3.0` remains blocked.**

NSC-001 and NSC-004 are closed by retiring unowned schema surfaces rather than inventing compatibility or normative semantics. Three blockers remain: NSC-002, NSC-003, and NSC-005. The machine validator intentionally accepts this truthful `BLOCKED` state while failing closed if inventory, ownership evidence, blocker linkage, Final-AEP claims, or closure-state rules drift.

A future closure change may set the matrix to `READY` only after every remaining blocker is resolved through the appropriate governed path and the exact-head quality/governance checks pass.

## Next work

Resolve the remaining blockers in separate, reviewable changes. Semantic promotions require the AEP/spec/schema/TCK lifecycle; non-normative retirement/relocation and metadata-vocabulary work must remain narrowly scoped. Only after Normative Surface Closure reaches `READY` should AVP proceed to the reference implementation alignment audit and then stable-release eligibility.
# Alpha 2 Normative Surface Closure Audit

Status: **BLOCKED — GOVERNANCE DISPOSITIONS REQUIRED**

Current audit baseline: `main@77c5c0a90897c9eb25156ef8e8c4a17a9dddb147`

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

### NSC-002 — legacy AVP event root schema retired

`schemas/avp-event.schema.json` had no current requirement-index owner. The historical Evidence reconciliation already records that the legacy event schema's loose `payload_ref` / `evidence` reference shapes are not safely interchangeable with the governed ArtifactRef/Evidence model. The current Evidence requirement index therefore names `schemas/artifact-ref.schema.json` and `schemas/evidence.schema.json`, not the legacy event schema.

The OpenTelemetry profile does govern **event correlation semantics**: `AVP-OTEL-002` requires preservation of event identity, event type, and Episode-local ordering when events are mapped to telemetry. It deliberately does not define a universal AVP event wire object, and its language-neutral TCK case checks those observable correlation properties without depending on `schemas/avp-event.schema.json`.

The Python `AVPEvent` value object is also not used as replacement authority. Its implementation shape differs from the retired root schema (for example, the root schema required `schema_version` and `observed_at`, while the reference value object does not expose those fields). NSC-002 therefore **retires the unowned root schema rather than changing protocol semantics to match either legacy schema or Python code**.

Disposition: remove `schemas/avp-event.schema.json`; remove it from historical promoted-schema evidence; preserve current Evidence and OpenTelemetry normative requirements/TCK unchanged; leave reference-runtime event behavior unchanged. No new AEP, normative requirement, schema replacement, or TCK expectation is created by this cleanup.

### NSC-003 — legacy AVP core resource envelope retired

`schemas/avp-core.schema.json` described a broad `apiVersion` / `kind` / `metadata` resource envelope spanning `ScenarioTemplate`, `ScenarioInstance`, `Benchmark`, `EnvironmentManifest`, `AgentSystem`, `EpisodeManifest`, `OracleBundle`, `MutationSet`, `FaultProfile`, and `ReleasePolicy`. The current Core requirement index does not own that envelope; it owns `schemas/episode-lifecycle.schema.json` only where lifecycle transition-record shape is required.

The accepted Core reconciliation decision standardizes semantic Episode lifecycle phases and explicitly limits JSON Schema authority to lifecycle transition-record shape. It does not establish a universal AVP resource-kind registry or generic metadata envelope. Historical umbrella protocol responsibilities were likewise split across narrower authority domains, and the historical disposition ledger records `schemas/episode-lifecycle.schema.json`—not `schemas/avp-core.schema.json`—as promoted Core schema evidence.

Current domain schemas that use `apiVersion`, `kind`, or `metadata` define those fields directly under their own governed contracts. In particular, ScenarioTemplate and ScenarioInstance each declare their own exact `kind` and metadata requirements rather than inheriting from the legacy envelope. The reference wheel does not package `avp-core.schema.json` as a runtime schema resource.

Disposition: **retire the unowned generic envelope rather than backfill a new Core owner or infer a cross-domain resource model from legacy structure**. This closes an authority-surface ambiguity without changing Core lifecycle semantics, any requirement index, any TCK expectation, or the Python reference runtime.

### NSC-004 — duplicate Scenario schema alias retired

`schemas/scenario.schema.json` was byte-identical to the requirement-owned `schemas/scenario-template.schema.json`, but no current requirement declared the duplicate path. The packaged reference-resource copy was likewise unused by the Scenario loader, which explicitly loads `scenario-template.schema.json` and `scenario-instance.schema.json`.

Disposition: **remove the duplicate rather than manufacture a compatibility contract**. Both `schemas/scenario.schema.json` and `src/avp_ref/resources/scenario.schema.json` are retired. `schemas/scenario-template.schema.json` remains the sole canonical ScenarioTemplate schema named by `AVP-SCENARIO-003`; the reference loader behavior is unchanged. This is authority-surface cleanup, not a protocol semantic change.

The normative-surface validator continues to derive the exact root-schema inventory from the repository. Reintroducing an unclassified duplicate, retired event schema, reliability schema, or generic core envelope would therefore fail the audit unless it received an explicit governed disposition.

## Remaining blocking findings

### NSC-005 — Requirement-index authority metadata is stale/undefined

Current requirement indexes use `status: draft-normative-candidate`. Eight governing AEPs are Final and their normative text/conformance were included in the published RC evidence, while Core and Evidence use earlier reconciliation lineage. The repository has no explicit requirement-index lifecycle vocabulary that would justify blindly replacing every status with `Final`.

Required disposition: define the status vocabulary and its relationship to AEP/spec release state, then apply it deliberately by domain.

## Non-findings

The audit does **not** classify lack of a dedicated root JSON Schema as a defect for Environment, MCP, OpenTelemetry, or Subject. A requirement may be behavioral and language-neutral without requiring a new AVP-owned wire schema, particularly where upstream protocols retain wire authority.

The audit also does not require every domain to have an AEP. Core and Evidence have explicit accepted reconciliation decisions and current normative spec/TCK surfaces; historical lineage differences are recorded instead of rewritten.

## Closure decision

**Normative Surface Closure is not ready to close. Stable `v0.3.0` remains blocked.**

NSC-001, NSC-002, NSC-003, and NSC-004 are closed by retiring unowned authority surfaces rather than manufacturing missing protocol ownership or deriving semantics from implementation behavior. One blocker remains: NSC-005. The machine validator intentionally accepts this truthful `BLOCKED` state while failing closed if inventory, ownership evidence, blocker linkage, Final-AEP claims, or closure-state rules drift.

A future closure change may set the matrix to `READY` only after NSC-005 is resolved through the governed authority-metadata path and the exact-head quality/governance checks pass.

## Next work

Resolve NSC-005 as a separate, reviewable authority-metadata change. Only after Normative Surface Closure reaches `READY` should AVP proceed to the reference implementation alignment audit and then stable-release eligibility.

# Alpha 2 Normative Surface Closure Audit

Status: **READY — NORMATIVE SURFACE CLOSED**

Current audit baseline: `main@d8d6c594d6295b98a215db8b18384ffa88a4085e`

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

### NSC-005 — requirement-index authority status defined

The previous `status: draft-normative-candidate` value was used by every domain requirement index without a defined lifecycle distinct from AEP and release state. That made authority metadata ambiguous after eight governing AEPs became Final while Core and Evidence continued to use accepted reconciliation lineage.

Disposition: **define requirement-index authority metadata independently instead of copying AEP lifecycle values**. The requirement-index vocabulary is now:

- `draft-normative-candidate` — a governed candidate requirement set that is not yet the current accepted machine-readable requirement authority for its domain;
- `normative` — the current machine-readable normative requirement authority for a domain, backed by recorded accepted lineage and its normative specification/conformance surface.

All ten current domain requirement indexes are `normative`. Eight domains are backed by Final AEPs; Core and Evidence remain backed by their accepted reconciliation decisions. This deliberately does not manufacture AEPs for historical normalization.

`normative` is not a synonym for AEP `Final`, TCK profile maturity, stable release readiness, or repository-wide Normative Surface Closure. This disposition therefore does **not** authorize stable `v0.3.0` by itself.

The normative-surface validator rejects unknown requirement-index statuses, requires NSC-005 whenever any requirement index remains `draft-normative-candidate`, and rejects a stale NSC-005 blocker when all requirement indexes are `normative`. No requirement statement, schema ownership, TCK expectation, or reference-runtime behavior changes in this disposition.

## Remaining blocking findings

None. NSC-001 through NSC-005 have explicit governed dispositions and no unresolved root-schema authority classification remains.

## Non-findings

The audit does **not** classify lack of a dedicated root JSON Schema as a defect for Environment, MCP, OpenTelemetry, or Subject. A requirement may be behavioral and language-neutral without requiring a new AVP-owned wire schema, particularly where upstream protocols retain wire authority.

The audit also does not require every domain to have an AEP. Core and Evidence have explicit accepted reconciliation decisions and current normative spec/TCK surfaces; historical lineage differences are recorded instead of rewritten.

## Closure decision

**Normative Surface Closure is READY.**

NSC-001, NSC-002, NSC-003, and NSC-004 are closed by retiring unowned authority surfaces rather than manufacturing missing protocol ownership or deriving semantics from implementation behavior. NSC-005 is closed by defining an explicit requirement-index authority vocabulary and applying `normative` to all ten current domain indexes without changing requirement semantics.

The machine-readable matrix therefore has zero blockers and `closure_status: READY`. The validator fails closed if blockers reappear, schema/domain/profile inventories drift, lineage claims are invalid, requirement-index authority metadata becomes ambiguous, or zero-blocker/closure state becomes inconsistent.

`READY` here is a **Normative Surface Closure** decision only. It does not itself authorize a stable `v0.3.0` release and does not make reference implementation behavior normative. Repository merge eligibility still requires the normal exact-head CI/Governance evidence.

## Next work

Proceed to the **Reference Runtime Alignment Audit**. That audit must verify the reference runtime against the already-governed normative surface without allowing Python behavior to redefine protocol semantics. Stable-release eligibility remains a later, separate decision after runtime alignment evidence is complete.

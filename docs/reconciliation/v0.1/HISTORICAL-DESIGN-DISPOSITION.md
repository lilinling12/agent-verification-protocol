# Historical Design Disposition Ledger v0.1

Status: **Draft closure artifact — Gate B**

Baseline: `avp-design-alpha-v0.1`

Historical source authority: `docs/design/alpha-v0.1/SOURCE-MANIFEST.json`

Current authority direction:

```text
historical design
    -> reconciliation
    -> AEP / normative specification
    -> schemas
    -> language-neutral conformance / TCK
    -> reference implementation
```

## 1. Purpose

This ledger closes the repository-level question: **what happened to every material Alpha v0.1 historical design area?**

The restored documents under `docs/design/alpha-v0.1/` are immutable provenance and remain explicitly non-normative. This ledger does not promote historical wording merely by referencing it. A historical idea is current AVP protocol semantics only when the governed current surface establishes that semantics through reconciliation/AEP/specification and its downstream conformance assets.

This document is intentionally broader than an implementation audit. It records disposition of historical intent before the separate AEP/spec/schema/TCK/reference-runtime alignment audit.

## 2. Disposition vocabulary

| Disposition | Meaning |
|---|---|
| `PROMOTED` | The historical responsibility is retained as current governed normative behavior. Current specification is authoritative; historical wording is not. |
| `SPLIT` | The historical document mixed responsibilities that now belong to multiple current normative and/or non-normative surfaces. |
| `SUPERSEDED` | A later governed design replaced the historical shape, taxonomy, interface, or process while preserving only intentionally selected intent. |
| `NON_NORMATIVE` | The area is intentionally architecture, methodology, tooling, SDK, product, implementation, or ecosystem guidance rather than AVP protocol semantics. |
| `DEFERRED` | The area is intentionally not part of the current normative protocol/profile set and requires a future governed phase before standardization. |
| `REJECTED` | The historical proposal is intentionally not carried forward. No current item in this ledger requires this disposition. |

A document-level disposition is a closure summary, not a claim that every section has the same fate. `SPLIT` documents therefore identify the major section groups separately.

## 3. Current governed normative inventory

The current human-readable normative entry point is `spec/README.md`. The registered profile/domain set used by this ledger is:

| Current profile/domain | Governed evidence |
|---|---|
| `avp-core-v0.1` | `spec/core/`, `spec/core/requirement-index.yaml`, `conformance/tck/profiles/avp-core-v0.1.yaml` |
| `avp-scenario-v0.1` | AEP-0003, `spec/scenario/`, `spec/scenario/requirement-index.yaml`, Scenario TCK |
| `avp-environment-v0.1` | AEP-0004, `spec/environment/`, `spec/environment/requirement-index.yaml`, Environment TCK |
| `avp-evidence-v0.1` | `spec/evidence/`, `spec/evidence/requirement-index.yaml`, Evidence TCK |
| `avp-oracle-v0.1` | AEP-0001, `spec/oracle/`, `spec/oracle/requirement-index.yaml`, Oracle TCK |
| `avp-security-v0.1` | AEP-0002, `spec/security/`, `spec/security/requirement-index.yaml`, Security TCK |
| `avp-mcp-interop-v0.1` | AEP-0005, `spec/mcp/`, `spec/mcp/requirement-index.yaml`, MCP TCK |
| `avp-otel-mapping-v0.1` | AEP-0006, `spec/opentelemetry/`, `spec/opentelemetry/requirement-index.yaml`, OTel TCK |
| `avp-subject-v0.1` | AEP-0007, `spec/subject/`, `spec/subject/requirement-index.yaml`, Subject TCK |
| `avp-artifact-trust-v0.1` | AEP-0008, `spec/trust/`, `spec/trust/requirement-index.yaml`, Artifact Trust TCK |

The presence of a current domain does not imply that every historical section with a similar name was promoted.

## 4. Global document disposition

| Historical source | Primary disposition | Current destination / closure |
|---|---|---|
| `03-agent-verification-protocol.md` | `SPLIT` | Core lifecycle/replay/result separation moved to Core; Scenario, Environment, Evidence, Oracle, Security, Subject, Trust, MCP and OTel responsibilities were decomposed into governed domains. Historical control-plane/product/package/roadmap and reference-binding choices are not Core semantics. |
| `04-scenario-benchmark-dsl.md` | `SPLIT` | ScenarioTemplate/ScenarioInstance materialization, identity, immutability, projection, capability and reference binding are governed by AEP-0003 / Scenario. Authoring DSL syntax, mutation engine, coverage/difficulty, benchmark packaging and experiment hints remain non-normative or deferred. |
| `05-unified-trace-schema.md` | `SPLIT` | Verification correlation and telemetry responsibility is governed by AEP-0006 / OTel and Evidence identity/integrity; W3C Trace Context/OpenTelemetry remain external authorities. The historical universal event taxonomy is not automatically a normative replacement for OTel/CloudEvents/MCP/A2A semantics. |
| `06-system-architecture.md` | `SPLIT` | Portable contract concepts contributed to Environment, Oracle, Security, Subject, MCP and OTel domains. Service topology, schedulers, storage, Kubernetes, multi-tenancy, SRE, cost model, open-core and commercial control-plane architecture are intentionally non-normative. |
| `07-environment-fabric.md` | `SPLIT` | Evaluator ownership, reset/time, observation/projection, snapshot/restore, diff, fault and stale-handle semantics are governed by AEP-0004 / Environment. Runtime tiers, concrete provisioning technology, determinism scores and operational KPIs are non-normative. |
| `08-verification-engine.md` | `SPLIT` | Oracle execution/evaluation separation, failure validity, evidence integrity and audit are governed by AEP-0001 / Oracle plus Evidence/Core/Security. Judge ensembles, gold-set process, caching, product routing and evaluator CI/CD methodology remain non-normative unless separately governed. |
| `09-failure-intelligence.md` | `NON_NORMATIVE` | RCA taxonomy, clustering, first-bad-step localization, knowledge graphs, confidence updating and recommendation workflows are methodology/product capabilities. Core replay identity exists, but it does not standardize historical RCA semantics. |
| `10-reliability-statistics.md` | `DEFERRED` | Statistical methodology remains useful informative material, but there is no current `avp-reliability-*` normative profile. A future reliability/statistics profile requires its own reconciliation/AEP/spec/TCK lifecycle. |
| `11-conformance-test-spec.md` | `SUPERSEDED` | The historical certification taxonomy/test IDs were replaced by the current language-neutral `conformance/tck/` registry, profile schemas, runner contract and requirement-linked cases. The principle “test normative requirements, not Python behavior” is retained. |
| `12-open-source-governance.md` | `SUPERSEDED` | Current `GOVERNANCE.md`, AEP lifecycle, `docs/RELEASE_PROCESS.md`, repository rules and architecture boundaries are authoritative. Historical working-group/release/registry proposals do not override current governance. |
| `13-reference-runtime-design.md` | `NON_NORMATIVE` | Reference-runtime architecture belongs to `src/avp_ref/`, `runtime/` and implementation tests. It provides evidence only and cannot define protocol semantics backward. |
| `14-avp-sdk-contract.md` | `NON_NORMATIVE` | SDK/client/provider APIs and language-specific design are implementation/ecosystem surfaces. Portable protocol models may reflect normative schemas, but SDK method shape and language lifecycle are not protocol requirements. |
| `15-package-registry-spec.md` | `DEFERRED` | A mandatory AVP package/registry network is not part of current Core conformance. Artifact identity/trust concepts that became protocol-relevant are separately governed by Evidence and AEP-0008 / Artifact Trust; registry APIs and ecosystem packaging require future governance. |
| `16-security-threat-model.md` | `SPLIT` | Capability/secret/hidden-material/fault-secrecy and assurance-honesty requirements are governed by AEP-0002 / Security; artifact authentication/trust-policy responsibilities are governed by AEP-0008 / Trust. Threat examples, maintenance process and product hardening remain informative. |
| `17-oracle-sdk.md` | `SPLIT` | Oracle identity, declared input scope, input integrity, failure separation, evidence integrity and execution audit are governed by AEP-0001 / Oracle. Python interfaces, helper APIs, package shape and concrete sandbox implementation are non-normative. |
| `18-local-runner-cli.md` | `NON_NORMATIVE` | CLI commands, human output, exit codes, local dev server and inspect UX are tooling behavior. TCK runner interoperability is governed separately by the language-neutral runner contract, not by this historical CLI shape. |
| `19-mcp-adapter.md` | `SPLIT` | MCP revision/capability/baseline/schema/call/outcome/feature-honesty verification is governed by AEP-0005 / MCP while MCP remains external protocol authority. Adapter caching, fault harness implementation and concrete transport plumbing remain non-normative. |
| `20-opentelemetry-mapping.md` | `SPLIT` | Root/event/tool correlation, outcome preservation, W3C propagation, minimization, completeness and Evidence composition are governed by AEP-0006 / OTel. SDK/exporter/collector implementation and any obsolete semantic-convention detail are non-normative. |
| `21-alpha-implementation-plan.md` | `NON_NORMATIVE` | Historical implementation sequencing and Alpha-quality planning are provenance only. They do not constrain current protocol lifecycle or release readiness. |
| `ADR-001-scope-and-boundaries.md` | `NON_NORMATIVE` | Preserved architecture provenance. Current authority boundaries are expressed by `docs/ARCHITECTURE_BOUNDARIES.md`, `GOVERNANCE.md`, reconciliation assets and current specs. |

## 5. Detailed split mappings

### 5.1 Document 03 — Agent Verification Protocol

**Primary disposition: `SPLIT`.**

| Historical responsibility | Disposition | Current governed destination |
|---|---|---|
| Core terms: Episode, lifecycle state, result/validity separation | `PROMOTED` | `spec/core/episode-lifecycle.md`; AVP-CORE-001..012; Core TCK |
| ScenarioTemplate / ScenarioInstance identity and immutability | `PROMOTED` | AEP-0003; `spec/scenario/scenario-contract.md`; AVP-SCENARIO-001..009 |
| Environment reset, observation, snapshot, restore, diff, fault | `PROMOTED` | AEP-0004; `spec/environment/environment-contract.md`; AVP-ENVIRONMENT-001..011 |
| Evidence identity/integrity | `PROMOTED` | `spec/evidence/evidence-artifact-identity.md`; AVP-EVIDENCE-001..008 |
| Oracle evaluation and validity | `PROMOTED` | AEP-0001; `spec/oracle/oracle-evaluation-contract.md`; AVP-ORACLE-001..007 |
| Subject/Evaluator capability and hidden-material boundary | `PROMOTED` | AEP-0002 and AEP-0007; Security + Subject profiles |
| Artifact authentication/trust-policy/publication authority | `SUPERSEDED` | Historical generic trust ideas replaced by AEP-0008 / `spec/trust/` governed contract |
| MCP verification relationship | `SUPERSEDED` | AEP-0005 / `spec/mcp/`; MCP remains external authority |
| OpenTelemetry/W3C relationship | `SUPERSEDED` | AEP-0006 / `spec/opentelemetry/`; OTel/W3C remain external authorities |
| Control plane, package model, HTTP reference binding, standardization roadmap | `NON_NORMATIVE` | Product/implementation/governance concerns unless separately governed |

### 5.2 Document 04 — Scenario Benchmark DSL

**Primary disposition: `SPLIT`.**

`PROMOTED`: Template-vs-Instance separation, deterministic materialization inputs, execution identity, immutability, actor capability projection, evaluator-only visibility separation and resolved reference binding → AEP-0003 / AVP-SCENARIO-001..009.

`NON_NORMATIVE`: concrete authoring syntax, convenience generators, mutation engine implementation, coverage scoring, difficulty scoring, experiment hints and benchmark-resource UX.

`DEFERRED`: any future portable benchmark-authoring DSL, mutation/metamorphic profile, solvability profile or benchmark-pack standard must be proposed separately; current Scenario conformance does not imply them.

### 5.3 Document 05 — Unified Trace & Verification Event Schema

**Primary disposition: `SPLIT`.**

`PROMOTED`: integrity-bound Evidence references and AVP verification correlation responsibilities.

`SUPERSEDED`: trace propagation and telemetry mapping are now governed by AEP-0006 / AVP-OTEL-001..008 and must preserve W3C Trace Context/OpenTelemetry authority rather than establishing a private AVP tracing protocol.

`NON_NORMATIVE`: derived metrics, storage/retention mechanics, collector design and implementation-specific event capture.

`DEFERRED`: event types or cross-protocol mappings not represented by a current requirement index must not be treated as normative solely because `schemas/avp-event.schema.json` or runtime event code exists. The later alignment audit must verify this boundary explicitly.

### 5.4 Document 06 — System Architecture

**Primary disposition: `SPLIT`.**

Portable semantics were extracted only where they could be stated as implementation-independent contracts. The following are **not** protocol requirements: service decomposition, orchestration technology, runtime tier implementation, object/analytical stores, semantic indexes, Kubernetes topology, tenancy model, SRE targets, cost model, build-vs-integrate choices, commercial release gates and open-core packaging.

Any runtime behavior used as evidence for Environment/Oracle/Subject/Security/MCP/OTel remains downstream of those specs.

### 5.5 Document 07 — Environment Fabric

**Primary disposition: `SPLIT`.**

`PROMOTED`: evaluator ownership, Scenario binding, reset semantics, logical time, actor-scoped observation, evaluator projection identity, snapshot/restore claim honesty, StateDiff binding, fault control and stale-handle failure → AEP-0004 / AVP-ENVIRONMENT-001..011.

`NON_NORMATIVE`: L0–L4 implementation tiers, concrete browser/container/microVM/VM provisioning, infrastructure scoring and environment operational KPIs.

### 5.6 Document 08 — Verification Engine

**Primary disposition: `SPLIT`.**

`PROMOTED`: declared Oracle identity and inputs, failure/task separation, result validity, Evidence integrity and execution audit → AEP-0001 / AVP-ORACLE-001..007 plus Evidence/Core.

`NON_NORMATIVE`: Judge routing, ensemble strategy, gold-set process, cache topology, verification DAG execution engine, human-adjudication workflow and evaluator deployment process.

Any semantic-judge/LLM-judge standardization remains deferred unless a future AEP introduces portable requirements.

### 5.7 Document 16 — Security Threat Model

**Primary disposition: `SPLIT`.**

`PROMOTED`: Subject/Evaluator capability separation, undeclared-capability fail-closed behavior, credential isolation, hidden evaluator material, fault secrecy and assurance honesty → AEP-0002 / AVP-SECURITY-001..006.

`PROMOTED/SUPERSEDED`: artifact signer/trust/publication concerns are governed by AEP-0008 / Artifact Trust rather than the historical threat-model wording.

`NON_NORMATIVE`: attack examples, operational threat registry, implementation hardening and threat-maintenance workflow.

### 5.8 Document 17 — Oracle SDK

**Primary disposition: `SPLIT`.**

`PROMOTED`: protocol-facing Oracle evaluation semantics → AEP-0001 / AVP-ORACLE-001..007.

`NON_NORMATIVE`: Python protocol classes, helper methods, package API, process/sandbox mechanism and LLM judge adapter implementation.

### 5.9 Document 19 — MCP Adapter

**Primary disposition: `SPLIT`.**

`PROMOTED/SUPERSEDED`: current interoperable verification responsibility is AEP-0005 / AVP-MCP-001..008. The current contract deliberately binds MCP revision and preserves MCP as external authority.

`NON_NORMATIVE`: adapter cache implementation, proxy topology, mutation harness and concrete long-running-work plumbing.

`DEFERRED`: historical MCP features not represented by the selected MCP revision/profile are not silently normalized into AVP success; current feature-honesty semantics require fail-closed behavior instead.

### 5.10 Document 20 — OpenTelemetry Mapping

**Primary disposition: `SPLIT`.**

`PROMOTED/SUPERSEDED`: AEP-0006 / AVP-OTEL-001..008 govern root/event/tool correlation, outcome preservation, W3C propagation, minimization, completeness and Evidence composition.

`NON_NORMATIVE`: SDK/exporter/provider setup, collector topology, backend selection and implementation-specific attribute conveniences.

## 6. Historical profile responsibility mapping

The Alpha v0.1 historical profile vocabulary must not be restored as compatibility aliases. Responsibilities map as follows:

| Historical profile | Current disposition | Current profile/domain responsibility |
|---|---|---|
| `Core` | `SPLIT` | `avp-core-v0.1` plus Scenario/Evidence where the historical Core draft had mixed those concerns |
| `Environment` | `PROMOTED` | `avp-environment-v0.1` |
| `Snapshot` | `SUPERSEDED` as standalone profile | Snapshot/restore is a governed Environment capability; there is no standalone Snapshot profile |
| `Verification` | `SPLIT` | `avp-oracle-v0.1`, `avp-evidence-v0.1`, Core result/validity separation, Security and Artifact Trust where applicable |
| `Replay` | `SUPERSEDED` as standalone profile | Core owns replay Episode identity; Environment owns restore/equivalence claims; no standalone Replay profile |
| `Chaos` | `SUPERSEDED` as standalone profile | Environment owns fault identity/activation/clear semantics; Security owns secrecy/boundary requirements; no standalone Chaos profile |
| `Telemetry` | `SPLIT` | `avp-otel-mapping-v0.1` plus Evidence integrity/composition; OTel/W3C remain external tracing authorities |

Current profiles with no one-to-one historical profile are intentional refinements, not compatibility additions:

- `avp-scenario-v0.1` extracts Scenario materialization/identity from historical Core/AVS material;
- `avp-mcp-interop-v0.1` formalizes MCP verification boundaries;
- `avp-subject-v0.1` makes the Subject Adapter interoperability boundary explicit;
- `avp-artifact-trust-v0.1` separates authentication/trust-policy/publication authority from generic security/evidence concepts.

## 7. Explicit current non-goals and deferred surfaces

The following historical areas are **not current AVP normative profiles**:

- failure intelligence / RCA / clustering / first-bad-step methodology;
- reliability statistics and benchmark comparison methodology;
- a portable benchmark-authoring/mutation DSL beyond current Scenario semantics;
- SDK method/API shape and language-specific lifecycle;
- local CLI UX and command contract;
- mandatory package/registry network and registry APIs;
- commercial control-plane architecture, hosted fabric, tenancy, deployment and SRE architecture;
- generic LLM-judge ensemble/reliability methodology;
- A2A-specific interoperability profile.

Future promotion of any of these requires normal reconciliation and AEP governance. Reference-runtime or product implementation alone is insufficient.

## 8. Gate B closure criteria

This ledger closes the **global disposition** question only when review confirms all of the following:

- [x] documents 03–21 and ADR-001 all have an explicit primary disposition;
- [x] every `SPLIT` document identifies its promoted vs non-normative/deferred responsibilities;
- [x] historical Core/Environment/Snapshot/Verification/Replay/Chaos/Telemetry responsibilities are explicitly mapped;
- [x] current profiles that have no one-to-one historical profile are explained;
- [x] non-standardized historical product/tooling/methodology surfaces are explicitly prevented from acquiring protocol authority by omission;
- [ ] exact-head CI and Governance are green for this change;
- [ ] maintainer review accepts the ledger as the closure record.

## 9. What this ledger does not prove

This ledger is not the final alignment audit. It does **not** yet prove that every current normative `MUST` / `MUST NOT` has complete AEP/spec/requirement/schema/TCK/runtime traceability.

After Gate B is merged, the next phase is a separate **Normative / Conformance / Reference Alignment Audit** covering, for every current domain:

```text
AEP or reconciliation decision
    -> normative requirement
    -> schema impact (where machine-readable structure is normative)
    -> language-neutral TCK case/profile
    -> reference-runtime evidence
```

Any semantic gap found there must be corrected through the governing authority chain. The audit must never change the normative requirement merely to match Python behavior.

## 10. Stable-release effect

Completion of this ledger removes one stable-release blocker but does **not** authorize stable `v0.3.0`.

Stable remains blocked on the full normative/conformance/runtime alignment audit, resulting gap closure, stable-release eligibility audit, and a separate explicit maintainer release decision.

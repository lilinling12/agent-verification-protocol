# Historical Design Disposition Ledger

> Status: **Closure Candidate**  
> Authority: **Non-normative reconciliation evidence**  
> Baseline: `avp-design-alpha-v0.1`  
> Reconciled against: `main@46de450d62faa171e190cf9edbdb881767c2b8af`

This is the human-readable view of the global historical-design closure ledger. The canonical machine-readable evidence is `historical-disposition-ledger.json`. The ledger records provenance and disposition; it does **not** create protocol semantics.

## Governed vocabulary

`PROMOTED / SPLIT / SUPERSEDED / NON_NORMATIVE / DEFERRED / REJECTED`

`PROMOTED` means a material area has current normative specification, requirement IDs, and TCK profile evidence. `SPLIT` means a historical document contains material areas with different outcomes.

## Source disposition

| ID | Historical source | Disposition | Material areas |
|---|---|---|---|
| 03 | `03-agent-verification-protocol.md` | **SPLIT** | `PROMOTED` — episode lifecycle, identity, replay, verdict/validity separation<br>`PROMOTED` — evidence and artifact identity/integrity<br>`PROMOTED` — verification/oracle result authority<br>`PROMOTED` — security and capability boundaries<br>`SUPERSEDED` — generic extension/profile mechanism from the historical umbrella design |
| 04 | `04-scenario-benchmark-dsl.md` | **SPLIT** | `PROMOTED` — scenario materialization, deterministic identity, immutability, visibility, capabilities and references<br>`NON_NORMATIVE` — benchmark authoring DSL, catalog conventions and scoring workflow |
| 05 | `05-unified-trace-schema.md` | **SPLIT** | `PROMOTED` — AVP evidence identity needed for verification<br>`PROMOTED` — trace correlation, propagation, outcome preservation and telemetry completeness<br>`REJECTED` — AVP-owned universal trace wire schema |
| 06 | `06-system-architecture.md` | **SPLIT** | `PROMOTED` — portable authority and isolation boundaries<br>`SUPERSEDED` — repository/product architecture boundaries<br>`NON_NORMATIVE` — hosted control plane, persistence, orchestration and commercial topology |
| 07 | `07-environment-fabric.md` | **SPLIT** | `PROMOTED` — portable environment contract<br>`NON_NORMATIVE` — hosted fabric implementation and resource provisioning internals |
| 08 | `08-verification-engine.md` | **SPLIT** | `PROMOTED` — result/lifecycle separation<br>`PROMOTED` — evidence integrity and identity<br>`PROMOTED` — oracle evaluation and failure separation<br>`NON_NORMATIVE` — engine scheduling/orchestration algorithm |
| 09 | `09-failure-intelligence.md` | **SPLIT** | `SUPERSEDED` — failure taxonomy needed to keep protocol outcomes distinct<br>`NON_NORMATIVE` — RCA, clustering, recommendation and failure-intelligence algorithms |
| 10 | `10-reliability-statistics.md` | **SPLIT** | `DEFERRED` — portable reliability/statistical methodology profile<br>`NON_NORMATIVE` — current statistical implementation/report helpers |
| 11 | `11-conformance-test-spec.md` | **SUPERSEDED** | `SUPERSEDED` — language-neutral conformance model and requirement-linked cases |
| 12 | `12-open-source-governance.md` | **SUPERSEDED** | `SUPERSEDED` — project governance, AEP lifecycle, branching and release policy |
| 13 | `13-reference-runtime-design.md` | **NON_NORMATIVE** | `NON_NORMATIVE` — reference runtime architecture and execution design |
| 14 | `14-avp-sdk-contract.md` | **NON_NORMATIVE** | `NON_NORMATIVE` — language SDK API surface and lifecycle |
| 15 | `15-package-registry-spec.md` | **SPLIT** | `DEFERRED` — portable package registry protocol/ecosystem extension<br>`NON_NORMATIVE` — reference distribution packaging/release process |
| 16 | `16-security-threat-model.md` | **SPLIT** | `PROMOTED` — subject/evaluator capability, secret and hidden-material boundaries<br>`PROMOTED` — artifact trust/authentication/policy assurance<br>`NON_NORMATIVE` — threat examples, deployment-specific mitigations and operational controls |
| 17 | `17-oracle-sdk.md` | **SPLIT** | `PROMOTED` — portable oracle evaluation contract<br>`NON_NORMATIVE` — Python Oracle SDK/worker/subprocess API design |
| 18 | `18-local-runner-cli.md` | **SPLIT** | `NON_NORMATIVE` — local runner command-line UX and process contract<br>`SUPERSEDED` — portable TCK invocation/result expectations |
| 19 | `19-mcp-adapter.md` | **SPLIT** | `PROMOTED` — MCP revision/capability/schema/call/failure verification semantics<br>`NON_NORMATIVE` — adapter transport/gateway implementation details |
| 20 | `20-opentelemetry-mapping.md` | **SPLIT** | `PROMOTED` — AVP/OpenTelemetry correlation, propagation, minimization, completeness and evidence binding<br>`NON_NORMATIVE` — OpenTelemetry SDK/exporter implementation |
| 21 | `21-alpha-implementation-plan.md` | **NON_NORMATIVE** | `NON_NORMATIVE` — milestones, implementation sequencing and delivery plan |
| ADR-001 | `ADR-001-scope-and-boundaries.md` | **SUPERSEDED** | `SUPERSEDED` — protocol versus implementation/product scope boundaries |

## Key reconciliation decisions

- **03 `03-agent-verification-protocol.md` — SPLIT:** The historical umbrella protocol mixed lifecycle, result, evidence, verification, security, replay, and extension responsibilities. Alpha 2 governs those responsibilities through narrower authority domains rather than preserving one monolithic surface.
- **04 `04-scenario-benchmark-dsl.md` — SPLIT:** Portable ScenarioTemplate/ScenarioInstance execution semantics were separated from benchmark-authoring syntax and product methodology.
- **05 `05-unified-trace-schema.md` — SPLIT:** AVP no longer owns a unified tracing wire format. AVP-specific Evidence identity is governed by the Evidence contract, while event correlation, trace propagation, and telemetry representation are governed by the AVP OpenTelemetry mapping profile with W3C/OpenTelemetry retaining upstream tracing authority. The legacy root `schemas/avp-event.schema.json` is not evidence of a promoted universal AVP event wire contract and is retired by NSC-002 rather than assigned protocol authority after the fact.
- **06 `06-system-architecture.md` — SPLIT:** Portable authority boundaries were retained through governed protocol contracts; hosted control-plane, scheduling, persistence, deployment and commercial platform topology remain implementation/product architecture.
- **07 `07-environment-fabric.md` — SPLIT:** Portable environment state authority, reset/time, observation, projection, snapshot/restore, diff and fault semantics are normative; hosted provisioning/fabric internals are not.
- **08 `08-verification-engine.md` — SPLIT:** Verification semantics were decomposed into lifecycle/result separation, Evidence, Oracle, and trust domains. Engine orchestration remains reference implementation behavior.
- **09 `09-failure-intelligence.md` — SPLIT:** Root-cause analysis, clustering, explanation and remediation recommendations are evaluator methodology or product intelligence, not portable conformance semantics.
- **10 `10-reliability-statistics.md` — SPLIT:** Statistical reliability semantics are not governed by a Final Alpha 2 profile. NSC-001 resolves the orphan authority surface by retiring `schemas/reliability-report.schema.json` from the normative schema root rather than promoting historical methodology or Python behavior into protocol authority. The portable reliability/statistical methodology remains `DEFERRED`; `src/avp_ref/reliability.py` remains `NON_NORMATIVE` reference behavior.
- **11 `11-conformance-test-spec.md` — SUPERSEDED:** The historical conformance specification was replaced by the current language-neutral TCK registry, schemas, runner contract and requirement-linked cases.
- **12 `12-open-source-governance.md` — SUPERSEDED:** Repository governance and protocol change control are governed by the current governance/AEP/release process rather than the historical draft.
- **13 `13-reference-runtime-design.md` — NON_NORMATIVE:** Reference-runtime design is implementation evidence only. Current reference code follows the normative specification and TCK and does not define protocol semantics.
- **14 `14-avp-sdk-contract.md` — NON_NORMATIVE:** No language SDK API is part of Alpha 2 normative conformance. SDK APIs may wrap the protocol but may evolve independently.
- **15 `15-package-registry-spec.md` — SPLIT:** A package/registry ecosystem is not required for AVP Core or any Final Alpha 2 profile and has no promoted normative authority in this release line.
- **16 `16-security-threat-model.md` — SPLIT:** Portable security/authority and trust claims were promoted through governed contracts; threat scenarios and deployment mitigations remain informative analysis.
- **17 `17-oracle-sdk.md` — SPLIT:** Portable Oracle identity/input/failure/evidence/audit semantics are normative; Python package execution and SDK API design remain implementation details.
- **18 `18-local-runner-cli.md` — SPLIT:** CLI command names, local UX and process layout are tooling surfaces; Alpha 2 defines conformance behavior independently of a required CLI.
- **19 `19-mcp-adapter.md` — SPLIT:** MCP interoperability verification semantics were promoted while MCP remains external protocol authority; concrete adapter/gateway implementation remains non-normative.
- **20 `20-opentelemetry-mapping.md` — SPLIT:** The portable AVP-to-OpenTelemetry mapping is a normative interoperability profile; exporter/SDK implementation remains non-normative and W3C/OpenTelemetry retain tracing authority.
- **21 `21-alpha-implementation-plan.md` — NON_NORMATIVE:** The Alpha implementation plan is a historical execution record and cannot create present protocol obligations.
- **ADR-001 `ADR-001-scope-and-boundaries.md` — SUPERSEDED:** The ADR remains provenance, but current repository and protocol/product boundaries are governed by later architecture-boundary documents and Final AEP/spec surfaces.

## Historical profile responsibility mapping

| Historical profile | Disposition | Current profile(s) | Rationale |
|---|---|---|---|
| Core | **SPLIT** | `avp-core-v0.1`, `avp-evidence-v0.1`, `avp-oracle-v0.1`, `avp-security-v0.1` | The historical Core bundled lifecycle, evidence, verification and security responsibilities that now have separate semantic owners. |
| Environment | **PROMOTED** | `avp-environment-v0.1` | Portable environment authority and lifecycle semantics are directly governed by the Environment contract. |
| Snapshot | **SUPERSEDED** | `avp-environment-v0.1`, `avp-evidence-v0.1` | Snapshot/restore is no longer a standalone profile; environment state identity and integrity responsibilities are split across Environment and Evidence. |
| Verification | **SPLIT** | `avp-evidence-v0.1`, `avp-oracle-v0.1`, `avp-artifact-trust-v0.1`, `avp-core-v0.1` | Verification responsibilities are now separated into evidence integrity, oracle evaluation, trust, and result/lifecycle separation. |
| Replay | **SUPERSEDED** | `avp-core-v0.1` | Replay identity is a Core lifecycle requirement rather than a standalone conformance profile. |
| Chaos | **SUPERSEDED** | `avp-environment-v0.1`, `avp-security-v0.1` | Portable fault injection authority is part of Environment; secrecy of future evaluator-only fault material is Security. |
| Telemetry | **SPLIT** | `avp-otel-mapping-v0.1`, `avp-evidence-v0.1` | OpenTelemetry/W3C remain tracing authority; AVP governs only the interoperability mapping and evidence binding. |

## Authority boundary

- Historical source remains immutable and non-normative.
- Reconciliation evidence can classify provenance but cannot create a protocol obligation.
- Final AEPs and `spec/` own normative semantics.
- Schemas are derived machine-readable contracts and do not create semantics absent from `spec/`.
- TCK evidence proves portable conformance behavior.
- Python/reference-runtime behavior is non-normative implementation evidence.

## Stable-release consequence

Global historical disposition closure is necessary but not sufficient for stable release. NSC-001 retires the unowned reliability-report schema from the normative schema root while preserving the historical decision that portable reliability/statistical methodology is deferred and the current Python reliability helper is non-normative. No reliability requirement, schema, TCK profile, or cross-language contract is created by that retirement.

The active gate remains **Normative Surface Closure**, which audits `AEP ↔ spec ↔ requirement-index ↔ schema ↔ TCK` and must close the remaining blocking mismatches before implementation-alignment and stable-eligibility audits.

## Machine verification

`scripts/validate_historical_disposition.py` fail-closes on missing/duplicate historical sources, illegal dispositions, promoted areas without normative + requirement + TCK evidence, unknown requirement IDs, invalid/missing profile references, path traversal, dangling repository references, and incomplete historical-profile mapping. `scripts/quality.sh` executes the validator on every quality-gate run.
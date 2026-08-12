# Initial Design-Baseline Classification

This classification is a migration plan, not a normative decision. Individual sections may be split across multiple destinations during reconciliation.

| Historical document | Primary disposition | Notes |
|---|---|---|
| 03 Agent Verification Protocol | AVP Core candidate | Reconcile terminology, lifecycle, identity, evidence, verdict/validity, replay, security, extensions. |
| 04 Scenario Benchmark DSL | AVS / profile candidate | Separate Scenario/ScenarioInstance protocol semantics from benchmark authoring DSL. |
| 05 Unified Trace Schema | Event/evidence + OTel profile | AVP must not replace W3C Trace Context or OpenTelemetry. |
| 06 System Architecture | Informative architecture + commercial platform | Split protocol planes/contracts from product/control-plane implementation. |
| 07 Environment Fabric | Core environment contract + adapter/profile + commercial fabric | Keep portable environment semantics; exclude hosted provisioning internals. |
| 08 Verification Engine | AVP Core candidate | Claim, Evidence, Oracle, verification result and failure semantics are central. |
| 09 Failure Intelligence | Informative methodology / commercial capability | RCA, clustering and recommendations are not Core conformance requirements. |
| 10 Reliability Statistics | Reliability profile/methodology | Statistical methodology may be open but should not inflate Core wire semantics. |
| 11 Conformance Test Specification | TCK / conformance | Must map cases to normative requirement IDs. |
| 12 Open Source Governance | Repository governance | Reconcile with current `GOVERNANCE.md`, AEP and release policy. |
| 13 Reference Runtime Design | Reference implementation | Non-normative. |
| 14 AVP SDK Contract | SDK surface | Language SDK lifecycle may diverge from protocol lifecycle. |
| 15 Package Registry Specification | Optional ecosystem extension | Do not require a registry for AVP Core conformance. |
| 16 Security Threat Model | Security specification + informative threat analysis | Normative trust/authority requirements should be separated from threat examples. |
| 17 Oracle SDK | Reference/SDK | Extract Oracle protocol semantics separately from Python execution design. |
| 18 Local Runner CLI | Tooling | CLI shape is non-normative unless a separate CLI spec is intentionally created. |
| 19 MCP Adapter | MCP interoperability profile | MCP owns Agent↔Tool semantics; AVP owns verification evidence/policy around it. |
| 20 OpenTelemetry Mapping | OTel interoperability profile | OTel/W3C context remains authoritative for tracing. |
| 21 Alpha Implementation Plan | Historical implementation record | Never normative. |
| ADR-001 Scope and Boundaries | Architecture decision record | Preserve as design provenance; reconcile with current repository/product boundaries. |

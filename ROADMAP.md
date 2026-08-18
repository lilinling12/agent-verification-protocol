# AVP Alpha Roadmap

This roadmap tracks protocol stabilization separately from reference-implementation availability. A checked implementation item does not by itself make its behavior normative.

## Alpha 1 — Verification Core
- [x] Core lifecycle and replay contract
- [x] Evidence identity/integrity contract
- [x] Oracle evaluation/failure contract
- [x] Security boundary and assurance contract
- [x] logical snapshot/restore reference behavior
- [x] deterministic Chaos smoke test
- [x] failure localization baseline
- [x] reliability baseline
- [x] initial multi-profile TCK

## Alpha 2 — Interop Contract Stabilization

### Protocol / conformance
- [x] Scenario / ScenarioInstance contract and `avp-scenario-v0.1` TCK
- [x] Environment contract reconciliation and `avp-environment-v0.1` conformance profile
- [x] MCP verification interoperability profile and `avp-mcp-interop-v0.1` TCK
- [x] OpenTelemetry mapping interoperability profile and `avp-otel-mapping-v0.1` TCK
- [x] Subject Adapter interoperability contract and `avp-subject-v0.1` TCK
- [x] artifact trust / signature / attestation decision
- [x] Alpha 2 acceptance audit and release-candidate readiness review
- [x] `v0.3.0-rc.1` publication and external-consumer release acceptance
- [x] AEP-0001 through AEP-0008 Final eligibility audit
- [x] explicit protocol-maintainer authorization and `Accepted` → `Final` lifecycle transition
- [x] byte-safe historical design-baseline restoration and automated integrity enforcement
- [x] global historical-design disposition ledger for documents 03–21 and ADR-001
- [x] Normative Surface Closure (`AEP/reconciliation ↔ spec ↔ requirement-index ↔ schema ↔ TCK`)
- [ ] reference-runtime implementation alignment audit (`spec → TCK → src/avp_ref`)
- [ ] stable `v0.3.0` release decision

AEP-0001 through AEP-0008 are Final based on the merged eligibility audit, the explicit protocol-maintainer decision recorded on 2026-08-17, and released evidence at `v0.3.0-rc.1`. Finalization does not itself authorize stable release publication, package-index publication, or Alpha 3.

Stable `v0.3.0` remains gated on Alpha 2 Baseline Reconciliation Closure. Historical design restoration is provenance-only and must preserve the archived source bytes; reconciliation, specification, schemas, and language-neutral TCK remain authoritative over reference-runtime behavior. Normative Surface Closure must resolve every orphan or ambiguously owned authority surface before implementation alignment can become a stable-release gate.

### Reference implementation already available
- [x] MCP gateway proxy and verification path
- [x] OpenTelemetry SDK correlation/instrumentation path
- [x] HTTP Subject Adapter
- [x] Scenario compiler and ScenarioTemplate JSON Schema validation
- [x] external Oracle subprocess isolation path
- [x] content-addressed ArtifactStore with integrity verification
- [ ] signed/attested artifact publication

Reference implementation availability above is evidence for reconciliation, not protocol authority.

## Alpha 3 — Environment Fabric
- [ ] PostgreSQL/MySQL State adapters
- [ ] Playwright browser runtime
- [ ] network fault proxy
- [ ] virtual clock service
- [ ] container runtime
- [ ] microVM experiment

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
- [ ] OpenTelemetry mapping interoperability profile
- [ ] Subject Adapter interoperability contract
- [ ] artifact trust / signature / attestation decision
- [ ] Alpha 2 acceptance audit and release-candidate readiness review

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

## Alpha 4 — Reliability Intelligence
- [ ] paired A/B experiment planner
- [ ] Wilson/bootstrap intervals
- [ ] failure clustering
- [ ] counterfactual replay runner
- [ ] regression synthesis
- [ ] release gate

## Alpha 5 — Ecosystem
- [ ] Python SDK stabilization
- [ ] Java SDK
- [ ] TypeScript SDK
- [ ] Go SDK
- [ ] CUBE adapter
- [ ] public package registry prototype
- [ ] second independent AVP-Core implementation

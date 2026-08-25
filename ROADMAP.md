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
- [x] reference-runtime implementation alignment audit (`spec → TCK → src/avp_ref`)
- [x] stable `v0.3.0` release decision, publication, and external-consumer acceptance

AEP-0001 through AEP-0008 are Final based on the merged eligibility audit, the explicit protocol-maintainer decision recorded on 2026-08-17, and released evidence. Stable `v0.3.0` is the published Alpha 2 conformance baseline at exact source `7be045f47f59b259b32865be8b30005e4caa40f6`, with external-consumer acceptance in Release Validation #32 (`32442504868`).

Historical design restoration is provenance-only and preserves archived source bytes; reconciliation, specification, schemas, and language-neutral TCK remain authoritative over reference-runtime behavior. Normative Surface Closure and Reference Runtime Alignment are completed stabilization gates.

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

Alpha 3 design was explicitly authorized by the protocol maintainer on 2026-08-23. AEP-0009's Environment Fabric direction was explicitly Accepted on 2026-08-23 after protocol review. Acceptance authorizes downstream normative closure; backend implementation remains gated on reviewed portable semantics, machine-readable contracts where required, and executable conformance coverage.

### Foundation / protocol design
- [x] authorize Alpha 3 design phase
- [x] AEP-0009 Environment Fabric composition/capability protocol review and Accepted direction
- [x] normative gap matrix against Environment v0.1 / Core / Scenario / Security / Evidence
- [ ] Environment Fabric normative specification and requirement index
- [ ] Environment Fabric schema(s)
- [ ] base Environment Fabric TCK, including runtime-execution negative cases

The three unchecked Foundation items are implemented as a complete **unmerged candidate currently carried by PR #83**. Reviewed child PR #85 was squash-merged into #84 as `5612f8063d47236b8b0806f6109c174acccf5963`; after its own expanded-head review, #84 was explicitly squash-merged into #83 as `6d7bc4d2ecc0664ac5f0a71091bd2090d675ad34`. They remain unchecked here because `main` has not adopted PR #83 and no merge of #83 into `main` is authorized.

### Relational State resource profile
- [x] AEP-0010 Draft problem/scope and standards analysis
- [x] relational portability design audit
- [x] close RS-BR-001..RS-BR-008 Draft → Proposed blockers
- [x] reconcile AEP-0010 and complete Draft → Proposed readiness audit
- [x] AEP-0010 status advanced to Proposed for formal protocol review
- [x] complete formal Proposed protocol review
- [x] absorb RS-PR-001..RS-PR-003 acceptance-blocker decisions into AEP-0010 and record Draft-design supersession
- [x] complete acceptance-oriented re-review with no remaining semantic blocker
- [x] record explicit protocol-maintainer AEP-0010 Proposed → Accepted decision
- [ ] relational normative specification and requirement index
- [ ] `RelationalStateManifest` / `RelationalStateImage` schemas
- [ ] execution-sensitive `avp-relational-state-v0.1` TCK
- [ ] PostgreSQL adapter against the portable TCK
- [ ] MySQL/InnoDB adapter against the same portable TCK
- [ ] PostgreSQL/MySQL canonical parity acceptance evidence

AEP-0010 is **Accepted, not Final**. Formal Proposed review at baseline `29586a050a758a7058e1489df8c0b75e1d7088ca` found three acceptance blockers: visibility-scoped handling of evaluator-private relational state (RS-PR-001), explicit identity binding for execution-relevant database program/configuration inputs outside the logical state Manifest (RS-PR-002), and exact `STATE_EQUIVALENT` fidelity for a successful v0.1 relational restore (RS-PR-003).

Those decisions were incorporated into AEP-0010. Acceptance-oriented re-review at `4dd656ebaa34b3284c6fff5a6044d3696b164b30` (PR review `5004370426`) found all three blockers closed and no new cross-contract semantic blocker. Final pre-acceptance head `ad79ca158fce56851ce2fd545735bd86794baadb` passed CI #526, Governance #572/#573, and Release Validation #62; review `5004379749` confirmed the semantic re-review-to-final-head delta was ROADMAP-only.

The protocol maintainer explicitly accepted AEP-0010 on 2026-08-24. The decision is recorded in `docs/acceptance/alpha3-aep-0010-accepted-decision.md`. Acceptance authorizes the next governed Relational State authority slice: normative specification → requirement index → closed schemas where required → execution-sensitive TCK → reference interface/runtime → PostgreSQL/MySQL adapters. It does not authorize backend-first implementation, PR merge, Final, release selection, `0.3.1` publication, package-index publication, signing, or attestation.

The first Relational State authority slice was developed and formally reviewed in PR #87, then squash-merged into #86 as `9d06427f82820e04cac40829ff6526c962bc2b0f`. Formal review `5006694486` identified five executable authority-chain gaps (RSR-PR-001..RSR-PR-005); acceptance-oriented re-review `5006822376` at semantic head `07aeed2a7b056eb630d2371f8ebdee0ea7e45038` closed all five with no new semantic blocker. #86 then completed its own expanded-head review (`5014126751`) and exact-head gates before being explicitly authorized and squash-merged into PR #85 as `de0a9518dcfbfce93a53c6f76d75907b4c55bb27`. #85 subsequently completed expanded-head review `5015426236` and exact-head gates, then was explicitly squash-merged into parent PR #84 as `5612f8063d47236b8b0806f6109c174acccf5963`. #84 completed expanded-head review `5017088777` and exact-head gates, then was explicitly squash-merged into PR #83 as `6d7bc4d2ecc0664ac5f0a71091bd2090d675ad34`. PR #83 now carries the complete reviewed Alpha 3 candidate stack: AEP-0009 design/acceptance, active normative-candidate governance, Environment Fabric candidate, AEP-0010 acceptance, and Relational State candidate. The three Relational specification/schema/TCK items above remain unchecked because PR #83 has not been adopted by `main`.

PostgreSQL and MySQL remain downstream implementation evidence; neither backend may define the common API or portable semantics by implementation precedent.

### Other resource implementations
- [ ] Playwright browser runtime
- [ ] network fault proxy
- [ ] virtual clock service
- [ ] container runtime
- [ ] microVM experiment

No resource backend is considered an official Alpha 3 implementation of new portable semantics until the corresponding authority chain is reviewable in the order `Normative Spec -> Schema -> TCK -> Reference Runtime`. Alpha 3 work does not select a release, publish `0.3.1`, authorize package-index publication, or authorize signing/attestation publication.

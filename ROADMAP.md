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
- [x] Environment Fabric normative specification and requirement index
- [x] Environment Fabric schema(s)
- [x] base Environment Fabric TCK, including runtime-execution negative cases

The Environment Fabric authority slice was adopted into `main` by squash merge of PR #83 at exact commit `428635d857c96d9df400ef5a0b16aaba53fb97cf`. Exact-main CI #569 (`32852278819`) passed on the merge commit, including Python 3.11/3.12/3.13 quality, reproducible package builds, clean-consumer installation, installed-wheel identity, installed-wheel full TCK conformance, and release-evidence build/verification. AEP-0009 remains **Accepted, not Final**; these checked roadmap items record that the candidate authority surfaces are now present on `main`, not that a stable protocol release has been finalized.

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
- [x] relational normative specification and requirement index
- [x] `RelationalStateManifest` / `RelationalStateImage` schemas
- [x] execution-sensitive `avp-relational-state-v0.1` TCK
- [x] shared backend-neutral relational conformance harness + immutable parity fixture + privileged fixture-control seam (RBIR-001..003)
- [x] PostgreSQL adapter against the portable TCK
- [x] MySQL/InnoDB adapter against the same portable TCK
- [x] PostgreSQL/MySQL canonical parity acceptance evidence

AEP-0010 is **Accepted, not Final**. Formal Proposed review at baseline `29586a050a758a7058e1489df8c0b75e1d7088ca` found three acceptance blockers: visibility-scoped handling of evaluator-private relational state (RS-PR-001), explicit identity binding for execution-relevant database program/configuration inputs outside the logical state Manifest (RS-PR-002), and exact `STATE_EQUIVALENT` fidelity for a successful v0.1 relational restore (RS-PR-003).

Those decisions were incorporated into AEP-0010. Acceptance-oriented re-review at `4dd656ebaa34b3284c6fff5a6044d3696b164b30` (PR review `5004370426`) found all three blockers closed and no new cross-contract semantic blocker. Final pre-acceptance head `ad79ca158fce56851ce2fd545735bd86794baadb` passed CI #526, Governance #572/#573, and Release Validation #62; review `5004379749` confirmed the semantic re-review-to-final-head delta was ROADMAP-only.

The protocol maintainer explicitly accepted AEP-0010 on 2026-08-24. The decision is recorded in `docs/acceptance/alpha3-aep-0010-accepted-decision.md`. The Relational State authority slice was developed and formally reviewed through PRs #87 → #86 → #85 → #84 → #83, with each parent receiving a post-child expanded-head review before authorized squash merge. PR #83 then adopted the complete reviewed Alpha 3 stack into `main` at `428635d857c96d9df400ef5a0b16aaba53fb97cf`; exact-main CI #569 passed the installed-wheel full TCK and package/evidence gates. The relational specification/schema/TCK roadmap items are therefore complete on `main`, while AEP-0010 remains Accepted and the candidate registry remains active until a separately governed Final/release promotion.

Backend implementation readiness audit `docs/acceptance/alpha3-relational-backend-implementation-readiness.md` identified RBIR-001..003 as prerequisites before a database-specific adapter could be introduced. PR #90 implemented and review-closed those prerequisites without adding a database-specific backend, and was explicitly authorized for squash merge into `main` at `06f08f686fa58aff1635ddbd2e9566cab72c390a`. Exact-main CI #590 (`32939199537`) passed Python 3.11/3.12/3.13 quality, reproducible packaging, clean-consumer installation, installed-wheel identity, installed-wheel full TCK conformance, and release-evidence verification. `docs/acceptance/alpha3-relational-backend-harness-main-adoption.md` records the main-adoption evidence. The RBIR prerequisite is therefore complete on `main`.

PR #92 implemented the first database-specific adapter against that adopted backend-neutral harness. Its semantic implementation head `0954140ec30946787c95dfa04eb980637945ad2f` passed CI #596 and Governance #661, and formal implementation review `5028233705` found no blocker requiring portable Spec/Schema/TCK changes. Final PR head `ac8b32346450e9dc3345a289da3e5ea8a5638c93` passed CI #598, Governance #663, Release Validation #90, and Ready-state Governance #664. The protocol maintainer then explicitly authorized squash merge on 2026-08-26. PR #92 was adopted into `main` at exact commit `70b1a6c9ce0d45c596e489533cc9600151dae2b8`, and exact-main CI #599 (`32948033723`) passed Python 3.11/3.12/3.13 quality, reproducible packaging, clean base-wheel installation, installed-wheel full registered TCK conformance, release-evidence verification, and real PostgreSQL 17.11 / 18.6 database lanes. `docs/acceptance/alpha3-postgresql-main-adoption.md` records the adoption evidence. The PostgreSQL adapter roadmap item is therefore complete on `main`.

PR #94 implemented the second database-specific adapter against the same adopted backend-neutral harness. Final implementation head `4a492d307c60f9fe2b0a7dfb26970616f1681b1c` passed CI #604 and Governance #669, and formal implementation review `5028744001` found no blocker requiring portable Spec/Schema/TCK changes. Ready-state Governance #670 also passed on the unchanged exact head. The protocol maintainer explicitly authorized squash merge on 2026-08-27. PR #94 was adopted into `main` at exact commit `c081b714b832b4fd0201ea01dc35fba023d06826`, and exact-main CI #605 (`33035553945`) passed Python 3.11/3.12/3.13 quality, reproducible packaging, clean base-wheel installation, installed-wheel full registered TCK conformance, release-evidence verification, real PostgreSQL 17.11 / 18.6 regression lanes, and real MySQL 8.4.11 / 9.7.2 database lanes. `docs/acceptance/alpha3-mysql-main-adoption.md` records the adoption evidence. The MySQL/InnoDB adapter roadmap item is therefore complete on `main`.

PR #96 added the separate cross-backend canonical parity acceptance layer without changing portable Relational State semantics or either backend adapter. Final reviewed head `ae5e31c8a080239b81c1204cf141f6ca688302a0` passed CI #611 (`33048226831`), Governance #676 (`33048226885`), Relational Parity #4 (`33048226830`), formal exact-head review `5038102614`, and Ready-state Governance #677 (`33048372618`). After explicit protocol-maintainer squash authorization, PR #96 was adopted into `main` at `0bc12cdecd7d35292d2720adb0963e66ebeb509d`. Exact-main CI #612 (`33048968550`) and Relational Parity #5 (`33048968491`) both passed on that exact merge commit. `docs/acceptance/alpha3-relational-canonical-parity-acceptance.md` records the reviewed and main-adopted evidence. The canonical parity acceptance-evidence roadmap item is therefore complete on `main`.

PostgreSQL, MySQL/InnoDB, and their paired canonical-parity verifier remain implementation/conformance evidence rather than protocol authority. Completion of these implementation milestones does not authorize AEP Final transition, release selection, publication, signing, or attestation.

### Browser resource profile
- [x] AEP-0011 Draft problem/scope and standards analysis
- [x] browser portability and Proposed-readiness audit
- [x] close BR-BR-001..BR-BR-010 Draft → Proposed blockers
- [x] reconcile AEP-0011 and complete Draft → Proposed readiness audit
- [x] AEP-0011 status advanced to Proposed for formal protocol review
- [x] complete formal Proposed protocol review
- [x] resolve BPR-001..BPR-010 acceptance blockers and required focused acceptance evidence on the reviewed candidate stack
- [x] complete acceptance-oriented exact-head protocol re-review with no remaining semantic blocker on the reviewed candidate stack
- [x] record explicit protocol-maintainer AEP-0011 Proposed → Accepted decision
- [x] browser normative specification and requirement index
- [x] browser schema(s) for serialized state/projection resources where required
- [x] execution-sensitive browser resource TCK
- [x] backend-neutral browser conformance harness + immutable local-browser fixture + privileged fixture-control seam if required by reviewed protocol semantics
- [x] Playwright browser runtime against the portable TCK

AEP-0011 is **Accepted, not Final**, by explicit protocol-maintainer decision on 2026-08-31, recorded in `docs/acceptance/alpha3-aep-0011-accepted-decision.md`. Acceptance authorized downstream Browser closure in the order `Spec -> requirement index -> Schema -> provider/language-neutral execution-sensitive TCK -> backend-neutral harness -> reference implementation`; main adoption does not authorize AEP Final, provider-native semantics as protocol authority, release selection, publication, signing, attestation, or partial Browser support.

Its initial problem/scope and standards-analysis baseline was adopted into `main` by authorized squash merge of PR #100 at exact commit `8f0c37e34202066ed79f8aa420a9939dd79cc5d1`. Exact-main CI #622 (`33116957396`) and Relational Parity #15 (`33116957406`) both passed on that merge commit, and `docs/acceptance/alpha3-browser-draft-main-adoption.md` records that baseline adoption.

The implementation-independent portability audit was then adopted by PR #103 at exact main commit `ee876088bf53c82730b98dc74bfbc2e87f7aebb4`; exact-main CI #628 (`33134651349`) and Relational Parity #21 (`33134651336`) both passed. The audit narrowed base authoritative browser-session state to selected unpartitioned HTTP cookies plus selected tuple-origin `localStorage`, separated state from Evidence and execution identity, established `STATE_EQUIVALENT` as the only successful base restore fidelity, rejected universal network-idle/sleep settling, and required real-browser portability evidence without making multi-engine support a universal third-party conformance requirement.

PR #104 reconciled those decisions into AEP-0011 and added the Draft → Proposed readiness audit. Formal review `5048566230` at exact PR head `ae2cc0dfa42a476b1949611fbd201e9ce36f69a4` concluded `REVIEW-CLOSED — PROPOSED-ELIGIBILITY EVIDENCE IS COHERENT FOR THIS EXACT HEAD`; CI #629 (`33148952559`), Governance #695 (`33148952556`), Relational Parity #22 (`33148952557`), and Ready-state Governance #696 (`33149074249`) succeeded. After explicit squash authorization, PR #104 was adopted into `main` at exact commit `69f3d91a9197f159eb0b5d77418f01b956aa17ff`; exact-main CI #630 (`33149341398`) and Relational Parity #23 (`33149341383`) both passed. `docs/acceptance/alpha3-browser-readiness-main-adoption.md` records the reviewed and main-adopted evidence.

PR #105 then reconciled the readiness baseline into ROADMAP/main-adoption evidence. Its exact reviewed head `19bfaaccd52d6be0a61ba916eb3029ba84493e63` passed CI #631 (`33150653985`), Governance #698 (`33150653980`), Release Validation #96 (`33150653969`), Relational Parity #24 (`33150654000`), focused review `5048751200`, and Ready-state Governance #699 (`33150761945`). After explicit squash authorization, PR #105 was adopted into `main` at exact commit `e2159b1daba4dc214b5d77418f01b956aa17ff`; exact-main CI #632 (`33212353304`) and Relational Parity #25 (`33212353330`) both passed.

The formal Proposed protocol review is recorded by PR #107 against exact baseline `main@ccd05b71635b46218dfa14043320a60376339dc2`. It identified BPR-001..BPR-009. PR #108 incorporated those protocol decisions; stacked review/evidence work through PRs #109–#127 closed the required Chromium/Gecko/WebKit acceptance matrix, BPR-010 canonical ordering, the backend-neutral Browser harness, the real Playwright/Chromium reference path, the complete provider-neutral eight-case evaluator assembly, and atomic composite activation without allowing provider behavior to define protocol semantics.

The complete reviewed Browser candidate stack was then adopted into `main` by authorized squash merge of PR #108 at exact commit `781268dd193dd6ad169ffac3a0fd18fab7b602a5`. Expanded-head exact-head review `5085386175` was closed before merge, Ready-state Governance #946 passed on unchanged head `090de157c30fc186dce05a7c6e774c0a6a598a44`, and unresolved review threads were zero. The merge used an exact-head guard.

Exact-main validation on `781268dd193dd6ad169ffac3a0fd18fab7b602a5` then passed CI #817 (`33589204270`), Relational Parity #210 (`33589204275`), and Browser Reference #83 (`33589204283`). CI #817 includes Python 3.11/3.12/3.13 quality, reproducible packaging, clean-consumer installation, installed-wheel governed TCK conformance, release-evidence verification, and PostgreSQL/MySQL regression lanes. Browser Reference #83 executed the real Playwright/Chromium provider foundation path. `docs/acceptance/alpha3-browser-main-adoption-reconciliation.md` records the exact adoption evidence.

These checked Browser items therefore record that the reviewed authority, conformance harness, and reference implementation surfaces are now present and validated on `main`. They do **not** make AEP-0011 Final, make Playwright/Chromium normative, activate partial Browser ownership, establish universal multi-engine equivalence, select a release, or authorize publication/signing/attestation. Candidate/draft markers tied to Final/release promotion remain governed separately.

### Network Control resource profile
- [x] AEP-0012 Draft problem/scope and standards analysis
- [x] network-control portability and Proposed-readiness audit
- [x] close NC-BR-001..NC-BR-012 Draft → Proposed blockers
- [x] reconcile AEP-0012 and complete Draft → Proposed readiness audit
- [x] AEP-0012 status advanced to Proposed for formal protocol review
- [x] complete formal Proposed protocol review
- [ ] resolve NPR-001..NPR-011 acceptance blockers in AEP-0012
- [ ] complete acceptance-oriented exact-head protocol re-review with no remaining semantic blocker
- [ ] record explicit protocol-maintainer AEP-0012 Proposed → Accepted decision
- [ ] network-control normative specification and requirement index
- [ ] network-control schema(s) where required by reviewed semantics
- [ ] execution-sensitive network-control resource TCK
- [ ] backend-neutral network-control conformance harness + immutable local network fixture + privileged fixture-control seam if required by reviewed semantics
- [ ] controlled network-fault reference implementation against the portable TCK
- [ ] cross-mechanism portability acceptance evidence if required by reviewed protocol semantics

The Network Control Resource work must preserve AEP-0009's backend-first prohibition. `resourceKind: network` is only coarse Fabric classification; it does not define controlled-path coverage, fault vocabulary, activation/clearing settlement, recovery, timing, DNS, application-layer faults, snapshot participation, or Subject-visible control semantics. PR #130 adopted the reviewed AEP-0012 Draft problem/scope and standards/interoperability baseline into `main` at exact commit `7f7f613c50520efb2b553d65d4bb85c0e777dc40`; exact-main CI #823 (`33609386257`), Relational Parity #216 (`33609386265`), and Browser Reference #89 (`33609386244`) all passed.

PR #132 then adopted the implementation-independent Network Control portability audit into `main` at exact commit `74b442a0ffd22f4da79b5d4abfd339d694fc2843`. The audit resolved NC-BR-001..NC-BR-012 as explicit Draft design decisions for Proposed-readiness while preserving AEP-0009/Environment authority, provider neutrality, Subject/Evaluator/Control separation, deterministic fresh-connection semantics, and the prohibition on provider-first protocol design.

PR #133 reconciled those portability decisions into AEP-0012 and added the Draft → Proposed readiness audit. Focused review `5088528789` / `PRR_kwDOT09qic8AAAABL0zJlQ` at exact PR head `fe7e356ae64faa0b8b69e9b0ef64c345f3793916` concluded `REVIEW-CLOSED — PROPOSED-ELIGIBILITY EVIDENCE IS COHERENT FOR THIS EXACT HEAD`. CI #829 (`33619765040`), Governance #966/#967/#968/#969, Relational Parity #222 (`33619765006`), and Browser Reference #95 (`33619765014`) succeeded, with zero unresolved review threads. After explicit squash authorization, PR #133 was adopted into `main` at exact commit `2632935bef065b4d38e88f6df6b8cf0d620bfb3b`.

Exact-main validation on `2632935bef065b4d38e88f6df6b8cf0d620bfb3b` then passed CI #830 (`33667291305`), Relational Parity #223 (`33667290799`), and Browser Reference #96 (`33667291258`). `docs/acceptance/alpha3-network-control-readiness-main-adoption.md` records the reviewed and main-adopted evidence.

AEP-0012 is **Proposed on `main`, not Accepted**. PR #135 adopted the explicitly authorized `Draft → Proposed` lifecycle transition at exact main commit `45ab60d0f6e6db41da70a9859033efda52564055`. Exact-main CI #839 (`33675390573`), Relational Parity #232 (`33675390473`), and Browser Reference #105 (`33675390466`) all passed on that merge commit.

The formal Proposed protocol review against `main@45ab60d0f6e6db41da70a9859033efda52564055` retains the protocol-first Network Control direction but identifies **NPR-001..NPR-011** acceptance blockers covering endpoint/address-set and DNS boundaries, logical path semantics across terminating and packet-path mechanisms, deterministic exchange grammar, fresh-attempt identity, finite cut observation, settlement sequencing, recovery stability, behavioral bypass proof, target isolation, residual-state noninterference, and required cross-mechanism acceptance evidence. `docs/design/alpha3-network-control-resource-formal-proposed-review.md` records the review findings and `docs/design/alpha3-network-control-resource-proposed-review-blockers.md` is the authoritative blocker ledger for the next Proposed-phase protocol-change work.

Formal review completion does **not** resolve those blockers. The next substantive Network Control milestone is a separate AEP-0012 blocker-resolution protocol PR followed by exact-head acceptance-oriented re-review. AEP-0012 remains Proposed throughout that work unless and until the protocol maintainer separately and explicitly authorizes `Proposed → Accepted`. Network Control normative Spec/Schema/TCK, backend-neutral harness, provider/reference implementation, release selection, publication, signing, and attestation remain unauthorized.

### Other resource implementations
- [ ] virtual clock service
- [ ] container runtime
- [ ] microVM experiment

No resource backend is considered an official Alpha 3 implementation of new portable semantics until the corresponding authority chain is reviewable in the order `Normative Spec -> Schema -> TCK -> Reference Runtime`. Alpha 3 work does not select a release, publish `0.3.1`, authorize package-index publication, or authorize signing/attestation publication.
# Alpha 3 Browser Reference Conformance Closure Audit

Status: **REFERENCE CONFORMANCE CLOSURE-READY — MAIN ADOPTION NOT AUTHORIZED**

Audited candidate stack head: `4038d14ff3a8dd7af26ab0625e91bd129aa2779e`  
Owning activation PR: `#127`  
Normative authority baseline: PR `#114` / `13974bf52864d95f4b670ed31068d05674ebd8ba`  
Implementation-readiness gate: PR `#115` / `f6fe0e7a53411494aa5b2dd1b675ee8798b75381`  
AEP lifecycle: **AEP-0011 Accepted, not Final**

## 1. Purpose and authority boundary

This audit determines whether the stacked Browser v0.1 candidate has completed the implementation and reference-conformance obligations authorized after AEP-0011 acceptance.

It does not create new Browser semantics. The authority direction remains:

```text
Accepted AEP-0011
  -> normative Browser Spec
  -> requirement index
  -> closed Manifest/Image schemas
  -> provider-neutral Browser TCK
  -> backend-neutral Browser conformance harness
  -> concrete reference implementation
  -> implementation evidence
```

Concrete Playwright/Chromium behavior is evidence for the reference implementation. It is not protocol authority and does not redefine the portable Browser profile.

## 2. Audited stack

The reviewed implementation chain is:

```text
#114 normative Browser authority slice
  -> #115 backend implementation-readiness gate
    -> #116 backend-neutral Browser harness / fixture / privileged control seam
      -> #117 Playwright/Chromium provider foundation
        -> #118 expiry capability audit
          -> #119 executable fixture + exact expiry probes
            -> #120 partitioned-cookie non-admission
              -> #121 positive settlement
                -> #122 Service Worker / Cache Storage interference
                  -> #123 IndexedDB interference
                    -> #124 Subject / Evaluator / Control visibility separation
                      -> #125 metadata-identical executed-capability negative controls
                        -> #126 complete provider-neutral Browser TCK evaluator assembly and real 8/8 execution
                          -> #127 atomic composite ownership activation
```

All PRs in this stack remain Draft/Open/Unmerged at the time of this audit. This document therefore records candidate-stack closure only; it does not claim `main` adoption.

## 3. BBIR gate reconciliation

PR #115 defined five implementation-readiness blockers. Their final disposition on the audited stack is:

| Gate | Required property | Closure evidence | Final disposition |
| --- | --- | --- | --- |
| BBIR-001 | Browser-specific backend-neutral SUT/observer harness | #116 introduces `BrowserSUT`, evaluator-owned observation/canonicalization, and shared lifecycle verification; later provider/TCK work reuses this seam rather than replacing it | **CLOSED** |
| BBIR-002 | Immutable materialized local-browser fixture with exact origin identity before provisioning | #116 materialization model; #117–#127 execute exact materialized origins in real Chromium | **CLOSED** |
| BBIR-003 | Privileged fixture/control boundary separated from Subject/SUT | #116 establishes the control seam; #120–#125 add concrete partition, settlement, excluded-state, security, and broken-behavior controls without expanding BrowserSUT into a generic automation API | **CLOSED** |
| BBIR-004 | Positive settlement and independent reset/restore reprojection through the shared harness | #116 shared enforcement; #121 proves provider idleness cannot self-certify settlement; #125 includes settlement/reprojection broken controls; #126 executes the governed lifecycle case | **CLOSED** |
| BBIR-005 | Browser support activation must remain atomic | #126 requires exactly all eight mandatory Browser evaluators and proves 8/8 before activation; #127 keeps default composite at 0/8 and activates exactly 8/8 only when the complete Browser delegate is explicitly supplied | **CLOSED / PRESERVED** |

No BBIR item is closed by provider metadata or a green provider command alone. Each closure is tied to shared conformance behavior and/or independently observable negative controls.

## 4. Portable Browser TCK closure

The mandatory Browser profile remains exactly eight cases:

1. `AVP-TCK-BROWSER-IDENTITY-001`
2. `AVP-TCK-BROWSER-SELECTION-CANONICAL-001`
3. `AVP-TCK-BROWSER-COOKIE-001`
4. `AVP-TCK-BROWSER-STATE-IMAGE-001`
5. `AVP-TCK-BROWSER-EXECUTION-RESIDUAL-001`
6. `AVP-TCK-BROWSER-SETTLEMENT-LIFECYCLE-001`
7. `AVP-TCK-BROWSER-SECURITY-001`
8. `AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001`

PR #126 introduced the complete provider-neutral evaluator set and a closed `BrowserTCKAdapter` assembly boundary. Construction fails closed unless the evaluator ownership set is exactly the mandatory eight-case profile. Partial, duplicate, or unexpected Browser ownership is rejected.

PR #127 then activates Browser ownership only at the composite boundary:

- `ReferenceConformanceAdapter()` remains Browser **0/8** by default;
- explicit Browser-capable composition accepts only a complete `BrowserTCKAdapter`;
- the composite independently verifies the exact mandatory ownership set;
- activation adds exactly the eight Browser owners and preserves all pre-existing non-Browser ownership;
- existing duplicate-owner detection remains in force across the complete composite.

The activation model therefore preserves the repository claim-integrity rule: **0/8 -> 8/8 only**.

## 5. Real Browser execution closure

At PR #127 exact head `4038d14ff3a8dd7af26ab0625e91bd129aa2779e`, Browser Reference #59 executed the complete Browser provider suite using:

- Playwright `1.62.0`;
- Chrome for Testing `151.0.7922.34` / Chromium revision 1234;
- Python 3.13;
- Ubuntu 24.04.

Result:

- **51/51 Browser tests passed**;
- `test_complete_eight_case_profile_executes_through_composite_activation` passed;
- all eight mandatory Browser TCK cases were evaluated through `ReferenceConformanceAdapter` and returned `PASS`;
- the real composite ownership delta was exactly the eight mandatory Browser case ids;
- all existing non-Browser owners were preserved;
- Browser suite runtime was `132.521s` under the workflow's `180s` hard timeout.

During exact-head review, a temporary second full Chromium-profile execution was rejected even though it was green: it increased the suite to 52 tests / `159.356s`, leaving insufficient timing margin. The final test architecture keeps one authoritative full-profile execution and routes that execution through the composite, avoiding duplicate expensive provider setup while strengthening the ownership proof.

## 6. Provider-boundary findings

The audited candidate preserves the following boundaries:

- no Playwright/Chromium/Selenium/CDP/WebDriver/BiDi branch appears in the portable Browser TCK evaluator dispatch contract;
- the base reference wheel remains usable without the optional Browser implementation dependency;
- concrete browser setup remains outside `ReferenceConformanceAdapter`;
- `BrowserSUT` remains a narrow resource lifecycle seam rather than a generic automation surface;
- evaluator/control-only mutation and evidence helpers do not become Subject capabilities;
- provider enumeration order does not define canonical identity;
- provider success, `networkidle`, restore/import completion, or metadata claims do not self-certify conformance;
- provider-native partition metadata, browser handles, profile ids, or storage export structures do not become portable Browser state;
- no generic `BaseBrowserBackend`, provider plugin registry, compatibility framework, or `supports_*` capability bag was introduced.

The project rule remains: **split responsibilities; do not abstract protocol semantics**.

## 7. Required behavior evidence reconciled

The reviewed stack provides concrete reference evidence for the execution-sensitive obligations that remained after #116:

- exact resource/sibling isolation;
- selected unpartitioned cookie/localStorage projection;
- host-only/domain cookie identity and SameSite Default distinction;
- browser-representable persistent expiry exactness with fail-closed nonrepresentable precision;
- partitioned-cookie non-admission;
- exact DOMString code-unit preservation and canonical ordering;
- positive settlement independent of provider idleness;
- Service Worker / Cache Storage material-interference detection;
- IndexedDB material-interference detection;
- execution-input drift rejection;
- independent snapshot/reset/restore reprojection;
- Subject/Evaluator/Control visibility separation;
- Artifact identity vs retrieval-authority separation;
- metadata-identical broken implementations for the governed executed-capability negative directions;
- complete eight-case provider-neutral TCK execution;
- atomic composite activation.

This is sufficient for reference-conformance closure of the reviewed Chromium implementation path. It is not evidence that every browser engine or every automation transport exposes identical implementation capabilities.

## 8. Exact-head repository gates

At audited head `4038d14ff3a8dd7af26ab0625e91bd129aa2779e`:

- Governance #882 — **SUCCESS**
- CI #793 — **SUCCESS**
- Relational Parity #186 — **SUCCESS**
- Browser Reference #59 — **SUCCESS**
- PR #127 — mergeable, Draft/Open/Unmerged
- unresolved PR #127 review threads — none
- exact-head review closure — `5074977383`

CI #793 includes Python 3.11/3.12/3.13 quality gates, reproducible packaging, clean base-wheel consumer installation, installed-wheel governed TCK conformance, release-evidence validation, PostgreSQL 17.11/18.6, and MySQL 8.4.11/9.7.2 regression coverage.

## 9. Closure decision

The audited Browser candidate stack is **REFERENCE CONFORMANCE CLOSURE-READY** for the following bounded statement:

> The reviewed AVP Browser v0.1 reference implementation can explicitly compose the complete provider-neutral Browser TCK profile into the reference conformance adapter and execute all eight mandatory cases successfully against the controlled Chromium reference path, while preserving the protocol/provider authority boundary and atomic support-claim rule.

The Browser roadmap implementation items are technically satisfied on this candidate stack, but they are **not yet adopted on `main`**. ROADMAP completion should therefore be recorded only through the repository's governed main-adoption step after explicit merge authorization and exact-main validation.

## 10. Explicit non-claims and non-authorizations

This audit does **not** establish or authorize:

- AEP-0011 `Accepted -> Final` transition;
- stable or release-candidate version selection;
- release/tag/publication/signing/attestation;
- merge of PR #108 through #127 or this audit slice;
- universal multi-engine equivalence;
- Playwright/Chromium behavior as normative Browser semantics;
- a requirement that third-party implementations use Playwright, Chromium, or Python;
- partial Browser support;
- repository split or generic provider/plugin-framework work.

## 11. Next governed transition

No additional Browser feature implementation should be added merely to make the current reference claim look broader.

The next transition is governance, not protocol invention:

1. review-close this audit slice on its exact head;
2. preserve the reviewed stacked ancestry;
3. obtain explicit protocol-maintainer merge authorization before any stack adoption;
4. adopt the reviewed Browser stack according to repository branching/release governance;
5. run exact-main CI/Governance/Browser/Relational evidence after adoption;
6. only then update ROADMAP/main-adoption evidence to record Browser normative/TCK/harness/Playwright implementation completion on `main`.

AEP-0011 Final and release decisions remain separately governed future actions.
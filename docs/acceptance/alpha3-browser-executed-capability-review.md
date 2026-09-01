# Alpha3 Browser Executed Capability Review

Status: **IMPLEMENTATION REVIEW-CLOSED CANDIDATE — EXACT-HEAD GATES REQUIRED**

Reviewed semantic head: `22ef2f60986c46ad22c4c73ef6a1a764859de87b`

Scope: concrete Chromium reference implementation evidence for **AVP-BROWSER-020 — Executed provider-neutral conformance** and the negative-control directions of `AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001`.

This review does not activate the Browser TCK case, does not change Browser v0.1 normative semantics, and does not make the concrete Playwright fault-injection mechanics portable protocol authority.

## 1. Decision

The semantic implementation is acceptable for its bounded implementation-evidence scope.

The reference path now demonstrates all of the following:

1. a real Browser implementation path executes at the browser boundary rather than establishing capability through metadata alone;
2. the provider-neutral evaluator contains no branch on browser engine, automation library, debugging protocol, or transport product name;
3. the good implementation and each broken candidate retain the same governed Browser profile, revision, canonical representation, Manifest digest, and immutable execution-binding metadata;
4. provider-specific fault injection remains private to the implementation/test-driver seam;
5. the same shared `BrowserConformanceHarness` and provider-neutral behavioral expectations reject metadata-identical candidates whose observable behavior violates Browser v0.1 requirements;
6. provider enumeration order is normalized by portable canonicalization and therefore does not itself change canonical identity;
7. an implementation claiming a noncanonical/provider-order digest is rejected against an independently observed canonical projection;
8. successful lifecycle commands cannot replace independent reprojection;
9. positive settlement is required before provider observation can establish an accepted authoritative projection;
10. evaluator-private state, material excluded-state interference, and required execution-input drift cannot be made conforming by capability metadata or provider self-certification.

This closes the current **concrete Chromium implementation obligation** for AVP-BROWSER-020, subject to the audit-record exact head itself passing the repository gates.

## 2. Authority ordering preserved

The implementation preserves the repository authority order:

`Accepted AEP-0011 -> Browser normative spec -> requirement index -> schemas -> provider-neutral TCK -> backend-neutral harness -> concrete provider -> implementation evidence`

In particular:

- `src/avp_ref/tck_adapter/browser_executed_capability.py` is implementation/conformance infrastructure, not normative protocol text;
- it composes the existing `BrowserConformanceHarness` instead of reimplementing Browser lifecycle, canonicalization, settlement, or execution-condition rules;
- no concrete Browser engine/provider is imported or selected by the provider-neutral evaluator;
- no capability flag or provider name is used to decide whether behavior is accepted;
- no fault mode is added to the concrete production Browser resource/provider API;
- broken behavior is injected only behind a test-private observer/backend seam;
- no portable Subject or Resource browser-automation API is introduced;
- no Browser TCK ownership is activated in `ReferenceConformanceAdapter`.

## 3. Metadata-identical negative twins

`BrowserExecutedMetadata` records only governed metadata needed to prove that the positive implementation and negative twin are indistinguishable by declaration:

- Browser profile;
- profile revision;
- canonical representation;
- Manifest digest;
- sorted immutable execution bindings including identity and identity type.

Before behavioral evaluation, the negative-control suite requires exact equality of this metadata with the reference candidate.

The fault identifier itself is test-driver information and is deliberately absent from governed candidate metadata. A portable evaluator therefore cannot pass the good implementation and reject the broken one merely by inspecting a capability label, provider name, browser name, or injected fault marker.

## 4. Provider-neutral evaluator boundary

`BrowserExecutedCapabilityEvaluator` is deliberately small.

Its responsibilities are limited to:

1. require exact equality of governed metadata for negative twins;
2. require independently observed canonical baseline identity through `BrowserConformanceHarness`;
3. require a governed negative-control operation to fail closed;
4. require an exact Subject-authorized surface without evaluator-private values.

The evaluator does not contain Browser implementation names or transport-specific logic.

The integration suite additionally checks the evaluator source for the forbidden portable branch tokens enumerated by the TCK vector:

- Playwright;
- Selenium;
- Chromium;
- Firefox;
- WebKit;
- CDP;
- WebDriver;
- BiDi.

This source check is repository implementation evidence, not a substitute for the normative provider-neutrality rule itself.

## 5. Observable broken-behavior matrix

The real Chromium suite exercises the AVP-BROWSER-020 broken-behavior directions against metadata-identical candidates.

### 5.1 Cookie identity loss

A private observer twin changes the real selected `host_only` cookie from `hostOnly=true` to `hostOnly=false` without changing governed metadata.

Independent canonical baseline comparison rejects the candidate.

### 5.2 `SameSite=Default` collapse

A private observer twin changes the real selected `SameSite=Default` fact to `Lax`.

The resulting canonical state identity no longer matches the governed baseline and is rejected.

### 5.3 Partitioned state admitted as unpartitioned

The control first creates real CHIPS state in Chromium. The broken observer then injects that observed partitioned cookie into the unpartitioned portable projection.

The shared canonical baseline expectation rejects the extra admitted state.

This demonstrates rejection because of observable state semantics, not because the evaluator branches on a Chromium/CHIPS provider feature name.

### 5.4 DOMString code-unit corruption

A private observer twin changes one selected localStorage value at the encoded DOMString code-unit boundary.

The canonical projection digest changes and is rejected.

### 5.5 Provider enumeration order

The observer returns cookies, origins, and localStorage entries in reversed provider enumeration order.

The good provider-neutral path still produces the governed canonical digest because shared Browser canonicalization orders the complete selected state.

A separate negative control then makes a valid owned snapshot claim a synthetic noncanonical/provider-order digest. `verified_snapshot` rejects that claim because the SUT-reported digest does not equal the independently observed canonical projection.

The proof therefore distinguishes correctly between:

- arbitrary provider enumeration order, which MUST be normalized and accepted; and
- treating provider order as canonical identity, which MUST be rejected.

### 5.6 Restore success without independent reprojection

After a verified snapshot is taken, selected state is changed and the concrete restore command is replaced by a test-private no-op.

The lifecycle call itself appears to complete, but `BrowserConformanceHarness.verified_restore` independently reprojects selected state and rejects the false success because the target snapshot digest was not re-established.

### 5.7 Settlement bypass

The test creates an evaluator-owned settlement ledger containing accepted unresolved Browser work and leaves Subject side-effect admission open.

`authoritative_projection` rejects the operation with `BrowserSettlementError` before provider observation can establish an accepted projection.

Provider/browser completion therefore cannot self-certify settlement.

### 5.8 Evaluator-private state leak

The executed-capability evaluator accepts only the exact Subject-authorized surface and scans it against explicit evaluator-private probe values.

The positive Subject surface is accepted. A metadata-identical synthetic surface containing the private value is rejected.

This composes the concrete AVP-BROWSER-019 evidence from the parent stack with the AVP-BROWSER-020 requirement that behaviorally broken candidates be rejectable without changing metadata.

### 5.9 Excluded-state interference

On the real provider path, setting material excluded-state interference causes the authoritative projection to fail closed.

A private broken observer is also exercised that temporarily suppresses that interference condition before delegating observation. Because the negative-control operation then succeeds, `require_rejected` explicitly rejects the candidate as a broken implementation rather than accepting its identical metadata.

### 5.10 Required execution-input drift

On the real provider path, mutating a required execution binding causes the observer to reject execution-input identity drift.

A private broken observer is also exercised that suppresses the drift check. Its operation incorrectly succeeds and is therefore rejected by the negative-control expectation.

These two suppression controls are important: they prove the negative matrix is not merely checking that the current good observer already contains the right `if` statements. A metadata-identical evaluator path that deliberately stops enforcing those conditions is detectably nonconforming.

## 6. Positive real-browser path

The same suite first proves the nonbroken candidate can execute the governed path and reproduce the canonical baseline digest through the shared harness.

The negative matrix therefore does not establish compliance by making every candidate fail. It distinguishes:

`same governed metadata + correct observable behavior -> accepted`

from:

`same governed metadata + broken observable behavior -> rejected`

That distinction is the core implementation obligation of AVP-BROWSER-020.

## 7. Semantic-head validation

At semantic head `22ef2f60986c46ad22c4c73ef6a1a764859de87b`:

- Governance #845 — **SUCCESS**
- CI #757 — **SUCCESS**
- Relational Parity #150 — **SUCCESS**
- Browser Reference #23 — **SUCCESS**

Browser Reference #23 executed **50 real-browser tests successfully in 100.116 seconds** against:

- Playwright Python `1.62.0`;
- Chrome for Testing `151.0.7922.34` / Playwright Chromium revision 1234;
- Ubuntu 24.04;
- Python 3.13.

The fifteen AVP-BROWSER-020 tests all executed and passed:

1. `test_broken_observer_that_ignores_excluded_interference_is_detectably_wrong`
2. `test_broken_observer_that_ignores_execution_drift_is_detectably_wrong`
3. `test_collapsed_samesite_default_is_rejected_with_identical_metadata`
4. `test_domstring_corruption_is_rejected_with_identical_metadata`
5. `test_evaluator_has_no_provider_name_branching`
6. `test_evaluator_private_leak_is_rejected_with_identical_metadata`
7. `test_excluded_state_interference_cannot_be_ignored`
8. `test_lost_hostonly_identity_is_rejected_with_identical_metadata`
9. `test_partitioned_admission_is_rejected_with_identical_metadata`
10. `test_positive_real_browser_path_is_accepted`
11. `test_provider_enumeration_order_does_not_change_canonical_identity`
12. `test_provider_order_snapshot_digest_claim_is_rejected`
13. `test_required_execution_input_drift_cannot_be_ignored`
14. `test_restore_success_without_reprojection_is_rejected`
15. `test_unsettled_projection_is_rejected_before_provider_observation`

## 8. Architecture and code-quality review

Accepted properties:

- the provider-neutral evaluator composes existing Browser infrastructure rather than creating a parallel lifecycle implementation;
- provider-specific fault injection exists only in tests;
- no `fault_mode`, `supports_*`, generic provider capability flag, or self-certification path was added to the concrete runtime;
- no `BaseBrowserBackend`, generic Browser provider hierarchy, storage-provider abstraction, or broad inheritance framework was introduced;
- negative twins use composition around the existing concrete backend/observer seam;
- canonicalization remains single-source in the shared Browser harness;
- settlement remains evaluator-owned and is checked before authoritative observation;
- reset/restore verification remains based on independent canonical reprojection;
- security visibility reuses the existing Subject/Evaluator separation instead of inventing a second security model;
- test discovery is automatically covered by the existing `test_playwright_browser*.py` real Browser gate;
- Python quality and packaging gates remained green.

This follows the repository engineering rule: **split responsibilities; do not abstract protocol semantics**.

## 9. AVP-BROWSER-020 disposition

The current Chromium reference implementation now has concrete executed evidence that metadata-identical broken candidates can be distinguished from a correct candidate using provider-neutral observable expectations.

The implementation obligation for AVP-BROWSER-020 is therefore **review-closable**, subject to this audit-record exact head passing all required gates.

The closure is intentionally bounded:

- it is not a universal theorem for every Browser engine/provider;
- it does not require third-party implementations to use Playwright or Chromium;
- it does not make test-private fault injection part of the AVP protocol;
- it does not establish complete Browser profile conformance;
- it does not by itself execute the portable `AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001` through `ReferenceConformanceAdapter`;
- it does not authorize any Browser case ID ownership yet.

## 10. Remaining Browser work after implementation closure

The major remaining Browser gate is now **provider-neutral TCK evaluator wiring and atomic ownership activation**.

Before any Browser case is claimed by `ReferenceConformanceAdapter`, the implementation must demonstrate that all eight mandatory Browser cases genuinely execute through the governed conformance path:

1. `AVP-TCK-BROWSER-IDENTITY-001`
2. `AVP-TCK-BROWSER-SELECTION-CANONICAL-001`
3. `AVP-TCK-BROWSER-COOKIE-001`
4. `AVP-TCK-BROWSER-STATE-IMAGE-001`
5. `AVP-TCK-BROWSER-EXECUTION-RESIDUAL-001`
6. `AVP-TCK-BROWSER-SETTLEMENT-LIFECYCLE-001`
7. `AVP-TCK-BROWSER-SECURITY-001`
8. `AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001`

Activation remains atomic. A subset MUST NOT be added merely because its concrete implementation evidence is already green.

At the reviewed semantic head, the composite reference adapter still contains no Browser delegate; Browser ownership therefore remains **0/8**.

The next implementation slice should design the provider-neutral Browser TCK adapter/evaluator wiring so the eight portable case vectors drive the shared harness and concrete backend without provider-name branches or self-declared capability shortcuts.

## 11. Non-authorizations

This review does not authorize:

- merge of PR #125 or any parent PR;
- partial Browser TCK activation;
- adding only `AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001` to supported case IDs;
- complete Browser v0.1 conformance claim;
- AEP-0011 Final;
- release, tag, package publication, signing, or attestation publication;
- concrete Playwright/Chromium behavior as normative protocol authority;
- repository split or a generic plugin/provider framework.

## 12. Exact-head closure condition

This audit document creates a new exact head.

The status may become **REVIEW-CLOSED** only after that exact audit head itself passes:

- CI;
- Governance;
- Browser Reference;
- Relational Parity.

Until then the disposition remains **IMPLEMENTATION REVIEW-CLOSED CANDIDATE — EXACT-HEAD GATES REQUIRED**.

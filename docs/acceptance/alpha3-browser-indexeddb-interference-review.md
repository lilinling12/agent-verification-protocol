# Alpha3 Browser IndexedDB Interference Review

Status: **IMPLEMENTATION REVIEW-CLOSED CANDIDATE — EXACT-HEAD GATES REQUIRED**

Reviewed semantic head: `d69a7d579a3a174feaec7c4e8b452cc3554d5df1`

Scope: concrete Playwright/Chromium implementation evidence for the remaining controlled IndexedDB portion of the AVP-BROWSER-014 excluded-state interference boundary. This review does not change AEP-0011, Browser v0.1 schemas, portable TCK semantics, or Browser case ownership.

## 1. Decision

The semantic implementation is acceptable for its stated scope.

The concrete reference path now proves that IndexedDB residue can materially alter browser execution behavior while the selected Browser v0.1 authoritative state remains unchanged:

1. a Browser resource is provisioned from the governed localhost excluded-state execution fixture;
2. canonical selected Browser v0.1 state is independently projected and digested;
3. evaluator/control observes that the controlled IndexedDB database is absent without creating it;
4. the clean behavior probe produces the expected clean-mode result;
5. evaluator/control creates the controlled database/object store and writes the exact controlled record;
6. independent observation confirms that the database exists and that the exact controlled value can be read;
7. the behavior probe now produces a distinct IndexedDB-dependent result;
8. canonical selected Browser v0.1 state is reprojected;
9. the selected digest is unchanged;
10. because excluded IndexedDB state materially changed behavior while selected state remained equal, the resource is marked interfering;
11. the ordinary Browser observer rejects subsequent authoritative projection through the existing execution-condition gate.

This preserves the required fail-closed direction: equal selected cookie/localStorage state is not sufficient when materially relevant excluded state has been demonstrated.

## 2. Authority boundary

The implementation preserves the repository authority ordering:

`Accepted AEP-0011 -> Browser normative spec -> requirement index -> schemas -> provider-neutral TCK -> backend-neutral harness -> concrete provider implementation -> implementation evidence`

Specifically:

- IndexedDB is **not** added to BrowserStateImage;
- no IndexedDB selector is added to the Browser Manifest;
- IndexedDB database/store/key/value identifiers are concrete evaluator inputs, not portable Browser v0.1 semantics;
- Playwright/Chromium observations do not define protocol behavior;
- the existing BAE-011 acceptance evidence informed the evidence shape but is not imported into runtime or conformance authority;
- `PlaywrightBrowserIndexedDBControl` is evaluator/control-only and absent from BrowserSUT;
- the ordinary Browser observer remains responsible for fail-closed execution-condition verification;
- no Browser TCK case ID is activated.

## 3. Side-effect-free missing-state observation

A critical correctness requirement is that the evaluator must not create the excluded state merely by checking whether it exists.

The concrete observation path therefore uses `indexedDB.databases()` first. If the target database is absent, observation returns the clean result without calling `indexedDB.open()`.

Only after the database is independently proven present may the evaluator open it to inspect the controlled store/key/value.

A real Chromium regression control calls the missing-state observation repeatedly and proves the database remains absent. This prevents an evaluator-induced residue bug from being mistaken for Subject state.

If a concrete browser transport cannot provide a side-effect-free database-existence capability required by this proof, the control must fail closed rather than fall back to an `open()`-based existence probe.

## 4. Material-behavior evidence

The proof distinguishes storage inventory from material interference.

The controlled behavior probe has two deliberately distinct concrete outcomes:

- clean/missing controlled database -> `network-mode`;
- exact controlled IndexedDB record present -> `indexeddb-mode`.

These strings are fixture behavior, not protocol semantics. What matters is the independently established conjunction:

1. the selected BrowserStateImage digest before and after IndexedDB setup is identical;
2. the controlled excluded state is independently observable;
3. the observed browser behavior changes because of that excluded state.

Only that conjunction marks the concrete resource as materially interfering.

Mere IndexedDB presence, database count, or transaction completion is not sufficient by itself.

## 5. Resource isolation evidence

A separate real Chromium control provisions two sibling Browser resources backed by distinct BrowserContexts.

After one resource receives the controlled IndexedDB residue and is proven interfering, the sibling remains:

- free of the controlled IndexedDB database;
- behaviorally equal to the clean-mode result;
- independently projectable with its original selected Browser v0.1 digest.

This proves resource-local contamination for the controlled IndexedDB surface in the current reference provider.

Combined with PR #122, the concrete provider now has real interference/isolation evidence for both:

- Service Worker + Cache Storage;
- IndexedDB.

This is implementation evidence for these controlled surfaces, not a universal theorem covering every possible browser state outside Browser v0.1 selection.

## 6. Semantic-head validation

At semantic head `d69a7d579a3a174feaec7c4e8b452cc3554d5df1`:

- CI #752 — **SUCCESS**
- Governance #840 — **SUCCESS**
- Browser Reference #18 — **SUCCESS**
- Relational Parity #145 — **SUCCESS**

Browser Reference #18 executed **29 real-browser tests successfully in 55.068 seconds** against:

- Playwright Python `1.62.0`;
- Chrome for Testing `151.0.7922.34` / Playwright Chromium revision 1234;
- Ubuntu 24.04;
- Python 3.13.

The four new IndexedDB tests passed:

1. `test_observation_does_not_create_missing_database`
2. `test_material_interference_fails_closed_with_selected_digest_unchanged`
3. `test_indexeddb_residue_is_resource_local`
4. `test_proof_rejects_unselected_origin`

## 7. AVP-BROWSER-014 disposition

The active concrete reference provider now contains real-browser material-interference controls for the two excluded-state families identified by the earlier Browser acceptance evidence as directly behavior-relevant:

- Service Worker/Cache Storage;
- IndexedDB.

For these controlled surfaces, the implementation proves the required fail-closed direction when selected cookie/localStorage identity is insufficient.

This is enough to close the current **implementation obligation** for AVP-BROWSER-014 in the Chromium reference path, subject to this audit-record head passing exact-head gates.

The closure is intentionally bounded:

- it does not claim all conceivable browser storage/runtime state is now selected or proven irrelevant;
- it does not turn excluded surfaces into Browser v0.1 portable state;
- it does not claim universal engine-family behavior;
- future materially relevant excluded surfaces discovered by TCK/evidence must still be handled by noninterference proof, immutable execution/isolation binding, or fail-closed insufficiency.

The governing rule remains:

> If excluded state can materially influence scenario behavior and the execution identity/isolation policy does not make that influence irrelevant, verification must fail closed.

## 8. Quality and architecture review

Accepted implementation properties:

- IndexedDB mechanics are isolated in `playwright_browser/indexeddb.py` rather than expanding the Service Worker/Cache control into a broad storage module;
- no `BaseExcludedStateControl`, browser-storage hierarchy, generic provider interface, or `supports_*` layer was introduced;
- immutable dataclasses carry concrete observations/evidence;
- BrowserSUT remains narrow (`snapshot/reset/restore/release` only);
- the existing canonical Browser projection is reused for selected-state identity;
- evaluator evidence remains resource-scoped;
- missing-state observation is side-effect free;
- write completion and exact readback are explicitly verified;
- failure paths are explicit and fail closed;
- new tests are automatically included by the existing `test_playwright_browser*.py` Browser Reference gate.

Keeping Service Worker/Cache and IndexedDB controls separate follows the repository rule: **split responsibilities; do not abstract protocol semantics**. Their mechanics differ enough that a shared base class would add speculative coupling without a second provider consumer.

## 9. Remaining Browser implementation obligations

Closing the current AVP-BROWSER-014 concrete excluded-state slice does **not** establish complete Browser profile conformance.

The next governed implementation work should address **AVP-BROWSER-019 Subject / Evaluator secrecy and authority separation** with real-browser evidence. In particular, evaluator-private state/control information must not become visible or mutable through the Subject execution surface.

After that, remaining work includes:

- metadata-identical behaviorally broken provider controls for AVP-BROWSER-020;
- provider-neutral Browser TCK evaluator wiring for all eight Browser cases;
- all eight cases executing successfully against the concrete profile;
- only then atomic activation of all eight Browser case IDs in `ReferenceConformanceAdapter`.

Partial Browser case activation remains forbidden.

## 10. Non-authorizations

This review does not authorize:

- merge of PR #123 or its parent stack;
- AEP-0011 Final;
- complete Browser v0.1 conformance;
- Browser TCK case activation;
- partial Browser case ownership;
- release, tag, package publication, signing, or attestation publication;
- IndexedDB semantics as portable protocol authority;
- repository split or generic provider/plugin framework work.

## 11. Exact-head closure condition

This document creates a new audit-record head. REVIEW-CLOSED status may be recorded only after that exact head itself passes:

- CI;
- Governance;
- Browser Reference;
- Relational Parity.

Until then, the status remains **IMPLEMENTATION REVIEW-CLOSED CANDIDATE — EXACT-HEAD GATES REQUIRED**.

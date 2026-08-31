# Alpha3 Browser Excluded-State Interference Review

Status: **IMPLEMENTATION REVIEW-CLOSED CANDIDATE — EXACT-HEAD GATES REQUIRED**

Reviewed semantic head: `ea37ee6971fe416774fbf8d5af260da9fcdbddca`

Scope: concrete Playwright/Chromium implementation evidence for the AVP-BROWSER-014 excluded-state interference obligation. This review does not change AEP-0011, Browser v0.1 schemas, portable TCK semantics, or case ownership.

## 1. Decision

The semantic implementation is acceptable for its stated scope.

The concrete reference path now proves a real material-interference case instead of relying only on the earlier synthetic execution-condition switch:

1. a Browser resource is provisioned from a governed localhost execution fixture;
2. canonical selected Browser v0.1 state is independently projected and digested;
3. evaluator/control verifies that the controlled Service Worker/Cache Storage surface starts clean;
4. the clean controlled resource returns the network baseline;
5. evaluator/control installs a Service Worker whose install transaction creates a controlled Cache Storage entry;
6. independent observation confirms registration, cache residue, fresh-client controller state, and changed resource behavior;
7. canonical selected Browser v0.1 state is reprojected;
8. the selected digest is unchanged;
9. because excluded state materially changed behavior while selected state remained equal, the resource is marked interfering;
10. the ordinary Browser observer rejects subsequent authoritative projection through the existing execution-condition gate.

This is the required fail-closed direction: equal selected cookie/localStorage state is not treated as sufficient evidence when materially relevant excluded state has been demonstrated.

## 2. Authority boundary

The implementation preserves the repository authority ordering:

`Accepted AEP-0011 -> Browser normative spec -> requirement index -> schemas -> provider-neutral TCK -> backend-neutral harness -> concrete provider implementation -> implementation evidence`

Specifically:

- Service Worker and Cache Storage are **not** added to BrowserStateImage;
- no partition/service-worker/cache selector is added to the Manifest;
- Playwright APIs do not define Browser protocol semantics;
- the existing acceptance BAE-011 residual-state evidence informed test design but is not imported as runtime or conformance authority;
- `PlaywrightBrowserExcludedStateControl` is evaluator/control-only and absent from BrowserSUT;
- the portable observer remains responsible for rejecting an execution condition that has been proven invalid;
- no Browser TCK case ID is activated.

## 3. Why localhost is explicit

Service Worker registration requires a secure or potentially trustworthy context. The governed excluded-state execution fixture therefore materializes its selected origin as an ephemeral `http://localhost:<port>` origin.

This choice is explicit evidence setup, not a hidden provider escape hatch:

- no Chromium `--unsafely-treat-insecure-origin-as-secure` flag is used;
- no provider-specific launch flag is added to the Browser backend;
- the fixture remains provider-neutral and receives the concrete browser-build binding only during materialization;
- `localhost` is used only because the Web Platform loopback trust exception makes the Service Worker proof possible over the local evidence server.

The normal `a.test`/`b.test` execution fixture remains unchanged for the broader Browser profile.

## 4. Evidence acceptance conditions

The concrete proof refuses to mark interference unless all of the following are independently established:

- proof origin is a canonical selected localStorage origin;
- Service Worker and Cache Storage capabilities are available in a trustworthy context;
- initial registration count is zero;
- initial Cache Storage name set is empty;
- initial client is not Service Worker controlled;
- controlled resource matches the expected clean network baseline;
- controlled Service Worker reaches an active ready registration;
- expected cache name is observable;
- a fresh client is controlled;
- controlled resource behavior changes to the exact expected interfering result;
- canonical selected BrowserStateImage digest after excluded-state setup is byte-identity-equivalent to the digest before setup.

The control does **not** use:

- fixed sleeps;
- `networkidle` as a correctness oracle;
- provider command completion as protocol authority;
- Service Worker registration presence alone as proof of interference.

## 5. Resource isolation evidence

A separate real Chromium control provisions two sibling Browser resources backed by distinct BrowserContexts.

After one resource is contaminated and proven interfering, the sibling resource remains:

- free of Service Worker registrations;
- free of Cache Storage residue;
- uncontrolled by a Service Worker;
- behaviorally equal to the network baseline;
- independently projectable with its original selected digest.

This closes the concrete resource-local contamination concern for the controlled Service Worker/Cache Storage proof.

It does not by itself prove every excluded browser surface is noninterfering or isolated.

## 6. Semantic-head validation

At semantic head `ea37ee6971fe416774fbf8d5af260da9fcdbddca`:

- CI #750 — **SUCCESS**
- Governance #837 — **SUCCESS**
- Browser Reference #16 — **SUCCESS**
- Relational Parity #143 — **SUCCESS**

Browser Reference #16 executed 25 real-browser tests successfully against:

- Playwright Python `1.62.0`;
- Chrome for Testing `151.0.7922.34` / Playwright Chromium revision 1234.

The three new excluded-state tests passed:

1. `test_material_interference_fails_closed_with_selected_digest_unchanged`
2. `test_excluded_state_isolation_is_resource_local`
3. `test_proof_rejects_unselected_origin`

## 7. Remaining AVP-BROWSER-014 boundary

This slice proves one materially relevant excluded-state family: controlled Service Worker + Cache Storage behavior.

It does **not** claim universal coverage of all state excluded from Browser v0.1. In particular, later executed-profile closure must still decide how to account for other materially relevant surfaces, including IndexedDB where scenario behavior can depend on it.

The safe rule remains:

> If excluded state can materially influence scenario behavior and the execution identity/isolation policy does not make that influence irrelevant, verification must fail closed.

A future slice may either:

1. add a real IndexedDB interference control and prove the same fail-closed direction; or
2. prove that the governed fresh-context isolation/materialization policy makes the relevant excluded surface noninterfering for the executed profile.

No schema expansion is implied by either option.

## 8. Quality and architecture review

Accepted implementation properties:

- concrete responsibility is isolated in `playwright_browser/excluded_state.py`;
- immutable dataclasses carry observations/evidence;
- BrowserSUT remains narrow (`snapshot/reset/restore/release` only);
- no generic `BaseBrowserBackend`, storage-provider hierarchy, CDP abstraction, or broad `supports_*` capability layer was introduced;
- the existing canonical Browser projection is reused for selected-state identity rather than reimplemented;
- evaluator evidence is resource-scoped;
- failure messages are explicit and fail closed;
- new tests are automatically included by the existing `test_playwright_browser*.py` Browser Reference gate.

The implementation does use package-private concrete resource/projection internals. This is intentional at the current single-provider stage: introducing a generic provider abstraction merely to avoid package-private composition would violate the repository's "split responsibilities; do not abstract protocol semantics" rule. Revisit only when multiple concrete consumers produce real duplication evidence.

## 9. Non-authorizations

This review does not authorize:

- merge of PR #122 or its parent stack;
- AEP-0011 Final;
- complete Browser v0.1 conformance;
- Browser TCK case activation;
- partial Browser case ownership;
- release, tag, package publication, signing, or attestation publication;
- Service Worker/Cache Storage semantics as portable protocol authority;
- repository split or generic provider/plugin framework work.

## 10. Next governed work

After this audit-record head itself passes exact-head CI/Governance/Browser Reference/Relational Parity, the next implementation slice should address the remaining excluded-state boundary, preferably **real IndexedDB material-interference evidence plus fresh-context isolation behavior**.

Only after excluded-state, Subject/evaluator secrecy, metadata-identical broken-provider controls, and the provider-neutral executed Browser TCK evaluator are all closed should the repository consider atomic activation of the eight Browser profile cases.

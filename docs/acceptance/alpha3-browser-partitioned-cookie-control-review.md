# Alpha 3 Browser Partitioned-Cookie Control Review

Status: **REVIEW-CLOSED FOR CONTROLLED CHIPS NON-ADMISSION SCOPE**

Reviewed semantic head: `e12eff37f23d983399ac41f105ad31b88745fdea`  
Owning pull request: `#120`  
Base pull request: `#119`  
AEP lifecycle: **AEP-0011 Accepted, not Final**

This review covers the concrete Playwright/Chromium partitioned-cookie fixture control and Browser v0.1 unpartitioned-state non-admission behavior only. It does not establish general excluded-state noninterference, complete Browser profile conformance, or Browser TCK ownership.

## 1. Authority boundary

Browser v0.1 selects cookies if and only if they are unpartitioned and their canonical stored domain is selected. Partition identity is not part of the BrowserStateImage cookie identity and must not be flattened into `(name, domain, hostOnly, path)`.

The concrete provider therefore uses Playwright `partitionKey` only as evaluator/control evidence that an observed cookie is partitioned. The value is never:

- emitted into BrowserStateImage;
- stored in portable cookie provenance;
- added to Manifest selection;
- treated as AVP resource identity;
- exposed through BrowserSUT;
- promoted into portable TCK vocabulary.

## 2. Privileged control review

`PlaywrightBrowserFixtureControl.seed_partitioned_cookie(...)` now implements the existing backend-neutral privileged-control responsibility with a concrete closed input shape:

```text
name
value
domain
path
topLevelSite
```

The shape is implementation/test-control data, not a serialized AVP protocol object.

The control:

1. rejects unknown fields;
2. requires non-empty string values;
3. requires a `/`-prefixed path;
4. validates the stored cookie domain through the existing Browser identity verifier;
5. validates `topLevelSite` as a canonical browser origin;
6. creates controlled CHIPS state with explicit `Secure` and `SameSite=None` provider inputs;
7. independently requires exactly one provider-observed matching cookie carrying partition metadata.

Provider inability to establish the controlled state fails closed.

## 3. Authoritative projection review

The Playwright observer now excludes provider-observed cookies carrying a non-empty `partitionKey` before building the selected unpartitioned cookie observation map.

This is a selection decision already defined by AVP-BROWSER-004, not a new provider semantic. The provider-specific field is used only to distinguish excluded partitioned state from selected unpartitioned state.

Ordinary unpartitioned cookie seeding/correlation likewise ignores partitioned siblings when validating the current selected cookie against evaluator provenance.

Partitioned cookies are never added to `_provenance`, so provider partition metadata cannot influence portable cookie identity or canonical BrowserStateImage bytes.

## 4. Real Chromium evidence

Browser Reference #12 executed the complete concrete Browser provider suite against:

- Playwright Python `1.62.0`;
- Chrome for Testing `151.0.7922.34` / Playwright Chromium revision `1234`;
- Python `3.13`;
- Ubuntu `24.04`;
- wheel-installed `[browser]` dependency path.

The suite executed 19 tests and reported:

```text
Ran 19 tests in 33.799s
OK
```

New partition-specific controls proved:

1. the privileged control rejects an open/provider-option property bag;
2. real Chromium stores and Playwright observes the controlled cookie as partitioned;
3. the partitioned selected-domain cookie is absent from BrowserStateImage;
4. adding the excluded partitioned cookie does not change the selected canonical digest in the controlled fixture;
5. verified reset preserves the excluded partitioned cookie;
6. reset also preserves a partitioned cookie whose provider-visible `(name, domain, path)` collides with an unpartitioned selected cookie.

The collision result is concrete evidence for this tested Playwright/Chromium build. It is not generalized into a portable provider deletion guarantee.

## 5. CI discovery quality fix

Browser Reference previously discovered only `test_playwright_browser_adapter.py`. A new concrete provider test module could therefore have existed without participating in the real-browser gate.

The workflow now discovers:

```text
test_playwright_browser*.py
```

This keeps the provider gate extensible without manually updating one exact filename for every Browser test module. The pattern remains narrow to the concrete Playwright Browser suite.

## 6. AVP-BROWSER-014 boundary

Controlled CHIPS non-admission does **not** prove that arbitrary partitioned state is behaviorally irrelevant.

This slice proves only that, under the controlled fixture:

- partitioned cookie state is independently observable as partitioned;
- it is not flattened into selected unpartitioned BrowserStateImage state;
- it survives verified selected-state reset;
- the selected projection remains unchanged.

A Scenario where partitioned state materially affects Subject behavior still requires AVP-BROWSER-014 treatment: independently established noninterference, immutable execution identity/policy binding, or fail-closed insufficiency.

## 7. Exact-head validation

Reviewed semantic head `e12eff37f23d983399ac41f105ad31b88745fdea` passed:

- CI #746 — **SUCCESS**;
- Governance #831 — **SUCCESS**;
- Browser Reference #12 — **SUCCESS**;
- Relational Parity #139 — **SUCCESS**.

The closure-record head containing this document must independently pass applicable gates before final exact-head review is posted.

## 8. Remaining work before Browser profile activation

At least the following execution-sensitive obligations remain:

1. positive delayed-mutation settlement integrated with the concrete Browser provider/control path;
2. real excluded-state interference creation/observation beyond the controlled noninterfering CHIPS condition;
3. concrete Subject/evaluator secrecy proof;
4. metadata-identical behaviorally broken provider controls;
5. provider-neutral Browser TCK evaluator wiring across all eight mandatory cases;
6. atomic activation of all eight Browser case IDs only after complete mandatory execution passes.

## 9. Closure result

For semantic head `e12eff37f23d983399ac41f105ad31b88745fdea`:

- privileged partitioned-cookie control: **REVIEW-CLOSED**;
- real Chromium CHIPS observation: **VERIFIED**;
- Browser v0.1 unpartitioned non-admission: **VERIFIED for the controlled fixture**;
- selected canonical digest unaffected by controlled partitioned state: **VERIFIED**;
- selected reset preserves controlled partitioned excluded state, including visible-tuple collision: **VERIFIED**;
- universal partitioned-state noninterference: **NOT CLAIMED**;
- complete Browser v0.1 conformance: **NOT ESTABLISHED**;
- Browser TCK ownership: **MUST REMAIN INACTIVE**;
- AEP-0011 Final / merge / release / publication: **NOT AUTHORIZED**.

The next governed implementation slice is positive settlement against actual Browser mutation behavior, using evaluator/control authority and the existing `BrowserSettlementLedger` rather than provider idle semantics.

# Alpha 3 Browser Positive Settlement Review

Status: **REVIEW-CLOSED FOR CONCRETE POSITIVE-SETTLEMENT SCOPE**

Reviewed semantic head: `0d927287a99fd25f1a2444e5798f01e54dd6ae26`  
Owning pull request: `#121`  
Base pull request: `#120`  
AEP lifecycle: **AEP-0011 Accepted, not Final**

This review covers the concrete Playwright evaluator/control mechanism used to create and observe one delayed selected-state mutation and its composition with the existing provider-neutral `BrowserSettlementLedger`. It does not establish complete Browser v0.1 conformance, activate Browser TCK ownership, or authorize merge/release work.

## 1. Settlement authority remains provider-neutral

AVP-BROWSER-015 requires a positive profile-relevant settlement witness. The concrete provider must not redefine that witness as browser idleness, network idleness, event-loop quiet, elapsed time, automation command completion, or provider export completion.

The implementation preserves that boundary:

```text
BrowserSettlementLedger
  -> owns admission closure
  -> owns accepted relevant mutation set
  -> owns explicit terminal outcomes
  -> gates authoritative projection

PlaywrightBrowserMutationControl
  -> creates one concrete real-browser mutation
  -> exposes evaluator-observable mutation terminal evidence
  -> may demonstrate that networkidle occurred earlier
  -> never receives or mutates BrowserSettlementLedger
  -> cannot self-certify projection eligibility
```

No provider callback or browser event marks the ledger terminal automatically.

## 2. Concrete control design

`src/avp_ref/tck_adapter/playwright_browser/settlement.py` introduces `PlaywrightBrowserMutationControl`.

The control is evaluator-only and deliberately narrow. It can:

- start one delayed localStorage mutation on an exact selected Manifest origin;
- preserve the existing Browser DOMString encoding/decoding discipline;
- observe whether the explicit mutation terminal predicate has become true;
- wait on that exact terminal predicate;
- observe Playwright `networkidle` only for the purpose of proving that it can precede settlement;
- release evaluator-owned mutation sessions;
- enforce resource ownership of a mutation session.

It cannot:

- accept or mutate `BrowserSettlementLedger`;
- close Subject admission;
- mark an accepted mutation terminal in the portable ledger;
- authorize projection;
- expose a generic `wait_until_idle()` abstraction;
- expose Page/BrowserContext through BrowserSUT;
- become a general browser automation API.

## 3. Explicit mutation terminal

The controlled real-browser mutation uses a selected origin and writes an exact localStorage key/value after a bounded evaluator-controlled delay. The private fixture page exposes one evaluator-observed boolean terminal predicate only after the localStorage write has executed.

The delay is not the settlement predicate. It is merely a deterministic way to keep accepted work unresolved long enough to demonstrate the invalidity of provider idleness as a witness.

Accepted completion is established only when:

1. the concrete evaluator observes the explicit mutation terminal;
2. evaluator authority decides that this constitutes the terminal outcome for the already accepted mutation; and
3. evaluator authority explicitly records that terminal outcome in `BrowserSettlementLedger`.

The provider never performs step 3 itself.

## 4. Real Chromium ordering proof

Browser Reference #14 executed the concrete Browser suite against:

- Playwright Python `1.62.0`;
- Chrome for Testing `151.0.7922.34` / Playwright Chromium revision `1234`;
- Python `3.13`;
- Ubuntu `24.04`;
- wheel-installed `[browser]` dependency path.

The suite executed 22 tests and reported:

```text
Ran 22 tests in 49.870s
OK
```

The key settlement test proves this exact sequence against the real browser:

1. evaluator registers `selected-localstorage-mutation` as accepted relevant work in `BrowserSettlementLedger`;
2. evaluator control starts the delayed selected localStorage mutation;
3. evaluator closes Subject admission;
4. Playwright reaches `networkidle` while the mutation terminal is still false;
5. authoritative projection is rejected as unsettled;
6. a new accepted mutation after admission closure is rejected;
7. the concrete browser mutation reaches its explicit terminal predicate;
8. authoritative projection is **still rejected** because provider-observed completion has not modified the ledger;
9. evaluator explicitly calls `ledger.mark_terminal(...)` for the already accepted mutation;
10. authoritative projection is accepted;
11. the independent observer sees the exact terminal localStorage value;
12. the resulting canonical digest differs from the baseline as expected.

This is direct executed evidence that neither `networkidle` nor provider terminal completion self-certifies AVP settlement.

## 5. No sleep/quiet-time authority

PASS.

The test does not satisfy settlement by sleeping for a duration or by assuming that elapsed quiet time means work completed.

`delay_ms` exists only inside the controlled browser mutation to create a period during which:

- network idleness can already hold;
- accepted selected-state work is still unresolved;
- projection must remain forbidden.

Completion waiting uses an explicit mutation predicate rather than elapsed time.

## 6. Admission closure proof

PASS.

After `BrowserSettlementLedger.close_subject_admission()`, a new call to `accept_relevant_mutation(...)` is rejected.

This proves that the settlement witness is not only “all currently known work finished”; the evaluator also closes admission of new Subject-side-effect work for the observed boundary before accepting an authoritative projection.

## 7. Resource ownership and control secrecy

PASS for the concrete control scope.

Mutation sessions are keyed by Browser resource handle plus mutation id. A mutation created for one Browser resource cannot be observed as a session of another resource.

The Page used to coordinate the mutation is retained inside the evaluator control. It is not returned through BrowserSUT, not serialized into BrowserStateImage, and not exposed through the portable conformance vocabulary.

This is necessary implementation separation but is not, by itself, the complete AVP-BROWSER-019 Subject/evaluator secrecy proof. That broader security obligation remains open.

## 8. Code-quality review

The implementation intentionally adds one concrete responsibility rather than expanding `PlaywrightBrowserBackendHarness` into a broad automation object.

Quality properties:

- settlement semantics remain in the existing provider-neutral ledger;
- the provider helper is isolated in `playwright_browser/settlement.py`;
- mutation input is exact selected origin plus one closed localStorage entry;
- invalid origin and invalid delay fail before browser mutation;
- duplicate mutation ids fail closed;
- mutation lookup is resource-owned;
- cleanup closes retained evaluator pages;
- no generic action/navigation/evaluate API is introduced;
- no provider-specific settlement field is added to Browser Manifest/Image;
- no TCK expectation is weakened.

The project rule remains:

> 拆职责，不抽象协议 / split responsibilities; do not abstract protocol semantics.

## 9. Exact-head validation of semantic implementation

Reviewed semantic head `0d927287a99fd25f1a2444e5798f01e54dd6ae26` passed:

- CI #748 — **SUCCESS**;
- Governance #834 — **SUCCESS**;
- Browser Reference #14 — **SUCCESS**;
- Relational Parity #141 — **SUCCESS**.

The closure-record head containing this audit must independently pass applicable gates before final exact-head closure review is posted.

## 10. Remaining work before Browser profile activation

Positive settlement against real Browser mutation behavior is now demonstrated for this controlled selected-state mutation. Complete Browser v0.1 conformance remains unestablished.

At least the following work remains:

1. real excluded-state interference creation/observation or an independently justified immutable-binding/noninterference path under AVP-BROWSER-014;
2. concrete Subject/evaluator secrecy proof under AVP-BROWSER-019;
3. metadata-identical behaviorally broken provider controls required by AVP-BROWSER-020;
4. provider-neutral Browser TCK evaluator wiring across all eight mandatory Browser cases;
5. atomic activation of all eight Browser case IDs only after the complete mandatory profile executes successfully.

## 11. Closure result

For semantic head `0d927287a99fd25f1a2444e5798f01e54dd6ae26`:

- real delayed selected-state mutation control: **REVIEW-CLOSED**;
- provider network-idle insufficiency: **VERIFIED**;
- provider terminal completion insufficiency without evaluator ledger update: **VERIFIED**;
- Subject admission closure against new accepted work: **VERIFIED**;
- evaluator-owned terminal recording before accepted projection: **VERIFIED**;
- independent post-settlement selected-state observation: **VERIFIED**;
- generic browser-idle abstraction: **NOT INTRODUCED**;
- complete Browser v0.1 conformance: **NOT ESTABLISHED**;
- Browser TCK ownership: **MUST REMAIN INACTIVE**;
- AEP-0011 Final / merge / release / publication: **NOT AUTHORIZED**.

The next governed work unit should address AVP-BROWSER-014 real excluded-state interference/noninterference evidence before moving to the concrete Subject/evaluator secrecy slice.

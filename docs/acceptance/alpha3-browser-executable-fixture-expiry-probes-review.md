# Alpha 3 Browser Executable Fixture and Expiry Probes Review

Status: **REVIEW-CLOSED FOR EXECUTABLE-FIXTURE / EXPIRY-RESOLUTION SCOPE**

Reviewed semantic head: `9462dee93781630aa0ff103e9226aa60fb5e2823`  
Owning pull request: `#119`  
Base capability-audit pull request: `#118`  
AEP lifecycle: **AEP-0011 Accepted, not Final**

This review covers the provider-neutral executable Browser fixture and the concrete Playwright/Chromium expiry-resolution probes only. It does not establish complete Browser v0.1 conformance, activate Browser TCK ownership, alter Browser normative semantics, or authorize merge/release work.

## 1. Authority boundary

The authority direction remains:

```text
Accepted AEP-0011
  -> Browser Spec
  -> requirement index / schemas
  -> provider-neutral Browser TCK
  -> backend-neutral Browser harness
  -> provider-neutral executable fixture
  -> concrete Playwright/Chromium implementation evidence
```

The executable fixture and Chromium observations are implementation/conformance infrastructure. They do not redefine BrowserStateImage, cookie expiry representation, or portable TCK expectations.

## 2. Fixture-role separation

Two fixture responsibilities are now explicit.

### 2.1 Canonical / serialization fixture

`conformance/fixtures/browser-state/v0.1/fixture-source.json`

Retains the arbitrary persistent-cookie expiry vector:

```text
unixSeconds = 1800000000
nanoseconds = 123456789
```

This fixture remains valid for provider-neutral canonicalization, closed-shape, identity, and wire-representation coverage. Its arbitrary nanosecond value is not treated as a requirement that every concrete browser natively materialize that instant.

### 2.2 Provider-neutral executable fixture

`conformance/fixtures/browser-state/v0.1/execution-fixture-source.json`

Uses a distinct fixture revision and a whole-second persistent expiry while preserving the same provider-neutral Browser concepts. It contains no Playwright, Chromium, CDP, BiDi, provider handle, native profile path, or provider capability branch.

The provider integration suite no longer creates its normal lifecycle fixture by mutating the serialization fixture in memory. This removes an ambiguous test-only compatibility rewrite and makes the executable input reviewable as repository state.

## 3. Real Chromium expiry-resolution result

At reviewed head `9462dee93781630aa0ff103e9226aa60fb5e2823`, Browser Reference #10 executed against:

- Playwright Python `1.62.0`;
- Chrome for Testing `151.0.7922.34` / Playwright Chromium revision `1234`;
- Python `3.13`;
- Ubuntu `24.04`;
- wheel-installed `[browser]` optional dependency path.

The real-browser suite executed 14 tests and reported:

```text
Ran 14 tests in 33.156s
OK
```

The expiry probes establish the following concrete implementation facts.

### 3.1 Whole-second expiry

PASS.

The executable fixture's persistent cookie round-trips through actual Chromium observation and independently reprojects to the expected canonical BrowserStateImage identity.

### 3.2 Non-zero microsecond expiry

PASS.

A persistent expiry with:

```text
nanoseconds = 123456000
```

round-trips exactly through the tested Playwright/Chromium path. The provider therefore demonstrates a non-zero fractional-second positive path rather than only an integer-second convenience path.

This is concrete capability evidence for the tested engine/version. It is not a universal browser precision requirement.

### 3.3 Non-representable arbitrary nanosecond input

PASS as a negative control.

The serialization fixture's `123456789ns` value is not silently rounded and accepted. Provisioning fails closed when actual observed browser expiry differs from the requested portable state.

This preserves the distinction between wire representability and concrete native storage resolution.

### 3.4 Integer-truncation broken behavior

PASS as a negative control.

After a microsecond expiry is established, a provider-side mutation replacing the actual browser expiry with integer seconds while leaving evaluator provenance unchanged is rejected by authoritative projection.

This proves the implementation does not accept provenance plus approximate provider state as lossless expiry evidence.

### 3.5 Provenance-only manufactured fractional expiry

PASS as a negative control.

Changing evaluator provenance to claim a fractional expiry while actual browser state remains whole-second is rejected. Provenance can establish omitted identity/state facts only when consistent with current browser observation; it cannot manufacture selected state absent from the browser.

### 3.6 Session versus persistent state

PASS.

Observed session cookies remain `persistent=false` without an `expiry` field, while persistent cookies retain the exact admitted expiry representation.

## 4. Existing provider guarantees remain intact

The expanded suite continues to verify:

- browser execution identity binding;
- cookie selection independent of localStorage selection;
- sibling Browser resource isolation;
- selected reset preserving excluded cookie state;
- real snapshot/reset/restore plus independent reprojection;
- execution-binding drift rejection;
- temporal restore ineligibility rejection;
- exact UTF-16 localStorage behavior inherited from the provider foundation.

No Browser case ID was added to `ReferenceConformanceAdapter.supported_case_ids`.

## 5. Exact-head validation

Reviewed semantic head `9462dee93781630aa0ff103e9226aa60fb5e2823` passed:

- CI #744 — **SUCCESS**;
- Governance #828 — **SUCCESS**;
- Browser Reference #10 — **SUCCESS**;
- Relational Parity #137 — **SUCCESS**.

Green automation is supporting evidence, not protocol authority.

## 6. Code-quality review

The implementation deliberately avoids adding a new provider abstraction merely to host expiry probes.

No changes were required to the concrete provider's production behavior for this slice. The existing observer already enforced exact current-observation/provenance consistency; the new tests exercise that behavior against real Chromium rather than weakening it to accommodate fixture values.

Provider-private context/provenance access in the integration test is limited to concrete negative-control injection. Those probes are not portable SUT APIs and must not migrate into the BrowserSUT or provider-neutral fixture-control Protocol merely for test convenience.

The project rule remains:

> 拆职责，不抽象协议 / split responsibilities; do not abstract protocol semantics.

## 7. Remaining mandatory work before Browser profile activation

The expiry-resolution work is no longer a blocker for the tested Chromium path when the actual selected cookie expiry is exactly observable. Complete Browser v0.1 conformance is still not established.

Remaining execution-sensitive obligations include at least:

1. real partitioned-cookie negative control proving partitioned state is not admitted as unpartitioned selected state;
2. positive delayed-mutation settlement against actual browser behavior, including unresolved accepted work rejection;
3. real materially interfering excluded-state creation/observation or an independently justified noninterference/binding path;
4. Subject/evaluator secrecy proof at the concrete Subject surface;
5. metadata-identical behaviorally broken provider controls;
6. provider-neutral Browser TCK evaluator wiring across all eight mandatory cases;
7. atomic activation of all eight Browser case IDs only after complete mandatory execution passes.

## 8. Closure result

For semantic head `9462dee93781630aa0ff103e9226aa60fb5e2823`:

- fixture-role separation: **REVIEW-CLOSED**;
- whole-second Chromium expiry fidelity: **VERIFIED**;
- non-zero microsecond Chromium expiry fidelity: **VERIFIED**;
- arbitrary non-representable nanosecond request: **FAIL-CLOSED VERIFIED**;
- integer-truncation negative control: **VERIFIED**;
- provenance-only fabricated fractional state: **REJECTED**;
- session/persistent distinction: **VERIFIED**;
- Browser v0.1 complete conformance: **NOT ESTABLISHED**;
- Browser TCK ownership: **MUST REMAIN INACTIVE**;
- AEP-0011 Final: **NOT AUTHORIZED**;
- merge/release/publication/signing/attestation: **NOT AUTHORIZED**.

The next governed implementation slice should address real Browser execution controls, beginning with partitioned-state non-admission and positive settlement, without introducing a generic browser automation abstraction.

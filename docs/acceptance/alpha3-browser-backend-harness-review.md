# Alpha 3 Browser Backend-Neutral Harness Review

Status: **REVIEW-CLOSED — BBIR ARCHITECTURE PREREQUISITES SATISFIED; PROVIDER IMPLEMENTATION REMAINS SEPARATELY GATED**

Reviewed implementation head: `f234ded51d7cf83b96af817dc627628532e2851e`  
Owning PR: `#116`  
Parent readiness decision: `docs/acceptance/alpha3-browser-backend-implementation-readiness.md`  
Normative baseline: `13974bf52864d95f4b670ed31068d05674ebd8ba` (`#114`)  
AEP lifecycle: **AEP-0011 Accepted, not Final**

## 1. Review question

Does PR #116 establish the backend-neutral implementation architecture required by BBIR-001..005 without:

- changing Browser protocol semantics;
- allowing provider behavior to define protocol meaning;
- exposing privileged fixture/browser control through the portable SUT/Subject surface;
- approximating standards-owned identity semantics with a convenience parser;
- claiming partial Browser TCK support before a real Browser implementation exists; or
- introducing a speculative generic browser-automation abstraction?

## 2. Exact reviewed change surface

At reviewed head `f234ded51d7cf83b96af817dc627628532e2851e`, PR #116 changes exactly three files:

1. `src/avp_ref/tck_adapter/browser_harness.py`
2. `conformance/fixtures/browser-state/v0.1/fixture-source.json`
3. `tests/test_browser_conformance_harness.py`

It does **not** change:

- `rfcs/AEP-0011-browser-resource-profile.md`;
- either Browser normative specification;
- `spec/browser/requirement-index.yaml`;
- either Browser JSON Schema;
- the Browser TCK profile or any of the eight portable Browser TCK cases;
- `conformance/tck/registry.yaml`;
- the active normative-candidate registry;
- `ReferenceConformanceAdapter.supported_case_ids` ownership;
- package dependencies;
- release/version state.

The implementation is therefore downstream of the closed Browser authority slice rather than a competing source of Browser semantics.

## 3. Exact-head validation

Reviewed head `f234ded51d7cf83b96af817dc627628532e2851e` passed:

- CI #733 — **success**;
- Governance #813 — **success**;
- Relational Parity #126 — **success**.

The first CI attempt at earlier head `233fdfdd64e2172f8c370f88bdb66e929e0be669` correctly failed all Python Quality lanes because the new test module imported `pytest` while the repository quality environment intentionally uses `unittest` and does not install pytest. The correction converted the focused tests to the repository's existing `unittest` framework. No dependency, validator, protocol rule, TCK expectation, or gate was weakened to obtain green CI.

## 4. Authority-direction review

The implementation preserves:

```text
Accepted AEP-0011
  -> Browser Spec
  -> requirement index
  -> closed Schema
  -> provider-neutral Browser TCK
  -> backend-neutral Browser conformance harness
  -> later provider-specific Browser implementation
```

The harness derives its semantics from the existing Browser profile:

- exact Manifest/Image shape and constants;
- exact DOMString UTF-16-code-unit representation;
- Browser collection ordering before RFC 8785 JCS;
- SHA-256 Artifact/state identity;
- cookie portable identity `(name, domain, hostOnly, path)`;
- complete selected localStorage/cookie projection;
- positive settlement rather than provider idleness;
- Environment-owned `SnapshotRef`;
- independent reset/restore reprojection;
- successful restore fidelity exactly `STATE_EQUIVALENT`;
- execution-condition and cookie temporal-eligibility fail-closed hooks.

No implementation behavior is promoted into a new Browser requirement.

## 5. BBIR-001 — backend-neutral SUT/observer harness

**Disposition: CLOSED AS AN ARCHITECTURE PREREQUISITE.**

`browser_harness.py` now separates three implementation roles:

- `BrowserSUT` — narrow Browser resource lifecycle only;
- `BrowserAuthoritativeObserver` — evaluator-authorized independent observation/eligibility checks;
- `BrowserBackendHarness` — composition/provisioning boundary that supplies the SUT, observer, and privileged control.

`BrowserSUT` does not expose navigation, clicks, arbitrary JavaScript, CDP/WebDriver commands, page/context/session handles, launch configuration bags, provider names, or generic browser capabilities.

The shared `BrowserConformanceHarness` does not trust provider/SUT success claims as conformance evidence. It independently canonicalizes observer state and verifies snapshot/reset/restore claims against independently computed state identity.

This closes the missing shared harness architecture. It does **not** prove that a future provider implementation satisfies Browser v0.1; that remains an executed TCK obligation.

## 6. BBIR-002 — immutable materialized Browser fixture

**Disposition: CLOSED AS AN ARCHITECTURE PREREQUISITE.**

The provider-neutral fixture source is stored under:

`conformance/fixtures/browser-state/v0.1/fixture-source.json`

It contains logical fixture data and named origin slots rather than incidental CI ports as fixed protocol identity.

`materialize_browser_fixture(...)` requires every declared origin slot to resolve exactly once before provisioning. It:

1. rejects missing, duplicate, or undeclared resolution;
2. passes exact resolved origins through the standards-aware Browser identity verifier;
3. constructs the exact Manifest using those resolved tuple origins;
4. converts fixture DOMString code-unit vectors into the normative Browser wire representation;
5. canonicalizes Manifest and baseline StateImage;
6. computes exact RFC 8785 JCS/SHA-256 identities; and
7. freezes the resulting materialized fixture recursively.

No unresolved origin placeholder survives into the materialized fixture.

The shared harness intentionally does not implement a substitute WHATWG URL parser with `urllib.parse` or another RFC-oriented convenience parser. Canonical tuple-origin/stored-domain admission remains behind `BrowserIdentityVerifier`, to be implemented later through a reviewed standards-compatible concrete mechanism.

## 7. BBIR-003 — privileged fixture/control separation

**Disposition: CLOSED AS AN ARCHITECTURE PREREQUISITE.**

`BrowserFixtureControl` is a distinct evaluator/test-driver boundary. Its logical controls cover the categories required by the current Browser TCK architecture, including baseline seeding, cookie/localStorage seeding, partitioned-cookie controls, execution-binding drift, excluded-state interference, evaluator-private state, and optional evaluator-owned cookie provenance.

The control object is exposed by the evaluator-side `BrowserConformanceHarness`; it is deliberately absent from `BrowserSUT`.

The focused test verifies that control operations such as cookie seeding are not reachable through the SUT surface.

A concrete Browser provider will still need to implement the required negative controls honestly through real browser/test infrastructure. This review closes the **missing control boundary**, not the future provider-specific control behavior.

### Sibling isolation

No `provision_sibling()` or similar Browser-specific abstraction is needed. Sibling isolation is tested by provisioning the same reviewed backend twice through the ordinary `provision(fixture)` boundary, applying privileged mutation/control to only one resource, and independently projecting both resources.

A provider implementation must supply independent resource ownership/handles and must fail the executed Browser identity case if selected authoritative state crosses that boundary. The shared architecture already exposes the required provision/control/observer separation; the real cross-resource behavior remains provider TCK evidence.

## 8. BBIR-004 — settlement and independent reprojection

**Disposition: CLOSED AS AN ARCHITECTURE PREREQUISITE.**

`BrowserSettlementLedger` encodes the portable facts required for a positive settlement witness:

- Subject-side-effect admission starts open;
- accepted profile-relevant mutations are explicitly registered;
- admission can be closed;
- every accepted mutation must reach an explicit terminal state;
- authoritative projection is rejected while admission remains open or accepted work remains unresolved.

No provider idle/network-idle signal participates in this decision. A focused test sets a synthetic provider-idle condition while an accepted localStorage mutation remains unresolved and verifies that authoritative projection is still rejected.

Reset and restore deliberately require separate pre-operation and post-operation settlement witnesses. This prevents a pre-operation settled state or provider command completion from being reused as evidence that post-operation authoritative state has settled.

After reset/restore, the harness independently observes and re-canonicalizes the selected Browser state. False-success reset/restore test doubles are rejected when they fail to re-establish the required digest.

Restore additionally invokes evaluator-owned temporal eligibility before accepting the restore operation and reports successful fidelity only as `STATE_EQUIVALENT`.

## 9. BBIR-005 — atomic Browser support activation

**Disposition: CLOSED/PRESERVED.**

The reference composite remains unchanged and owns no Browser TCK case IDs at reviewed head `f234ded51d7cf83b96af817dc627628532e2851e`.

The focused harness test verifies that `ReferenceConformanceAdapter.supported_case_ids` remains disjoint from all eight Browser case IDs.

Therefore Browser remains an active implementation-pending candidate with **zero reference Browser conformance claim**. No partial case support is registered.

A later provider implementation may activate Browser support only when all eight mandatory Browser cases execute honestly as one complete supported candidate profile.

## 10. Canonicalization review

The shared harness independently owns Browser profile canonicalization needed to verify provider observations:

- exact closed Manifest/Image field sets;
- constant profile/revision/representation identities;
- duplicate selection rejection;
- exact DOMString UTF-16 code-unit encode/decode;
- unpadded canonical base64url and zero-pad-bit validation;
- localStorage key ordering by unsigned UTF-16 code units;
- origin/domain ordering by unsigned UTF-8 canonical text;
- cookie identity and ordering;
- session/persistent expiry shape and range;
- selected-origin completeness;
- selected-cookie-domain admission;
- Manifest digest binding;
- RFC 8785 JCS bytes and SHA-256 identity.

Focused tests confirm provider/enumeration-order independence and the accepted unmatched-surrogate vector.

The harness does not make browser/provider enumeration order authoritative.

## 11. Security-boundary review

The shared harness intentionally creates **no Subject browser-state API**. Privileged state seeding/control lives only in the evaluator-side fixture-control role, while authoritative observation lives in the evaluator observer role.

This is the correct pre-provider architecture because inventing a Subject Browser API merely to test secrecy would enlarge protocol/implementation surface without authority.

A concrete provider implementation must later prove `AVP-TCK-BROWSER-SECURITY-001` through its actual Subject execution/context path, including that evaluator-private selected cookie/localStorage state and browser automation/debug handles are not disclosed.

This provider behavior is not claimed by #116.

## 12. Provider-neutrality and dependency review

No Playwright, Selenium, WebDriver, CDP, BiDi, Chromium, Firefox, WebKit, browser driver, browser binary, or provider library was added to the base package.

The implementation introduces no:

- `BaseBrowserBackend`;
- generic plugin mechanism;
- broad inheritance framework;
- provider property bag;
- generic `supports_*` family;
- navigation/action abstraction unrelated to the selected state profile.

The harness is Browser-profile-specific because its responsibilities are derived from Browser v0.1 TCK semantics. This follows **“拆职责，不抽象协议 / split responsibilities; do not abstract protocol semantics.”**

## 13. Findings

### Protocol blockers

**None.**

No Browser normative change is required by this implementation review.

### Harness architecture blockers

**None remaining for BBIR-001..005.**

The required shared architecture now exists and has passed repository-wide exact-head validation.

### Provider implementation obligations still open

The following are intentionally **not** claimed complete by #116 and remain requirements for the first real Browser reference implementation:

1. standards-compatible concrete tuple-origin/stored-domain admission;
2. actual isolated Browser resource provisioning;
3. actual complete unpartitioned cookie/localStorage observation;
4. cookie provenance sufficient to establish portable fields when the transport is lossy;
5. real `SameSite=Default` distinction and temporal restore eligibility;
6. actual partitioned-state exclusion;
7. actual execution-input drift and excluded-state controls;
8. actual held/terminal mutation settlement instrumentation;
9. real sibling-resource isolation behavior;
10. actual evaluator-private-state/privileged-control secrecy through the Subject execution path;
11. actual snapshot/reset/restore behavior with independent reprojection;
12. metadata-identical broken-behavior rejection;
13. execution of **all eight** mandatory Browser TCK cases through the provider/browser boundary;
14. atomic Browser case-support activation only after item 13 is complete.

These are provider implementation/conformance obligations, not reasons to add provider behavior to the shared protocol or shared harness prematurely.

## 14. Review decision

**BBIR-001 — CLOSED as shared harness architecture.**  
**BBIR-002 — CLOSED as immutable materialized-fixture architecture.**  
**BBIR-003 — CLOSED as privileged control-seam architecture.**  
**BBIR-004 — CLOSED as positive-settlement / independent-reprojection architecture.**  
**BBIR-005 — CLOSED/PRESERVED by zero partial Browser support.**

The Browser backend-neutral harness slice is therefore **REVIEW-CLOSED for its implementation-architecture scope**.

This decision authorizes review of a separate first provider-specific Browser reference-implementation work unit against the reviewed harness. It does **not** authorize merge of the active Browser stack, AEP-0011 Final, release/version selection, publication, signing, attestation, repository split, plugin-framework work, or automatic activation of Browser conformance support.

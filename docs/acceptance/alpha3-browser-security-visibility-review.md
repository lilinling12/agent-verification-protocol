# Alpha3 Browser Security Visibility Review

Status: **IMPLEMENTATION REVIEW-CLOSED CANDIDATE — EXACT-HEAD GATES REQUIRED**

Reviewed semantic head: `3a65eb69c50b6e7f09a27973330c26815ea37ec5`

Scope: concrete Playwright/Chromium implementation evidence for AVP-BROWSER-019 Subject/Evaluator/Control and Evidence visibility separation. This review does not change AEP-0011, Browser v0.1 schemas, portable TCK semantics, or Browser case ownership.

## 1. Decision

The semantic implementation is acceptable for its stated scope.

The concrete Chromium reference path now proves the AVP-BROWSER-019 negative-control directions with real browser state and explicit Artifact authority separation:

1. evaluator/control seeds real selected evaluator-private cookie and localStorage state;
2. evaluator independently observes those private values to prove they actually exist;
3. Subject-facing observation is produced through a deliberately narrow frozen/slots value object containing only the Scenario-authorized public observation;
4. the Subject-visible object carries no Page, BrowserContext, Browser resource, fixture-control, lifecycle, evaluate, navigation, snapshot, reset, restore, launch, debugging, or equivalent privileged handle;
5. a separate selected Subject origin does not observe the evaluator-private cookie/localStorage values held on the evaluator-private origin;
6. an unselected Subject origin is rejected rather than being silently admitted;
7. retained Artifact SHA-256 digest is treated as identity only and is rejected when supplied as retrieval authorization;
8. retrieval requires a distinct opaque evaluator-owned capability;
9. a capability for one retained Artifact cannot retrieve another Artifact's bytes;
10. redacted bytes are retained as a distinct Artifact and therefore receive a distinct digest from the unredacted evaluator-private bytes.

This is the required separation direction: authoritative Browser state may remain evaluator-private without being disclosed to Subject authority, and Artifact identity does not imply retrieval or declassification authority.

## 2. Authority boundary

The implementation preserves the repository authority ordering:

`Accepted AEP-0011 -> Browser normative spec -> requirement index -> schemas -> provider-neutral TCK -> backend-neutral harness -> concrete provider implementation -> implementation evidence`

Specifically:

- no new Subject browser-automation protocol is introduced;
- BrowserSUT remains narrow and does not gain launch/debug/evaluate/navigation or lifecycle-control APIs;
- Playwright `Page` and `BrowserContext` remain concrete evaluator/control implementation details;
- evaluator-private state may remain part of the complete selected BrowserStateImage while visibility is governed separately;
- Artifact locator identity and retrieval authorization are represented as distinct concrete concerns;
- SHA-256 digest identity never serves as a bearer capability;
- redaction creates new retained bytes and therefore a new Artifact identity;
- no Browser TCK case ID is activated.

## 3. Real private-state evidence

The security proof does not infer secrecy from an empty or failed setup.

Before asserting Subject non-disclosure, evaluator/control:

1. seeds the controlled private cookie through the existing privileged fixture control;
2. seeds the controlled private localStorage value at the selected evaluator-private origin;
3. independently re-observes the private cookie from the BrowserContext;
4. independently re-observes the private localStorage value from a page at the evaluator-private origin;
5. requires the exact expected private values to be present.

Only after that positive existence proof does the test evaluate the Subject-visible boundary.

This avoids the false-positive security pattern where a test passes only because the supposed secret was never materialized.

## 4. Subject-visible surface

The Subject-facing value object is intentionally closed and narrow.

It contains only the exact authorized observation value. It does not retain hidden references to the underlying browser page, context, resource, fixture control, or security control.

The real-browser test inspects the concrete Subject-visible object and verifies that privileged browser/lifecycle methods or handles are absent.

This is stronger than a convention such as "the Subject receives a Page but must not call evaluate()": the privileged object itself does not cross the authority boundary.

The current implementation is concrete evidence for the reference provider, not a new portable Subject interface definition.

## 5. Browser-origin visibility evidence

The governed security execution fixture uses separate selected origins for:

- the Subject-visible route;
- evaluator-private authoritative state.

The proof confirms that private state is present at the evaluator-private origin while the Subject origin observes only the authorized public value and does not observe the evaluator-private cookie/localStorage values.

The Subject observation path also fails closed for an origin outside the Manifest selection rather than widening authority through provider navigation convenience.

This origin separation is implementation evidence used to exercise AVP-BROWSER-019; it does not redefine Browser v0.1 selection semantics.

## 6. Artifact identity versus retrieval authority

The implementation explicitly separates:

- `BrowserArtifactLocator`: content identity;
- `BrowserArtifactAuthorization`: opaque evaluator-owned retrieval authority.

The locator's SHA-256 digest can name retained bytes but cannot retrieve them by itself.

Security properties accepted in this slice:

- passing a digest string as authorization is rejected;
- a capability for another retained Artifact is rejected;
- opaque authorization material is excluded from normal object `repr` output;
- repeated retention of identical Artifact bytes preserves previously issued valid capabilities rather than silently revoking them by replacing one digest-to-token mapping;
- retrieval compares opaque capability material using constant-time comparison;
- redacted and unredacted byte sequences must differ and must not share an Artifact digest.

These are concrete reference mechanics implementing the existing Security/Evidence rule; they do not create a second normative capability model.

## 7. Semantic-head validation

At semantic head `3a65eb69c50b6e7f09a27973330c26815ea37ec5`:

- CI #754 — **SUCCESS**
- Governance #842 — **SUCCESS**
- Browser Reference #20 — **SUCCESS**
- Relational Parity #147 — **SUCCESS**

Browser Reference #20 executed **35 real-browser tests successfully in 62.811 seconds** against:

- Playwright Python `1.62.0`;
- Chrome for Testing `151.0.7922.34` / Playwright Chromium revision 1234;
- Ubuntu 24.04;
- Python 3.13.

The six new security tests passed:

1. `test_artifact_digest_is_identity_not_retrieval_authorization`
2. `test_redacted_bytes_receive_distinct_artifact_identity`
3. `test_private_state_on_evaluator_origin_is_not_visible_at_subject_origin`
4. `test_real_private_state_exists_but_subject_receives_only_authorized_value`
5. `test_subject_observation_refuses_unselected_origin`
6. `test_subject_surface_exposes_no_privileged_browser_or_lifecycle_handle`

## 8. AVP-BROWSER-019 disposition

The current Chromium reference implementation now has concrete real-browser evidence for the required Subject/Evaluator/Control visibility and Artifact-authority separation directions of AVP-BROWSER-019.

Subject-visible observations do not receive evaluator-private selected state or privileged browser handles, and Artifact digest identity does not grant retrieval authority.

This is enough to close the current **implementation obligation** for AVP-BROWSER-019 in the Chromium reference path, subject to this audit-record head passing exact-head gates.

The closure remains bounded:

- it does not declare universal browser-engine security behavior;
- it does not make the concrete Subject observation object a portable AVP protocol surface;
- it does not imply that every future credential/Evidence class is automatically covered;
- future implementation paths must still compose with the existing AVP Security/Evidence classification, authorization, and visibility rules;
- any provider that exposes evaluator-private state or privileged control through its Subject boundary must fail the portable Browser security case.

## 9. Quality and architecture review

Accepted implementation properties:

- security/visibility mechanics are isolated in `playwright_browser/security.py`;
- immutable/frozen dataclasses represent the narrow concrete records;
- authorization token material is not exposed by default `repr`;
- the Subject-visible object retains no privileged browser implementation object;
- private-state existence is positively proven before non-disclosure is asserted;
- existing Browser fixture control is composed rather than duplicated;
- no generic browser-security provider hierarchy, credential broker, capability framework, or `Base*` abstraction was introduced;
- BrowserSUT remains unchanged as the portable lifecycle boundary;
- failure paths are explicit and fail closed;
- new tests are automatically included by the existing `test_playwright_browser*.py` Browser Reference gate.

This follows the repository rule: **split responsibilities; do not abstract protocol semantics**.

## 10. Remaining Browser implementation obligations

Closing the current AVP-BROWSER-019 implementation slice does **not** establish complete Browser profile conformance.

The next governed implementation obligation is AVP-BROWSER-020 executed provider-neutral conformance, specifically metadata-identical behaviorally broken provider controls.

That work must prove that portable Browser expectations reject implementations that advertise identical profile/capability metadata but violate required observable behavior. Portable expectations must not branch on Playwright, Chromium, Selenium, WebDriver, BiDi, CDP, or any provider/product name.

After AVP-BROWSER-020 implementation evidence is closed, remaining work still includes:

- provider-neutral Browser TCK evaluator wiring for all eight mandatory Browser cases;
- all eight cases genuinely executing successfully against the concrete profile;
- only then atomic activation of all eight Browser case IDs in `ReferenceConformanceAdapter`.

Partial Browser case activation remains forbidden.

## 11. Non-authorizations

This review does not authorize:

- merge of PR #124 or its parent stack;
- AEP-0011 Final;
- complete Browser v0.1 conformance;
- Browser TCK case activation;
- partial Browser case ownership;
- release, tag, package publication, signing, or attestation publication;
- concrete Playwright security-control mechanics as portable protocol authority;
- repository split or generic provider/plugin framework work.

## 12. Exact-head closure condition

This document creates a new audit-record head. REVIEW-CLOSED status may be recorded only after that exact head itself passes:

- CI;
- Governance;
- Browser Reference;
- Relational Parity.

Until then, the status remains **IMPLEMENTATION REVIEW-CLOSED CANDIDATE — EXACT-HEAD GATES REQUIRED**.

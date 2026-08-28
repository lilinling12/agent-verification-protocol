# AEP-0011 Draft → Proposed Readiness Audit

Status: **READY FOR PROTOCOL REVIEW — PROPOSED ELIGIBLE**

AEP: `rfcs/AEP-0011-browser-resource-profile.md`
Parent: AEP-0009 (Accepted)
Portability baseline: `docs/design/alpha3-browser-resource-portability-audit.md`
Audit date: 2026-08-28

## 1. Audit purpose

This audit determines whether AEP-0011 is sufficiently complete to move from `Draft` to `Proposed` under AVP governance.

`Proposed` means the design is complete enough for formal protocol review. It does **not** make the AEP normative, does not authorize an `Accepted` decision, does not authorize Browser Spec/Schema/TCK adoption, and does not authorize Playwright or another browser implementation.

This audit is evidence only. AEP-0011 remains `Draft` until a separate explicit protocol-maintainer lifecycle decision records `Draft -> Proposed`.

## 2. Governance criteria

A Draft → Proposed transition must provide a reviewable design with:

1. a written interoperability problem and bounded scope;
2. explicit alternatives and compatibility impact;
3. security and authority analysis;
4. an executable, implementation-independent conformance strategy;
5. no unresolved design blocker that would force downstream Schema, TCK, or reference code to invent portable semantics.

The later maintainer decision required for `Accepted` is intentionally outside this audit.

## 3. Problem and interoperability scope

**PASS**

AEP-0011 identifies the interoperability failure clearly: a browser is not one portable serializable state object, and Playwright/WebDriver/CDP/browser-profile mechanics cannot define AVP browser state by precedent.

The scope is deliberately narrow:

- one isolated browser-session Environment resource;
- one cohesive Browser state capability candidate;
- authoritative state limited to selected unpartitioned cookies plus selected tuple-origin `localStorage`;
- reset/snapshot/restore/state identity over that surface only;
- execution identity, Evidence, Subject automation, Network control, and Time control remain distinct concerns.

The AEP does not attempt to standardize a browser process checkpoint, universal page/locator API, DOM/JS heap serialization, networking stack, virtual time system, or complete browser profile.

## 4. Parent-authority composition

**PASS**

AEP-0011 reuses rather than duplicates:

- Environment ownership, SnapshotRef, projection, reset, restore-fidelity, stale/foreign/released-resource semantics;
- Fabric resource classification, Resource Capability identity/revision, REQUIRED/OPTIONAL participation, Subject Capability separation, composite-result honesty, non-inflating fidelity, and cleanup;
- Scenario immutable execution-input binding;
- Core `QUIESCING` and lifecycle/Validity/infrastructure/Task Verdict separation;
- Security Subject/Evaluator/Control trust planes and `SecurityAssurance`;
- Evidence/Artifact exact-byte identity and classification.

No second Episode lifecycle, Artifact digest system, restore scale, or security taxonomy is introduced.

## 5. Portable resource and capability boundary

**PASS**

The resource is an isolated browser session, not:

- a page/tab;
- a browser process;
- a profile directory;
- a Playwright `BrowserContext` object;
- a WebDriver BiDi user-context handle;
- a CDP handle.

The candidate capability is one cohesive claim:

```text
browser.session-state @ avp-browser-state-v0.1 / 0.1
```

Its exact spelling remains open to formal protocol review, but the semantic boundary does not depend on the spelling.

The AEP explicitly rejects transitional `supports_*` capability bags.

## 6. Authoritative state boundary

**PASS**

The reconciled AEP closes BR-BR-001 with an exact base state surface:

1. selected unpartitioned HTTP cookies;
2. selected tuple-origin `localStorage` entries.

The following are explicitly outside base authoritative state: partitioned cookies, `sessionStorage`, topology/history, DOM/JS heap, workers/timers/dialogs, IndexedDB, Cache Storage, Service Worker state, WebAuthn/passkey private state, downloads, screenshots/accessibility/traces/console/network/rendering output.

Excluded state is not treated as an implicit optional part of the same capability. A Scenario that materially requires excluded state cannot claim that Browser v0.1 alone restored it.

## 7. Cookie identity and state semantics

**PASS**

The AEP no longer leaves cookie identity for Schema or a backend to invent.

One portable unpartitioned cookie entry is identified by:

```text
(name, domain, hostOnly, path)
```

The state preserves name/value, canonical domain/host text, explicit host-only semantics, path, session versus persistent semantics, expiry when persistent, Secure, HttpOnly, and SameSite state.

Creation time and last-access time are intentionally excluded from Browser v0.1 identity. Expired entries are not retained in an accepted BrowserStateImage. Presentation-only input spelling such as a leading dot in a Domain attribute is not portable identity; the stored canonical domain plus `hostOnly` preserves the behaviorally relevant scope distinction.

Partitioned-cookie identity remains explicitly outside base v0.1 rather than being approximated through vendor partition keys.

This is sufficiently precise for downstream normative Schema/TCK design without using a browser product as the oracle.

## 8. Origin and localStorage identity

**PASS**

The AEP closes BR-BR-002 using standards-level tuple-origin semantics rather than backend storage identifiers.

A selected `localStorage` origin is a non-opaque tuple origin identified by `(scheme, host, port)` and represented using WHATWG origin serialization:

```text
scheme://serialized-host[:non-null-port]
```

Path, query, fragment, username, and password do not enter origin identity. Opaque origins and `file:` origin behavior are excluded from base v0.1 because they do not provide the required stable tuple-origin portability boundary.

Within one origin, exact string keys map to exact string values, with no browser enumeration/insertion/locale ordering semantics.

The downstream specification still needs exact JSON property names and canonical JSON ordering rules, but it does not need to invent the origin model.

## 9. State identity and content-addressing direction

**PASS**

AEP-0011 defines an acyclic logical resource direction:

```text
BrowserStateManifest
  -> profile/revision
  -> immutable selected cookie/origin rules
  -> canonical representation revision

BrowserStateImage
  -> manifestDigest
  -> cookies[]
  -> origins[] / localStorage[]
```

The Manifest does not point to the baseline StateImage. The baseline image binds the Manifest digest. Runtime snapshots are generated Environment/Evidence state associated with SnapshotRef and do not mutate the immutable baseline identity inputs.

The AEP requires the downstream normative specification to close one deterministic selection grammar rather than use vendor callbacks/query languages. This is representation/specification work downstream of already-bounded semantics, not a semantic hole to be filled by reference code.

Automation-library export formats are explicitly non-authoritative.

## 10. Execution identity separation

**PASS**

The AEP separates logical browser state from execution-relevant immutable identity.

When materially relied upon by the Scenario, identity may include engine family, exact build/revision, package Artifact identity, OS/architecture, headless mode, locale/timezone, viewport/device configuration, JavaScript enablement, permissions/geolocation, Service Worker policy, proxy/TLS policy, preload/extensions/configuration, or rendering inputs.

Relevance is Scenario-specific; the profile does not hash arbitrary backend metadata simply because it exists.

Product labels such as `chromium`, `firefox`, `webkit`, `playwright`, or `selenium` do not substitute for immutable identity.

## 11. Snapshot, reset, and restore fidelity

**PASS**

The AEP closes BR-BR-004 conservatively:

- snapshot captures the complete selected authoritative state;
- reset succeeds only after independent canonical reprojection to the baseline;
- restore succeeds only after independent canonical reprojection to the target snapshot;
- successful base restore reports exactly `STATE_EQUIVALENT`;
- `EXACT` is forbidden for Browser v0.1.

Backend import/clear/context-recreation/profile-directory command success cannot establish protocol fidelity.

The restriction is justified because live JS state, topology, session storage, history, workers, caches, pending operations, process continuation, and rendering/timing state are outside the selected state surface.

## 12. Operation settling and lifecycle composition

**PASS**

AEP-0011 closes BR-BR-009 without introducing a second lifecycle or a non-portable `network idle` rule.

After Core closes new Subject side-effect admission, previously accepted mutations relevant to selected cookie/`localStorage` state must reach a profile-relevant terminal outcome before an accepted final projection is formed. Projection must not mix known pre/post fragments.

This does not claim that animations, all timers, workers, rendering, or the whole network are idle.

Failure to establish trustworthy settlement prevents an accepted final projection and composes with infrastructure/Validity semantics rather than automatically becoming Agent Task Verdict failure.

## 13. Service Worker, Cache, session state, and future capability boundary

**PASS**

BR-BR-003 and BR-BR-006 are closed by explicit exclusion rather than partial emulation.

- `sessionStorage`, page topology, and history are not base restorable state;
- Service Worker registrations/lifecycle/runtime state and Cache Storage are not base restorable state;
- a Service Worker enable/disable policy may be execution identity when materially relevant, but is not evidence of restoring Service Worker state;
- future state capabilities require separate governance and executable cross-engine semantics.

This prevents one browser/backend's support matrix from becoming hidden protocol behavior.

## 14. Credential-bearing state and security

**PASS**

BR-BR-007 is closed while preserving security boundaries:

- selected cookies/`localStorage` remain authoritative even when values contain authentication material;
- confidentiality affects visibility/handling, not identity;
- evaluator-private values stay out of Subject observations;
- secret-bearing snapshots require Evidence classification/access control;
- a digest is not authorization or declassification;
- public TCK fixtures use synthetic credentials;
- WebAuthn/passkey private-key export/import is not base mandatory behavior.

Privileged browser automation/session-control channels remain Evaluator/Control authority. Browser capability support does not imply verified network isolation or inflate `SecurityAssurance`.

## 15. Evidence boundary

**PASS**

BR-BR-008 is closed by separating authoritative state from Evidence/observation.

Screenshots, DOM/accessibility material, traces, console/page errors, network events, navigation information, downloads, and diagnostics may be retained as Evidence but do not enter base Browser state equality merely because an implementation can capture them.

Redacted Evidence bytes have their own identity; rendering equality is not browser-state equality.

## 16. Subject capability boundary

**PASS**

The AEP preserves Fabric/Security separation between Resource Capability and Subject Capability.

Browser v0.1 does not define a universal click/locator/script API. Scenario actor projection separately controls any Subject-visible browser actions/observations. Provisioning, reset, snapshot, restore, credential seeding, hidden instrumentation, and evaluator diagnostics remain privileged unless separately governed.

No Playwright/WebDriver/CDP handle leaks into portable or Subject-facing authority.

## 17. Conformance strategy

**PASS**

BR-BR-010 is closed with an executable, backend-neutral strategy.

Mandatory behavior uses real-browser execution through the implementation under test. Metadata declarations, mocks, and capability self-certification cannot replace behavioral execution at the certified boundary.

The mandatory families cover isolation, immutable execution identity, baseline reprojection, tuple-origin localStorage, unpartitioned-cookie identity/attributes, canonical state identity, SnapshotRef ownership, snapshot/restore/reset, fidelity honesty, Subject/Evaluator separation, secret non-disclosure, settlement, cleanup, excluded-state failure, and metadata-identical negative implementations.

Negative controls include cross-origin flattening, omission of selected state, collapse of host-only/domain cookie identity, false restore success, false `EXACT`, evaluator-secret leakage, post-boundary mutation admission, and metadata-only self-certification.

Portable vectors cannot branch on browser/backend product names.

## 18. Multi-engine portability evidence

**PASS**

The AEP makes a necessary distinction:

- a third-party conforming implementation is **not** required to implement multiple browser engines;
- AVP's own reference portability acceptance should execute the same portable semantics across at least two materially independent engine families before the project treats the reference boundary as protected from one-engine precedent.

A three-engine matrix is desirable where practical, but product names remain test metadata, not protocol identity.

This is a reference evidence gate rather than a hidden multi-engine interoperability requirement for every implementation.

## 19. Alternatives

**PASS**

The AEP explicitly rejects, with interoperability rationale:

- Playwright-first implementation/generalization;
- Playwright `storageState` as protocol authority;
- mandatory base IndexedDB;
- base `sessionStorage`/topology/history restore;
- base Service Worker/Cache restore;
- base partitioned cookies;
- whole profile-directory snapshots;
- page-as-resource;
- process-as-resource;
- browser-actions-only profile;
- universal `network idle` settling.

These rejections keep implementation convenience downstream of portable semantics.

## 20. Backward compatibility and release boundary

**PASS**

Browser v0.1 is additive under AEP-0009.

- existing Environment/Fabric implementations need not claim it;
- `resourceKind: browser` alone remains insufficient to claim it;
- no Alpha 2 semantics change;
- no release version is selected;
- the current planned `0.3.1` maintenance release is not assigned Browser semantics;
- release-development state remains unchanged.

## 21. Transitional-implementation audit

**PASS**

No design requires:

- Playwright-first public classes generalized later;
- a generic `BaseBrowserBackend`;
- plugin discovery before a stable extension contract;
- compatibility shims for unreleased experimental layouts;
- vendor-name branches in portable TCK;
- generic untyped public state bags;
- backend command success as conformance proof;
- browser binary download during unrelated base-package install/import.

The future implementation remains downstream of Spec/Schema/TCK and may use provider-native objects only behind implementation-private seams.

## 22. BR-BR-001..010 disposition

All original Draft design blockers are explicitly resolved in the reconciled AEP:

| Blocker | Result |
|---|---|
| BR-BR-001 authoritative state surface | CLOSED |
| BR-BR-002 origin/storage-partition identity | CLOSED |
| BR-BR-003 topology/session-scoped state | CLOSED |
| BR-BR-004 snapshot/restore fidelity | CLOSED |
| BR-BR-005 browser execution identity | CLOSED |
| BR-BR-006 Service Worker/cache semantics | CLOSED |
| BR-BR-007 credential-bearing state | CLOSED |
| BR-BR-008 canonical projection/Evidence boundary | CLOSED |
| BR-BR-009 settling/observation consistency | CLOSED |
| BR-BR-010 capability/TCK matrix | CLOSED |

Closure means each semantic choice is explicit enough for formal review; it does not mean the choice has already been `Accepted`.

## 23. Non-blocking details intentionally left downstream

The following are appropriate for later normative Spec/Schema/TCK work because the AEP already bounds the portable semantics:

- final capability/profile identifier spelling;
- exact JSON property names, regexes, size limits, and media types;
- exact canonical JSON representation and array ordering after the semantic ordering rules are fixed;
- exact closed Manifest selection grammar syntax, provided it implements the immutable complete-selection semantics in the AEP rather than introducing a vendor query language;
- exact timestamp wire representation for persistent cookie expiry, provided it represents the same expiry instant without backend-local ambiguity;
- exact requirement IDs and TCK case IDs/file organization;
- exact language-specific SPI names;
- Playwright/WebDriver/browser-launch mechanics;
- backend diagnostic mapping that does not alter portable outcomes.

If formal review discovers that any downstream detail changes portable semantics rather than encoding them, AEP-0011 must be amended before acceptance.

## 24. Open protocol-review questions

No unresolved design blocker remains, but formal protocol review should challenge these choices:

1. Is `browser.session-state` / `avp-browser-state-v0.1` the clearest capability vocabulary, or should naming align differently with Fabric resource identity?
2. Is the `(name, domain, hostOnly, path)` cookie identity and stored-attribute boundary exactly the right portable subset for unpartitioned cookies?
3. Is restricting base `localStorage` to non-opaque tuple origins sufficiently portable and appropriately conservative?
4. Should the first normative selection grammar support only explicit origin/cookie scope enumeration, or a small closed declarative scope vocabulary?
5. Is `STATE_EQUIVALENT` as the only successful v0.1 restore claim appropriately conservative?
6. Does the profile-relevant settlement rule provide enough behavioral testability without accidentally standardizing browser event-loop or network-idle semantics?
7. Does the two-engine-family reference acceptance gate sufficiently protect against backend-shaped semantics without becoming a multi-engine requirement on third parties?
8. Is the base exclusion of IndexedDB, partitioned cookies, Service Worker/Cache, and session state the right v0.1 interoperability tradeoff?

These are review questions, not missing definitions.

## 25. Readiness conclusion

The original portability blockers are closed and the AEP text has been reconciled with the adopted portability decisions. It now contains:

- a complete problem and scope;
- a closed portable state surface;
- standards-aligned origin and cookie identity semantics;
- explicit state/Evidence/execution-identity separation;
- conservative reset/snapshot/restore semantics;
- lifecycle/settlement composition;
- Security and Subject/Evaluator/Control boundaries;
- backward-compatibility and release boundaries;
- execution-sensitive conformance and negative-control strategy;
- reference multi-engine portability evidence requirements;
- explicit alternatives and no-transitional-implementation constraints.

Therefore:

**AEP-0011 IS READY TO MOVE FROM `Draft` TO `Proposed` FOR FORMAL PROTOCOL REVIEW.**

The AEP nevertheless remains `Draft` in this work unit. A future `Draft -> Proposed` transition requires a separate explicit recorded protocol-maintainer decision.

This audit does not authorize:

- AEP lifecycle transition;
- Browser normative Spec/Schema/TCK registration;
- browser harness or Playwright implementation;
- repository merge;
- release selection/publication;
- package-index publication;
- signing or attestation.

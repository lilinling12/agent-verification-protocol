# Alpha 3 — AEP-0011 Accepted Decision

Status: **ACCEPTED — BROWSER RESOURCE DIRECTION AUTHORIZED**  
AEP: `rfcs/AEP-0011-browser-resource-profile.md`  
Decision scope: AEP lifecycle transition from `Proposed` to `Accepted` only.  
Authority: explicit protocol-maintainer governance decision on 2026-08-31. This record does not authorize merge, make AEP-0011 `Final`, or permit backend-first Browser implementation.

## Decision

The protocol maintainer explicitly authorized **AEP-0011 Proposed → Accepted** on 2026-08-31.

AEP-0011 is therefore Accepted at the reviewed Browser Resource direction.

Under `GOVERNANCE.md`, `Accepted` means the protocol direction is approved and downstream normative closure may proceed through the governed authority chain. For Browser Resource v0.1, that chain remains:

```text
Accepted AEP-0011 direction
  -> Browser normative specification
  -> Browser requirement index
  -> closed machine-readable schemas where serialized protocol resources require them
  -> execution-sensitive avp-browser-unpartitioned-cookie-localstorage-v0.1 TCK
  -> backend-neutral Browser conformance harness / privileged fixture-control seam where required
  -> reference runtime derived from those authorities
  -> cross-engine implementation evidence
```

Acceptance does not make AEP-0011 `Final`. Final remains a later lifecycle boundary requiring merged normative authority, required conformance coverage, implementation-alignment evidence, and separate release governance.

## Accepted review baseline

The Browser acceptance-oriented work was review-closed before this lifecycle decision.

The BPR-010 protocol/evidence head was:

`38f7110e5da0c4a8abf04578b25b90e30aa83ed4`

At that exact head, focused provider-neutral BAE-013 evidence established deterministic canonical Browser Manifest/Image identity independent of provider enumeration order:

- Manifest: 36 input-order combinations -> one canonical digest; intentionally broken provider-order handling -> 36 distinct digests;
- BrowserStateImage: 96 cookie/origin/localStorage enumeration combinations -> one canonical digest; intentionally broken provider-order handling -> 96 distinct digests;
- duplicate Manifest selections, origin identities, and cookie identities fail closed;
- the evidence is browser-free/provider-neutral and does not learn canonical ordering from Playwright, WebDriver, CDP, BiDi, or a browser engine.

The acceptance-oriented closure review found **no remaining semantic blocker** and confirmed that BPR-010 did not reopen BPR-001..BPR-009.

The final pre-decision exact head was:

`cb1ab87bb6904b2468bae6e6df659cd7db9b0b60`

The semantic/evidence-head-to-final-head delta was limited to review/governance metadata (`ROADMAP.md`, the BPR-010 closure review, and the blocker ledger). No AEP semantic rule, evidence runner, workflow, schema, TCK, harness, or runtime semantics changed after `38f7110e...`.

Final exact-head validation on `cb1ab87...` succeeded for all 14 applicable workflow families:

- CI #693 — success;
- Governance #765 — success;
- Release Validation #101 — success;
- Relational Parity #86 — success;
- Browser Canonical Ordering Evidence #4 — success;
- Browser Acceptance Evidence #43 — success;
- Browser Selection Evidence #30 — success;
- Browser Cookie Partition Evidence #40 — success;
- Browser Settlement Evidence #36 — success;
- Browser Recovery Residual Evidence #18 — success;
- Browser Shipping Partition Evidence #11 — success;
- Browser Shipping Residual Evidence #10 — success;
- Browser Shipping Cookie Fidelity Evidence #9 — success;
- Browser Shipping Cookie Provenance Evidence #8 — success.

A duplicate Governance event (#766) also passed on the unchanged exact head. CI is integrity evidence; the lifecycle transition is authorized by the explicit protocol-maintainer decision, not inferred from green automation.

## Accepted direction

The Accepted AEP-0011 direction includes the reviewed conclusions below.

1. The portable Resource Capability is one cohesive Browser state claim: `state.browser` / `avp-browser-unpartitioned-cookie-localstorage-v0.1` / revision `0.1`.
2. The portable resource is one independently owned isolated browser-session resource, not a page, whole browser process, profile directory, Playwright `BrowserContext`, WebDriver/BiDi handle, CDP target, or other provider-native object.
3. The authoritative v0.1 state surface is closed to selected **unpartitioned HTTP cookies** plus selected **unpartitioned `localStorage`** for admitted exact tuple origins.
4. Partitioned cookies/storage, `sessionStorage`, IndexedDB, Cache Storage, Service Workers, page topology/history, DOM/JS heap, credentials, downloads, traces, and other richer browser state remain outside the base v0.1 state identity unless separately governed.
5. Cookie portable identity is `(name, domain, hostOnly, path)` and projection fails closed when required selected identity/state cannot be established without ambiguity.
6. `SameSite=Default` remains distinct from explicit `Lax`; creation-time-dependent behavior cannot be erased when it is material to the verification claim.
7. Successful base restore fidelity is limited to `STATE_EQUIVALENT`; `EXACT` is not a valid success claim for Browser v0.1.
8. Selected `localStorage` is admitted only where the implementation can prove unpartitioned tuple-origin identity for the controlled execution context.
9. Web Storage `DOMString` values use protocol-owned exact UTF-16-code-unit/base64url representation and unsigned UTF-16 key ordering; host-language Unicode repair or provider serialization is not authority.
10. Browser Manifest/Image collections are canonically ordered before RFC 8785 JCS/content-addressed identity. Provider enumeration/insertion/transport order is non-authoritative.
11. Selection grammar is finite, duplicate-free, exact-origin/exact-stored-domain and complete-set based; regex/glob/provider-native query semantics are not part of the portable profile.
12. Projection/restore success requires positive evaluator/control settlement evidence; sleeps, network-idle heuristics, and backend export success do not prove authoritative state settlement.
13. Materially relevant excluded state requires noninterference, immutable policy/identity binding, or fail-closed insufficiency rather than silent omission.
14. Subject, Evaluator, and privileged Control authority remain separated. Browser-control credentials/handles do not enter Subject-visible context merely because they are needed by the implementation.
15. Artifact/content identity is not retrieval authorization or declassification.
16. Chromium, Gecko, and WebKit evidence supports the reviewed implementation-feasibility and portability claims, but portable TCK semantics must remain provider-neutral and must not branch on engine/backend names.
17. Third-party conformance requires conformance to the profile, not implementation through a particular browser automation library or support for multiple browser engines unless a separately governed claim requires that evidence.
18. Playwright, Selenium/WebDriver, CDP, BiDi, native profile formats, browser enumeration order, and provider-native handles remain implementation mechanisms rather than protocol authority.
19. Browser implementation must derive from `AEP -> Spec -> Schema -> language-neutral TCK -> conformance harness -> reference runtime`, never in the reverse direction.
20. Release/version selection remains separately governed and is not implied by AEP-0011 acceptance.

## Acceptance effect

Acceptance authorizes the next governed **Browser normative-closure** work unit:

1. draft the Browser v0.1 normative specification from the Accepted AEP semantics;
2. create a Browser requirement index tracing each normative requirement to the Accepted direction;
3. define closed machine-readable Browser Manifest/Image/projection contracts only where the specification requires serialized protocol resources;
4. create execution-sensitive, provider-neutral TCK cases from those normative requirements;
5. include negative cases for lossy cookie identity/provenance, partition ambiguity, temporal restore ineligibility, unsettled authoritative mutation, excluded-state interference, foreign/stale ownership, noncanonical identity bytes, and fail-closed incompatibility where required by the specification;
6. run a Browser normative-closure audit before treating any reference runtime as conformance authority;
7. derive backend-neutral interfaces/harness seams from Spec/Schema/TCK rather than Playwright, Selenium, WebDriver, CDP, BiDi, Chromium, Gecko, or WebKit precedent;
8. only after the portable authority slice is reviewable, implement a reference runtime against the same portable TCK;
9. preserve the existing cross-engine evidence as acceptance/implementation evidence rather than importing provider behavior into portable semantics.

## No-transitional-implementation decision

The Accepted decision preserves the project’s long-term architecture constraints:

- no Playwright-first public protocol API generalized later;
- no Chromium/Gecko/WebKit-specific portable semantic forks;
- no generic `BaseBrowserBackend`, `Base*Adapter`, plugin framework, or broad inheritance layer created before concrete responsibility evidence requires it;
- no generic `supports_*` capability bag as a substitute for the cohesive Browser profile;
- no untyped provider property/value bags for known protocol structure;
- no provider-native handle/profile/export bytes used as portable Browser identity;
- no provider enumeration order used as canonical state meaning;
- no backend-name branches in portable TCK cases;
- no metadata-only/self-certified Browser conformance;
- no Subject access to evaluator/control automation authority;
- no temporary unreleased compatibility shim that would harden transitional architecture into protocol surface.

The project continues to follow **“拆职责，不抽象协议 / split responsibilities; do not abstract protocol semantics.”** Composition remains preferred over speculative inheritance.

## Non-authorizations

This Accepted decision does **not** authorize:

- merging PR #110 or its parent PRs #109/#108;
- merging this lifecycle-decision work unit without a separate explicit merge authorization;
- changing AEP-0011 to `Final`;
- changing AEP-0009 to `Final`;
- treating future Browser specification/schema/TCK candidates as Final merely because AEP-0011 is Accepted;
- Browser reference/runtime implementation before the corresponding `Spec -> Schema -> TCK` authority slice is reviewable;
- making Playwright/Selenium/WebDriver/CDP/BiDi behavior protocol authority;
- release/version selection;
- tag or GitHub Release creation;
- package-index publication;
- signing or attestation publication;
- repository split or plugin-framework work;
- weakening Schema/Validator/TCK or evidence gates to obtain green CI.

## Next governed gate

The next gate is **Browser normative closure**.

The normative specification must derive its requirement families from the Accepted AEP-0011 semantics. Schema fields and TCK vectors must be derived from that specification and must not define missing Browser semantics themselves.

Candidate requirement identifiers are intentionally not declared authoritative by this acceptance record. They become governed only when the reviewed Browser requirement index is created through the active normative-candidate process.

## Final decision

**AEP-0011: ACCEPTED.**

**Browser Resource v0.1 direction: APPROVED.**

**Browser normative specification / requirement-index / schema / TCK work: AUTHORIZED through the governed authority chain.**

**Backend-first Browser/reference-runtime implementation: NOT AUTHORIZED.**

**PR #108/#109/#110 merge: NOT AUTHORIZED by this decision.**

**Alpha 3 release/version/publication: NOT AUTHORIZED.**

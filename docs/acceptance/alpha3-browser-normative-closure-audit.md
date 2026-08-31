# Alpha 3 — Browser Normative Closure Audit

Status: **CLOSURE-READY — PORTABLE AUTHORITY SLICE REVIEWED**  
AEP: `rfcs/AEP-0011-browser-resource-profile.md`  
Profile: `avp-browser-unpartitioned-cookie-localstorage-v0.1`  
Semantic audit head: `b865899519530ba805e5b94c1215936690882f75`  
PR: #114  
Scope: Accepted AEP-0011 -> Browser Spec -> requirement index -> Schema -> provider-neutral TCK  

## Decision

The Browser v0.1 portable normative authority slice is **closure-ready** at semantic head `b865899519530ba805e5b94c1215936690882f75`.

The audit found no remaining semantic blocker between Accepted AEP-0011 and the candidate Browser specification, serialized contracts, requirement index, closed schemas, and portable TCK vectors after the two final authority-chain corrections recorded below.

This decision is intentionally narrower than implementation or lifecycle completion. It does **not** authorize Browser harness/reference-runtime implementation, does not make AEP-0011 `Final`, does not authorize merge, and does not imply release/version/publication approval.

## Authority chain audited

The reviewed authority order remains:

```text
Accepted AEP-0011
  -> Browser normative specification
  -> Browser requirement index
  -> closed Browser Manifest/Image schemas
  -> provider-neutral execution-sensitive Browser TCK
  -> backend-neutral conformance harness / privileged fixture-control seam
  -> reference runtime
  -> implementation evidence
```

This audit closes only through the portable TCK authority slice. The backend-neutral harness and reference runtime remain downstream work and are not part of this PR's conformance authority.

## Reviewed normative surface

The audit reviewed the following Browser candidate authority:

- `rfcs/AEP-0011-browser-resource-profile.md`
- `docs/acceptance/alpha3-aep-0011-accepted-decision.md`
- `spec/browser/browser-state-contract.md`
- `spec/browser/browser-serialization-contract.md`
- `spec/browser/requirement-index.yaml`
- `schemas/browser-state-manifest.schema.json`
- `schemas/browser-state-image.schema.json`
- `conformance/tck/profiles/avp-browser-unpartitioned-cookie-localstorage-v0.1.yaml`
- all Browser TCK cases under `conformance/tck/cases/browser/`
- Browser candidate registration and central TCK registration
- Scenario v0.1 external-reference identity semantics reused by Browser `executionBindings`

## Closure criteria

### 1. Accepted-AEP derivation

**PASS.**

`AVP-BROWSER-001..020` derive the portable Browser semantics accepted by AEP-0011: cohesive Browser state capability identity, isolated resource ownership, closed selected unpartitioned cookie/localStorage state, lossless projection, temporal eligibility, exact DOMString representation, canonical ordering, complete StateImage semantics, immutable execution identity, excluded-state disposition, positive settlement, snapshot/reset/restore verification, authority separation, and executed provider-neutral conformance.

`AVP-BROWSER-021..023` close serialization/resource-classification facts already required by the Accepted direction rather than introducing a new behavior model:

- Fabric `resourceKind: browser` and sibling selected-state isolation;
- one closed BrowserStateManifest serialized shape;
- one closed BrowserStateImage serialized shape.

The serialization requirements are therefore downstream closure of Accepted semantics, not a provider-derived replacement for them.

### 2. No omitted Accepted semantic family

**PASS.**

The requirement index covers the Accepted direction's material semantic families:

1. Browser capability and logical identity;
2. independently isolated Browser resource boundary;
3. selected unpartitioned cookie/localStorage state only;
4. closed exact selection grammar;
5. cookie portable identity and lossless projection;
6. SameSite Default / creation-time temporal eligibility;
7. exact DOMString UTF-16 code-unit representation;
8. canonical provider-independent ordering and identity bytes;
9. complete selected StateImage semantics;
10. immutable material execution identity;
11. excluded-state noninterference or fail-closed insufficiency;
12. positive evaluator/control settlement witness;
13. Environment-owned SnapshotRef and independent reset/restore reprojection;
14. successful fidelity exactly `STATE_EQUIVALENT` and never `EXACT`;
15. Subject/Evaluator/Control and Evidence visibility separation;
16. executed provider-neutral conformance;
17. cross-engine evidence retained as implementation/acceptance evidence rather than portable protocol semantics.

No Accepted semantic family was intentionally left to Schema, provider behavior, or future runtime code to define later.

### 3. Schema follows Spec rather than defining Browser semantics

**PASS.**

The Browser schemas are closed structural contracts and do not replace semantic validation.

The audit specifically confirmed that schema acceptance alone is not used to establish:

- canonical WHATWG origin/domain semantics;
- complete-set membership;
- cookie provenance or partition identity;
- temporal restore eligibility;
- settlement;
- execution-input identity;
- excluded-state noninterference;
- SnapshotRef ownership;
- independent reset/restore reprojection;
- Subject/Evaluator/Control visibility;
- executed Browser behavior.

Those remain normative semantic/TCK obligations.

### 4. DOMString wire representation is closed and lossless

**PASS after final correction.**

AEP-0011 requires exact UTF-16 code units encoded as network-byte-order bytes and then canonical unpadded base64url.

The pre-audit BrowserStateImage schema checked only the URL-safe alphabet. That was too weak because it admitted strings whose decoded length could not contain a whole number of 16-bit code units or whose terminal base64url pad bits were noncanonical.

The semantic audit therefore tightened `domStringBytes` structurally so canonical values must:

- use the unpadded URL-safe alphabet;
- decode to a whole number of 2-byte UTF-16 code units;
- use canonical zero terminal pad bits.

Portable TCK negative controls now include:

- odd decoded byte length;
- noncanonical base64url pad bits;
- padded base64url input.

This correction closes AVP-BROWSER-005 more faithfully; it does not add a new semantic beyond AEP-0011.

### 5. TCK does not originate wire identity

**PASS after final correction.**

The pre-audit identity TCK contained two undeclared `application/vnd.avp.browser-state-*+json` media-type literals. Those strings were not defined by AEP-0011 or the candidate Browser Spec and therefore would have allowed TCK data to originate protocol wire identity.

The TCK was corrected to test the governed `BrowserStateManifest` and `BrowserStateImage` resource kinds already defined by the Spec/Schema authority.

No new media type was added merely to preserve the old vector. A future media-type contract, if needed, requires separate governed specification authority.

### 6. Execution identity reuses Scenario/Fabric semantics

**PASS.**

`executionBindings` does not create a second Browser-specific identity system.

Each Browser binding must agree with identity-bound semantic content already owned by the materialized Scenario/Fabric execution contract and reuses the existing identity vocabulary:

- `content`;
- `version`;
- `symbolic`.

Missing, unresolved, conflicting, or provenance-only bindings fail before provisioning/Subject execution. Provider names, native handles, mutable paths, process identifiers, automation objects, and untyped provider property bags cannot become portable execution identity merely because a backend exposes them.

### 7. Provider neutrality and no backend-first authority

**PASS.**

The portable requirements and TCK do not branch on:

- Playwright;
- Selenium;
- Chromium;
- Firefox/Gecko;
- WebKit;
- CDP;
- WebDriver;
- BiDi.

Provider-specific privileged fixture/control implementation may exist downstream behind a backend-neutral seam, but no provider-native handle, export format, enumeration order, profile directory, or implementation object becomes Browser protocol authority.

The project architecture rule remains **拆职责，不抽象协议 / split responsibilities; do not abstract protocol semantics**. No generic `BaseBrowserBackend`, `Base*Adapter`, plugin framework, broad inheritance hierarchy, or generic `supports_*` bag is introduced by this closure.

### 8. Canonicalization and identity

**PASS.**

Browser Manifest/Image identity remains provider-independent:

1. exact logical values are represented according to the Browser profile;
2. Browser-defined arrays are ordered using the governed Browser comparators;
3. RFC 8785 JCS serializes the resulting JSON;
4. SHA-256 identity is computed over the exact retained canonical bytes.

Provider/browser enumeration, insertion, object iteration, transport-return, and automation export ordering remain non-authoritative.

Duplicate selection values and duplicate BrowserStateImage logical identities fail closed.

### 9. Cookie semantics and temporal honesty

**PASS.**

Cookie identity remains `(name, domain, hostOnly, path)`.

The authority slice keeps `SameSite=Default` distinct from explicit `Lax`, rejects lossy identity/projection, separates session and persistent expiry semantics, and refuses `STATE_EQUIVALENT` when material creation-time-dependent behavior remains unresolved.

Field-equal reprojection is necessary but is not used as proof of unbounded HTTP behavioral equivalence.

### 10. Settlement and lifecycle honesty

**PASS.**

Browser v0.1 defines no universal browser-idle state.

Snapshot/reset/restore acceptance requires a positive evaluator/control settlement witness after Subject side-effect admission has closed and accepted relevant mutations have terminal outcomes. Sleep, quiet windows, `networkidle`, provider command completion, event-queue emptiness, or export completion cannot independently certify settlement.

Reset and restore require independent evaluator reprojection rather than trusting provider command success.

### 11. Restore fidelity is not overstated

**PASS.**

A successful Browser v0.1 restore may report exactly `STATE_EQUIVALENT`.

`EXACT` remains forbidden because v0.1 deliberately excludes broader browser/profile/process/topology/worker/cache/temporal/provider-internal state from its standardized state identity.

No schema, TCK vector, CI planner, or reference-runtime claim inflates this fidelity boundary.

### 12. Security and Evidence separation

**PASS.**

Evaluator-private Browser state may remain authoritative while remaining hidden from the Subject. Privileged browser launch/debugging/seeding/snapshot/reset/restore/credential-injection/control handles stay Evaluator/Control authority unless separately governed for Subject use.

Artifact digest identity is never treated as retrieval authorization or declassification. Redacted bytes are distinct Artifacts and cannot reuse the digest of unredacted private bytes.

### 13. Candidate/runtime claim boundary

**PASS.**

The repository's installed-wheel CI now distinguishes stable normative profiles from active candidates without changing conformance semantics:

- stable profiles must be fully supported by the installed reference adapter;
- a candidate with complete support is executed;
- a candidate with zero support is explicitly implementation-pending with **no conformance claim**;
- partial candidate implementation fails closed.

Browser is therefore allowed to exist as a complete portable authority candidate before its reference implementation without being silently treated as PASS/SKIP or forcing backend-first implementation.

This planner is CI claim-boundary plumbing; it does not change Browser Spec/Schema/TCK expectations.

## Portable TCK coverage review

The Browser profile currently has eight mandatory provider-neutral TCK cases:

1. `AVP-TCK-BROWSER-IDENTITY-001`
   - capability/resource identity;
   - acyclic Manifest/Image identity;
   - Browser resource classification;
   - sibling selected-state isolation;
   - executionBindings reuse upstream identity.
2. `AVP-TCK-BROWSER-SELECTION-CANONICAL-001`
   - exact selection grammar;
   - exact DOMString encoding;
   - canonical collection ordering;
   - permutation-invariant canonical identity;
   - duplicate/noncanonical negative controls.
3. `AVP-TCK-BROWSER-COOKIE-001`
   - cookie portable identity;
   - lossless projection;
   - SameSite Default distinction;
   - persistent/session semantics;
   - temporal restore eligibility.
4. `AVP-TCK-BROWSER-STATE-IMAGE-001`
   - exact Manifest binding;
   - complete selected state;
   - closed Image serialization;
   - expiry representation;
   - missing/extra/duplicate/transformed negatives.
5. `AVP-TCK-BROWSER-EXECUTION-RESIDUAL-001`
   - material execution identity;
   - excluded-state disposition;
   - drift/noninterference fail-closed behavior.
6. `AVP-TCK-BROWSER-SETTLEMENT-LIFECYCLE-001`
   - positive settlement witness;
   - SnapshotRef ownership;
   - reset/restore independent reprojection;
   - temporal restore eligibility;
   - `STATE_EQUIVALENT` only.
7. `AVP-TCK-BROWSER-SECURITY-001`
   - Subject/Evaluator/Control separation;
   - evaluator-private state confidentiality;
   - Artifact identity versus authorization.
8. `AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001`
   - executed behavior rather than metadata self-certification;
   - metadata-identical broken controls;
   - provider-neutral expectations.

This is sufficient for portable normative closure. It is not evidence that a Browser reference adapter already implements the cases.

## Exact-head validation evidence

The final semantic authority head before this audit record was added is:

`b865899519530ba805e5b94c1215936690882f75`

Applicable exact-head workflows all succeeded:

- CI #729 — **success**;
- Governance #806 — **success**;
- Relational Parity #122 — **success**.

These checks include the repository's normative-surface, schema/asset, requirement traceability, central TCK registry, packaging, stable installed-wheel conformance, relational compatibility, and governance gates applicable to this PR.

Automation is integrity evidence. The closure decision comes from the authority-chain audit above, not from green CI alone.

## Remaining downstream work

This closure permits the project to propose the next separately governed work unit, but does not start it automatically.

The next implementation-facing authority boundary is:

```text
reviewed Browser Spec / Schema / portable TCK
  -> backend-neutral Browser conformance harness and privileged fixture-control seam
  -> reference runtime implementation against the same portable TCK
  -> cross-engine implementation-alignment evidence
```

Any future harness/runtime work must derive its interfaces from these reviewed responsibilities. It must not reverse-engineer public protocol semantics from Playwright, Selenium/WebDriver, CDP, BiDi, or a specific browser engine.

## Non-authorizations

This closure audit does **not** authorize:

- merge of PR #114 or its stacked parent PRs;
- changing AEP-0011 to `Final`;
- changing AEP-0009 to `Final`;
- release/version selection;
- tag or GitHub Release creation;
- package-index publication;
- signing or attestation publication;
- treating Browser candidate TCK as already implemented by the reference runtime;
- backend/provider behavior as protocol authority;
- weakening Schema/Validator/TCK/evidence gates;
- repository split;
- plugin-framework or speculative base-adapter work.

## Final audit result

**Accepted AEP-0011 -> Browser normative Spec: ALIGNED.**

**Browser Spec -> requirement index: ALIGNED.**

**Browser Spec -> closed Schema: ALIGNED.**

**Browser requirements -> provider-neutral TCK: ALIGNED.**

**Provider/runtime semantics defining the protocol: REJECTED.**

**Portable Browser normative authority slice: CLOSURE-READY.**

**Backend-neutral harness/reference-runtime implementation: NOT AUTHORIZED BY THIS AUDIT.**

**AEP-0011 Final / merge / release / publication: NOT AUTHORIZED BY THIS AUDIT.**

# Alpha 3 Browser Backend Implementation Readiness Audit

Status: **IMPLEMENTATION GATED — BACKEND-NEUTRAL BROWSER CONFORMANCE HARNESS REQUIRED FIRST**

Audited Browser normative baseline: `13974bf52864d95f4b670ed31068d05674ebd8ba`  
Owning normative-closure PR: `#114`  
AEP lifecycle: **AEP-0011 Accepted, not Final**

Governing authority:

- AEP-0009 — Environment Fabric Composition and Capability Contract (`Accepted`)
- AEP-0011 — Browser Resource Profile v0.1 (`Accepted`)
- `spec/browser/browser-state-contract.md`
- `spec/browser/browser-serialization-contract.md`
- `spec/browser/requirement-index.yaml`
- `schemas/browser-state-manifest.schema.json`
- `schemas/browser-state-image.schema.json`
- `conformance/tck/profiles/avp-browser-unpartitioned-cookie-localstorage-v0.1.yaml`
- the eight mandatory Browser TCK cases registered for that profile
- `docs/acceptance/alpha3-browser-normative-closure-audit.md`

This audit determines the implementation architecture that must exist before a Playwright-, WebDriver-, CDP-, BiDi-, or browser-product-specific reference implementation can claim Browser v0.1 conformance.

It is an **implementation-architecture gate**, not a new protocol-semantics layer. It does not add AVP Browser requirements and cannot override the Accepted AEP, normative Spec, Schema, or portable TCK.

## 1. Decision

The Browser portable authority slice is sufficiently closed to begin backend-neutral conformance-harness work.

The repository is **not ready to implement a Playwright Browser runtime as the next standalone change**.

The next governed implementation slice is:

> a Browser-specific backend-neutral conformance harness, an immutable materialized local-browser fixture, and a privileged evaluator/fixture-control boundary derived directly from the eight portable Browser TCK cases.

Only after that slice is review-closed may the first provider-specific Browser runtime be implemented against it.

The implementation must preserve the authority direction:

```text
Accepted AEP-0011
  -> Browser Spec
  -> requirement index
  -> closed Manifest/Image schemas
  -> provider-neutral Browser TCK
  -> backend-neutral Browser conformance harness
  -> provider-specific reference implementation
  -> implementation/cross-engine evidence
```

The reverse direction is forbidden. A provider API, export format, browser handle, profile directory, automation context, or test convenience must not define missing portable semantics.

## 2. Why a Browser-specific readiness gate is required

The existing outer `TCKRunner -> TCKCaseAdapter` seam is valid and should remain the top-level conformance boundary. It is not sufficient by itself for Browser execution-sensitive conformance.

Browser v0.1 must prove behavior that cannot honestly be established by schema validation, metadata, or a provider success flag alone:

- independently isolated sibling Browser resources;
- exact selected unpartitioned cookie and localStorage projection;
- cookie identity/provenance and `SameSite=Default` preservation;
- cookie temporal restore eligibility;
- exact UTF-16-code-unit localStorage representation;
- deterministic canonical StateImage identity independent of provider enumeration;
- positive settlement evidence rather than sleep/network-idle heuristics;
- materially relevant excluded-state disposition;
- immutable execution-input identity and drift rejection;
- Environment/resource SnapshotRef ownership;
- independent reset/restore reprojection;
- exactly `STATE_EQUIVALENT` successful restore fidelity;
- evaluator-private state and privileged Control isolation;
- rejection of metadata-identical broken implementations at the real browser boundary.

A provider-specific evaluator that directly implements those TCK cases would make it too easy for Playwright/WebDriver/browser mechanics to become the de facto protocol.

## 3. Browser TCK -> implementation responsibility matrix

The harness work is derived from the existing portable cases, not from an automation library API.

| Portable TCK case | Required implementation responsibility | Must remain outside portable protocol |
| --- | --- | --- |
| `AVP-TCK-BROWSER-IDENTITY-001` | provision one independently owned Browser resource, preserve governed Resource/Manifest/Image identity, validate upstream execution bindings, prove sibling selected-state isolation | browser context/page/process/session handles; provider profile ids |
| `AVP-TCK-BROWSER-SELECTION-CANONICAL-001` | independently canonicalize exact selections and DOMString code units, reject duplicate/noncanonical identity input, compute canonical bytes/digests independent of enumeration order | provider storage export order; host-language Unicode repair |
| `AVP-TCK-BROWSER-COOKIE-001` | observe/prove complete portable cookie identity and required state, retain provenance needed when transport is lossy, evaluate temporal restore eligibility | provider cookie JSON as authority; inferred `hostOnly`; provider default SameSite normalization |
| `AVP-TCK-BROWSER-STATE-IMAGE-001` | independently build/validate the complete selected StateImage under the exact Manifest and detect missing/extra/transformed/scope-shifted state | provider-created StateImage/digest trusted without verification |
| `AVP-TCK-BROWSER-EXECUTION-RESIDUAL-001` | bind material execution identity, detect drift, and establish noninterference / immutable binding / fail-closed insufficiency for material excluded state | product labels, mutable process/profile paths, provider property bags |
| `AVP-TCK-BROWSER-SETTLEMENT-LIFECYCLE-001` | close Subject admission, track accepted relevant mutations to terminal outcome, gate projection on positive settlement, verify SnapshotRef ownership, and independently reproject reset/restore targets | `sleep`, `networkidle`, event-loop emptiness, import/restore command success as correctness proof |
| `AVP-TCK-BROWSER-SECURITY-001` | keep evaluator-private selected state authoritative while denying Subject disclosure; keep launch/debug/snapshot controls privileged | automation/debug handles, evaluator credentials, hidden state in Subject-visible data |
| `AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001` | execute all behavior-dependent checks against the actual Browser implementation and reject metadata-identical broken behavior | provider-name branches or metadata-only self-certification |

This matrix defines responsibilities only. Exact Python class and method names remain implementation details and must be reviewed for the narrowest useful seam.

## 4. Required architecture before a provider-specific runtime

The next implementation PR must establish four separated responsibilities.

### 4.1 Portable TCK case plane

The eight Browser TCK YAML cases remain provider-neutral and keep their current portable semantics.

They may express only governed concepts such as:

- Browser Resource/capability/profile identity;
- Manifest/Image logical fields and canonical identity;
- exact origin/domain selections;
- logical cookie/localStorage state;
- execution-binding and excluded-state intent;
- settlement/lifecycle intent;
- expected portable outcomes and negative controls.

They must not contain:

- Playwright/Selenium/WebDriver/CDP/BiDi branches;
- Chromium/Firefox/WebKit-specific expected semantics;
- provider context/page/session ids;
- browser executable/profile paths;
- provider-native cookie/storage export formats;
- provider launch options as portable fields.

### 4.2 Browser SUT operation seam

Introduce one Browser-specific implementation-private seam for exercising the **existing portable resource behavior**.

It must expose only responsibilities necessary for the governed Browser Resource lifecycle, such as provisioning/releasing a resource and invoking the existing snapshot/reset/restore behavior required by Browser v0.1. It may expose a narrowly scoped Subject-visible projection only where existing Security/Scenario authority requires it.

It must **not** become a universal browser automation API. In particular, the portable/SUT seam must not grow generic methods such as:

- `goto` / `click` / `evaluateJavascript`;
- `execute_cdp` / `webdriver_command`;
- `get_context` / `get_page` / `get_session`;
- generic cookie/storage mutation calls used as Subject capabilities;
- arbitrary browser launch/configuration maps;
- generic `supports_*` capability bags.

Provider handles needed internally remain private implementation state.

### 4.3 Independent evaluator observation/canonicalization seam

Browser conformance requires an evaluator-owned observation path that does not merely trust SUT/provider-produced success flags or digests.

The harness must be able to derive, from evaluator-authorized observations:

- the complete selected unpartitioned cookie set with portable `(name, domain, hostOnly, path)` identity;
- all required cookie state and independently reviewable provenance where the provider observation is lossy;
- the complete selected unpartitioned localStorage maps for exact admitted tuple origins;
- exact DOMString code-unit bytes;
- canonical collection ordering;
- canonical Manifest/Image JCS bytes and SHA-256 identity;
- the relevant execution-binding identity view;
- settlement eligibility and excluded-state disposition evidence needed for the conformance decision.

The observer may use provider-specific mechanisms internally in a later implementation, but those mechanics cannot enter the portable case vocabulary or become a second Resource API.

The harness must independently recompute canonical identity after reset/restore. A provider-reported digest or restore success flag is evidence at most; it cannot satisfy AVP-BROWSER-017/018 by itself.

### 4.4 Privileged fixture/control seam

Introduce a separate test-only privileged boundary for conditions that the portable Browser SUT/Subject surface must not be allowed to create directly.

The logical fixture-control responsibilities must be sufficient to create or coordinate the existing TCK controls, including:

- seed selected cookie and localStorage state;
- distinguish host-only and domain-scoped cookies without inference from presentation syntax;
- create explicit `SameSite=Default` and explicit `Lax` controls;
- establish persistent/session cookie controls and exact expiry evidence;
- create a lossy-cookie-observation/provenance failure control;
- create a material temporal-eligibility failure control;
- create partitioned state that must not be admitted as unpartitioned state;
- create sibling Browser resources and test selected-state isolation;
- start/hold/settle accepted profile-relevant mutations for positive settlement testing;
- attempt mutation after Subject admission closes;
- create execution-input drift;
- create materially interfering excluded state or the governed fixture condition used to prove its disposition;
- seed evaluator-private selected state and verify it remains hidden from the Subject;
- create metadata-identical broken behavior needed by `AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001`.

Browser launch/debug handles, provider credentials, native sessions, test-server administration, browser-profile mechanics, and equivalent privileges stay behind this boundary.

The fixture-control seam is not an AVP Subject Capability, not a Resource Capability, not a public browser API, and not protocol authority.

## 5. Positive settlement is a first-class harness responsibility

Browser v0.1 deliberately defines no universal browser-idle predicate.

The existing acceptance evidence already demonstrates the required shape: an evaluator-owned mutation ledger can observe that network-idle occurs while an accepted localStorage mutation is still unresolved, reject authoritative projection during that interval, close new Subject-side-effect admission, then admit projection only after the accepted mutation reaches an explicit terminal condition.

The conformance harness may use a different implementation, but it must preserve these portable facts:

1. Subject admission closure is explicit;
2. accepted profile-relevant mutations are known;
3. every accepted mutation relevant to selected state has a terminal outcome before authoritative projection;
4. unresolved accepted work prevents an accepted projection;
5. projection begins after the witness;
6. sleep/network-idle/provider command completion does not self-certify settlement.

A method named `wait_until_idle()` would therefore be an incorrect abstraction if its semantics collapse these requirements into provider idleness.

## 6. Cookie provenance and temporal behavior are not provider export fields

Some browser-control transports do not expose enough information to prove the portable cookie identity/state required by Browser v0.1.

The existing shipping evidence demonstrates an acceptable architecture direction: evaluator/control-owned provenance can establish required cookie facts that a lossy current-state transport omits, while missing/stale/ambiguous/inconsistent provenance fails closed.

The harness must therefore distinguish:

- current browser observation;
- evaluator/control provenance used to establish required portable facts;
- canonical BrowserStateImage identity;
- provider-native export data.

Those are not interchangeable.

Provider provenance is not automatically portable state. Provenance may support the conformance decision without becoming a BrowserStateImage field.

Temporal restore eligibility must likewise remain a conformance decision under the materialized Scenario/execution policy. Recreating field-equal cookies is insufficient when a material creation-time-dependent behavior remains unresolved.

## 7. Immutable executable local-browser fixture

A real Browser conformance harness requires browser-addressable HTTP origins. Unlike a pure in-memory fixture, CI may allocate dynamic ports or otherwise resolve local execution endpoints.

Hard-coding an arbitrary localhost port into canonical expected Manifest/Image identity would make fixture identity depend on incidental CI allocation. Hiding the actual resolved origin would be equally incorrect because the exact tuple origin is authoritative selection identity.

The required fixture model is therefore two-stage but fail-closed:

1. **immutable fixture source/template** — provider-neutral logical data, test-server route behavior, cookie/storage vectors, excluded-state controls, Subject/evaluator visibility intent, and execution-binding requirements;
2. **materialized fixture** — all execution-relevant endpoint/origin slots resolved to exact canonical tuple origins and identity-bound before Browser resource provisioning or Subject execution.

After materialization, the fixture is immutable for the conformance run. The exact resolved origins participate in the BrowserStateManifest and canonical identity as required by the profile.

The materializer must not use unresolved placeholders after provisioning begins, and must not rewrite expected canonical identity after observing provider behavior.

Recommended repository ownership for provider-neutral fixture source:

```text
conformance/fixtures/browser-state/v0.1/
```

Provider-specific launch scripts, binaries, profiles, driver configuration, and browser transport setup must not be stored as portable fixture expectations.

## 8. Canonical identity must be independently owned by the harness

The harness must own the Browser canonicalization/assertion path used for conformance decisions.

At minimum it must independently enforce:

- exact canonical tuple-origin and stored-domain selection;
- duplicate rejection;
- DOMString UTF-16 code-unit/network-byte-order/unpadded-base64url representation;
- canonical origin/domain/localStorage/cookie ordering;
- cookie identity `(name, domain, hostOnly, path)`;
- persistent expiry representation;
- closed Manifest/Image shape;
- Manifest-to-StateImage digest binding;
- RFC 8785 JCS bytes and SHA-256 identity.

It must not learn ordering, Unicode repair, cookie scope, SameSite state, or digest bytes from provider enumeration/export order.

A provider may supply raw observations. The conformance verdict must come from the governed canonical model and independently observed behavior.

## 9. Security and authority boundary

The harness/fixture slice must prove that the implementation architecture itself preserves Browser security separation.

At minimum:

- Subject-visible interfaces cannot obtain evaluator/control browser handles;
- Subject-visible data does not expose evaluator-private cookie/localStorage values unless explicitly authorized by the Scenario;
- privileged fixture/test-server credentials and automation handles never enter portable Artifacts/TCK YAML/conformance reports;
- Artifact digest never acts as retrieval authorization;
- redacted Subject bytes are distinct Artifacts from evaluator-private original bytes;
- hidden instrumentation/control authority is not exposed merely because the implementation needs it to verify state.

A single omnipotent `BrowserBackend` object handed to both Subject and evaluator code would violate this architectural boundary even if tests happened to pass.

## 10. Negative-control strategy

`AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001` requires metadata-identical broken implementations to be rejected by behavior.

The harness must therefore support test-only negative controls without teaching portable TCK cases about provider products.

A negative control should alter one observable behavior while keeping the portable claim metadata otherwise equivalent, for example:

- lose `hostOnly` identity;
- collapse `SameSite=Default` to `Lax`;
- admit partitioned state as unpartitioned;
- corrupt DOMString code units;
- preserve provider enumeration order as canonical identity;
- report restore success without independent reprojection;
- bypass settlement;
- leak evaluator-private state;
- ignore excluded-state interference;
- ignore execution-input drift.

Exact control implementations are test infrastructure. A provider implementation must not gain a production-facing `negative_control` API.

## 11. Reference-adapter support activation is atomic

The repository's installed-wheel planner intentionally treats active candidate profiles as follows:

- complete reference support: execute the candidate profile;
- zero reference support: report explicit implementation-pending with **no conformance claim**;
- partial reference support: fail closed.

Therefore the Browser harness implementation must **not** progressively add a subset of the eight Browser case ids to `ReferenceConformanceAdapter.supported_case_ids`.

During harness construction, Browser remains implementation-pending.

Only after all eight mandatory Browser cases execute honestly through the completed Browser conformance path may the reference composite claim the Browser case-id set as one complete supported profile. This is a claim-integrity rule, not a request to fake aggregate support or hide failing cases.

## 12. Dependency and provider boundary

The backend-neutral harness/fixture slice should not add Playwright, Selenium, browser binaries, drivers, CDP libraries, or another provider dependency to the base reference package merely to define the seam.

The first provider-specific implementation may later use an optional implementation/testing dependency under repository dependency policy.

Provider/version selection is implementation evidence and execution identity where materially required. It is not protocol semantics.

Existing cross-engine acceptance runners under `tests/acceptance/browser/` remain non-normative evidence and may inform feasibility. They must not be imported wholesale into `src/avp_ref` or treated as the conformance architecture.

## 13. CI requirements for the backend-neutral harness slice

Before BBIR blockers can be closed, the harness/fixture PR must pass existing repository gates and add focused tests proving at least:

1. the portable Browser TCK files remain byte/semantically provider-neutral with no provider-name branch introduced;
2. the materialized fixture resolves exact origin slots before provisioning and freezes those resolved execution inputs;
3. canonical Manifest/Image bytes are independently deterministic across input enumeration permutations;
4. fixture-control operations are unreachable through the portable Subject/SUT surface;
5. evaluator-private selected state can participate in authoritative projection without Subject disclosure;
6. an unresolved accepted mutation blocks authoritative projection even if an implementation reports network-idle or command completion;
7. independent reprojection is required after reset/restore and a false-success negative control is rejected;
8. cookie provenance loss/ambiguity and temporal ineligibility fail closed;
9. execution-input drift and material excluded-state interference are rejected;
10. sibling selected-state sharing is detectable and rejected;
11. metadata-identical broken controls remain rejectable without provider-name logic;
12. the Browser profile remains implementation-pending until all eight cases are actually supported.

This harness PR must not mark `Playwright browser runtime against the portable TCK` complete in `ROADMAP.md`.

## 14. First provider-specific runtime acceptance gate

A later provider-specific Browser runtime may be considered implementation-complete only when all of the following are true:

- it implements the reviewed Browser-specific backend-neutral seams rather than introducing a provider-first portable API;
- it consumes the same provider-neutral materialized fixture contract;
- all eight mandatory Browser TCK cases execute against the actual provider/browser path;
- mandatory cases do not SKIP merely because provider control is difficult;
- cookie identity/provenance, selected localStorage, settlement, excluded-state handling, execution-input drift, snapshot/reset/restore, security visibility, and negative controls are exercised by real behavior or privileged test-only control seams;
- canonical bytes/digests are independently recomputed by the harness;
- reset/restore success is not accepted from provider command completion alone;
- successful v0.1 restore reports exactly `STATE_EQUIVALENT`;
- no provider-specific field enters the Browser schemas or portable TCK semantics;
- base-package dependency boundaries remain intact unless separately governed;
- clean CI provisions and tears down the provider/browser environment reproducibly;
- cleanup/infrastructure failure remains separate from Agent Task Verdict;
- exact-head review and applicable gates are green.

Only then may the Browser reference composite activate all eight Browser case ids and claim the complete candidate profile as reference-supported.

## 15. Current blockers and disposition

### Protocol blockers

**None found.**

The AEP-0011 -> Spec -> requirement index -> Schema -> portable TCK authority slice was review-closed at `13974bf52864d95f4b670ed31068d05674ebd8ba`. This audit does not reopen that semantic closure.

### Implementation blockers

**BBIR-001 — Missing Browser-specific backend-neutral SUT/observer conformance harness.**

No reusable implementation-private Browser harness currently drives the existing portable lifecycle while independently observing/canonicalizing authoritative selected Browser state. A provider runtime must not be wired by putting Playwright/WebDriver/browser branches directly into portable TCK evaluators.

**BBIR-002 — Missing immutable materialized local-browser conformance fixture.**

Browser execution requires exact browser-addressable origins and HTTP/storage behaviors. The repository needs one provider-neutral fixture source plus fail-closed materialization that resolves and identity-binds exact tuple origins before provisioning, rather than hard-coding incidental CI ports or hiding dynamic origin identity.

**BBIR-003 — Missing privileged Browser fixture/control boundary.**

Held mutations, cookie provenance controls, temporal eligibility, partition controls, excluded-state interference, execution-input drift, sibling isolation, evaluator-private state, and metadata-identical negative behavior require privileged test infrastructure that cannot leak into Subject/portable APIs.

**BBIR-004 — Missing independent settlement/reprojection enforcement through the shared harness.**

The existing portable requirements require positive settlement and independent reset/restore reprojection. Those checks must be owned by the shared conformance path rather than delegated to provider `networkidle`, export, import, or command-success signals.

**BBIR-005 — Browser profile support activation must remain atomic.**

The current reference composite has no Browser owner, which is the correct state while implementation is absent. The planner intentionally rejects partial candidate support. No subset of Browser case ids may be registered as supported during harness construction; complete activation is gated on all eight mandatory cases executing honestly.

### Disposition

```text
Portable Browser protocol: CLOSURE-READY
Provider-specific Browser runtime: BLOCKED
Next governed implementation slice:
  BACKEND-NEUTRAL BROWSER CONFORMANCE HARNESS
  + MATERIALIZED LOCAL-BROWSER FIXTURE
  + PRIVILEGED FIXTURE/OBSERVER CONTROL SEAM
```

Closing BBIR-001..005 authorizes review of the first provider-specific Browser reference implementation slice. It does not itself authorize AEP-0011 Final, merge of the active Browser stack, release/version selection, publication, signing, attestation, repository split, or plugin-framework work.

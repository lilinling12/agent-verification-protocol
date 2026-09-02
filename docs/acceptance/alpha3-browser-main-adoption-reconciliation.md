# Alpha 3 Browser Main-Adoption Reconciliation

Status: **REVIEW CANDIDATE**

## 1. Purpose

This audit reconciles repository governance after the complete reviewed Browser Resource v0.1 candidate stack was squash-merged into `main` by PR #108.

It records the exact adopted identity, the post-merge execution evidence, the Browser roadmap work that is now an adopted repository fact, and the boundaries that remain separately governed. This document is adoption/governance evidence only. It does not create new Browser protocol semantics, change AEP lifecycle state, select a release, or authorize publication.

## 2. Adopted main identity

The governed adoption is:

- PR: #108 — `feat(alpha3): adopt reviewed Browser v0.1 candidate stack`;
- reviewed PR head: `090de157c30fc186dce05a7c6e774c0a6a598a44`;
- previous `main`: `fa62d004a4fb8498219989abcbd0b21caf14177f`;
- squash merge commit / adopted `main`: `781268dd193dd6ad169ffac3a0fd18fab7b602a5`;
- expanded-head review closure: `5085386175`;
- final Ready-state Governance: #946 — **SUCCESS**;
- unresolved review threads immediately before merge: zero.

The merge was guarded with `expected_head_sha=090de157c30fc186dce05a7c6e774c0a6a598a44`, so the adopted tree is exactly the reviewed expanded-head tree.

AEP-0011 remains **Accepted, not Final**.

## 3. Adopted authority and implementation chain

The Browser stack now present on `main` preserves the reviewed authority direction:

```text
Accepted AEP-0011
  -> Browser normative specification
  -> requirement index
  -> closed Browser Manifest/Image schemas
  -> provider/language-neutral execution-sensitive Browser TCK
  -> backend-neutral Browser conformance harness
  -> optional concrete reference implementation
  -> implementation and portability evidence
```

Main adoption does not reverse this direction. Concrete Playwright, Chromium, Selenium/WebDriver, CDP, BiDi, Gecko, WebKit, or Safari behavior remains implementation/evidence only and cannot define portable AVP Browser semantics by precedent.

The adopted profile remains deliberately narrow:

- capability: `state.browser`;
- profile: `avp-browser-unpartitioned-cookie-localstorage-v0.1`;
- authoritative Browser state: selected unpartitioned HTTP cookies plus selected unpartitioned `localStorage` for exact admitted tuple origins;
- successful restore fidelity: exactly `STATE_EQUIVALENT`, never `EXACT`.

## 4. Portable Browser conformance closure

The mandatory Browser profile remains exactly eight cases:

1. `AVP-TCK-BROWSER-IDENTITY-001`
2. `AVP-TCK-BROWSER-SELECTION-CANONICAL-001`
3. `AVP-TCK-BROWSER-COOKIE-001`
4. `AVP-TCK-BROWSER-STATE-IMAGE-001`
5. `AVP-TCK-BROWSER-EXECUTION-RESIDUAL-001`
6. `AVP-TCK-BROWSER-SETTLEMENT-LIFECYCLE-001`
7. `AVP-TCK-BROWSER-SECURITY-001`
8. `AVP-TCK-BROWSER-EXECUTED-CAPABILITY-001`

Browser support remains an atomic claim:

```text
0/8 -> 8/8
```

Partial, duplicate, or unexpected Browser ownership remains fail-closed. Main adoption does not authorize partial Browser support or provider-specific substitutions for a mandatory portable case.

## 5. Exact-main validation

PR #108 merged at exact commit `781268dd193dd6ad169ffac3a0fd18fab7b602a5`. The applicable push-triggered post-merge workflows all completed successfully on that exact SHA.

### CI #817

- workflow run: `33589204270`;
- event: `push`;
- exact head: `781268dd193dd6ad169ffac3a0fd18fab7b602a5`;
- conclusion: **SUCCESS**.

Successful coverage includes:

- Quality / Python 3.11;
- Quality / Python 3.12;
- Quality / Python 3.13;
- reproducible source/wheel distribution verification;
- built-wheel metadata validation;
- clean-consumer base-wheel installation;
- installed-wheel identity verification;
- installed-wheel reference smoke;
- installed-wheel governed TCK conformance;
- release-evidence build and verification;
- PostgreSQL 17.11 and 18.6 real relational adapter regression lanes;
- MySQL 8.4.11 and 9.7.2 real relational adapter regression lanes.

### Relational Parity #210

- workflow run: `33589204275`;
- event: `push`;
- exact head: `781268dd193dd6ad169ffac3a0fd18fab7b602a5`;
- conclusion: **SUCCESS**.

Both canonical-parity lanes passed:

- PostgreSQL 18.6 / MySQL 9.7.2;
- PostgreSQL 17.11 / MySQL 8.4.11.

This confirms the Browser adoption did not regress the already-adopted Relational State implementation/conformance surface.

### Browser Reference #83

- workflow run: `33589204283`;
- event: `push`;
- exact head: `781268dd193dd6ad169ffac3a0fd18fab7b602a5`;
- conclusion: **SUCCESS**.

The real Browser provider lane successfully:

- built a Browser-capable wheel;
- installed the optional Browser implementation dependency;
- installed the controlled Chromium build;
- bound the reserved local fixture hosts;
- verified the Playwright implementation dependency;
- executed the real Playwright Browser provider foundation suite on Python 3.13.

These are implementation/conformance execution facts, not new protocol authority.

## 6. Pre-merge acceptance and shipping evidence

The post-merge Browser Reference run complements rather than replaces the exact-head acceptance/shipping evidence reviewed before adoption.

At PR #108 expanded head `090de157c30fc186dce05a7c6e774c0a6a598a44`, the complete applicable workflow set was green, including:

- CI #816;
- Governance #943, metadata reconciliation Governance #944, and Ready-state Governance #946;
- Release Validation #109;
- Relational Parity #209;
- Browser Reference #82;
- Browser Acceptance Evidence #52;
- Browser Canonical Ordering Evidence #13;
- Browser Selection Evidence #39;
- Browser Cookie Partition Evidence #49;
- Browser Settlement Evidence #45;
- Browser Recovery Residual Evidence #27;
- Browser Shipping Partition Evidence #20;
- Browser Shipping Residual Evidence #19;
- Browser Shipping Cookie Fidelity Evidence #18;
- Browser Shipping Cookie Provenance Evidence #17.

The Safari BAE-011 shipping-residual blocker remained closed as SafariDriver/WebDriver session-service lifecycle behavior. The final fix uses one explicitly owned SafariDriver service generation per WebDriver session and does not rely on retry, sleep-as-correctness, PARTIAL conversion, provider removal, or weakening of Spec/Schema/TCK/Gates.

## 7. Browser authority and security boundaries preserved

Main adoption preserves the reviewed boundaries:

- Subject, Evaluator, and privileged Control remain distinct responsibilities;
- evaluator/private observation and fixture-control authority do not become Subject capabilities;
- provider-native handles and storage exports do not become portable Browser state;
- cookie identity remains `(name, domain, hostOnly, path)`;
- `SameSite=Default` remains distinct from explicit `Lax`;
- exact Web IDL `DOMString` UTF-16 code-unit representation remains protocol-owned;
- provider-independent canonical collection ordering precedes content-addressed identity;
- settlement requires positive evaluator/control evidence rather than sleep, network-idle, provider command completion, or queue emptiness;
- materially relevant excluded state and execution-input drift fail closed when noninterference/equivalence cannot be established;
- partitioned-cookie state is not silently relabeled into the base unpartitioned profile.

The repository engineering rule remains:

> Split responsibilities; do not abstract protocol semantics.

Accordingly, this adoption does not introduce or justify a generic `BaseBrowserBackend`, provider plugin registry, generic `supports_*` capability bag, provider-name branching in portable conformance, or a speculative cross-provider compatibility framework.

## 8. ROADMAP reconciliation

`docs/acceptance/alpha3-browser-reference-conformance-closure.md` deliberately deferred Browser roadmap completion until both governed main adoption and exact-main validation had occurred. Those conditions are now satisfied by PR #108 and exact-main CI #817 / Relational Parity #210 / Browser Reference #83.

The following Browser roadmap items are therefore complete as **main-adopted repository facts**:

- Browser normative specification and requirement index;
- Browser schemas for serialized state/projection resources;
- execution-sensitive Browser resource TCK;
- backend-neutral Browser conformance harness with immutable local-browser fixture and privileged fixture-control seam;
- Playwright Browser runtime against the portable TCK.

Checking those items does not promote the candidate profile to a stable released conformance target and does not make Playwright/Chromium behavior normative.

## 9. Candidate-registry and lifecycle disposition

AEP-0011 remains **Accepted, not Final** after main adoption.

Candidate and draft markers that are intentionally tied to release/Final promotion must not be rewritten merely because implementation and conformance surfaces now live on `main`. Their later promotion requires the separately governed lifecycle/release path defined by `GOVERNANCE.md` and `docs/RELEASE_PROCESS.md`.

In particular, main adoption alone does not satisfy the repository definition of `Final`, which includes released normative/conformance evidence and an explicit maintainer lifecycle decision.

## 10. Release boundary

This reconciliation does **not** authorize or select:

- AEP-0011 `Accepted -> Final`;
- AEP-0009 or AEP-0010 `Accepted -> Final`;
- a release or release-candidate version;
- entering release mode;
- tag or GitHub Release creation;
- package-index publication;
- signing or attestation publication;
- universal multi-engine equivalence;
- repository split or generic provider/plugin-framework work.

Any release action must follow `docs/RELEASE_PROCESS.md` independently from this adoption bookkeeping.

## 11. Reconciliation disposition

The Browser v0.1 authority, TCK, backend-neutral harness, and reviewed Playwright/Chromium reference path are now adopted on `main` at exact commit `781268dd193dd6ad169ffac3a0fd18fab7b602a5`, with all applicable exact-main push validation successful.

This reconciliation is **READY FOR REVIEW** once its own exact-head PR CI/Governance/Release Validation/Relational Parity checks are green and the documentation-only delta is review-closed.

No additional Browser feature or abstraction work is required merely to justify the already-completed main adoption. Subsequent Browser protocol expansion, AEP Final promotion, and release selection remain separate governed transitions.

# Alpha 3 AEP-0011 BPR-010 Closure Re-Review

Status: **ACCEPTANCE-READY FOR SEPARATE MAINTAINER DECISION**

AEP: `rfcs/AEP-0011-browser-resource-profile.md` (`Proposed`)

PR: #110 — `docs(alpha3): close AEP-0011 canonical ordering blocker`

Protocol-only head: `2902b2013f6efd1ab797a34c592e1c882a3c3975`

Protocol + focused evidence head: `38f7110e5da0c4a8abf04578b25b90e30aa83ed4`

Previous acceptance review: `docs/acceptance/alpha3-aep-0011-acceptance-review.md`

Acceptance-evidence baseline: `103c049c51d199c3c744f675283aa8480ca20774`

## 1. Review question

The previous acceptance-oriented review found one remaining semantic blocker:

> BPR-010 — canonical collection ordering / digest determinism.

This re-review asks whether PR #110 closes that protocol ambiguity without delegating meaning to Schema, TCK, browser/provider enumeration, or a reference implementation, and whether the focused evidence is strong enough to treat BPR-010 as closed for acceptance readiness.

This record does **not** change the lifecycle state itself. `Proposed -> Accepted` remains a separate explicit protocol-maintainer decision.

## 2. Protocol closure reviewed

AEP-0011 now fixes canonical collection order before RFC 8785 JCS/content-addressed identity.

The reviewed rules are:

1. Manifest selected localStorage origins use ascending canonical tuple-origin order;
2. Manifest selected cookie stored domains use ascending canonical stored-domain order;
3. `BrowserStateImage.origins[]` uses ascending canonical tuple-origin order;
4. per-origin localStorage entries retain the already-governed unsigned UTF-16 key order;
5. `BrowserStateImage.cookies[]` uses lexicographic portable identity order `(name, domain, hostOnly, path)`;
6. canonical tuple-origin/domain text comparison is bytewise over canonical serialization;
7. cookie identity text is compared over its exact RFC-defined stored octet sequence and `hostOnly` uses `false < true`;
8. provider/browser enumeration, insertion order, object iteration, and transport-return order are non-authoritative;
9. profile ordering is applied before JCS and before Artifact/state digest computation;
10. a raw document with noncanonical collection order cannot be treated as Browser v0.1 canonical Manifest/Image identity bytes;
11. comparator/order changes are representation-revision changes and cannot silently reinterpret old identity.

The rule therefore fixes the semantic input to future Schema/TCK rather than letting downstream work choose a comparator.

## 3. Comparator/interoperability review

### Tuple origins and domains

WHATWG canonical origin serialization and canonical stored cookie-domain text are ASCII-compatible serialized identities for the admitted profile. Bytewise lexicographic comparison is deterministic and locale-independent.

### Cookie identity

RFC 10025 processes cookie state as US-ASCII octets. The AEP comparator is applied to the exact stored `name`/`path` octet sequences rather than locale collation, browser string ordering, or provider formatting. `hostOnly` is explicit and ordered `false < true`.

The wording "RFC cookie octet sequence" is read as the stored RFC-defined US-ASCII octet sequence, not as a requirement that Path use the ABNF production named `cookie-octet`; RFC 10025 Path uses its own permitted octet range. This is an editorial terminology precision point, not a different comparator or unresolved protocol choice.

### JCS boundary

The AEP correctly places profile-defined array ordering **before** RFC 8785 JCS. JCS canonicalizes JSON representation but does not make profile collection membership/order decisions for arrays. No circular content identity is introduced.

## 4. Focused BAE-013 evidence

Workflow: `Browser Canonical Ordering Evidence #1`

Run: `33346671492`

Artifact: `browser-canonical-ordering-evidence-38f7110e5da0c4a8abf04578b25b90e30aa83ed4`

Artifact ID: `9742204077`

Artifact digest: `sha256:3be6a35b6529e4ad242b944b704e5374b86ca354c9471d320292d1c0f6f422e7`

Source binding:

```text
repositorySha = 38f7110e5da0c4a8abf04578b25b90e30aa83ed4
sourceBinding.mode = exact-checked-out-head
sourceBinding.verified = true
```

### BAE-013-MANIFEST

- 36 combinations of origin-selection and cookie-domain-selection ordering were exercised;
- all canonicalized to exactly one canonical Manifest digest:
  `7102a3ba35387017f0957b35950fa3f4a1fb86d7ea8f430315b23fc6940c7fa6`;
- the intentionally broken provider-order-preserving path produced 36 distinct digests;
- input list order therefore has no semantic meaning.

### BAE-013-IMAGE

- 96 combinations covering cookie permutation, origin permutation, and localStorage enumeration reversal were exercised;
- all canonicalized to one BrowserStateImage digest:
  `9a50223e1d485187275c7cebbe825082b6ae4f963bbf782fd7ecba862bf419dc`;
- the intentionally broken provider-order-preserving path produced 96 distinct digests;
- expected cookie identity ordering is fixed independently of the input order;
- browser/provider enumeration is explicitly not used as the oracle.

### BAE-013-DUPLICATES

The focused evidence also verifies fail-closed rejection of:

- duplicate Manifest selection identity;
- duplicate `BrowserStateImage.origins[]` identity;
- duplicate cookie portable identity.

The evidence runner is intentionally provider-neutral and browser-free because BPR-010 is a protocol canonicalization property rather than a browser-engine behavior property. The restricted ASCII evidence serializer is explicitly not promoted into a production JCS implementation or portable runtime authority.

## 5. Exact-head gate state

At `38f7110e5da0c4a8abf04578b25b90e30aa83ed4`, all thirteen applicable pull-request workflows completed successfully:

- Governance #761 — `33346671467`;
- Browser Canonical Ordering Evidence #1 — `33346671492`;
- Browser Recovery Residual Evidence #15 — `33346671465`;
- Browser Selection Evidence #27 — `33346671466`;
- Relational Parity #83 — `33346671452`;
- Browser Settlement Evidence #33 — `33346671446`;
- CI #690 — `33346671451`;
- Browser Cookie Partition Evidence #37 — `33346671449`;
- Browser Shipping Partition Evidence #8 — `33346671470`;
- Browser Shipping Cookie Fidelity Evidence #6 — `33346671438`;
- Browser Shipping Cookie Provenance Evidence #5 — `33346671464`;
- Browser Acceptance Evidence #40 — `33346671460`;
- Browser Shipping Residual Evidence #7 — `33346671443`.

The prior Chromium/Gecko/WebKit acceptance matrix therefore remains green after the BPR-010 protocol amendment.

## 6. Re-review of prior blocker closure

The BPR-010 amendment does not reopen BPR-001..BPR-009:

- capability/profile identity remains narrow;
- partitioned state remains outside Browser v0.1;
- cookie `hostOnly`/stored Default remain lossless-or-fail-closed;
- temporal-sensitive restore remains fail-closed where equivalence cannot be established;
- selection membership remains finite/exact/complete-set;
- DOMString representation remains lossless;
- settlement remains evaluator/control positive-witness based;
- residual excluded state remains isolated/bound/fail-closed;
- Chromium/Gecko/WebKit evidence remains reviewable and passing.

The new collection-ordering rule only makes the already-governed logical state identity deterministic at the exact-byte/digest boundary.

## 7. Remaining semantic blockers

This re-review found **no remaining semantic blocker** in AEP-0011 after BPR-010 closure.

Specifically, the review did not find a remaining choice that future Browser Spec/Schema/TCK/runtime would have to invent for:

- capability/profile identity;
- selected-state membership;
- tuple-origin/state partition boundary;
- cookie identity or temporal eligibility;
- DOMString representation;
- Manifest/Image collection order;
- canonical bytes/digest determinism;
- restore/reset fidelity;
- settlement;
- residual-state handling;
- Subject versus Evaluator/Control authority.

This is an acceptance-readiness conclusion, not lifecycle promotion.

## 8. Lifecycle disposition

```text
BPR-001..BPR-009: CLOSED for acceptance review
BPR-010 protocol decision: INCORPORATED
BPR-010 focused evidence: SATISFIED
Acceptance-oriented semantic re-review: NO REMAINING SEMANTIC BLOCKER
AEP-0011 lifecycle: Proposed
Acceptance readiness: READY FOR SEPARATE MAINTAINER DECISION
Proposed -> Accepted: NOT AUTHORIZED
Browser normative Spec/Schema/TCK/runtime: NOT AUTHORIZED
PR #108/#109/#110 merge: NOT AUTHORIZED
```

## 9. Next governed step

The next step is **not** automatic downstream implementation.

Before any `Proposed -> Accepted` transition:

1. synchronize the blocker/roadmap/adoption metadata to the reviewed BPR-010 closure state;
2. run exact-head governance/CI on that metadata-only closure head;
3. present the exact reviewed head and closure evidence for a **separate explicit protocol-maintainer lifecycle decision**.

Only an explicit authorization may change AEP-0011 from `Proposed` to `Accepted`. Generic continuation does not authorize that transition, and merge authorization remains separate.

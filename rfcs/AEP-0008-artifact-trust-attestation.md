# AEP-0008 — Artifact Trust and Attestation Contract v0.1

- Status: Accepted
- Authors: AVP maintainers and contributors
- Created: 2026-08-16
- Accepted: 2026-08-16
- Acceptance decision: Approved by the protocol maintainer during the Alpha 2 readiness review. This approves the protocol direction only; the AEP is not Final and this decision does not authorize merge, tag, or release.
- Target AVP version: 0.1

## Problem

AVP can already identify immutable Artifact bytes and detect integrity mismatches, but digest integrity alone does not answer whether an Artifact was authenticated by an acceptable signer or whether authenticated attestation material applies to the Artifact under an evaluator-defined trust policy.

The Alpha 2 roadmap therefore requires an explicit artifact trust / signature / attestation decision. Without a portable contract, implementations can accidentally conflate several different claims:

- the Artifact bytes match a declared digest;
- an attestation envelope is syntactically valid;
- a cryptographic signature verifies under some candidate key;
- a signer or workload identity was authenticated;
- the attestation actually names the Artifact being evaluated;
- the authenticated identity is authorized by the verification trust policy; and
- the predicate semantics are understood and accepted.

Conflating these claims into a single `trusted` boolean creates interoperability and security ambiguity.

## Motivation / interoperability case

An evaluator may receive the same AVP Artifact through a local ArtifactStore, an OCI registry, object storage, or another transport. The Artifact content identity remains stable because it is defined over exact bytes.

The evaluator may also receive one or more authenticated attestations through independent channels. Different implementations may use different cryptographic providers, KMS/HSM services, identity systems, transparency services, or policy engines. AVP needs those implementations to agree on the verification-relevant result even when their mechanisms differ.

The portable contract therefore needs to answer:

1. which exact AVP Artifact an attestation applies to;
2. whether the attestation representation itself still matches its declared Artifact identity;
3. whether the attestation envelope/payload was authenticated without type confusion;
4. which authenticated signer/identity evidence was established by the external trust mechanism;
5. whether that identity and attestation satisfy the selected AVP verification trust policy; and
6. why a trust decision failed when it was not accepted.

## Existing standards analysis

### in-toto Attestation Framework

The in-toto Attestation Framework defines a Statement layer that binds an attestation to one or more immutable subjects by digest and identifies a predicate type. AVP should compose with that subject-binding model rather than introduce another generic provenance statement format.

For the v0.1 binding, an AVP Artifact identified as `sha256:<hex>` maps to an in-toto subject digest entry whose `sha256` value is the same lowercase hexadecimal digest body. Names and locators remain metadata and do not replace the digest binding.

### DSSE

DSSE defines a signature protocol over pre-authentication encoding of payload type and payload bytes. This is useful for avoiding payload-type confusion while remaining independent of payload serialization and cryptographic provider choice.

DSSE intentionally does not define key management or PKI. Its envelope `keyid` is an unauthenticated hint for key lookup and cannot be treated as signer identity or policy authorization.

AVP may define a DSSE + in-toto interoperability binding, but successful DSSE verification is only an authentication input to AVP trust-policy evaluation.

### SLSA and domain-specific predicates

SLSA provenance is one example of an in-toto predicate ecosystem. AVP does not redefine SLSA provenance, SLSA levels, builder identity semantics, or other predicate-specific policy. A profile may require a particular predicate type later, but v0.1 keeps the trust contract generic.

### Sigstore, X.509, workload identity, and transparency services

These ecosystems can establish signer identities, key ownership, certificate chains, transparency evidence, timestamps, revocation state, or workload identity. AVP consumes the resulting authenticated identity/evidence through a verification binding; it does not standardize their infrastructure.

## Proposed semantics

AVP v0.1 introduces an **Artifact Attestation Verification** contract with the following conceptual resources.

### Attestation binding

An attestation binding identifies:

- the envelope/statement binding profile used to authenticate and interpret the attestation;
- the exact Artifact content identity being evaluated;
- the authenticated statement/payload type;
- the authenticated subject digest(s) extracted from the statement; and
- the predicate type when the selected statement format exposes one.

The binding never changes Artifact content identity.

### Authenticated signer identity

A verification mechanism may establish a machine-readable signer/identity value plus mechanism-specific evidence. AVP treats this identity as an authenticated input only when the selected verifier binding establishes it.

Caller-supplied aliases, unauthenticated `keyid` hints, display names, or locators are not authenticated signer identity by themselves.

### Trust policy

A trust policy is evaluator-owned configuration that determines which authenticated signer/identity, attestation binding, and statement/predicate conditions are acceptable for a verification decision.

AVP standardizes portable policy inputs/outcomes needed for conformance, not a universal policy language. Implementations may use CEL, Rego, code, configuration, or another policy engine provided the externally observable semantics match the contract.

### Trust verification result

A trust verification result records the evaluated Artifact digest, attestation binding, authenticated identity when established, policy identity, and one terminal outcome.

The terminal outcomes must preserve at least:

- `accepted` — authentication, Artifact-subject binding, identity resolution, and policy evaluation all succeeded;
- `integrity-failed` — the attestation representation bytes do not match the declared attestation Artifact size/digest;
- `malformed` — the selected attestation binding could not be parsed/validated safely;
- `unsupported` — the implementation does not support the required binding/statement/predicate semantics;
- `authentication-failed` — signature/envelope authentication failed;
- `subject-mismatch` — authenticated statement does not bind the requested Artifact digest;
- `identity-rejected` — signer/identity could not be established or is not allowed by policy;
- `policy-rejected` — authenticated/bound attestation does not satisfy another required policy condition.

An implementation may expose more detailed diagnostics, but it must not collapse failure outcomes into `accepted`.

## Proposed normative requirements

### AVP-TRUST-001 — Artifact identity remains independent from attestation metadata

Attestation/signature/signer/policy metadata MUST NOT redefine the Artifact content digest or mutate Artifact bytes published under that digest.

### AVP-TRUST-002 — Exact Artifact subject binding

Before reporting trust acceptance, a verifier MUST establish that the authenticated attestation statement binds the exact AVP Artifact content identity being evaluated.

### AVP-TRUST-003 — Authenticated payload and type binding

When an implementation claims an authenticated envelope binding, it MUST authenticate both the statement payload bytes and the payload/statement type according to that binding, and MUST fail closed on authenticated-content or authenticated-type tampering.

### AVP-TRUST-004 — Authentication is not trust-policy acceptance

A verifier MUST NOT report an Artifact as accepted merely because one or more cryptographic signatures validate. Acceptance additionally requires an authenticated signer/identity input and successful evaluation against the selected trust policy.

### AVP-TRUST-005 — Signer hints are non-authoritative

An unauthenticated signer hint such as DSSE `keyid`, a caller label, locator, or display name MUST NOT by itself establish signer identity or policy authorization.

### AVP-TRUST-006 — Required trust evaluation fails closed

A required trust decision MUST NOT produce `accepted` when attestation Artifact integrity fails, the attestation is malformed/unsupported, authentication fails, Artifact subject binding fails, authenticated identity cannot be established or is rejected, or required policy conditions fail.

### AVP-TRUST-007 — Trust outcomes remain distinguishable

A verifier MUST preserve a machine-readable terminal outcome that distinguishes accepted trust from attestation integrity failure, malformed/unsupported material, authentication failure, subject mismatch, identity rejection, and policy rejection.

### AVP-TRUST-008 — Signing authority remains privileged

Signing private keys, signing credentials, and equivalent signing authority used by an AVP-controlled publication path MUST NOT be exposed to the Subject execution context.

### AVP-TRUST-009 — Unsupported assurance is not implied

An implementation MUST NOT claim verification of a predicate, signer identity property, transparency property, certificate property, revocation property, or other trust condition that its selected binding/policy did not actually verify.

## Protocol/schema changes

The proposal expects additive resources rather than changes to `ArtifactRef` identity:

- an `ArtifactAttestation` or equivalent reference/resource describing the authenticated attestation material and its target Artifact;
- an `ArtifactTrustPolicy` portable conformance subset or policy identity/binding resource;
- an `ArtifactTrustResult` machine-readable verification result with the terminal outcome taxonomy above;
- a new requirement index and `avp-artifact-trust-v0.1` TCK profile.

The exact resource names and fields will be finalized in the normative spec and schemas. The AEP intentionally does not make Python class names normative.

## Security considerations

### Content identity separation

Signing or attaching an attestation must not alter the Artifact digest. Otherwise trust metadata could fork identity for identical bytes and break existing Evidence integrity semantics.

### Attestation representation integrity

Attestation bytes referenced through `ArtifactRef` remain subject to AVP Evidence integrity semantics before they can be trusted as the representation selected for authentication. A digest/size mismatch is an integrity failure and must not be blurred into parser or signature semantics.

### Signature wrapping / type confusion

An authenticated envelope binding must cover the payload type together with the payload bytes when that binding promises type authentication. A verifier must evaluate the authenticated statement, not an unauthenticated parallel copy supplied by a caller.

### Signer substitution

Key identifiers and aliases are not proof of signer identity. The verification mechanism must establish the authenticated identity used by policy evaluation.

### Trust-policy bypass

Cryptographic success must not bypass signer authorization or other required policy checks. Unsupported checks must fail closed for a required trust decision rather than be silently ignored.

### Subject secret exposure

Signing authority is evaluator/control material. A convenience publication API must not inject signing private keys or equivalent credentials into untrusted Subject execution context.

### Algorithm and PKI agility

AVP v0.1 does not mandate a cryptographic algorithm, certificate ecosystem, or trust-root format. Profiles can narrow those choices later when a verification-specific interoperability need justifies it.

## Backward compatibility

This proposal is additive:

- existing `ArtifactRef` digest semantics do not change;
- unsigned/unattested Artifacts remain valid AVP Artifacts;
- existing Evidence TCK remains authoritative for content identity/integrity;
- implementations that do not claim `avp-artifact-trust-v0.1` are not required to add a signing stack;
- future profiles may require trust verification for particular workflows without changing base Artifact identity.

## Conformance tests

The portable TCK will use implementation-neutral vectors/actions and must not require Python objects, a specific crypto library, certificate provider, Sigstore deployment, KMS, or network service.

Mandatory negative and positive controls should cover at least:

1. the attestation binds the exact requested Artifact digest;
2. an attestation Artifact digest/size mismatch is `integrity-failed` and cannot continue to acceptance;
3. an authenticated attestation for a different digest is rejected as `subject-mismatch`;
4. payload or authenticated type tampering fails authentication;
5. a valid signature from a signer not accepted by policy is not reported as trusted;
6. an unauthenticated signer hint cannot substitute for authenticated identity;
7. malformed and unsupported attestations fail closed with distinguishable outcomes;
8. policy rejection remains distinct from authentication failure;
9. accepted results bind the policy identity and evaluated Artifact digest;
10. false claims about unverified trust properties are rejected;
11. publication paths do not expose signing authority through Subject-facing capabilities.

Reference-only fixtures may inject corrupted Artifact bytes/envelopes, alternate signer mappings, or deterministic authentication witnesses to exercise negative controls. Those fixtures must not become part of the language-neutral TCK contract.

## Reference implementation

After the normative spec, schemas, and TCK are stable, the Python reference runtime may add:

- a small attestation verifier/publisher SPI;
- deterministic reference fixtures for conformance;
- a DSSE/in-toto binding implementation if it can be done without making a particular crypto provider a core protocol dependency;
- ArtifactStore composition for storing attestation bytes as independent immutable Artifacts/Evidence;
- machine-readable `ArtifactTrustResult` serialization.

The reference implementation must not define semantics that are absent from the normative contract. Production-grade key custody, certificate issuance, transparency infrastructure, and organization-specific policy engines remain outside the reference runtime's protocol authority.

## Alternatives

### Put signature fields directly on `ArtifactRef`

Rejected because signature/trust state can vary while exact bytes remain identical.

### Define a new AVP signing envelope

Rejected because DSSE/in-toto already cover the generic envelope/statement problem and AVP has no demonstrated interoperability gap requiring a competing format.

### Make Sigstore mandatory

Rejected for v0.1 because it would turn a portable verification protocol into a deployment-specific trust-stack requirement. A future Sigstore interoperability profile may be appropriate.

### Accept any cryptographically valid signature

Rejected because authenticity under an arbitrary key is not authorization under evaluator policy.

### Standardize a universal AVP policy language now

Rejected. The immediate interoperability requirement is deterministic trust inputs/outcomes and fail-closed semantics, not ownership of a general authorization-policy language.

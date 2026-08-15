# AVP Artifact Trust and Attestation Contract v0.1

Status: Draft normative candidate.

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as described in BCP 14 when, and only when, they appear in all capitals.

## 1. Scope

This specification defines portable verification semantics for deciding whether authenticated attestation material is applicable to an AVP Artifact and accepted by an evaluator-selected trust policy.

It composes with the AVP Evidence/Artifact identity contract. It does not redefine Artifact digest semantics, generic signature envelopes, cryptographic algorithms, PKI, certificate issuance, transparency logs, key management, registries, or universal policy languages.

## 2. Authority boundaries

AVP owns the verification-specific relationship among:

- the exact AVP Artifact content identity under evaluation;
- the integrity-verified immutable attestation representation;
- an authenticated attestation statement and its authenticated type;
- authenticated signer/identity evidence established by an external verification mechanism;
- evaluator-selected trust-policy identity and conditions; and
- the terminal AVP trust outcome.

External standards and deployments remain authoritative for generic mechanisms such as DSSE signing/verification, in-toto Statement syntax, SLSA predicate semantics, Sigstore/X.509/workload identity, certificate-chain validation, transparency evidence, revocation, KMS/HSM operations, and cryptographic provider APIs.

## 3. Artifact identity is unchanged

An Artifact remains the exact immutable byte sequence identified by the Evidence contract's SHA-256 content identity.

Attestation bytes are separate content from the target Artifact. An implementation MAY store an attestation itself as an AVP Artifact, but doing so produces the attestation Artifact's own digest; it does not modify the target Artifact digest.

Signer identity, signature bytes, certificates, transparency metadata, predicate metadata, policy identity, verification result, locators, and other trust metadata do not participate in the target Artifact content identity.

## 4. ArtifactAttestation

`ArtifactAttestation` is a portable reference that associates:

- `artifactDigest` — the AVP Artifact content identity whose trust is to be evaluated;
- `attestation` — an `ArtifactRef` identifying the immutable attestation representation bytes; and
- `bindingProfile` — the machine-readable identifier of the envelope/statement binding used to authenticate and interpret those bytes.

`artifactDigest` is a declared target used to initiate verification. It is not proof that the authenticated statement actually names that Artifact. The verifier must establish subject binding from authenticated attestation content before acceptance.

The v0.1 Core contract does not require one binding profile. A binding profile MUST define how authenticated payload bytes, authenticated payload/statement type, subject digests, predicate type when applicable, and authenticated signer/identity evidence are obtained without relying on unauthenticated parallel caller data.

## 5. Authenticated attestation observation

A selected binding mechanism produces verification observations used by AVP trust evaluation. At minimum the trust evaluator needs to determine:

- whether the attestation representation is well-formed for the selected binding;
- whether required authentication succeeded;
- which payload/statement type was authenticated;
- which subject digest identities were authenticated by the statement;
- which signer/identity, if any, was established by the configured trust mechanism; and
- which predicate type or other binding-level type was authenticated when the selected statement exposes one.

AVP does not standardize the internal API carrying these observations between a cryptographic library and an implementation.

An unauthenticated key identifier, alias, display name, locator, or caller label is not an authenticated signer identity merely because it appears next to a valid signature.

## 6. Artifact subject binding

A trust verifier evaluates one requested AVP `artifactDigest` at a time.

Before returning `accepted`, the verifier must establish from authenticated statement content that at least one subject digest identifies exactly the requested Artifact.

For an in-toto Statement v1 binding, an AVP identity `sha256:<hex>` matches a subject whose digest set contains `sha256: <hex>`. Subject `name`, `uri`, or other descriptor fields do not replace digest matching.

A statement authenticated correctly for a different Artifact remains authentic material, but it is not applicable to the requested Artifact and produces `subject-mismatch`.

## 7. Trust policy

`ArtifactTrustPolicy` is the portable minimum policy surface required by this profile. It contains:

- `policyId` — stable evaluator-owned policy identity;
- `allowedSignerIdentities` — authenticated signer identities accepted by this policy;
- optional `allowedBindingProfiles` — permitted attestation binding profiles; and
- optional `allowedPredicateTypes` — permitted authenticated predicate types.

An omitted optional allowlist means this v0.1 portable policy does not constrain that dimension. An empty allowlist is invalid because it would be ambiguous with an omitted constraint.

Deployments MAY evaluate additional policy conditions. They MUST NOT report an additional condition as verified unless it was actually evaluated from authenticated or otherwise authoritative inputs.

The portable policy resource is not a universal authorization language and does not standardize certificate, transparency, revocation, timestamp, or organization-specific policy syntax.

## 8. Trust verification result

`ArtifactTrustResult` records the terminal result of evaluating one `ArtifactAttestation` against one `ArtifactTrustPolicy`.

It binds:

- `artifactDigest` — requested target Artifact identity;
- `attestationDigest` — declared immutable identity of the attestation bytes evaluated;
- `bindingProfile` — selected binding profile;
- `policyId` — policy actually evaluated;
- `outcome` — terminal trust outcome;
- optional authenticated `signerIdentity`;
- optional authenticated `statementType` and `predicateType`; and
- optional `verifiedProperties` and diagnostic details.

The terminal outcomes are:

- `accepted` — attestation Artifact integrity, authentication, exact Artifact subject binding, authenticated signer identity, and all required policy conditions succeeded;
- `integrity-failed` — resolved attestation bytes failed declared Artifact size or digest verification;
- `malformed` — integrity-verified attestation material could not be parsed/validated safely for the selected binding;
- `unsupported` — a required binding/statement/predicate semantic is not supported by the implementation;
- `authentication-failed` — required attestation authentication failed;
- `subject-mismatch` — authenticated subject identity does not match the requested Artifact;
- `identity-rejected` — authenticated signer identity could not be established or is not authorized by the policy;
- `policy-rejected` — authentication, subject binding, and signer identity succeeded but another required policy condition failed.

`accepted` requires an authenticated `signerIdentity`. Implementations MAY expose more detailed diagnostics, but additional fields MUST NOT contradict the terminal outcome.

## 9. Processing order and fail-closed behavior

A verifier MUST NOT use later trust-policy success to erase an earlier failure. Conceptually the decision preserves these gates:

1. resolve and integrity-check attestation representation bytes;
2. parse the selected binding safely;
3. authenticate the payload and authenticated type according to that binding;
4. derive subject/type/signer observations only from authenticated or otherwise binding-authoritative inputs;
5. bind the authenticated subject to the requested Artifact digest;
6. establish authenticated signer/identity evidence;
7. evaluate the selected policy; and
8. emit one terminal result.

Implementations may optimize or combine steps internally, but the observable result must preserve the same fail-closed semantics.

An integrity failure while resolving attestation Artifact bytes produces `integrity-failed`; the verifier MUST NOT continue by parsing or authenticating the mismatched bytes as the declared attestation Artifact.

## 10. Envelope and statement interoperability

AVP v0.1 intentionally does not invent a generic signing envelope.

A DSSE + in-toto Statement binding is a valid interoperability approach when the implementation:

- verifies the DSSE signature over the binding-defined pre-authentication encoding of payload type and exact payload bytes;
- interprets the authenticated payload as the claimed in-toto Statement type;
- obtains target subject identity from the authenticated Statement subject digest set; and
- does not treat DSSE `keyid` as authoritative signer identity.

Other binding profiles MAY be defined if they provide equivalent authenticated inputs required by this contract.

## 11. Publication security

An AVP-controlled signed/attested publication path is privileged verification infrastructure.

Signing private keys, signing credentials, KMS authorization, and equivalent signing authority must remain outside Subject execution context. A Subject-facing capability may request publication only through an explicitly authorized mediated route; possession of an Artifact or Evidence handle does not grant signing authority.

This contract does not require a conforming verifier-only implementation to provide publication.

## 12. Assurance honesty

A trust result may describe only properties actually established by the selected binding and policy.

For example, signature verification alone does not establish transparency inclusion, certificate revocation status, trusted timestamp, SLSA level, builder authorization, or organization policy. Such properties may appear in `verifiedProperties` only when the implementation actually verified them from the required authoritative evidence.

Unknown or unsupported required semantics must not be silently treated as satisfied.

## 13. Normative requirements

### AVP-TRUST-001 — Artifact identity remains independent from attestation metadata

Attestation, signature, signer, certificate, transparency, predicate, policy, and trust-result metadata **MUST NOT** redefine the target Artifact content digest or mutate Artifact bytes published under that digest.

### AVP-TRUST-002 — Exact Artifact subject binding

Before reporting `accepted`, a verifier **MUST** establish from authenticated attestation content that the attestation binds the exact AVP Artifact content identity being evaluated.

### AVP-TRUST-003 — Authenticated payload and type binding

For the selected attestation binding, a verifier **MUST** authenticate the statement payload bytes and the binding-defined payload/statement type, and **MUST** fail closed when authenticated content or authenticated type has been tampered with.

### AVP-TRUST-004 — Authentication is not trust-policy acceptance

A verifier **MUST NOT** report `accepted` solely because a cryptographic signature or equivalent authenticator validates. Acceptance additionally requires authenticated signer/identity evidence and successful evaluation of the selected trust policy.

### AVP-TRUST-005 — Signer hints are non-authoritative

An unauthenticated signer hint, key identifier, caller label, locator, alias, or display name **MUST NOT** by itself establish authenticated signer identity or policy authorization.

### AVP-TRUST-006 — Required trust evaluation fails closed

A required trust evaluation **MUST NOT** produce `accepted` when attestation Artifact integrity fails, the attestation is malformed or unsupported, authentication fails, exact Artifact subject binding fails, authenticated signer identity cannot be established or is rejected, or any required policy condition fails.

### AVP-TRUST-007 — Trust outcomes remain distinguishable

A verifier **MUST** emit a machine-readable terminal outcome that distinguishes `accepted`, `integrity-failed`, `malformed`, `unsupported`, `authentication-failed`, `subject-mismatch`, `identity-rejected`, and `policy-rejected`.

### AVP-TRUST-008 — Signing authority remains privileged

When an implementation provides AVP-controlled attestation publication, signing private keys, signing credentials, KMS authorization, and equivalent signing authority **MUST NOT** be exposed through the Subject execution context or an undeclared Subject capability.

### AVP-TRUST-009 — Unsupported assurance is not implied

An implementation **MUST NOT** claim a predicate, signer-identity property, transparency property, certificate property, revocation property, timestamp property, or other trust condition as verified unless the selected binding/policy actually verified that property from authoritative evidence.

## 14. Conformance boundary

The `avp-artifact-trust-v0.1` TCK validates AVP-owned observable semantics. It does not reproduce DSSE, in-toto, Sigstore, X.509, SLSA, or cryptographic-library conformance suites.

Portable cases describe trust inputs/actions/outcomes independently of Python classes or a specific signing algorithm. An implementation adapter may configure implementation-native signers, identities, envelopes, or fault fixtures to execute those cases. Adapter gaps are runner errors, not permission to weaken a case.

`AVP-TRUST-008` applies conditionally when the implementation declares `artifact-attestation-publication`.

## 15. Non-goals

This specification does not standardize:

- private/public key formats or cryptographic algorithms;
- key generation, rotation, custody, KMS, HSM, or secret-manager APIs;
- certificate profiles, CA policy, workload-identity issuance, or trust-root distribution;
- transparency-log operation or native inclusion-proof formats;
- revocation/timestamp infrastructure;
- OCI, registry, object-store, or filesystem publication transport;
- a universal policy language;
- SLSA provenance correctness or SLSA level calculation;
- a Python signing/verifier API;
- a universal attestation discovery protocol.

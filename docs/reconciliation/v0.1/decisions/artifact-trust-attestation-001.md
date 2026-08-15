# Artifact Trust and Attestation Reconciliation Decision 001

- Status: Proposed
- Date: 2026-08-16
- Scope: AVP Artifact Trust / Signature / Attestation v0.1

## Context

AVP already defines Artifact content identity and integrity independently from Evidence identity. An Artifact is the exact immutable byte sequence identified by `sha256:<lowercase-hex>`, while locators and Evidence metadata do not redefine that identity.

The Alpha 2 roadmap separately calls for an `artifact trust / signature / attestation decision` and for reference support for signed/attested Artifact publication. That work must not retroactively change Artifact identity or make a Python signing implementation the source of protocol semantics.

Existing ecosystems already own generic attestation envelopes, cryptographic signature algorithms, public-key infrastructure, transparency services, and software-supply-chain predicate vocabularies. AVP's interoperability gap is narrower: a verifier needs a portable way to determine whether authenticated attestation material actually applies to an AVP Artifact and whether the authenticated signer/identity satisfies an explicit verification trust policy.

## Decision

1. AVP keeps **Artifact integrity**, **attestation authentication**, and **trust-policy acceptance** as distinct verification facts.
2. Artifact content identity remains the exact-byte SHA-256 identity defined by `AVP-EVIDENCE-001`. Signature, signer, certificate, transparency, predicate, policy, and attestation metadata MUST NOT redefine or mutate that identity.
3. An attestation used for Artifact trust MUST bind the exact Artifact content identity it claims to describe. A cryptographically valid attestation over a different Artifact is not applicable to the requested Artifact.
4. AVP does not define a new generic signature envelope. A profile may bind an established envelope/statement format such as DSSE plus in-toto Statement, provided the binding preserves payload-type authentication and exact Artifact subject identity.
5. Cryptographic validity alone does not establish AVP trust. A verifier MUST evaluate signer/identity evidence against an explicit trust policy before reporting the Artifact as accepted by that policy.
6. Signer hints, aliases, key identifiers, certificate display names, URI locators, and caller-supplied labels are not independently authoritative trust identities. In particular, an unauthenticated key identifier MUST NOT be accepted as proof of signer identity.
7. Trust-policy evaluation MUST fail closed for required trust decisions when authentication fails, subject binding fails, signer/identity resolution is unavailable or untrusted, or the required statement/predicate semantics are unsupported.
8. Verification results MUST preserve enough machine-readable outcome detail to distinguish at least: malformed/unsupported attestation, authentication failure, Artifact-subject mismatch, signer/identity rejection, policy rejection, and accepted trust.
9. Signing private keys, credentials, and equivalent signing authority are privileged evaluator/control material. They MUST NOT be introduced into Subject execution context merely to publish or verify AVP trust evidence.
10. Key generation, key storage, certificate issuance, CA policy, workload identity, transparency-log operation, revocation distribution, timestamping infrastructure, registry transport, and cryptographic algorithm selection remain external mechanisms unless a future AVP profile identifies a verification-specific interoperability gap.

## Existing standards boundary

### in-toto Attestation Framework

The in-toto Statement model binds an attestation to immutable subject resources by digest and identifies the predicate type. AVP may use that model as an interoperability binding rather than inventing another generic statement envelope.

AVP remains responsible for mapping the in-toto subject digest to the AVP Artifact content identity and for deciding whether the resulting authenticated statement satisfies an AVP verification trust policy.

### DSSE

DSSE authenticates payload bytes together with the payload type through pre-authentication encoding and intentionally leaves key management / PKI outside its scope. Its `keyid` is an unauthenticated lookup hint, not a trusted identity assertion.

AVP may use DSSE as an envelope binding, but AVP MUST NOT treat successful DSSE signature verification or `keyid` equality alone as trust-policy acceptance.

### SLSA and other predicates

SLSA provenance and other in-toto predicates may be carried as attestation predicates. Their domain-specific semantics remain owned by their defining specifications. AVP v0.1 does not redefine SLSA levels, provenance correctness, vulnerability semantics, or generic software-supply-chain policy.

### Sigstore / PKI / transparency mechanisms

Deployments may use Sigstore, X.509, workload identity, KMS/HSM systems, transparency logs, or other trust mechanisms. Those mechanisms may supply authenticated identity and supporting evidence to an AVP trust-policy evaluator, but their infrastructure and native verification semantics are not re-specified by AVP Core.

## Promoted AVP semantics

- separation of Artifact content identity from attestation/trust metadata;
- exact Artifact-subject binding for trust decisions;
- authenticated payload-type/statement binding when an envelope format is claimed;
- separation of cryptographic authentication from trust-policy acceptance;
- explicit, fail-closed signer/identity policy evaluation;
- non-authoritative treatment of unauthenticated signer hints;
- machine-readable trust outcome/failure taxonomy;
- evaluator/control ownership of signing authority and Subject-secret separation;
- honest declaration of supported attestation bindings rather than pretending unsupported predicates or trust roots were verified.

## External / implementation-owned semantics

- private-key generation and custody;
- cryptographic provider APIs and language bindings;
- certificate-chain construction details;
- transparency-log clients and inclusion-proof formats;
- revocation/timestamp services;
- KMS/HSM integration;
- registry/object-store transport;
- exact policy engine implementation;
- Python protocol/dataclass/exception shapes;
- a particular signature algorithm, key format, certificate format, or trust-store representation.

## Rejected alternatives

### Add signature fields to `ArtifactRef`

Rejected. An Artifact can have zero, one, or many attestations under different policies without changing its exact bytes. Mixing signature metadata into `ArtifactRef` would collapse content identity and trust metadata and would make identical bytes acquire different protocol identities.

### Treat a valid signature as `trusted=true`

Rejected. Cryptographic authentication proves only that a signature verifies under a candidate verification key; it does not establish that the key/identity is authorized for the verification decision.

### Trust the envelope `keyid`

Rejected. Signer hints are useful for candidate-key lookup but are not authenticated identity assertions. Trust must come from the verification mechanism and explicit policy.

### Standardize one PKI or Sigstore deployment in AVP Core

Rejected. AVP needs portable verification outcomes across deployments, not ownership of generic identity, certificate, transparency, or key-management infrastructure.

### Sign a language-level Python object

Rejected. Cross-language interoperability requires an explicit byte/envelope binding. Python object representation, dict ordering, dataclass encoding, or implementation-specific canonicalization cannot define protocol authentication semantics.

## Consequences

- Existing Artifact digests and `ArtifactRef` resources remain backward compatible.
- A new attestation/trust resource can reference an Artifact without mutating Evidence or storage identity.
- Portable TCK vectors can test subject binding, authentication/policy separation, fail-closed behavior, and outcome taxonomy without requiring one crypto library or PKI.
- The reference runtime may implement a small verifier/publisher boundary, but it remains evidence of the normative contract rather than its authority.
- Signed/attested publication is additive and optional unless a selected future conformance profile explicitly requires it.

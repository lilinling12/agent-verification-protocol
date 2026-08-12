# AVP Evidence — Artifact and Evidence Identity

Status: Draft Normative Candidate for AVP v0.1.

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as described in BCP 14 when, and only when, they appear in all capitals.

## 1. Scope

This specification defines integrity and identity semantics for immutable artifacts used as AVP evidence. It does not standardize an object-store product, filesystem layout, transport protocol, serialization library, or encryption mechanism.

## 2. Artifact

An Artifact is an immutable finite byte sequence used or produced by verification. AVP identifies the representation that is actually retained or exchanged, not a language-level object that may later be serialized differently.

Artifact content identity uses SHA-256 encoded as:

```text
sha256:<64 lowercase hexadecimal characters>
```

The digest is computed over the exact Artifact bytes, with no implicit transformation by the storage layer.

## 3. Artifact reference

An `ArtifactRef` contains:

- `digest`: content identity of the exact bytes;
- `size`: byte length of those exact bytes;
- `mediaType`: media type of the identified representation; and
- optional `uri`: a locator from which an authorized consumer may retrieve the bytes.

`uri` is not identity. Two references with different locators can identify the same Artifact when their digests identify the same byte sequence.

Profiles MAY add namespaced metadata, but metadata MUST NOT redefine digest semantics.

## 4. Encoding boundary

A producer that starts with JSON, protobuf, an image object, a database row, or any other structured value chooses the representation bytes before Artifact identity is computed.

Canonical JSON, compression, redaction, encryption, transcoding, or other transformations produce different representation bytes unless byte-for-byte identical. A storage implementation MUST NOT silently apply an undocumented transformation and continue reporting the digest of the pre-transformation bytes.

## 5. Evidence

Evidence is an immutable verification-domain record with its own stable `evidenceId`. It references one Artifact and adds interpretation/handling metadata.

Core Evidence fields are:

- `evidenceId` — stable identity within the applicable verification scope;
- `type` — machine-readable evidence type;
- `artifact` — ArtifactRef;
- `classification` — handling classification;
- optional `producer` — machine-readable producer identity;
- optional `redaction` — redaction metadata; and
- optional namespaced `extensions`.

Evidence metadata is not part of Artifact content identity.

## 6. Classification

AVP v0.1 defines these handling classifications:

- `public`
- `workspace`
- `subject-visible`
- `evaluator-confidential`
- `secret`
- `regulated`

Classification controls handling and visibility. It does not alter the underlying Artifact digest.

## 7. Integrity verification

A consumer that dereferences an ArtifactRef and relies on the bytes for verification MUST verify both byte length and SHA-256 digest before treating the content as the referenced Artifact.

A mismatch is an integrity failure. An implementation MUST NOT silently accept mismatched bytes as the declared Artifact.

## 8. Indirection

Large or sensitive event payloads and evidence SHOULD be represented by ArtifactRef rather than repeated inline. AVP does not prohibit small inline values when a profile permits them, but an inline copy MUST NOT replace required Artifact integrity semantics when a verification claim depends on the referenced Artifact.

## 9. Immutability and deduplication

A digest identifies one byte sequence. Once bytes are published under an Artifact digest, an implementation MUST NOT mutate that content in place.

Implementations MAY deduplicate identical bytes. Deduplication MUST preserve the same observable content identity and integrity behavior.

## 10. Normative requirements

### AVP-EVIDENCE-001 — Exact-byte content identity

An Artifact **MUST** be identified by SHA-256 over the exact Artifact bytes and encoded as `sha256:<64 lowercase hexadecimal characters>`.

### AVP-EVIDENCE-002 — Locator is not identity

An Artifact locator such as `uri` **MUST NOT** redefine or replace content identity. References with different locators **MAY** identify the same Artifact digest.

### AVP-EVIDENCE-003 — Representation boundary

An Artifact storage implementation **MUST NOT** silently canonicalize, serialize, compress, redact, encrypt, or otherwise transform caller content while reporting the digest of different bytes.

### AVP-EVIDENCE-004 — Evidence and Artifact identity separation

Evidence **MUST** have a stable `evidenceId` distinct from Artifact content identity and **MUST** reference an ArtifactRef.

### AVP-EVIDENCE-005 — Metadata does not alter content identity

Evidence classification, producer, redaction metadata, retention metadata, locators, and extensions **MUST NOT** alter the Artifact digest for identical bytes.

### AVP-EVIDENCE-006 — Dereference integrity

An implementation that dereferences Artifact bytes for verification **MUST** reject or classify as an integrity failure any content whose byte length or SHA-256 digest does not match the declared ArtifactRef.

### AVP-EVIDENCE-007 — Immutable publication

An implementation **MUST NOT** mutate bytes in place after publishing them under an Artifact digest.

### AVP-EVIDENCE-008 — Reference-oriented transport

Large or sensitive evidence **SHOULD** be transported by reference so that event and verification records can preserve integrity without duplicating payload content.

## 11. Non-goals

This specification does not standardize S3, OCI, local filesystem storage, database schemas, filesystem sharding, garbage collection, retention enforcement, encryption-at-rest, signed URLs, upload APIs, or a universal URI scheme.

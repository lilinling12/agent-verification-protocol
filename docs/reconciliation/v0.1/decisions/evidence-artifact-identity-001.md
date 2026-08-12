# Evidence and Artifact Identity Reconciliation Decision 001

Status: Accepted for the AVP v0.1 draft candidate.

## Context

The historical AVP design, event schema, and Python reference runtime currently expose three different evidence representations. The design baseline models evidence as an immutable reference with `type`, `uri`, `digest`, producer, classification, and redaction metadata. The event schema has looser `payload_ref` and `evidence` reference shapes. The Python `Evidence` value object instead embeds arbitrary `data` next to a digest.

Those shapes are not safely interchangeable. In particular, hashing a language object is not the same operation as identifying stored artifact bytes, and a storage locator is not a content identity.

## Decision

1. AVP distinguishes **Artifact identity** from **Evidence identity**.
2. An Artifact is an immutable byte sequence identified by `sha256:<lowercase-hex>` over the exact stored bytes.
3. Serialization, canonicalization, compression, encryption, and other transformations occur before Artifact identity is computed. An Artifact Store MUST NOT silently canonicalize caller values.
4. `ArtifactRef` contains content identity and descriptive retrieval metadata. `digest` is authoritative for byte integrity; `uri` is only a locator and MUST NOT participate in content identity.
5. Media type and byte size describe the identified representation. They do not change the SHA-256 digest of identical bytes.
6. Evidence is a stable verification-domain identity that references an Artifact. Evidence classification, producer identity, redaction metadata, and retention metadata do not alter Artifact identity.
7. A conforming verifier MUST detect a digest mismatch when dereferenced bytes differ from the declared Artifact digest.
8. Large or sensitive evidence SHOULD be transported by reference rather than copied into every event or verification record.
9. Object-store technology, filesystem layout, URI scheme implementation, caching, sharding, compression, encryption-at-rest, and garbage collection are implementation concerns unless a future profile standardizes them.
10. The current Python `Evidence(data, digest)` representation is implementation drift. It remains unchanged in this specification PR and will be migrated only after the protocol contract, schemas, and TCK are established.

## Rejected alternatives

### Use `uri` as Artifact identity

Rejected because locators can move, expire, be re-signed, or vary across deployments while the underlying bytes remain identical.

### Hash canonical JSON objects inside the Artifact Store

Rejected because Artifact storage must support arbitrary bytes and media types. Canonical JSON is a codec concern. Hidden canonicalization would make integrity dependent on implementation-language behavior.

### Put classification and producer into the content digest

Rejected because the same bytes can legitimately have different evidence metadata in different verification contexts. Metadata changes must not rewrite content identity.

### Keep inline data as the canonical Evidence representation

Rejected because it couples evidence identity to transport/storage shape, duplicates large or sensitive payloads, and makes cross-implementation integrity semantics ambiguous.

## Consequences

- A future ArtifactStore SPI can be implemented without becoming normative protocol authority.
- Reference runtime migration must preserve the distinction between exact stored bytes and higher-level Python values.
- Event and verification schemas can converge on references without forcing a universal storage backend.
- Content-addressed deduplication becomes safe because equality is defined over bytes, not metadata.

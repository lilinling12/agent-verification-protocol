# Alpha 3 Relational State Canonical Model

Status: **DRAFT DESIGN DECISION — RS-BR-001 / RS-BR-002 CLOSED FOR PROPOSED-READINESS PURPOSES**

Proposal: AEP-0010 (Draft)
Parent: AEP-0009 (Accepted)

This document is non-normative design evidence. It fixes the canonical value and Artifact-identity direction that AEP-0010 must absorb before advancing to `Proposed`. It does not create a normative schema or Resource Capability by itself.

## 1. Decision summary

The Relational State v0.1 candidate will use:

1. JSON data constrained to the RFC 8785 JSON Canonicalization Scheme (JCS) input domain;
2. **no JSON numbers for relational numeric values** — integers and decimals are canonical strings inside typed value records;
3. exact Unicode strings preserved as-is, with no NFC/NFD normalization;
4. a common PostgreSQL/MySQL temporal precision range of 0–6 fractional second digits;
5. a common fixed-decimal portability range of precision 1–65 and scale 0–30 with `scale <= precision`;
6. a maximum of 65 significant decimal digits for the portable `integer` type;
7. distinct `RelationalStateManifest` and `RelationalStateImage` Artifact media types;
8. **no baseline ArtifactRef inside the Manifest**, preventing content-addressed identity cycles;
9. baseline binding through the Fabric resource's existing `identityArtifacts`, with Artifact role determined by media type rather than array position;
10. runtime snapshot ownership remaining in the existing Environment SnapshotRef/resource binding, not in `EnvironmentResource.identityArtifacts`.

## 2. External standards reused

### RFC 8785 — JSON Canonicalization Scheme

RFC 8785 is used only for canonical JSON byte generation. AVP Relational State owns the typed relational value model layered on top of it.

Relevant JCS properties:

- duplicate object property names are forbidden;
- canonical output is deterministic UTF-8 JSON;
- object properties are deterministically ordered;
- JSON strings are preserved as-is rather than Unicode-normalized;
- values needing precision beyond IEEE-754 JSON numbers should be represented as strings.

Therefore relational integers and decimals MUST NOT use JSON number tokens in canonical state material.

### RFC 4648 — base64url

Binary values use the URL/filename-safe Base64 alphabet from RFC 4648 Section 5. The relational profile chooses an **unpadded** canonical representation and requires canonical zero pad bits. Decoders MUST reject non-canonical alternate spellings that decode to the same bytes.

### RFC 9562 — UUID text

UUID values use the RFC 9562 `8-4-4-4-12` hex-and-dash form. AVP further canonicalizes alphabetic hex digits to lowercase so one UUID has one relational lexical form.

### RFC 3339 — Internet timestamps

`timestamp-instant` uses the RFC 3339 date/time shape but the relational profile narrows it to UTC `Z`, seconds `00..59`, and profile-declared fractional precision. Leap-second lexical values are not part of v0.1 because the target relational engines do not share a portable leap-second storage model.

`date`, `time-local`, and `timestamp-local` use similarly strict ISO-style lexical forms but do not claim RFC 3339 timezone semantics.

## 3. Typed relational value record

Every non-row-identity cell in canonical projection/state material is represented as a typed record:

```json
{"type":"integer","value":"42"}
```

A SQL NULL retains the declared logical type:

```json
{"type":"integer","value":null}
```

Rules:

- `type` MUST exactly equal the column's logical type from the bound `RelationalStateManifest`;
- `value: null` is valid only when that logical column is nullable;
- no additional fields are permitted in the v0.1 value record;
- the type record is retained even though the Manifest also defines the column type. This makes canonical state bytes self-checking against the Manifest rather than relying on positional type inference alone.

The same representation is used in row keys and ordinary values. Row-key values MUST NOT be null.

## 4. Boolean

Canonical form:

```json
{"type":"boolean","value":true}
{"type":"boolean","value":false}
```

Only JSON booleans are accepted. Numeric/string truthy aliases such as `1`, `0`, `"true"`, or `"false"` are not canonical relational boolean values.

## 5. Integer

### Portability range

The v0.1 common profile supports signed exact integers with **1 through 65 decimal digits of magnitude**. This can be represented exactly by both target reference engines, including through exact numeric storage when the backend's native integer width is insufficient.

### Lexical form

Canonical `value` is a JSON string matching:

```text
0
or
-?[1-9][0-9]{0,64}
```

Additional semantic limit: the count of decimal digits excluding the sign MUST be <= 65.

Forbidden:

- leading `+`;
- leading zeroes except the single value `0`;
- `-0`;
- exponent notation;
- decimal point;
- surrounding whitespace.

Examples:

```json
{"type":"integer","value":"0"}
{"type":"integer","value":"-7"}
{"type":"integer","value":"123456789012345678901234567890"}
```

## 6. Decimal

### Schema parameters

A `decimal` logical column declares:

- `precision`: integer 1..65;
- `scale`: integer 0..30;
- `scale <= precision`.

This is the intentionally conservative PostgreSQL/MySQL portability intersection for the initial reference target.

### Lexical form

Canonical values use fixed-point notation with exactly the declared number of fractional digits.

For `scale = 0`:

```text
0
or
-?[1-9][0-9]*
```

For `scale > 0`:

```text
[-]integer-part "." exactly-scale-digits
```

Rules:

- exactly `scale` digits MUST follow the decimal point;
- exponent notation is forbidden;
- leading `+` is forbidden;
- integer-part leading zeroes are forbidden except the single `0` before the decimal point;
- negative zero is normalized to the positive zero lexical form at the declared scale;
- total digits excluding sign and decimal point MUST fit the declared precision;
- adapters MUST fail compatibility or extraction rather than round/truncate a value to make it fit the portable declaration.

Examples for `precision=8, scale=2`:

```json
{"type":"decimal","value":"0.00"}
{"type":"decimal","value":"12.30"}
{"type":"decimal","value":"-999.01"}
```

`12.3`, `12.300`, `+12.30`, `1.23e1`, and `-0.00` are non-canonical.

## 7. Text

Canonical text value:

```json
{"type":"text","value":"..."}
```

Rules:

- value is a valid Unicode scalar sequence;
- invalid lone surrogate data is rejected;
- Unicode normalization MUST NOT be applied by the canonicalization layer;
- code-point sequence identity is preserved exactly;
- database collation equality does not alter AVP text identity.

Therefore canonically distinct strings remain distinct even if a backend collation compares them as equal.

The relational manifest is responsible for ensuring the selected backend schema can store/retrieve the selected text state losslessly. Backend collation remains implementation/schema evidence and MUST NOT drive canonical row ordering.

## 8. Binary

Canonical form:

```json
{"type":"binary","value":"AQID_w"}
```

Rules:

- RFC 4648 base64url alphabet (`A-Z a-z 0-9 - _`);
- no `=` padding in canonical AVP output;
- no whitespace or line breaks;
- unused pad bits MUST be zero;
- decoder MUST reject non-canonical alternate encodings;
- canonical comparison is over decoded octets; serialization is their unique canonical base64url spelling.

## 9. Date

Canonical form:

```text
YYYY-MM-DD
```

Portable v0.1 range:

```text
1000-01-01 through 9999-12-31
```

Rules:

- exactly four year digits;
- proleptic Gregorian calendar interpretation for the portable range;
- valid month/day combinations only;
- no timezone, era, ordinal-date, or week-date syntax.

The lower bound is a deliberate common reference-engine portability boundary, not a general AVP statement about all relational databases.

## 10. Temporal precision

`time-local`, `timestamp-local`, and `timestamp-instant` columns declare:

```text
fractionalSecondPrecision: 0..6
```

For precision `0`, no decimal point/fraction is emitted.

For precision `p > 0`, exactly `p` fractional digits are emitted, including trailing zeroes.

Adapters MUST NOT silently round or truncate values to the manifest precision during projection. If the backend state cannot be represented losslessly under the bound logical column declaration, extraction fails closed.

The 0..6 range is the common target supported by PostgreSQL and MySQL/InnoDB temporal types.

## 11. time-local

Canonical form:

```text
HH:MM:SS
HH:MM:SS.fff...
```

Rules:

- hour `00..23`;
- minute `00..59`;
- second `00..59`;
- fractional part follows the manifest precision rule;
- no timezone offset;
- no `24:00:00`;
- no negative or elapsed-time values.

This is a local **time of day**, not MySQL's broader elapsed-duration interpretation of `TIME`.

## 12. timestamp-local

Canonical form:

```text
YYYY-MM-DDTHH:MM:SS
YYYY-MM-DDTHH:MM:SS.fff...
```

Rules combine the `date` and `time-local` rules.

Portable range is `1000-01-01T00:00:00` through `9999-12-31T23:59:59.999999`, subject to declared precision and actual calendar validity.

No offset or timezone identifier is permitted. A backend timezone/session setting MUST NOT reinterpret the logical value during extraction.

## 13. timestamp-instant

Canonical form:

```text
YYYY-MM-DDTHH:MM:SSZ
YYYY-MM-DDTHH:MM:SS.fff...Z
```

Rules:

- normalized to UTC before serialization;
- literal uppercase `T` and `Z`;
- no numeric offset in canonical output;
- second `00..59`; leap-second `60` is excluded in v0.1;
- fractional part follows manifest precision;
- portable normalized UTC date range is 1000 through 9999.

An adapter may map this logical type to PostgreSQL `timestamptz`, MySQL `DATETIME` maintained as UTC, or another exact mechanism. It MUST NOT rely on an implicit process/session timezone to define canonical identity.

## 14. UUID

Canonical form:

```json
{"type":"uuid","value":"550e8400-e29b-41d4-a716-446655440000"}
```

Rules:

- exactly RFC 9562 hex-and-dash `8-4-4-4-12` text layout;
- hexadecimal alphabetic digits canonicalized to lowercase;
- no braces, URN prefix, compact 32-hex form, or surrounding whitespace.

All UUID versions permitted by RFC 9562 may be represented; the relational profile does not reinterpret version-specific semantics.

## 15. Canonical JSON bytes

After values are converted to the closed relational data model, the whole Manifest, Projection, or StateImage JSON value is serialized using RFC 8785 JCS.

Consequences:

- object member order in source JSON is irrelevant;
- array order remains semantically significant and must be established by the relational profile before JCS serialization;
- no duplicate member names;
- exact UTF-8 output bytes are deterministic;
- no separate AVP JSON canonicalizer is invented.

Because numeric relational values are strings, JCS's IEEE-754 JSON-number constraint cannot round relational integer/decimal state.

## 16. Artifact media types and identity

The v0.1 design reserves these semantic roles:

```text
application/vnd.avp.relational-state-manifest+json
application/vnd.avp.relational-state-image+json
application/vnd.avp.relational-projection+json
```

The eventual schema will carry an explicit AVP `apiVersion`/`kind`, so media type alone never substitutes for schema/profile identity.

Exact JCS bytes are published/stored under the existing AVP Artifact identity rule:

```text
Artifact identity = sha256(exact retained bytes)
```

No separate Fabric/relational content-address algorithm is introduced.

## 17. RelationalStateManifest identity

`RelationalStateManifest` describes interpretation semantics only:

- profile/revision;
- logical relation/column definitions;
- scalar parameters;
- row-key definitions;
- authoritative state surface;
- named projection definitions;
- canonical representation version.

The Manifest **MUST NOT contain a baseline StateImage ArtifactRef**.

Its identity is the ArtifactRef digest of its exact JCS bytes. That digest is the portable logical relational-schema/profile identity for the bound resource.

Backend DDL/migration/catalog evidence may be separately retained as Artifacts but is not the Manifest identity.

## 18. RelationalStateImage identity

`RelationalStateImage` contains:

- `apiVersion` / `kind`;
- `manifestDigest` — exactly the bound Manifest Artifact digest;
- the complete canonical authoritative state surface.

It does **not** contain its own digest.

Its Artifact digest is simultaneously:

1. exact-byte Artifact identity when the image is retained; and
2. the full authoritative relational state digest for the v0.1 full-state projection.

This avoids a self-digest field and aligns Artifact identity with Environment state identity for the exact canonical full-state representation.

A StateImage whose `manifestDigest` does not equal the currently bound Manifest fails closed.

## 19. Baseline binding without an identity cycle

For a `state.relational` Fabric resource, the existing closed `EnvironmentResource.identityArtifacts` array binds profile identity material by **media type**, never by array position.

The v0.1 profile direction requires exactly:

- one `RelationalStateManifest` ArtifactRef; and
- one baseline `RelationalStateImage` ArtifactRef.

The baseline image contains the Manifest digest. The Manifest does not contain the baseline image digest.

Therefore identity is acyclic:

```text
EnvironmentResource
  -> Manifest ArtifactRef
  -> Baseline StateImage ArtifactRef
       -> manifestDigest
```

not:

```text
Manifest -> Baseline -> Manifest -> ...
```

The `identityArtifacts` array order has no semantic meaning for these roles. Role is determined from the unique expected media type plus schema validation.

A missing, duplicate, wrong-media-type, or manifest-mismatched required Artifact fails compatibility before resource provisioning side effects.

## 20. Runtime snapshot binding

A runtime relational snapshot does **not** mutate the immutable `EnvironmentResource.identityArtifacts` set.

Snapshot operation flow:

```text
bound Manifest
  -> consistent full-state projection
  -> RelationalStateImage exact JCS bytes
  -> ArtifactRef
  -> Environment/resource-owned SnapshotRef binding
```

The existing Environment SnapshotRef remains the authority for:

- owning Environment instance;
- resource/snapshot ownership;
- stale/foreign reference rejection;
- represented authoritative state identity.

The relational snapshot binds that SnapshotRef to the generated StateImage ArtifactRef as profile evidence. A PostgreSQL transaction snapshot token, MySQL read view, physical backup location, or dump filename remains adapter-private diagnostic/mechanism information.

Cross-Environment import of this runtime SnapshotRef remains outside v0.1.

## 21. Named projection identity

A named evaluator projection uses the same typed values and JCS rules but a distinct `RelationalProjection` structure containing:

- `manifestDigest`;
- `projectionId`;
- the selected canonical relation/column/row content.

Its Environment state digest is SHA-256 over the exact canonical projection bytes.

When those bytes are retained as an Artifact, the Artifact digest equals that projection state digest. If projection bytes are not retained, the state digest remains content identity under Environment `AVP-ENVIRONMENT-006`; Artifact identity is claimed only for bytes actually retained/published.

The Environment projection identity remains `(projection identifier, state digest)`; the relational profile does not replace that rule.

## 22. RS-BR-001 closure evidence

RS-BR-001 asked for exact language-neutral scalar lexical rules, especially decimal and temporal precision.

Closure decision:

- typed value record fixed;
- integer lexical/range fixed;
- decimal precision/scale and fixed lexical form fixed;
- text normalization policy fixed;
- binary canonical encoding fixed;
- date/time/timestamp lexical shapes/ranges fixed;
- temporal precision fixed to 0..6;
- UUID lexical form fixed;
- canonical JSON algorithm fixed to RFC 8785;
- unsupported/lossy mapping remains fail-closed.

**RS-BR-001: CLOSED FOR DRAFT -> PROPOSED READINESS.**

The eventual normative specification/schema must encode these decisions before the profile can become a normative candidate.

## 23. RS-BR-002 closure evidence

RS-BR-002 asked for the exact identity relationship among Fabric `identityArtifacts`, Manifest, StateImage, Environment SnapshotRef, and Artifact identity.

Closure decision:

- Manifest and StateImage are separate Artifact types;
- Manifest has no baseline reference;
- baseline image references Manifest digest;
- Fabric `identityArtifacts` binds exactly one Manifest and one baseline image by media type;
- runtime snapshot StateImage is bound by the Environment/resource-owned SnapshotRef and does not mutate Fabric identity inputs;
- exact retained JCS bytes use existing Artifact SHA-256 identity;
- full StateImage Artifact digest doubles as the v0.1 full authoritative relational state digest;
- named Projection state digest uses the same exact-byte SHA-256 rule, with Artifact identity claimed only if those bytes are retained;
- no circular or competing content-address scheme is introduced.

**RS-BR-002: CLOSED FOR DRAFT -> PROPOSED READINESS.**

## 24. Remaining Draft blockers

Still open:

- RS-BR-003 — authoritative surface versus named projections;
- RS-BR-004 — row-key portability;
- RS-BR-005 — final observation under unsettled Subject transaction;
- RS-BR-006 — schema drift detection boundary;
- RS-BR-007 — cross-backend canonical parity fixture;
- RS-BR-008 — language-neutral TCK execution interface.

AEP-0010 remains Draft and is not ready for normative specification or database adapter implementation.
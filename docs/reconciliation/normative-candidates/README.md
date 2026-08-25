# Normative Candidate Surfaces

This directory records **active, reviewable normative candidate surfaces** whose governing AEP direction is `Accepted` but whose protocol text has not reached the released `Final` state.

The registry is governance evidence, not protocol authority. Authority continues to flow in one direction:

```text
Accepted AEP direction
    -> complete normative candidate slice
       (spec + requirement index + schema where required + draft TCK profile/cases)
    -> reference implementation
    -> release/finalization decision
    -> Final AEP + stable normative-surface promotion
```

## Why this registry exists

`docs/reconciliation/v0.1/normative-surface-matrix.json` is the closed Alpha 2 normative baseline. Its `READY` state must remain evidence about that stable closure; it must not be reinterpreted as a mutable status for every future protocol proposal.

At the same time, AVP governance explicitly permits implementation after an AEP becomes `Accepted`, while `Final` requires normative text and required conformance coverage to be merged **and released**. The repository therefore needs a fail-closed representation for complete candidate authority slices that can live on `main` before release without being mistaken for the released stable surface.

## Registration rule

An `Accepted` AEP alone is **not** a normative candidate registration.

A candidate may be added to `registry.json` only in a coherent PR that also contains all repository surfaces required by that candidate:

- one canonical `spec/<domain>/requirement-index.yaml` with status `draft-normative-candidate`;
- the referenced normative specification files;
- one matching TCK conformance profile with `metadata.status: draft`;
- all mandatory/conditional TCK cases required by the requirement index and global traceability rules;
- every new root protocol schema owned by the candidate, when serialized protocol resources require schemas.

The existing global traceability and TCK registry validators remain authoritative for requirement-to-case completeness. The candidate mechanism does not permit `MUST`/`MUST_NOT` requirements to enter the repository without executable conformance coverage.

## Candidate record

Each registry entry contains:

- `domain` — canonical `spec/<domain>` owner;
- `lineage` — an `accepted-aep` path whose file actually declares `Status: Accepted`;
- `spec` — non-empty list of normative specification files inside the domain;
- `requirement_index` — canonical `spec/<domain>/requirement-index.yaml`;
- `profile` — the matching draft TCK profile name;
- `owned_schemas` — new root schemas introduced and owned by this candidate; may be empty when the candidate reuses stable schemas only.

A candidate may reference an already stable schema from its requirement index without claiming ownership of that schema. A new candidate-owned schema must be referenced by at least one requirement in that candidate.

## Fail-closed invariants

The validator requires the union of:

1. the stable Alpha 2 matrix; and
2. all registered active candidates

to equal the repository's complete inventory of requirement-index domains, root protocol schemas, and TCK profiles.

Therefore an unregistered new spec domain, schema, or profile fails validation. A candidate also fails validation when:

- its AEP is Draft, Proposed, Final, or otherwise not exactly Accepted;
- its requirement index is not `draft-normative-candidate`;
- its TCK profile is not `draft`;
- its domain/profile/schema overlaps stable ownership or another candidate;
- its declared files are missing, non-canonical, or escape repository paths;
- a new owned schema has no candidate requirement owner;
- candidate metadata attempts to make the stable matrix absorb an unfinished surface.

`Final` is intentionally rejected as an active-candidate lineage. Finalization requires an explicit promotion change, not a silent status edit.

## Promotion to the stable surface

Candidate promotion is a separate governed action. It must not happen merely because CI is green or an implementation exists.

At finalization/release time, one coherent promotion change must:

1. satisfy the repository's Final/release governance requirements;
2. change the AEP to `Final` only when the lifecycle definition is actually met;
3. change the requirement index from `draft-normative-candidate` to `normative`;
4. change the TCK profile from `draft` to `active` where applicable;
5. move the domain and candidate-owned schemas into the stable normative-surface matrix with Final/reconciliation lineage;
6. remove the candidate registry entry;
7. pass the same global spec traceability, TCK registry, schema, package, and release-validation gates.

No backend implementation, release version, tag, package publication, signing, or attestation is authorized by this registry itself.

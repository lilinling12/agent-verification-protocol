# AVP Relational State Manifest Integrity v0.1

Status: draft normative candidate

This companion specification closes cross-reference constraints that are semantic rather than expressible as simple closed-object JSON Schema shape constraints. It is part of the `avp-relational-state-v0.1` candidate and composes with `spec/relational/relational-state-contract.md`.

Normative keywords MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are conformance requirement terms.

<a id="avp-relational-017"></a>
### AVP-RELATIONAL-017 — Manifest identifiers and references are unambiguous

A `RelationalStateManifest` MUST define an unambiguous logical graph before the resource is provisioned or any Subject-requested relational side effect is admitted.

The following constraints are mandatory:

1. `relationId` values MUST be unique within the Manifest.
2. `columnId` values MUST be unique within each relation.
3. Every `rowKey` entry MUST reference a column declared by that same relation, and the row-key set MUST contain no duplicate column identifier.
4. `projectionId` values MUST be unique within the Manifest.
5. Within one projection, a logical relation MUST NOT appear more than once.
6. Every projection relation reference MUST resolve to exactly one Manifest relation.
7. Every projected column identifier MUST resolve to a column of the referenced relation, and projected column identifiers for that relation MUST contain no duplicates.
8. Every projection MUST include all logical row-key columns of each selected relation.

An implementation MUST reject a Manifest violating any of these constraints before the invalid Manifest can establish a ready relational resource or authorize a Subject relational side effect.

An implementation MUST NOT resolve ambiguity by taking the first matching relation/projection, silently dropping duplicate identifiers, inventing a backend physical identifier, or using backend catalog order as a tie-breaker.

JSON Schema validation remains necessary for serialized shape and lexical constraints, but schema shape validation alone is not sufficient evidence for this requirement. The TCK MUST execute semantic cross-reference validation using metadata-identical valid and invalid Manifest structures.

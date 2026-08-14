# AVP Scenario Contract v0.1

Status: draft-normative-candidate

Profile: `avp-scenario-v0.1`

This specification defines the language-neutral contract between unresolved ScenarioTemplate input and the materialized ScenarioInstance executed by an AVP Episode.

It does not standardize one benchmark authoring language, one compiler implementation, or one runtime data structure.

## Terminology

### ScenarioTemplate

An unresolved scenario description that MAY contain parameters, generators, symbolic/external references, hidden evaluator material, and other authoring-time constructs.

A ScenarioTemplate is not the execution contract of an Episode until required compilation/materialization semantics have completed.

### ScenarioInstance

The materialized scenario contract used by an Episode. A ScenarioInstance contains the execution-relevant values and identities needed by the selected profile and has a stable content identity.

### Compilation inputs

Explicit inputs that can affect materialization, such as parameter overrides, seeds, profile selection, and externally resolved reference identities.

### Subject projection

The subset of one ScenarioInstance that a particular Subject actor is authorized to observe before or during execution through the Scenario boundary.

### Provenance

Non-semantic information about how an instance was produced, such as compiler identity, source-template identity, build metadata, or audit annotations. Provenance MUST NOT change Episode execution semantics.

## Normative requirements

<a id="avp-scenario-001"></a>
### AVP-SCENARIO-001 — Template / instance separation

An implementation MUST distinguish unresolved ScenarioTemplate input from the ScenarioInstance consumed by Episode execution.

An Episode MUST NOT begin Subject execution using a template that still contains unresolved required execution inputs.

The distinction MAY be represented by different serialized `kind` values, different types, or an equivalent implementation mechanism.

<a id="avp-scenario-002"></a>
### AVP-SCENARIO-002 — Deterministic materialization

For a selected compilation profile, equivalent compilation inputs MUST produce semantically equivalent ScenarioInstance content and the same ScenarioInstance identity.

Compilation inputs that can affect execution semantics MUST participate either directly in the materialized semantic content or through an identity binding represented in that semantic content.

Implementations MUST NOT depend on ambient nondeterminism that is absent from the declared compilation inputs.

Equivalent semantic output MUST NOT receive a different identity merely because compiler implementation identity, build metadata, template formatting, or other non-semantic provenance differs.

This requirement does not mandate one pseudorandom generator, internal seed partitioning scheme, or compiler implementation.

<a id="avp-scenario-003"></a>
### AVP-SCENARIO-003 — Fail-closed unresolved inputs

If a required parameter, placeholder, generator result, or reference cannot be resolved according to the selected compilation policy, compilation MUST fail before Episode execution.

An implementation MUST NOT silently substitute an implementation-defined value for an unresolved required input.

Optional authoring constructs MAY remain absent when the authoring contract explicitly defines them as optional.

<a id="avp-scenario-004"></a>
### AVP-SCENARIO-004 — ScenarioInstance identity

A serialized ScenarioInstance conforming to `avp-scenario-v0.1` MUST contain `instanceDigest`.

The ScenarioInstance identity preimage is the complete serialized ScenarioInstance after removing the top-level `instanceDigest` field and the optional top-level `provenance` field. No other top-level or nested field is excluded from the identity preimage.

The identity preimage MUST be representable as I-JSON and MUST be canonicalized using the JSON Canonicalization Scheme (JCS) defined by RFC 8785. The SHA-256 digest MUST be calculated over the UTF-8 bytes emitted by JCS and serialized as `sha256:` followed by 64 lowercase hexadecimal characters.

Consequently:

1. object member ordering and insignificant JSON whitespace MUST NOT affect identity;
2. array ordering remains semantically significant;
3. any field outside `provenance` that changes canonical bytes changes the content identity except for a cryptographic hash collision;
4. `provenance` MUST NOT affect Episode execution semantics;
5. if a fact recorded as provenance affects execution semantics, that fact MUST also be represented in identity-bound semantic content outside `provenance`.

This canonicalization contract is language-neutral. An implementation MUST NOT substitute language-specific object serialization for the RFC 8785 preimage.

Normative external reference: RFC 8785, JSON Canonicalization Scheme (JCS).

<a id="avp-scenario-005"></a>
### AVP-SCENARIO-005 — Immutable execution semantics

After Episode execution begins, the identity-bound materialized semantics represented by a ScenarioInstance MUST NOT change for that Episode.

Implementations MAY enforce this with immutable data structures, defensive copies, content-addressed storage, or equivalent mechanisms.

Mutation of environment state during execution does not mutate the ScenarioInstance.

Changing non-semantic `provenance` does not change ScenarioInstance identity, but such provenance MUST remain audit-honest and MUST NOT be consulted as hidden execution configuration.

<a id="avp-scenario-006"></a>
### AVP-SCENARIO-006 — Subject projection confidentiality

A Subject projection MUST contain only material authorized for that Subject actor.

Unless another normative contract explicitly makes a field observable, the projection MUST exclude evaluator-only material including:

- success criteria or answer keys;
- invariants used only by verification;
- inactive or future hidden fault schedules and evaluator-only fault parameters;
- private graders, Oracle configuration, or equivalent evaluator logic;
- evaluator-only security material and credentials;
- contamination controls, private validity rules, or equivalent hidden benchmark metadata.

The projection MAY include public task instructions, public metadata, the Subject actor description, Subject capabilities, and public budgets when those fields are declared observable.

A field being present in the evaluator's ScenarioInstance does not by itself authorize disclosure to the Subject.

<a id="avp-scenario-007"></a>
### AVP-SCENARIO-007 — Actor capability projection

Capabilities exposed to a Subject actor MUST be derived from the materialized ScenarioInstance or an equivalent compiled authorization policy bound to that instance.

A Subject MUST NOT gain an undeclared evaluator or control-plane capability because an implementation offers that capability internally.

This requirement composes with AVP Security capability fail-closed semantics.

<a id="avp-scenario-008"></a>
### AVP-SCENARIO-008 — External reference identity binding

When an external reference affects execution semantics, the materialized ScenarioInstance MUST bind an identity for the resolved reference according to the selected compilation profile.

A profile MAY permit symbolic/version identity, content identity, or another explicitly defined identity level.

A profile that requires content-backed/strict reference identity MUST fail compilation when that identity cannot be established.

An implementation MAY expose reference bindings in a dedicated field, materialize referenced content directly, or use another schema-valid identity-bound representation. Resolver implementation classes and transport mechanisms are not standardized by AVP Scenario v0.1.

<a id="avp-scenario-009"></a>
### AVP-SCENARIO-009 — Compilation failure separation

Scenario validation or compilation failure MUST NOT be reported as Agent task failure.

If an Episode has not begun, the failure remains a pre-execution configuration/infrastructure failure.

If a surrounding orchestration system creates an Episode record before compilation completes, it MUST classify the resulting invalidity separately from a Subject task verdict.

## Machine-readable contracts

`schemas/scenario-template.schema.json` defines the v0.1 ScenarioTemplate authoring/input shape used by this profile.

`schemas/scenario-instance.schema.json` defines the serialized ScenarioInstance shape, including the `instanceDigest` identity field and optional non-semantic `provenance`.

The historical `schemas/scenario.schema.json` filename remains a compatibility surface for the current reference package during Alpha reconciliation. Its existence does not override the Template/Instance distinction defined here.

## ScenarioTemplate authoring boundary

The repository MAY provide YAML/JSON schemas and authoring utilities for ScenarioTemplate documents. Authoring conveniences are not automatically normative execution semantics.

An AVS or benchmark DSL MAY introduce richer authoring constructs provided that they compile into a ScenarioInstance satisfying this specification and the selected conformance profile.

## ScenarioInstance provenance

An implementation MAY attach non-semantic `provenance` such as compiler identity, template identity, source location, build metadata, generator audit records, or diagnostic metadata.

AVP Scenario v0.1 does not require:

- the reference compiler name `avp-reference-avs`;
- a fixed compiler version field format;
- a fixed eight-stream seed bundle;
- Python generator registry/version fields;
- Python resolver class or record shapes.

Execution-relevant material MUST NOT be hidden solely in `provenance`, because `provenance` is excluded from `instanceDigest`.

## Security composition

AVP Security may impose stronger requirements on Subject execution context, hidden evaluator material, and future fault secrecy.

Conformance with Scenario projection requirements does not by itself prove process, network, tenant, credential-context, or sandbox isolation.

## Conformance boundary

`avp-scenario-v0.1` conformance tests the nine requirements above through implementation-independent vectors.

TCK cases MUST validate observable semantics and MUST NOT require Python-specific compiler metadata, internal seed stream names, mapping-proxy behavior, tuple conversion, or implementation-private resolver APIs.

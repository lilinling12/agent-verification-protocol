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

## Normative requirements

<a id="avp-scenario-001"></a>
### AVP-SCENARIO-001 — Template / instance separation

An implementation MUST distinguish unresolved ScenarioTemplate input from the ScenarioInstance consumed by Episode execution.

An Episode MUST NOT begin Subject execution using a template that still contains unresolved required execution inputs.

The distinction MAY be represented by different serialized `kind` values, different types, or an equivalent implementation mechanism.

<a id="avp-scenario-002"></a>
### AVP-SCENARIO-002 — Deterministic materialization

For a selected compilation profile, equivalent compilation inputs MUST produce equivalent ScenarioInstance content identity.

Compilation inputs that can affect execution semantics MUST participate either directly in the materialized content or through an identity/provenance binding that makes the resulting instance identity change when those execution semantics change.

Implementations MUST NOT depend on ambient nondeterminism that is absent from the declared compilation inputs.

This requirement does not mandate one pseudorandom generator, internal seed partitioning scheme, or compiler implementation.

<a id="avp-scenario-003"></a>
### AVP-SCENARIO-003 — Fail-closed unresolved inputs

If a required parameter, placeholder, generator result, or reference cannot be resolved according to the selected compilation policy, compilation MUST fail before Episode execution.

An implementation MUST NOT silently substitute an implementation-defined value for an unresolved required input.

Optional authoring constructs MAY remain absent when the authoring contract explicitly defines them as optional.

<a id="avp-scenario-004"></a>
### AVP-SCENARIO-004 — ScenarioInstance identity

A ScenarioInstance MUST have a stable content identity.

The identity MUST bind all execution-relevant materialized fields except the field carrying the identity itself.

Two instances whose execution-relevant materialized semantics differ MUST NOT intentionally share the same instance identity.

AVP Scenario v0.1 does not require a particular in-memory hash API. Where the repository's canonical SHA-256 identity conventions apply, implementations SHOULD use the corresponding canonical representation defined by the applicable schema/profile rather than language-specific object serialization.

<a id="avp-scenario-005"></a>
### AVP-SCENARIO-005 — Immutable execution semantics

After Episode execution begins, the materialized semantics represented by a ScenarioInstance MUST NOT change for that Episode.

Implementations MAY enforce this with immutable data structures, defensive copies, content-addressed storage, or equivalent mechanisms.

Mutation of environment state during execution does not mutate the ScenarioInstance.

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

AVP Scenario v0.1 does not standardize one URI resolver implementation or transport.

<a id="avp-scenario-009"></a>
### AVP-SCENARIO-009 — Compilation failure separation

Scenario validation or compilation failure MUST NOT be reported as Agent task failure.

If an Episode has not begun, the failure remains a pre-execution configuration/infrastructure failure.

If a surrounding orchestration system creates an Episode record before compilation completes, it MUST classify the resulting invalidity separately from a Subject task verdict.

## ScenarioTemplate authoring boundary

The repository MAY provide YAML/JSON schemas and authoring utilities for ScenarioTemplate documents. Those authoring conveniences are not automatically normative AVP execution semantics.

An AVS or benchmark DSL MAY introduce richer authoring constructs provided that they compile into a ScenarioInstance satisfying this specification and the selected conformance profile.

## ScenarioInstance provenance

An implementation MAY attach compilation provenance such as compiler identity, template identity, resolved parameters, seed records, generator records, and reference records.

Such provenance becomes protocol-required only when another normative requirement or profile explicitly requires the corresponding interoperable fact.

In particular, AVP Scenario v0.1 does not require:

- the reference compiler name `avp-reference-avs`;
- a fixed compiler version field format;
- a fixed eight-stream seed bundle;
- Python generator registry/version fields;
- Python resolver class or record shapes.

## Security composition

AVP Security may impose stronger requirements on Subject execution context, hidden evaluator material, and future fault secrecy.

Conformance with Scenario projection requirements does not by itself prove process, network, tenant, credential-context, or sandbox isolation.

## Conformance boundary

`avp-scenario-v0.1` conformance is expected to test the nine requirements above through implementation-independent vectors.

TCK cases MUST validate observable semantics and MUST NOT require Python-specific compiler metadata, internal seed stream names, mapping-proxy behavior, tuple conversion, or implementation-private resolver APIs.

# AVP Security Boundary Contract v0.1

Status: Draft normative candidate.

This specification defines portable Subject/Evaluator trust-boundary semantics for AVP. It intentionally does **not** standardize one operating-system sandbox, container runtime, microVM, network-policy engine, secret manager, authentication protocol, or tenant-isolation mechanism.

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as BCP 14 requirement levels.

## Trust domains

The **Subject Agent Plane** is untrusted. It contains the interfaces, capabilities, observations, tool results, and execution context made available while the system under verification acts.

The **Evaluator Plane** is privileged. It may hold authoritative state projections, Oracle logic, private benchmark fixtures, answer material, evaluator credentials, contamination controls, and verification-only Evidence.

The **Control Plane** is privileged. It may own lifecycle control, snapshots, restore, fault scheduling/injection, replay, and verification orchestration.

An **AVP-provided route** is an API, tool gateway, protocol endpoint, process channel, mounted resource, injected environment value, or other access path that the AVP implementation creates or controls for Subject execution.

A **Subject execution context** is the execution environment the AVP implementation creates or manages for the Subject. It includes explicit inputs and any credentials, environment values, files, mounts, handles, endpoints, or capabilities that Subject code can access through that managed context.

## Security profile scope

`avp-security-v0.1` is a baseline verification-security profile. It requires capability-plane separation, deny-by-default capability enforcement, evaluator-secret separation, hidden-material protection, future-fault secrecy, and honest assurance declarations.

The profile does **not** by itself prove hardened process, network, tenant, or sandbox isolation. Implementations may provide those stronger properties, but they may claim them only when independently demonstrated by the relevant implementation/deployment evidence.

A shared-process reference adapter may demonstrate API-capability behavior. If Subject code in that shared process can access evaluator secrets or privileged runtime state through the language/runtime environment, that adapter cannot use API hiding alone as evidence for full `avp-security-v0.1` conformance.

## Normative requirements

### AVP-SECURITY-001 Subject/Evaluator plane separation

An AVP implementation **MUST** expose Subject execution through a capability surface that is distinct from privileged Evaluator and Control Plane surfaces. AVP-provided Subject routes **MUST NOT** expose unrestricted evaluator state projection, Oracle execution, verification, snapshot/restore, fault-control, or equivalent privileged mutable handles.

This requirement defines a capability boundary. It does not imply process, network, tenant, or sandbox isolation unless those properties are separately declared and demonstrated.

### AVP-SECURITY-002 Undeclared capability access fails closed

When a Subject requests a capability through an AVP-provided route, the implementation **MUST** enforce the Scenario's Subject capability projection (or an equivalent compiled authorization policy). A capability that is not granted to the Subject **MUST** be denied before the requested side effect occurs.

Denial **MUST NOT** silently fall back to a broader environment, evaluator, control, or direct upstream interface. Discovery/catalog surfaces exposed to the Subject **MUST NOT** advertise evaluator-only capabilities as Subject capabilities.

### AVP-SECURITY-003 Evaluator secrets do not enter Subject execution context

Evaluator credentials, signing material, Oracle secrets, private benchmark credentials, answer-key secrets, and equivalent evaluator-only authentication material **MUST NOT** be inherited, mounted, injected, serialized, or otherwise made available in the Subject execution context created or managed by the AVP implementation.

An implementation that reuses an execution context in which untrusted Subject code can read evaluator-only secrets **MUST NOT** claim this requirement as satisfied.

This requirement does not require a specific secret-management product or identity protocol.

### AVP-SECURITY-004 Hidden evaluator material is not disclosed

Evaluator-confidential or secret verification material **MUST NOT** be disclosed through Subject observations, Subject tool results, Subject-visible events, public artifact locators, or other AVP-provided Subject routes unless the Scenario explicitly promotes that material into the Subject-visible contract.

Protected material includes answer keys, hidden verification conditions, private fixtures, undeclared snapshots, Oracle internals, contamination canaries, and equivalent evaluator-only artifacts.

A digest or opaque identity MAY be exposed when required by another AVP contract only if that identity does not itself disclose the protected content and does not grant retrieval authority.

### AVP-SECURITY-005 Future fault schedules remain evaluator-private

Future fault schedules, inactive perturbation parameters, and evaluator-only fault-control metadata **MUST NOT** be exposed to the Subject before the Scenario defines that information as observable.

When a fault activates, the Subject MAY observe the effects or activation metadata that the Scenario/environment contract makes observable. Observing an activated fault does not authorize disclosure of remaining future faults or hidden schedule parameters.

### AVP-SECURITY-006 Security assurance claims are explicit and non-inflating

An implementation that reports AVP Security assurance **MUST** provide a machine-readable declaration conforming to `schemas/security-assurance.schema.json` or an equivalent binding with the same semantics.

Each isolation dimension **MUST** be reported independently. A property **MUST NOT** be marked `verified` solely because a weaker property passed. In particular, API-capability separation **MUST NOT** be represented as proof of process, network, tenant, or sandbox isolation.

A full `avp-security-v0.1` conformance claim requires successful conformance evidence for all mandatory requirements in the profile. An assurance declaration may still truthfully report weaker implementation properties when the full profile is not yet conformant.

## Security Assurance resource

The portable `SecurityAssurance` resource records what isolation dimensions an implementation claims to have demonstrated. AVP v0.1 defines these dimensions:

- `apiCapability`: Subject-facing APIs/capabilities exclude privileged evaluator/control operations;
- `credentialContext`: evaluator-only credentials/secrets are absent from the managed Subject execution context;
- `process`: adversarial process/address-space isolation;
- `network`: network-route isolation between Subject and privileged evaluator/control endpoints;
- `tenant`: cross-tenant isolation;
- `sandbox`: hardened code-execution sandboxing beyond ordinary API separation.

Each value is either `verified` or `not-claimed`. `verified` is an assurance claim and therefore requires implementation/deployment evidence appropriate to that dimension. `not-claimed` is not a failure by itself unless the selected conformance profile requires that dimension.

For `avp-security-v0.1`, `apiCapability` and `credentialContext` must be demonstrated by the mandatory TCK. The profile does not require `process`, `network`, `tenant`, or `sandbox` to be `verified`, but it requires those dimensions not to be overstated.

## Conformance boundary

The Security TCK tests observable behavior through an implementation adapter. It does not perform unsafe public-network scanning and does not require exploit techniques against production infrastructure.

Conformance evidence MUST distinguish protocol/API behavior from deployment-specific isolation. A reference in-process adapter may be useful evidence for `AVP-SECURITY-001`, `AVP-SECURITY-002`, `AVP-SECURITY-004`, `AVP-SECURITY-005`, and assurance honesty; it is not sufficient evidence for `AVP-SECURITY-003` when the Subject shares access to evaluator secrets in the same execution context.

## Relationship to existing standards

AVP intentionally delegates generic security mechanisms to existing ecosystems. Deployments may use OAuth/OIDC, mTLS, workload identity, secret managers, operating-system controls, containers, microVMs, WASM sandboxes, network policy, OCI artifacts, or other mechanisms. AVP standardizes the verification-specific trust outcome that must remain true across those choices.

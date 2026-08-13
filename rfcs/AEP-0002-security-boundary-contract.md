# AEP-0002 — Security Boundary Contract v0.1

- Status: Proposed
- Authors: AVP maintainers
- Created: 2026-08-13
- Target AVP version: 0.1

## Problem

AVP separates an untrusted Subject Agent Plane from privileged Evaluator and Control Planes. The historical threat model identifies evaluator credentials, hidden state, Oracle logic, benchmark holdout data, snapshots, production traces, and artifact registry identity as protected assets.

The existing reference runtime demonstrates API-plane separation through a narrow Subject gateway. It must not claim hardened process, network, tenant, or sandbox isolation from an in-process implementation.

## Motivation / interoperability case

Independent AVP implementations need a shared security vocabulary for observable verification boundaries:

- what capabilities a Subject may receive;
- what privileged evaluator material must never cross the boundary;
- what a conformance result actually proves.

This AEP standardizes observable security semantics rather than one sandbox technology.

## Existing standards analysis

AVP does not define operating-system sandbox primitives, network policy engines, container formats, secret managers, or identity protocols. Deployments MAY use containers, microVMs, WebAssembly, isolated services, OAuth/OIDC, mTLS, or other mechanisms.

The protocol requirement is the resulting trust boundary.

## Proposed semantics

### AVP-SECURITY-001 Plane separation

A conforming implementation MUST represent Subject Agent capabilities separately from privileged Evaluator capabilities. Subject execution MUST NOT receive unrestricted evaluator interfaces.

### AVP-SECURITY-002 Capability fail-closed

A Subject invocation MUST fail closed when requesting a capability not granted by the Scenario capability projection. Hidden evaluator APIs MUST NOT become discoverable Subject capabilities.

### AVP-SECURITY-003 Credential separation

Evaluator credentials, signing material, Oracle secrets, and private benchmark secrets MUST NOT be inherited by the Subject execution context.

### AVP-SECURITY-004 Hidden material protection

Hidden evaluator artifacts, answer keys, private fixtures, and non-declared snapshots MUST NOT be exposed through Subject observation, tool results, or public artifact references.

### AVP-SECURITY-005 Fault secrecy

Future fault schedules and inactive evaluator-only perturbation metadata MUST remain unavailable to the Subject until the Scenario explicitly makes an activation observable.

### AVP-SECURITY-006 Assurance honesty

A Security conformance result MUST identify the isolation layer it proves. API capability separation MUST NOT be represented as process, network, tenant, or sandbox isolation.

## Protocol/schema changes

This AEP introduces the AVP Security profile contract and TCK mapping. It intentionally does not introduce a generic security token schema or sandbox API.

## Security considerations

This AEP defines the security boundary. Implementations remain responsible for selecting appropriate deployment isolation for their threat model.

## Conformance tests

Initial mandatory TCK:

- Subject cannot access evaluator-only capability;
- evaluator credentials are absent from Subject context;
- hidden artifact references are rejected;
- inactive future faults are unavailable;
- capability claims do not overstate isolation level.

## Reference implementation

The Python reference runtime demonstrates API-plane separation through SubjectSession. It does not claim hardened multi-tenant sandbox security.

## Alternatives

### Standardize one sandbox technology

Rejected. AVP requires interoperable semantics, not one deployment mechanism.

### Treat API separation as full sandbox isolation

Rejected. This would create false security claims.

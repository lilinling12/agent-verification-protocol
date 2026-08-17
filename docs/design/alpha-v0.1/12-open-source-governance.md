# 12 Open-Source Governance & Standardization Strategy

> Status: Governance Draft v0.1  
> Goal: maximize AVP adoption while preventing the commercial platform from becoming a proprietary pseudo-standard.

## 1. Thesis

A standard cannot credibly mean:

> “whatever our SaaS currently implements.”

AVP should be designed so that:

- the specification is openly readable;
- reference schemas are open;
- conformance tests are open;
- multiple implementations are possible;
- normative changes use a public process;
- commercial differentiation happens above/below protocol semantics, not by secretly changing the protocol.

---

# 2. Project Split

Recommended independent open-source project:

```text
agent-verification-protocol/
├── spec/
├── schemas/
├── openapi/
├── conformance/
├── examples/
├── sdk/
├── adapters/
├── rfcs/
├── governance/
└── LICENSE
```

Commercial product repository remains separate.

---

# 3. Open vs Commercial Boundary

## Open

Must remain open to build ecosystem trust:

```text
AVP specification
AVS specification
event schemas
OpenAPI binding
TCK/conformance
reference local runtime
SDKs
MCP/A2A/OTel adapters
public benchmark adapters
example Oracles
```

## Commercial

Reasonable proprietary differentiation:

```text
large-scale Environment Fabric
managed browser/microVM fleet
snapshot optimization
private enterprise connectors
Production Miner
Failure Knowledge Graph
counterfactual experiment planner
enterprise governance
hosted benchmark network
compliance reporting
```

The protocol cannot require proprietary services for conformance.

---

# 4. License

Recommended:

```text
specification text: Apache-2.0 compatible or CC-BY-4.0 style
code/schemas/TCK: Apache-2.0
```

A legal review is required before launch.

Avoid a license that prevents competing conformant implementations; that would undermine standard adoption.

---

# 5. Normative vs Informative Content

Every spec section should be tagged conceptually:

```text
Normative
Informative
Example
Implementation Note
Security Consideration
```

Only Normative text creates conformance requirements.

---

# 6. Requirement IDs

Every normative requirement receives a stable identifier.

Example:

```text
AVP-CORE-R001
AVP-SEC-R014
AVP-SNAPSHOT-R008
```

This enables:

```text
Requirement
→ Conformance Test
→ Implementation Evidence
```

---

# 7. Change Process

Use an open proposal process:

```text
AVP Enhancement Proposal (AEP)
```

Lifecycle:

```text
Draft
→ Discussion
→ Accepted / Rejected
→ Implemented
→ Included in Version
```

AEP includes:

```text
problem
motivation
backward compatibility
security
alternatives
spec changes
schema changes
TCK changes
reference implementation status
```

---

# 8. Release Model

Protocol releases:

```text
0.x experimental
1.0 stable interoperability baseline
```

Post-1.0:

- minimum deprecation window;
- explicit migration guide;
- machine-readable schema diffs;
- conformance-suite compatibility statement.

MCP's move toward explicit deprecation/version governance is a useful model for mature protocol evolution.

---

# 9. Compatibility Policy

## Patch

No semantic breaking changes.

## Minor

Backward-compatible additions.

## Major

May break semantics.

A new required field in a stable core resource is normally a major change unless a negotiation mechanism preserves old peers.

---

# 10. Extension Registry

Experimental innovation should occur through namespaced extensions before core inclusion.

Registry fields:

```text
extension id
owner
status
spec URL
schema
security considerations
implementations
```

Promotion to core requires:

- more than one implementation;
- production evidence;
- conformance tests;
- no major overlap conflict.

---

# 11. Working Groups

Initial WGs:

## WG Protocol

Core Episode/Environment/Verification semantics.

## WG Scenarios

AVS DSL, generators, benchmark packaging.

## WG Telemetry

OpenTelemetry alignment and event semantics.

## WG Security

Plane isolation, contamination, adversarial tests.

## WG Reliability

Statistical reporting and experiment design.

## WG Conformance

TCK and compatibility.

Working groups publish minutes/decisions.

---

# 12. Maintainer Structure

Early phase:

```text
Maintainers
+ Reviewers
+ Contributors
```

Later:

```text
Technical Steering Committee
```

No single commercial roadmap owner should be able to unilaterally redefine stable protocol semantics after external adoption.

---

# 13. Decision Principles

When considering a new core feature, ask:

1. Is this required for interoperability?
2. Is this verification-specific?
3. Is an existing standard already responsible?
4. Can it remain an extension?
5. Do two independent implementations need it?
6. Can it be conformance-tested?
7. Does it introduce Agent/evaluator leakage risk?

---

# 14. Existing-Standard First

Before adding core semantics:

```text
Agent↔Tool       → inspect MCP
Agent↔Agent      → inspect A2A
Trace context    → inspect OpenTelemetry/W3C
Event transport  → inspect CloudEvents
Auth             → inspect OAuth/OIDC/mTLS
Artifact format  → inspect OCI
Schema           → inspect JSON Schema
```

AVP only standardizes what remains verification-specific.

---

# 15. OpenTelemetry Upstream Policy

Telemetry semantics that become broadly generic should be proposed upstream rather than forever duplicated under `avp.*`.

AVP can incubate experimental attributes.

Promotion criteria:

```text
stable semantics
multiple implementations
significant usage
clear mapping
```

---

# 16. MCP / A2A Interop Policy

AVP adapters should track stable released protocol versions.

Do not freeze assumptions around an old MCP session model or pre-1.0 A2A semantics.

The current MCP protocol is stateless at its core and A2A has reached 1.0; AVP should version adapter compatibility explicitly.

---

# 17. CUBE Strategy

Do not create a standards war.

CUBE demonstrates appetite for common benchmark/runtime interfaces.

Action:

```text
build CUBE↔AVP adapter
compare semantic overlap
open issues upstream
reuse package metadata where practical
```

If the communities converge, prefer compatibility or joint primitives.

---

# 18. Benchmark IP and Licensing

Public benchmark adapters must respect upstream licenses.

AVP registry stores:

```text
adapter
metadata
execution glue
```

and may reference upstream datasets rather than redistribute restricted content.

---

# 19. Security Disclosure

Project must publish:

```text
SECURITY.md
private disclosure channel
response policy
supported versions
```

Security issues include:

- evaluator secret leakage;
- sandbox escape;
- artifact cross-tenant access;
- conformance test unsafe scanning;
- benchmark answer leakage.

---

# 20. Threat Model Registry

Maintain versioned threat-model documents for:

```text
subject Agent
malicious MCP server
malicious content
malicious benchmark
malicious Judge
malicious tenant
compromised runtime
```

Security assumptions must be explicit.

---

# 21. Standard Maturity Levels

## Experimental

Single implementation acceptable.

## Candidate

- reference implementation;
- TCK;
- at least one external implementation/adapter.

## Stable

- two independent conformant implementations;
- migration/compat policy;
- security review;
- production usage.

## Mature

- multiple vendors;
- extension ecosystem;
- governance independent enough to avoid unilateral vendor control.

---

# 22. 1.0 Exit Criteria

Do not rush AVP 1.0.

Require:

1. two independent `AVP-Core` implementations;
2. one independent Environment implementation;
3. production usage in at least three different Agent domains;
4. TCK for all core MUST requirements;
5. stable extension mechanism;
6. documented MCP/A2A/OTel interop;
7. security review;
8. migration history across at least two 0.x releases.

---

# 23. Registry Architecture

Potential public registry:

```text
Scenario Packages
Environment Packages
Oracle Packages
Mutation Packs
Extensions
Conformance Results
Benchmark Adapters
```

A registry should accept content-addressed artifacts and signed metadata.

---

# 24. Trust and Signing

Future package metadata MAY support:

```text
signature
publisher identity
provenance
SBOM
build attestation
```

Use established supply-chain standards where possible rather than inventing AVP-specific cryptography.

---

# 25. Community Incentives

Make the open standard valuable independently:

```text
local runner
one-command TCK
SDK generation
public adapters
example benchmark packs
GitHub Actions
clear contribution path
```

The protocol should solve real integration pain before asking people to “join a standard”.

---

# 26. Commercial Strategy Alignment

The company benefits when AVP becomes common because:

```text
more AVP Agents
→ easier platform onboarding

more AVP Environments
→ more reusable verification worlds

more AVS Scenarios
→ richer benchmark ecosystem
```

Commercial moat remains:

```text
scale
managed execution
enterprise connectors
private reliability data
failure graph
RCA automation
```

---

# 27. Anti-Capture Rules

After Stable:

- specification changes require public proposal;
- stable requirement meaning cannot be changed silently;
- TCK is public;
- proprietary extensions cannot masquerade as AVP Core;
- certification marks require transparent criteria.

---

# 28. Naming

Before public launch, perform trademark/package-name availability review.

Working terms:

```text
Agent Verification Protocol (AVP)
Agent Verification Scenario (AVS)
AVP Conformance Kit
```

Do not claim formal standards-body status before one exists.

Use:

> open protocol / proposed specification

rather than:

> international standard.

---

# 29. Documentation Structure

Public docs:

```text
Introduction
Concepts
Architecture
Protocol
Scenario DSL
Security
Telemetry
Conformance
Extensions
Governance
Migration
Examples
```

Normative versioned docs must remain permanently accessible.

---

# 30. First Public Release Proposal

`v0.1-alpha`:

```text
AVP Core
AVP Environment
AVP Verification
AVS
Event Schema
HTTP binding
local reference runtime
refund example
TCK initial suite
MCP adapter
OTel adapter
```

The release should be runnable, not only readable.

---

# 31. Next Standard Work

After this stage:

```text
13 Reference Runtime Design
14 AVP SDK Contract
15 Package/Registry Specification
16 Security Threat Model
17 Oracle SDK
18 Local Runner UX
19 MCP Adapter Spec
20 OpenTelemetry Mapping
```

Then implementation can begin without losing standards discipline.

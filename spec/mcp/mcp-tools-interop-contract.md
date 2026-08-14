# AVP MCP Tools Interoperability Contract v0.1

Status: draft normative candidate

## 1. Scope

This specification defines AVP-owned verification semantics for MCP-backed Subject tool execution. It intentionally does not redefine the Model Context Protocol.

The selected external protocol authority for this profile is MCP `2026-07-28`.

Normative keywords MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are requirement terms for AVP conformance.

## 2. External protocol authority

### AVP-MCP-001 — Selected MCP revision binding

An AVP MCP verification configuration MUST identify the MCP protocol revision used for the evaluated interaction. AVP implementations MUST preserve the semantics of that MCP revision and MUST NOT substitute AVP-defined wire semantics for MCP-defined behavior.

AVP MCP v0.1 targets MCP `2026-07-28`.

Use of `server/discover` is not an AVP requirement. Implementations MAY establish server capabilities by any MCP-conforming mechanism appropriate to the selected revision.

## 3. Capability projection

### AVP-MCP-002 — Scenario capability binding

The MCP tool surface available to a Subject MUST be restricted to the MCP capabilities authorized by the compiled ScenarioInstance for that Subject actor.

A call to an MCP tool outside the authorized set MUST fail closed before any upstream `tools/call` execution is sent.

MCP authorization and OAuth remain separate concerns and MUST NOT be represented as replaced by this AVP capability policy.

## 4. Baseline contract identity

### AVP-MCP-003 — Baseline tool-contract identity

Before an MCP tool call is accepted as part of verified execution, the evaluator MUST establish a baseline identity for the tool contract used by the run.

The identity MUST bind tool names and schema-relevant contract semantics used for validation. Retrieval metadata that does not alter the tool contract — including cache TTL, cache scope, pagination cursor values, or page partitioning — MUST NOT by itself create tool-contract drift.

AVP does not prescribe one digest algorithm for MCP's own protocol objects. If an AVP implementation emits digests as verification identities, the digest preimage and canonicalization used by that implementation MUST be deterministic and stable for the selected profile.

## 5. Validation and drift

### AVP-MCP-004 — Schema validation and drift fail-closed

Tool arguments MUST be validated against the baseline MCP input schema before upstream execution.

When an MCP tool declares an output schema, structured output MUST satisfy that schema before it is accepted as a successful AVP tool result.

An implementation that claims pre-call schema/catalog drift detection MUST compare the active material tool contract against the baseline before upstream execution. Material drift MUST fail closed before the side-effecting tool invocation is issued.

Cache-only metadata changes MUST NOT be treated as material schema drift.

## 6. Verification record binding

### AVP-MCP-005 — Verification call binding

Each MCP tool interaction accepted as AVP verification evidence MUST bind, directly or through an integrity-protected containing record, at minimum:

- correlation identity;
- tool name;
- normalized argument identity;
- bound tool-schema identity;
- bound baseline catalog/tool-set identity;
- normalized accepted-result identity, when one exists;
- whether upstream execution failed before an accepted result existed.

The binding MUST make it possible to distinguish calls that use different tool contracts or different arguments even when their human-readable tool names are equal.

AVP does not prescribe a Python dataclass, event name, storage engine, or telemetry backend for this record.

## 7. MCP wire preservation

### AVP-MCP-006 — MCP wire-semantic preservation

An AVP MCP implementation MUST preserve all mandatory semantics of the selected MCP revision for the transport it uses.

AVP-specific trace, evidence, or evaluator metadata MUST NOT overwrite or conflict with MCP-reserved metadata.

For MCP `2026-07-28` Streamable HTTP, the syntax and encoding of `MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name`, and `Mcp-Param-*` are MCP-owned behavior. AVP conformance does not redefine these fields.

A gateway that mirrors tool parameters into MCP HTTP headers MUST follow the selected MCP revision's value-encoding rules, including required Base64 sentinel encoding for values that cannot be safely represented as plain header values.

## 8. Failure separation

### AVP-MCP-007 — Upstream failure separation

Transport errors, MCP protocol errors, authorization failures, and upstream tool failures MUST NOT be represented as successful accepted tool results.

If the evaluator records a failed upstream attempt, the record MUST distinguish that failure from an interaction with an accepted result identity.

An absent accepted result MUST NOT be assigned a fabricated success digest.

## 9. Unsupported feature honesty

### AVP-MCP-008 — Unsupported MCP feature honesty

An AVP implementation MUST fail closed when an MCP response requires a protocol feature or extension that the implementation does not support for verified execution.

The implementation MUST NOT reinterpret an unsupported interactive, extension, or continuation result as an ordinary successful tool completion.

MCP Multi Round-Trip Requests are not mandatory in AVP MCP v0.1. A reference implementation that does not support MRTR MUST reject `input_required` and MUST NOT claim MRTR support.

## 10. Non-normative implementation freedom

AVP MCP v0.1 does not standardize:

- MCP SDK choice;
- HTTP client implementation;
- use of `server/discover` as a bootstrap mechanism;
- one in-memory representation of MCP catalogs;
- one call-record class;
- one hash helper implementation;
- one cache strategy;
- one observability backend;
- one MCP authorization implementation.

## 11. Security composition

Subject-visible MCP capabilities MUST compose with AVP Security capability isolation. Evaluator credentials, hidden verification state, future fault schedules, or unrestricted MCP tool access MUST NOT be exposed merely because the underlying MCP endpoint is capable of providing them.

MCP transport and authorization security requirements continue to apply independently of AVP conformance.

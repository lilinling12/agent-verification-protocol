# AEP-0005 — MCP Tools Interoperability Profile v0.1

- Status: Final
- Authors: AVP maintainers
- Created: 2026-08-15
- Accepted: 2026-08-16
- Acceptance decision: Approved by the protocol maintainer during the Alpha 2 readiness review. This approves the protocol direction only; the AEP is not Final and this decision does not authorize merge, tag, or release.
- Finalized: 2026-08-17
- Final decision: Explicitly approved by the protocol maintainer for `Accepted` → `Final` on 2026-08-17, based on the merged Alpha 2 Final-eligibility audit and released evidence at `v0.3.0-rc.1` / `ef199124017b0dcc8c4a966d00c4f407760f9a06`; the published release bytes passed external-consumer and full TCK validation, no post-release protocol-semantic drift invalidated that evidence, and this Finalization does not authorize stable `v0.3.0` publication.
- Target AVP version: 0.1

## Problem

AVP already routes Subject tool calls through a verification gateway that speaks Model Context Protocol (MCP) `2026-07-28`. The reference gateway validates allowed tools, captures a baseline tool catalog, detects schema drift, validates call inputs and structured outputs, mirrors MCP HTTP routing headers, and records content digests for verification.

Those behaviors currently mix two authorities:

1. MCP owns the wire protocol, request metadata, tool discovery/call semantics, Streamable HTTP binding, JSON Schema requirements, cache metadata, mirrored headers, and MRTR semantics.
2. AVP owns how an evaluator binds an external MCP tool surface into a reproducible verification run.

AVP must not fork or restate MCP as a competing protocol. It needs a narrow interoperability profile that identifies which MCP revision is selected and standardizes only the verification mappings AVP depends on.

## Interoperability goal

Independent AVP implementations should be able to verify the same MCP-backed Subject tool interaction while using different MCP SDKs, transports, gateway implementations, languages, and deployment topologies.

A conforming AVP MCP implementation must preserve MCP semantics for the selected revision while producing stable evaluator-side bindings for authorization, catalog identity, schema identity, calls, results, and failures.

## Proposed semantics

### AVP-MCP-001 — Selected MCP revision binding

An AVP MCP interoperability profile MUST identify the MCP protocol revision it targets. Implementations MUST use MCP-defined wire and message semantics for that revision rather than redefining them as AVP semantics.

For v0.1 the target revision is `2026-07-28`.

### AVP-MCP-002 — Scenario capability binding

The evaluator MUST bind the MCP tools exposed to the Subject to the compiled Scenario capability policy. A tool outside that allowed set MUST fail closed before an upstream MCP tool invocation is issued.

### AVP-MCP-003 — Baseline tool-contract identity

Before accepting a tool call for verification, the evaluator MUST establish an immutable baseline identity for the tool contract used by the run. Tool-contract identity MUST cover the tool name and schema-relevant contract content. Retrieval metadata such as cache TTL, pagination shape, or cache scope MUST NOT create false contract drift when the underlying tool contract is unchanged.

### AVP-MCP-004 — Schema validation and drift fail-closed

Inputs MUST be validated against the bound MCP tool input schema before upstream execution. When output schema is declared, accepted structured output MUST be validated against that schema. If the implementation claims schema-drift detection, a material tool-contract drift detected before invocation MUST fail closed before the side-effecting tool call is sent upstream.

### AVP-MCP-005 — Verification call binding

Each accepted MCP tool interaction used as AVP verification evidence MUST bind at minimum:

- correlation identity;
- tool name;
- normalized argument identity;
- bound tool-schema identity;
- bound baseline catalog identity;
- normalized result identity when a result is accepted;
- whether upstream execution failed before an accepted result existed.

AVP does not standardize one event, storage, or Python record representation for this binding.

### AVP-MCP-006 — MCP wire-semantic preservation

An AVP gateway MUST preserve the selected MCP revision's required request metadata and transport semantics. AVP-specific tracing or evaluator metadata MUST NOT silently overwrite or conflict with MCP-reserved request metadata.

For Streamable HTTP under MCP `2026-07-28`, mirrored standard and tool-parameter headers remain MCP-defined behavior. AVP does not redefine their syntax or encoding.

### AVP-MCP-007 — Upstream failure separation

An MCP transport, protocol, authorization, or upstream tool failure MUST NOT be represented as a successful accepted tool result. If a verification call record is emitted for a failed upstream attempt, it MUST distinguish the absence of an accepted result from a successful result identity.

### AVP-MCP-008 — Unsupported MCP feature honesty

An implementation MUST fail closed when it receives an MCP feature/result shape that it does not support for verified execution. It MUST NOT flatten an unsupported interactive or extension result into a successful ordinary tool result.

In particular, support for MCP Multi Round-Trip Requests (MRTR) is not required by AVP MCP v0.1. An implementation that does not support MRTR MUST reject `input_required` rather than claiming successful completion.

## MCP-owned semantics explicitly not standardized by AVP

AVP MCP v0.1 does not redefine:

- JSON-RPC message semantics;
- MCP Streamable HTTP framing;
- `MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name`, or `Mcp-Param-*` encoding;
- `server/discover` semantics or whether discovery is used;
- `tools/list` pagination and cache semantics;
- tool `inputSchema` / `outputSchema` semantics;
- MCP authorization;
- MRTR wire formats;
- MCP extensions;
- SDK APIs or transport implementation classes.

`server/discover` is optional in MCP `2026-07-28`. The current Python reference gateway uses it as a bootstrap mechanism; AVP conformance MUST NOT require that specific bootstrap strategy.

## Security composition

MCP tool exposure remains subject to the AVP Security capability boundary. Evaluator credentials, hidden state, future fault information, and unrestricted MCP capabilities MUST NOT be leaked into Subject-visible tool surfaces. MCP authorization remains owned by MCP/OAuth specifications and is not replaced by AVP capability policy.

## Conformance direction

The AVP MCP TCK should validate the verification mapping rather than duplicate the MCP conformance suite. Portable cases should cover revision binding, capability denial before upstream call, baseline identity stability across cache metadata changes, schema drift before side effects, successful call binding, upstream failure separation, and unsupported MRTR fail-closed behavior.

The TCK MUST NOT require the Python `MCPVerificationGateway`, `urllib`, one SDK, or `server/discover` as implementation APIs.

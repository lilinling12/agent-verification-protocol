# MCP Tools Interoperability Reconciliation Decision 001

- Status: Proposed
- Date: 2026-08-15
- Scope: AVP MCP Tools Interoperability v0.1

## Decision

Promote only AVP-owned verification mappings around MCP tool execution. MCP `2026-07-28` remains the authority for wire format, request metadata, tool definitions, Streamable HTTP behavior, cache metadata, mirrored headers, authorization, and MRTR.

## Promoted AVP semantics

- bind the selected MCP revision into the verification configuration;
- bind Subject-visible MCP tools to compiled Scenario capabilities;
- capture immutable baseline tool-contract/catalog identity for a verification run;
- validate tool inputs before upstream invocation;
- validate declared structured output before acceptance;
- fail closed on material schema/catalog drift before side effects when drift detection is claimed;
- bind accepted calls to correlation, tool, arguments, schema, catalog, result, and upstream-failure identity;
- keep failed upstream attempts distinct from accepted results;
- reject unsupported MCP result shapes rather than flattening them into success.

## MCP-owned semantics kept external

- JSON-RPC envelope and error semantics;
- protocol negotiation and revision compatibility;
- Streamable HTTP request/response framing;
- standard and mirrored HTTP header syntax/encoding;
- `server/discover` semantics and optionality;
- `tools/list` pagination/cache behavior;
- tool JSON Schema semantics;
- authorization and OAuth behavior;
- MRTR wire format;
- MCP extensions and SDK APIs.

## Reference implementation consequence

The Python reference gateway is implementation evidence only. Its use of `server/discover`, `urllib`, internal digest models, and current call-record dataclass are non-normative.

The reference implementation must first conform to the selected MCP revision at the wire boundary. During this reconciliation, the `x-mcp-header`/`Mcp-Name` Base64 sentinel encoding gap was identified and corrected before any AVP interoperability conformance claim is promoted.

## Conformance consequence

AVP TCK cases will exercise the verification mappings without duplicating MCP's own conformance suite. A test vector may assume a conforming MCP endpoint/fixture and then verify AVP policy binding, identity binding, drift handling, evidence binding, failure separation, and feature-support honesty.

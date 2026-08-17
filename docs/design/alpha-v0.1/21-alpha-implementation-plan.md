# 21 AVP Alpha Implementation Plan

The project has crossed from architecture design into protocol implementation.

## Alpha goal

Prove the full loop:

```text
Scenario
→ isolated Subject capabilities
→ authoritative Environment State
→ faults
→ verification evidence
→ reliability
→ failure localization
→ replay
→ release decision
```

## Current completed slice

Commerce Refund reference world proves:

- State Truth > Agent self-report;
- Evaluator failure != Agent failure;
- subject capability boundary;
- state-equivalent restore;
- wrong-target localization;
- tool-fault recovery;
- repeated-run metrics.

## Next engineering order

1. AVS compiler and immutable ScenarioInstance.
2. MCP HTTP gateway against a real MCP server.
3. PostgreSQL State Adapter.
4. OTel export with AVP correlation.
5. external Agent HTTP adapter.
6. paired experiment runner.
7. Browser runtime.
8. counterfactual replay across Agent component interventions.

## Definition of Alpha-quality

Alpha does not mean shallow. It means semantics may still change.

Every shipped Alpha feature should be end-to-end and conformance-tested.

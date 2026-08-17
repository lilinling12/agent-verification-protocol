# 08 Verification Engine Specification

> Status: Draft v0.1  
> Parent: AVP  
> Principle: **Verify claims from the strongest available evidence.**

## 1. Purpose

Verification Engine converts Episode evidence into structured conclusions without collapsing all evaluation into a single LLM-generated score.

Its central question is:

> **What can be established from available evidence, with what method, under what validity assumptions?**

The engine is built around:

```text
Claim
→ Evidence Policy
→ Evaluator Routing
→ Result
→ Conflict Resolution
→ Verdict
→ Validity
```

---

# 2. Verification Hierarchy

Recommended default precedence:

```text
Authoritative State Oracle
    >
Executable Test
    >
Temporal / Policy Rule
    >
Schema / Structured Validator
    >
Agentic Evidence Collector
    >
Semantic LLM Judge
    >
Human Adjudication
```

This is not a quality ranking. Human adjudication may be highest-quality but lowest-throughput.

The principle is:

> Do not use semantic opinion to answer a question for which deterministic truth exists.

---

# 3. Claim Model

Every verification starts from a Claim.

```yaml
claim:
  id: refund.completed
  dimension: state.postcondition
  severity: critical
  subject: refund:rf_123
  expected:
    status: completed
```

Core dimensions:

```text
outcome
state.postcondition
state.invariant
state.collateral
tool.selection
tool.argument
tool.target
trajectory
control
policy
safety
semantic
efficiency
eval.validity
```

---

# 4. Claim Properties

Each Claim declares:

```text
id
dimension
severity
scope
subject
expected relation
evidence policy
evaluator policy
hard/soft
aggregation policy
```

Severity baseline:

```text
info
minor
major
critical
```

A `critical hard` Claim may veto deployment.

---

# 5. Evidence Policy

A Claim declares what evidence types are allowed.

```yaml
evidence:
  require:
    - environment_state
  allow:
    - tool_events
    - authority_witness
  deny:
    - agent_self_report
```

This prevents a semantic judge from using prohibited hidden answer keys or trusting the Agent's own declaration of success.

---

# 6. Evidence Trust Levels

```text
T0 — untrusted external content
T1 — subject-generated content
T2 — instrumented interaction event
T3 — runtime-authoritative event
T4 — evaluator-authoritative state/evidence
```

A Claim may specify minimum trust.

Example:

```text
financial transfer success → T4
response tone → T1 sufficient
```

---

# 7. State Oracle

A State Oracle evaluates authoritative State.

Example:

```text
claim: correct refund exists

source:
  projection = commerce.refunds

predicate:
  exactly_one(refund where order_id = target
                       and status = completed)
```

State Oracle output:

```json
{
  "verdict": "PASS",
  "confidence": 1.0,
  "evidence": ["artifact://state/..."],
  "oracle_version": "refund-state@7"
}
```

---

# 8. Invariant Oracle

Runs across an Episode or interval.

Example:

```text
customer.deleted == false
```

at every material State transition.

This can detect:

> final state looks correct, but the Agent temporarily performed an unsafe mutation and later repaired it.

---

# 9. Collateral-Damage Oracle

Compares expected mutation scope with actual State Diff.

```text
Allowed:
  refund target order

Observed:
  refund target order
  customer marketing consent
```

Result:

```text
Outcome PASS
Collateral FAIL
```

This is a major differentiator from final-answer evaluation.

---

# 10. Executable Tests

Executable graders are sandboxed code.

They MUST declare:

```text
input evidence
runtime image
test code digest
dependency lock digest
timeout
network policy
```

A crashed grader yields `ORACLE_FAILURE`, not subject `FAIL`.

---

# 11. Temporal Verification

Temporal rules operate on event traces and State transitions.

Core operators:

```text
BEFORE
AFTER
NEVER
EVENTUALLY
WITHIN
UNTIL
COUNT
NO_MUTATION_AFTER
MUST_OBSERVE_BEFORE
MUST_CONFIRM_BEFORE
```

Example:

```text
human.approval BEFORE environment.commit(financial.transfer)
```

Temporal violations should identify the earliest offending event.

---

# 12. Control Decision Verification

Baseline decisions:

```text
ACT
ASK
CONFIRM
REFUSE
RECOVER
STOP
```

Evaluation should use a **cost-sensitive confusion matrix**.

For a high-risk ambiguous transfer:

```text
expected CONFIRM
observed ACT
```

is more severe than:

```text
expected ACT
observed ASK
```

Therefore simple accuracy is insufficient.

---

# 13. Tool Verification

Core checks:

## Discovery

Was the relevant tool discoverable and did the Agent discover it?

## Selection

Was the selected tool appropriate?

## Arguments

Do arguments satisfy schema and semantic constraints?

## Target

Was the correct entity/object targeted?

## Result Use

Did subsequent behavior correctly incorporate tool result?

## Recovery

After failure, did the Agent retry, switch tool, re-ground or escalate appropriately?

## Over-action

Did it continue calling state-changing tools after the goal was satisfied?

---

# 14. False Success Verification

A first-class failure type:

```text
Agent reports success
AND
authoritative success Claim FAILS
```

This should receive a high severity for action Agents.

---

# 15. Policy Engine

Policies describe constraints not always encoded in business State.

Examples:

- “refund above HKD 2,000 requires confirmation”;
- “cannot email PII externally”;
- “must verify identity before medication change”.

Policy evaluator should be versioned separately from the Scenario.

---

# 16. Safety Verification

Safety is based on:

```text
intent
capability
authority
action
state effect
data exposure
policy
```

Final textual harmlessness is insufficient.

A malicious webpage that causes a secret to be uploaded is a safety failure even if final output is polite.

---

# 17. Semantic Judge

Use only for genuinely semantic claims:

- answer relevance;
- explanation quality;
- source quality;
- completeness;
- human-facing clarity;
- nuanced artifact quality.

Semantic Judge must declare:

```text
model
prompt/rubric digest
temperature/settings
allowed evidence
tool access
judge version
```

---

# 18. Agentic Judge

Agentic Judge may collect/verify evidence across multiple artifacts.

It is useful for:

- research-report fact verification;
- code artifact inspection;
- complex multi-file output.

However, it is still an evaluator subject to calibration and prompt injection.

Agentic Judge SHOULD run with least privilege and restricted tools.

---

# 19. Judge Prompt Injection Defense

Trace/tool/file content is untrusted.

Judge runtime SHOULD:

- separate rubric from evidence;
- delimit evidence structurally;
- disable arbitrary tool use;
- disallow subject credentials;
- restrict network;
- scan explicit evaluator-targeting instructions;
- log all judge tool activity.

---

# 20. Judge Reliability Contract

Every Judge version may publish:

```text
gold-set accuracy
precision/recall
critical-failure false-negative rate
calibration metrics
slice performance
latency
cost
sample size
```

An uncalibrated Judge SHOULD be labeled `UNCALIBRATED`.

---

# 21. Judge Gold Set

Gold set should combine:

```text
deterministic synthetic errors
human-adjudicated examples
production incidents
mutation-derived variants
security attacks
edge cases
```

The gold set itself is versioned and protected from leakage.

---

# 22. Judge Ensemble

Ensemble is not naive majority voting.

Example routing/combining logic:

```text
State Oracle FAIL critical → FAIL
Temporal Rule FAIL critical → FAIL
State PASS + Semantic disagreement → semantic review
Two semantic judges disagree on high-risk item → adjudication
```

Ensemble policy is versioned.

---

# 23. Conflict Model

Conflicts are explicit:

```text
Judge A PASS
Judge B FAIL
State Oracle PASS
```

Result may be:

```text
task PASS
semantic INCONCLUSIVE
```

Do not hide disagreement in an averaged 0.71 score.

---

# 24. Evaluation Validity Engine

Runs independently of subject Claims.

Checks:

```text
initial state valid
environment healthy
trace complete
oracle healthy
judge healthy
contamination absent
resource manifest available
required fault actually activated
replay fidelity sufficient
```

The validity engine may invalidate the entire Episode or specific Claims.

---

# 25. Partial Validity

Some Claims may remain valid while others become invalid.

Example:

```text
State Oracle valid
Semantic Judge crashed
```

Output:

```text
state claims: valid
semantic claims: invalid
episode summary: PARTIALLY_VALID
```

AVP core currently has Episode-level validity; platform implementations SHOULD preserve per-Claim validity internally for future standardization.

---

# 26. Contamination Verification

Signals:

- benchmark canary exposure;
- explicit answer-key exposure;
- benchmark metadata;
- Agent search query naming benchmark;
- answer overlap with leaked material;
- evaluator endpoint accessed.

Contamination does not necessarily mean the Agent behaved maliciously; it means the measurement may no longer answer the intended question.

---

# 27. Verification Result

Canonical structure:

```json
{
  "claim_id": "refund.completed",
  "dimension": "state.postcondition",
  "severity": "critical",
  "method": "state_oracle",
  "evaluator_version": "refund-state@7",
  "verdict": "PASS",
  "confidence": 1.0,
  "validity": "VALID",
  "evidence": ["ev_91"]
}
```

---

# 28. Aggregation

Aggregation policy should be Scenario/Release-policy driven.

Example:

```text
critical hard Claim FAIL → task FAIL
major claims ≥ 80%       → quality threshold
minor semantic score     → report only
```

No universal weighted average is mandated.

---

# 29. Verification DAG

A Verification plan is a DAG:

```text
State Projection
   ├── Postcondition Oracle
   ├── Collateral Oracle
   └── Policy Oracle

Event Stream
   ├── Temporal Oracle
   └── Control Oracle

Final Artifact
   └── Semantic Judge

All
   ↓
Validity Engine
   ↓
Verdict Policy
```

DAG execution enables parallelism and caching.

---

# 30. Caching

Deterministic evaluator results MAY be cached by:

```text
claim digest
evidence digest
evaluator digest
```

Semantic Judge outputs SHOULD only be cached when all material settings/evidence identities match.

---

# 31. Verification Evidence Graph

Claims and evidence form a graph:

```text
Claim
 ← supported_by — Evidence
 ← evaluated_by — EvaluatorVersion
 ← invalidated_by — ValidityFinding
```

This graph supports audit and downstream Release Gates.

---

# 32. Human Adjudication

Human review is used for:

- high-risk disagreement;
- Judge calibration;
- new failure taxonomy;
- ambiguous policy;
- product-significant regressions.

Human annotations MUST record:

```text
reviewer role
rubric version
evidence shown
decision
confidence optional
timestamp
```

---

# 33. Evaluator CI/CD

Changing an Oracle/Judge/Policy must trigger:

```text
schema validation
gold-set regression
critical FNR check
latency/cost check
compatibility check
release gate
```

Evaluator software is production software.

---

# 34. Conformance

`AVP-Verification` MUST verify:

1. Claim results identify evidence.
2. Critical deterministic failure can veto semantic PASS.
3. Oracle execution error maps to validity failure.
4. Evaluator Plane is isolated.
5. Evaluator version is immutable/resolvable.
6. Agent self-report is not automatically authoritative.
7. Hidden answer data is not exposed to subject.

---

# 35. Product Implication

The Verification Engine should make a user feel:

> “I can inspect why this verdict is true.”

rather than:

> “Another LLM said 8.7/10.”

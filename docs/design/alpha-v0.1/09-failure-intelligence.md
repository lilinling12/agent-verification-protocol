# 09 Failure Intelligence & Counterfactual RCA

> Status: Draft v0.1  
> Purpose: turn Episode failures into actionable, evidence-backed engineering hypotheses.

## 1. Thesis

A failed Agent run is not useful unless the platform can answer:

```text
What failed?
Where did it first become wrong?
What conditions trigger the failure?
Which Agent component is implicated?
What intervention improves it?
Did the intervention really fix the same failure?
```

Failure Intelligence is therefore not trace summarization.

It is:

```text
Localization
+ Taxonomy
+ Clustering
+ Comparative Analysis
+ Counterfactual Intervention
+ Regression Synthesis
```

---

# 2. Failure vs Incident vs Symptom

## Symptom

Observed bad event:

- HTTP 500;
- wrong answer;
- loop;
- unsafe tool call.

## Failure

Verification-level condition:

- wrong target changed;
- confirmation omitted;
- recovery failed.

## Incident

Production/business manifestation:

- customer charged twice;
- unauthorized email sent.

One Incident may contain many symptoms and one or more failures.

---

# 3. Primary Failure Record

```yaml
failure:
  id: fail-991
  episode_id: ep-77
  taxonomy: state.wrong_target
  severity: critical
  first_bad_step: evt-41
  first_bad_state: sha256:S41
  downstream:
    - false_success
    - collateral_refund
  evidence:
    - ev-state-diff-41
  cluster: cluster-12
```

---

# 4. Failure Taxonomy v0.1

## Goal / Understanding

```text
goal.misinterpretation
goal.missing_constraint
goal.wrong_scope
goal.user_correction_ignored
```

## Control

```text
control.act_instead_of_ask
control.act_instead_of_confirm
control.act_instead_of_refuse
control.stop_instead_of_recover
control.premature_stop
control.over_action
```

## Tool

```text
tool.discovery_failure
tool.wrong_selection
tool.wrong_argument
tool.wrong_target
tool.schema_misread
tool.result_misuse
tool.unnecessary_call
```

## Observation / State

```text
state.stale_observation
state.missed_update
state.wrong_entity_binding
state.collateral_damage
state.false_success
state.constraint_violation
```

## Recovery

```text
recovery.no_retry
recovery.bad_retry
recovery.retry_loop
recovery.fallback_failure
recovery.escalation_failure
```

## Memory / Context

```text
context.loss
context.conflict
memory.stale
memory.poisoned
memory.wrong_recall
```

## Safety / Security

```text
security.prompt_injection_followed
security.secret_exposure
security.permission_violation
security.privilege_escalation
security.untrusted_instruction_execution
```

## Coordination

```text
multiagent.bad_delegation
multiagent.cyclic_delegation
multiagent.duplicate_action
multiagent.authority_loss
multiagent.shared_state_conflict
```

## Evaluation

```text
eval.oracle_failure
eval.environment_failure
eval.trace_failure
eval.contamination
eval.broken_task
```

Evaluation failures are excluded from subject failure-rate metrics by default.

---

# 5. First Bad Step

Definition:

> The earliest event or State transition for which available evidence indicates a causally relevant deviation from the acceptable behavior set.

Important:

```text
first error message
≠
first bad step
```

Example:

```text
#12 stale observation accepted   ← first bad step
#16 wrong tool argument
#17 DB error
#18 retry
#23 final wrong answer
```

The root debugging target is usually #12.

---

# 6. Localization Signals

Candidate generation uses:

- first violated invariant;
- first violated temporal rule;
- first wrong State mutation;
- wrong target binding;
- first unsafe Control decision;
- stale/fault-conditioned observation use;
- first metamorphic divergence;
- first unexpected tool call;
- first authority-witness mismatch.

---

# 7. Causal Neighborhood

For each candidate event, build a local event graph:

```text
prior observations
prior user messages
current tool schema
current State version
active faults
authority witnesses
memory reads
selected action
resulting State diff
```

This is more useful than embedding the full 200-step Trace.

---

# 8. Failure Feature Vector

Structured features:

```text
taxonomy
tool identity
schema fields
target type
control gate
fault type
State delta signature
risk class
Agent component versions
horizon bucket
language
runtime
retry pattern
```

Semantic features:

```text
local event graph summary
task semantics
tool description semantics
error text
```

Graph features:

```text
event type neighborhood
dependency edges
State-transition topology
```

Clustering SHOULD combine these modalities.

---

# 9. Clustering

Use two stages:

## Stage A — High-precision structured grouping

Examples:

```text
same tool + same field + same error
same violated control gate
same State-delta signature
```

## Stage B — Semantic/graph merge

Merge structurally adjacent groups when evidence suggests same engineering cause.

This avoids letting embeddings turn unrelated failures into one vague cluster.

---

# 10. Cluster Object

```yaml
cluster:
  id: cluster-12
  label: Wrong order id after ambiguous search
  taxonomy:
    - tool.wrong_target
    - control.act_instead_of_ask
  size: 84
  affected_agents: [v41, v42]
  slices:
    zh-CN: 0.61
    high-risk: 0.87
  first_seen: ...
  last_seen: ...
```

---

# 11. Version Diff

Compare Agent A and B at cluster level.

```text
Overall success: +4.2 pp

Cluster changes:
wrong-target            -58%
recovery-timeout        -31%
missed-confirmation     +190%  ← regression
context-loss            unchanged
```

This is more actionable than one aggregate score.

---

# 12. Root Cause Hypothesis

A hypothesis explicitly separates evidence from inference.

```yaml
hypothesis:
  id: rca-7
  statement: >
    refund.create argument naming causes model to bind customer_id
    to order_id in ambiguous Chinese requests.
  implicated_component:
    type: tool_schema
    ref: refund.create@9
  supporting:
    - cluster-12
    - schema-field-confusion
  confidence_before_replay: 0.64
```

Do not label it “root cause” yet.

---

# 13. Intervention Catalog

Possible interventions:

```text
model change
instruction change
tool rename
field rename
description rewrite
tool split
tool merge
schema constraint
typed validator
confirmation gate
permission change
retrieval change
memory policy
retry policy
re-grounding step
context compaction
user-simulator clarification
```

---

# 14. Counterfactual Replay

Procedure:

```text
1 choose checkpoint before first-bad-step candidate
2 restore
3 hold declared variables constant
4 apply one intervention
5 replay repeated trials
6 compare target failure and side effects
7 optionally revert intervention and reproduce failure
```

---

# 15. Evidence Grades

## Grade A — Strong intervention evidence

- failure reproduces before intervention;
- intervention removes/reduces target failure;
- revert restores failure;
- repeated across multiple Scenario instances.

## Grade B — Strong repeated association + intervention

Intervention improves target failure repeatedly but exact revert not available.

## Grade C — Trace-supported hypothesis

Strong local evidence, no controlled replay.

## Grade D — Semantic speculation

LLM/human explanation only.

UI wording should reflect the grade.

---

# 16. Counterfactual Experiment Design

Do not compare:

```text
Agent v1 entire system
vs
Agent v2 entire system
```

and call it RCA.

For causal debugging, vary the smallest feasible factor.

Example:

```text
tool schema field only
```

while freezing:

- ScenarioInstance;
- environment seed;
- user seed;
- fault seed;
- model version;
- prompt version.

Agent sampling may still be stochastic, requiring repeated replay.

---

# 17. Replay Confounders

Record:

```text
model endpoint changed
provider load changed
external web changed
runtime image changed
browser version changed
uncontrolled clock
non-replayed external API
```

If confounders are material, downgrade causal evidence.

---

# 18. Minimal Reproducer

For each confirmed cluster, generate a minimized Scenario:

```text
remove irrelevant tools
reduce DB entities
shorten conversation
remove unrelated policy
preserve failure
```

This creates an Agent equivalent of a minimal bug reproduction.

---

# 19. Delta Debugging

Automated minimization can iteratively remove:

- tools;
- context blocks;
- entities;
- prior messages;
- policy clauses;
- memory entries.

Keep a removal if the failure probability remains above a threshold.

Because Agents are stochastic, minimization is probabilistic, not binary.

---

# 20. Regression Synthesis

Confirmed failure produces:

```text
base reproducer
semantic variants
boundary variants
fault variants
security variants
metamorphic variants
```

Example:

```text
wrong-order ambiguity
→ same name
→ same date
→ same amount
→ Chinese pronoun
→ English pronoun
→ stale order list
```

---

# 21. Regression Quarantine

Auto-generated scenarios MUST enter quarantine until:

```text
schema valid
initial state valid
oracle valid
solvability acceptable
non-duplicate
no answer leakage
```

Only then join blocking release suites.

---

# 22. Production Incident Mining

Production Episode signals:

```text
user correction
manual override
tool retry
exception
unexpected State delta
high-risk action
long trajectory
high cost
policy warning
support ticket
```

These are candidates, not automatic failures.

---

# 23. Novelty Detection

Novel failure detection compares:

- taxonomy;
- event graph;
- State diff;
- semantic embedding;
- component version.

Novel high-risk clusters should be surfaced even when frequency is low.

---

# 24. Failure Knowledge Graph

Nodes:

```text
FailurePattern
AgentVersion
AgentComponent
Tool
SchemaField
ScenarioFamily
EnvironmentCondition
Fault
Intervention
RegressionTest
Release
```

Edges:

```text
OCCURS_IN
TRIGGERED_BY
CORRELATED_WITH
HYPOTHESIZED_CAUSE
CONFIRMED_BY
IMPROVED_BY
REGRESSED_AFTER
PROTECTED_BY
```

---

# 25. Confidence Update

Counterfactual experiments update graph edge strength.

Example:

```text
tool field ambiguity
   --HYPOTHESIZED_CAUSE 0.64-->
wrong-target cluster

after replay:
   --CONFIRMED_BY 0.92-->
```

No requirement to interpret these as Bayesian probabilities unless a calibrated model is used.

---

# 26. Recommended User Workflow

```text
Release blocked
   ↓
Open regression cluster
   ↓
See first bad step
   ↓
Inspect causal neighborhood
   ↓
Review proposed hypotheses
   ↓
Run 3 candidate interventions
   ↓
Compare counterfactual results
   ↓
Accept patch
   ↓
Generate regression suite
   ↓
Re-run Release Gate
```

---

# 27. RCA Quality Metrics

Evaluate Failure Intelligence itself.

Metrics:

```text
first_bad_step_top1_accuracy
first_bad_step_top3_recall
taxonomy_precision
cluster_purity
cluster_stability
hypothesis_confirmation_rate
counterfactual_fix_rate
minimal_reproducer_success
regression_recurrence_rate
```

Human-reviewed incident sets are needed for calibration.

---

# 28. Security

Failure analysis may contain secrets/PII.

The RCA Agent/Judge:

- receives redacted local evidence by default;
- should not receive subject credentials;
- has restricted network;
- cannot mutate production;
- cannot access unrelated tenants.

---

# 29. Conformance

A platform claiming `AVP Failure Intelligence` SHOULD:

1. preserve immutable source events;
2. represent first-bad-step as an annotation;
3. distinguish hypothesis from confirmed cause;
4. record replay interventions;
5. report uncontrolled replay variables;
6. keep Eval failures separate from subject failure clusters;
7. version taxonomy.

---

# 30. Strategic Moat

The long-term moat is not the clustering model.

It is the accumulated graph:

```text
Failure Pattern
→ Trigger
→ Component
→ Intervention
→ Verified Outcome
```

across thousands of real Agent changes.

# 10 Agent Reliability & Statistical Methodology

> Status: Methodology Draft v0.1  
> Goal: make Agent comparisons scientifically defensible rather than leaderboard theater.

## 1. Why Agent Reliability Is Different

Agent outcomes vary because of:

```text
task sampling
Scenario generation
user simulation
model sampling
tool latency/errors
runtime resources
provider behavior
browser/OS state
network
external web
Judge noise
```

A single success rate hides these sources.

Therefore AVP experiments must preserve **experimental design**, not only final score.

---

# 2. Unit of Observation

Primary unit:

```text
Episode
```

But Episodes are nested:

```text
Benchmark
  → ScenarioTemplate
    → ScenarioInstance
      → seed family
        → repeated Episode
```

Naively treating all Episodes as IID may understate uncertainty.

---

# 3. Pass Metrics

## Per-run success

```text
p̂ = successful valid Episodes / valid Episodes
```

## Success@k

Probability that at least one of k runs succeeds.

Useful for:

> “try several times and keep one good result.”

## Pass^k

Probability all k repeated runs succeed.

Useful for:

> “this autonomous workflow must work reliably every time.”

For an independent run probability `p`, a simple conceptual form is:

```text
Pass^k = p^k
```

But real repeated Agent runs may be correlated, so empirical grouped estimation is preferred where possible.

---

# 4. Do Not Confuse `pass@k` and `Pass^k`

Coding benchmark conventions often use `pass@k` to mean at least one successful sample.

Reliability engineering often wants the opposite property:

```text
all repeated executions succeed
```

AVP reporting MUST label semantics explicitly.

Recommended names:

```text
success_at_k
all_success_k
```

UI may display `Pass^k` as a friendly alias for `all_success_k`.

---

# 5. Repeated-Run Design

A reliability experiment should define:

```yaml
repetitions:
  per_instance: 8

seeds:
  freeze:
    - environment
    - user
    - fault
  vary:
    - agent_sampling
```

Another experiment may intentionally vary environment/fault seeds.

These answer different questions.

---

# 6. Reliability Slices

Always report by relevant slices:

```text
risk
task family
language
tool topology
horizon
fault
environment runtime
customer segment
permission level
```

High overall success may hide catastrophic low-frequency risk.

---

# 7. Confidence Intervals

For simple binary proportions, report uncertainty.

Recommended baseline:

- Wilson interval for one proportion;
- bootstrap or paired methods for complex/nested designs.

Avoid reporting:

```text
87.13%
```

without uncertainty/sample size.

---

# 8. Agent A vs B

Prefer paired experiments.

Pair on:

```text
ScenarioInstance
environment seed
user seed
fault seed
runtime class
```

Then vary AgentSystem.

Pairing reduces variance from task difficulty.

---

# 9. Paired Binary Comparison

For paired PASS/FAIL results, McNemar-style analysis can test discordant pairs.

The most informative counts are:

```text
A pass / B pass
A pass / B fail
A fail / B pass
A fail / B fail
```

The second and third cells directly characterize regressions/improvements.

---

# 10. Paired Bootstrap

For complex metrics, use paired resampling at the correct experimental unit.

If repeated Episodes share a ScenarioInstance, bootstrap clusters rather than individual runs when appropriate.

Always preserve experimental dependence structure.

---

# 11. Effect Size

Statistical significance is not sufficient.

Report:

```text
absolute delta
relative delta when meaningful
confidence interval
sample size
risk-weighted delta
cost delta
latency delta
```

Example:

```text
+0.4 pp
95% CI [-0.6, +1.4]
```

should not be presented as a meaningful improvement.

---

# 12. Non-Inferiority and Equivalence

Release decisions often ask:

> Does candidate improve cost without making safety/reliability materially worse?

Use non-inferiority margins.

Example:

```yaml
safety:
  allowed_drop_pp: 0

success:
  allowed_drop_pp: 1.0

cost:
  required_improvement_percent: 15
```

This is more appropriate than always testing “different from zero”.

---

# 13. Minimum Detectable Effect

Experiment planning should support:

```text
baseline rate
desired effect
alpha
power
pair correlation estimate
cluster structure
```

Output:

```text
recommended ScenarioInstances
repetitions
expected Episode count
```

---

# 14. Sequential / Adaptive Testing

Agent Eval can be expensive.

Allowed pattern:

```text
run initial batch
→ obvious catastrophic regression?
   stop
→ uncertain?
   allocate more Episodes
```

Stopping rules must be predeclared to avoid cherry-picking.

A Release Gate should record whether sequential testing was used.

---

# 15. Multiple Comparisons

Large dashboards test many slices.

If the product marks individual slices as “statistically significant”, it should account for multiplicity or clearly label exploratory results.

Recommended separation:

```text
pre-registered primary metrics
confirmatory slices
exploratory slices
```

---

# 16. Infrastructure as Experimental Variable

Runtime configuration MUST be recorded:

```text
CPU request/limit
RAM request/limit
GPU
disk
region
network
runtime image
browser
concurrency
time limit
```

Infra failures are separately measured.

If resource configuration changes between Agent A/B, comparison is confounded unless intentional.

---

# 17. Infra Stability Calibration

Before benchmark use, calibrate a resource band.

Goal:

```text
enough headroom to prevent incidental infra failures
but not so much that resources materially change task capability
```

Calibration runs should compare performance across resource levels.

The environment package SHOULD publish recommended resource bands.

---

# 18. Invalid Episode Treatment

Validity states such as:

```text
ENVIRONMENT_FAILURE
ORACLE_FAILURE
TRACE_INCOMPLETE
CONTAMINATED
```

are not ordinary subject FAIL.

Report:

```text
valid success rate
invalid rate
invalid reason distribution
```

High invalid rate can itself block a benchmark or release decision.

---

# 19. Missingness

Do not simply discard invalid runs without analysis.

Missing/invalid Episodes may be non-random.

Example:

> one Agent systematically causes OOM by launching huge dependency installs.

This may be subject behavior, infrastructure, or both.

The validity classifier must distinguish:

```text
infra-independent Agent resource behavior
vs
platform accidental kill
```

When ambiguous, report sensitivity analyses.

---

# 20. Reliability under Faults

Define:

```text
clean_success
fault_conditioned_success
recovery_success
robustness_retention
```

Example:

```text
clean = 0.94
timeout condition = 0.80
retention = 0.851
```

Do not hide clean vs perturbed behavior in one score.

---

# 21. Security Metrics

Examples:

```text
attack_success_rate
unauthorized_action_rate
secret_exposure_rate
confirmation_bypass_rate
privilege_escalation_rate
```

For safety-critical metrics, false negatives may be more costly than false positives.

Release policy can assign zero tolerance.

---

# 22. Control Confusion Matrix

For:

```text
ACT
ASK
CONFIRM
REFUSE
RECOVER
STOP
```

report full confusion matrix.

Also report risk-weighted loss.

Example:

```text
CONFIRM → ACT
```

may carry weight 100;

```text
ACT → ASK
```

may carry weight 2.

Weights are domain policy, not protocol constants.

---

# 23. Cost and Latency

Report cost conditional on success:

```text
mean cost / Episode
cost / successful Episode
p50/p95 latency
steps / successful Episode
tool calls / successful Episode
```

A cheaper Agent with dramatically lower success is not necessarily better.

---

# 24. Long-Horizon Reliability

For long tasks, capture:

```text
failure hazard by step/time
survival curve to completion
checkpoint recovery rate
time-to-first-bad-step
```

This can reveal:

> 95% of failures occur after step 50.

---

# 25. Hierarchical Model

For mature experiments, an optional hierarchical model can separate variance from:

```text
Scenario family
Scenario instance
Agent version
environment
seed
runtime
time window
```

The protocol does not mandate one Bayesian/frequentist implementation.

It mandates preserving enough metadata to support such analysis.

---

# 26. Benchmark Stability

Track benchmark behavior over time:

```text
difficulty drift
invalid-rate drift
environment drift
Judge drift
contamination rate
reference-agent drift
```

A living benchmark should publish a versioned calibration report.

---

# 27. Judge Uncertainty

When semantic Judge outputs drive metrics, separate:

```text
subject uncertainty
judge uncertainty
```

Judge calibration errors are not magically part of binomial task uncertainty.

Where Judge reliability is material, report sensitivity to evaluator versions.

---

# 28. Reporting Minimum

Every serious experiment report SHOULD include:

```text
Agent version digests
Benchmark/Scenario version
Environment/runtime manifest
valid Episode count
invalid Episode count
repeat policy
primary metric
uncertainty interval
A/B pairing policy
resource policy
Judge/Oracle versions
cost/latency
known confounders
```

---

# 29. Example Report

```text
Candidate B vs Baseline A

Valid paired ScenarioInstances: 420
Runs per instance: 4

Task success
A 82.1%
B 86.4%
Δ +4.3 pp
95% paired bootstrap CI [+2.0, +6.5]

all_success_4
A 57.2%
B 65.1%
Δ +7.9 pp

Critical safety
A 0 / 1,680
B 3 / 1,680
BLOCK

Invalid eval rate
A 0.6%
B 0.7%

Conclusion
Candidate improves task reliability but fails zero-tolerance safety policy.
```

---

# 30. Release Decision, Not Score Worship

A release may be blocked even when aggregate capability rises.

Release policies combine:

```text
minimum reliability
non-inferiority
zero-tolerance safety
validity quality
cost ceilings
statistical evidence
```

---

# 31. Conformance

A compliant Reliability Engine SHOULD:

1. distinguish `success_at_k` from `all_success_k`;
2. expose sample size and uncertainty;
3. preserve pairing metadata;
4. separate invalid Episodes;
5. report resource methodology;
6. support slice analysis;
7. prevent silent aggregation of safety hard failures;
8. record experimental design with results.

---

# 32. Research Anchors

Methodology should remain compatible with established statistical practice and current Agent-eval evidence, including empirical findings that infrastructure alone can shift agentic benchmark results by multiple percentage points.

The standard should prefer robust, transparent experimental design over a bespoke “Agent score”.

# 17 Oracle SDK Specification

> Status: Draft v0.1  
> Goal: make deterministic verification easy enough that teams do not default to LLM-as-a-Judge.

## 1. Oracle Definition

An Oracle evaluates one or more Claims from declared trusted evidence.

It is:

```text
versioned
deterministic where possible
sandboxed
evidence-scoped
observable
testable
```

---

## 2. Python Interface

```python
class Oracle:
    def descriptor(self) -> OracleDescriptor: ...
    def evaluate(self, context: OracleContext) -> list[VerificationResult]: ...
```

---

## 3. OracleDescriptor

```text
name
version
digest
claim dimensions
required evidence
runtime requirements
network policy
determinism
timeout
```

---

## 4. OracleContext

Provides only declared inputs:

```text
scenario metadata
Claim
State projections
event query
artifact reader
virtual time
```

No hidden global runtime access.

---

## 5. Evidence Reader

Oracle receives capability-limited artifact access.

Example:

```python
ctx.evidence.json("state://commerce/refunds")
```

It cannot enumerate every tenant artifact.

---

## 6. Built-In Helpers

```text
assert_equal
assert_count
assert_no_change
assert_only_changed
assert_before
assert_never
assert_schema
assert_authorized
```

---

## 7. State Oracle

Example:

```python
@oracle("refund.completed", version="1.0.0")
def refund_completed(ctx):
    refunds = ctx.state("commerce.refunds")
    ok = any(
        r["order_id"] == ctx.param("target_order_id")
        and r["status"] == "completed"
        for r in refunds
    )
    return ctx.result(ok, evidence=[refunds.ref])
```

---

## 8. Temporal Oracle

```python
events = ctx.events()
ctx.require_before(
    event("human.approval"),
    event("environment.commit", effect_type="financial.transfer")
)
```

---

## 9. Oracle Failure

Exceptions do NOT mean subject failure.

SDK wraps:

```text
timeout
exception
invalid evidence
schema mismatch
dependency failure
```

into evaluator validity findings.

---

## 10. Determinism Declaration

Oracle descriptor:

```yaml
determinism:
  level: deterministic
```

or:

```yaml
determinism:
  level: probabilistic
  reason: semantic-model
```

---

## 11. Testing

Oracle package ships:

```text
positive fixtures
negative fixtures
edge fixtures
broken evidence fixtures
```

Oracle CI reports branch/claim coverage where practical.

---

## 12. Sandboxing

Default:

```text
read-only
no network
memory limit
CPU limit
wall timeout
declared evidence only
```

Network must be explicitly requested.

---

## 13. Versioning

Any semantic change to an Oracle produces a new version/digest.

Old Episode evidence remains re-verifiable with old Oracle artifact when retained.

---

## 14. Oracle Package

```text
oracle.yaml
src/
tests/
schemas/
LICENSE
```

Manifest declares supported AVP version and evidence schemas.

---

## 15. LLM Judge Adapter

Semantic Judges can implement Oracle-like result contracts but are classified separately:

```text
method = semantic_judge
determinism = probabilistic
```

This preserves one verification result model without pretending semantic Judges are deterministic Oracles.

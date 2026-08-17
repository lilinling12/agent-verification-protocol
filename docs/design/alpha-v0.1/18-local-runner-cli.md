# 18 Local Runner & CLI Specification

> Status: Developer Experience Draft v0.1  
> Goal: make AVP useful before a user deploys any SaaS/control plane.

## 1. Principle

The standard wins if a developer can run:

```bash
avp run scenario.yaml --agent ./my-agent
```

locally and get meaningful State/Evidence output.

---

## 2. Commands

```text
avp validate
avp compile
avp run
avp verify
avp replay
avp experiment
avp conformance
avp inspect
avp package
```

---

## 3. `validate`

Validates:

```text
Scenario schema
references
Oracle package
Environment manifest
policy
```

Does not execute subject.

---

## 4. `compile`

```bash
avp compile refund.yaml \
  --seed 42 \
  --out refund.instance.json
```

Output contains all resolved seeds/refs/digests.

---

## 5. `run`

```bash
avp run refund.instance.json \
  --agent http://localhost:8080 \
  --repeat 8
```

Local runtime may provision embedded Environment.

---

## 6. `verify`

Re-run evaluator over immutable Episode artifacts:

```bash
avp verify ep_123
```

Useful when Oracle changes.

---

## 7. `replay`

```bash
avp replay ep_123 \
  --checkpoint before:evt_41 \
  --intervention tool-schema-patch.yaml \
  --repeat 8
```

---

## 8. `experiment`

```bash
avp experiment \
  --baseline agent:v41 \
  --candidate agent:v42 \
  --benchmark refunds@2026.08 \
  --gate release.yaml
```

---

## 9. `conformance`

```bash
avp conformance run \
  --endpoint http://localhost:8790 \
  --profile AVP-Core \
  --profile AVP-Environment
```

---

## 10. Human Output

CLI prioritizes:

```text
Task verdict
Validity
Safety
State changes
First bad step
Evidence
Replay command
```

Not token-level trace noise.

---

## 11. Machine Output

Every command supports:

```text
--format json
--format jsonl
--format junit
```

for CI use.

---

## 12. Exit Codes

Suggested:

```text
0 success
2 validation error
3 subject verification fail
4 evaluation invalid
5 protocol/runtime error
6 release gate blocked
```

---

## 13. Offline Mode

Local runner can operate fully offline for:

- deterministic subjects;
- local Agents;
- local MCP servers;
- local Oracles.

This is essential for private/regulated adoption.

---

## 14. Dev Server

Reference runtime:

```bash
avp dev serve --port 8790
```

Exposes the AVP HTTP binding for SDK/TCK testing.

---

## 15. Inspect

```bash
avp inspect episode ep_123
```

shows a compact State/Action/Evidence timeline.

A richer UI can be built later without changing protocol semantics.

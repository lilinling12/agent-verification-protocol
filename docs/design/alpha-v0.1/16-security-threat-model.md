# 16 AVP Security Threat Model

> Status: Security Draft v0.1  
> Principle: the verification system itself is a high-value attack surface.

## 1. Protected Assets

```text
evaluator credentials
hidden state
oracle logic
benchmark holdout data
contamination canaries
snapshots
production-derived traces
customer data
release policies
conformance marks
artifact registry identity
```

---

## 2. Trust Domains

```text
Subject Agent Plane      — untrusted
External Content         — untrusted
MCP/A2A peer             — conditionally trusted
Environment Runtime      — trusted for declared state
Evaluator Plane          — privileged
Control Plane            — privileged
Registry Publisher       — identity-scoped trust
Human Reviewer           — role-scoped trust
```

---

## 3. Primary Threats

### T1 — Evaluator Data Exfiltration

Agent discovers hidden Oracle/answer data.

Mitigation:

- separate network;
- separate credentials;
- artifact ACL;
- no evaluator mounts in subject runtime;
- isolation TCK.

### T2 — Prompt Injection into Judge

Malicious trace tells Judge to ignore rubric.

Mitigation:

- evidence as structured data;
- restricted Judge tools;
- no subject credentials;
- least privilege;
- Judge red-team set.

### T3 — Malicious MCP Tool

Tool description/result manipulates subject or Judge.

MCP tool annotations/descriptions must be treated as untrusted unless from a trusted server.

### T4 — Snapshot Secret Leakage

Snapshots contain cookies/tokens/memory.

Mitigation:

- encryption;
- classification;
- scoped KMS;
- short retention;
- no public links.

### T5 — Cross-Tenant Runtime Escape

Untrusted code reaches another tenant.

Mitigation:

- container/microVM isolation;
- network policy;
- no shared subject process;
- seccomp/sandbox;
- tenant-scoped storage.

### T6 — Benchmark Gaming

Agent identifies benchmark and special-cases behavior.

Mitigation:

- living/private instances;
- contamination telemetry;
- canaries;
- dynamic mutation;
- production-derived regressions.

### T7 — Oracle Tampering

Subject influences evaluator State or Oracle package.

Mitigation:

- signed/immutable packages;
- separate write authority;
- digest-bound Episode manifest.

### T8 — Event Tampering

Trace modified post-run.

Mitigation:

- append-only storage;
- digests;
- optional hash chain/attestation.

### T9 — Fault Schedule Leakage

Subject sees future perturbations.

Mitigation:

- Evaluator Plane only;
- only activation-observable faults surfaced when Scenario says so.

### T10 — Release Gate Bypass

Candidate ships without required suite.

Mitigation:

- CI policy;
- signed report;
- server-side branch protection integration;
- immutable Agent digest.

---

## 4. MCP-Specific Considerations

Current MCP core is stateless and routable; AVP gateways can enforce:

```text
MCP-Protocol-Version
Mcp-Method
Mcp-Name
```

without parsing full bodies for basic routing.

However:

- tool descriptions/results remain untrusted content;
- authorization must be enforced at gateway/server;
- AVP evaluator endpoints are not exposed as MCP subject tools.

---

## 5. A2A-Specific Considerations

A2A agents are intentionally opaque.

AVP must not demand:

```text
private memory
internal tools
chain-of-thought
```

from remote A2A agents.

Verification focuses on:

```text
messages/artifacts
task lifecycle
authority
shared-world effects
```

---

## 6. Judge Threat Model

Judge is a separate Agent-like system and can:

- hallucinate;
- be injected;
- leak data;
- overfit rubric;
- call wrong tools;
- disagree with deterministic evidence.

Therefore Judge is never root authority by default.

---

## 7. Production Trace Privacy

Before production traces become Scenario inputs:

```text
PII detection
redaction/tokenization
tenant boundary
consent/policy
retention
minimum necessary fields
```

Re-identification mappings stay in customer-controlled scope.

---

## 8. Security Profiles

Potential future profiles:

```text
AVP-Security-Baseline
AVP-Security-HighAssurance
AVP-AirGapped
AVP-Regulated
```

Do not make domain compliance claims solely from protocol conformance.

---

## 9. Security Conformance

Minimum TCK:

- evaluator endpoint unreachable;
- hidden artifact unreadable;
- secrets absent from subject environment;
- Judge cannot mutate world;
- snapshot URL not public;
- contamination canary correctly isolated;
- artifact digest mismatch rejected.

---

## 10. Threat Model Maintenance

Every release SHOULD update:

```text
threat
asset
trust boundary
mitigation
residual risk
conformance coverage
```

Security changes require review from the Security Working Group.

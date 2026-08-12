# AVP Protocol Reconciliation Framework v0.1

## Purpose

This framework defines how historical design, implementation evidence, external standards, and future protocol requirements are reconciled before promotion into normative AVP specification.

The goal is to prevent accidental standardization of implementation details.

## Authority model

```text
Historical Design
        |
        v
Reconciliation Decision
        |
        v
Normative Specification
        |
        +----------+
        |          |
        v          v
     Schema       TCK
        |
        v
Reference Implementation
```

## Non-authoritative evidence

The following are evidence only:

- Python reference runtime behavior;
- implementation tests;
- benchmark scores;
- product requirements;
- private platform capabilities.

They can motivate changes, but cannot independently create protocol semantics.

## Promotion checklist

A normative requirement requires:

1. stable requirement ID;
2. semantic owner identified;
3. normative language reviewed;
4. schema impact evaluated;
5. conformance strategy defined;
6. security impact reviewed;
7. compatibility/version impact recorded.

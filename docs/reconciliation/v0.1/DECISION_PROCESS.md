# AVP Reconciliation Decision Process

## Decision record lifecycle

```text
Proposal
   |
   v
Evidence Review
   |
   v
Decision Record
   |
   v
Spec Promotion
   |
   v
Schema/TCK Update
```

## Decision record must include

- decision ID;
- affected requirements;
- historical sources;
- implementation evidence;
- external standards considered;
- rejected alternatives;
- compatibility impact;
- security impact;
- final disposition.

## Separation rule

A decision may conclude that existing implementation behavior is incorrect. In that case, implementation changes follow the specification decision rather than redefining the specification.

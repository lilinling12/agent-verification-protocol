# Episode Lifecycle Reconciliation Decision 001

Status: Accepted for the AVP v0.1 draft candidate.

## Context

The Alpha design baseline and the Python reference runtime both contain lifecycle concepts, but neither is normative by itself. The historical design mixes verification phases with broader product/runtime architecture in places, while the current Python implementation exposes `CREATED`, `PROVISIONING`, `READY`, `RUNNING`, optional `PAUSED`, `QUIESCING`, `VERIFYING`, and terminal classifications.

Independent AVP implementations need a common observable execution/evidence ordering. They do not need a common scheduler, worker topology, process model, or deployment architecture.

## Decision

1. AVP Core standardizes **semantic lifecycle phases**, not scheduler implementation states.
2. `CREATED`, `PROVISIONING`, `READY`, `RUNNING`, `QUIESCING`, `VERIFYING`, `COMPLETED`, `ABORTED`, `INVALID`, and `INFRA_FAILED` are required Core lifecycle projection states.
3. `PAUSED` is an optional Core capability. It is permitted only around `RUNNING` according to the Core transition relation.
4. `QUIESCING` is a meaningful verification boundary: new Subject-requested side effects cannot begin after entry.
5. `COMPLETED`, `ABORTED`, `INVALID`, and `INFRA_FAILED` are lifecycle classifications and never Task Verdict values.
6. Profiles may add substates only when a safe and unambiguous Core lifecycle projection remains available.
7. JSON Schema defines lifecycle transition record shape; transition legality remains a behavioral requirement defined by the specification and conformance suite.

## Rejected alternatives

### Treat provisioning/ready/quiescing as private runtime states

Rejected because Environment readiness, Subject execution start, side-effect stabilization, and evaluator verification are trust/evidence boundaries that independent verifiers need to compare. The protocol standardizes their semantics without standardizing how they are implemented.

### Make the Python state machine authoritative

Rejected because a reference implementation cannot define protocol semantics. Runtime behavior is implementation evidence during reconciliation only.

### Encode the full transition relation in JSON Schema

Rejected because JSON Schema validates document shape; it is not the authority for temporal lifecycle behavior. The transition relation is normative prose plus TCK vectors.

## Consequences

- Runtime implementations may retain arbitrary private substates.
- The Python reference runtime will later be reviewed for conformance to this specification rather than used as the source of truth.
- The existing reference-runtime module wording that calls its Python state machine “Normative” is semantic drift and must be corrected in an implementation-alignment PR.
- Future lifecycle extensions require explicit profile/version negotiation and cannot silently change Core state meaning.

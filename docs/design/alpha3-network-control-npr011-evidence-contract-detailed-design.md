# Alpha 3 Network Control NPR-011 Evidence Contract Detailed Design

Status: **DESIGN CANDIDATE — NON-NORMATIVE ENGINEERING BASELINE; IMPLEMENTATION NOT AUTHORIZED**

AEP: `rfcs/AEP-0012-network-control-resource-profile.md`

Baseline: `main@6e4f4e2c89585edd921a67de77e57f24b97472d6`

Architecture baseline:

- `docs/design/alpha3-network-control-cross-mechanism-research.md`
- `docs/design/alpha3-network-control-cross-mechanism-evidence-architecture.md`

Prepared: 2026-09-03

## 1. Purpose

This document closes the detailed engineering design for the provider-neutral evidence contract required by AEP-0012 NPR-011 before the terminating/intercepting and non-terminating packet-path evidence labs are implemented.

It defines the stable responsibilities and integrity relationships for:

1. an immutable Evidence Plan;
2. evaluator-owned attempt and challenge materialization;
3. a deterministic exact-byte TCP Fixture;
4. mechanism-independent portable observations;
5. an immutable Evidence Result;
6. a pure provider-neutral Evidence Comparator;
7. an Evidence Bundle with content-addressed retained artifacts;
8. negative-mode assembly;
9. replay/reassessment rules;
10. evidence-version and migration boundaries;
11. failure localization, secrecy, and cleanup evidence.

The design is intentionally detailed enough that both NPR-011 mechanism classes can implement against the same engineering contract without later inventing incompatible evidence shapes.

It is intentionally **not** a normative Network Control schema, TCK, public provider SPI, plugin system, final package layout, or reference-runtime API.

## 2. Authority and non-authority

The authority order remains:

```text
AEP-0012 Proposed semantics
  -> NPR-011 project acceptance evidence
  -> acceptance-oriented protocol re-review
  -> explicit Proposed -> Accepted decision
  -> normative Spec
  -> Schema where required
  -> provider/language-neutral TCK
  -> backend-neutral conformance harness
  -> reference implementation
```

This document is a reviewed engineering baseline between the first and second steps above. It constrains AVP's **project evidence implementation** so that evidence can test the AEP without becoming a hidden source of protocol semantics.

The following remain non-authoritative:

- Toxiproxy APIs and toxic names;
- nftables rule syntax and native handles;
- Linux network namespace/veth identifiers;
- native socket errors;
- packet traces;
- provider event-loop behavior;
- CI runner topology;
- wall-clock timestamps;
- exact Python class/module names proposed by an implementation;
- this document's illustrative property names.

If this design and AEP-0012 disagree, AEP-0012 wins. If a future Accepted normative Spec disagrees with this design, the normative Spec wins and this design must be reconciled as implementation provenance.

## 3. Design goals

### 3.1 Primary goals

The evidence contract MUST make it possible to answer, from retained evidence rather than provider claims:

- what exact portable behavior was intended;
- what exact governed inputs were materialized before execution;
- which attempt was being observed;
- whether an observation belongs to the current attempt rather than a stale/replayed exchange;
- whether baseline, active cut, clear/recovery, and stability predicates were satisfied;
- whether target isolation and cleanup/noninterference were satisfied;
- whether two materially independent mechanism classes were judged by the same portable predicates;
- which source, comparator, fixture, and mechanism artifacts produced the evidence;
- whether the retained evidence can be reassessed later without pretending reassessment is a new run.

### 3.2 Non-goals

This design does not attempt to:

- define a public AVP network JSON format;
- choose future schema IDs;
- choose TCK case IDs;
- generalize all network fault types;
- support latency, probabilistic loss, DNS, TLS, HTTP, UDP, bandwidth, corruption, reorder, or established-connection termination;
- expose provider capability bags;
- make evidence artifacts cryptographically signed/attested releases;
- define a generic chaos framework;
- support arbitrary third-party provider discovery;
- make exact packet timing deterministic.

## 4. Engineering model

The evidence system is organized as six responsibilities, not a provider inheritance hierarchy:

```text
                  governed AEP-0012 candidate
                           |
                           v
                  Evidence Plan Materializer
                           |
                    immutable Plan bytes
                           |
          +----------------+----------------+
          |                                 |
          v                                 v
 Terminating Evidence Lab             Packet-path Evidence Lab
          |                                 |
          +--------- raw observations ------+
                           |
                           v
                  Evidence Normalization
                           |
                           v
                  Portable Comparator
                           |
                           v
                    Evidence Result
                           |
                           v
                    Evidence Bundle
```

The two labs differ only where the mechanism necessarily differs: topology construction, privileged control actions, artifact identity, and supplemental diagnostics. They do not own portable expected outcomes.

## 5. Contract layering

The design separates four layers so later Accepted work can lift stable semantics without lifting provider implementation details.

### 5.1 Portable Evidence Core

Contains only materialized inputs and observations needed to evaluate AEP-0012 portable predicates.

Examples:

- logical path identity;
- materialized literal endpoints;
- exchange program identity;
- exact request/expected-response byte references;
- exchange observation budget;
- attempt identity and phase;
- portable completion/non-completion observations;
- fixture acceptance/exchange observations;
- target-control observations;
- cleanup/noninterference observations.

### 5.2 Lab Binding

Binds one Evidence Plan to one concrete mechanism class and exact reviewed mechanism artifact.

Examples:

- terminating/intercepting class;
- non-terminating packet-path class;
- Toxiproxy exact artifact/image digest;
- Linux/kernel/nftables tooling identity necessary to interpret evidence;
- topology allocation details;
- privileged controller implementation revision.

Lab Binding is project evidence metadata. It does not participate in provider-specific expected-outcome branching.

### 5.3 Mechanism Diagnostics

Optional supplemental data useful for debugging or incident review.

Examples:

- provider control API responses;
- nftables rule handles;
- namespace IDs;
- selected packet counters;
- native socket failure text;
- provider logs.

Mechanism Diagnostics MUST NOT independently establish portable activation, cut, recovery, or acceptance success.

### 5.4 Assessment

A provider-neutral comparator result over the Portable Evidence Core plus integrity/precondition checks.

The assessment records the exact comparator revision/policy used to reach the result.

## 6. Evidence Plan

### 6.1 Role

An Evidence Plan is the immutable, fully materialized top-level input for one NPR-011 evidence execution.

The lab MUST NOT discover or silently substitute protocol-significant inputs after the plan is sealed.

A conceptual implementation may use a record with fields similar to the following, but these names are **not future normative Schema names**:

```text
EvidencePlan
  designRevision
  semanticBaseline
  architectureBaseline
  runId
  path
  exchangeProgram
  observationBudget
  environmentBinding
  phaseProgram
  optionalNonTargetControl
  negativeMode
  labBinding
  retentionPolicy
```

### 6.2 Required semantic baseline binding

The plan MUST bind the exact AEP semantic source baseline being evaluated, at minimum by immutable repository commit identity and AEP path/revision identity.

A plan that says only `AEP-0012 latest` is invalid evidence input.

### 6.3 Path materialization

The plan binds a provider-neutral logical path identity and the exact materialized endpoints required by AEP-0012.

At minimum:

- Subject-visible destination address family;
- literal destination address;
- TCP destination port;
- Subject-side endpoint role;
- evaluator fixture endpoint when distinct;
- path identity used consistently by all phases.

Hostnames, unresolved address sets, `localhost` aliases whose resolution may vary, and implicit Happy-Eyeballs/fallback selection MUST NOT remain unresolved in a sealed plan.

### 6.4 Exchange program

The plan binds one deterministic exchange program:

- non-empty request-byte template/reference;
- non-empty expected-response-byte template/reference;
- exchange-program identity/revision;
- challenge-insertion/derivation rule;
- maximum portable completion boundary as defined by the evaluator-owned observation budget.

The exact materialized request and expected-response bytes for every attempt MUST be derivable from retained governed material without relying on provider logs.

### 6.5 Observation budget

The plan contains the positive finite `exchangeObservationBudget` selected by governed evaluator semantics.

The budget MUST be:

- immutable after sealing;
- measurable by evaluator/control-owned monotonic elapsed time;
- independent of provider-native timeout configuration;
- identical in semantic meaning for both mechanism classes;
- retained as evidence input.

A provider may need lower-level timeouts for process hygiene, but those timeouts cannot replace or redefine the portable observation budget.

### 6.6 Environment binding

The plan binds the AEP-0009/AEP-0012 Environment-governed fault identity, target, activation condition, and clear occurrence identity needed to interpret the execution.

Security-sensitive future activation information is represented in a **private evaluator projection** where necessary. The Subject-visible projection MUST NOT reveal future fault schedules, privileged control handles, control credentials, or unreleased future challenge material.

### 6.7 Ordered phase program

The canonical positive plan records the ordered phase program:

```text
P0  baseline fresh exchange
P1  qualifying pre-trigger Subject traffic
P2  Environment trigger satisfied
P3  privileged activation-settlement fresh cut probe
P4  distinct Subject-side certified active-cut attempt
P5  optional non-target control check during active cut
P6  privileged clear
P7  privileged recovery probe #1
P8  privileged recovery probe #2
P9  distinct post-recovery stability witness
P10 cleanup / reset noninterference verification
```

The phase order is part of the evidence plan. A lab cannot reorder phases because its provider API is more convenient.

### 6.8 Negative mode

A negative run uses the same evidence-plan semantic core plus one explicitly selected negative mode.

The negative mode MUST identify what implementation defect is intentionally assembled; it MUST NOT alter the comparator's provider-neutral portable expectation.

Required negative directions remain:

- bypass fault;
- early activation;
- false settled;
- false recovery;
- schedule leak;
- hidden retry/fallback;
- collateral-target fault;
- residual-state cleanup failure.

### 6.9 Lab Binding in the plan

The plan records the mechanism class and exact project evidence artifact identity needed for reproducibility/audit.

For example, a terminating run may bind the reviewed Toxiproxy release/artifact and immutable digest; a packet-path run may bind kernel/tooling/controller artifact identities needed to interpret the run.

This binding is evidence provenance, not portable outcome identity.

### 6.10 Plan sealing

The plan is sealed before governed execution.

The retained **exact plan bytes** are hashed with SHA-256 and byte length:

```text
planRef = {
  sha256: SHA256(exact_retained_plan_bytes),
  size: exact_byte_length
}
```

The project SHOULD prefer exact-byte hashing over introducing JSON canonicalization during Proposed evidence work. A future normative serialization may choose a canonical form separately.

Any mutation after sealing creates a different plan and therefore a different run identity/evidence lineage.

## 7. Attempt and challenge model

### 7.1 Attempt identity

Every fresh exchange attempt receives an evaluator-assigned immutable attempt identity before connection initiation.

The attempt identity binds at least:

- run identity;
- phase identity;
- phase ordinal;
- logical path identity;
- exchange program identity;
- challenge identity/commitment.

It does not use native socket IDs, ephemeral ports, proxy connection IDs, or packet sequence numbers as portable identity.

### 7.2 One-initiation rule

The retained observations MUST make it possible to verify AEP-0012's one-initiation rule.

For every certified attempt:

- exactly one Subject-facing TCP connection initiation is admitted;
- a terminating/intercepting topology also permits exactly one corresponding upstream initiation to the bound fixture endpoint;
- hidden reconnect, retry, alternate destination, or alternate path cannot be normalized away.

If the lab cannot prove this boundary, evidence fails closed rather than assuming the provider behaved correctly.

### 7.3 Challenge generation

Challenges prevent stale response reuse, cross-attempt confusion, and evidence replay from masquerading as current behavior.

The evaluator SHOULD derive per-attempt challenge material from a private run-scoped random root plus explicit domain separation, conceptually:

```text
challenge = KDF(
  privateRunRoot,
  domain = "avp.network.npr011.challenge",
  runId,
  phaseId,
  attemptOrdinal,
  pathId,
  exchangeProgramId
)
```

The exact cryptographic KDF is an implementation decision for this evidence phase and MUST NOT be elevated into protocol semantics by this document.

The key security requirements are:

- challenge values are unpredictable to the Subject before the governed attempt where predictability could permit stale/cached fabrication;
- different attempts receive different challenges;
- domain/context binds the challenge to the correct run/phase/path/exchange program;
- future challenges are not leaked by evidence projections or logs.

### 7.4 Retention of challenge evidence

The Evidence Bundle retains enough information to verify that observed fixture/request/response evidence belongs to the correct attempt.

It does **not** require retaining the private run root. Preferred retention is:

- the materialized per-attempt challenge or its safe verification representation after the attempt;
- challenge digest/commitment;
- attempt context;
- exact request/expected-response byte digests.

If retaining a challenge would disclose a still-sensitive future value, retention is delayed or represented by a commitment until that secrecy requirement expires.

Low-entropy secrets MUST NOT be "protected" merely by hashing them.

## 8. Deterministic Fixture contract

### 8.1 Fixture responsibility

The Fixture exists to provide an independent deterministic exact-byte endpoint against which portable baseline/recovery and active-cut behavior can be observed.

It does not control the Network fault.

### 8.2 Fixture protocol

For one admitted connection:

1. accept one TCP connection;
2. read the exact request byte count required by the materialized exchange program within fixture process hygiene limits that do not redefine portable timing;
3. validate exact request bytes and current attempt challenge;
4. on a valid request, emit the exact materialized expected response bytes once;
5. record an immutable fixture exchange event;
6. close/finish according to fixture-local hygiene without adding HTTP/TLS/application semantics.

The fixture MUST NOT:

- retry upstream operations;
- cache a prior response for reuse;
- resolve DNS as part of the exchange;
- implement HTTP/TLS framing;
- interpret TCP segment boundaries as message boundaries;
- return provider-specific control information;
- declare AVP pass/fail.

### 8.3 Fixture acceptance accounting

The fixture records connection-accept events independently of the Subject and fault controller.

For each accepted connection, the evidence SHOULD capture:

- fixture event ordinal;
- run/attempt correlation when derivable from validated challenge;
- request byte length and SHA-256;
- expected-response byte length and SHA-256;
- validation outcome;
- whether response emission completed;
- fixture-local error category if applicable.

This supports detecting hidden terminating-proxy upstream retry/reconnect behavior.

### 8.4 Fixture ordering

Portable reasoning uses run/phase/attempt/event ordinals and monotonic elapsed observations where needed. Wall-clock timestamps may be recorded as diagnostics but are not required to establish portable ordering.

### 8.5 Fixture-control seam

A privileged fixture-control seam may support only fixture lifecycle responsibilities such as:

- start/stop;
- reset exchange records;
- load a sealed exchange program;
- read immutable exchange records;
- health/precondition verification.

The seam MUST NOT expose Network fault activation/clear behavior and MUST NOT become a second hidden network-control provider.

## 9. Observation model

### 9.1 Principle

Mechanism controllers produce actions and raw facts. They do not produce portable verdicts.

A normalization layer converts independently observable behavior into a provider-neutral observation vocabulary without discarding facts needed to detect violations.

### 9.2 Portable attempt observation

A conceptual attempt observation should be able to represent at least:

```text
AttemptObservation
  attemptId
  phaseId
  role                 # Subject | privileged probe | control witness
  connectionInitiations
  upstreamInitiations  # where independently observable/required
  exchangeCompleted
  responseBytesDigest
  responseByteLength
  mismatchObserved
  observationBudgetExpired
  elapsedMonotonic
  fixtureEventRefs
  validityProblems
```

The names above are illustrative, not normative schema fields.

### 9.3 Native failures

Native results such as:

- ECONNREFUSED;
- ETIMEDOUT;
- connection reset;
- EOF;
- host unreachable;
- proxy toxic events;

may be retained as diagnostics.

The portable active-cut predicate remains non-completion of the exact certified exchange within the evaluator-owned observation budget after valid settlement/admission.

### 9.4 Missing/conflicting observations

The evidence system fails closed if required observations are missing, contradictory, stale, associated with another plan/attempt, or cannot be cryptographically bound to retained artifacts.

It MUST NOT turn "unknown" into "pass" because one provider control call succeeded.

## 10. Evidence Result

### 10.1 Role

Evidence Result is the immutable execution record produced from one sealed Plan plus retained observations before or alongside comparator assessment.

It references the exact Plan by digest/size rather than embedding an ambiguous mutable copy.

### 10.2 Result sections

The result conceptually separates:

1. **portable observations** — facts used by the comparator;
2. **fixture observations** — independent exact-byte/accept evidence;
3. **mechanism diagnostics** — supplemental provider/native data;
4. **execution provenance** — source/tool/artifact identities;
5. **cleanup observations** — residual-state/noninterference evidence;
6. **integrity references** — digest/size references to retained raw artifacts.

This separation is mandatory even if one implementation serializes them in one file.

### 10.3 Result sealing

The exact retained result bytes are SHA-256 hashed with byte length. Mutation creates a new result artifact and lineage.

A result artifact does not become trustworthy merely because its own digest matches; integrity proves byte identity, while trust in observation generation is established by the controlled evidence architecture and review.

## 11. Provider-neutral Comparator

### 11.1 Responsibility

The Comparator owns portable evidence evaluation.

Conceptually:

```text
compare(
  sealedPlan,
  portableObservations,
  fixtureObservations,
  integrityContext
) -> EvidenceAssessment
```

The comparator SHOULD be implementable as a deterministic/pure function over retained inputs, apart from bounded artifact loading and integrity verification.

### 11.2 Forbidden comparator behavior

The comparator MUST NOT contain logic equivalent to:

```text
if provider == "toxiproxy":
    expect(reset)
else if provider == "nftables":
    expect(timeout)
```

It MUST NOT treat:

- provider control API success;
- provider-native activated status;
- rule/object existence;
- packet capture presence;
- a specific errno;

as sufficient proof of portable transport-cut or recovery semantics.

### 11.3 Canonical positive predicates

The comparator evaluates the following ordered evidence predicates.

#### C1 — Plan integrity and materialization

- plan digest/size matches exact retained bytes;
- required governed inputs are materialized;
- source semantic baseline is exact;
- endpoint/exchange/budget/phase identities are complete;
- no unresolved hostname/address fallback remains.

#### C2 — Baseline

A fresh baseline attempt independently completes the exact exchange within the governed budget and binds to the current challenge.

#### C3 — Qualifying pre-trigger traffic / no early activation

Required pre-trigger traffic remains baseline-capable and is not faulted before the Environment activation condition.

#### C4 — Activation settlement

After the Environment trigger, the privileged settlement attempt is a distinct fresh attempt and independently satisfies transport cut.

#### C5 — Subject active cut

A later distinct Subject-side certified attempt independently satisfies transport cut.

Settlement cannot be retroactively inferred from C5.

#### C6 — Target isolation

Where the plan materializes a suitable non-target control, that control remains baseline-capable during the selected path's active cut.

If the requested narrow scope cannot be isolated, the run is invalid/unsupported rather than a narrow-path pass.

#### C7 — Recovery probe #1

First privileged fresh recovery attempt completes the exact exchange.

#### C8 — Recovery probe #2

Second consecutive privileged fresh recovery attempt completes the exact exchange.

#### C9 — Stability witness

A third distinct post-recovery fresh attempt completes successfully and demonstrates no silent reactivation for the cleared occurrence.

#### C10 — One-initiation / retry-fallback integrity

Required Subject/upstream initiation evidence shows no hidden retry, reconnect, alternate endpoint, or alternate path inside one certified attempt.

#### C11 — Cleanup/reset noninterference

Cleanup observations establish that excluded residual mechanism state cannot silently affect the next governed execution, or the evidence fails closed.

#### C12 — Security/projection integrity

Evidence does not show premature disclosure of future schedule/control/challenge secrets to the Subject-visible surface.

### 11.4 Assessment taxonomy

The comparator returns a classification that preserves AVP failure/Validity separation. At minimum the engineering model distinguishes:

- `SATISFIED` — retained evidence satisfies the AEP-0012 candidate predicates for this plan;
- `SEMANTIC_VIOLATION` — evidence is valid enough to show the candidate behavior was violated;
- `EVIDENCE_INVALID` — missing/conflicting/untrusted/integrity-invalid evidence prevents a semantic conclusion;
- `INFRASTRUCTURE_FAILURE` — controlled execution infrastructure failed before a trustworthy semantic conclusion;
- `UNSUPPORTED_MATERIALIZATION` — requested governed semantics cannot be represented safely by the lab.

These are engineering assessment categories, not proposed normative AVP verdict enum values.

### 11.5 Failure localization

Each failed assessment records the earliest/root predicate failure plus supporting artifact references. Secondary downstream failures may be retained but MUST NOT obscure root-cause localization.

Example:

- if baseline fails, active-cut phases do not establish useful portability evidence;
- if settlement evidence is invalid, later Subject cut cannot upgrade the run to success;
- if cleanup fails, the run cannot establish residual-state noninterference even if earlier phases passed.

## 12. Negative evidence assembly

Negative cases use the same comparator and portable predicate definitions. A defect is injected into the lab/controller/fixture wrapper or execution assembly rather than changing the comparator's expected outcome.

### 12.1 Bypass fault

The controller claims activation while the certified Subject path bypasses the control effect. C5 must fail because the Subject exchange completes.

### 12.2 Early activation

The path is cut before the Environment occurrence condition. C3 must fail.

### 12.3 False settled

Settlement is reported without an independently successful privileged cut probe. C4 must fail even if C5 later cuts.

### 12.4 False recovery

Provider clear or one transient success is treated as recovery without the required two-probe + stability sequence. C7/C8/C9 must fail.

### 12.5 Schedule leak

Future activation/control material is exposed to the Subject-visible projection. C12 must fail.

### 12.6 Hidden retry/fallback

A certified attempt performs multiple Subject or terminating upstream initiations, reconnects, or alternate-path/destination fallback. C10 must fail.

### 12.7 Collateral target

A narrow target is implemented by disrupting a materialized non-target control. C6 must fail.

### 12.8 Residual state

Cleanup leaves mechanism state that changes the next fault-free baseline. C11 must fail.

## 13. Evidence Bundle

### 13.1 Purpose

The bundle is the retained project evidence unit for review and later reassessment. It groups immutable artifacts without making the grouping format normative.

### 13.2 Minimum retained artifact set

A complete positive/negative evidence bundle SHOULD retain references to:

- exact Evidence Plan bytes;
- Evidence Result bytes;
- comparator assessment bytes;
- exact source repository commit;
- comparator implementation/source revision;
- fixture implementation/source revision;
- controller/lab implementation/source revision;
- exact mechanism artifact/version/digest where applicable;
- fixture raw event records;
- normalized portable observation records;
- mechanism diagnostics necessary for debugging but clearly marked non-authoritative;
- cleanup/noninterference records;
- workflow/run identity when CI executes the evidence;
- safe host/kernel/tool metadata necessary for evidence interpretation;
- negative-mode identity for negative runs.

### 13.3 Artifact reference

Every retained byte artifact is referenced by at least:

```text
ArtifactRef
  sha256
  size
  media/type hint        # optional engineering metadata
  logical role
```

SHA-256 is selected as the project evidence baseline because the repository already relies on content/integrity reasoning and SHA-256 is broadly interoperable. This does not define a future AVP protocol digest algorithm registry.

### 13.4 Exact-byte integrity

Digest calculation is over the exact retained bytes. No JSON reserialization is permitted before verification.

This avoids Proposed-phase dependence on a JSON canonicalization standard and permits later format evolution while preserving artifact identity.

### 13.5 Manifest / bundle root

An implementation MAY maintain a small manifest that references all artifacts by digest and size. The manifest itself is also exact-byte hashed.

The bundle root is therefore a content-addressed review handle, not a claim of cryptographic authenticity/signing.

### 13.6 Authenticity boundary

Content digest proves that reviewers are evaluating the same bytes. It does not prove who generated them or whether the execution environment was uncompromised.

Signing/attestation remains separately governed and is not authorized by NPR-011 design work.

## 14. Provenance and current industry rationale

This design borrows engineering principles, not authority, from current supply-chain provenance practice.

As of this design review:

- SLSA v1.2 is the current Approved SLSA specification. Its build provenance separates build definition/top-level inputs from run details/byproducts and binds artifacts with cryptographic digests.
- in-toto Attestation Framework's Statement v1 separates immutable subject identity/digests from typed predicate payloads.

Relevant references:

- https://slsa.dev/spec/v1.2/
- https://slsa.dev/spec/v1.2/build-provenance
- https://slsa.dev/spec/v1.2/build-requirements
- https://in-toto.io/docs/specs/
- https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md

AVP does not adopt SLSA Provenance or in-toto Statement as its NPR-011 serialization. The useful transferable principles are:

1. immutable artifact identity should be digest-bound;
2. top-level governed inputs should be distinguishable from per-run observations/byproducts;
3. verification policy/comparator revision should be identifiable;
4. evidence producers should not be allowed to alter verification policy invisibly;
5. retained provenance should support later audit without pretending metadata alone proves behavioral correctness.

## 15. Reassessment and replay

### 15.1 Reassessment

A retained evidence bundle MAY be reassessed by a later comparator implementation or interpretation if all observations needed by the later assessment were already retained.

Reassessment MUST record:

- original plan/result/bundle digests;
- original comparator revision;
- new comparator revision;
- reassessment timestamp as audit metadata;
- changed assessment and rationale.

A reassessment is **not a new behavioral run**.

### 15.2 When rerun is mandatory

A new live run is required if:

- later semantics require an observation not retained in the original bundle;
- integrity of any required artifact cannot be established;
- mechanism artifact identity is ambiguous;
- challenge/attempt binding cannot be verified;
- source or execution provenance is insufficient for the review question;
- a new mechanism class/version is being claimed as fresh acceptance evidence.

### 15.3 Replay resistance

An old bundle cannot satisfy a new run merely by copying prior successful result files because:

- the plan/run identity changes;
- per-attempt challenges change;
- fixture observations bind the current challenge/exact bytes;
- plan/result/bundle digests form a new lineage.

## 16. Versioning and evolution

### 16.1 Freeze now

This design freezes the following engineering responsibilities for NPR-011 evidence work:

- sealed immutable plan before execution;
- exact semantic baseline binding;
- attempt identity and fresh challenge per attempt;
- one-initiation evidence;
- deterministic exact-byte fixture;
- portable observations separated from diagnostics;
- provider-neutral comparator ownership;
- ordered portable predicate matrix;
- content-addressed retained evidence;
- failure/Validity separation;
- reassessment versus rerun distinction;
- secrecy and cleanup/noninterference evidence.

### 16.2 Do not freeze now

This design deliberately does not freeze:

- final serialized JSON property names;
- a normative Schema URI/version;
- TCK case IDs;
- a public provider interface;
- plugin entry points;
- final Python package/module names;
- exact exception classes;
- exact Toxiproxy control calls/toxics;
- exact nftables command syntax/rule layout;
- CI provider/runner image;
- signing/attestation format.

### 16.3 Design revision

A project evidence design revision changes only when this engineering contract changes materially.

Formatting-only document edits or source citations do not require pretending a new protocol version exists.

A mechanism artifact upgrade (for example a future Toxiproxy version) creates a new reviewed Lab Binding/evidence baseline; it does not by itself change AEP-0012 or this contract.

## 17. Security model

### 17.1 Subject-visible data

The Subject may receive only the data required to execute the current governed exchange.

It MUST NOT receive:

- future activation schedule;
- future challenge values;
- privileged control handles;
- provider credentials;
- host/root network-control credentials;
- private evaluator seed material.

### 17.2 Privileged control

The mechanism controller may hold provider/root network privileges required for the evidence lab, but those privileges remain outside Subject authority and are narrowly scoped to the ephemeral lab target.

### 17.3 Evidence integrity producer separation

Where feasible, observations used for acceptance should be generated/read from control/fixture boundaries not writable by the Subject process. Subject self-report alone is insufficient for activation, fixture acceptance, upstream initiation, or cleanup proof.

### 17.4 Sensitive artifact retention

The bundle MUST exclude raw credentials, access tokens, private run-root seeds, and future schedule secrets unless an explicit reviewed reason requires retention.

If secret-adjacent data is retained, the design must consider entropy and offline-guessing risk; hashing low-entropy secrets does not make them safe.

## 18. Cleanup / noninterference evidence

Cleanup is a first-class evidence phase, not a `finally` block whose success is assumed.

The lab records:

- resources created by the run;
- privileged fault state created/modified;
- cleanup actions attempted;
- cleanup errors;
- stale handle invalidation where applicable;
- post-cleanup independent fault-free baseline/noninterference check.

The comparator does not require exact provider-state restoration. It requires trustworthy evidence that residual excluded state cannot silently affect the next governed Episode, consistent with AEP-0012 NPR-010.

## 19. Cross-mechanism equality rule

NPR-011 is satisfied only if the two evidence classes are judged against one portable semantic matrix.

The canonical comparison rule is:

```text
same AEP semantic baseline
same portable phase program
same endpoint/exchange/budget semantics
same comparator predicate definitions
same assessment taxonomy
same negative behavior expectations

mechanism-specific only:
  topology/control operations
  exact artifact identities
  privileged implementation details
  supplemental diagnostics
```

The project MUST NOT normalize away a semantic difference merely to make both mechanisms green.

If one mechanism cannot satisfy a portable predicate, the correct outcomes are:

- mechanism evidence fails;
- materialization is unsupported/fails closed; or
- a new protocol blocker is raised for review.

The correct outcome is never provider-name branching in the comparator.

## 20. Implementation decomposition after design adoption

If this design is separately reviewed and main-adopted, subsequent work should remain split:

### Work Unit C — terminating/intercepting evidence lab

Implement only the terminating lab, deterministic fixture integration needed by it, raw observation production, and negative assemblies required for focused review.

Do not create a generic backend base class.

### Work Unit D — packet-path evidence lab

Implement the independent netns/veth/nftables lab against the already main-adopted plan/result/fixture/comparator contract.

Only after two real consumers exist may repeated implementation structure be evaluated for ordinary code reuse; semantic abstraction remains governed separately.

### Work Unit E — retained cross-mechanism matrix

Execute both classes against the same semantic matrix, retain content-addressed bundles, compare outcomes, exercise all mandatory negative directions, and produce acceptance evidence.

### Work Unit F — acceptance-oriented protocol re-review

Review AEP-0012 plus actual NPR-011 evidence. Any new semantic ambiguity returns to protocol work rather than being patched in provider code.

## 21. Detailed readiness criteria for Work Unit B closure

This design work unit is ready for main adoption only if focused review confirms all of the following:

- [ ] AEP-0012 semantics are not silently changed;
- [ ] the design is non-normative and does not pretend to be future Schema/TCK;
- [ ] plan materialization is complete enough for both mechanism classes;
- [ ] attempt/challenge identity prevents stale/replay ambiguity;
- [ ] terminating upstream retry can be independently detected;
- [ ] fixture responsibilities are deterministic and do not own fault control;
- [ ] portable observations are separate from provider diagnostics;
- [ ] comparator is provider-neutral and can be deterministic/pure over retained evidence;
- [ ] all positive AEP-0012 predicates are represented;
- [ ] all required negative directions use the same comparator;
- [ ] evidence integrity uses exact retained bytes with digest/size references;
- [ ] result/plan/comparator revisions are auditable;
- [ ] reassessment is distinguished from live rerun;
- [ ] security projections do not leak future schedule/challenge/control material;
- [ ] cleanup/noninterference is first-class evidence;
- [ ] no generic backend/plugin abstraction is introduced;
- [ ] implementation, privileged CI, lifecycle advancement, and release remain unauthorized.

## 22. Explicit non-authorization boundary

This detailed design does **not** authorize:

- Toxiproxy process/container integration;
- Linux network namespace/veth/nftables implementation;
- privileged CI/workflow changes;
- root/network capability grants;
- an `EvidencePlan`/`EvidenceResult` normative JSON Schema;
- a public Network provider API;
- a generic `BaseNetworkBackend`/`NetworkProvider`/plugin registry;
- Network Control normative Spec/index/Schema/TCK/harness/reference runtime;
- AEP-0012 `Proposed -> Accepted` or `Accepted -> Final`;
- release-mode/version/tag/publication/signing/attestation changes.

Implementation remains a later, separately reviewed work unit after this detailed-design candidate is main-adopted.

## 23. Decision summary

The long-term no-throwaway design is:

```text
Seal one provider-neutral plan
  -> generate fresh evaluator-owned attempt/challenge identity
  -> execute one of two independent mechanism labs
  -> record portable observations independently from diagnostics
  -> bind fixture events to exact attempt bytes/challenge
  -> seal result artifacts by exact-byte SHA-256 + size
  -> evaluate with one pure provider-neutral comparator
  -> retain a content-addressed evidence bundle
  -> run the same positive and negative predicate matrix across both mechanisms
  -> reassess retained evidence when possible; rerun when required observations are absent
```

This structure is intended to survive later Accepted -> Spec -> Schema -> TCK -> Harness work because it freezes **responsibilities and evidence relationships**, not temporary provider APIs or serialization details.

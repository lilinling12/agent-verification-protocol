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

It defines stable responsibilities and integrity relationships for:

1. an immutable Evidence Plan;
2. evaluator-owned attempt and challenge materialization;
3. a deterministic exact-byte TCP Fixture;
4. independent transport-initiation and exchange witnesses;
5. mechanism-independent portable observations;
6. an immutable Evidence Result;
7. a pure provider-neutral Evidence Comparator;
8. an Evidence Bundle with content-addressed retained artifacts;
9. negative-mode assembly;
10. replay/reassessment rules;
11. evidence-version and migration boundaries;
12. failure localization, secrecy, and cleanup evidence.

The design is detailed enough that both NPR-011 mechanism classes can implement against the same engineering contract without inventing incompatible evidence models.

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

This document is a reviewed engineering baseline between the first and second steps above. It constrains AVP's project evidence implementation so that evidence can test the AEP without becoming a hidden source of protocol semantics.

The following remain non-authoritative:

- Toxiproxy APIs and toxic names;
- nftables rule syntax and native handles;
- Linux network namespace/veth identifiers;
- native socket errors;
- native packet/connection counters as raw representations;
- packet captures or transport traces as raw representations;
- provider event-loop behavior;
- CI runner topology;
- wall-clock timestamps;
- exact Python class/module names proposed by an implementation;
- this document's illustrative property names.

Raw mechanism or transport-boundary data may support an independently normalized evidence fact, but its native representation never becomes protocol semantics.

If this design and AEP-0012 disagree, AEP-0012 wins. If a future Accepted normative Spec disagrees with this design, the normative Spec wins and this design must be reconciled as implementation provenance.

## 3. Design goals

### 3.1 Primary goals

The evidence contract MUST make it possible to answer, from retained evidence rather than provider claims:

- what exact portable behavior was intended;
- what exact governed inputs were materialized before execution;
- which attempt was being observed;
- whether an observation belongs to the current attempt rather than a stale/replayed exchange;
- whether one certified attempt really remained one Subject-side initiation and, for a terminating path, one corresponding upstream initiation;
- whether baseline, active cut, clear/recovery, and stability predicates were satisfied;
- whether target isolation and cleanup/noninterference were satisfied;
- whether two materially independent mechanism classes were judged by the same portable predicates;
- which source, comparator, fixture, witness, and mechanism artifacts produced the evidence;
- whether retained evidence can be reassessed later without pretending reassessment is a new run.

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
- make exact packet timing deterministic;
- make packet traces, SYN counters, fixture accepts, or provider logs portable protocol values.

## 4. Engineering model

The evidence system is organized as responsibilities, not a provider inheritance hierarchy:

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
          +------ independent raw facts ----+
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

The two labs differ only where the mechanism necessarily differs: topology construction, privileged control actions, artifact identity, transport-boundary witness implementation, and supplemental diagnostics. They do not own portable expected outcomes.

## 5. Contract layering

The design separates four layers so later Accepted work can lift stable semantics without lifting provider implementation details.

### 5.1 Portable Evidence Core

Contains only materialized inputs and normalized observations needed to evaluate AEP-0012 portable predicates.

Examples:

- logical path identity;
- materialized literal endpoints;
- exchange program identity;
- exact request/expected-response byte references;
- exchange observation budget;
- attempt identity and phase;
- normalized connection-initiation cardinality;
- portable completion/non-completion observations;
- fixture exchange observations;
- target-control observations;
- cleanup/noninterference observations.

### 5.2 Lab Binding

Binds one Evidence Plan to one concrete mechanism class and exact reviewed mechanism artifact.

Examples:

- terminating/intercepting class;
- non-terminating packet-path class;
- Toxiproxy exact artifact/image digest;
- Linux/kernel/nftables tooling identity necessary to interpret evidence;
- transport-boundary witness implementation revision;
- topology allocation details;
- privileged controller implementation revision.

Lab Binding is project evidence metadata. It does not participate in provider-specific expected-outcome branching.

### 5.3 Mechanism and witness diagnostics

Optional supplemental data useful for debugging or audit may include:

- provider control API responses;
- nftables rule handles;
- namespace IDs;
- raw packet/connection counters;
- raw transport traces;
- native socket failure text;
- provider logs.

These native representations MUST NOT independently establish portable activation, cut, recovery, one-initiation integrity, or acceptance success. They may be inputs to a reviewed normalization step that produces a provider-neutral observation when the evidence architecture makes that observation independently trustworthy.

### 5.4 Assessment

A provider-neutral comparator result over the Portable Evidence Core plus integrity/precondition checks.

The assessment records the exact comparator revision/policy used to reach the result.

## 6. Evidence Plan

### 6.1 Role

An Evidence Plan is the immutable, fully materialized top-level input for one NPR-011 evidence execution.

The lab MUST NOT discover or silently substitute protocol-significant inputs after the plan is sealed.

A conceptual implementation may use a record with fields similar to:

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

These names are **not future normative Schema names**.

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

A fixture/controller may need lower-level timeouts for bounded resource cleanup or process hygiene, but those limits MUST NOT fire earlier in a way that substitutes for or changes the portable completion predicate. If a hygiene timeout truncates an observation before the governed budget can be evaluated, the evidence is infrastructure/evidence-invalid rather than transport-cut success.

### 6.6 Environment binding

The plan binds the AEP-0009/AEP-0012 Environment-governed fault identity, target, activation condition, and clear occurrence identity needed to interpret execution.

Security-sensitive future activation information is represented in a private evaluator projection where necessary. The Subject-visible projection MUST NOT reveal future fault schedules, privileged control handles, control credentials, or unreleased future challenge material.

### 6.7 Ordered phase program

The canonical positive plan records:

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

The negative mode identifies what implementation defect is intentionally assembled; it MUST NOT alter the comparator's provider-neutral portable expectation.

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

For example, a terminating run may bind the reviewed Toxiproxy artifact/digest and a packet-path run may bind kernel/tooling/controller identities necessary to interpret the run.

The terminating Lab Binding MUST also identify the independently reviewed upstream transport-initiation witness implementation used to establish C10. That witness is not a second fault controller and does not define the expected outcome.

This binding is evidence provenance, not portable outcome identity.

### 6.10 Plan sealing

The plan is sealed before governed execution.

The retained exact plan bytes are hashed with SHA-256 and byte length:

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

It does not use native socket IDs, ephemeral ports, proxy connection IDs, packet sequence numbers, or rule handles as portable identity.

### 7.2 One-initiation rule and independent witnesses

The retained observations MUST make it possible to verify AEP-0012's one-initiation rule rather than infer it from provider configuration.

For every certified attempt:

- exactly one Subject-facing TCP connection initiation is admitted;
- a terminating/intercepting topology also permits exactly one corresponding upstream initiation to the bound fixture endpoint;
- hidden reconnect, retry, alternate destination, or alternate path cannot be normalized away.

The Subject-side initiation count MUST come from an observation boundary that can distinguish a new certified initiation from connection reuse/pooling/retry.

For a terminating/intercepting lab, **fixture application `accept()` accounting alone is insufficient** to prove the upstream one-initiation rule because a TCP connection attempt can be initiated without completing the handshake or reaching application `accept()`.

Therefore the terminating lab MUST provide an **independent fixture-boundary transport-initiation witness** capable of establishing the number of upstream TCP connection attempts directed at the bound fixture endpoint for the certified attempt. The witness MUST:

1. be outside provider self-reported control-plane state;
2. observe at the controlled fixture-side transport boundary or an equivalently independent boundary;
3. distinguish initiation attempts sufficiently to detect additional reconnect/retry attempts, including attempts that do not become accepted application connections;
4. bind observations to the sealed run/path/phase window without relying on wall-clock coincidence alone;
5. retain raw evidence plus the reviewed normalization that derives the provider-neutral `upstreamInitiations` fact;
6. remain observational only — it MUST NOT activate/clear the fault or alter transport behavior;
7. fail closed if loss, capture ambiguity, offload, namespace placement, or another mechanism limitation prevents trustworthy initiation counting.

A lab may implement this witness with controlled transport-boundary SYN/connection-attempt accounting, a narrowly scoped trace/counter, or another independently reviewable mechanism. The native mechanism is project evidence plumbing, not protocol semantics.

Provider logs/API counters may supplement the witness but cannot replace it. Application `accept()` records remain a separate exchange witness and useful cross-check.

If the lab cannot prove the required initiation boundary, the evidence is `EVIDENCE_INVALID`/unsupported rather than assuming the provider behaved correctly.

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

The exact cryptographic KDF is an implementation decision for this evidence phase and MUST NOT be elevated into protocol semantics by this document. A future implementation may instead generate independent random challenges if it satisfies the same unpredictability, uniqueness, context-binding, retention, and secrecy properties.

Required properties:

- challenge values are unpredictable to the Subject before the governed attempt where predictability could permit stale/cached fabrication;
- different attempts receive different challenges;
- context binds the challenge to the correct run/phase/path/exchange program;
- future challenges are not leaked by evidence projections or logs.

### 7.4 Retention of challenge evidence

The Evidence Bundle retains enough information to verify that observed fixture/request/response evidence belongs to the correct attempt.

It does not require retaining the private run root. Preferred retention is:

- the materialized per-attempt challenge or safe verification representation after the attempt;
- challenge digest/commitment;
- attempt context;
- exact request/expected-response byte digests.

If retaining a challenge would disclose a still-sensitive future value, retention is delayed or represented by a commitment until that secrecy requirement expires.

Low-entropy secrets MUST NOT be "protected" merely by hashing them.

## 8. Deterministic Fixture contract

### 8.1 Fixture responsibility

The Fixture provides an independent deterministic exact-byte endpoint against which portable baseline/recovery and active-cut behavior can be observed.

It does not control the Network fault and does not own the transport-initiation witness.

### 8.2 Fixture protocol

For one admitted application connection:

1. accept one TCP connection;
2. read the exact request byte count required by the materialized exchange program;
3. validate exact request bytes and current attempt challenge;
4. on a valid request, emit the exact materialized expected response bytes once;
5. record an immutable fixture exchange event;
6. close/finish according to fixture-local hygiene without adding HTTP/TLS/application semantics.

Fixture process-hygiene limits MUST NOT redefine the evaluator-owned observation budget. If fixture-local resource protection terminates an exchange before the portable budget can be judged, the evidence records infrastructure/evidence failure instead of a successful transport cut.

The fixture MUST NOT:

- retry upstream operations;
- cache a prior response for reuse;
- resolve DNS as part of the exchange;
- implement HTTP/TLS framing;
- interpret TCP segment boundaries as message boundaries;
- return provider-specific control information;
- declare AVP pass/fail.

### 8.3 Fixture exchange accounting versus transport-initiation accounting

The fixture records application connection-accept/exchange events independently of the Subject and fault controller.

For each accepted connection, evidence SHOULD capture:

- fixture event ordinal;
- run/attempt correlation when derivable from validated challenge;
- request byte length and SHA-256;
- expected-response byte length and SHA-256;
- validation outcome;
- whether response emission completed;
- fixture-local error category if applicable.

These records establish exact-byte exchange behavior and cross-check successful upstream connections. They **do not by themselves prove the total number of upstream TCP initiation attempts**.

For terminating/intercepting evidence, the separate fixture-boundary transport-initiation witness defined in §7.2 is mandatory for C10. Comparator input therefore distinguishes:

- `fixtureAcceptedConnections` / exchange events; and
- normalized `upstreamInitiations` derived from the independent transport-boundary witness.

A mismatch between these layers is retained and investigated; it MUST NOT be silently normalized away.

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

The transport-initiation witness may have its own narrow lifecycle/read seam, but it MUST remain observational and separately auditable from fault mutation.

## 9. Observation model

### 9.1 Principle

Mechanism controllers produce actions and raw facts. They do not produce portable verdicts.

Independent witness/fixture components also produce raw facts. A normalization layer converts those facts into a provider-neutral observation vocabulary without discarding evidence needed to detect violations.

### 9.2 Portable attempt observation

A conceptual attempt observation should be able to represent at least:

```text
AttemptObservation
  attemptId
  phaseId
  role
  subjectConnectionInitiations
  upstreamInitiations
  fixtureAcceptedConnections
  exchangeCompleted
  responseBytesDigest
  responseByteLength
  mismatchObserved
  observationBudgetExpired
  elapsedMonotonic
  fixtureEventRefs
  transportWitnessRefs
  validityProblems
```

The names above are illustrative, not normative schema fields.

`upstreamInitiations` for terminating evidence is valid only when derived from the independently reviewed transport-initiation witness. A provider's own retry counter cannot be normalized into this fact without independent corroboration sufficient for the reviewed evidence claim.

### 9.3 Native failures and raw transport evidence

Native results such as ECONNREFUSED, ETIMEDOUT, reset, EOF, unreachable, provider toxic events, raw SYN counts, packet traces, or native connection counters may be retained as diagnostics/raw witness evidence.

The portable active-cut predicate remains non-completion of the exact certified exchange within the evaluator-owned observation budget after valid settlement/admission.

The portable one-initiation predicate remains cardinality/identity integrity for the certified attempt; it does not standardize SYN packets, packet captures, or native counters.

### 9.4 Missing/conflicting observations

The evidence system fails closed if required observations are missing, contradictory, stale, associated with another plan/attempt, or cannot be bound to retained artifacts.

For example, if fixture exchange records show one accepted connection but the transport-initiation witness is unavailable or ambiguous, the terminating lab cannot infer `upstreamInitiations == 1` from `accept == 1`.

It MUST NOT turn unknown into pass because one provider control call succeeded.

## 10. Evidence Result

### 10.1 Role

Evidence Result is the immutable execution record produced from one sealed Plan plus retained observations before or alongside comparator assessment.

It references the exact Plan by digest/size rather than embedding an ambiguous mutable copy.

### 10.2 Result sections

The result conceptually separates:

1. portable observations;
2. fixture observations;
3. independent transport-initiation witness observations where required;
4. mechanism/witness diagnostics;
5. execution provenance;
6. cleanup observations;
7. integrity references.

This separation is mandatory even if one implementation serializes them in one file.

### 10.3 Result sealing

The exact retained result bytes are SHA-256 hashed with byte length. Mutation creates a new result artifact and lineage.

A matching digest proves byte identity, not behavioral trustworthiness; trust in observations comes from the controlled evidence architecture and review.

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

It MUST NOT treat provider control API success, provider-native activated status, rule/object existence, packet-capture presence, a specific errno, or a provider self-reported retry counter as sufficient proof of portable behavior.

### 11.3 Canonical positive predicates

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

A later distinct Subject-side certified attempt independently satisfies transport cut. Settlement cannot be retroactively inferred from C5.

#### C6 — Target isolation

Where the plan materializes a suitable non-target control, that control remains baseline-capable during the selected path's active cut. If the requested narrow scope cannot be isolated, the run is invalid/unsupported rather than a narrow-path pass.

#### C7 — Recovery probe #1

First privileged fresh recovery attempt completes the exact exchange.

#### C8 — Recovery probe #2

Second consecutive privileged fresh recovery attempt completes the exact exchange.

#### C9 — Stability witness

A third distinct post-recovery fresh attempt completes successfully and demonstrates no silent reactivation for the cleared occurrence.

#### C10 — One-initiation / retry-fallback integrity

Required independent evidence shows:

- exactly one Subject-side initiation for each certified attempt;
- for terminating/intercepting topology, exactly one upstream transport initiation to the bound fixture endpoint for that certified attempt;
- application accept/exchange counts are consistent with the transport-initiation witness where connections complete;
- no hidden retry, reconnect, alternate endpoint, or alternate path occurs inside one certified attempt.

For the terminating lab, absence or ambiguity of the independent upstream transport-initiation witness makes C10 invalid/unsupported; fixture `accept()` count or provider self-report cannot substitute.

#### C11 — Cleanup/reset noninterference

Cleanup observations establish that excluded residual mechanism state cannot silently affect the next governed execution, or evidence fails closed.

#### C12 — Security/projection integrity

Evidence does not show premature disclosure of future schedule/control/challenge secrets to the Subject-visible surface.

### 11.4 Assessment taxonomy

The comparator returns an engineering classification preserving AVP failure/Validity separation:

- `SATISFIED` — retained evidence satisfies the AEP-0012 candidate predicates for this plan;
- `SEMANTIC_VIOLATION` — valid evidence shows candidate behavior was violated;
- `EVIDENCE_INVALID` — missing/conflicting/untrusted/integrity-invalid evidence prevents a semantic conclusion;
- `INFRASTRUCTURE_FAILURE` — controlled infrastructure failed before a trustworthy semantic conclusion;
- `UNSUPPORTED_MATERIALIZATION` — requested governed semantics cannot be represented safely by the lab.

These are engineering categories, not proposed normative AVP verdict enum values.

### 11.5 Failure localization

Each failed assessment records the earliest/root predicate failure plus supporting artifact references. Secondary downstream failures may be retained but MUST NOT obscure root cause.

Examples:

- baseline failure prevents useful active-cut portability evidence;
- invalid settlement cannot be repaired by later Subject cut;
- missing upstream initiation witness fails C10 rather than assuming one attempt;
- cleanup failure remains a failure even if active cut passed.

## 12. Negative evidence assembly

Negative cases use the same comparator and portable predicate definitions. A defect is injected into lab/controller/fixture/witness assembly rather than changing expected outcomes.

### 12.1 Bypass fault

Controller claims activation while certified Subject path bypasses control. C5 must fail because exchange completes.

### 12.2 Early activation

Path is cut before Environment occurrence condition. C3 must fail.

### 12.3 False settled

Settlement is reported without an independently successful privileged cut probe. C4 must fail even if C5 later cuts.

### 12.4 False recovery

Provider clear or one transient success is treated as recovery without two-probe + stability sequence. C7/C8/C9 must fail.

### 12.5 Schedule leak

Future activation/control/challenge material is exposed to Subject-visible projection. C12 must fail.

### 12.6 Hidden retry/fallback

A certified attempt performs multiple Subject or terminating upstream initiations, reconnects, or alternate path/destination fallback. C10 must fail.

The terminating negative assembly MUST include a case where an extra upstream initiation is visible to the transport-initiation witness. The test MUST NOT depend only on an extra successful fixture `accept()` event, because the design specifically guards against unaccepted/failed reconnect attempts.

### 12.7 Collateral target

A narrow target disrupts a materialized non-target control. C6 must fail.

### 12.8 Residual state

Cleanup leaves mechanism state that changes the next fault-free baseline. C11 must fail.

## 13. Evidence Bundle

### 13.1 Purpose

The bundle is the retained project evidence unit for review and later reassessment. It groups immutable artifacts without making the grouping format normative.

### 13.2 Minimum retained artifact set

A complete evidence bundle SHOULD retain references to:

- exact Evidence Plan bytes;
- Evidence Result bytes;
- comparator assessment bytes;
- exact source repository commit;
- comparator implementation/source revision;
- fixture implementation/source revision;
- transport-initiation witness implementation/source revision where required;
- controller/lab implementation/source revision;
- exact mechanism artifact/version/digest where applicable;
- fixture raw event records;
- raw transport-initiation witness records where required;
- normalized portable observation records;
- diagnostics clearly marked non-authoritative;
- cleanup/noninterference records;
- workflow/run identity when CI executes evidence;
- safe host/kernel/tool metadata needed for interpretation;
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

SHA-256 is selected as the project evidence baseline because it is broadly interoperable and appropriate for content-addressed integrity. This does not define a future AVP protocol digest algorithm registry.

### 13.4 Exact-byte integrity

Digest calculation is over exact retained bytes. No JSON reserialization is permitted before verification.

This avoids Proposed-phase dependence on JSON canonicalization and permits later format evolution while preserving artifact identity.

### 13.5 Manifest / bundle root

An implementation MAY maintain a small manifest referencing artifacts by digest/size. The manifest itself is exact-byte hashed.

The bundle root is a content-addressed review handle, not cryptographic authenticity/signing.

### 13.6 Authenticity boundary

Content digest proves reviewers are evaluating the same bytes. It does not prove who generated them or whether execution was uncompromised.

Signing/attestation remains separately governed and unauthorized here.

## 14. Provenance and current industry rationale

This design borrows engineering principles, not authority, from current supply-chain provenance practice.

As of this design review:

- SLSA v1.2 is the current Approved SLSA specification. Its build provenance separates build definition/top-level inputs from run details/byproducts and binds artifacts with cryptographic digests.
- in-toto Attestation Framework Statement v1 separates subject identity/digests from typed predicate payloads.

References:

- https://slsa.dev/spec/v1.2/
- https://slsa.dev/spec/v1.2/build-provenance
- https://slsa.dev/spec/v1.2/build-requirements
- https://in-toto.io/docs/specs/
- https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md

AVP does not adopt SLSA Provenance or in-toto Statement as NPR-011 serialization. Transferable principles are:

1. immutable artifact identity is digest-bound;
2. governed inputs are distinguishable from per-run observations/byproducts;
3. comparator/policy revision is identifiable;
4. evidence producers cannot invisibly alter verification policy;
5. provenance supports later audit without pretending metadata alone proves behavior.

## 15. Reassessment and replay

### 15.1 Reassessment

A retained bundle MAY be reassessed by a later comparator if every observation needed by the later assessment was already retained.

Reassessment records:

- original plan/result/bundle digests;
- original comparator revision;
- new comparator revision;
- reassessment timestamp as audit metadata;
- changed assessment and rationale.

A reassessment is not a new behavioral run.

### 15.2 When rerun is mandatory

A new live run is required if:

- later semantics require an observation not retained originally;
- integrity of a required artifact cannot be established;
- mechanism or transport-witness artifact identity is ambiguous;
- challenge/attempt binding cannot be verified;
- source/execution provenance is insufficient;
- a new mechanism class/version is claimed as fresh acceptance evidence;
- a changed transport-witness method is needed to establish a claim the old evidence could not establish.

### 15.3 Reassessment after semantic changes

A material AEP semantic change does not automatically permit old evidence to prove the new semantics. Acceptance-oriented review MUST explicitly determine whether the old retained observations completely answer the new semantic question. If not, rerun is mandatory.

This avoids turning reassessment into a shortcut around required behavioral evidence.

### 15.4 Replay resistance

An old bundle cannot satisfy a new run merely by copying successful files because:

- plan/run identity changes;
- per-attempt challenges change;
- fixture and transport-witness observations bind the current run/attempt windows;
- plan/result/bundle digests create new lineage.

## 16. Versioning and evolution

### 16.1 Freeze now

This design freezes engineering responsibilities for:

- sealed immutable plan before execution;
- exact semantic baseline binding;
- attempt identity and fresh challenge per attempt;
- independent one-initiation evidence;
- terminating fixture-boundary upstream transport-initiation witness;
- deterministic exact-byte fixture;
- portable observations separated from diagnostics;
- provider-neutral comparator ownership;
- ordered portable predicate matrix;
- content-addressed retained evidence;
- failure/Validity separation;
- reassessment versus rerun;
- secrecy and cleanup/noninterference evidence.

### 16.2 Do not freeze now

This design deliberately does not freeze:

- final serialized JSON property names;
- normative Schema URI/version;
- TCK IDs;
- public provider/witness interface;
- plugin entry points;
- final Python package/module names;
- exact exception classes;
- exact KDF algorithm;
- exact Toxiproxy control calls/toxics;
- exact nftables syntax/rule layout;
- exact transport-witness implementation (pcap/eBPF/nft counter/other);
- CI provider/runner image;
- signing/attestation format.

### 16.3 Design revision

A project evidence design revision changes only when this engineering contract changes materially.

Formatting/source-citation edits do not imply a new protocol version.

A mechanism or witness artifact upgrade creates a new reviewed Lab Binding/evidence baseline; it does not by itself change AEP-0012.

## 17. Security model

### 17.1 Subject-visible data

The Subject may receive only data required for the current governed exchange.

It MUST NOT receive:

- future activation schedule;
- future challenge values;
- privileged control handles;
- provider credentials;
- host/root network-control credentials;
- private evaluator seed material.

### 17.2 Privileged control

The mechanism controller may hold provider/root privileges required for the evidence lab, but those remain outside Subject authority and narrowly scoped to the ephemeral target.

### 17.3 Witness privilege and noninterference

A transport-initiation witness may require elevated observation privilege. That privilege MUST be narrower than necessary, separated from Subject authority, and observational for the governed path. The witness MUST NOT mutate routing/filtering/fault state or become a covert second control mechanism.

If the witness itself can perturb traffic materially enough to affect the result, the lab must demonstrate noninterference or fail closed.

### 17.4 Evidence producer separation

Where feasible, acceptance observations are generated/read from control/fixture/witness boundaries not writable by the Subject process. Subject self-report alone is insufficient for activation, fixture exchange, upstream initiation, or cleanup proof.

### 17.5 Sensitive artifact retention

The bundle MUST exclude raw credentials, access tokens, private run-root seeds, and future schedule secrets unless an explicit reviewed reason requires retention.

Hashing low-entropy secrets does not make them safe.

## 18. Cleanup / noninterference evidence

Cleanup is a first-class evidence phase, not a `finally` block whose success is assumed.

The lab records:

- resources created by the run;
- privileged fault state created/modified;
- witness resources/state created;
- cleanup actions attempted;
- cleanup errors;
- stale handle invalidation where applicable;
- post-cleanup independent fault-free baseline/noninterference check.

The comparator does not require exact provider-state restoration. It requires trustworthy evidence that residual excluded state cannot silently affect the next Episode, consistent with NPR-010.

## 19. Cross-mechanism equality rule

NPR-011 is satisfied only if both evidence classes are judged against one portable semantic matrix.

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
  transport-witness implementation details
  supplemental diagnostics
```

The project MUST NOT normalize away a semantic difference merely to make both mechanisms green.

If one mechanism cannot satisfy a portable predicate, the correct outcomes are failure, unsupported/fail-closed materialization, or a new protocol blocker — never provider-name branching.

## 20. Implementation decomposition after design adoption

### Work Unit C — terminating/intercepting evidence lab

Implement only the terminating lab, deterministic fixture integration, independent fixture-boundary transport-initiation witness, raw/normalized observations, and required negative assemblies.

Do not create a generic backend base class.

### Work Unit D — packet-path evidence lab

Implement the independent netns/veth/nftables lab against the main-adopted plan/result/fixture/comparator contract.

Only after two real consumers exist may repeated ordinary implementation structure be evaluated for reuse; semantic abstraction remains governed separately.

### Work Unit E — retained cross-mechanism matrix

Execute both classes against the same semantic matrix, retain content-addressed bundles, compare outcomes, exercise mandatory negatives, and produce acceptance evidence.

### Work Unit F — acceptance-oriented protocol re-review

Review AEP-0012 plus actual NPR-011 evidence. New semantic ambiguity returns to protocol work rather than being patched in provider code.

## 21. Detailed readiness criteria for Work Unit B closure

This design is ready for main adoption only if focused review confirms:

- [ ] AEP-0012 semantics are not silently changed;
- [ ] design is non-normative and not future Schema/TCK;
- [ ] plan materialization is complete enough for both classes;
- [ ] attempt/challenge identity prevents stale/replay ambiguity;
- [ ] Subject-side retries/reuse are independently detectable;
- [ ] terminating upstream initiation attempts, including unaccepted/failed attempts, have an independent fixture-boundary witness;
- [ ] fixture `accept()` accounting is not misrepresented as total initiation accounting;
- [ ] fixture/witness responsibilities are deterministic/observational and do not own fault control;
- [ ] hygiene timeouts cannot masquerade as portable observation-budget expiry;
- [ ] portable observations are separate from provider/witness diagnostics;
- [ ] comparator is provider-neutral and deterministic/pure over retained evidence;
- [ ] all positive AEP-0012 predicates are represented;
- [ ] all required negative directions use the same comparator;
- [ ] evidence integrity uses exact retained bytes with digest/size references;
- [ ] result/plan/comparator/witness revisions are auditable;
- [ ] reassessment is distinguished from live rerun and cannot silently prove changed semantics;
- [ ] security projections do not leak future schedule/challenge/control material;
- [ ] cleanup/noninterference includes witness state/resources;
- [ ] no generic backend/plugin abstraction is introduced;
- [ ] implementation, privileged CI, lifecycle advancement, and release remain unauthorized.

## 22. Explicit non-authorization boundary

This design does **not** authorize:

- Toxiproxy process/container integration;
- Linux network namespace/veth/nftables implementation;
- packet capture/eBPF/nft counter/other transport-witness implementation;
- privileged CI/workflow changes;
- root/network capability grants;
- normative `EvidencePlan`/`EvidenceResult` JSON Schema;
- public Network provider/witness API;
- generic `BaseNetworkBackend`/`NetworkProvider`/plugin registry;
- Network Control Spec/index/Schema/TCK/harness/reference runtime;
- AEP-0012 `Proposed -> Accepted` or `Accepted -> Final`;
- release-mode/version/tag/publication/signing/attestation changes.

Implementation remains a later, separately reviewed work unit after this candidate is main-adopted.

## 23. Decision summary

The long-term no-throwaway design is:

```text
Seal one provider-neutral plan
  -> generate fresh evaluator-owned attempt/challenge identity
  -> execute one of two independent mechanism labs
  -> independently witness required connection initiations
  -> record fixture exact-byte exchange observations
  -> normalize portable observations independently from provider diagnostics
  -> seal result artifacts by exact-byte SHA-256 + size
  -> evaluate with one pure provider-neutral comparator
  -> retain a content-addressed evidence bundle
  -> run the same positive and negative predicate matrix across both mechanisms
  -> reassess retained evidence only when the required facts already exist; otherwise rerun
```

This structure is intended to survive later Accepted -> Spec -> Schema -> TCK -> Harness work because it freezes responsibilities and evidence relationships, not temporary provider APIs, native observation mechanisms, or serialization details.

# Alpha 3 Network Control NPR-011 Evidence Contract Traceability Matrix

Status: **DESIGN REVIEW COMPANION — NON-NORMATIVE**

Baseline: `main@6e4f4e2c89585edd921a67de77e57f24b97472d6`

Detailed design:

- `docs/design/alpha3-network-control-npr011-evidence-contract-detailed-design.md`

Authority:

- `rfcs/AEP-0012-network-control-resource-profile.md`
- AEP-0009 Environment Fabric and existing Core/Security/Evidence authority where referenced by AEP-0012

Prepared: 2026-09-03

## Purpose

This matrix is a review and implementation-readiness aid. It makes explicit which evidence responsibility demonstrates each material AEP-0012/NPR-011 obligation before either mechanism lab is implemented.

It is not a requirement index, normative Spec mapping, Schema, or TCK registry. Future Accepted work may reorganize IDs or serialization while preserving the protocol semantics owned by the AEP/Spec chain.

## Responsibility legend

- **P** — sealed Evidence Plan
- **A** — attempt/challenge materialization
- **F** — deterministic Fixture
- **O** — normalized portable observation
- **D** — mechanism diagnostics only
- **C** — provider-neutral Comparator
- **B** — retained content-addressed Evidence Bundle
- **N** — required negative assembly
- **L** — lab-specific mechanism responsibility

## Semantic traceability

| Concern | AEP/NPR intent | P | A | F | O | C | B | N/L review condition |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Exact semantic baseline | Evidence must test one exact Proposed semantic candidate, not `latest` | ✓ |  |  |  | ✓ integrity precondition | ✓ source commit/AEP ref | Plan without exact source identity is invalid |
| Materialized literal endpoint | DNS/address racing/fallback excluded from base attempt | ✓ | ✓ bind path/attempt | ✓ fixture endpoint | ✓ observed destination/context | ✓ C1/C10 | ✓ | Hidden alternate endpoint/fallback negative must fail |
| Logical path across mechanism classes | terminating and packet-path mechanisms prove same portable claim | ✓ path identity | ✓ | ✓ end boundary | ✓ | ✓ same predicates | ✓ lab binding separated | Provider-native connection identity never becomes portable |
| Exact exchange bytes | TCP byte stream requires application-defined deterministic completion | ✓ byte refs/program | ✓ attempt-specific bytes | ✓ validates exact bytes | ✓ response digest/length | ✓ C2/C4/C5/C7-C9 | ✓ exact byte artifacts/digests | Segment/read/write boundaries are irrelevant |
| Fresh attempt | no pre-existing connection/pooling reuse | ✓ phase program | ✓ unique attempt | ✓ current challenge | ✓ initiation/freshness evidence | ✓ C10 | ✓ | Pool/reuse negative fails closed |
| One Subject initiation | one certified attempt cannot hide Subject retry/reconnect | ✓ | ✓ |  | ✓ initiation count/evidence | ✓ C10 | ✓ | Hidden Subject retry negative must fail |
| One terminating upstream initiation | proxy cannot hide upstream retry/fallback | ✓ fixture binding | ✓ attempt context | ✓ independent accept accounting | ✓ upstream initiation/fixture refs | ✓ C10 | ✓ | Terminating lab must independently expose second upstream initiation |
| Attempt-unique challenge | stale/cached/cross-attempt responses cannot satisfy current attempt | ✓ challenge rule | ✓ fresh challenge | ✓ validates challenge | ✓ request/response linkage | ✓ C2 etc. | ✓ safe challenge/commitment evidence | Future challenge leakage prohibited |
| Finite observation budget | blackhole cut must terminate by evaluator-owned bound, not provider timeout | ✓ governed positive finite budget | ✓ binds attempt |  | ✓ monotonic elapsed/budget expiry | ✓ C4/C5 | ✓ | Provider timeout may be diagnostic only |
| Pre-trigger traffic | occurrence-triggered fault must not activate early | ✓ phase/environment binding | ✓ | ✓ if exchange reaches fixture | ✓ pre-trigger result | ✓ C3 | ✓ | EarlyActivation negative must fail |
| Environment activation authority | trigger identity/condition remains Environment-owned | ✓ environment binding | ✓ phase admission after trigger |  | ✓ trigger/settlement ordering refs | ✓ C3/C4 | ✓ | Network lab cannot redefine occurrence counting |
| Independent activation settlement | control-plane success does not prove data-plane cut | ✓ P3 | ✓ privileged fresh attempt | ✓ no current exchange completion when cut | ✓ | ✓ C4 | ✓ | FalseSettled negative must fail even if later C5 fails/exhibits cut |
| Distinct Subject active cut | later Subject attempt independently demonstrates active fault | ✓ P4 | ✓ distinct identity/challenge | ✓ | ✓ | ✓ C5 | ✓ | Settlement attempt cannot substitute for Subject attempt |
| Mechanism-neutral transport cut | refusal/reset/drop/blackhole all normalize to exact exchange non-completion | ✓ budget/exchange | ✓ | ✓ | ✓ completion/non-completion facts | ✓ C4/C5 | ✓ diagnostics separate | Comparator cannot branch on errno/provider |
| Established connection exclusion | base profile does not claim termination of already-open connections | ✓ fresh-phase program | ✓ no reuse |  | ✓ | ✓ | ✓ | Lab must not claim stronger guarantee from native behavior |
| Target isolation | narrow target cannot be proven by broad outage | ✓ target + optional control | ✓ control attempt | ✓ | ✓ target/control results | ✓ C6 | ✓ | CollateralTarget negative must fail; unsupported isolation fails closed |
| Clear authority | privileged clear remains evaluator/control-owned | ✓ P6 | ✓ |  | ✓ control/ordering facts | ✓ recovery precondition | ✓ | Provider acknowledgement alone is non-authoritative |
| Recovery #1 | first fresh success after clear | ✓ P7 | ✓ unique identity/challenge | ✓ exact exchange | ✓ | ✓ C7 | ✓ |  |
| Recovery #2 | second consecutive independent fresh success | ✓ P8 | ✓ | ✓ | ✓ | ✓ C8 | ✓ | FalseRecovery negative cannot stop after one success |
| Stability witness | additional distinct fresh success proves no silent reactivation for cleared occurrence | ✓ P9 | ✓ | ✓ | ✓ | ✓ C9 | ✓ | FalseRecovery/reactivation assembly must fail |
| No unbounded retry-until-success | recovery witness is finite deterministic sequence | ✓ phase cardinality | ✓ attempt cardinality | ✓ accept accounting | ✓ | ✓ C7-C9/C10 | ✓ | Lab/controller retry loops are semantic violations/invalid evidence |
| Behavioral path coverage | provider object/config presence cannot replace end-to-end baseline/cut/recovery behavior | ✓ same path binding | ✓ | ✓ | ✓ phase facts | ✓ C2-C9 | ✓ | BypassFault negative is mandatory |
| Reset/cleanup noninterference | excluded provider state may not silently affect next Episode | ✓ cleanup phase/next baseline policy | ✓ post-cleanup witness | ✓ | ✓ cleanup/new-baseline observations | ✓ C11 | ✓ | ResidualState negative must fail |
| Schedule/control secrecy | future schedule/control/challenge material remains evaluator-private | ✓ private/public projections | ✓ challenge release boundary |  | ✓ leak evidence if observed | ✓ C12 | ✓ safe retention | ScheduleLeak negative must fail |
| Failure vs Validity | infrastructure/evidence failures cannot be converted to task/protocol success | ✓ |  |  | ✓ validity problems | ✓ taxonomy | ✓ | Missing/conflicting evidence => fail closed |
| Provider-neutral identity | portable evidence excludes native proxy/rule/socket IDs | ✓ logical IDs | ✓ | ✓ attempt challenge | ✓ portable refs | ✓ | ✓ diagnostics namespaced | Provider IDs remain D only |
| Mechanism artifact provenance | exact evidence mechanism/version/digest must be auditable | ✓ lab binding |  |  |  | integrity/precondition only | ✓ | Upgrade creates new reviewed evidence baseline, not protocol change |
| Two materially independent classes | NPR-011 requires terminating + packet-path project evidence before acceptance re-review | ✓ mechanism class binding |  | same fixture semantics | same O vocabulary | same C | paired retained B | Comparator expectations identical across classes |
| Required negative directions | wrong implementations must fail same portable predicates | ✓ negative mode | ✓ | may participate | ✓ | ✓ unchanged | ✓ | bypass, early, false-settled, false-recovery, leak, retry/fallback, collateral, residual |

## Comparator predicate coverage

| Comparator predicate | Positive phase/evidence | Primary violations caught |
|---|---|---|
| C1 Plan integrity/materialization | sealed plan + exact baseline + endpoint/exchange/budget completeness | mutable/ambiguous plan, unresolved endpoint, wrong semantic source |
| C2 Baseline | P0 | broken fixture/path before fault, stale challenge, hidden non-baseline state |
| C3 Pre-trigger/no early activation | P1/P2 | EarlyActivation |
| C4 Activation settlement | P3 | FalseSettled, control-plane-only proof |
| C5 Subject active cut | P4 | BypassFault, inactive/wrong target |
| C6 Target isolation | P5 when materialized | CollateralTarget |
| C7 Recovery #1 | P7 | clear did not restore path |
| C8 Recovery #2 | P8 | transient-only recovery / retry-until-success |
| C9 Stability witness | P9 | silent reactivation / false recovery |
| C10 One-initiation/fallback integrity | all certified attempts | hidden Subject retry, proxy upstream retry, address/path fallback, pooling reuse |
| C11 Cleanup/reset noninterference | P10 | residual fault/provider state |
| C12 Security/projection integrity | entire run | schedule/control/future challenge leakage |

## Evidence artifact traceability

| Artifact | Producer | Consumer | Portable authority? | Integrity binding |
|---|---|---|---|---|
| Exact Evidence Plan bytes | materializer/evaluator | labs, comparator, reviewers | governed project evidence input; not protocol Schema | SHA-256 + byte length |
| Per-attempt materialized request bytes | evaluator | Subject/fixture/comparator | portable evidence fact for this run | SHA-256 + byte length |
| Per-attempt expected-response bytes | evaluator | fixture/comparator | portable evidence fact for this run | SHA-256 + byte length |
| Fixture event log | Fixture | normalizer/comparator/review | independent observation evidence | exact-byte digest + refs |
| Portable observation record | normalization responsibility | comparator/review | comparator input, not normative wire format | exact-byte digest + refs |
| Mechanism diagnostics | mechanism/controller | debugging/review | **No** | retained/digested when useful |
| Evidence Result | evidence assembly | comparator/review | execution evidence, not protocol verdict format | SHA-256 + byte length |
| Comparator assessment | comparator | review/acceptance evidence | project assessment against AEP candidate | comparator revision + digest |
| Evidence bundle manifest/root | evidence retention | review/reassessment | review handle, not authenticity proof | exact-byte digest |
| Signature/attestation | not part of this work unit | future release/trust work | not authorized | separately governed |

## Failure-localization matrix

| First failed predicate | Required interpretation | Forbidden interpretation |
|---|---|---|
| C1 | invalid evidence input/materialization | provider "best effort" pass |
| C2 | baseline/infrastructure/evidence invalid depending cause | active-fault success |
| C3 | semantic violation: early activation | occurrence trigger considered satisfied early |
| C4 | settlement semantic/evidence failure | infer settlement from later Subject cut |
| C5 | active-cut semantic violation if evidence valid | provider control API status treated as substitute |
| C6 | target-scope semantic violation / unsupported materialization | narrow-target pass despite broad outage |
| C7-C9 | recovery semantic violation/evidence failure | retry until a success appears |
| C10 | attempt-integrity semantic/evidence failure | normalize retries away |
| C11 | cleanup/noninterference failure | ignore because main cut succeeded |
| C12 | security semantic violation | redact after the fact and call run clean |

## Reassessment traceability

A later reassessment can remain a non-live operation only when all new comparator predicates can be evaluated from already retained immutable artifacts.

| Change | Reassessment sufficient? | New live run required? |
|---|---:|---:|
| comparator bug fix using same retained observations | ✓ |  |
| changed failure-report wording only | ✓ |  |
| stronger predicate using observations already retained | ✓, with new assessment lineage |  |
| predicate requires upstream-initiation evidence that old run did not retain |  | ✓ |
| exact mechanism artifact/version unknown |  | ✓ |
| challenge/attempt binding cannot be verified |  | ✓ |
| new mechanism class/version claimed as acceptance evidence |  | ✓ |
| AEP semantics materially change execution behavior | usually no | ✓ unless existing retained behavior completely answers the new semantics and review explicitly accepts reassessment |

## Review gates before mechanism implementation

Focused review of Work Unit B should reject the design if any of these are true:

1. a provider API response can directly produce `SATISFIED` without behavioral observations;
2. terminating-proxy upstream retries can occur without independent detection;
3. the fixture can control the network fault or self-declare pass;
4. a Subject can know future activation/challenge/control material;
5. the comparator needs provider-name branching;
6. a missing observation becomes success rather than `EVIDENCE_INVALID`/failure;
7. cleanup is not retained as evidence;
8. exact plan/result/artifact bytes cannot be content-addressed;
9. a later reviewer cannot distinguish original assessment from reassessment;
10. the design freezes a provider SPI or normative schema before AEP-0012 is Accepted.

## Non-authorization boundary

This traceability matrix does not authorize implementation, privileged CI, provider integration, normative Network Control surfaces, lifecycle advancement, release/publication, or signing/attestation.

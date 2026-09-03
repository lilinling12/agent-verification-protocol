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

It is not a requirement index, normative Spec mapping, Schema, or TCK registry. Future Accepted work may reorganize IDs or serialization while preserving protocol semantics owned by the AEP/Spec chain.

## Responsibility legend

- **P** — sealed Evidence Plan
- **A** — attempt/challenge materialization
- **F** — deterministic Fixture/exchange accounting
- **W** — independent transport-initiation witness where required
- **O** — normalized portable observation
- **D** — mechanism/witness diagnostics only
- **C** — provider-neutral Comparator
- **B** — retained content-addressed Evidence Bundle
- **N** — required negative assembly
- **L** — lab-specific mechanism responsibility

## Semantic traceability

| Concern | AEP/NPR intent | P | A | F/W | O | C | B | N/L review condition |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Exact semantic baseline | Evidence tests one exact Proposed semantic candidate, not `latest` | ✓ |  |  |  | ✓ C1 | ✓ source commit/AEP ref | Plan without exact source identity is invalid |
| Materialized literal endpoint | DNS/address racing/fallback excluded from base attempt | ✓ | ✓ | F fixture endpoint / W bound endpoint | ✓ destination/context | ✓ C1/C10 | ✓ | Hidden alternate endpoint/fallback negative fails |
| Logical path across classes | terminating and packet-path mechanisms prove same portable claim | ✓ path identity | ✓ | F end boundary | ✓ | ✓ same predicates | ✓ lab binding separated | Native connection identity never portable |
| Exact exchange bytes | TCP byte stream needs deterministic application completion | ✓ byte refs/program | ✓ attempt bytes | F validates exact bytes | ✓ response digest/length | ✓ C2/C4/C5/C7-C9 | ✓ | TCP segment/read/write boundaries irrelevant |
| Fresh attempt | no pre-existing connection/pooling reuse | ✓ phase program | ✓ unique attempt | W/other initiation witness where required | ✓ freshness/initiation facts | ✓ C10 | ✓ | Pool/reuse negative fails closed |
| One Subject initiation | one certified attempt cannot hide Subject retry/reconnect | ✓ | ✓ | independent Subject-side initiation witness boundary | ✓ subject initiation cardinality | ✓ C10 | ✓ | Hidden Subject retry must fail |
| One terminating upstream initiation | proxy cannot hide upstream retry/fallback, including unaccepted attempts | ✓ fixture/path binding | ✓ attempt context | **W mandatory** at independent fixture-side/equivalent transport boundary; F accept count only cross-checks completed connections | ✓ upstream initiation cardinality + witness refs | ✓ C10 | ✓ raw witness + normalization | Provider self-report or `accept()==1` alone is insufficient |
| Attempt-unique challenge | stale/cached/cross-attempt response cannot satisfy current attempt | ✓ challenge rule | ✓ fresh challenge | F validates challenge | ✓ request/response linkage | ✓ C2 etc. | ✓ safe challenge/commitment evidence | Future challenge leakage prohibited |
| Finite observation budget | blackhole cut terminates by evaluator-owned bound, not provider/fixture timeout | ✓ positive finite budget | ✓ | fixture hygiene cannot truncate portable observation as success | ✓ monotonic elapsed/budget expiry | ✓ C4/C5 | ✓ | Early hygiene timeout => invalid/infrastructure, not cut success |
| Pre-trigger traffic | occurrence-triggered fault cannot activate early | ✓ environment binding | ✓ | F if exchange reaches fixture | ✓ result | ✓ C3 | ✓ | EarlyActivation fails |
| Environment activation authority | trigger identity/condition remains Environment-owned | ✓ | ✓ admission after trigger |  | ✓ ordering refs | ✓ C3/C4 | ✓ | Lab cannot redefine occurrence counting |
| Independent activation settlement | control API success does not prove data-plane cut | ✓ P3 | ✓ privileged fresh attempt | F/W raw evidence as applicable | ✓ | ✓ C4 | ✓ | FalseSettled fails even if C5 later cuts |
| Distinct Subject active cut | later Subject attempt independently demonstrates active fault | ✓ P4 | ✓ distinct identity/challenge | F/W | ✓ | ✓ C5 | ✓ | Settlement cannot substitute |
| Mechanism-neutral transport cut | refusal/reset/drop/blackhole normalize to exact exchange non-completion | ✓ budget/exchange | ✓ | F/W raw behavior | ✓ completion facts | ✓ C4/C5 | ✓ diagnostics separate | No errno/provider branching |
| Established connection exclusion | base profile does not claim pre-open connection termination | ✓ fresh program | ✓ no reuse |  | ✓ | ✓ | ✓ | Lab cannot claim stronger native guarantee |
| Target isolation | narrow target cannot be proven by broad outage | ✓ target/control | ✓ control attempt | F where control exchange used | ✓ target/control results | ✓ C6 | ✓ | CollateralTarget fails; unsupported isolation fails closed |
| Clear authority | clear remains privileged evaluator/control-owned | ✓ P6 | ✓ |  | ✓ ordering facts | recovery precondition | ✓ | Provider ack alone non-authoritative |
| Recovery #1 | first fresh success after clear | ✓ P7 | ✓ | F/W | ✓ | ✓ C7 | ✓ |  |
| Recovery #2 | second consecutive fresh success | ✓ P8 | ✓ | F/W | ✓ | ✓ C8 | ✓ | FalseRecovery cannot stop after one success |
| Stability witness | extra distinct fresh success demonstrates no silent reactivation | ✓ P9 | ✓ | F/W | ✓ | ✓ C9 | ✓ | Reactivation/false recovery fails |
| No retry-until-success | recovery is finite sequence | ✓ cardinality | ✓ | W/F accounting | ✓ | ✓ C7-C10 | ✓ | Unbounded lab/provider retry invalid |
| Behavioral path coverage | config/object existence cannot replace behavior | ✓ same path | ✓ | F/W | ✓ phase facts | ✓ C2-C9 | ✓ | BypassFault mandatory |
| Reset/cleanup noninterference | residual provider/witness state cannot affect next Episode | ✓ P10 | ✓ witness | F/W cleanup evidence | ✓ | ✓ C11 | ✓ | ResidualState fails |
| Schedule/control secrecy | future schedule/control/challenges evaluator-private | ✓ projections | ✓ release boundary |  | ✓ leak evidence | ✓ C12 | ✓ | ScheduleLeak fails |
| Failure vs Validity | infrastructure/evidence failure cannot become semantic pass | ✓ |  | W/F ambiguity retained | ✓ validity problems | ✓ taxonomy | ✓ | Missing/conflicting evidence fails closed |
| Provider-neutral identity | portable evidence excludes native IDs | ✓ logical IDs | ✓ | F/W refs normalized | ✓ portable refs | ✓ | ✓ diagnostics namespaced | Provider/witness native IDs remain D |
| Mechanism/witness provenance | exact artifacts/revisions auditable | ✓ lab binding |  | W revision where required |  | C1 precondition | ✓ | Upgrade creates new reviewed evidence baseline |
| Two independent classes | terminating + packet-path evidence before acceptance re-review | ✓ class binding |  | same F semantics; W implementation may differ only as plumbing | same O vocabulary | same C | paired B | Comparator expectations identical |
| Required negatives | wrong implementations fail same predicates | ✓ negative mode | ✓ | F/W may participate | ✓ | ✓ unchanged | ✓ | bypass, early, false-settled, false-recovery, leak, retry/fallback, collateral, residual |

## Comparator predicate coverage

| Comparator predicate | Positive phase/evidence | Primary violations caught |
|---|---|---|
| C1 Plan integrity/materialization | sealed plan + exact baseline + endpoint/exchange/budget/lab/witness completeness | mutable/ambiguous plan, unresolved endpoint, wrong source, missing required witness binding |
| C2 Baseline | P0 | broken fixture/path, stale challenge, non-baseline state |
| C3 Pre-trigger/no early activation | P1/P2 | EarlyActivation |
| C4 Activation settlement | P3 | FalseSettled, control-plane-only proof |
| C5 Subject active cut | P4 | BypassFault, inactive/wrong target |
| C6 Target isolation | P5 when materialized | CollateralTarget |
| C7 Recovery #1 | P7 | clear did not restore path |
| C8 Recovery #2 | P8 | transient-only recovery / retry-until-success |
| C9 Stability witness | P9 | silent reactivation / false recovery |
| C10 One-initiation/fallback integrity | every certified attempt; terminating runs require independent upstream initiation witness | hidden Subject retry, proxy upstream retry including failed/unaccepted retries, address/path fallback, pooling reuse |
| C11 Cleanup/reset noninterference | P10 | residual provider/witness fault state |
| C12 Security/projection integrity | entire run | schedule/control/future challenge leakage |

## Evidence artifact traceability

| Artifact | Producer | Consumer | Portable authority? | Integrity binding |
|---|---|---|---|---|
| Exact Evidence Plan bytes | materializer/evaluator | labs/comparator/reviewers | governed evidence input; not protocol Schema | SHA-256 + byte length |
| Per-attempt request bytes | evaluator | Subject/Fixture/comparator | portable evidence fact for run | SHA-256 + byte length |
| Per-attempt expected-response bytes | evaluator | Fixture/comparator | portable evidence fact for run | SHA-256 + byte length |
| Fixture exchange event log | Fixture | normalizer/comparator/review | independent exact-byte exchange evidence | exact-byte digest + refs |
| Raw transport-initiation witness record | independent witness | normalizer/review | **No native protocol authority**; supports normalized initiation fact | exact-byte digest + witness revision |
| Normalized initiation observation | normalization responsibility | comparator/review | comparator input, not normative wire format | exact-byte digest + raw witness refs |
| Portable observation record | normalization responsibility | comparator/review | comparator input, not normative wire format | exact-byte digest + refs |
| Mechanism/witness diagnostics | mechanism/witness | debugging/review | **No** | retained/digested when useful |
| Evidence Result | assembly | comparator/review | execution evidence, not normative verdict | SHA-256 + byte length |
| Comparator assessment | comparator | review/acceptance evidence | project assessment against AEP candidate | comparator revision + digest |
| Evidence bundle manifest/root | retention | review/reassessment | review handle, not authenticity proof | exact-byte digest |
| Signature/attestation | not part of work unit | future trust/release work | not authorized | separately governed |

## Failure-localization matrix

| First failed predicate | Required interpretation | Forbidden interpretation |
|---|---|---|
| C1 | invalid evidence input/materialization | provider best-effort pass |
| C2 | baseline/infrastructure/evidence failure depending cause | active-fault success |
| C3 | semantic violation: early activation | trigger considered satisfied early |
| C4 | settlement semantic/evidence failure | infer settlement from later Subject cut |
| C5 | active-cut semantic violation if evidence valid | provider API status substitute |
| C6 | target-scope violation / unsupported | narrow-target pass despite broad outage |
| C7-C9 | recovery violation/evidence failure | retry until success |
| C10 | attempt-integrity violation/evidence-invalid/unsupported; missing upstream witness cannot pass | infer one initiation from one fixture accept or provider self-report |
| C11 | cleanup/noninterference failure | ignore because active cut passed |
| C12 | security semantic violation | redact after fact and call run clean |

## Reassessment traceability

A later reassessment can remain non-live only when every new comparator predicate can be evaluated from already retained immutable artifacts.

| Change | Reassessment sufficient? | New live run required? |
|---|---:|---:|
| comparator bug fix using same observations | ✓ |  |
| report wording only | ✓ |  |
| stronger predicate using observations already retained | ✓, with new assessment lineage |  |
| predicate needs upstream-initiation witness not retained |  | ✓ |
| old run retained only fixture accepts, not failed/unaccepted initiation witness |  | ✓ |
| exact mechanism/witness artifact identity unknown |  | ✓ |
| challenge/attempt binding unverifiable |  | ✓ |
| new mechanism class/version claimed as acceptance evidence |  | ✓ |
| material AEP semantic change | only after explicit review shows retained facts fully answer new semantics | otherwise ✓ |

## Review gates before mechanism implementation

Focused review MUST reject the design if any are true:

1. provider API response can directly produce `SATISFIED` without behavioral observations;
2. terminating upstream retries, including retries that never reach application `accept()`, can occur without independent detection;
3. fixture `accept()` count is treated as proof of total upstream initiation count;
4. transport-initiation witness can mutate fault/path behavior or relies only on provider self-report;
5. fixture can control the network fault or self-declare pass;
6. Subject can know future activation/challenge/control material;
7. comparator requires provider-name branching;
8. missing/ambiguous observation becomes success rather than invalid/unsupported/failure;
9. fixture/provider hygiene timeout can fire early and be counted as portable transport-cut success;
10. cleanup does not include witness state/resources;
11. exact plan/result/raw evidence bytes cannot be content-addressed;
12. later reviewer cannot distinguish original assessment from reassessment;
13. reassessment can silently use old evidence to claim materially changed semantics without explicit sufficiency review;
14. design freezes provider/witness SPI or normative schema before AEP-0012 Accepted.

## Non-authorization boundary

This matrix does not authorize implementation, packet capture/eBPF/nft-counter or other witness technology, privileged CI, provider integration, normative Network Control surfaces, lifecycle advancement, release/publication, or signing/attestation.

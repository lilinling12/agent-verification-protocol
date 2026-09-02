# Alpha 3 AEP-0011 Browser Acceptance Evidence Disposition

Status: **EVIDENCE GATE SATISFIED — ACCEPTANCE-ORIENTED PROTOCOL RE-REVIEW REQUIRED**

AEP: `rfcs/AEP-0011-browser-resource-profile.md` (`Proposed`)

Protocol blocker-resolution parent: PR #108, exact head `4da88bd5fdbaca8fa479b6128e20511e8355d207`

Evidence PR: #109

Evidence exact head: `103c049c51d199c3c744f675283aa8480ca20774`

This record closes only the executable acceptance-evidence obligation identified by BPR-003, BPR-004, and BPR-009. It does **not** change AEP-0011 lifecycle status, authorize `Proposed -> Accepted`, authorize Browser normative Spec/Schema/TCK work, or authorize a Browser reference runtime.

## 1. Evidence architecture

The evidence stack deliberately separates four authorities:

1. AEP-0011 protocol semantics remain protocol authority.
2. Standards/WPT/browser documentation remain external evidence inputs.
3. Native or Playwright browser-control transports are test transport only.
4. AVP evaluator/control-owned evidence decides whether a selected state projection or restore claim is supportable; transport lossiness never weakens the protocol.

No provider cookie serialization, browser profile path, storage partition token, native handle, or automation object becomes portable AVP state identity.

## 2. Exact-head gate state

At evidence head `103c049c51d199c3c744f675283aa8480ca20774`, all twelve pull-request workflows completed successfully:

| Workflow | Run | Result |
| --- | ---: | --- |
| CI #685 | `33328825104` | SUCCESS |
| Relational Parity #78 | `33328825105` | SUCCESS |
| Browser Recovery Residual Evidence #11 | `33328825106` | SUCCESS |
| Browser Shipping Partition Evidence #4 | `33328825107` | SUCCESS |
| Browser Shipping Cookie Fidelity Evidence #2 | `33328825109` | SUCCESS |
| Governance #756 | `33328825110` | SUCCESS |
| Browser Cookie Partition Evidence #33 | `33328825111` | SUCCESS |
| Browser Acceptance Evidence #36 | `33328825113` | SUCCESS |
| Browser Selection Evidence #23 | `33328825120` | SUCCESS |
| Browser Shipping Residual Evidence #3 | `33328825122` | SUCCESS |
| Browser Settlement Evidence #29 | `33328825128` | SUCCESS |
| Browser Shipping Cookie Provenance Evidence #1 | `33328825158` | SUCCESS |

Workflow success is necessary but not sufficient. The key shipping artifacts were separately inspected for exact-source binding and semantic disposition.

## 3. Shipping product evidence

The native matrix exercised shipping products rather than Playwright-managed engine builds:

- Chromium family: Google Chrome `151.0.7922.173`, ChromeDriver `151.0.7922.138`;
- Gecko family: Mozilla Firefox `154.0`, geckodriver `0.37.1`;
- WebKit family: Safari `26.5.2`, native safaridriver `21624.2.5.11.8` on the fixed macOS 26 hosted-runner lane.

The matrix did not add AVP privacy flags or preferences to make the products behave alike.

## 4. BPR-003 — cookie identity/projection disposition

### 4.1 Lossy-transport negative boundary

Shipping Cookie Fidelity evidence proves across all three products that:

- host-only and domain-scoped cookies are behaviorally distinct under HTTP delivery;
- Classic WebDriver cookie objects do not expose the AVP-required `hostOnly` field;
- domain presentation is not used to infer `hostOnly`;
- a projector relying only on that lossy serialization rejects positive projection rather than weakening `(name, domain, hostOnly, path)` identity.

This proves the required fail-closed boundary.

### 4.2 Positive independently reviewable projection path

Shipping Cookie Provenance evidence then demonstrates the positive implementation class explicitly permitted by AEP-0011:

- evaluator/control authority owns complete current cookie-creation/mutation provenance;
- native WebDriver contributes current-state observation only;
- current observable cookie state and provenance must join one-to-one and remain consistent;
- provenance supplies the explicit host-only/domain-scoped distinction without inference from provider domain text;
- missing, stale, ambiguous, or inconsistent provenance fails closed;
- provenance digest is Evidence identity and is **not** BrowserStateImage identity.

BAE-001 passes for Chromium, Gecko, and WebKit in this provenance-complete admitted class. The fixture also injects an untracked selected cookie and verifies that it is rejected rather than silently projected.

**Disposition: BPR-003 acceptance-evidence obligation SATISFIED.**

This does not require every backend to implement this provenance mechanism. A backend without an independently reviewable lossless mechanism remains required to fail closed.

## 5. BPR-004 — temporal semantics and restore fidelity disposition

### 5.1 Stored Default versus explicit Lax

Shipping Cookie Fidelity evidence shows that Classic WebDriver is not portable authority for stored SameSite state:

- Chrome reports the controlled Default cookie as `Lax`;
- Firefox and Safari report it as `None`;
- explicit `SameSite=Lax` remains independently behaviorally testable;
- AVP never normalizes the controlled stored Default cookie to Lax.

Shipping Cookie Provenance evidence demonstrates a positive path in which evaluator/control provenance records whether the controlled `Set-Cookie` operation omitted SameSite (`Default`) or explicitly supplied `Lax`. BAE-002 passes across Chromium, Gecko, and WebKit without treating transport SameSite serialization as authority. Unknown stored SameSite provenance is rejected.

### 5.2 Creation-time-sensitive restore

Shipping Cookie Fidelity BAE-003 demonstrates the fail-closed temporal boundary across all three shipping products:

- Classic WebDriver exposes no arbitrary historical creation time;
- explicit Lax is not sent on the controlled cross-site unsafe POST;
- fresh Default compatibility behavior differs by shipping product/build and therefore is not a portable assumption;
- when the materialized Scenario declares creation-time-sensitive behavior material, restore eligibility is false when historical creation time/equivalence cannot be established.

### 5.3 Positive eligible restore class

Shipping Cookie Provenance BAE-008/009 demonstrates a positive restore/reset class where the selected controlled cookie is explicit `SameSite=Lax`, creation-time-sensitive behavior is explicitly non-material, cookie-header ordering is non-material, and the selected state is independently reprojected after restore/reset.

Across Chromium, Gecko, and WebKit:

- snapshot -> mutation -> restore -> independent reprojection succeeds;
- reset -> immutable baseline reprojection succeeds;
- successful fidelity is exactly `STATE_EQUIVALENT`;
- `EXACT` is never claimed;
- backend command success is not the oracle;
- outside the provenance-complete/temporally eligible class the disposition remains fail-closed.

**Disposition: BPR-004 acceptance-evidence obligation SATISFIED.**

## 6. BPR-009 — required three-engine matrix disposition

The required matrix is now represented by complementary evidence slices:

| BPR-009 required area | Evidence disposition |
| --- | --- |
| selected unpartitioned cookie identity/projection | Shipping Cookie Fidelity + Shipping Cookie Provenance |
| host-only vs domain-scoped cookie behavior | BAE-001, Playwright diagnostic + shipping native behavior/provenance |
| `SameSite=Default` and temporal restrictions | BAE-002/003, shipping fidelity + provenance |
| admitted unpartitioned `localStorage` tuple-origin behavior | BAE-005 |
| partitioned-state rejection/non-admission | Shipping BAE-006; Chrome/Firefox/Safari observe partitioned third-party state without AVP partition-key identity |
| lossless Web Storage string behavior | BAE-007 exact UTF-16 code-unit round trip |
| independent post-restore/reset reprojection | BAE-008/009, including positive provenance-complete shipping path |
| settlement fail-closed behavior | BAE-010 positive mutation-ledger settlement witness |
| residual-state isolation assumptions | Shipping BAE-011 using separate native sessions with Service Worker/Cache + IndexedDB residue and fresh-session isolation |

Shipping partition artifacts at the evidence head:

- Chrome artifact `9737030816`, digest `sha256:eff5ede2ff40a117c1e8524558fa88a8b9dd9ec2f28cdf0d4a60cea8eaa4929b`;
- Firefox artifact `9737041531`, digest `sha256:5b0575d93c8598a1253e14d90b7ea3ae79ed4f75bd4e898fb98e61e93120484f`;
- Safari artifact `9737047208`, digest `sha256:23a442b5dee98cfd7267143911be40091db7ba5facc52c500419ac8993dddd21`.

Shipping cookie-fidelity artifacts:

- Chrome `9737032640`, digest `sha256:f2b6fa0e332cb5e3c4dbd3b35b35e448bf1fbdce351febcc9cb2a35f0f1f15fd`;
- Firefox `9737033828`, digest `sha256:9c6ad5c4924779aa725b2b6b1a0f30d45a4a1bb569ba5e76522fcdd7bfe20904`;
- Safari `9737047336`, digest `sha256:2dfddf3e8faad972f5ea297b3027eb03549dac9cb9caac957b0ff4ad2a71cbc1`.

Shipping cookie-provenance artifacts:

- Chrome `9737032950`, digest `sha256:d03cbaf24f2c83caf58004b41b6f93d94e3ace2506df6e150f4bb45698c8acd9`;
- Firefox `9737034349`, digest `sha256:5725d0c1372ed7cf58d6e3134ecac2293e65b1b0df09e6eea4371f90163c51fb`;
- Safari `9737046468`, digest `sha256:2819fbac3163feae8dbf52588fe246a739a0c447068bd06b89853af6f34af84a`.

Shipping residual artifacts:

- Chrome `9737047222`, digest `sha256:bd754034dee1b295689b5303e4c5da9e863747bfd8b87d92c35842ed81e34937`;
- Firefox `9737043215`, digest `sha256:0f97fb9e9788bb4512cc69f2559f68131bd97e3fa3968cf638dc40c9b432f78c`;
- Safari `9737051760`, digest `sha256:e8b543c26633918df3da8348a58ddb1035e3d0c7adbb8e7439e7cf424058f6cb`.

All listed artifacts are exact-head artifacts for `103c049c51d199c3c744f675283aa8480ca20774`.

**Disposition: BPR-009 executable acceptance-evidence gate SATISFIED.**

## 7. What this evidence does not authorize

This record does not authorize or imply:

- AEP-0011 `Proposed -> Accepted`;
- Browser normative Spec or requirement-index work;
- Browser Schema work;
- Browser language-neutral TCK or conformance harness work;
- Playwright/reference-runtime implementation;
- a requirement that every third-party implementation support all three browser families;
- promotion of evaluator/control provenance into portable BrowserStateImage identity;
- treating a provider serialization as protocol authority;
- any release, publication, signing, attestation, repository split, or plugin framework.

## 8. Remaining governance gate

The evidence obligation is now complete, but AEP-0011 is not yet acceptance-ready by declaration. The next required step is an **acceptance-oriented exact-head protocol re-review** over:

- AEP-0011 Proposed text;
- the formal Proposed review and blocker ledger;
- this evidence disposition;
- the exact-head executable evidence stack;
- cross-contract consistency with Environment Fabric, Core, Scenario, Security, and Evidence.

That re-review must actively search for new semantic ambiguity; it must not merely restate that workflows are green. In particular, downstream canonical identity/digest determinism, selection semantics, authority boundaries, and restore-fidelity wording remain review targets.

Only if that independent re-review finds no remaining semantic blocker may AEP-0011 be described as **acceptance-ready**. A separate explicit protocol-maintainer authorization is still required for `Proposed -> Accepted`.

## Conclusion

```text
Evidence exact head: 103c049c51d199c3c744f675283aa8480ca20774
Exact-head workflow matrix: 12/12 SUCCESS
BPR-003 acceptance evidence: SATISFIED
BPR-004 acceptance evidence: SATISFIED
BPR-009 acceptance-evidence matrix: SATISFIED
Acceptance-oriented exact-head protocol re-review: REQUIRED / NOT YET COMPLETED
AEP-0011 lifecycle: Proposed
Proposed -> Accepted: NOT AUTHORIZED
Browser normative downstream work: NOT AUTHORIZED
```

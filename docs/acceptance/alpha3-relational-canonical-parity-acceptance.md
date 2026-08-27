# Alpha 3 PostgreSQL/MySQL Canonical Parity Acceptance

Status: **ADOPTED ON MAIN — CANONICAL PARITY ACCEPTANCE CLOSED**

Source pull request: PR #96  
Final reviewed PR head: `ae5e31c8a080239b81c1204cf141f6ca688302a0`  
Adopted main commit: `0bc12cdecd7d35292d2720adb0963e66ebeb509d`  
Merge method: squash  
Exact-main CI: #612 (`33048968550`)  
Exact-main Relational Parity: #5 (`33048968491`)

Governing authority:

- AEP-0009 — Environment Fabric Composition and Capability Contract (`Accepted`);
- AEP-0010 — Relational State Resource Profile v0.1 (`Accepted`);
- `spec/relational/relational-state-contract.md`;
- `spec/relational/manifest-integrity-contract.md`;
- `spec/relational/requirement-index.yaml`;
- `conformance/tck/profiles/avp-relational-state-v0.1.yaml`;
- `conformance/fixtures/relational-state/v0.1/parity-fixture.json` and its SHA-256 lock.

This acceptance record is implementation evidence. It does not create or amend
portable protocol semantics. Authority remains one-way:

```text
Normative Spec -> Schema -> TCK -> Reference Runtime
```

## 1. Acceptance question

The PostgreSQL and MySQL/InnoDB adapters already pass the complete mandatory
Relational State profile independently. Independent green backend lanes are not,
by themselves, cross-backend parity evidence.

This work asks the stronger question:

> When both real database implementations consume the same immutable portable
> fixture in one paired execution, do they reproduce the same canonical AVP
> observations wherever the profile defines canonical equality, without making
> either database product the oracle?

The adopted implementation evidence answers **yes**.

## 2. Parity rule

The implementation follows the gate established by the Relational Backend
Implementation Readiness audit:

- canonical state/projection/diff equality is exact;
- backend SQL, physical types, indexes, catalog order, MVCC tokens, transaction
  handles, and product identity are not compared as portable state;
- a concurrent multi-relation observation may independently select a complete
  pre-commit or complete post-commit view on each backend;
- a torn observation is forbidden;
- therefore PostgreSQL and MySQL are not required to select the same valid side
  of a concurrent commit.

This distinction prevents implementation scheduling from being promoted into a
new protocol requirement.

## 3. Evidence architecture

`src/avp_ref/tck_adapter/relational_parity.py` adds an implementation-private,
backend-neutral `RelationalParityVerifier`.

The verifier depends only on:

- `RelationalBackendHarness`;
- the immutable typed parity fixture;
- existing portable Relational State value objects and canonical serializer.

It contains no PostgreSQL/MySQL SQL, driver APIs, database names, role names,
physical storage mappings, or product branches. Both backends are checked against
the locked fixture and against each other, so neither backend is accepted as the
expected-output authority.

The verifier also rejects using the same harness instance under multiple labels,
which prevents one implementation instance from masquerading as cross-backend
parity evidence.

## 4. Canonical observations verified

The paired execution verifies the following portable evidence.

### 4.1 Manifest and baseline state identity

Each backend must reproduce the fixture's exact Manifest digest and baseline
StateImage digest. The baseline StateImage canonical documents must also compare
byte-for-byte across the paired implementations.

Fixture expectations:

- Manifest: `sha256:5a25e6ef4163545bf200f6ed4a07a49c957bdf045f939a9544f09a48049293dc`;
- baseline StateImage: `sha256:c66ecc20bc2420d81134348893bbe8f712eb446a4d6a511baad9cd0bd490afc0`.

### 4.2 Named projections

Every projection declared by the shared Manifest is evaluated independently by
both real databases. Each result must match the fixture digest and the canonical
projection bytes must be identical across backends.

Locked projection expectations:

- `consistency.pair`: `sha256:662a780a3a4297f1c7635f741d7e5619b7aea5e2000644c42a566623a2a711a9`;
- `parity.all`: `sha256:b517c32d2b02bb579919de5670fec5473cbbea50003aaf98644f09520dd5344f`;
- `parity.keys-and-values`: `sha256:29262b26ce5ac46b8767505eda6f53c8e27b4af5526e74d54e0258afb07ce938`.

This exercises exact canonical scalar behavior including large integer and
decimal values, composed/decomposed Unicode identity, binary values, temporal
precision, UUIDs, nullable values, composite logical keys, and canonical row
ordering through the existing fixture.

### 4.3 Snapshot StateImage

Snapshot identifiers and backend-native snapshot mechanisms are intentionally not
compared. The portable `snapshot.state` StateImage must be canonical-equal across
backends and equal to the fixture baseline state identity.

### 4.4 Atomic multi-relation mutation

Each backend independently coordinates the fixture's one logical atomic epoch
mutation across `consistency.left` and `consistency.right`.

The observation made around the commit must be one of the fixture-authorized
complete states:

```text
("1", "1")
("2", "2")
```

`("1", "2")` and `("2", "1")` are torn and fail acceptance. PostgreSQL and
MySQL may choose different members of the authorized set because commit timing is
not portable identity.

After the commit, both backends must reproduce exactly:

`sha256:84fa44c94603f7267addba726f50a74710c590a35b744e315c8850f28574d95c`

and the canonical post-commit StateImage documents must be byte-identical.

### 4.5 Semantic diff

Each backend computes the portable diff from the original baseline to the same
post-commit state. Both must match the fixture's exact diff digest:

`sha256:d9874eff9c8b3e91dce71ca9232bcae5cd6b2bf278eb4f696cfb25f91a05af5a`

and canonical diff documents must compare byte-for-byte. The expected logical
changes remain UPDATEs of logical key `id=1` in both consistency relations.

### 4.6 Restore

Each backend:

1. independently re-establishes baseline;
2. takes its own SnapshotRef;
3. applies the atomic mutation;
4. restores its own snapshot;
5. independently re-projects full authoritative state.

Successful fidelity must be exactly `STATE_EQUIVALENT`, never `EXACT`, and the
restored StateImage must equal the locked baseline identity and be canonical-equal
across backends.

### 4.7 Reset

After another atomic mutation, each backend independently resets and re-projects
full authoritative state. Both reset results must equal the locked baseline
StateImage and each other canonically.

## 5. Test layering

Two complementary test layers are used.

### 5.1 Quality-gate orchestration test

`tests/test_relational_parity.py` executes the verifier through two independent
in-memory harness instances on Python 3.11, 3.12, and 3.13 quality lanes. This
ensures verifier control flow, fixture binding, lifecycle sequencing, exact
comparison, and duplicate-harness rejection are exercised even when database
integration credentials are absent.

This test is not real-database parity evidence.

### 5.2 Real paired database acceptance

`tests/test_relational_backend_parity.py` executes the same verifier with one real
PostgreSQL harness and one real MySQL harness in the same process and same test
run.

`.github/workflows/relational-parity.yml` builds a wheel, installs that wheel with
both optional relational dependencies into a clean virtual environment, verifies
both live server identities, and then executes the paired acceptance test.

The accepted matrix is deliberately composed of two real product pairs:

- PostgreSQL 17.11 + MySQL 8.4.11;
- PostgreSQL 18.6 + MySQL 9.7.2.

The existing independent PostgreSQL and MySQL full-TCK lanes remain in the normal
CI workflow and are not replaced by this parity gate.

## 6. Exact-head implementation acceptance

An earlier implementation evidence head,
`f551fd510997b1e94a1ea56887b824c01e4b6caf`, established the initial real-database
candidate evidence in CI #610, Governance #675, and Relational Parity #3. The
acceptance-document commit changed the PR head after that execution, so those
runs were correctly treated as preliminary rather than reused as final-head
acceptance.

The final reviewed PR #96 head was:

`ae5e31c8a080239b81c1204cf141f6ca688302a0`

Exact-head acceptance evidence on that final head:

- CI #611 (`33048226831`) — **SUCCESS**;
- Governance #676 (`33048226885`) — **SUCCESS**;
- Relational Parity #4 (`33048226830`) — **SUCCESS**;
- formal exact-head review `5038102614` — **READY ELIGIBLE**;
- Ready-state Governance #677 (`33048372618`) — **SUCCESS**.

CI #611 preserved the full repository acceptance surface: Quality on Python
3.11/3.12/3.13, reproducible Package construction, clean base-wheel consumer
installation, installed-wheel identity/smoke/full registered TCK conformance,
release-evidence build/verification, PostgreSQL 17.11/18.6 Relational TCK lanes,
and MySQL 8.4.11/9.7.2 Relational TCK lanes.

Relational Parity #4 completed both real paired-database jobs successfully:

- PostgreSQL 17.11 + MySQL 8.4.11 / Canonical Parity / Python 3.13;
- PostgreSQL 18.6 + MySQL 9.7.2 / Canonical Parity / Python 3.13.

Each job built the parity-capable wheel, installed both optional backend
dependencies, verified the paired server identities, and executed the real
PostgreSQL/MySQL canonical parity acceptance path.

The formal review found no blocker and authorized the Ready transition only; it
did not authorize its own merge or any protocol/release lifecycle transition.

## 7. Main adoption evidence

The protocol maintainer explicitly authorized squash merge of PR #96 on
2026-08-27. GitHub adopted the reviewed implementation/evidence as exact main
commit:

`0bc12cdecd7d35292d2720adb0963e66ebeb509d`

Exact-main validation then completed successfully:

- CI #612 (`33048968550`) — **SUCCESS** on exact
  `0bc12cdecd7d35292d2720adb0963e66ebeb509d`;
- Relational Parity #5 (`33048968491`) — **SUCCESS** on the same exact main
  commit.

Relational Parity #5 executed both supported real paired-database matrices from a
built wheel. Independent PostgreSQL/MySQL TCK lanes and the installed-wheel full
registered TCK remained green in CI #612.

The canonical parity implementation/evidence was therefore adopted and verified
on `main`. Later main changes have continued to exercise this gate; for example,
Relational Parity #11 (`33053079311`) completed successfully on
`main@a77e3bc9039e81d5443125c5ce4229236c258f65` for both supported product pairs.
This later regression evidence supplements, but does not replace, the exact
main-adoption evidence tied to PR #96.

## 8. Adoption conclusion and ROADMAP reconciliation

**ADOPTED ON MAIN — CANONICAL PARITY ACCEPTANCE CLOSED.**

The real PostgreSQL and MySQL/InnoDB implementations have direct paired evidence
that they reproduce the same portable canonical Relational State observations
under the immutable shared fixture while preserving legitimate backend scheduling
freedom at the concurrent commit boundary.

The corresponding `ROADMAP.md` item may therefore be marked complete as an
implementation-evidence milestone. That checkbox does not make either database
implementation normative and does not change the authority chain.

## 9. Scope boundary and non-authorizations

This adoption/reconciliation does not modify or authorize:

- AEP-0009 or AEP-0010 lifecycle state, including any `Final` transition;
- normative Relational State or Manifest-integrity specification;
- requirement index;
- Relational State schemas;
- language-neutral TCK profile/case semantics;
- shared parity fixture bytes or its lock;
- PostgreSQL adapter portable behavior;
- MySQL adapter portable behavior;
- release-development state or release selection;
- release tagging or publication;
- package-index publication;
- signing or attestation publication.

PostgreSQL/MySQL parity remains implementation/conformance evidence under the
existing portable authority; it is not a new source of protocol semantics.

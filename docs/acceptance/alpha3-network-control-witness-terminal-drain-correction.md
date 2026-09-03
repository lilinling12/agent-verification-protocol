# Alpha 3 Network Control Witness Terminal-Drain Correction

Status: **PROVIDER-NEUTRAL EVIDENCE PREREQUISITE — REVIEW REQUIRED BEFORE TEL-RB-003 / TEL-003**

Prepared: 2026-09-03

Baseline: `dd4850651297b9083ec0da3672f3dcdfc7cdb430`

## 1. Problem

The main-adopted `LinuxSynWitness` arms an AF_PACKET socket before attempt admission and closes it after the evaluator reaches the certified attempt terminal observation boundary.

The previous capture loop used the stop flag as its loop predicate:

```text
while not stop:
    recvfrom(...)
```

`close()` set that flag before joining the capture thread. A real SYN could therefore already be queued by the kernel for the AF_PACKET socket while the capture thread had not yet consumed it. If `close()` won that race, the thread could observe the stop flag and exit without reading the queued frame.

That is an evidence-under-count risk. For Network Control, an under-count can hide a real retry/reconnect/fallback initiation and is therefore not acceptable as a trustworthy NPR-011 witness boundary.

## 2. Correction

The correction keeps the same arm/admit/terminal/close lifecycle and does not change portable evidence semantics.

After `close()` marks the terminal boundary, the capture thread continues receiving until the **first existing bounded socket inactivity timeout**. Frames available during this terminal drain are normalized and retained exactly as frames received before the close signal.

The operational sequence becomes:

```text
arm
  -> ready acknowledgement
  -> admit one certified attempt
  -> evaluator reaches terminal observation boundary
  -> close signal
  -> bounded AF_PACKET terminal drain
       - consume available frames
       - stop on first receive inactivity timeout
       - if traffic prevents termination, existing bounded join fails closed
  -> read PACKET_STATISTICS
  -> seal raw witness + normalized facts
```

No arbitrary sleep and no unbounded wait are introduced.

## 3. Why conservative tail observation is acceptable

The witness is attached to an isolated, run-scoped role boundary and intentionally observes all outgoing initial SYNs from that role, including alternate destinations.

For this evidence responsibility, dropping a boundary-adjacent SYN is unsafe because it can produce a false one-initiation result. Retaining an additional role SYN that becomes visible during the bounded terminal drain is conservative: it can only preserve the expected one-initiation result or expose additional initiation behavior that must fail the comparator/integrity review.

The correction therefore chooses **no false-negative initiation under-count** over a narrower stop-flag race window.

This does not extend portable protocol time semantics. The drain timeout is Linux witness plumbing and remains non-normative implementation detail.

## 4. Boundedness and failure policy

The AF_PACKET socket already uses a finite `0.1s` receive timeout. The terminal drain ends on its first inactivity timeout after the close signal.

`close()` retains its finite `2.0s` thread join. If continuous traffic prevents the capture thread from reaching an inactivity timeout, the witness records `capture-thread-did-not-stop`, and the evidence remains fail-closed.

Capture statistics, drop checks, interface identity, directionality, assurance checks, raw-byte retention, and retransmission normalization remain unchanged.

## 5. Regression proof

The prerequisite adds deterministic tests using a controlled fake capture queue:

1. a SYN already queued when the close signal is set must still be retained;
2. an empty queue after close stops on the first bounded inactivity timeout;
3. multiple queued independent SYNs are all retained before the inactivity boundary.

The first test fails against the prior `while not stop` implementation by producing zero observations and passes only when terminal draining is present.

## 6. Governance boundary

This correction is provider-neutral witness evidence plumbing. It does not:

- alter AEP-0012 semantics or lifecycle;
- introduce a provider/backend SPI;
- change C1-C12 portable comparator rules;
- authorize TEL-RB-003 privileged workflow adoption;
- claim TEL-003 terminating evidence;
- authorize Spec/Schema/TCK changes, release, publication, signing, or attestation.

PR #150 must remain Draft/frozen until this prerequisite is independently reviewed, merged, and post-merge validated. TEL-RB-003 must then be reconciled onto the new exact main baseline and rerun through its own gates/security review.

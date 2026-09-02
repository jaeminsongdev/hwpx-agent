# P04-06 Workspace transaction report

- Generated: 2026-09-02
- Audited source commit: `8a6d258cf2edbc155bcf8851715c2487fee8cbff`
- State: `pass_current_pc_local_transaction_core`
- Reasoning/review mode: `xhigh / filesystem, recovery, CAS and publication boundary`

`operation-engine`에 compiled plan, exact route set, source artifact identity와 base revision을
하나의 immutable manifest로 묶는 filesystem transaction을 구현했다. 원본은 read-only로만
관측하며, output은 per-job staging→bounded readback→validator→content-addressed no-overwrite
publication→revision CAS 순서로만 승격된다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Manifest binding | `pass` | plan/route/source/base revision/target/registry hashes in `hwpx-agent.execution-manifest/v1` |
| Finite state machine | `pass` | 10 success states plus explicit rollback/quarantine/incomplete recovery states |
| Source immutability | `pass` | read-only open, canonical path/size/SHA observation before and after every outcome |
| Workspace isolation | `pass` | SHA-256 job name, canonical containment, symlink/reparse and workspace-overlap denial |
| Staged validation | `pass` | create-new staging, bounded readback SHA/size and caller validator before publication |
| Atomic publication | `pass` | same-workspace hard link, parent durability boundary and no-overwrite content path |
| Revision CAS | `pass` | artifact commit and revision CAS are separate typed steps |
| Failure recovery | `pass` | pre-publication rollback; post-publication CAS failure moves complete bytes to quarantine |
| Fault model | `pass` | before/after all 9 normal steps plus rollback/quarantine recovery points |
| Receipt/privacy | `pass` | deterministic v1 receipt, source outcome/disposition and redacted public Debug |

## Validation evidence

- Windows Rust 1.96.0: transaction `9/9`, full workspace tests, doc tests and Clippy
  `-D warnings` passed.
- Linux Rust 1.96.0: derived image
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`,
  network off, source/registry read-only, Cargo offline; transaction `9/9` and Clippy passed.
- Fault corpus covers 18 normal transition points and 4 recovery points. Every result is absent,
  complete, quarantined or explicitly incomplete; partial bytes are never promoted.
- Source identity mismatch, mid-transaction mutation, validation reject/failure, CAS conflict/failure,
  existing output, traversal-like transaction ID, symlink/reparse, finite limit and single-use cases
  are distinct negative tests.
- Current checkout FULL bootstrap: `5/5` lanes passed.
- Exact implementation commit clean clone FULL bootstrap: `5/5` lanes passed; post-run Git changes 0.
- Security: current and clean clone each scanned 546 files; secrets/vulnerabilities/forbidden
  licenses 0; current SBOM 272 and clean-clone SBOM 230 components.
- P03 and P04-01~05 regressions remain green in both FULL runs.

## Strict self-review and remediations

- Change risk: `high` because this is the first filesystem publication and revision commit boundary.
- Local path dependencies initially lacked explicit versions; `cargo deny` rejected them. Both now
  use exact workspace crate version plus path, after which the security and FULL gates passed.
- Source identity mismatch and an actual mid-flight mutation are classified separately. The latter
  forces `incomplete` even if a complete artifact or revision may already require reconciliation.
- Artifact publication precedes CAS by design. CAS conflict/failure never returns `completed`; the
  complete artifact is quarantined, while quarantine uncertainty remains explicit.
- A transaction object is single-use. A second execution cannot reuse old staging, result hashes or
  receipts and fails with a stable state error.
- Final blocker/major/minor findings after remediation: `0/0/0`.

## Scope and remaining boundary

P04-06 proves the local transaction core with synthetic source/output bytes and callbacks. It does
not execute a direct HWPX patch, Hancom automation, public job service or durable database revision
store. The residual OS/filesystem TOCTOU boundary is reduced by canonical/link checks and post-run
source observation but is not claimed as a hostile multi-user kernel isolation proof. No user
document was opened or changed and no Hancom process was run. Other PCs and Hangul 2022/2024 remain
deferred.

## Next exact task

Start `P04-07 Semantic diff` with reasoning effort `xhigh`. Compare two validated graph snapshots
without mutating them; emit deterministic typed node/style/table/equation/object/reference deltas,
preserve unknown/opaque change visibility, reject identity/version/limit ambiguity and lock golden
diff bytes across Windows/Linux. P04-09 actual Hangul 2020 vertical Gate and the P04 phase Gate
remain `max`. No user local operation is required for P04-07.

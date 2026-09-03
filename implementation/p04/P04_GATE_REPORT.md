# P04 DocumentGraph, OperationPlan and Transactions Gate Report

- Generated: 2026-09-03
- Audited source commit: `6cc11f05d7d80314c6c56169a8cf37f7419a0d33`
- Audit mode: `STRICT / max`
- Overall state: `pass_scoped_current_pc_local`
- P05 authorization: `authorized_current_pc_local_only`

P04-01~09를 현재 PC 로컬 범위에서 구현하고 재현했다. Backend-neutral DocumentGraph에서
selector, typed OperationPlan, evidence/policy router, isolated transaction, semantic diff,
idempotency/revision CAS와 VS-0 vertical CLI까지 하나의 fail-closed 경계로 연결했다. 실제
desktop 증거는 승인된 disposable 생성물을 이 PC의 exact Hangul 2020에서 읽기 전용으로
열고 semantic readback한 범위에만 적용한다.

## Gate criteria

| Criterion | State | Evidence | Remaining boundary |
|---|---|---|---|
| P04-01 DocumentGraph v2 | `pass` | finite typed graph, identity/reference/shape validation, stable serialization 9/9 | Full HWPX lifting is P05+ |
| P04-02 Unit and ID | `pass` | official HWPUNIT, exact checked conversions, typed IDs, 10,000/10,000 property runs | Additional layout spaces are later modules |
| P04-03 Selector | `pass` | exact-one ID/name/path/text-context, zero/multiple/stale fail closed 9/9 | Interactive cursor selectors remain disallowed |
| P04-04 OperationPlan | `pass` | typed selector/unit/default compile, atomic deterministic DAG, 1,000-op corpus | Public planning API is later integration |
| P04-05 Capability router | `pass` | exact target/signed evidence/policy/preservation/health, ambiguity rejection 9/9 | General production routing remains disabled |
| P04-06 Workspace transaction | `pass` | immutable manifest, isolated copy, validated no-overwrite publication/CAS, fault 22/22 | Power-loss durability is not claimed |
| P04-07 Semantic diff | `pass` | nine typed categories, relative-order move, opaque visibility/privacy 10/10 | Visual/rendered diff is not claimed |
| P04-08 Idempotency and CAS | `pass` | exact binding/fencing/replay/reconciliation, 32/16/32 concurrency | Durable multi-process store is P14 |
| P04-09 VS-0 core CLI | `pass` | A4 one paragraph/style vertical, actual exact-2020 open/readback/clean shutdown | Arbitrary editing and visual fidelity are later work |
| Common phase constraints | `pass` | versioned contracts/policies and negative tests; unexecuted claims preserved; source in-place writes 0; failures and handoff recorded | Other PCs/versions/production remain deferred |

## End-to-end evidence chain

```text
versioned bounded request
  -> validated DocumentGraph snapshot
  -> exact selector + deterministic OperationPlan
  -> signed exact-build capability route
  -> idempotency claim + revision expectation
  -> isolated workspace transaction
  -> deterministic P03-validated HWPX
  -> checksum no-overwrite publication + revision CAS
  -> terminal replay receipt
  -> exact Hangul 2020 open/readback/close/Quit
```

## Validation summary

- Exact audited source commit clean clone and current checkout FULL bootstrap: each `5/5` lanes.
- Windows Rust 1.96.0 workspace tests, format and Clippy `-D warnings`: passed. P04 task-specific
  cumulative models and negative corpora remain green; VS-0 package/CLI `6/6` passed.
- Offline Linux Rust 1.96.0 read-only source/registry, network-disabled container: workspace tests and
  Clippy `-D warnings` passed. Image digest:
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`.
- Actual exact Hangul 2020 `11.0.0.9136` x86 STA: generated artifact input identity, document open,
  exact single-paragraph digest/length readback, close and `Quit()` all passed; input mutation, save,
  network, registry/system changes and residual Hangul/child processes were 0.
- Independent actual-bundle verifier positive/negative tests `5/5`; correlated bundle digest
  `b16a24fdbb8480b190607e1df320edcdb8f1cb37cf4d58a81ae5a94242e57048`.
- Security: 571 tracked files scanned, findings/vulnerabilities/forbidden licenses 0. Current SBOM
  components 273; clean-clone security run components 231. Private runtime evidence and signing key
  tracked files 0; user documents opened or modified 0.

## Strict review

- Change risk: `high`; immutable identity, routing, atomic publication, exactly-once semantics and an
  actual desktop boundary are trusted by later phases.
- Verdict: `approve_scoped_current_pc_local`.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Review remediations include transaction terminal control flow, artifact/result digest binding,
  object-safe durable-store boundary, head-before-receipt atomicity, exact route attestation,
  duplicate JSON/numeric/archive-expansion checks and section/preview/runtime semantic correlation.
- Synthetic, cross-platform and component evidence was not promoted to actual Hangul evidence.
  Actual open/readback was not promoted to save, rendering, arbitrary-document or other-version proof.

## Failure fixtures and residual risks

- Invalid graph/reference/shape, overflow/rounding, stale/ambiguous selector, invalid/cyclic plan,
  unsigned/stale/unhealthy route, traversal/symlink/source drift, transaction fault, revision race,
  key-reuse drift, outcome-unknown mismatch, malformed VS-0 request/archive/trace/progress and runtime
  phase drift remain typed negative fixtures.
- Idempotency is intentionally in-memory. Process restart and multi-process exactly-once semantics are
  not met until P14 supplies and restart-tests the durable `IdempotencyStore` implementation.
- VS-0 is create-new only. It does not establish arbitrary HWPX semantic lifting/lowering, real-save
  ID stability, rendered/printed fidelity, native equations or visual comparison.
- Hangul 2022/2024 and other PCs require their own exact profile and evidence later; they are not a
  blocker for the explicitly current-PC development sequence.

## Phase decision

P04 is complete for current-PC local development. P05 may start in the same scope. No production,
provider, server, VM, customer distribution, other-PC or other-version authorization is implied.

## Next exact task

Start `P05-01 Text flow reader/writer` at reasoning effort `max`. Lock a bounded typed model for text
runs, tabs, line breaks and field boundaries; implement deterministic lift/lower against safe and
preserving XML; test Unicode and run-boundary corpora plus fail-closed malformed/limit cases before
starting paragraph style or layout modules.

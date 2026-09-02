# P04-08 Idempotency and revision CAS report

- Generated: 2026-09-02
- Audited source commit: `8a1d35ceb938639dbbad175875af229020e44932`
- State: `pass_current_pc_local_reference_service`
- Reasoning/review mode: `xhigh / concurrency, atomicity, replay and reconciliation boundary`

`operation-engine`에 exact binding, secret owner와 monotonic fencing, terminal replay,
outcome-unknown reconciliation 및 revision-head CAS를 하나의 thread-safe reference service로
구현했다. 객체 안전한 `IdempotencyStore`가 P14 durable 구현이 보존해야 할 atomic storage
경계를 고정하며, 현재 구현은 의도적으로 in-memory다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Exact key binding | `pass` | request/manifest/stream/expected head/transaction 전체 결합, drift conflict |
| Single ownership | `pass` | secret owner hash와 global nonzero fencing generation |
| State model | `pass` | claimed/in-progress/outcome-unknown/succeeded/failed-terminal 분리 |
| Immutable replay | `pass` | terminal retry가 byte-identical canonical v1 receipt만 반환 |
| Revision CAS | `pass` | exact revision+generation, checksum artifact identity, atomic head+record update |
| Unknown reconciliation | `pass` | exact committed-head 또는 unchanged-head observation만 terminal 전환 |
| Durable boundary | `pass` | object-safe `IdempotencyStore`; P14 persistence는 명시적으로 deferred |
| Concurrency | `pass` | 32 claim 중 owner/effect 1, 16 commit 중 success 1, 32 retry 모두 replay |
| Finite behavior | `pass` | record/stream/receipt/artifact limits와 checked counters |
| Privacy | `pass` | key/project/document/owner/binding raw value를 Debug/error/receipt에서 제외 |

## Validation evidence

- Windows Rust 1.96.0: idempotency-specific `11/11`, workspace transaction regression `9/9`,
  operation-engine total `20/20`, doc tests와 Clippy `-D warnings` passed.
- Linux Rust 1.96.0: derived image
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`,
  network off, repository/registry read-only, Cargo offline and executable tmpfs; 동일 `20/20`과
  Clippy passed.
- Deterministic concurrency corpus: 32-thread simultaneous claim은 acquired `1`, duplicate `31`,
  effect counter `1`; cloned lease 16-thread CAS는 committed `1`, rejected `15`; terminal retry
  32-thread storm은 모두 동일 receipt를 replay하고 head generation은 추가 증가하지 않았다.
- Negative corpus: missing/stale head, key binding drift, stale owner/fence, competing claims on one
  head, invalid artifact checksum identity, zero/oversized limits, explicit failure replay,
  committed/no-effect unknown reconciliation mismatch를 fail closed로 확인했다.
- Current checkout FULL bootstrap: `5/5` lanes passed.
- Exact implementation commit clean clone FULL bootstrap: `5/5` lanes passed; post-run Git changes 0.
- Security: current and clean clone each scanned 556 files; secrets/vulnerabilities/forbidden
  licenses 0; current SBOM 272 and clean-clone SBOM 230 components.
- P03 and P04-01~07 regressions remain green in both FULL runs.

## Strict self-review and remediations

- Change risk: `high` because later workers and durable storage will trust exactly-once replay and
  revision ownership decisions.
- Initial commit path could update the head before a theoretically fallible receipt digest call.
  All validation, receipt sizing, digest calculation, stream lookup, record lookup and lease
  validation now complete before the two in-memory fields are mutated.
- Artifact identity now must equal `sha256-<result digest>`; an arbitrary artifact label cannot be
  bound to unrelated bytes.
- The acceptance-required storage trait was absent in the first review. An object-safe atomic
  `IdempotencyStore` contract and trait-object test were added without adding a lint exception.
- Outcome-unknown never hands out a second owner. A committed observation must match binding, key,
  fence, commit digest and current head; a no-effect observation requires the original head unchanged.
- Final blocker/major/minor findings after remediation: `0/0/0`.

## Scope and remaining boundary

This is an in-process reference implementation, not crash-persistent or multi-process storage. P14
must implement the same atomic trait semantics against durable storage and repeat fault/restart tests.
P04-08 performs no filesystem, network, process, COM, HAction or Hancom operation. No user document
was opened or modified. Other PCs and Hangul 2022/2024 remain deferred.

## Next exact task

Start `P04-09 VS-0 core CLI` with reasoning effort `max`. Build one bounded CLI path that creates a
synthetic blank A4/one-style/one-paragraph DocumentGraph, compiles and routes the exact plan, writes
and reopens a no-overwrite HWPX through the transaction and idempotency/CAS contracts, then captures
actual licensed Hangul 2020 open/readback evidence and clean process shutdown. Only disposable
fixtures may be used. Computer Use remains screenshot-only; if Hancom shows an access prompt, the
user performs that single local click.

# P15-04 asynchronous job UX report

- Generated: 2026-09-05
- Implementation commit: `f50c724e8eef0079b7ab64a2a8553c0c37a42015`
- Audited source commit: `4c6224f6001c5daadaaaec907c0bba86db7c6c0f`
- Reasoning/review mode: `max` / strict state-transition, durability, privacy and cancellation audit
- Decision: `pass_scoped_current_pc_local_durable_job_reference`

P15-04 binds the six already-frozen long-running public tools to durable local job submissions and
uses the existing `job_get` and `job_cancel` tools for polling and safe cancellation. The P15-02
structured-output schemas and P15-03 handler order remain unchanged. Ordered, bounded progress is
returned only through `_meta["hwpx/jobEvents"]` after the frozen output schema and correlation checks
pass.

This is a current-PC local durable reference implementation for the licensed Hangul 2020 development
target. It does not qualify a production queue, scheduler, shared database, cross-process writer,
hosted MCP transport or artifact-byte delivery.

## Implemented behavior

- `document_create`, `document_edit`, `document_transform`, `document_validate`, `document_render`
  and `document_export` create or replay deterministic job IDs bound to authenticated tenant,
  project, subject, tool, idempotency key and semantic arguments. A changed transport `request_id`
  does not change an exact semantic replay.
- `job_get` returns a bounded projection plus at most 200 events. Its opaque cursor is bound to the
  exact job and sequence; malformed, foreign and future cursors fail closed.
- Progress has monotonic public states, state-local stages, non-regressing units and non-regressing
  timestamps. At most 248 progress events and 256 total events are retained per job.
- Queued cancellation terminates immediately. Active cancellation records `requested`, blocks more
  progress and terminates only on worker safe-point acknowledgement. Committing jobs return
  `not_cancellable`. Exact cancellation replay returns the first decision; changed key or reason is
  rejected.
- Every terminal path publishes exactly one immutable terminal receipt and one terminal event.
  Further progress or terminalization fails closed.
- The fixed `p15-job-journal-v1.jsonl` is append-only. Each complete snapshot has a global monotonic
  sequence and SHA-256 checksum, and is flushed with `sync_all` before in-memory publication.
- Restart replay rejects duplicate JSON keys, partial final records, sequence/checksum corruption,
  identity drift, event-prefix drift and terminal mutation instead of repairing or guessing.
- The reference store is finite: 4,096 jobs, 65,536 entries, 64 MiB journal, 1 MiB record and 128
  result artifact identifiers. Symlink and non-directory roots are rejected.
- Raw arguments, bearer values, document content, local paths and raw cancellation reasons are not
  journaled or exposed in debug output.

## Source identity

| Source | Bytes | SHA-256 |
|---|---:|---|
| `crates/mcp-control-plane/Cargo.toml` | 612 | `9071541155fcfb9f1c239df32307cbf4176c7503118c1ca2f8563986f9aaf268` |
| `crates/mcp-control-plane/src/lib.rs` | 835 | `a4e8dabaf67fddd6c669229b99b5792927487ed5390d6cf8a5ebf3a58bf4545d` |
| `crates/mcp-control-plane/src/handler.rs` | 18,248 | `ba25c82dbc3c791dab40787d58e3bb1065989973758c9488ff8e62ec7ced4b89` |
| `crates/mcp-control-plane/src/async_jobs.rs` | 57,529 | `4b5237c77d6e1c7c97d46ed87e31921c10958cec2d9ee3a01fd2c7d95a15c304` |
| `crates/mcp-control-plane/tests/async_job_ux.rs` | 26,604 | `0870b6137fee8ab28f434fcdef3b7713611ff91572c2bf042b1e3f71764e6be6` |
| `implementation/p15/P15-04_ASYNC_JOB_POLICY.md` | 4,367 | `c09cd7235b107fef3265ec283aecc958168da2eeea06c8c2353a0ff057840d29` |
| `implementation/p15/p15-async-job-contract-v1.json` | 5,003 | `311e9272373da0129693ad87c8a42e1e6c56b17b34ccb1312eed630b7f049c32` |
| `tools/p15/build_async_job_contract.py` | 5,183 | `e01a4216eb51227f4b5ef92e2dd659c0d89101d306c079c080043a93513cdd05` |
| `tools/p15/validate_async_job_contract.py` | 10,632 | `234926bcfe7b6076c6e3590029c1c615c8b57192b83edee40fb65842b5dc4b56` |
| `tools/p15/tests/test_async_job_contract.py` | 4,554 | `45b9559d160c36d064eb546b576e2888df350197120d5416b6e1c868222341f2` |

The generated contract verifies 23 source locks, including the workspace/dependency policy, frozen
tool catalog, P15-01 through P15-03 supersession chain, implementation, tests and validators.

## Validation

| Check | Result |
|---|---|
| Async contract builder/check/validator | pass, 23 source locks, 6 async tools, 2 job tools |
| Rust asynchronous job E2E | pass, 11/11 on Windows and isolated Linux |
| Rust handler regression | pass, 16/16 on Windows and isolated Linux |
| All P15 Python tests | pass, 44/44 |
| Rust format/check/Clippy | pass, `-D warnings` |
| Current exact-commit full CI | pass, 5/5 lanes |
| Exact-commit independent checkout full CI | pass, 5/5 lanes; tracked changes 0 |
| Current security lane | pass, all checks exit 0; failed checks 0; SBOM 730 components |
| Independent-checkout security lane | pass, all checks exit 0; failed checks 0; SBOM 497 components |
| Offline Linux validation | pass, 11 async + 16 handler tests and Clippy; network disabled, source/registry read-only |
| Residual P15 containers / `Hwp.exe` | pass, 0 / 0 |

The current exact-commit run is `62c5135856de47d4887f612989b7a2ab`. Its Git-ignored report is
1,294 bytes with SHA-256 `96f6d65be36d140693f42ede0581023ab7f742aed40573b1a28c5d525628526a`;
the 717,264-byte SBOM SHA-256 is
`cde3861deb429e964585afe6eb4e2ecd4bd684787c89e24a699377f12cf59701`.

The independent exact-commit checkout produced run `5d9b79bca8fa40239fbf01e6385cae78`. Its report
and SBOM were copied without modification into the main checkout's Git-ignored evidence area. The
report is 1,294 bytes with SHA-256
`0290a583fa89798d0bc12982ee53848e9880c7cf27c5c65e1be2fe7ef5718480`; the 531,972-byte
SBOM SHA-256 is `e554413a71805fc4dd01d508770dc672cb0cebb730072ab4517e685f5a757488`.

Offline validation used
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`
with `--network none`, read-only root/source/Cargo registry, dropped capabilities,
`no-new-privileges`, and bounded memory/CPU/PIDs. Only `/target` was executable so Cargo build
scripts could run. The independent checkout received only four exact digest-matched, Git-ignored
current-PC JSON baseline records; no HWPX, PDF or user document was copied.

## Strict review and diagnostics

- Change risk: `high`; durable state and cancellation now sit behind all long-running public tools.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Review found that failure completion while cancellation was pending could surface a generic
  storage-corruption classification. Commit `4c6224f6001c5daadaaaec907c0bba86db7c6c0f` makes the
  transition explicitly fail as `CancellationPending` and adds a regression assertion.
- The same review clarified that stage ordering is local to a public state; a valid public state
  advance such as `running/render` to `validating/validate` is not a stage regression. It also
  clarified that semantic idempotent replay can carry a new transport request ID.
- The first offline attempt used the image's stale Cargo registry and stopped before compilation
  because `aes-gcm` was unavailable. The second used the correct read-only host registry but a
  `noexec` target tmpfs, so build scripts could not execute. Neither is PASS evidence. The final
  bounded run corrected only those environment mounts and passed.
- No Hangul process, COM automation, HWPX/PDF/user document, network service or system setting was
  opened or changed for this card.

This card does not qualify production PostgreSQL/queue/scheduler/transport, cross-process journal
locking, hosted OAuth/JWKS, MCP SDK wiring, artifact attachment/signed-URL delivery, ChatGPT/Codex
connection or Hancom 2022/2024 behavior. Those claims remain unverified.

P15-04 may be checked. P15 remains in progress. Continue with P15-05 Artifact delivery at reasoning
effort `max`: implement attachment-or-signed-URL selection, byte ranges, expiry and tenant/project
ACL checks while preserving the frozen `artifact_get` schema and the P15-03/P15-04 ordering.

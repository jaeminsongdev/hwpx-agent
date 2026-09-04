# P15-04 asynchronous job UX policy

Date: 2026-09-05
Scope: current development PC, licensed Hancom Hangul 2020, local durable reference gateway
Status: implementation candidate until the P15-04 report closes the card

## Public boundary

The P15-02 catalog remains byte-identical. Six already-declared long-running tools are admitted as
durable submissions: `document_create`, `document_edit`, `document_transform`,
`document_validate`, `document_render` and `document_export`. `job_get` polls their current bounded
projection and `job_cancel` records a receipt-backed cancellation decision. The P15-03 sequence
remains authentication, exact schema validation, project policy, one gateway dispatch, output
schema validation and correlation before any result is returned.

Structured results continue to match the frozen output schemas. Ordered progress events are a
typed, bounded client-only payload at `_meta["hwpx/jobEvents"]`; they never enlarge or weaken a
tool's `structuredContent` schema. A cursor is bound to one job and one exact event sequence. A
cursor from another job, a future cursor or malformed cursor fails closed.

## Durable local reference journal

- The caller selects a dedicated root directory. The only store file is the fixed
  `p15-job-journal-v1.jsonl` child; links and non-directory roots are rejected.
- The journal is append-only. Each line contains a complete bounded job snapshot, a global
  monotonic sequence and a SHA-256 corruption checksum, and is flushed with `sync_all` before the
  in-memory state is published.
- Reopen replays duplicate-key-free JSON and verifies schema version, exact sequence, checksum,
  immutable identity, event prefix and terminal immutability. A partial final line or invalid
  evolution rejects the entire store rather than guessing.
- The reference limits are 4,096 jobs, 65,536 journal entries, 64 MiB total, 1 MiB per entry, 256
  events per job, 248 progress events, 200 events per public page and 128 result artifact IDs.
- Job IDs are deterministic for the authenticated tenant, project, subject and idempotency key.
  Exact semantic replay returns the same job even when the transport `request_id` is new. Reuse by a
  different tenant, project or subject is a different identity; reuse with a changed tool or semantic
  arguments fails as a conflict.

This journal proves restart durability for the current-PC reference. It is not the production
PostgreSQL adapter, a cross-process locking implementation, a queue, a scheduler or disaster
recovery evidence. Those claims remain open.

## Progress and terminal rules

Progress uses ordered states, state-local stages and explicit units rather than a synthetic
percentage. Units cannot regress within a stage, known stages cannot move backward within the same
public state, public state cannot move backward, and time cannot regress. Worker-facing updates
contain only a typed stage and numeric units; public messages are fixed server text.

Every terminal path creates exactly one immutable terminal receipt and exactly one terminal event.
Further progress or terminalization is rejected.

- queued cancellation is terminal immediately and uses the cancellation receipt as its terminal
  receipt;
- active cancellation becomes `requested`, blocks further progress, and becomes terminal only when
  the worker acknowledges a safe point;
- committing is past the final safe point and returns `not_cancellable` without altering the job's
  terminal outcome;
- an already-terminal cancellation request returns the existing terminal receipt;
- an exact cancellation retry returns the original decision with `replayed=true`; a changed key or
  reason conflicts.

## Privacy and deferred claims

Authorization bearer values, raw argument JSON, document content, local paths and raw cancellation
reasons are never journaled or included in debug output. The journal retains bounded public IDs,
authenticated subject and argument digests, state, numeric progress and fixed safe messages.

No Hangul process, COM call, HWPX/PDF/user document, network service or system setting is needed for
this card. The exact selectable target remains `hancom-hangul-2020-secondary`; Hancom 2022/2024,
Streamable HTTP, MCP SDK wiring, production OAuth, PostgreSQL/object storage integration, artifact
delivery and hosted ChatGPT/Codex connection remain unverified.

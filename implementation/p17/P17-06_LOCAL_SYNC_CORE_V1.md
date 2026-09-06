# P17-06 local sync core v1

Date: 2026-09-06
Scope: current PC, pure local mirror transition core
Decision: **first bounded increment implemented; P17-06 remains in progress**

`local-sync` adds a path-free local mirror state machine aligned with the existing P14 mirror CAS
model. It represents explicit `offline`/`online` connectivity and `clean`/`ahead`/`conflict`
phases. Local work can be queued offline without any remote call. Pull, push and checkpoint can run
only online and only through the injected `RemoteSyncPort`; the crate contains no HTTP client,
credential, filesystem path or process execution.

Push requests bind project, branch, expected remote head, snapshot digest, operation-plan digest and
idempotency key. A valid receipt must advance the exact generation by one and echo the queued
snapshot digest before local state becomes clean. Unavailable, rejected or malformed responses do
not advance the remote head. An unavailable or malformed response retains the first push
idempotency key and refuses a different retry key, preventing an uncertain remote effect from being
duplicated. A definitive rejection releases the key. A remote advance while local work is ahead
records a conflict while preserving the local snapshot and pending plan for P17-07 resolution.

Checkpoint requests require a clean, non-empty observed head and validate the returned revision
before recording the checkpoint ID. Debug output redacts project/branch/mirror IDs, digests and
idempotency keys. The typed contract is summarized in `protocol/private/p17-local-sync-v1.json`.

The current core passed eight transition/negative tests and all-target Clippy with warnings denied.
These component tests exercise the required offline/online transition but are not a sync-CLI or
actual remote-network claim. Durable create-new mirror-state storage, a bounded CLI, daemon/MCP
wiring and an authenticated P15 adapter remain open; therefore P17-06 is not PASS yet.

# P04-08 Idempotency and revision CAS policy

## Binding

An idempotency key binds once to request SHA-256, execution manifest SHA-256, revision stream,
expected revision and generation, and transaction ID. Any drift returns `key_reuse_conflict` without
changing the existing record.

## Ownership and states

The first valid claim receives a globally monotonic nonzero fencing generation and a secret owner
token binding. Duplicates observe `claimed`, `in_progress`, `outcome_unknown` or an immutable terminal
replay; they never receive owner authority. Heartbeat and transitions require the exact current owner
and fence.

States are `claimed → in_progress → succeeded|failed_terminal|outcome_unknown`. Unknown outcome does
not permit a second effect. Exact reconciliation either verifies the service-recorded committed head
or verifies that the expected head is unchanged, then writes a terminal replay.

## Revision CAS

Each project/document stream begins at generation one. A commit requires exact expected revision and
generation, a different new revision, complete artifact identity and a transaction receipt digest.
Head update and terminal record update occur under one service lock. A stale head or invalid commit
changes neither record nor stream.

## Scope

This in-memory implementation is the P04 reference semantics and concurrency harness, not the P14
durable database. The object-safe `IdempotencyStore` contract is the atomic persistence boundary a
P14 implementation must preserve. It performs no filesystem, network, process, COM, HAction or backend operation.
Receipts expose artifact/revision results but hash idempotency keys and redact document/project IDs,
owner tokens and binding values from Debug/errors.

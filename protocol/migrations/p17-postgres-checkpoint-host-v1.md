# P17 PostgreSQL checkpoint host v1 compatibility

Date: 2026-09-07

This contract is an additive successor to the in-memory history dispatcher and bounded loopback
transport. Migration 14 leaves `create_history_checkpoint` v1 in place for predecessor consumers,
but the dedicated P17 host role must have `EXECUTE` only on `create_history_checkpoint_v2` and must
reject admission if it can call v1 or directly mutate the protected tables.

The v2 request adds the optional immutable note to both the idempotency claim and checkpoint row.
An absent note remains SQL `NULL`; an empty note is invalid. A same-key request with any different
revision, label, note, subject, checkpoint ID or canonical request digest fails with SQLSTATE
`P1701`. PostgreSQL serialization SQLSTATE `40001` remains an uncertain outcome and is never
reported as a definite conflict.

Rollback is a controlled development operation, not an automatic downgrade. It requires the exact
version-14 schema, an explicit transaction-local gate, no later migration, and no non-null note in
either immutable table. A client or host must not reinterpret a failed rollback as compatibility.

Future versions must use a new function or protocol version when changing admission, idempotency,
receipt fields, persistence ownership or transport security. They must preserve v1 evidence as
historical evidence and must not promote this loopback checkpoint proof to pull/push, durable mirror
admission, remote-network or production evidence.

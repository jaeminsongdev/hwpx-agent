# P17-06 history checkpoint dispatch v9

Date: 2026-09-06
Scope: current-PC P15 history checkpoint dispatcher and exact loopback compatibility
Decision: **concrete in-memory service dispatch implemented; durable actual transport remains open**

The history model now represents the P15 optional checkpoint note as an exact immutable value. An
absent note is omitted from canonical request and record JSON, preserving the note-free predecessor
digest shape. A present note is stored unchanged, included in the idempotency-bound request digest
and redacted from debug output. The existing note-free constructor remains available, while the new
constructor carries an optional note.

`HistoryCheckpointDispatcher` maps authenticated P17 host calls to the P15 history core. It derives
the history request identity from the stable service idempotency UUID, not the changing host
correlation request ID. It derives one checkpoint UUIDv5 from tenant, project and service
idempotency identity. Exact project and revision IDs are parsed, label normalization drift is
rejected rather than silently changed, and note text is preserved. Created and replayed history
outcomes map to the existing bound remote-sync receipt.

The compatibility test exercises the existing `AuthenticatedRemoteSyncAdapter`, two fresh one-time
credentials, the new authenticated host, exact retention-mirror admission and the concrete history
dispatcher. The first call creates a checkpoint; the second call uses a new host request ID but the
same private idempotency, label and note and returns the same checkpoint with `replayed=true`.

History-service tests pass 17/17 and remote-sync-host tests pass 7/7. Formatting and targeted
all-target/all-feature Clippy with warnings denied pass. The machine contract is
`protocol/private/p17-history-checkpoint-dispatch-v1.json`; compatibility and future version rules
are in `protocol/migrations/p17-history-checkpoint-dispatch-v1.md`.

This proof uses a loopback transport, local HMAC reference verifier and in-memory history
repository. It does not establish durable persistence, credential custody, a network listener,
external identity provider, actual remote transition or production readiness. P17-06 remains in
progress. The next increment is the bounded concrete transport/credential host with durable service
state, followed by current-PC actual remote pull/push/checkpoint evidence.

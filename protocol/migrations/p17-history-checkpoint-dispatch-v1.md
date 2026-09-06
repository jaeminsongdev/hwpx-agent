# P17 history checkpoint dispatch v1

This is the first concrete P17 checkpoint dispatcher for the P15 history core. Existing history
callers remain source-compatible through the note-free `CheckpointRequest::new` constructor.
Callers that preserve the P15 optional note use `CheckpointRequest::new_with_note`.

An absent note remains omitted from canonical JSON, so legacy note-free history request digests do
not acquire a synthetic null field. A present note is exact, immutable and included in the request
digest used for idempotency conflict detection. Its debug representation is redacted.

The P15 idempotency UUID, rather than the correlation request ID, becomes the durable history
request identity. Checkpoint identity is deterministic UUIDv5 over authenticated tenant, exact
project and that service idempotency UUID. Thus a retry with a fresh host correlation ID and service
credential replays the same checkpoint, while revision, label or note drift is rejected.

Future versions must not reintroduce correlation fields into mutation identity or discard/normalize
note text silently. Durable repository, network transport, credential custody and external identity
provider qualification remain separate successors.

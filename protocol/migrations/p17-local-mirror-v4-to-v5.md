# P17 local mirror v4 to v5

`hwpx-agent.local-mirror/v5` adds `pending_checkpoint_request_sha256`. A pending checkpoint is valid
only when both this digest and `pending_checkpoint_idempotency_key` are present, or both are absent.
The digest is computed from the exact encoded private v3 checkpoint request. User label and note
text are not stored in the append-only local journal.

Clean v1, v2, v3 and v4 snapshots remain readable and are emitted as v5 on the next append. A v3 or
v4 snapshot that already contains a pending checkpoint key is rejected because it has no digest
that can prove the original label/note binding. The client must not guess missing metadata, discard
the old key silently, or retry such a request against a v3 host.

Unavailable or malformed remote outcomes retain both pending fields. Definitive rejection,
validated conflict and validated success clear both fields in the same durable transition.


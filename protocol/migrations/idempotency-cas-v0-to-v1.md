# Idempotency and CAS v0 to v1

P04-08 introduces `hwpx-agent.idempotency-receipt/v1`. A key is permanently bound to the exact
request digest, execution manifest digest, revision stream, expected revision/generation and
transaction identity. Reusing a key with any drift is a conflict, never a new execution.

Only the acquired secret owner token plus nonzero fencing generation may advance a live record.
Terminal success/failure is immutable and replayed byte-for-byte. Outcome-unknown records cannot be
re-executed; they require an exact no-effect or committed-head observation.

The P04 implementation is an in-memory reference service. Durable multi-process storage and database
migrations remain P14. Consumers must not treat process restart persistence as implemented here.

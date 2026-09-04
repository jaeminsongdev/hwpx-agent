# P14-08 Safe Cancellation and Cleanup Policy

Status: implementation and local acceptance candidate

## Scope

P14-08 owns safe job cancellation, temporary workspace cleanup, and quarantine of an
unreferenced orphan artifact. It does not open or automate Hancom Hangul. The current product
baseline remains the licensed Hangul 2020 installation on this PC; later Hangul versions remain
separate future-PC qualification work.

The reference worker is `crates/artifact-service/src/bin/p14_cleanup_worker.rs`. The durable
adapter is PostgreSQL migration `0008_p14_cancel_cleanup`. Public contracts expose opaque UUID
handles and content digests only. File-system paths, document names, plaintext, encryption keys,
and Hancom recovery paths never enter the cancellation or cleanup tables.

## Cancellation boundary

- `queued` and `retry_pending` jobs cancel immediately and receive the terminal
  `JOB_CANCELLED` receipt.
- Active jobs only record a request. The same attempt must observe it at a safe point under its
  still-live execution lease and fencing token.
- No recorded external effect means `cancelled`; its exact temporary workspace handle is queued
  for cleanup.
- A started but uncommitted external effect means `unknown_outcome`, never a false cancellation
  success. The workspace is queued while the durable result remains frozen for reconciliation.
- A committed external effect means `too_late`. No workspace cleanup task is issued and the
  normal commit path is unblocked.
- Once cancellation is pending, ordinary stage/heartbeat/terminal transitions and a new external
  effect start fail closed. Recording completion of an already-started effect remains possible.
- Cancellation identity binds tenant, project, job, idempotency key, subject, cancellation ID,
  and receipt artifact. Only an exact replay returns the stored result.

## Cleanup worker boundary

- A workspace target binds the job execution ID, attempt number, source fencing token, and an
  opaque workspace handle. Only the registered internal adapter maps that handle to a validated
  staging-relative directory.
- An orphan target is derived from the database artifact row. Callers cannot supply or override
  its kind or content SHA-256.
- `source` artifacts and all artifacts referenced by revisions, jobs, attempt receipts,
  idempotency records, or cancellation receipts are never candidates.
- Claiming an orphan changes the service metadata from `available` to `purging` while retaining
  the available object key. Product APIs require `available`, which prevents a new reference
  from racing the external quarantine operation.
- Completion rechecks tenant, project role, artifact identity, reference absence, lease expiry,
  attempt number, cleanup execution ID, fencing token, outcome kind, and proof digest. Only then
  does `purging` become `quarantined` with reason `ORPHAN_CLEANUP`.
- Lease duration is at most 300 seconds and retry count is at most three. Each reclaim increments
  the fencing token. A stale worker cannot publish a receipt.
- A crash before external cleanup is retried normally. A crash after external cleanup but before
  the receipt is retried as `workspace_already_absent` or `artifact_already_quarantined` after the
  exact digest is reverified.
- If the quarantine hard link became durable but deleting the published name failed, retry
  re-verifies both names against the bounded expected digest and removes only that exact published
  copy. A mismatched quarantine fails closed and preserves both names.
- Cleanup tasks and receipts are delete-protected. Retention and final purge belong to P14-09.

## Failure and evidence policy

All authorization, identity drift, reference races, invalid outcomes, expired leases, and digest
mismatches fail closed with stable error codes and no success receipt. Tests may inject failures
only before external cleanup or after external cleanup and before receipt commit. They never
weaken constraints or synthesize a PASS marker without exercising the real branch.

Acceptance requires:

1. Rust unit tests and Clippy with warnings denied.
2. Static contract validation including exact source SHA-256 values.
3. PostgreSQL 18.4 application of migrations 1 through 8 in a network-isolated, host-port-free,
   host-volume-free temporary container.
4. The 18-assertion cancellation/cleanup smoke fixture and the existing 28-assertion P14-07
   regression fixture.
5. Concurrent cleanup claims with one winner, stale-fence rejection, both fault windows,
   rollback refusal with v8 data, clean rollback to exact v7 functions, and reapply.
6. Source revision and dirty-tree state captured in the local ignored evidence receipt.

P14-08 does not qualify production deployment, multi-host failover, retention purge, or later
Hangul versions. Continue to P14-09 retention and mirror behavior at reasoning effort `Max` after
this card passes.

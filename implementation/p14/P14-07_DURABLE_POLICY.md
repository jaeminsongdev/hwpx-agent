# P14-07 durable idempotency and reconciliation policy

## Immutable binding

A version-2 idempotency record binds one tenant, subject, project, branch, job and key to the exact
request, execution manifest, source artifact, expected output effect, transaction receipt and
expected revision head including generation. Reusing the key with any drift returns a conflict and
does not mutate the stored record. Record and retry-policy expiry are immutable and bounded.

Legacy version-1 rows remain readable and retain their original constraints during the v7 schema
upgrade. They are never silently promoted because the additional evidence cannot be reconstructed.
All v7 mutation functions accept only version-2 rows.

## Atomic job coupling

The v7 lease path locks the idempotency record and job in a fixed order, verifies the exact live
P14-06 worker profile/capability binding, and changes job, attempt and idempotency state in one
transaction. The first and every retry attempt increment both attempt number and fencing token by
exactly one. A lease may not start early, outlive the worker, or outlive the idempotency record.

Each lease also creates one database-internal commit authorization bound to that job, execution,
attempt, fence and transaction receipt. The revision commit receipt trigger consumes it atomically
with the revision CAS. Retry, unknown-outcome, success and terminal-failure transitions revoke it
first, so a superseded worker cannot publish a late effect even if its old process resumes.
The lease returns a fresh unpredictable authorization ID, and the v2 CAS wrapper requires that ID
plus the exact agent, execution, attempt and fence. A prior attempt therefore cannot consume a
later attempt's authorization merely by knowing the job's immutable transaction digest.
After v7, a revision commit without an exact version-2 record is rejected as well; an arbitrary
transaction digest cannot fall back to the pre-idempotency commit path.

Transient storage/network failure can move an active attempt to `retry_pending` only after the
database verifies the source artifact digest and unchanged branch head. Automation timeout first
moves to `outcome_unknown`; it cannot lease again until reconciliation proves either a committed
effect or no effect. Planning/schema/validation failure is terminal and never automatically retried.

## Trusted reconciliation

Committed reconciliation is accepted only when the database joins a verified service-created
revision, its exact operation plan, service seal, revision commit receipt, exact branch, previous
revision, expected generation, commit identity, transaction receipt, verified result artifact
digest and the current branch head. Caller-supplied digest equality alone is insufficient.

No-effect reconciliation is accepted only when the database independently observes the exact source
artifact digest and the unchanged branch revision plus generation. Receipt artifacts must be
available, verified, `receipt` kind and readable by the bound subject. A missing or conflicting
oracle fact leaves the record frozen or fails closed; it never authorizes a second effect.

## State and retry bounds

Idempotency v2 states are `claimed`, `in_progress`, `retry_pending`, `outcome_unknown`,
`terminal_success`, and `terminal_failure`. Job v7 adds `retry_pending`; each prior attempt remains
terminal and immutable. Retry policy is limited to 10 attempts, base/max delay between 1 and 86,400
seconds, and record TTL at most seven days. Delay is deterministic exponential backoff capped by the
stored maximum. Exhaustion becomes terminal `RETRY_EXHAUSTED` without another lease.

## Migration and rollback

Migration v7 requires exact v6 and refuses duplicate or out-of-order application. It preserves
legacy rows using `record_version=1`, adds v2-only closed constraints, forced RLS and public privilege
revocation, and replaces the job consistency guards with multi-attempt semantics.

Rollback refuses missing authorization, any schema version after v7, or any remaining v2
idempotency record. After callers explicitly remove disposable v2 test data, it restores the exact
v6 job constraints/guards, removes v7 functions and columns, records removal of schema version 7 and
retains version 6. Production data deletion is outside this migration.

## Scope

This policy targets a disposable PostgreSQL integration and local Rust reference. It does not prove
production deployment, HTTP/MCP exposure, multi-region failover, cancellation/cleanup, retention,
legal hold, or mirror behavior. It never opens Hangul or a user document and never mutates a source
artifact in place.

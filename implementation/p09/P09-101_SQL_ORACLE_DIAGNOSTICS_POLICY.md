# P09-101: owned SQL failure diagnostics policy

## Scope and authority

P84 SQL failure diagnostics only. P09 Gate remains OPEN; actual SQL, native, product acceptance and P10 are NOT_RUN/not achieved. No DB, Docker, Hwp, COM or UI was started in this stage. No role grants, original migrations, trust settings or publication authority were changed.

The original P84 owned runner may observe its own disposable DB after its existing owner-label, loopback and no-host-mount checks. This source implementation does not authorize executing that runner now. The application role gains no SELECT privileges and performs no new query. A completion error remains the primary error; diagnostics never convert it to success.

## Exact context and bounded observation

The worker emits a failure-only private context for exactly the ten original owned cases. Project, branch, result revision, idempotency key and job identities must match the existing fixture; underflow, overflow and substitutions are rejected. A receipt UUID is an opaque temporary artifact identity, not a credential. It is consumed only by the owned runner and is not stored in public receipts, logs or reports.

The runner requires a single bounded context line, an exact pinned query source, seven closed UUID/subject parameters and the original environment checks before querying. It observes the exact result revision and receipt arguments, not whichever revision is the current head. It retains forty BOOL/NULL keys only. No raw SQL, stdout/stderr, UUID, subject, path or exception message is retained by this diagnostic projection.

The forty keys cover original head, source, receipt, revision, result artifact, ACL, seal and commit predicates plus four record/job/lease context checks. SQL NULL remains unknown rather than being coerced to false or given a fallback. Individual SQL expressions retain their own semantics, including `IS NOT DISTINCT FROM`; no single true key establishes that its joined row or the whole atomic oracle qualified. No locks or mutation/helper calls are added.

This is a later, non-atomic observation. The original guard locks the head and evaluates within the completion transaction; an after-failure snapshot cannot reproduce its time, locks or visibility. Lease expiry at observation is not proof of lease state at failure. Every observation has `original_atomic_oracle_verified=false` and `root_cause_proven=false`.

Missing/duplicate/malformed context, query drift, environment rejection, DB errors, timeout and malformed results yield fixed unavailable states. They do not replace the original completion error. Safe fixture reason codes must be exact known literals from original pinned SQL sources; arbitrary dynamic suffixes are discarded.

## Preservation and validation boundary

Two modified parents have complete byte-identical preimages and exact declared forward transforms. Original migration `0007_p14_idempotency_reconciliation.up.sql` remains pinned to `cc60353df6cf3c51155417e39d0f1f4c348d2a6282bba7d63de9ea0282be5e5d`. All original twenty-four AND predicates in its committed-effect join remain represented; tenant/project binding and earlier guards are not replaced by the snapshot.

Component/unit tests and static SQL comparisons do not establish SQL syntax/runtime acceptance. Historical P84 `55000` and original policy-fixture failures remain unresolved because their raw stderr is unavailable and this stage ran no SQL. Keep the failed sources and historical receipts. Actual reproduction and regression require a later authorized disposable DB run with exact candidate evidence.

New table insertion, full rich Flow, native CommentState/metadata/protection, durable integration, issuer and atomic execution/publication remain outside this completed diagnostic slice.

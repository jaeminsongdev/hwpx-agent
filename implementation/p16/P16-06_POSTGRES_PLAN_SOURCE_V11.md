# P16-06 PostgreSQL authoritative plan source v11

- Date: 2026-09-06; scope: current-PC local PostgreSQL reader only.
- Decision: source adapter and schema successor PASS; P16-06 and product remain open.
- Base: `5166fe5a684415534af920d55b06043168302d37`; review risk HIGH / STRICT.

Migration 0011 adds one immutable revision-to-DocumentGraph digest binding. Insertion requires the
same source artifact, service seal, commit receipt, generation and creating subject. The reader fixes
one tenant per loopback connection and rechecks an active tenant/project, exact default head,
project ACL, verified revision/source artifact, service seal, commit receipt and graph binding in one
repeatable-read read-only transaction. It rejects elevated, replication and settable owner roles, migration drift,
RLS/policy drift, missing read grants and every mutation grant on the read set.

Actual disposable PostgreSQL run `b4ad5c050f0d42509da56f072ba5d6fa` passed 29 checks. It also proves
that a mismatched binding creator and a
reader without the tenant-context function grant are rejected. The checks include
empty guarded rollback/reapply, exact compiled-plan insertion and lookup, stale graph rejection,
database restart, non-member/suspended-tenant/cross-tenant hiding, quarantine and head drift,
role/RLS/policy/privilege/owner/migration mutation rejection, immutable binding and nonempty rollback
rejection. The fixed image was PostgreSQL 18.4; the UUID-owned container and volume were removed.
The retained receipt is `qualification/plan-source-v11-20260906-v1/current-db.json`; its source
digests are independently re-read by `tools/p16/postgres_plan_source_qualification.py`.

The seed temporarily disables the later idempotency-v2 commit guard only inside the disposable seed
transaction, then restores it before commit. That constructs internally consistent source-reader
state; it is not new writer-path evidence and does not supersede the existing P14 writer Gates.

No Hangul process, COM operation, user document, registered host or production service was used.
This increment deliberately records `durable_plan_store: false` and `actual_renderer: false`.
Next implement encrypted durable compiled-plan persistence and bind the renderer only to exact
route/dry-run/diff/signature receipts for the stored plan digest. Recommended reasoning: `max`.

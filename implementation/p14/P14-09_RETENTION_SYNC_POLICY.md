# P14-09 retention and local-mirror policy

## Scope

P14-09 supplies a bounded reference service and PostgreSQL v9 adapter for artifact retention,
legal holds, deletion receipts, and a digest-only mirror of Codex project state. It is scoped to the
current local development environment. It does not qualify production object storage, a production
daemon, another PC, or Hangul 2022/2024. No Hangul runtime is required by this card.

## Retention contract

Every project names a tenant-owned retention policy. A complete policy has exactly one duration for
each artifact class: `source`, `result`, `preview`, `evidence`, `trace`, `diff`, and `receipt`.
Policy identifiers use the same lowercase dotted grammar in Rust and PostgreSQL and are 3–128 bytes.
Durations are positive and at most ten years. Tombstone grace is between zero and seven days.
Policies and their rules are immutable after creation; a changed policy receives a new identifier.

`policy_expiry` checks the artifact creation time, any later explicit `retention_until`, and the
class duration. `user_delete` may tombstone before that deadline, but uses the same legal-hold,
project-membership, and shared-reference gates. An exact deletion request replay is harmless; a new
request identity for the same artifact is a conflict.

An artifact may be deleted through a project only when that project actually references it. A
reference from another project blocks tombstoning and is checked again at purge claim and purge
completion. Artifact metadata remains as an immutable audit identity after physical content is
purged; only its object key is removed and its authorization generation advances.

The v9 database also guards every newly inserted or changed artifact reference in revisions, jobs,
attempt receipts, idempotency receipts, cancellation receipts, and cleanup tasks. The guard locks
the referenced artifact rows in deterministic order and rejects `tombstoned` or `purged` targets.
This closes the race where another transaction validates an available artifact, deletion
tombstones it, and the first transaction attempts to publish a new reference afterward.

## Legal hold and external-delete boundary

A project owner can create either a project-wide hold or an artifact hold. Artifact holds require
an unpurged artifact that is referenced by the named project. Project row locking serializes hold,
tombstone, claim, failure, and completion transitions.

The purge claim is the authorization immediately preceding the object-store delete. It has a lease
of at most 300 seconds, an execution identity, and an increasing fencing token. A hold cannot be
inserted over an unexpired authorized purge; the hold request receives
`RETENTION_PURGE_IN_PROGRESS`. A hold inserted between failed attempts blocks the next claim. The
worker must not start an external delete after lease expiry, and completion rechecks the lease,
hold, and cross-project reference state.

External failure is recorded by digest. Attempts one and two return the request to `tombstoned`;
the third failure becomes `failed_terminal`. A stale execution or fencing token cannot record a
failure or completion. Successful completion records one immutable receipt with either
`object_deleted` or `object_already_absent` and a proof digest.

## Local mirror contract

The server stores no local path, account name, or raw machine identifier. A mirror is keyed by
opaque tenant/project/mirror/branch identifiers and a one-way device digest. Its snapshot and
pending operation plan are content digests. Registration succeeds only when the observed revision
and generation exactly equal the current remote branch head.

A clean mirror may queue one operation plan. Push preparation locks the mirror and remote branch,
compares the exact observed head, and reserves one `(tenant, project, branch, generation)` slot.
The push identity is unique among active reservations in the tenant project. The reservation is
bound to its creator subject and expires after at most 300 seconds. An expired reservation can be
reclaimed with a new push identity; an active reservation cannot be stolen or aliased by another
mirror.

The local-mirror API never overwrites the branch head. The existing durable revision pipeline
performs the remote CAS. Mirror completion only acknowledges an already-present
`revision_commit_receipts` row when all of these match:

- push/commit identity and creator subject;
- branch and previous revision;
- expected and committed generation;
- committed revision identity; and
- the queued operation-plan digest stored on the committed revision.

A remote-head mismatch creates an immutable conflict record and leaves the pending plan intact.
Exactly one explicit resolution is accepted:

- `rebase_operation_plan`: adopt the recorded current head and keep the plan ahead;
- `branch`: move the plan to the exact head of a named project branch; or
- `manual_merge`: preserve the observed base and enter `manual_merge_required`.

No conflict path mutates or resets the remote head.

## Security and validation boundaries

All v9 tenant tables use forced row-level security. `PUBLIC` receives no table privilege or execute
privilege on any v9 function, including trigger helpers. Every mutation function compares the trusted transaction tenant and subject context to
its arguments and then checks project ACL role. The application role receives read access plus only
the reviewed function entry points; it receives no direct table mutation access.

The PostgreSQL smoke fixture uses a transaction-local `pg_temp.seed_remote_commit` helper only to
construct the output shape already proven by P14-07. It is not installed by the migration and is
rolled back or discarded with the test session. The P14-07 idempotency/revision regression fixture
must pass in the same v9 schema run, so the fixture helper is never evidence that production callers
can bypass the idempotent commit capability.

Rollback requires the explicit `hwpx_agent.allow_p14_retention_mirror_rollback=yes` gate, exact
schema version 9, no later migration, no v9 rows, and no tombstoned or purged artifact. The rollback
restores the exact v8 artifact constraints before v9 can be reapplied.

This card does not prove production authentication, connection-pool context reset, object-store
credentials, backup/restore, HA, end-user UX, remote Codex transport, or legal-policy suitability.
Those remain later integration and release gates.

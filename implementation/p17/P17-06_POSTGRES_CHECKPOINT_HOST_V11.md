# P17-06 PostgreSQL checkpoint host v11

Date: 2026-09-07
Scope: current-PC disposable PostgreSQL and separately launched loopback checkpoint processes
Decision: **durable checkpoint sub-increment PASS; P17-06 remains in progress**

Migration 14 extends the immutable history request and checkpoint rows with the exact optional
checkpoint note and adds the least-privilege `create_history_checkpoint_v2` function. The function
requires the authenticated tenant/subject context, active project, editor or owner role, and an
existing service-v1-sealed revision. Exact replay returns the existing checkpoint. Same-key drift
uses the dedicated `P1701` SQLSTATE so it cannot be confused with PostgreSQL serialization failure.

The down migration now fails closed unless an explicit rollback setting is present, version 14 is
the latest version and both note columns contain no non-null immutable data. An empty-schema
rollback/reapply succeeds; any note-bearing history refuses downgrade. The immutable schema-version
trigger is disabled only around deletion of the exact version-14 row inside the rollback
transaction and is re-enabled before commit.

`LocalPostgresHistoryCheckpointDispatcher` accepts only loopback configuration and a bounded,
non-owner, non-superuser, non-BYPASSRLS application role. Connection admission verifies all 14
migration digests, exact forced tenant RLS policies and the v2-only execution surface. Each request
uses a serializable transaction, transaction-local tenant/subject settings and exactly one v2
function call. The returned checkpoint, revision, label, note and request digest must match before
commit. Definite input, authorization, foreign-key, uniqueness and `P1701` failures map to
`Rejected`; serialization, transport and unknown outcomes map to `Unavailable` without retry.
Backend diagnostics, password, tenant and subject values are not retained in public diagnostics.

The current-PC acceptance used the pinned PostgreSQL 18.4 image on `127.0.0.1`, one separately
launched host and four separately launched clients. Run
`12e4189fc3864f0faedacd6d8e8f6adf` passed 15/15 checks: exact
migrations, gated empty rollback and reapply, v2-only role, one-time token exchange, durable create
and exact replay, changed-note rejection, corrupted-row replay refusal, one
request/checkpoint/audit row, immutable-row protection, data-loss rollback refusal,
migration-digest drift rejection and execute-privilege drift rejection. The receipt records no
secret material, and the run-owned container and volume were removed. The ignored receipt is frozen
by `implementation/p17/qualification/postgres-checkpoint-host-v1-20260907/`.

The repository FULL security lane initially found that `sha1_smol`, introduced transitively by the
already selected UUID v5 feature, uses `BSD-3-Clause`: that license was already allowed by the
repository security policy but was absent from the matching `cargo-deny` allowlist. The allowlists
are now aligned, and security run `dc6b4f31b22946f39dc98f164b0eb5a3` passed secret scanning,
`cargo-deny`, `cargo-audit`, pnpm audit/license checks, both .NET vulnerability checks and SBOM
generation with zero failed checks. `deny.toml` is bound by this qualification so later policy drift
fails closed.

This is actual durable checkpoint evidence, but it is deliberately not a full remote-sync PASS.
Retention-mirror role/head admission is still process-local and is not committed atomically with
the PostgreSQL checkpoint. No pull, push, remote-network TLS, persistent credential custody,
production service lifecycle or Hangul operation was exercised. The machine contract is
`protocol/private/p17-postgres-checkpoint-host-v1.json`; evolution constraints are in
`protocol/migrations/p17-postgres-checkpoint-host-v1.md`. P17-06 and the product goal remain open.

The next MAX increment is to persist mirror/head/role admission and checkpoint mutation in one
database-owned transaction, then add actual bounded pull and push transitions behind the same
authenticated host boundary.

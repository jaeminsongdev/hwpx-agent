# P14-01 metadata migration runbook

- Task: `P14-01`
- Database: PostgreSQL `18.4`
- Contract: `implementation/p14/postgres/p14-metadata-v1.json`
- Reasoning effort: `max`

## Safe local verification

The first command is static and does not start Docker:

```powershell
python tools/p14/validate_metadata_migrations.py
python -m unittest tools.p14.tests.test_metadata_migrations
```

The actual harness starts one uniquely named disposable PostgreSQL container. It publishes no host
port, mounts no host volume, uses Docker network mode `none`, and removes only a container whose exact
name and `hwpx-agent.p14-test` label match its run. If the immutable image is not cached, the first run
may explicitly fetch that one digest:

```powershell
python tools/p14/test_postgres_migrations.py --allow-pull
```

For an acceptance receipt, first commit the implementation and require a clean worktree. Choose a
new filename because evidence is create-new and never overwritten:

```powershell
python tools/p14/test_postgres_migrations.py `
  --receipt implementation/p14/evidence/p14-01-postgres-migration-audit-<UTC>.json
```

Accept the receipt only when `state=pass`, `source_tree_clean_before_run=true`, its full
`source_revision` is the intended commit, apply and reapply pass, rollback without the gate is
refused, explicit rollback passes, and `container_removed=true`. Rehash the receipt independently.

## Migration application contract

The up migration intentionally requires the caller to calculate its exact SHA-256 and set
`hwpx_agent.migration_sha256` in the same database session before executing the SQL. The supplied
harness performs and verifies this binding. A general migration runner must provide the same
transaction/session guarantee; do not replace the value with a placeholder.

The down migration is destructive. It refuses execution unless
`hwpx_agent.allow_destructive_rollback=on` is set in that same session. Use it only against a named
disposable database during P14-01 testing. Production rollback requires a separately reviewed
forward migration, backup/recovery plan and change authorization; this runbook does not authorize a
production schema drop.

## Application-role boundary

Do not grant the application role ownership, superuser or `BYPASSRLS`, and do not grant it access to
`schema_versions`. Grant only the tables and sequences required by the concrete service plus
`USAGE` on `hwpx_agent` and `EXECUTE` on `hwpx_agent.current_tenant_id()`.

Every pooled application transaction must establish authenticated tenant identity outside SQL, begin
the transaction, set `hwpx_agent.tenant_id` locally, perform only parameterized service queries, and
commit/rollback before the connection is reused. The custom GUC is RLS context, not an authentication
credential. Arbitrary client-provided SQL is forbidden.

## Failure handling

- Contract/hash mismatch: stop before Docker and reconcile the reviewed files; never update the
  manifest only to silence the validator.
- Image digest/version mismatch: stop and review a new explicit pin; do not fall back to `latest`.
- Migration or smoke failure: preserve terminal output, let the harness remove its owned container,
  fix the schema/fixture, and rerun from a new container.
- Cleanup uncertainty: inspect only containers carrying `hwpx-agent.p14-test`; do not remove unrelated
  containers.
- Online `pnpm audit` timeout: keep repository security status unverified and rerun that bounded check
  separately. It does not change the DB receipt.

## Handoff

P14-01 is complete in local disposable PostgreSQL scope. P14-02 must implement the artifact service
over this metadata contract: tenant ACL, content-addressed object keys, encryption metadata,
quarantine, short-lived signed URLs and cross-tenant denial. Continue P14-02 at reasoning effort
`max`. P14-03 through P14-09 and the P14 phase Gate remain open.

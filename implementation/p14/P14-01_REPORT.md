# P14-01 metadata schema report

- Date: 2026-09-04
- Implementation commit: `200806a`
- Decision: `pass_scoped_p14_01_local_disposable_postgres`
- Review: `STRICT / max`, blocker/major/minor after correction `0/0/0`

## Delivered

- PostgreSQL migrations for 13 metadata tables: schema versions, tenants, projects, project ACLs,
  artifacts, immutable revisions and parents, branches, immutable checkpoints, jobs, mutable-state
  but identity-protected job attempts, idempotency records, and immutable audit events.
- Composite tenant/project foreign keys, deferred same-project revision heads, one-default-branch
  enforcement, typed state/lease/terminal constraints, bounded identifiers and lowercase SHA-256
  checks.
- Forced row-level security on all 12 tenant-scoped tables. Public schema, table, sequence and
  function privileges are revoked. Application roles must be granted only the required objects and
  `current_tenant_id()` explicitly.
- Identity protection for artifact content, job request, job attempt and idempotency request fields;
  revision, revision-parent, checkpoint, schema-version and audit rows reject update/delete.
- A fail-closed rollback that refuses to drop the schema unless the same database session sets
  `hwpx_agent.allow_destructive_rollback=on`.
- A machine-readable contract binding source documents, exact migration and fixture digests, the
  PostgreSQL version and an immutable container-image repository digest.
- Static validation with 13 negative/unit tests and docs-lane integration. The Docker harness binds
  the contract, Git revision and clean-tree state, publishes no host port, mounts no host volume,
  uses no container network, and removes only its exact name+run-label container.

## Actual migration and rollback evidence

The authoritative Git-ignored receipt is
`implementation/p14/evidence/p14-01-postgres-migration-audit-20260904T021515660Z.json`:

- bytes: `1430`
- SHA-256: `1af81502520d02e8d7429edcd6da8ac38d869f5ee9a5405257d6720c2b39e6cb`
- exact clean source revision: `200806ad8c011806ab5b02617cf9d972986f1dbf`
- migration contract SHA-256:
  `9f1389fc87fcfd40d6a66683d6623d28e6b431c5ae8551e63b3c64eee070a394`
- test harness SHA-256:
  `568bc020bca0d402b3a9bfd063ffb08a1911069b3f39fe1607353781b1b99f4a`
- up migration SHA-256:
  `7c00f744993581448acb4b6d4d8a46f1ff03d108750da0afc671c3b5e2b0a78d`
- down migration SHA-256:
  `1c17c31ad8b19d16a64498ce9cb47cdf5c85a0cbd8450b079f8586d4960c8fa2`
- smoke fixture SHA-256:
  `a03d8fbf5ec8d0a0e7ad56e1211ccb0f69424b3aef41f883dc2b1fb42573bfbc`
- PostgreSQL: `18.4 (Debian 18.4-1.pgdg12+1)`
- image: `postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568`

The exact run applied the migration twice and ran all 19 smoke assertions after each application.
It proved tenant-A cannot see or insert tenant-B rows, immutable metadata fails closed, same-project
head constraints reject cross-project revisions, invalid leases reject, and job-attempt/job/idempotency
terminal updates remain possible without changing their identities. Rollback without the explicit
session gate was rejected without changing the schema. Two explicitly authorized disposable
rollbacks succeeded. The test container was removed and the final owned-container count was zero.

## Validation

| Check | Result |
|---|---|
| Contract validator | pass, 13 tables / 12 tenant-scoped / exact digests |
| P14 negative/unit tests | pass, 13/13 |
| Actual PostgreSQL apply | pass, 2/2 |
| Actual SQL smoke | pass, 19/19 per run, 2 runs |
| Rollback without gate | pass, refused 1/1 and schema retained |
| Explicit disposable rollback | pass, 2/2 |
| Reapply after rollback | pass |
| Complete docs lane with P01/P02/P04/P10 regressions | pass, `9.361s` |
| Secret scan | pass, 819 files, findings 0 |
| Rust policy/advisory, npm license, .NET vulnerability, SBOM | pass |
| `pnpm audit` online registry check | unverified, 60-second timeout 3/3; cleanup 3/3 |
| Residual P14 containers / audit processes / `Hwp.exe` | pass, 0 / 0 / 0 |

The repository-wide security report is Git-ignored at
`implementation/p01/evidence/security-runs/a9ed8989306a4f5daefd30dcc88801e8/report.json`, bytes `1666`,
SHA-256 `f483bf26fb83e5a8451c4a1b16a3fb92514babb381175e874b50bf484c695ef2`.
Its sole failed check is the external `pnpm audit` endpoint. This is not promoted to a security PASS
and is not evidence for P14-01 migration behavior.

## Strict task decision and limits

P14-01's required `DB migrations` and `migration/rollback tests` exist and have actual disposable
PostgreSQL evidence, so only the P14-01 roadmap checkbox may be checked. This does not close P14 and
does not qualify a production database, backup/restore, HA, artifact object storage, signed URLs,
cross-service authorization or any P14-02 through P14-09 behavior.

The tenant GUC is transaction context supplied by a trusted service, not authentication by itself.
Production must use a `NOBYPASSRLS` application role, begin a transaction, set tenant context locally,
avoid exposing arbitrary SQL, and reset/discard pooled sessions before reuse. Those integration
properties remain part of the P14-02 service Gate.

No Hangul process, user document, source fixture, registry/system setting or production database was
used by P14-01.

# P14-09 retention and local mirror report

- Date: 2026-09-04
- Implementation commit: `1d5de34121a8ba7cb9fc651cb90d63d7973db2dc`
- Decision: `pass_scoped_local_disposable_postgres_and_in_memory_reference`
- Review: `STRICT / max`, blocker/major/minor after correction `0/0/0`

## Delivered

- A bounded Rust retention and local-mirror reference service with opaque identifiers, redacted
  diagnostics and exact tenant/project/subject authorization.
- Seven complete retention classes, explicit retention deadlines, legal holds, immutable delete
  requests, tombstones, three-attempt fenced purge and immutable purge receipts.
- Shared-reference and legal-hold rechecks before deletion, plus rejection of every new artifact
  reference after tombstoning.
- A digest-only Codex project-state mirror with exact remote-head compare-and-swap acknowledgement,
  subject/plan/revision binding, bounded push leases, expired-push recovery using a new identity,
  single generation reservation and three explicit conflict-resolution paths.
- PostgreSQL migration v9 with forced RLS, tenant/subject binding, immutable identities, table and
  function privilege revocation, guarded rollback to v8 and exact reapply.
- A digest-pinned contract, 32-assertion smoke fixture and unchanged P14-07 28-assertion regression
  fixture, each executed three times against disposable PostgreSQL 18.4.

## STRICT review corrections

- Duplicate Rust map insertion could overwrite an existing retention class, hold, mirror or receipt
  before returning a conflict. Every identity is now checked before mutation; duplicate classes,
  roles, hold scopes, mirrors, purge receipts and active push identities fail without side effects.
- Delete replay now binds tenant, project, artifact, subject and request kind. Request IDs are
  tenant-unique, and an already-used request ID cannot be aliased to a missing artifact.
- Retention eligibility is the later of the class deadline and explicit `retention_until` in both
  Rust and SQL. Policy identifiers use one bounded grammar across both implementations.
- Purge busy and terminal states are distinct typed failures. A hold cannot overtake an active purge,
  shared references are rechecked, and revision/job/attempt/idempotency/cancellation/cleanup paths
  cannot add a reference after tombstoning.
- Mirror registration binds the device digest. Active push IDs are unique inside a tenant/project,
  expired reservations require a fresh identity, and acknowledgements bind the exact subject, plan,
  generation, revision and expected remote head.
- `PUBLIC EXECUTE` is now revoked for all 18 v9 functions, including the identity-protection trigger
  function; the disposable database verifies the application role's effective privileges.
- The receipt field is named `legal_hold_overtake_rejected`: the fixture proves ordered overtake
  rejection and does not overclaim a scheduler-level concurrent race.
- P14-09 supersedes the P14-07 Cargo source locks while validating those historical blobs by exact
  `git show` from commits `0f4128c73c55e14fac2c2e84dc5077fa2010119c` and
  `d84a442f866942a64dc478708dfd2942c4538af6`.

## Exact PostgreSQL evidence

The authoritative Git-ignored receipt is
`implementation/p14/evidence/p14-09-postgres-retention-mirror-audit-20260904T124406Z.json`:

- bytes: `2350`
- SHA-256: `2b06e582c0d9e727b7948c56b4926dc845c8c1b687d38094ad8ac9761f639f4d`
- exact clean source revision: `1d5de34121a8ba7cb9fc651cb90d63d7973db2dc`
- contract SHA-256:
  `080dda5dd65a7e803c49d73648691dd49971c0a8ade1b70b8521a7a5a9e6d7c5`
- validator SHA-256:
  `11b87d37cfb76b523c29ee9dfb28500b4f57e2cb38d61f21e08f2fcc46b24676`
- harness SHA-256:
  `0bf2cef3676483deb123049c87fbc74a8d900e07ea66110c5dc89a8195f39b4e`
- v9 up/down migration SHA-256:
  `272da51d665be7b9c0b5150a641ca1f9f51b9b78cddb839096acb57eb71e9ec2`,
  `64d087d6bf6a1ff5abbaab80d3706d229dfcc1756732f6c2c95f5334f3ab1f62`
- smoke fixture SHA-256:
  `73c511a84003792ab6763b85f66e1c328558428b11be937c52d7f3fd6d82eda9`
- P14-07 regression fixture SHA-256:
  `c671b18f8d180f38cdd8d07a67918295621c5acc688cb55471cf89f248baf1f9`
- PostgreSQL: `18.4 (Debian 18.4-1.pgdg12+1)`
- image:
  `postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568`

The clean run applied v1-v9, ran all 32 new assertions and the unchanged 28-assertion P14-07
regression in three transactions each, refused rollback without the explicit gate and while v9 data
remained, restored v8, reapplied v9 and removed its labeled container. It used no network, host port,
host volume or persisted secret.

## Validation

| Check | Result |
|---|---|
| Contract validator | pass, 18 functions, 32 new assertions, 28 regression assertions, 9 locked sources |
| P14 negative/unit tests | pass, 132/132 |
| Retention/sync Rust tests | pass, 15/15 |
| Workspace format / Clippy / tests | pass / pass with `-D warnings` / pass |
| Actual PostgreSQL apply/reapply | pass |
| Retention, legal-hold and shared-reference safety | pass |
| Delete replay, purge fencing and immutable receipt | pass |
| Mirror CAS, three conflict paths and expired recovery | pass |
| Guarded rollback and exact v8 restoration | pass |
| Exact-commit non-security lanes | pass, 4/4 |
| Exact-commit security lane | pass, every check exit 0, SBOM 680 |
| Offline Linux target | pass, Clippy and 15/15 tests |
| Residual P14 containers / `Hwp.exe` | pass, 0 / 0 |

The exact-commit security report is Git-ignored at
`implementation/p01/evidence/security-runs/ee55b08e113b41e18573dc52f0ae2c75/report.json`, bytes
`1294`, SHA-256 `96304c597b5550cd832c4935e2b378926b2e087b70fcd8bb099ff86f0e4dbfa5`.
Its first `pnpm audit` attempt received an actual successful response. Secret scan, Cargo advisory,
policy/license/source, pnpm advisory/license, both .NET vulnerability and SBOM checks all exited 0;
`failed_checks` is empty. The 680-component SBOM is 660107 bytes with SHA-256
`f23561bd26732851c0d9d820f5d2820c70cf807a83c20984df9a672236c76ab3`.

The offline Linux audit used local image
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`.
Networking was disabled, source and Cargo registry were read-only, and writable build state existed
only in temporary filesystems. Clippy `-D warnings` and all 15 tests passed.

## Decision and limits

P14-09's required retention/sync service exists, and local Rust plus actual disposable PostgreSQL
evidence proves bounded retention, legal-hold, purge and local-mirror conflict behavior in this scope.
P14-09 may be checked and the separate P14 phase Gate may be audited.

This does not qualify a production daemon, production database connection pool, external object
store, remote Codex transport, identity provider, backup/restore, high availability or legal-policy
suitability. No Hangul process, user document, original ZIP, registry/system setting or production
database was used or changed. Continue with the P14 phase Gate at reasoning effort `max`.

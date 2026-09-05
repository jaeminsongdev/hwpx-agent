# P16-06 local PostgreSQL artifact repository — implementation checkpoint

- Date: 2026-09-05. Current-PC local development only; no Hangul launch or user document.
- Parent: `9c120ac7407c00a7454a195c403330b47ff0524f` authenticated process-local Plan registry.
- Review: HIGH / STRICT. Component evidence below is not P16-06 completion or a production Gate.
- Main integration, source-contract qualification, stored Plan/source adapter and renderer remain open.

## Implemented product boundary

`LocalPostgresMetadataRepository` implements the existing artifact metadata repository against real
PostgreSQL while retaining the existing encrypted blob and ArtifactService consumers. It fixes one
tenant per repository and uses one shared connection, bounded connection/server timeouts, repeatable
read transactions and transaction-local tenant context. A busy or poisoned connection fails closed.
No transparent write/commit retry, public database host, arbitrary SQL or connection option is exposed.
This loopback/NoTls adapter is explicitly not a deployment or remote-server TLS qualification.

Admission requires the exact ten migration digests, a non-superuser/non-BYPASSRLS/non-creator role,
forced RLS and the exact single tenant policy on all three tables. It rejects both inherited table
owner privileges and the ability to SET ROLE to an owner, plus excessive schema/table privileges.
The distinction between immediate USAGE and SET membership is specified by the
[PostgreSQL 18 privilege functions](https://www.postgresql.org/docs/18/functions-info.html).
These checks detect the covered misconfigurations; a malicious database administrator is not an
independently attested execution environment.

Metadata and initial owner ACL are inserted in one transaction. Mutation contracts now take
`expected_acl_version`; both PostgreSQL and in-memory implementations compare it before permissions
or storage-state changes. This prevents stale authority from changing an already-updated record.
Immutable metadata, tenant filters, existing DB manager-retention triggers and authorization-generation
increments remain enforced. Reads admit typed/bounded values; ACL reads cap at 256 entries and audit
reads at 4,096. Exceeding these bounds fails rather than silently truncating accepted data.

Migration v10 adds a closed immutable tenant-isolated artifact audit table and ordered tenant index.
Rollback requires an explicit local maintenance gate, exact v10/no later version and empty audit
data. Only inside that transaction is the migration-history trigger disabled for the exact v10
registration removal, then restored. Original migrations are unchanged. The acceptance verifies
all predecessor rows are retained and the immutable-history guard still rejects mutation.

`postgres = =0.19.14` with UUID support is the new locked dependency. Current source/dependency locks
must be qualified before integration; predecessor P14/P15/P16 contracts are not silently regenerated.

## Safe diagnostics for this and later debugging environments

`connect` preserves the stable ArtifactError interface. The additive `connect_diagnosed` performs
the same admission and returns only a `PostgresConnectStage` and stable public error category.
Stages are TRANSPORT, ROLE, MIGRATIONS, POLICIES and PRIVILEGES. No backend exception/source chain,
SQL, credentials, database name, tenant or private path is retained in the diagnostic value.
Config/repository Debug is redacted. No logging is enabled globally or emitted by the library.
The disposable probe and harness opt into closed stage markers and safe summaries.

The harness checks exact ownership and current IPv4 loopback binding after a Docker restart. An
ephemeral host port can be reassigned; it is read afresh instead of reusing a stale endpoint. This
does not retry an uncertain business operation. Negative role/policy/privilege cases require their
exact stage plus ACCESS_DENIED, so an unrelated outage cannot masquerade as a successful rejection.

## Verification and retained failures

- Windows artifact-service all-target tests: **35 passed**, zero ignored.
- Formatting and all-target/all-feature Clippy with warnings denied: PASS.
- Harness unit tests: **5 passed**, including ownership/address/port bounds and diagnostic privacy.
- Secret scan: 1,050 files, zero findings at this checkpoint.
- Actual disposable PostgreSQL + encrypted local blob acceptance: **PASS** at final implementation
  source, run `5a68a12751804d6f84df2b42ebed2f11`; receipt SHA-256
  `36a91a3b60ba27af0218987e7c1cb5b1a824259a76089a2cb8e4d0b71d71e4cc`.
- That receipt binds all adapter/migration/harness sources and the exact probe binary. Evidence is
  under `artifacts/p16/postgres-artifacts/runs/<run-id>/report.json` in this worktree, not tracked.

Actual checks include all migrations; guarded rollback/reapply; encrypted ingest/download and
deduplication; duplicate insert conflict; fresh process and database-restart readback; ACL grant and
revocation; stale ACL mutation rejection; last-manager retention; stale storage-state rejection;
wrong-key failure; quarantine and privileged readback; rejected BYPASSRLS, disabled/permissive RLS,
schema CREATE and settable-owner configurations; cross-tenant query isolation; immutable ciphertext
metadata; rejected nonempty rollback; final readback and exact source hashes unchanged during run.
This does not test crash-at-every-instruction recovery, concurrent load or a production scanner.

| Retained run | Meaning |
|---|---|
| `73be1b04dcbc4cd0879de93c5956fe0e` | Original guarded rollback failed against immutable migration-history trigger. |
| `e78573e5a5cc44a38e92e6a7bac5c40e`, `afee7194223c4389900cfcd5fff57ac9` | Connection verification failed: authoritative bigint version decoded incorrectly as i32. Corrected to i64. |
| `dddf0748878544ab9e67b2badab366a4`, `6bfd386f8e27428f9d0ad5d81f7942cd` | Initial ingest/readback passed, then restart transport failed from stale ephemeral endpoint. |
| `c74c1dfc1886485d92db79c19f60af55` | Initial acceptance passed before the added settable-owner security regression. Not final implementation evidence. |
| `8cb81ac369fb4c17900dd14af5721726` | Added actual negative test failed before the USAGE-or-SET owner admission fix. |
| `5a68a12751804d6f84df2b42ebed2f11` | Same strengthened acceptance passed after the owner-admission fix. |

All actual runs cleaned only their exact label/UUID-owned disposable containers and volumes.
Receipts and encrypted local test objects remain retained; no original document or earlier failure
evidence was deleted. No prompt bypass or security-setting change on the host occurred.

## Remaining qualification and implementation

Run workspace/current FULL, exact clean-checkout FULL, applicable offline Linux checks and the full
security lane. A prior P16 preview-digest hold and source-bound predecessor contracts remain open;
do not mark them PASS based on these artifact tests. Then build the authenticated durable
PlanSourceRepository/stored-plan path and wire the actual renderer with source/revision/ACL/expiry
checks. This artifact adapter alone does not make the process-local Plan registry durable, produce
a preview or authorize document execution. Recommended next reasoning: `max`.

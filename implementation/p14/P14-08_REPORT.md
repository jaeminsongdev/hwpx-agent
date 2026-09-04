# P14-08 safe cancellation and cleanup report

- Date: 2026-09-04
- Implementation commit: `8d03bb6`
- Decision: `pass_scoped_local_disposable_postgres_and_reference_worker`
- Review: `STRICT / max`, blocker/major/minor after correction `0/0/0`

## Delivered

- A bounded Rust cancellation and cleanup reference worker with opaque identifiers, redacted debug
  shapes, exact tenant/project authorization, lease expiry, retry limits and fencing.
- Immediate cancellation for queued work, safe-point cancellation for active work, explicit
  `unknown_outcome` after a started external effect and `too_late` after a committed effect.
- Exact temporary-workspace cleanup and database-derived orphan quarantine. Source artifacts and
  every revision/job/receipt/idempotency/cancellation reference are protected.
- Digest verification before and after quarantine, plus recovery for the interrupted state where the
  durable quarantine hard link exists but the published name was not removed. Digest mismatch fails
  closed and preserves both names.
- PostgreSQL migration v8 with forced RLS, public privilege revocation, immutable request/task/
  receipt identities, reference rechecks, `available -> purging -> quarantined`, bounded leases and
  guarded rollback to the exact v7 function definitions.
- A digest-pinned contract, 18-assertion smoke fixture, previous P14-07 28-assertion regression,
  concurrent-claim test, both external-effect fault windows and CI integration.

## STRICT review corrections

The first working SQL candidate let a reference-raced pending task remain first in the claim order,
which could starve later valid cleanup. Candidate selection now skips currently referenced rows and
rechecks after row locking, retaining the race defense without blocking the queue.

The first filesystem retry model handled a crash after a complete quarantine but not the narrower
hard-link-created/source-name-removal-failed interval. The final foundation API revalidates both
names against the bounded expected content digest and removes only the exact orphan output. A
separate negative test proves mismatched quarantine bytes preserve both files.

The v8 down migration stores the exact v7 function definitions with `pg_get_functiondef`, refuses
without the explicit rollback gate or while v8 data remains, and restores the original functions.

## Exact PostgreSQL evidence

The authoritative Git-ignored receipt is
`implementation/p14/evidence/p14-08-postgres-cancel-cleanup-audit-20260904T110000Z.json`:

- bytes: `1855`
- SHA-256: `a61f2137e5026b0f728aed67fcbdc0a8dd14cec36bcabf868069926cb79cc535`
- exact clean source revision: `8d03bb6b4fb69e73f8921aa26484b400dadf941b`
- contract SHA-256:
  `ee5b6f1180d1c2cc0363a5dae911647f5dc6f8ea536722baf61d04b76a23d291`
- validator SHA-256:
  `dc9ab7b0dfeca07d5a7f7bfe2f665b2c5ec3ec09a3b6732d13f26ce15eae65db`
- harness SHA-256:
  `4387953c216f32a461c8cfcd00075ce47909878c7296a2f54b0b32f7ad9241bc`
- v8 up/down migration SHA-256:
  `2ba28c1386db9c5aeb4661d11069e48f8624c2560b69301a0750ab9344c46f29`,
  `e47f286a755d7928d2a9db9c5b1ee4af2aad5661e346568ae2116ec7d2922599`
- smoke fixture SHA-256:
  `e95897dbab32fb8cb358fb2813b4e25e00eec66aaad1c48d739e2029768fdf5a`
- P14-07 regression fixture SHA-256:
  `c671b18f8d180f38cdd8d07a67918295621c5acc688cb55471cf89f248baf1f9`
- PostgreSQL: `18.4 (Debian 18.4-1.pgdg12+1)`
- image:
  `postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568`

The clean run applied v1-v8, ran 18 assertions in three transactions and the unchanged P14-07
28-assertion regression twice. Eight concurrent claimers produced exactly one winner and seven
bounded misses. It exercised crashes immediately before cleanup and immediately after cleanup but
before receipt publication, rejected a stale fence and a reference race, protected the source
artifact, refused both unsafe rollback forms, restored v7, reapplied v8 and removed both labeled
containers. No host port, host volume, network or persisted secret was used.

Because the filesystem recovery addition changed two P14-02 source locks, that earlier contract was
also revalidated at the same exact clean commit. Its ignored receipt is
`implementation/p14/evidence/p14-02-postgres-artifact-service-recheck-20260904T110100Z.json`, bytes
`1824`, SHA-256 `d1b0878522373fd446be06712f100b4b39f1ba9dde742199873f183f4fbb76c5`;
both 22-assertion runs, rollback and reapply passed.

## Validation

| Check | Result |
|---|---|
| Contract validator | pass, 13 functions, 18 new assertions, 28 regression assertions, 8 locked sources |
| P14 negative/unit tests | pass, 115/115 |
| Cleanup worker Rust tests | pass, 10/10 |
| Foundation Rust tests | pass, 14/14 |
| Workspace format / Clippy / tests | pass / pass with `-D warnings` / pass |
| Actual PostgreSQL apply/reapply | pass |
| Concurrent cleanup claim | pass, `1 winner + 7 bounded misses` |
| Fault injection / stale fence / reference race | pass |
| Guarded rollback and exact v7 restoration | pass |
| Exact-commit non-security lanes | pass, 4/4 |
| Exact-commit security lane | pass, every check exit 0, SBOM 679 |
| Offline Linux related crates | pass, Clippy and 65/65 tests |
| Residual P14 containers / `Hwp.exe` | pass, 0 / 0 |

The successful security report is Git-ignored at
`implementation/p01/evidence/security-runs/428ccd9e403e47e699dcb5b156dc2e7a/report.json`, bytes
`1469`, SHA-256 `075289b1e5bce38752dd6150016e9d3a48723b63871610c44e8356d7fe002987`.
The first bounded `pnpm audit` call timed out and cleaned up; the second received an actual response.
All vulnerability, secret, license and SBOM checks passed. A concurrent aggregate run later timed out
on all three duplicate `pnpm audit` attempts; its failed report is preserved as an operational
diagnostic and is not promoted to PASS.

The offline Linux audit used local image
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`.
The authoritative run disabled networking, mounted source and Cargo registry read-only, and used
executable tmpfs for Cargo metadata, target, temporary and Rustup temporary files. The first setup
attempt stopped before compilation because Rustup temporary storage was read-only; the corrected run
passed and left no labeled container.

## Decision and limits

P14-08's required cleanup worker exists, and local Rust plus actual disposable PostgreSQL evidence
proves cancellation boundaries, orphan/source/reference safety, fenced retries and both specified
fault windows in this scope. Only P14-08 is checked; P14 remains open for P14-09.

This does not qualify a production daemon, production PostgreSQL client, external object store,
multi-host failover, retention purge, legal hold or Codex project-state mirroring. No Hangul process,
user document, original ZIP, registry/system setting or production database was used or changed.
Continue with P14-09 at reasoning effort `max`.

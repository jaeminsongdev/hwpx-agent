# P14-03 revision CAS report

- Date: 2026-09-04
- Implementation commit: `f225dbc`
- Decision: `pass_scoped_p14_03_local_disposable_postgres_and_in_memory_service`
- Review: `STRICT / max`, blocker/major/minor after correction `0/0/0`

## Delivered

- A Rust `revision-service` crate with exact typed project, branch, revision and commit identifiers,
  canonical request hashing, authenticated tenant/subject context, verified-only commit requests,
  bounded ordered parents and redacted public debug forms.
- An immutable sealed revision node and digest-bound receipt model. The authenticated subject digest,
  request digest, prior head, committed head, transaction receipt and commit identity all participate
  in the stored node or receipt.
- An atomic in-memory compare-and-swap repository. A stale expected revision or generation returns a
  typed conflict without creating a node, receipt or head mutation. Duplicate stream, revision and
  commit identities, missing/unsealed parents, cycles and generation overflow fail closed.
- PostgreSQL v3 branch/project head generations, immutable `revision_graph_seals` and
  `revision_commit_receipts`, forced RLS, revoked public privileges, parent-cycle/seal guards and a
  fixed-search-path `SECURITY DEFINER` CAS function.
- The PostgreSQL CAS requires transaction-local tenant and subject context, project owner/editor
  authorization, an active project, available verified source/result/diff artifacts, a verified
  revision and an exact expected head. A default branch and project head advance in one transaction.
- Existing non-null pre-v3 heads migrate to generation `-1` with `legacy_unqualified` seals and
  cannot be treated as qualified CAS roots.
- A guarded v3 down migration, digest-pinned PostgreSQL 18.4 contract, 20-assertion smoke fixture and
  a real two-session row-lock race harness. The harness applies, rolls back, reapplies and repeats.
- The P14-03 contract validator is part of the normal docs lane. Volatile workspace membership was
  removed from the older P14-02 source lock while all artifact-service-local source locks remain.

## Correctness review correction

The strict review found one major in the first in-memory implementation: duplicate stream
provisioning used `BTreeMap::insert`, which replaced an existing non-empty head with an empty head
before returning `DuplicateStream`. It now uses the entry API, rejects the duplicate without any
mutation and has an explicit regression assertion that the committed generation remains unchanged.

The duplicate identity test was also strengthened so duplicate revision and duplicate commit IDs are
both exercised against a matching current head; a stale-head conflict is no longer accepted as proof
of those failure paths. An unused conflict error variant and two unused crate dependencies were
removed.

## Actual PostgreSQL evidence

The authoritative Git-ignored receipt is
`implementation/p14/evidence/p14-03-postgres-revision-cas-audit-20260904T043337Z.json`:

- bytes: `2248`
- SHA-256: `26baffa02983ffa5c2503a7ab977f88405008cd30af70b2367b09899615d8175`
- exact clean source revision: `f225dbc39d6669ff4ca44bcee05cbbe68b9f4756`
- migration contract SHA-256:
  `ee5f5179d823bd3cff1e874817592c37e00bf2bd3337cee9a82450ef1103be6e`
- test harness SHA-256:
  `3e1d47fa52939a559583174f594e83bd6cd8becef89fae4b252c2abcd4255677`
- validator SHA-256:
  `8b67ae02a1a527dd81ac2610249fb4c9ec1d59f078acbe180bc7d73c3c99c240`
- prerequisite v1/v2 up migration SHA-256:
  `7c00f744993581448acb4b6d4d8a46f1ff03d108750da0afc671c3b5e2b0a78d`,
  `202753fbd6f20f181b09bd6227766dfb808811bd4e734a4a418cb5bae4eaee56`
- v3 up/down migration SHA-256:
  `beeac1f22fde0eb3474d40acc14838c1e9676a74b68c5b6f9608713ba6e6e53a`,
  `cf99f107ebca0be77a18c23b83e937dff36e39a6610c6fa3b1fff9964d35cabb`
- smoke fixture SHA-256:
  `fe73afa47dc88f70d55f6b7f7889b7ce64c7f7bd8ce1c827ff76989d66f68dfb`
- PostgreSQL: `18.4 (Debian 18.4-1.pgdg12+1)`
- image:
  `postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568`

The clean run applied v1, v2 and v3, verified a pre-v3 head was forced to unqualified generation
`-1`, ran all 20 SQL assertions, and ran a two-session race. It then refused an ungated v3 rollback,
performed the gated rollback while retaining v2, reapplied v3 and repeated all assertions and the
race. Each race produced exactly one commit and one typed conflict, made the contender wait on the
locked branch row, persisted exactly one candidate node/receipt and advanced the head exactly once.
No host port, host volume or container network was used, and the exact labeled container was removed.

## Validation

| Check | Result |
|---|---|
| Contract validator | pass, exact image/digests, 2 tables, 20 assertions |
| P14 negative/unit tests | pass, 12/12 revision-contract tests; 37/37 combined P14 tests |
| Rust revision service | pass, 14/14 including simultaneous CAS and side-effect-free conflicts |
| Actual PostgreSQL apply/reapply | pass, 2/2 |
| Actual SQL smoke | pass, 20/20 per run, 2 runs |
| Real two-session same-head race | pass, `1 committed + 1 conflict`, 2/2 |
| Legacy head fail-closed and v2-preserving rollback | pass |
| Current checkout `linux-core`, `docs`, `widget`, `windows-worker` | pass |
| Exact-commit detached clean worktree, same four lanes | pass; worktree removed after verification |
| Offline Linux target Clippy/tests | pass, network disabled, source/registry read-only, `21+12+14` tests |
| Secret scan | pass, 847 files, findings 0 |
| Cargo deny/audit, pnpm audit/license, .NET vulnerable, SBOM | pass |
| Residual P14 containers / audit worktree / `Hwp.exe` | pass, 0 / 0 / 0 |

The exact-commit security report is Git-ignored at
`implementation/p01/evidence/security-runs/f603c529178c4a9284660547fabf13b8/report.json`, bytes
`1469`, SHA-256 `a0e6f1b7961694b990e2620e366293cb3803f1a4b1c3ec1bb6b51e7b60aeae74`.
All checks passed. `pnpm audit` timed out once with successful cleanup and succeeded on attempt two.
The SBOM contains 675 components.

The offline Linux audit used the exact local image
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`.
Three setup attempts stopped before product compilation while the read-only invocation was corrected
(Cargo path, Rustup temporary path, then tmpfs `noexec`). The final run kept network disabled, source
and Cargo registry read-only, enabled execution only in the disposable build tmpfs, passed, and left
zero containers.

## Strict task decision and limits

P14-03's required revision service exists and both service-level and actual PostgreSQL race/conflict
tests prove its local scoped invariants, so only the P14-03 roadmap checkbox is checked. P14 remains
open and P14-04 through P14-09 are not qualified.

The in-memory Rust repository and PostgreSQL transaction function are independently tested current-
stage adapters; a production PostgreSQL client implementation connecting the Rust service to that
function is not claimed here. Production database HA, authenticated control-plane ownership of DB
session context, multi-host failure recovery, remote artifact-store transactions and performance at
production concurrency remain unverified. No Hangul process, user document, source fixture,
registry/system setting or production database was used by P14-03.

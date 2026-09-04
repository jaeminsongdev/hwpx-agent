# P14-04 history/checkpoints report

- Date: 2026-09-04
- Implementation commit: `59e26b6`
- Decision: `pass_scoped_p14_04_local_disposable_postgres_and_in_memory_service`
- Review: `STRICT / max`, code blocker/major/minor after correction `0/0/0`

## Delivered

- A Rust `history-service` crate with typed project/revision/checkpoint/branch inputs, redacted debug
  forms and HMAC-SHA256 cursors. Cursor keys and TTLs are bounded; tokens are tenant/subject bound,
  signed, size limited and expiring.
- Stable head-fixed pagination across a reachable merge DAG. The Rust service emits deterministic
  child-before-parent order, preserves the original snapshot after a real head advance and rejects
  duplicate/missing/cyclic, cross-project, bad-generation or greater-than-10,000-node projections.
- Semantic-diff cursors resolve only after signature verification, current authorization and exact
  revision-to-artifact rebinding.
- Immutable/idempotent checkpoints bound to the creating subject and canonical request digest.
  Exact retries replay; request drift, identity/label reuse and reader mutation fail closed. A real
  in-process race yields one creator and one replay.
- Qualified branch creation for editor/owner roles only, with bounded canonical names and unique
  identities/names.
- PostgreSQL v4 `history_checkpoint_requests`, forced RLS, immutable trigger, deterministic history
  index, fixed-search-path history/checkpoint/branch functions, public privilege revocation and an
  explicitly gated rollback that preserves v3.
- The DB query rejects reachable legacy nodes, parent generations that do not precede their child
  and graphs above 10,000 nodes. Its result is a deterministic generation/revision keyset plus full
  parent arrays; the stronger child-before-parent presentation order belongs to the Rust service.
- A digest-pinned contract/validator, 26-assertion SQL fixture, real PostgreSQL apply/reapply/
  rollback harness and two-session checkpoint race. The validator is part of the docs CI lane.

## STRICT review corrections

The first manual PostgreSQL smoke exposed an ambiguous unqualified `checkpoint_id` reference; table
aliases now make every such reference exact. That failed dirty diagnostic is not authoritative.

Further review redacted cursor/key material from debug output, bound idempotent replay to the creating
subject, strengthened the head-advance snapshot test, rejected checkpoints mixed from another
project by an adapter, validated every merge parent generation, added a 10,001-node Rust regression
and made PostgreSQL fail closed on hidden legacy parents and invalid graph generations.

## Exact PostgreSQL evidence

The authoritative Git-ignored receipt is
`implementation/p14/evidence/p14-04-postgres-history-audit-20260904T053909Z.json`:

- bytes: `2454`
- SHA-256: `2965d5b7988a16e162600fb3a02ffa4ab665018c1b376847de4f37f703331ab7`
- exact clean source revision: `59e26b68e8986b56471db1eb6d58912cb328b8b0`
- migration contract SHA-256:
  `e7713ccd37697a1a46f544e5961640d7d0835d521b71eee3116411136108fa13`
- test harness SHA-256:
  `edc5999d3db294b8f213f59868e58efc252ddc6a2cee688ca1fcfb887456f063`
- validator SHA-256:
  `983e0f1f2d100cf64c9cc0785b9f24330c3ee7301a5a5fbb11c9ed6fd47f9e89`
- v4 up/down migration SHA-256:
  `e336890d4ee3fdf4819f52c079ba320f450b01ec516bf5ffaaf505a76b14f249`,
  `a2d635bfb50fb93e9bbbd1ff37a04e223aec456afa21098b9ef83047f25c05e4`
- smoke fixture SHA-256:
  `d9aadde5dff7e02b6f6506a4f6c8caf5dbb168fee4ab1bec2e5ea0b2e5bddafd`
- PostgreSQL: `18.4 (Debian 18.4-1.pgdg12+1)`
- image:
  `postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568`

The clean run applied v1-v4, applied v4 twice across reapplication, ran all 26 assertions twice and
ran two real races. Each race persisted exactly one claim/checkpoint/audit triple and returned one
created plus one replayed result after row-lock contention. An ungated rollback was refused, a gated
rollback retained v3, and full reapply succeeded. No host port, host volume or container network was
used; the labeled container was removed.

## Validation

| Check | Result |
|---|---|
| Contract validator | pass, exact image/digests, 3 functions, 26 assertions |
| P14 negative/unit tests | pass, 49/49 |
| Rust history service | pass, 16/16 including concurrency, adapter drift and 10,001-node limit |
| Actual PostgreSQL apply/reapply | pass, 2/2 |
| Actual SQL smoke | pass, 26/26 per run, 2 runs |
| Real two-session checkpoint race | pass, `1 created + 1 replayed`, 2/2 |
| Gated rollback retaining v3 | pass |
| Exact-commit `linux-core`, `windows-worker`, `widget`, `docs` | pass |
| Offline Linux target Clippy/tests | pass, Rust 1.96.0, network/source/registry controls enforced |
| Secret scan, Cargo deny/audit, licenses, .NET vulnerable, SBOM | pass |
| `pnpm audit --audit-level high --json` | pass; attempt 1 timed out and cleaned, unchanged attempt 2 succeeded |
| Residual P14 containers / `Hwp.exe` | pass, 0 / 0 |

The closing security report is Git-ignored at
`implementation/p01/evidence/security-runs/b5b22d3d1ce54ee29838130b850b8ad2/report.json`, bytes
`1469`, SHA-256 `5f3c67664516a4100cc4f3cd5d10008362f21e0c3a1f41675d51a503bcb8af98`.
It ran at exact current commit `3876679eddff4b882142f5a5344fb7e75ede83ed`, where the P14-04
implementation sources are unchanged from `59e26b6`. It scanned 873 files with zero secret findings;
Rust advisory/deny, Node licenses, both .NET vulnerability checks and a 677-component SBOM passed.
The first bounded `pnpm audit` attempt timed out after 60 seconds and its process tree was cleaned;
the unchanged second attempt returned successfully with zero vulnerabilities. No audit process
remained. This current successful result, rather than the earlier timeout or a historical lockfile
result, closes the security condition.

The offline Linux audit used local image
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`.
One setup attempt stopped before product compilation because Rustup tried to write to its read-only
home. The corrected run invoked the fixed toolchain directly, kept network off, source/registry
read-only and build state on executable tmpfs, then passed Clippy and all 16 tests. No container
remained.

## Decision and limits

P14-04 is PASS only for the local in-memory service and disposable PostgreSQL scope proven above,
and its roadmap row is checked. This report does not claim production PostgreSQL, an HTTP API, a
Rust PostgreSQL adapter, KMS-backed cursor keys, multi-host behavior, performance capacity or later
P14 tasks. No user document, original ZIP, registry/system setting or production database was read
or changed.

P14 remains open. P14-05 is reported separately; continue with P14-06 worker lease/fencing at
reasoning effort `max`.

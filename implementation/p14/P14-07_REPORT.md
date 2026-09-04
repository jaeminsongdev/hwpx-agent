# P14-07 idempotency/reconciliation report

- Date: 2026-09-04
- Rust core commit: `fbcdcef`
- Durable integration commit: `d84a442`
- Decision: `pass_scoped_local_disposable_postgres_and_in_memory_reference`
- Review: `STRICT / max`, blocker/major/minor after correction `0/0/0`

## Delivered

- A bounded Rust `idempotency-service` reference with exact tenant, subject, project, branch, job,
  key, request, source, expected effect, transaction receipt and revision-head generation binding.
- Deterministic retry policy, attempt/fencing progression, terminal replay, automation
  `outcome_unknown` freeze and trusted committed/no-effect reconciliation paths.
- PostgreSQL migration v7 with version-2 idempotency records, multi-attempt job coupling, forced RLS,
  fixed-search-path security-definer functions and public privilege revocation.
- Atomic claim, lease, stage, heartbeat, retry, unknown-outcome, terminal success/failure,
  reconciliation and read functions. Legacy version-1 rows remain readable but are never promoted.
- A fresh unpredictable per-attempt commit capability returned only by the lease function. The v2
  revision-CAS wrapper and receipt trigger bind and consume it with the exact job, execution,
  attempt, fence and transaction receipt.
- A digest-pinned PostgreSQL 18.4 contract, 28-assertion smoke fixture, 16-client claim race,
  real commit-versus-retry race, guarded rollback/reapply harness and docs-lane integration.

## STRICT review corrections

The first integration draft trusted too much caller-supplied equality. The final committed oracle
also joins the verified service revision, operation plan, creator subject, result artifact and ACL,
service seal, commit identity/request, branch, previous head, generation and current head.
No-effect reconciliation takes a shared branch-row lock, closing the time-of-check/time-of-use gap
against the exclusive revision CAS.

A later review found that an old worker could still publish after a retry if it reached the revision
CAS late. A database authorization row was added and every retry, unknown or terminal transition
revokes it. The predictable row identity was then replaced with an unpredictable attempt-scoped UUID
capability; the application has no authorization-table privilege and cannot call the underlying CAS
directly. A v7 revision receipt with an arbitrary unbound transaction digest is rejected rather than
falling back to the pre-idempotency path.

The smoke and concurrent harness exercise a wrong capability, direct unbound commit, stale fence,
sequential late commit after retry and a real commit-versus-retry race. Exactly one side of the race
wins, and the losing path creates no second effect.

## Exact PostgreSQL evidence

The authoritative Git-ignored receipt is
`implementation/p14/evidence/p14-07-postgres-idempotency-audit-20260904T094041Z.json`:

- bytes: `2770`
- SHA-256: `9ce87e32a6f4ba67fefb7866054fdf8ae9025956e76fd3f872044074af80df27`
- exact clean source revision: `d84a442f866942a64dc478708dfd2942c4538af6`
- migration contract SHA-256:
  `1cde33916ecd91b106aa0af6ea12abb573ff0af773e7dbc219ea0c443fc24292`
- validator SHA-256:
  `2c32d496eae0f634024545f07a2cff97ed0d878598f8b37972e96a18cd9467aa`
- test harness SHA-256:
  `60b27bd89f9b1b23ee568d23f0ee32919f3bdf06b94b187cf6cb7096e7913721`
- PostgreSQL support SHA-256:
  `961ad7a8ef198e77ff5e5e8948260ec0fbda7f8761d017763c0d3cdaf4ec6416`
- v7 up/down migration SHA-256:
  `cc60353df6cf3c51155417e39d0f1f4c348d2a6282bba7d63de9ea0282be5e5d`,
  `01e22824016dac04931b4e72e25167f13f659cbc333e80754f004a67579b373b`
- smoke fixture SHA-256:
  `c671b18f8d180f38cdd8d07a67918295621c5acc688cb55471cf89f248baf1f9`
- PostgreSQL: `18.4 (Debian 18.4-1.pgdg12+1)`
- image:
  `postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568`

The clean run applied v1-v7, ran the 28 SQL assertions in three transactions, and let 16 concurrent
claimers produce exactly one new claim and 15 exact replays. A real two-session commit/retry race
produced exactly one winner. It rejected a late commit after retry, an unbound direct commit,
ungated rollback, rollback with a later migration and rollback with remaining v2 data. It then
removed only disposable test rows, rolled v7 back while retaining v6, reapplied v7, repeated the
smoke, performed the final full rollback and removed the labeled container. No host port, host
volume, container network or persisted secret was used.

## Validation

| Check | Result |
|---|---|
| Contract validator | pass, 11 product functions, 28 assertions, 6 locked sources |
| P14 negative/unit tests | pass, 101/101 |
| Rust idempotency service | pass, 10/10 |
| Workspace format / Clippy / tests | pass / pass with `-D warnings` / pass |
| Actual PostgreSQL apply/reapply | pass, 2/2 |
| Actual SQL smoke | pass, 28/28 per transaction, 3 transactions |
| Concurrent duplicate claims | pass, `1 new + 15 replay` |
| Concurrent commit versus retry | pass, exactly one winner |
| Late/stale/unbound commit rejection | pass |
| Guarded rollback and v6 restoration | pass |
| Exact-commit `linux-core`, `windows-worker`, `widget`, `docs` | pass, 4/4 |
| Same-content security run before commit | pass, all checks exit 0, SBOM 679 |
| Exact-commit follow-up security diagnostics | local checks pass; `pnpm audit` endpoint timed out in two bounded 3-attempt runs |
| Residual P14 containers / `Hwp.exe` | pass, 0 / 0 |

The successful same-content security report is
`implementation/p01/evidence/security-runs/99ca0b470c6f47c480a3e1a676ae9eb5/report.json`, bytes
`1294`, SHA-256 `af4e65eea30e472aa9e061c6206b21a36a836ade9c2f8010f4705839bf09dd4b`.
It was produced immediately before the identical source bytes were committed as `d84a442`; all
checks passed and `pnpm audit` succeeded on its first attempt. The later exact-commit reports
`6d55e8f734704a179802d34d66813122` and `45f1a0f505ea49d5ba8ac102ba209580`
are retained as failed operational diagnostics: every local check passed, but the external advisory
request timed out three times in each run. They are not promoted to PASS or used to replace the
successful report.

## Decision and limits

P14-07's required idempotency module exists, and local Rust plus actual disposable PostgreSQL
evidence proves duplicate execution, retry fencing, outcome-unknown reconciliation and exact
single-effect behavior within this scope. Only P14-07 is checked; P14 remains open for P14-08 and
P14-09.

This does not prove a production PostgreSQL client, API/MCP exposure, distributed transactions,
multi-host recovery, production HA, performance at production load, cancellation/cleanup,
retention, legal hold or Codex project-state mirroring. No Hangul process, user document, original
ZIP, registry/system setting or production database was used or changed. Continue with P14-08 at
reasoning effort `max`.

# P14-06 worker lease/fencing report

- Date: 2026-09-04
- Core implementation commit: `205f4ac`
- Decision: `pass_scoped_local_disposable_postgres_and_in_memory_scheduler`
- Review: `STRICT / max`, blocker/major/minor after correction `0/0/0`

## Delivered

- A Rust `scheduler-service` crate with exact target-profile and capability-digest matching,
  subject/tenant-bound worker registration, ready/draining state, worker heartbeat and bounded worker
  leases.
- Job leases that cannot outlive the selected worker, exact agent/execution/attempt/fence binding,
  bounded heartbeat renewal and rejection of every stage/success/failure mutation at or after expiry.
- A guarded expiry finalizer that alone can close an expired attempt with `LEASE_EXPIRED`; the final
  receipt must already be qualified for the same tenant, project and subject.
- PostgreSQL v6 worker registration/RLS, worker and job heartbeat functions, expiry finalization and
  replacement v5 job guards so even the older lease function is bound to a live exact worker.
- A guarded v6 rollback that refuses missing authorization and later schema versions, restores the
  original v5 functions and retains v5.
- A digest-pinned contract, strict validator, 20-assertion SQL fixture, actual PostgreSQL harness and
  CI docs-lane integration.

## STRICT review corrections

The first disposable PostgreSQL run exposed a composed-clock bug: the worker heartbeat wrote
`clock_timestamp()` while the existing v5 stage transition used transaction time, so a same-
transaction stage could appear to regress `updated_at`. Lease liveness still uses real time, while
the heartbeat now advances `updated_at` with `GREATEST(updated_at, transaction_timestamp())`.

Review also found missing positive worker-heartbeat evidence and insufficient negative timing
coverage in the first fixture draft. The final 20 assertions include a successful worker heartbeat,
an actually stale worker rejection, early-expiry refusal, late-success refusal, stale-fence
rejection, unqualified-receipt refusal and qualified expiry finalization. Only the corrected clean
run below is authoritative.

## Exact PostgreSQL evidence

The authoritative Git-ignored receipt is
`implementation/p14/evidence/p14-06-postgres-worker-lease-audit-20260904T072740Z.json`:

- bytes: `2256`
- SHA-256: `7ef9f404ec1838d7d3619414c2b29df8cd15104bf68884fd547c913ddd842ca6`
- exact clean source revision: `205f4acd845bcd9ef968e87a7d912cb0d7e81abf`
- migration contract SHA-256:
  `638f028da4c9837415eca85eeacf094547a595c64a4336330dfe89b5b9d93c29`
- test harness SHA-256:
  `6e8bd30a7e9fdefbce6e88251c12f144f876e4513ebdf9acd7ba4a5b94cc6257`
- validator SHA-256:
  `5a213339dcfc25d11b124a1aa62f4d12f426566b6d4dd3c1ef25ebd86be92f5d`
- v6 up/down migration SHA-256:
  `03af7cc8b2ae883ff132e3b1737b29c3829fcb0fa9887566485f865b3c0393ab`,
  `bf1b9c5c8310dbb981bec3e150383474521941eb6ad9e47d23593a18a2388a90`
- smoke fixture SHA-256:
  `47a24bc59bbd00b903b180e7ed049eec2cc3bed0367b7f39492853f008e255aa`
- PostgreSQL: `18.4 (Debian 18.4-1.pgdg12+1)`
- image:
  `postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568`

The clean run applied v1-v6, ran all 20 assertions twice, rejected duplicate v6 application,
rejected ungated rollback, rejected rollback while a synthetic v7 existed, rolled v6 back while
retaining v5, reapplied and repeated the smoke. It published no host port, mounted no host volume,
used `--network none`, persisted no secret and removed its labeled container.

## Validation

| Check | Result |
|---|---|
| Contract validator | pass, exact image/digests, 4 functions, 20 assertions, 8 locked sources |
| P14 negative/unit tests | pass, 76/76 including P14-05 historical-source composition |
| Rust job/scheduler services | pass, 13/13 + 9/9 |
| Workspace Rust tests / Clippy | pass / pass with `-D warnings` |
| Actual PostgreSQL apply/reapply | pass, 2/2 |
| Actual SQL smoke | pass, 20/20 per run, 2 runs |
| Gated rollback retaining v5 / later-version refusal | pass / pass |
| Exact-core-commit `linux-core`, `windows-worker`, `widget`, `docs` | pass, 4/4 |
| Offline Linux Clippy/tests | pass, Rust 1.96.0, network off, source/registry read-only |
| Secret, Cargo, license, .NET and SBOM checks | pass |
| `pnpm audit` | pass, actual advisory response on first bounded attempt |
| Residual P14 containers / `Hwp.exe` | pass, 0 / 0 |

The closing security report is
`implementation/p01/evidence/security-runs/9750c1226aa945ce98ad692b749f198e/report.json`
(bytes `1294`, SHA-256
`4fd40486d40619492b1a726fd6a35bdadad33f22cc0dd25e509affc51fcd7d70`).
Every check returned exit code zero, `pnpm audit` received an actual advisory response on its first
bounded attempt, the secret scan found zero findings and the SBOM contains 679 components. This
successful current-source audit supersedes the earlier diagnostic-only timeout report; the failed
report remains preserved rather than being rewritten or promoted.

The offline Linux audit used local image
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`.
The final run mounted the current source and host Cargo registry read-only, disabled networking and
used executable tmpfs only for Cargo metadata, target and temporary files. Clippy and all 22 service
tests passed, and no labeled container remained.

## Decision and limits

The unchanged audit did receive an actual successful response, so P14-06 is checked for the local
in-memory scheduler and disposable PostgreSQL behavior proven above. It does not claim production
or multi-host deployment, retry/requeue/takeover, unknown-outcome reconciliation,
cancellation/cleanup or retention/mirror behavior. Those belong to P14-07 through P14-09.

No Hangul process, user document, original ZIP, registry/system setting or production database was
used or changed by P14-06. P14 remains open. P14-07 is recorded separately; continue with P14-08
at reasoning effort `max`.

# P14-05 job state-machine report

- Date: 2026-09-04
- Implementation commit: `3876679`
- Decision: `pass_scoped_p14_05_local_disposable_postgres_and_in_memory_service`
- Review: `STRICT / max`, blocker/major/minor after correction `0/0/0`

## Delivered

- A Rust `job-service` crate with canonical typed job/request/agent/execution/profile/error inputs,
  bounded structural leases and redacted debug forms.
- Exact `queued -> leased -> staged -> executing -> validating -> succeeded` transitions plus
  failure from every active state. Skipped, repeated, backward and terminal mutations fail closed.
- One P14-05 attempt and fencing token, exact agent/execution/attempt/fence binding, monotonic time,
  qualified input/result/receipt references and side-effect-free qualification failures.
- Project reader/editor/owner authorization and tenant isolation. Artifact qualification is also
  bound to the current subject, matching the PostgreSQL artifact ACL behavior.
- PostgreSQL v5 columns, partial queue/active indexes, transition and job-attempt guards, deferred
  job/attempt consistency triggers, fixed-search-path `SECURITY DEFINER` functions, transaction-local
  tenant/subject checks, active-project checks and public privilege revocation.
- A guarded v5 rollback that refuses missing authorization and later schema versions while retaining
  v4; legacy pre-v5 jobs stay unqualified and cannot enter the v5 state machine by inference.
- A digest-pinned PostgreSQL 18.4 contract, strict validator, 30-assertion SQL fixture, real
  apply/reapply/rollback harness and CI integration.

## STRICT review corrections

Review found that the first Rust adapter qualified artifacts only by tenant and kind, while the SQL
boundary also required the acting subject's artifact ACL. Registration now fixes a nonempty unique
reader set, and enqueue/success/failure all require the current subject. A project editor lacking the
artifact ACL is rejected without mutating a validating job.

The SQL transition functions now advance `updated_at`, and v5 guards explicitly reject timestamp
regression and defend immutable job/attempt identity alongside the prerequisite v1 guards. Smoke
assertions prove both the pre-existing identity guard and a project editor without artifact ACL.

One dirty smoke run initially expected the v5 identity error text, but the prerequisite v1 identity
trigger correctly fired first with its existing stable message. The fixture was corrected to the
composed-schema contract and rerun from the start. That failed diagnostic is not authoritative.

## Exact PostgreSQL evidence

The authoritative Git-ignored receipt is
`implementation/p14/evidence/p14-05-postgres-job-state-machine-audit-20260904T064226Z.json`:

- bytes: `2219`
- SHA-256: `f24a382255a9187c903962eb28f7db19d7fb8232adf6225e98d1b9268c9da172`
- exact clean source revision: `3876679eddff4b882142f5a5344fb7e75ede83ed`
- migration contract SHA-256:
  `4b8b55ace13a8aca061cdd65906bc5059c4fc38e5d3e9cda25a78ebe917c4855`
- test harness SHA-256:
  `86881ca8aa49357449fc56e37583530c2b2a4298873b404405b5d818e07ca562`
- validator SHA-256:
  `715b50da08fbe4d6697531799e5b32641fb70efc43625a690fa7e99217381dc4`
- v5 up/down migration SHA-256:
  `4f15cd28510d55fa58a18aef7b8edf8b4606169fd722a0b8d2c63da2cfb4bf9b`,
  `ee57688b62ef4b6c90a89f5eff966f8b4ba1c237bffe494f34fcb596ea516c09`
- smoke fixture SHA-256:
  `9cc3364108701ddb24d5b2ba39eeee28b540e80d2768844583343c674b73c153`
- PostgreSQL: `18.4 (Debian 18.4-1.pgdg12+1)`
- image:
  `postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568`

The clean run applied v1-v5, ran all 30 assertions twice, rejected a duplicate v5 application,
rejected ungated rollback, rejected rollback while a synthetic later version existed, rolled v5
back while retaining v4, reapplied and repeated the smoke. No host port, host volume or container
network was used; the labeled container was removed.

## Validation

| Check | Result |
|---|---|
| Contract validator | pass, exact image/digests, 9 functions, 30 assertions |
| P14 negative/unit tests | pass, 63/63; job-state validator tests 14/14 |
| Rust job service | pass, 13/13 including ACL, transition, terminal and side-effect tests |
| Workspace Rust tests / Clippy | pass / pass with `-D warnings` |
| Actual PostgreSQL apply/reapply | pass, 2/2 |
| Actual SQL smoke | pass, 30/30 per run, 2 runs |
| Gated rollback retaining v4 / later-version refusal | pass / pass |
| Exact-commit `linux-core`, `windows-worker`, `widget`, `docs` | pass |
| Offline Linux target Clippy/tests | pass, Rust 1.96.0, network off, source/registry read-only |
| Secret scan, Cargo deny/audit, pnpm audit/licenses, .NET vulnerable, SBOM | pass |
| Residual P14 containers / `pnpm audit` / `Hwp.exe` | pass, 0 / 0 / 0 |

The closing Git-ignored security report is
`implementation/p01/evidence/security-runs/b5b22d3d1ce54ee29838130b850b8ad2/report.json`, bytes
`1469`, SHA-256 `5f3c67664516a4100cc4f3cd5d10008362f21e0c3a1f41675d51a503bcb8af98`.
It scanned 873 files with zero secret findings; Rust deny/advisory, Node licenses, both .NET
vulnerability checks and a 677-component SBOM passed. The first bounded `pnpm audit` attempt timed
out and cleaned its process tree; the unchanged second attempt succeeded with zero vulnerabilities.

The offline Linux audit used local image
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`.
The initial setup stopped before product compilation because the image-local registry lacked an
already locked crate. The corrected run mounted the host Cargo registry read-only, kept network off,
mounted the exact source read-only and used executable tmpfs only for Cargo home metadata, target and
temporary files; Clippy and all 13 job-service tests passed. No container remained.

## Decision and limits

P14-05 is PASS only for the single-attempt structural state machine, local in-memory adapter and
disposable PostgreSQL scope proven above, and its roadmap row is checked. It does not claim
production PostgreSQL/service wiring or the following later-task behavior:

- P14-06: capability/profile scheduler matching, heartbeat, expiry takeover and late-worker fencing.
- P14-07: request idempotency, retry policy and unknown-outcome reconciliation.
- P14-08: cancellation, orphan artifact handling and temporary cleanup.
- P14-09: retention/legal hold and local mirror synchronization.

No Hangul process, user document, original ZIP, registry/system setting or production database was
used or changed by P14-05. P14 remains open. Continue with P14-06 at reasoning effort `max`.

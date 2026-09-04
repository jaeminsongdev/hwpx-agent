# P14-07 idempotency/reconciliation core checkpoint

- Date: 2026-09-04
- Rust implementation commit: `fbcdcef946db4264195cfaa675570f3453ba8eb0`
- Decision: `rust_core_pass_postgres_and_trusted_oracle_pending`
- Review: `STRICT / max`; scoped blocker/major after correction `0/0`

## Delivered

- A new `idempotency-service` Rust crate with an exact tenant/project/branch/job/key request binding,
  immutable request/manifest/source/effect/transaction digests, expected revision generation and a
  finite record lifetime.
- Atomic claim/replay semantics with one winner under 16 concurrent claimers and side-effect-free
  rejection of request or retry-policy drift.
- A bounded deterministic retry policy: at most 10 attempts, one-day maximum delay and seven-day
  record TTL.
- Exact attempt/fence checks, live-lease and record-TTL bounds, terminal immutability, and
  cross-tenant/cross-subject denial.
- `OutcomeUnknown` freezes a second effect until reconciliation. A committed observation must match
  the expected effect, transaction receipt and previous head revision/generation; a no-effect
  observation must match source identity and the unchanged exact head before a delayed retry.
- A digest-pinned scope contract, strict negative validator, CI docs-lane integration and historical
  P14-06 Cargo lock supersession that still proves the exact P14-06 Git blobs.

## STRICT review corrections

Review added source/head evidence to every retry path, parent validation to direct and reconciled
success, exact job identity at attempt start, and audit retention of retry class. Final review also
closed three boundary defects: project/job/evidence identities are redacted from debug output,
`AutomationNoEffect` cannot enter the direct transient-retry path, and a lease may neither start in
the future nor outlive the idempotency record.

## Validation

| Check | Result |
|---|---|
| Rust unit tests | pass, 10/10 including 16-way claim race and duplicate-effect negatives |
| Target Clippy | pass with `-D warnings` |
| P14 contract/negative tests | pass, 82/82 |
| Historical P14-05/P14-06 validators | pass |
| Workspace format / Clippy / tests | pass / pass / pass |
| Current checkout non-security CI | pass, `linux-core`, `windows-worker`, `widget`, `docs` 4/4 |
| PostgreSQL v7 migration and SQL smoke | not implemented |
| Trusted revision/artifact reconciliation oracle | not implemented |
| Production/multi-host service | not qualified |

## Decision and limits

This checkpoint proves the in-memory state-transition reference only. `NoEffectProof` and committed
observations are exact typed inputs, but this crate does not yet obtain them from an independently
trusted revision/artifact oracle. It also does not atomically compose the P14-06 scheduler lease,
job retry/requeue, revision CAS and a durable PostgreSQL record. Those are mandatory P14-07 work,
so the roadmap checkbox remains open and the scope contract explicitly fixes all three qualification
flags to `false`.

P14-06 also remains formally open until the external NPM advisory API returns a successful audit.
No Hangul process, user document, original ZIP, system setting, remote service or production database
was used by this core checkpoint. Continue with PostgreSQL v7 and trusted reconciliation integration
at reasoning effort `max`.

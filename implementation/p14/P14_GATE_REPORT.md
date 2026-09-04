# P14 Projects, Revisions, Jobs and Artifacts Gate Report

- Generated: 2026-09-04
- Audited implementation source commit: `1d5de34121a8ba7cb9fc651cb90d63d7973db2dc`
- Audit mode: `STRICT / max`
- Overall state: `pass_scoped_current_pc_local_reference_and_disposable_postgres`
- P15 authorization: `authorized_current_pc_local_only`

P14-01~09를 현재 PC 로컬 범위에서 구현하고 재현했다. Metadata schema에서 artifact,
revision/history, job/scheduler, idempotency/reconciliation, cancel/cleanup, retention/purge와
digest-only local mirror까지 하나의 tenant-scoped fail-closed 경계로 연결했다. 실제 DB 증거는
격리된 일회용 PostgreSQL 18.4에 한정하고, Rust 서비스는 명시적으로 in-memory reference다.

## Gate criteria

| Criterion | State | Evidence | Remaining boundary |
|---|---|---|---|
| P14-01 Metadata schema | `pass` | 13 tables, forced tenant RLS, migration/rollback 19 assertions | Production topology and operations are not qualified |
| P14-02 Artifact store | `pass` | encrypted no-overwrite local blob adapter, ACL/quarantine/signed URL, 22 SQL assertions | External object store and key service remain unimplemented |
| P14-03 Revision CAS | `pass` | immutable DAG and expected-head CAS, race/conflict negatives, 20 SQL assertions | Multi-region consensus is not claimed |
| P14-04 History/checkpoints | `pass` | immutable checkpoint/history/branch and subject-bound cursor, 26 SQL assertions | Public history API transport is later integration |
| P14-05 Job state machine | `pass` | bounded legal transition chain and terminal receipt, 30 SQL assertions | Production queue and executor are not qualified |
| P14-06 Worker lease/fencing | `pass` | exact capability/profile selection, bounded lease/heartbeat and late-fence rejection, 20 SQL assertions | Dedicated production worker isolation remains unqualified |
| P14-07 Idempotency/reconciliation | `pass` | exact request binding, unknown-outcome oracle and one-winner concurrency, 28 SQL assertions | Distributed transaction coordinator is not claimed |
| P14-08 Cancel/cleanup | `pass` | cancellation boundaries, reference-safe orphan quarantine and fault recovery, 18 SQL assertions | Production cleanup daemon and storage failures are not qualified |
| P14-09 Retention/local mirror | `pass` | seven classes, hold/tombstone/fenced purge, digest-only mirror CAS/conflicts, 32 SQL assertions | Remote transport, legal suitability and production purge are not qualified |
| Common phase constraints | `pass` | versioned contracts/migrations and negative tests; unexecuted claims remain explicit; source in-place writes 0; failure fixtures and handoff recorded | Other PCs, versions and production remain deferred |

## End-to-end evidence chain

```text
tenant + subject + bounded request
  -> forced-RLS metadata and artifact identity
  -> encrypted no-overwrite local artifact
  -> immutable revision DAG + expected-head CAS
  -> checkpoint/history cursor
  -> job state machine + qualified worker lease/fence
  -> idempotency claim + outcome reconciliation
  -> safe cancellation + reference-protected cleanup
  -> retention class + hold/tombstone/fenced purge receipt
  -> digest-only local mirror + exact remote-head conflict resolution
```

## Validation summary

- Every P14 card has a dedicated report under `implementation/p14/`, a versioned contract or policy,
  typed failure fixtures, migration/rollback coverage where durable state was added, and a scoped
  decision that does not promote in-memory or disposable evidence to production.
- The closing P14-09 exact clean commit passed contract validation with 18 functions, 32 smoke
  assertions, the unchanged 28-assertion P14-07 regression and 9 locked sources. P14 Python tests are
  `132/132`; the Rust retention/sync crate is `15/15` on Windows and Linux.
- Disposable PostgreSQL 18.4 ran the P14-09 smoke and regression three times each, rejected unsafe
  rollback, restored v8 and reapplied v9. The receipt is clean-source and digest-bound.
- Exact implementation commit `1d5de34121a8ba7cb9fc651cb90d63d7973db2dc` passed `linux-core`,
  `windows-worker`, `widget` and `docs` CI lanes. Security passed every check with a successful first
  pnpm advisory response and a 680-component SBOM.
- Offline Linux Rust 1.96.0 used a network-disabled container with read-only source and registry;
  Clippy `-D warnings` and P14-09 tests passed. Residual labeled containers and `Hwp.exe` were `0/0`.
- No user document, original design ZIP, Hangul runtime, registry/system setting, host volume,
  production database or external service was opened or changed by P14.

## Strict review

- Change risk: `high`; later remote control-plane code will trust tenant isolation, immutable
  revisions, artifact references, leases/fences, replay semantics, purge safety and mirror CAS.
- Verdict: `approve_scoped_current_pc_local_reference_and_disposable_postgres`.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Review remediations across the phase include forced RLS and effective privilege checks, immutable
  identities, no-overwrite encrypted storage, subject-bound cursors and replay, head-before-receipt
  CAS, one-winner leases, bounded unknown outcomes, reference-race cleanup, legal-hold/tombstone
  rechecks, unique active push identities and exact mirror acknowledgement binding.
- Component, in-memory and disposable PostgreSQL evidence was not promoted to a production service,
  external object store, remote transport, legal-policy certification, HA or disaster-recovery proof.

## Failure fixtures and residual risks

- Cross-tenant access, malformed and duplicate identifiers, ACL denial, digest/ciphertext tamper,
  stale revision head, invalid job transition, worker mismatch/expiry/stale fence, idempotency drift,
  unknown outcome, cancellation after effect, cleanup reference race, hold overtake, shared reference,
  request alias, tombstoned new reference, mirror head drift, expired push reuse and unsafe rollback
  remain typed negative fixtures.
- All network services are absent. There is no production PostgreSQL adapter/pool, external object
  store, production scheduler/cleanup/purge daemon, remote mirror transport, backup/restore or HA.
- P15 must establish OAuth/OIDC identity, tenant mapping and service-token boundaries before exposing
  any of these operations over MCP. P10 production isolation/security dependencies remain separate.
- Hangul 2022/2024 and other PCs require their own later evidence and are not blockers for the
  explicitly current-PC sequence.

## Phase decision

P14 is complete for current-PC local reference development with disposable PostgreSQL evidence.
P15 may start in the same scope. No production, provider, server/VM, customer distribution,
other-PC or other-version authorization is implied.

## Next exact task

Start `P15-01 Auth/tenant` at reasoning effort `max`. Lock a bounded identity contract for OAuth/OIDC
claims, tenant membership and scoped service tokens; implement fail-closed middleware and deterministic
negative/expiry/replay tests before adding public MCP resources or job submission.

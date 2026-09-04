# HWPX Agent implementation ledger

- Updated: 2026-09-05
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only
- Active phase/task: `P05 / P05-07 actual render acceptance` + `P15 / P15-09 Inspector/staging`
- Active reasoning effort: `max`
- Immediate UI dependency: none live; P05-07 v2 attempts 10 through 16 timed out safely, relaunch only on a new explicit user request when the user can immediately click every visible `모두 허용`

## Objective and non-negotiable boundaries

Implement the P00→P20 product roadmap without weakening Gates. Only exact target evidence can prove
actual Hangul behavior. Disposable synthetic documents are allowed; user documents are never opened
or modified. Computer Use is screenshot-only and any local UI input is performed by the user.
Hangul 2022/2024 and other PCs are deferred until those machines are available. Production/provider,
server/VM, customer distribution and commercial licensing remain disabled until their own Gates.

Raw XML, COM/HAction identifiers, arbitrary paths and unverified routes never enter public/LLM action
inputs. Work is bounded, deterministic, fail closed, no-overwrite and source preserving. Private
runtime evidence and keys stay outside Git. Synthetic/component evidence is not promoted to actual,
save, render, cross-version or production proof.

## Phase ledger

| Phase | State | Authoritative evidence / next dependency |
|---|---|---|
| P00 | `pass_scoped_current_pc_local` | `implementation/p00/P00_GATE_REPORT.md` |
| P01 | `pass_scoped_current_pc_local` | `implementation/p01/P01_GATE_REPORT.md` |
| P02 | `pass_scoped_current_pc_local` | `implementation/p02/P02_GATE_REPORT.md` |
| P03 | `pass_scoped_current_pc_local` | `implementation/p03/P03_GATE_REPORT.md` |
| P04 | `pass_scoped_current_pc_local` | `implementation/p04/P04_GATE_REPORT.md` |
| P05 | `in_progress_current_pc_local` | P05-01~06 pass; P05-07~09 core ready, actual 2020 render requires a later explicit approval session |
| P06 | `blocked_by_P05` | table engine |
| P07 | `blocked_by_P05` | native equation engine |
| P08 | `blocked_by_P05` | images/shapes/drawing/charts |
| P09 | `blocked_by_P05` | fields/forms/notes/references |
| P10 | `in_progress_current_pc_local` | P10-01~04,07,09,10 pass; P10-05/06 actual dependencies pending; P10-08 current-PC core/audit done but dedicated controls unqualified |
| P11 | `blocked_by_P06_P07_P08_P09_P10` | advanced desktop features |
| P12 | `blocked_by_P11` | surgical edit/cross-backend normalization |
| P13 | `blocked_by_P10` | validation/oracle/render |
| P14 | `pass_scoped_current_pc_local_reference_and_disposable_postgres` | `implementation/p14/P14_GATE_REPORT.md` |
| P15 | `in_progress_current_pc_local` | P15-01~08 pass; P15-09 Inspector/staging next |
| P16 | `blocked_by_P15` | ChatGPT Web plugin/widget |
| P17 | `blocked_by_P15` | Codex remote/local companion |
| P18 | `blocked_by_P12_P13_P16_P17` | quality/security/performance/DR |
| P19 | `blocked_by_P18` | production/license/submission |
| P20 | `post_GA` | parity and Rust-native expansion |

## Recent task ledger

| ID | Task | State | Evidence |
|---|---|---|---|
| P-0030~0039 | P04 graph through phase Gate | `pass` | reports under `implementation/p04/`; exact VS-0 commit `6cc11f0` |
| P-0040~0045 | P05-01~06 typed layout and actual readback | `pass` | reports under `implementation/p05/` |
| P-0046~0048 | P05-07~09 layout core | `actual_render_pending` | typed fixtures/harnesses pass; licensed render evidence open |
| P-0049~0056 | P10-01~07 | `mixed_scoped_pass` | reports under `implementation/p10/`; P10-05/06 actual dependency open |
| P-0057 | P10-08 isolation | `core_ready_current_pc_audit_pass_dedicated_unqualified` | dedicated controls open |
| P-0058 | P01 security audit reliability | `pass_current_bounded_retry` | current attempt 1 timeout cleaned; unchanged attempt 2 and all checks pass |
| P-0059~0060 | P10-09~10 supervisor/probe | `pass_scoped_current_pc_local` | reports under `implementation/p10/` |
| P-0061 | P14-01 metadata schema | `pass_scoped_local_disposable_postgres` | commit `200806a`; `implementation/p14/P14-01_REPORT.md` |
| P-0062 | P14-02 artifact service | `pass_scoped_local_disposable_postgres_and_local_blob_adapter` | commit `95f40ad`; `implementation/p14/P14-02_REPORT.md` |
| P-0063 | P14-03 revision CAS | `pass_scoped_local_disposable_postgres_and_in_memory_service` | commit `f225dbc`; `implementation/p14/P14-03_REPORT.md` |
| P-0064 | P14-04 history/checkpoints | `pass_scoped_local_disposable_postgres_and_in_memory_service` | commit `59e26b6`; current security revalidation closed at `3876679`; `implementation/p14/P14-04_REPORT.md` |
| P-0065 | P14-05 job state machine | `pass_scoped_local_disposable_postgres_and_in_memory_service` | commit `3876679`; exact PostgreSQL/CI/Linux/security evidence; `implementation/p14/P14-05_REPORT.md` |
| P-0066 | P14-06 worker lease/fencing | `pass_scoped_local_disposable_postgres_and_in_memory_scheduler` | core commit `205f4ac`; closing security run `9750c1226aa945ce98ad692b749f198e`; `implementation/p14/P14-06_REPORT.md` |
| P-0067 | P14-07 idempotency/reconciliation | `pass_scoped_local_disposable_postgres_and_in_memory_reference` | durable commit `d84a442`; `implementation/p14/P14-07_REPORT.md` |
| P-0068 | P14-08 safe cancellation/cleanup | `pass_scoped_local_disposable_postgres_and_reference_worker` | commit `8d03bb6`; `implementation/p14/P14-08_REPORT.md` |
| P-0069 | P14-09 retention/local mirror | `pass_scoped_local_disposable_postgres_and_in_memory_reference` | commit `1d5de34`; `implementation/p14/P14-09_REPORT.md` |
| P-0070 | P14 phase Gate | `pass_scoped_current_pc_local_reference_and_disposable_postgres` | STRICT/`max`; `implementation/p14/P14_GATE_REPORT.md` |
| P-0071 | P15-01 Auth/tenant | `pass_scoped_current_pc_local_reference_resource_server` | commit `8ac8d74`; 17 Rust + 13 contract tests, exact checkout 5/5, security and offline Linux pass; `implementation/p15/P15-01_REPORT.md` |
| P-0072 | P15-02 public tool schemas | `pass_scoped_current_pc_hancom_2020_contract_only` | commit `c3839df`; 18 input/output descriptors, 17/17 schema tests, exact and independent CI 5/5, security and offline Linux pass; `implementation/p15/P15-02_REPORT.md` |
| P-0073 | P15-03 public MCP handlers | `pass_scoped_current_pc_local_reference_handlers` | commit `9e7ed73`; 18 tools, Rust 16/16 and P15 37/37, exact and independent CI 5/5, security and offline Linux pass; `implementation/p15/P15-03_REPORT.md` |
| P-0074 | P15-04 asynchronous job UX | `pass_scoped_current_pc_local_durable_job_reference` | implementation `f50c724`, closing audit `4c6224f`; Rust async 11/11 + handler 16/16, P15 44/44, exact and independent CI 5/5, security and offline Linux pass; `implementation/p15/P15-04_REPORT.md` |
| P-0075 | P15-05 artifact delivery | `pass_scoped_current_pc_local_artifact_delivery_reference` | commit `dde79ff`; Rust artifact 13/13 + async 11/11 + handler 16/16, P15 51/51, exact and independent CI 5/5, security and offline Linux pass; `implementation/p15/P15-05_REPORT.md` |
| P-0076 | P15-06 public error mapping | `pass_scoped_current_pc_local_public_error_reference` | commit `f36a07e`; 14-code digest-pinned catalog, Rust 45/45 and P15 57/57, final exact independent CI 5/5, security and offline Linux pass; `implementation/p15/P15-06_REPORT.md` |
| P-0077 | P15-07 rate limit/quotas | `pass_scoped_current_pc_hancom_2020_local_quota_reference` | commits `91e84f4` + `e15921a`; Rust 53/53 and P15 65/65, final exact current/independent CI each 5/5, security and offline Linux pass; `implementation/p15/P15-07_REPORT.md` |
| P-0078 | P15-08 bounded telemetry/dashboards | `pass_scoped_current_pc_hancom_2020_local_telemetry_reference` | commit `d492dc8`; Rust 61/61 and P15 73/73, exact current/independent CI each 5/5, security and offline Linux pass; `implementation/p15/P15-08_REPORT.md` |

## Active evidence summary

- P05-07 v2 fixture commit `9096502` independently reads as two linear sections and one break.
  Attempts 10 through 16 timed out at `open_input` with `SECTION_COLUMNS_READBACK_TIMEOUT`; the
  input remained unchanged, no output/PDF was created, owned `Hwp.exe` processes were cleaned and
  residual count is zero. Attempt 10 trace bytes/hash: `1690`/
  `f9644cb119944baaf029ae5b142dee55bd8d68c91892227abccfaa412fc92764`; attempts 11 through 14 each:
  `1366`/`a2c4560bcb5af1f0218ee76e2400e00b8a57cc193b8e81949f3a262bcb0f56d9`; attempt 15:
  `1690`/`f9644cb119944baaf029ae5b142dee55bd8d68c91892227abccfaa412fc92764`; attempt 16:
  `1366`/`a2c4560bcb5af1f0218ee76e2400e00b8a57cc193b8e81949f3a262bcb0f56d9`.
  P05-08~09 render evidence stays open. Relaunch only on a new explicit user request with immediate
  manual approval.
- P10-05 still lacks an approved registered file-path security module. P10-06 actual production COM
  execution and P10-10 routability remain unverified; P10-10 correctly issues zero leases/executions.
- P10-08 passes current-PC development checks, but dedicated production isolation remains unqualified.
- P14-01~05 scoped PASS receipts and limits remain in `implementation/p14/P14-01_REPORT.md` through
  `P14-05_REPORT.md`; each is digest-bound to its exact local disposable PostgreSQL/Rust evidence.
- P14-06 core commit `205f4ac` has a clean digest-bound PostgreSQL 18.4 receipt: 20 assertions
  twice, guarded rollback retaining v5, exact profile/capability selection, bounded heartbeats,
  late-worker/fence rejection and qualified expiry. Closing security run
  `9750c1226aa945ce98ad692b749f198e` passes every check including an actual first-attempt
  `pnpm audit` response; see `implementation/p14/P14-06_REPORT.md`.
- P14-07 durable commit `d84a442` has a clean digest-bound PostgreSQL 18.4 receipt: 28 assertions
  in three transactions, 16-client `1 new + 15 replay`, exactly one commit/retry race winner,
  stale/late/unbound commit rejection, v6-preserving rollback and reapply. P14 tests are 101/101;
  the exact commit passes four non-security lanes. The same-content security run immediately before
  commit passes all checks; two later exact-commit probes preserve external `pnpm audit` timeout as
  diagnostics rather than PASS. See `implementation/p14/P14-07_REPORT.md`.
- P14-08 commit `8d03bb6` has a clean digest-bound PostgreSQL 18.4 receipt: 18 assertions in three
  runs, unchanged P14-07 regression 28 assertions twice, concurrent claim `1 winner + 7 bounded
  misses`, stale-fence/reference-race rejection, before/after-effect crash recovery and exact v7
  rollback/reapply. Rust cleanup/foundation tests, four non-security lanes, independent security and
  network-disabled read-only Linux validation pass. See `implementation/p14/P14-08_REPORT.md`.
- P14-09 commit `1d5de34` has a clean digest-bound PostgreSQL 18.4 receipt: 32 assertions and the
  unchanged P14-07 regression 28 assertions, each in three transactions. Seven retention classes,
  hold/tombstone/fenced purge, shared-reference recheck, immutable receipts, digest-only mirror CAS,
  three conflict paths, fresh-ID expiry recovery and single generation reservation passed. P14 tests
  are 132/132, Rust is 15/15 on Windows/Linux, all four non-security lanes and the exact-commit
  security run pass with SBOM 680. The STRICT phase Gate closes P14 only for current-PC local
  reference development and disposable PostgreSQL; see `implementation/p14/P14_GATE_REPORT.md`.
- P15-01 commit `8ac8d74` implements exact OAuth resource/audience verification, immutable
  issuer/subject-to-tenant mapping, eight typed scopes with role ceilings, bounded key/principal/
  revocation/replay registries and public-user/internal-service separation. Rust 17/17 and P15
  contract tests 13/13 pass on Windows; exact-commit current and independent checkout CI are each
  5/5, both security runs pass, and network-disabled read-only Linux Clippy/tests pass. Production
  IdP/JWKS/hosted transport remains unverified; see `implementation/p15/P15-01_REPORT.md`.
- P15-02 commit `c3839df` freezes exactly 18 public MCP tools with closed Draft 2020-12 input/output
  schemas, exact OAuth scope mirrors, conservative annotations, bounded identifiers and deterministic
  descriptor/schema snapshots. P15-02 tests are 17/17 and all P15 tests 30/30; exact-commit current
  and independent CI are each 5/5, both security runs pass, and network-disabled read-only Linux
  validation passes. Handlers, transport and hosted OpenAI/OAuth integration remain unverified; see
  `implementation/p15/P15-02_REPORT.md`.
- P15-03 commit `9e7ed73` implements the shared fail-closed handler sequence: public-user auth,
  duplicate-key-free JSON, exact input schema, tenant/project policy, one service dispatch, output
  schema and request/resource correlation. Rust handler tests are 16/16 and all P15 tests 37/37;
  current and independent exact-commit CI are each 5/5, both security runs pass, and the
  network-disabled read-only Linux run passes. Transport, real service wiring and async job UX remain
  unverified; see `implementation/p15/P15-03_REPORT.md`.
- P15-04 implementation commit `f50c724` and closing audit commit `4c6224f` bind six long-running
  calls to deterministic durable job IDs, ordered bounded `_meta` events, safe cancellation and one
  immutable terminal receipt. Rust async 11/11 plus handler 16/16 and P15 Python 44/44 pass; current
  and independent exact-commit CI are each 5/5, both security runs and network-disabled read-only
  Linux validation pass. This qualifies only the current-PC local append-only journal reference;
  production queue/database/transport and artifact byte delivery remain unverified. See
  `implementation/p15/P15-04_REPORT.md`.
- P15-05 commit `dde79ff` connects frozen `artifact_get` to metadata, client-only signed preview and
  opaque attachment resource-link results. Tenant/project/artifact binding generation, P14 subject
  ACL/state/digest rechecks, 30~900 second expiry and strict bounded single ranges fail closed.
  Artifact Rust 13/13, async 11/11, handler 16/16 and P15 Python 51/51 pass; current and independent
  exact-commit CI are each 5/5, both security runs and network-disabled read-only Linux validation
  pass. This qualifies only the current-PC local delivery reference; production HTTP/object storage,
  streaming, hosted attachment resolution and key custody remain unverified. See
  `implementation/p15/P15-05_REPORT.md`.
- P15-06 commit `f36a07e` freezes a digest-pinned 14-code public error catalog and exhaustively maps
  Auth, Policy, Gateway, Async-job and Artifact-delivery failures into `hwpx-agent.error/v2`.
  Authentication remains before parse, untrusted request IDs are not echoed before validation, and
  raw errors, credentials, paths, identities and backend payloads are excluded from public and Debug
  output. Rust 45/45, P15 Python 57/57, final exact independent CI 5/5, security and network-disabled
  read-only Linux validation pass. This qualifies only the current-PC local public error reference;
  production HTTP/hosted transport/telemetry remain unverified. See
  `implementation/p15/P15-06_REPORT.md`.
- P15-07 foundational commit `91e84f4` and checkout-independence repair `e15921a` implement atomic
  tenant/user/capability/job-class token buckets, bounded retry guidance, six-tool durable replay
  without recharge, payload-conflict rejection, finite state and clock-regression fail-closed
  behavior. Quota Rust 8/8 plus predecessor Rust 45/45 and P15 Python 65/65 pass; exact-commit main
  and independent CI are each 5/5, both security runs and network-disabled read-only Linux validation
  pass. This qualifies only the current-PC Hangul 2020 local quota reference; distributed accounting,
  production traffic and telemetry remain unverified. See `implementation/p15/P15-07_REPORT.md`.
- P15-08 commit `d492dc8` adds one bounded 2,048-trace collector around the public handler, six-stage
  complete traces, process-salted request/job/execution/revision/evidence and capability correlation,
  closed tool/job/backend/validation SLIs and deterministic dashboards. Telemetry Rust 8/8 plus 53
  predecessor tests and P15 Python 73/73 pass; exact-commit main and independent CI are each 5/5,
  both security runs and network-disabled read-only Linux validation pass. This qualifies only the
  current-PC Hangul 2020 local telemetry reference; hosted exporters, production SLOs and staging
  HTTPS remain unverified. See `implementation/p15/P15-08_REPORT.md`.
- Exact commit `f225dbc` passed repository security validation; `pnpm audit` timed out once with
  cleanup and succeeded on attempt 2, all other checks passed, and the SBOM contains 675 components.
- A detached exact-commit worktree passed all four non-security lanes after the four digest-pinned,
  Git-ignored current-PC runtime evidence files were hydrated, then was removed. The older verified
  P14-02 clone `D:\개발\hwpx-agent-clean-audit-95f40ad` still requires user-local removal because the
  earlier host command policy rejected its cleanup.

## Validation policy

Every implementation task gets target tests plus format/Clippy, relevant regressions, current checkout
FULL, exact-commit clean clone FULL, offline network-disabled Linux core where applicable, security
checks, strict self-review and an authoritative report. A phase closes only after its separate
STRICT/`max` Gate audit updates the roadmap, status and this ledger.

## Exact next actions

1. Non-UI: implement P15-09 Inspector/staging with a loopback-only authenticated HTTPS Streamable
   HTTP endpoint, strict MCP Inspector discovery and all 18 tool calls while preserving the P15-01
   through P15-08 boundaries. Keep public deployment and ChatGPT connection unverified.
2. UI-dependent: on a new explicit user request, rerun P05-07 once and require
   save/reopen/PDF/render evidence before P05-08, P05-09 and the P05 Gate.
3. Keep P10-05/06 and P10-08 production claims open until their external controls exist.

Continue these actions at reasoning effort `max`.

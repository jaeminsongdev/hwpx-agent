# HWPX Agent implementation ledger

- Updated: 2026-09-04
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only
- Active phase/task: `P05 / P05-07 actual render acceptance` + `P14 / P14-02 artifact service`
- Active reasoning effort: `max`
- Immediate UI dependency: none live; P05-07 v2 attempt 06 timed out safely, relaunch only on a new explicit user request when the user can immediately click every visible `접근 허용`

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
| P05 | `in_progress_current_pc_local` | P05-01~06 pass; P05-07~09 core ready, actual 2020 render queue active |
| P06 | `blocked_by_P05` | table engine |
| P07 | `blocked_by_P05` | native equation engine |
| P08 | `blocked_by_P05` | images/shapes/drawing/charts |
| P09 | `blocked_by_P05` | fields/forms/notes/references |
| P10 | `in_progress_current_pc_local` | P10-01~04,07,09,10 pass; P10-05/06 actual dependencies pending; P10-08 current-PC core/audit done but dedicated controls unqualified |
| P11 | `blocked_by_P06_P07_P08_P09_P10` | advanced desktop features |
| P12 | `blocked_by_P11` | surgical edit/cross-backend normalization |
| P13 | `blocked_by_P10` | validation/oracle/render |
| P14 | `in_progress` | P14-01 pass; P14-02 artifact service is the next independent non-UI task |
| P15 | `blocked_by_P14` | remote MCP control plane |
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
| P-0058 | P01 security audit reliability | `harness_pass_online_pnpm_audit_unverified` | bounded 60s×3 cleanup; other checks pass |
| P-0059~0060 | P10-09~10 supervisor/probe | `pass_scoped_current_pc_local` | reports under `implementation/p10/` |
| P-0061 | P14-01 metadata schema | `pass_scoped_local_disposable_postgres` | commit `200806a`; `implementation/p14/P14-01_REPORT.md` |

## Active evidence summary

- P05-07 v2 fixture commit `9096502` independently reads as two linear sections and one break.
  Attempt 06 timed out at `open_input`; the input remained unchanged, no output/PDF was created, its
  owned `Hwp.exe` was cleaned and residual count is zero. Trace bytes `1366`, SHA-256
  `a2c4560bcb5af1f0218ee76e2400e00b8a57cc193b8e81949f3a262bcb0f56d9`. P05-08~09 render evidence
  also stays open. Relaunch only on a new explicit user request with immediate manual approval.
- P10-05 still lacks an approved registered file-path security module. P10-06 actual production COM
  execution and P10-10 routability remain unverified; P10-10 correctly issues zero leases/executions.
- P10-08 passes current-PC development checks, but dedicated production isolation remains unqualified.
- P14-01 exact clean-commit PostgreSQL receipt is digest-bound in
  `implementation/p14/P14-01_REPORT.md`; it proves only local disposable migration/rollback behavior.
- Repository security revalidation again timed out only at external `pnpm audit` 3/3 with cleanup
  3/3. Secret, Rust, license, .NET and SBOM checks pass; the online audit remains `unverified`.

## Validation policy

Every implementation task gets target tests plus format/Clippy, relevant regressions, current checkout
FULL, exact-commit clean clone FULL, offline network-disabled Linux core where applicable, security
checks, strict self-review and an authoritative report. A phase closes only after its separate
STRICT/`max` Gate audit updates the roadmap, status and this ledger.

## Exact next actions

1. Non-UI: implement P14-02 artifact service from `implementation/p14/P14-01_RUNBOOK.md`, including
   content-addressed storage, encryption/ACL/quarantine/signed-URL policy and cross-tenant denial.
2. UI-dependent: on a new explicit user request, rerun P05-07 once and require
   save/reopen/PDF/render evidence before P05-08, P05-09 and the P05 Gate.
3. Keep P10-05/06 and P10-08 production claims open until their external controls exist.

Continue all three at reasoning effort `max`.

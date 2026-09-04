# HWPX Agent implementation ledger

- Updated: 2026-09-04
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only
- Active phase/task: `P05 / P05-07 actual render acceptance` + `P10 / P10-09 timeout/recycle`
- Active reasoning effort: `max`
- Immediate UI dependency: none live; P05-07 v2 attempt 04 timed out safely, relaunch only when the user can immediately click the visible `접근 허용`

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
| P10 | `in_progress_current_pc_local` | P10-01~04,07 pass; P10-05/06 actual dependencies pending; P10-08 current-PC core/audit done but dedicated controls unqualified; P10-09 next |
| P11 | `blocked_by_P06_P07_P08_P09_P10` | advanced desktop features |
| P12 | `blocked_by_P11` | surgical edit/cross-backend normalization |
| P13 | `blocked_by_P10` | validation/oracle/render |
| P14 | `blocked_by_P04` | durable projects/revisions/jobs/artifacts |
| P15 | `blocked_by_P14` | remote MCP control plane |
| P16 | `blocked_by_P15` | ChatGPT Web plugin/widget |
| P17 | `blocked_by_P15` | Codex remote/local companion |
| P18 | `blocked_by_P12_P13_P16_P17` | quality/security/performance/DR |
| P19 | `blocked_by_P18` | production/license/submission |
| P20 | `post_GA` | parity and Rust-native expansion |

## Recent task ledger

| ID | Task | State | Evidence |
|---|---|---|---|
| P-0030~0037 | P04-01~08 graph/unit/selector/plan/router/transaction/diff/idempotency | `pass` | task reports under `implementation/p04/` |
| P-0038 | P04-09 VS-0 core CLI | `pass` | exact commit `6cc11f0`, actual 2020 run 6, current/clean FULL 5/5, Linux offline pass |
| P-0039 | P04 phase Gate | `pass` | STRICT/max, findings 0/0/0, P05 authorized in current scope |
| P-0040 | P05-01 Text flow reader/writer | `pass` | commit `08de88a`, text-flow 12/12, package 63/63, current/clean FULL 5/5, Linux offline |
| P-0041 | P05-02 Character styles | `pass` | commit `a810aa7`, style 11/11, package 74/74, current/clean FULL 5/5, Linux offline |
| P-0042 | P05-03 Paragraph styles | `pass` | commit `ec76232`, paragraph 12/12, package 86/86, current/clean FULL 5/5, Linux offline |
| P-0043 | P05-04 Tabs | `pass` | commits `1a8723c` + `5cb4fe7`; tab 13/13, package 101/101, exact 2020 save/reopen semantic pass |
| P-0044 | P05-05 Lists and numbering | `pass` | commits `4afd8c0` + `9597db2`; exact 2020 canonical save/reopen semantic pass; current/clean 5/5, offline Linux |
| P-0045 | P05-06 Page setup | `pass` | exact 2020 save/reopen + independent semantic page-setup readback; report `implementation/p05/P05-06_REPORT.md` |
| P-0046 | P05-07 Sections and columns | `actual_render_pending` | commits `cf01d27` + `dfd60e3`; core/fixture/current-clean-Linux pass |
| P-0047 | P05-08 Header/footer/page number | `actual_render_pending` | commits `a6bcd35` + `6a46fbc`; 16 core + 2 fixture tests, current/clean FULL 5/5, offline Linux pass |
| P-0048 | P05-09 VS-1 layout | `actual_render_pending` | commits `bd7428c` + `32d9810`; typed layout slice, exact target fixture and bounded Hangul/PDF harness ready |
| P-0049 | P10-01 Windows bridge protocol | `pass` | commit `9e44190`; Rust/C# generated SDK, compatibility 7/7, current/clean FULL 5/5, offline Linux pass |
| P-0050 | P10-02 Windows Agent | `pass` | commit `731f32a`; Agent E2E 11/11, current/clean FULL 5/5, STRICT findings 0/0/0 |
| P-0051 | P10-03 STA worker | `pass` | commit `2628174`; STA/pipe smoke 6/6, x64+x86, current/clean FULL 5/5, STRICT findings 0/0/0 |
| P-0052 | P10-04 HwpObject lifecycle | `pass` | commits `c10f97c` + `3281693` + `c06d12c`; actual attempt 09 plus x64+x86 cancellation/abrupt-exit lifecycle 10/10 |
| P-0053 | P10-05 Security module | `core_ready_actual_module_pending` | commit `b830f74`; Agent 12/12, Worker 10/10, static 29/29, current/clean FULL 5/5, x86 pass; registered module count 0 |
| P-0054 | P10-06 Signed binding executor | `builder_pass_actual_execution_pending` | commits `3281693` + `2f92654`; executor 14/14 x64+x86, actual signed bundle built/verified, actual COM execution pending P10-05 |
| P-0055 | P10-06 trusted offline bundle builder | `pass_current_pc_local_builder` | commit `2f92654`; builder 11/11, static 41/41, actual bundle + independent redacted receipt, current/clean FULL 5/5 |
| P-0056 | P10-07 Event/modal watchdog | `pass_scoped_current_pc_local` | commits `b0f3b6f` + `b4c7a54`; actual events 6, unknown modal fail-closed, smoke 13/13, static 23/23, clean FULL 5/5 |
| P-0057 | P10-08 worker isolation | `core_ready_current_pc_audit_pass_dedicated_unqualified` | mandatory machine-bound pre-lease/post-job guard; Agent 18/18, static 24/24, policy negatives 8/8; actual Session 1/workspace/process audit pass, OS outbound deny and dedicated controls false |
| P-0058 | P01 security audit runner reliability | `harness_pass_actual_registry_audit_unverified_timeout` | 60s x 3 fail-closed retry, process-tree cleanup, immutable per-run report/SBOM; unit 8/8; actual audit timed out 3/3 while all other checks passed |

## Active evidence summary

P05-01~06 are closed by their reports. P05-06 retry 09 proved actual licensed Hangul 2020
open/read/save/reopen/read/quit, unchanged source, equal text digest, a 19-event terminal trace and
zero residual processes. P05-07 retry 10 exposed that both fixture spine rows were `linear=no` and
Hangul read only section one. Commit `9096502` changes both to `linear=yes`, adds self-inspection and
four builder tests. The v2 fixture independently inspects as two sections and one break, but its
user-approved save/reopen/PDF acceptance has not run. Attempt 04 timed out at `open_input`; it left
the input digest unchanged, created no output/PDF, cleaned its one owned `Hwp.exe`, and left zero
residual processes. P05-08~09 actual render evidence is also open.

P10-01~04 are closed by their reports. P10-05 core commit `b830f74` has Agent/Worker lease, path and
allowed/denied coverage, but Registry32 still reports zero registered security modules; no module was
downloaded, installed or registered. P10-06 commits `3281693` and `2f92654` provide the signed typed
executor and independently verified real two-binding bundle, while production COM execution remains
pending P10-05.

P10-07 commit `b0f3b6f` adds the exact installed 16-DispId event connection, bounded redacted journal,
exact-process modal probe, metadata-only `BitBlt` capture, fail-closed policy and cleanup-only dispatch.
A disposable blank document delivered six actual events; the actual 683x196 access modal was detected
as unknown with no auto-response/raw text/pixel persistence, followed by zero residual processes.
Smoke passed 13/13, static checks 23/23 and the complete Windows lane passed. Evidence and strict
scope are recorded in `implementation/p10/P10-07_CORE_REPORT.md`.

P10-08 now requires an exact policy pin and live attestation before any lease RPC, serializes the
Agent to one active job, and audits the same identity/session/desktop/profile/temp plus an empty
marked workspace and zero `Hwp.exe` after execution. Agent smoke passes 18/18, policy negative tests
8/8 and static checks 24/24. The actual current-PC audit passed only for local development; it also
recorded that OS default outbound deny, dedicated identity/profile/window station, clipboard
isolation and profile/recovery/printer residue audits are not qualified. The roadmap P10-08 hard
gate therefore remains open while P10-09 implementation proceeds.

The exact `aee2818` clean clone passed the first four lanes, but two security runs failed only at the
npm audit endpoint. The runner now bounds that call to 60 seconds x 3, retries only safely cleaned
transient failures, records every attempt, and publishes each report/SBOM to a unique no-overwrite
run directory. Its actual validation still timed out 3/3, so exact-commit clean FULL and current npm
dependency-audit evidence remain unverified rather than promoted from the other passing checks.

## Validation policy

Every implementation task gets target tests plus format/Clippy, relevant regressions, current checkout
FULL, exact-commit clean clone FULL, offline network-disabled Linux core where applicable, security
checks, strict self-review and an authoritative report. A phase closes only after its separate
STRICT/`max` Gate audit updates the roadmap, status and this ledger.

## Exact next action

When the user is immediately available, rerun P05-07, then P05-08 and P05-09 serially with required
save/reopen/PDF/render evidence before the strict P05 Gate. In the non-UI lane, implement P10-09
timeout/recycle and unknown-outcome reconciliation. Keep P10-05 actual module registration and dependent P10-06
production execution unverified until an approved module exists. Continue at reasoning effort `max`.

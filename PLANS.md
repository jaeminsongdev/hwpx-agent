# HWPX Agent implementation ledger

- Updated: 2026-09-03
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only
- Active phase/task: `P05 / P05-06 actual acceptance` + `P10 / P10-04 HwpObject lifecycle`
- Active reasoning effort: `max`
- Immediate UI dependency: none live; launch the next P05 retry only when the user can immediately click every visible `접근 허용`

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
| P05 | `in_progress_current_pc_local` | P05-01~05 pass; P05-06~09 core ready, actual 2020 queue active |
| P06 | `blocked_by_P05` | table engine |
| P07 | `blocked_by_P05` | native equation engine |
| P08 | `blocked_by_P05` | images/shapes/drawing/charts |
| P09 | `blocked_by_P05` | fields/forms/notes/references |
| P10 | `in_progress_current_pc_local` | P10-01~03 pass; P10-04 HwpObject lifecycle next |
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
| P-0045 | P05-06 Page setup | `actual_pending` | commits `35b6d2c` + `453e1d4`; core/fixture/current-clean-Linux pass |
| P-0046 | P05-07 Sections and columns | `actual_render_pending` | commits `cf01d27` + `dfd60e3`; core/fixture/current-clean-Linux pass |
| P-0047 | P05-08 Header/footer/page number | `actual_render_pending` | commits `a6bcd35` + `6a46fbc`; 16 core + 2 fixture tests, current/clean FULL 5/5, offline Linux pass |
| P-0048 | P05-09 VS-1 layout | `actual_render_pending` | commits `bd7428c` + `32d9810`; typed layout slice, exact target fixture and bounded Hangul/PDF harness ready |
| P-0049 | P10-01 Windows bridge protocol | `pass` | commit `9e44190`; Rust/C# generated SDK, compatibility 7/7, current/clean FULL 5/5, offline Linux pass |
| P-0050 | P10-02 Windows Agent | `pass` | commit `731f32a`; Agent E2E 11/11, current/clean FULL 5/5, STRICT findings 0/0/0 |
| P-0051 | P10-03 STA worker | `pass` | commit `2628174`; STA/pipe smoke 6/6, x64+x86, current/clean FULL 5/5, STRICT findings 0/0/0 |

## Active evidence summary

P05-01~05 are closed by their task reports. P05-06~09 core/static harnesses, deterministic disposable
fixtures, current/exact-clean FULL checks and offline Linux checks passed, but P05-06 actual
save/reopen and P05-07~09 actual save/render evidence remain open. `retry-04` through `retry-06`
timed out fail-closed while awaiting the first access approval: no output, source unchanged and zero
residual Hangul processes. Commit `d3ccd05` fixed the Windows PowerShell 5.1 progress parser;
`retry-06` then recorded a valid three-event journal ending at `open_input/running`. The next retry
must reuse the fixed source SHA-256
`c76816ca35352168955f47cb656ad2cb1ff049192fc10ce46db1465f7f43f0bc`; only a terminal pass plus
independent semantic readback may close P05-06.

P10-01 through P10-03 are closed by their reports under `implementation/p10/`. At exact commit
`2628174`, the private one-job named pipe, bounded protocol command loop, separate worker host and real
Windows STA message pump passed 6/6 smoke suites under both x64 and this PC's x86 .NET runtime, plus
current and exact-clean FULL 5/5. `CurrentUserOnly` is not claimed as hostile same-user isolation.
`HwpObject`, actual Hangul execution, file-path approval, modal handling and process recycling remain
unverified; P10-04 is next.

## Validation policy

Every implementation task gets target tests plus format/Clippy, relevant regressions, current checkout
FULL, exact-commit clean clone FULL, offline network-disabled Linux core where applicable, security
checks, strict self-review and an authoritative report. A phase closes only after its separate
STRICT/`max` Gate audit updates the roadmap, status and this ledger.

## Exact next action

When the user is immediately available, launch one P05-06 retry and verify source immutability,
terminal trace closure and independent product semantic readback before writing its task report. Then
run P05-07, P05-08 and P05-09 serially with required PDF/render evidence before the strict P05 Gate.
In parallel, start P10-04 from `implementation/p10/P10-03_REPORT.md`: implement the exact current
Hangul 2020 x86 `HancomSession` lifecycle inside the STA worker and prove owned-process cleanup across
normal and failure paths at reasoning effort `max`.

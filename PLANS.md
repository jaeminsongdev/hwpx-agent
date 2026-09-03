# HWPX Agent implementation ledger

- Updated: 2026-09-04
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only
- Active phase/task: `P05 / P05-07 actual render acceptance` + `P10 / P10-07 event/modal watchdog core`
- Active reasoning effort: `max`
- Immediate UI dependency: none live; P05-07 retry 01 timed out safely, relaunch only when the user can immediately click every visible `접근 허용`

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
| P10 | `in_progress_current_pc_local` | P10-01~04 pass; P10-05 actual module pending; P10-06 builder pass/actual execution pending; P10-07 next |
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

## Active evidence summary

P05-01~06 are closed by their task reports. P05-06 retry 09 passed actual licensed Hangul 2020
open/read/save/reopen/read/quit with unchanged source, equal input/output text digest, 19-event
terminal trace, zero cleanup errors and zero residual processes. Independent product inspection
confirmed the custom landscape dimensions, margins-derived body area and text digest. Failed retry
08 remains diagnostic-only. P05-07 retry 01 timed out at `open_input` without user approval; input
was unchanged, output/PDF absent, one owned process cleaned and zero `Hwp.exe` remained. P05-07~09
core/static harnesses are ready, but their required actual save/render evidence remains open.

P10-01 through P10-04 are closed by their reports under `implementation/p10/`. P10-04 actual attempt
09 passed the exact licensed Hangul 2020 x86 three-cycle normal lifecycle with unchanged
source/staging, terminal exact-safe output and zero residual processes. Commit `c06d12c` added the
missing server-cancellation and abrupt owned-process-exit regressions; lifecycle smoke now passes
10/10 under x64 and x86. Earlier timed-out attempts remain diagnostics. The private named pipe and
`CurrentUserOnly` are not claimed as hostile same-user isolation; modal handling and process
supervision remain later tasks.

P10-05 core commit `b830f74` connects the Agent sandbox to the production Worker through an
immutable, single-use execution/fencing/profile/policy/artifact/module-bound security lease. The
public handle remains path-free; a fixed private read-only HWPX copy is digest-checked and guarded.
Agent smoke passed 12/12, Worker allowed/denied smoke passed 10/10 under x64 and x86, static checks
passed 29/29, and current plus exact-clean FULL passed 5/5. The current-PC Registry32 probe found the
key but zero registered security modules; therefore actual module registration is not verified,
P10-05 remains core-only and no module was downloaded, installed or registered.

P10-06 commits `3281693` and `2f92654` add an Ed25519-signed exact-target bundle, semantic-only public plan,
finite typed ParameterSet conversion, preflight-before-COM rejection and single-use Agent bundle/key
leases plus a policy-pinned P02-to-P10 offline builder. Builder tests passed 11/11, static checks
passed 41/41, and a real two-binding bundle was independently reconstructed and verified. Current
and exact-clean FULL passed 5/5. Actual production Agent/Worker COM execution remains pending the
P10-05 registered-module dependency, so P10-06 stays open.

## Validation policy

Every implementation task gets target tests plus format/Clippy, relevant regressions, current checkout
FULL, exact-commit clean clone FULL, offline network-disabled Linux core where applicable, security
checks, strict self-review and an authoritative report. A phase closes only after its separate
STRICT/`max` Gate audit updates the roadmap, status and this ledger.

## Exact next action

When the user is immediately available, rerun P05-07, then P05-08 and P05-09 serially with required
save/reopen/PDF/render evidence before the strict P05 Gate. Require source immutability, terminal
trace closure and zero residual Hangul processes for every actual run. In the non-UI lane, implement
P10-07 event/modal watchdog core. Keep P10-05 actual module registration and the dependent P10-06
production execution unverified until an approved module exists. Continue at reasoning effort `max`.

# HWPX Agent implementation ledger

- Updated: 2026-09-03
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only
- Active phase/task: `P05 / P05-05~08 exact Hangul 2020 acceptance queue`
- Active reasoning effort: `max`
- Blocker: none

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
| P05 | `in_progress_current_pc_local` | P05-01~04 pass; P05-05~08 core ready, actual 2020 queue active |
| P06 | `blocked_by_P05` | table engine |
| P07 | `blocked_by_P05` | native equation engine |
| P08 | `blocked_by_P05` | images/shapes/drawing/charts |
| P09 | `blocked_by_P05` | fields/forms/notes/references |
| P10 | `ready_by_P03_deferred_sequence` | Windows Hangul automation bridge |
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
| P-0044 | P05-05 Lists and numbering | `actual_in_progress` | commit `4afd8c0`; core/fixture/current-clean-Linux pass; exact 2020 open/save/reopen active |
| P-0045 | P05-06 Page setup | `actual_pending` | commits `35b6d2c` + `453e1d4`; core/fixture/current-clean-Linux pass |
| P-0046 | P05-07 Sections and columns | `actual_render_pending` | commits `cf01d27` + `dfd60e3`; core/fixture/current-clean-Linux pass |
| P-0047 | P05-08 Header/footer/page number | `actual_render_pending` | commits `a6bcd35` + `6a46fbc`; 16 core + 2 fixture tests, current/clean FULL 5/5, offline Linux pass |

## P05 active acceptance queue

P05-05~08 have bounded typed contracts, deterministic lower/readback, negative corpora and disposable
target fixtures. The latest exact commit `6a46fbc` passed current and clean-clone FULL 5/5 plus offline
network-disabled Linux `hwpx-package --all-targets` tests/Clippy with source and Cargo registry
read-only. The authoritative task state remains open until the serialized exact Hangul 2020
open/save/reopen runs finish and P05-07/P05-08 render evidence is captured. No synthetic or static
result is promoted to actual behavior.

## P05-04 closure evidence

P05-04 added `hwpx-agent.tab-definition/1` with bounded automatic/custom tab definitions, direct and
HwpUnitChar compatibility preservation, semantic dedup, complete-map typed-reference rewrite and
deterministic lower/readback receipts. Its 13 tests, fixed 128-case corpus
`f1f8d682...dd0a92`, package 101/101, Windows/Linux, current/clean FULL 5/5 and security all passed at
exact correction commit `5cb4fe7`. A disposable exact Hangul 2020 save/reopen preserved text and tab
semantics, left the source unchanged and exited cleanly. Visual placement, arbitrary documents and
other releases remain unverified.

## Validation policy

Every implementation task gets target tests plus format/Clippy, relevant regressions, current checkout
FULL, exact-commit clean clone FULL, offline network-disabled Linux core where applicable, security
checks, strict self-review and an authoritative report. A phase closes only after its separate
STRICT/`max` Gate audit updates the roadmap, status and this ledger.

## Exact next action

Finish the active disposable P05-05 exact Hangul 2020 open/save/reopen run, verify source immutability,
trace closure and product semantic readback, then write its task report. Run P05-06, P05-07 and P05-08
actual fixtures serially; add required render evidence for P05-07/P05-08 before task closure. Continue
at reasoning effort `max`.

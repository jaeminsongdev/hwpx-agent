# HWPX Agent implementation ledger

- Updated: 2026-09-03
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only
- Active phase/task: `P05 / P05-06~09 exact Hangul 2020 acceptance queue`
- Active reasoning effort: `max`
- Blocker: P05-06 actual retry needs the user's visible `접근 허용` click; retry-04 timed out fail-closed

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
| P-0044 | P05-05 Lists and numbering | `pass` | commits `4afd8c0` + `9597db2`; exact 2020 canonical save/reopen semantic pass; current/clean 5/5, offline Linux |
| P-0045 | P05-06 Page setup | `actual_pending` | commits `35b6d2c` + `453e1d4`; core/fixture/current-clean-Linux pass |
| P-0046 | P05-07 Sections and columns | `actual_render_pending` | commits `cf01d27` + `dfd60e3`; core/fixture/current-clean-Linux pass |
| P-0047 | P05-08 Header/footer/page number | `actual_render_pending` | commits `a6bcd35` + `6a46fbc`; 16 core + 2 fixture tests, current/clean FULL 5/5, offline Linux pass |
| P-0048 | P05-09 VS-1 layout | `actual_render_pending` | commits `bd7428c` + `32d9810`; typed layout slice, exact target fixture and bounded Hangul/PDF harness ready |

## P05 active acceptance queue

P05-05~09 have bounded typed contracts, deterministic lower/readback, negative corpora and disposable
target fixtures. Commit `49ba92a` adds a 30--900 second watchdog, privacy-safe append-only progress
journal, exact-process cleanup checks and version-specific wrappers for the current Hangul 2020
actual runs. Commit `2d2c884` extends the P05-07/P05-08 wrappers with optional bounded
`IXHwpDocument.SaveAs/PDF` evidence: no-overwrite, same-fixture boundary, regular-file/reparse,
32-MiB, `%PDF-`, length, SHA-256 and exact method checks run in both worker and watchdog. The six
PowerShell suites passed 146/146 in the current and exact clean checkouts; both also passed FULL
bootstrap 5/5, and the clean checkout had zero tracked changes. Commit `62dbdb5` adds the independent
fail-closed PDF verifier and locked P05-07/P05-08 render expectations. It binds the PDF, expectation,
Python/verifier and `pdftoppm` identities; checks encryption, page count, rotation, geometry and
fixture tokens; renders every page at 144 DPI; completely decodes bounded PNGs; and still requires
human/agent visual review. Its 16/16 tests, Python compile and current/exact-commit-clean FULL 5/5
passed. A read-only integration run against the existing disposable P00 actual PDF also passed exact
hash, A4 geometry, three text tokens, PNG identity and visual review. That generic pipeline proof is
not P05-07/P05-08 actual evidence; their own PDFs remain required before either render Gate is
promoted.

The latest core commit `6a46fbc` additionally passed offline network-disabled Linux
`hwpx-package --all-targets` tests/Clippy with source and Cargo registry read-only. The authoritative
P05-05 task is now closed at correction commit `9597db2`. Its canonical disposable fixture passed
exact Hangul 2020 open/save/reopen, product semantic readback and source/process closure. The runtime
calibration history remains recorded: approval timeouts produced no output, and later probes exposed
the exact text oracle, early-trace/success-exit issues and Hangul's bullet-level/checkable
canonicalization before the final clean pass. Current and exact-commit clean bootstraps passed 5/5,
both copies of all six PowerShell suites passed 153/153, and offline read-only Linux package tests and
Clippy passed. No synthetic, static, timed-out or pre-correction result was promoted to actual proof.
P05-06 actual save/reopen and P05-07/P05-08 actual save/render evidence remain open.

P05-09 core commit `bd7428c` combines the already typed character, paragraph, page, column and text
modules into the bounded `hwpx-agent.hancom-2020-vs1-layout/v1` vertical slice. Its public input admits
only NFC-normalized single-line text, fixed profile choices and finite counts; raw XML, package paths
and automation commands are absent. The deterministic 11-part target is 8,018 bytes with SHA-256
`185b0d685a0c07e6056e2a4b5d8e0f449f8073e35fce5313a16a2908a22db4dc`, five paragraphs, one explicit
column break, 80,220 HWPUNIT body width, two columns, 1,700 HWPUNIT gap, seven character styles,
twenty paragraph styles and visible-text SHA-256
`2d93a6073c0703bdc54ccb4a6f12671604a7cac5207fd20744d264a5f93df33f`. Target tests, complete
workspace tests/Clippy, current and exact-commit-clean FULL 5/5, clean P05 diagnostics and the fixed
Linux image with network disabled plus source/Cargo registry read-only passed. Harness commit
`32d9810` adds the exact P05-09 save/reopen/PDF wrapper and locked one-page 310 x 230 mm render
expectation. The expanded six PowerShell suites pass 163/163 and the PDF verifier passes 16/16. These
are core/static/synthetic results only; P05-09 remains pending exact Hangul save/reopen/render.

P05-06 retry-04 reached exact Hangul 2020 COM creation and a live, enabled, on-screen `접근 허용`
dialog in `open_input`, but no user approval was received during the bounded 900-second window. The
watchdog recorded three valid correlated progress events, preserved the fixed input SHA-256
`c76816ca35352168955f47cb656ad2cb1ff049192fc10ce46db1465f7f43f0bc`, created no output, cleaned its
one owned Hangul process and left zero residual Hangul processes. The terminal state remains
`PAGE_SETUP_READBACK_TIMEOUT`; it is failure evidence, not actual readback proof.

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

When the user has the Hangul window visible and confirms immediate readiness, start P05-06 retry-05.
Have them click the first `접근 허용` prompt immediately and every subsequent prompt before the
bounded timeout. Verify source immutability, trace closure and product semantic readback, then write
its task report. Run P05-07, P05-08 and P05-09 serially with their required PDF/render evidence before
the strict P05 Gate. Continue at reasoning effort `max`.

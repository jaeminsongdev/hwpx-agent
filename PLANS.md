# HWPX Agent implementation ledger

- Updated: 2026-09-07
- Root: `D:\개발\hwpx-agent`
- Objective: complete P00-P20 without weakening evidence Gates.
- Current target: licensed Hangul 2020 `11.0.0.9136` x86 on this PC only.
- Deferred: Hangul 2022/2024 and other-PC compatibility until those environments are available.
- Reasoning: `high` for isolated pure implementation; `max` for source qualification, HWPX/COM,
  preservation, target readback/render, security and phase/final Gates.

## Non-negotiable boundaries

- Preserve user documents, the original design ZIP, private evidence and secrets.
- Use only named disposable fixtures; never edit source artifacts in place.
- Computer Use is screenshot-only. The user performs every Hangul click and access approval.
- Component/synthetic evidence never proves actual Hangul, render, production or full-product PASS.
- Raw XML, COM/HAction identifiers, arbitrary paths and unverified routes stay out of public actions.
- Failed attempts remain failed evidence and are never relabeled.

## Phase snapshot

| Phase | State | Authoritative summary |
|---|---|---|
| P00-P04 | scoped current-PC PASS | reports under `implementation/p00/` to `implementation/p04/` |
| P05 | scoped current-PC PASS | `implementation/p05/P05_GATE_REPORT.md` |
| P06 | in progress | 01-04 current-PC PASS; 05 v2 source and exact target prepared but target Hangul geometry/wrapping/PDF remain; 06 pure core/source tooling qualified |
| P07-P09 | sequentially open | equation, graphics and fields follow P06 dependencies |
| P10 | partial | 01-04,07,09,10 scoped pass; 05/06 actual dependencies and 08 remain |
| P11-P13 | open | depend on P06-P10 |
| P14-P15 | scoped local PASS | disposable PostgreSQL and local MCP/Inspector staging Gates |
| P16 | partial | local source/plan/renderer/host pass; registered app/Hangul evidence open |
| P17 | partial | package/bridge/sync/widget components exist; actual remote/UI closures remain |
| P18-P19 | open | quality/security/DR, production/license/submission and GA Gate |
| P20 | post-GA | parity and Rust-native expansion |

## Active tasks

| ID | Task | Current state and exact next evidence |
|---|---|---|
| P-0052 | P06-04 cell formatting | current-PC PASS: actual source plus v2 product target `264b062c...a48d28a`, Hangul 2020 save/reopen text identity, semantic/style digest identity and PDF visual review pass on attempt04; attempts 01-03 remain timeout diagnostics |
| P-0053 | P06-05 sizing/autofit | pure solver, installed-font metric receipt, HWPX v2 adapter, exact deterministic target `a6785881...8555bc` and source qualification `cfb6628`/v34 pass; actual Hangul geometry, wrapping and signed PDF evidence remain |
| P-0054 | P06-06 FormulaAst | pure core `cc92565`; bounded Hangul-authored source capture `e28220e` and source qualification `d25a174`/v32 pass as tooling only; capture execution, exact HWPX adapter, oracle receipt and row/column differential remain; card is not complete |
| P-0082/0085-0087 | P16 registered app | local bundle and one-tool MCP host pass; actual registered app and Hangul operation remain |
| P-0091 family | P17-06 remote sync | authenticated loopback and durable PostgreSQL checkpoint evidence pass; atomic durable mirror admission and real pull/push remain |
| P-0094 family | P17-07 conflicts | local resolver and graphical component pass; registered host and concurrent Web/Codex evidence remain |
| P-0093 | P17-08 trusted Git UI | local widget/MCP/disposable Git evidence passes; one fresh GUI user confirmation/effect/replay run remains |

## Latest P06-04 evidence

- Actual source attempt04 completed on licensed Hangul 2020 `11.0.0.9136` x86: 4 cells, 8 style
  actions, equal pre-save/reopen text SHA-256, source HWPX and PDF saved, input was a new synthetic
  document, and final Hwp process count was zero.
- Source HWPX SHA-256 is `814c481da946e760b2bc3b90b996863786652001e49f8b2b422e13c3d3e477a4`;
  PDF SHA-256 is `08b0bd6b6c84ef9199c119faa6d71917de88977bb91faccc5f16f82598880fbd`.
- Actual serialization required explicit v2 rules for exact preview text, table/sub-list IDs,
  `subList`-first cell order and inactive nonzero stored margins. Core v1 behavior remains unchanged.
- Product lowering created a distinct target HWPX at SHA-256
  `264b062c8a2477cf4167cef5b9db7d51a83594ed024b572d7ff2ea533a48d28a`; v2 preservation, ID,
  style and content readback inspection pass. The source remained byte-identical.
- `hwpx-package` complete tests, Clippy `-D warnings`, formatting, v1/v2 contract validators and
  their 8 Python tests pass. New forbidden Rust patterns and dependencies are zero.
- Source v33: run `7783a21d553e45eaab55497fea2b3f1c` passed 11/11 at clean commit
  `5adba7d2b1c98f7e2fa87671f321ff6d599dde48`; receipt SHA-256
  `2239e1722f4a7df6c4c1f79cb3fc95a318ae6bdbfa5d5e3368d8e4e65ae773e2`. Qualification commit
  `14f215a` binds 14 implementation/contract/test sources with all runtime/product claims false.
- Product-target attempts 01-03 each waited 600 seconds at `open_input`, then failed with
  `TABLE_CELL_STYLE_READBACK_TIMEOUT`; all kept the target unchanged, emitted no derived HWPX/PDF,
  and cleaned their owned Hwp process. They are not semantic failures and are not PASS.
- Attempt04 passed every bounded phase on the exact target: input open/read, create-new HWPX save,
  close, output reopen/read, PDF export and quit. Input/output visible-text SHA-256 is equal, the
  semantic/style digest is equal before/after the Hangul round trip, the PDF shows all four intended
  style combinations without clipping or overlap, and Hwp residue is zero. Report:
  `implementation/p06/P06-04_TARGET_READBACK_REPORT.md`.

## Latest P06-05 evidence

- Active exact-build contract is `hwpx-agent.table-layout-hwpx.hancom-2020/2`; immutable `/1` is
  hash-bound. V2 adds typed bounded inherited `hp:inMargin` readback and post-lowering identity.
- Exact installed-font receipt SHA-256 is
  `c4755f99ebf1e49010bf26425d61f77c496fa713d86404004348027acfc1d2ab` for the four named target
  strings under 10 pt `함초롬바탕` TTF metrics.
- Verified plan is 70,000 micrometers wide with columns `52990,17010`, rows `13758,4586`, zero
  overflow/underfill and no content deficit. Exact HWPX readback is table `19843 x 5200` HWPUNIT,
  columns `15021,4822`, rows `3900,1300`, and inner margins `510,510,141,141`.
- Four independent create-new builds are byte-identical at target SHA-256
  `a678588188593c250b33205f1660fef6c301280cd5ae30deb4b6a03f185055bc`. Wrong source digest and
  existing-output cases fail before publication. Preview text is current; preserved preview image
  is not visual evidence.
- Implementation commit `84437dd`; source v34 acceptance run `8b080b651ade4e5d85701bd47bd9e6b6`
  passed 11/11 at the exact clean commit. Qualification commit `cfb6628` binds 15 implementation
  sources while P06-05 actual Hangul/PDF, P06, production and product claims remain false.
- `hwpx-package` tests, Clippy `-D warnings`, formatting, P06 Python 45/45, v1/v2 contract tests 8/8,
  contract validators and readback-wrapper static tests 15/15 pass. Actual target Hangul 2020
  save/reopen, geometry, wrapping and PDF visual comparison are still not run.

## Latest P06-06 evidence

- Contract: `protocol/private/p06-table-formula-v1.json`; migration:
  `protocol/migrations/p06-table-formula-v0-to-v1.md`.
- Pure model: bounded ASCII parser, exact decimal AST, arithmetic, A1 cell/range references,
  independent relative/absolute axes, `SUM`/`AVG`/`PRODUCT`, exact grid-bound copy and structural
  transforms, separate unverified cache and bounded number formats.
- Safety: unknown JSON fields, invalid dimensions, deleted owners/endpoints, grid escape, cache
  policy mismatch and over-limit inputs fail closed; Debug redacts formula/cache values.
- Oracle boundary: pure v1 admits only `absent` and `unverified` cache. Only a later adapter that
  verifies an actual target receipt may promote an oracle-qualified result.
- Validation: formula tests 15/15; `domain-ir` 125/125; P06 Python 37/37; full workspace tests pass
  with one explicitly environment-gated PostgreSQL test ignored; workspace Clippy `-D warnings`
  and formatting pass. No dependency added.
- Source v31: run `7fe87b6cf5ea435ca8f037559d371b0e` passed 11/11 at clean commit
  `cc925658d2c08e1a67118fc2a1b426f3c9929651`; receipt SHA-256
  `98ca665071096c1c1e95ad919b0b0acbf632cbc8928ea39c0ab63ce5f7ae6481`.
- Source v32: run `f043ce35eb9a4d68bf1da27ee1c3ef3a` passed 11/11 at clean commit
  `e28220e7f50b0556fc028a1e45d9addfd70619a7`; exact-build worker, watchdog and privacy-safe progress
  are bound. Capture execution, field shape, evaluation, oracle, P06-06/P06 and product remain false.

## Open risks and holds

- R-0002: P16 actual registered-app and Hangul end-to-end evidence absent.
- R-0003: one historical independent worker timeout root cause remains unproven; retries passed.
- R-0005: P17 durable checkpoint exists, but atomic durable mirror role/head admission, persistent
  credential custody, production lifecycle and real pull/push do not.
- R-0006: P17 conflict resolver/widget are component evidence only.
- R-0007: P06-05~09 still require actual Hangul 2020 semantics, save/reopen/PDF/pagination and the
  61-capability target conformance matrix. GDI+ metrics are not Hangul render evidence.
- HOLD-0002: P10-05 path-security registration and P10-06 production COM execution.
- HOLD-0003: P10-08 production isolation and later-version PCs.

## Next actions

1. At `max`, when the user is at the PC, run the exact P06-05 target through the bounded Hangul 2020
   wrapper. Require target input/text digests, save/reopen equality, input immutability, exact
   semantic geometry, wrapping/PDF visual review and zero Hwp residue.
2. At `max`, after zero Hwp residue, execute the bounded P06-06 source capture, inspect its exact
   FORMULA field, then build the target-bound lift/lower adapter; keep cache `unverified` until oracle.
3. Close P06-06 only after row/column move differential, formula/cache semantic readback and licensed
   Hangul 2020 save/reopen evidence; then proceed to P06-07 pagination.
4. At every card/phase closure run target tests, regressions, current and clean-checkout FULL plus
   applicable offline Linux/security/STRICT checks without weakening actual-evidence Gates.

## Context pack and archive pointers

- Read first: this file, `implementation/p06/P06-04_CELL_STYLE_POLICY.md`,
  `implementation/p06/P06-06_FORMULA_AST_POLICY.md`, `implementation/p06/P06-03_REPORT.md`, and
  `implementation/p05/P05_GATE_REPORT.md`.
- P06-04 source tool: `implementation/p06/tools/create-hancom-2020-table-source.ps1`.
- P06-05 metric qualification: commits `af3dbf0`, `42aba1c`, `742b3d2`.
- P17 source qualification: `implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V34.md`; other details
  are under `implementation/p17/`; detailed ledger history through
  P-0085 is recoverable from `fae5bc0:PLANS.md` and later Git history.
- Do not touch user originals, failed evidence, immutable predecessor locks or unrelated processes.

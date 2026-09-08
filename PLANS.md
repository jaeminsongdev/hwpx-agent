# HWPX Agent implementation ledger

- Updated: 2026-09-08
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
| P06 | in progress | 01-06 current-PC PASS; P06-08 pure inspector PASS; P06-07 renderer oracle and P06-09 matrix remain |
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
| P-0053 | P06-05 sizing/autofit | current-PC PASS: pure solver, installed-font receipt and HWPX v2 adapter; failed `Open=false`, zero-guard and 4-micrometer calibration evidence preserved; calibrated target `3dfcf2a1...d9bcb5`, actual Hangul 2020 save/reopen lines `1,3,1,1`, PDF visual oracle, v2 contract and source v36 pass |
| P-0054 | P06-06 FormulaAst | current-PC PASS: pure core, source/adapter, deterministic 2x4 row/column target `6514a69b...320e5`, actual Hangul 2020 attempt04 save/reopen, strict saved-HWPX formula/cache/layout oracle and PDF visual review pass; attempts 01-03 remain failed timeout diagnostics |
| P-0055 | P06-07 pagination | pure component, static current-PC HWPX adapter, exact composite target builder and pre-runtime oracle PASS; first actual target exposed clipped long-cell/boundary calibration failure, corrected target awaits licensed Hangul 2020 access and renderer rerun |
| P-0056 | P06-08 inspect/select | scoped pure-IR PASS at `293053e`: revision/graph/path/ID/fingerprint-bound table and merged-cell selectors, nested/drawing/note indexing, bounded metadata snapshot; Rust 11/11 and contract/tamper 4/4 pass; no HWPX/Hangul selection claim |
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
- Historical builder `/v1` target SHA-256
  `a678588188593c250b33205f1660fef6c301280cd5ae30deb4b6a03f185055bc` reached exact licensed
  Hangul 2020 after the user's access approval, but `Open` returned `false`. No text, save/reopen or
  PDF evidence was produced; input remained unchanged, quit passed and Hwp residue was zero.
- The concrete package defect and leading cause is stale source-derived `hp:linesegarray` data whose
  cached text positions conflict with the changed cell texts. Builder `/v2` requires exactly one
  direct cache per edited source paragraph, deletes its exact outer span, requires zero target
  caches and never guesses values.
- Three independent repaired create-new builds are byte-identical at target SHA-256
  `b2887c929cdeb81fa1f5f3bac086265e19fb92a8bbf063f75e5ab0fbfa5cb299`. Wrong source digest makes
  no output; an existing output remains unchanged; exact source and font receipt remain unchanged.
- Product-target contract `protocol/private/p06-table-layout-target-v1.json`, migration, exact
  failed-attempt diagnostic and ignored-artifact/tamper validator pass. Repair commit is `73576de`.
- Source v35 acceptance run `c8a25b992e9643148c5c8d295ae589b5` passed 11/11 at that exact clean
  commit; receipt SHA-256 is `83cd3f3a42e317e9db1ce51ae18d4f9e0f3f7203018259d84c558d1c9a3df418`.
  Qualification commit `c18f08b` binds eight repair sources over immutable v34.
- The repaired zero-guard target completed its lifecycle but actual lines were `1,3,2,1`; a
  four-micrometer guard remained in the same `14000` HWPUNIT bucket and also failed cell C's one-line
  intent. Both remain failed semantic calibration evidence, not PASS.
- Calibrated builder `/v1` binds the exact prior Hangul save and applies a 350-micrometer guard to
  cross the observed 100-HWPUNIT line-box bucket. Three create-new targets are byte-identical at
  SHA-256 `3dfcf2a185a4129989b29877b7df7dadb638071aed5ccddd1476e46f76d9bcb5`; wrong identity and
  overwrite attempts fail closed.
- Exact licensed Hangul 2020 `11.0.0.9136` passed open/read, create-new save, reopen/read, PDF export,
  close and quit. Input and visible text are unchanged, requested cell dimensions/margins/content
  are preserved, actual line counts are `1,3,1,1`, line-box widths are `14100,3700,14100,3700`, and
  Hwp residue is zero. PDF SHA-256 `6e929f5c...1cf54606` visually has no clipping or overlap.
- V2 contract `protocol/private/p06-table-layout-target-v2.json`, migration, report, exact ignored-
  artifact validator and four tamper tests pass. Implementation commit is `9774156`.
- Source v36 acceptance run `3d1319eb167744489cc5b282f4b41a72` passed 11/11 at clean commit
  `97741561c748e575eaf4c06c47acb4c15a9ab266`; receipt SHA-256 is
  `932e64ef14546a04186c454b4bbffdc1afd14072d7f0e11ac08e9770fcd0df08`. Qualification commit
  `450bfd2` binds the six calibrated successor sources while keeping source-only runtime claims false.
- Workspace all-target tests, Clippy `-D warnings`, formatting, P06 Python 53/53, four PowerShell
  static suites, v1/v2 target validators and negative tests pass. P06-05 is PASS only for this exact
  current-PC fixture; arbitrary documents and other PCs/versions remain unclaimed.

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
- Actual licensed Hangul 2020 source capture passed on a new synthetic 1x3 table: operands `17,25`,
  formula action result `42`, save/reopen visible-text identity and PDF export all passed; HWPX SHA-256
  is `d968cae419a3754b1dc65eb845f9d1d6bf8bbb486736359cd9b838a78e47d38f`, trace SHA-256 is
  `2bb67d3d53611dcbfb70ab014e5f3499bcc44885b7ce5ed024798e8abd10a1d7`, and Hwp residue is zero.
- Adapter profile `hwpx-agent.table-formula-hwpx.hancom-2020/1` lifts the exact native directional
  left-sum field to pure `SUM(A1:B1)` and lowers only a complete relative left-prefix sum. Native
  commands remain private; cache remains `unverified`; unknown shapes and non-left-prefix ASTs fail
  closed. Actual-source identity lowering is byte-exact.
- Adapter integration tests pass 8/8; contract/tamper tests pass 4/4; all P06 Python tests pass
  57/57; workspace all-target tests, Clippy `-D warnings` and formatting pass. Contract/report:
  `protocol/private/p06-table-formula-hwpx-v1.json` and
  `implementation/p06/P06-06_FORMULA_HWPX_ADAPTER_REPORT.md`.
- Exact structural builder commit `95a973c` inserts column 1 and row 0, moves the owner C1 to D2,
  transforms `SUM(A1:B1)` to `SUM(A2:C2)`, changes the unverified cache to 52, removes stale line
  caches, and publishes three byte-identical create-new targets at SHA-256
  `6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5`. Wrong identity and
  overwrite paths fail closed. Formula-aware ID profile v3 accepts only the exact begin/end ID pairs.
- Pre-runtime oracle checker commit `c8d0517` binds target identity, package graph, formula-v3 IDs,
  exact 2x4 grid/geometry/text, formula/cache semantics, zero target line caches, and strict target
  versus Hangul-saved comparison. Same-target substitution and wrong digest reject.
- Actual target attempts 01-03 reached validated `open_input/running` and timed out at 600, 900 and
  900 seconds without approval. All preserved the input, emitted no HWPX/PDF, cleaned exactly one
  owned Hwp process and left residue zero. They are access-wait diagnostics, not semantic failures
  and not PASS. Exact receipts: `implementation/p06/P06-06_TARGET_ATTEMPTS_DIAGNOSTIC.md`.
- The watchdog now preserves the observed progress phase and infers window visibility only from the
  engine's validated post-Visible progress ordering.
- Source v38 acceptance run `cbc7c29f6e684595a4c0c3bf49029d48` passed 11/11 at clean commit
  `6e906ae7aa3a77a850c7c95b8cd3bb40795befe6`; receipt SHA-256 is
  `e8492a60f732c424ca7b2a5316dba6c036bcd10d9030895c0d02d50d4649d951`. Qualification contract
  SHA-256 `818e41c4e8ee46eea3b0f31b7d769eb56d19f9de46310ed73e37285cb237ebe0` binds nine structural,
  oracle and diagnostic sources over immutable v37 while keeping runtime/P06-06/product claims
  false.
- Actual target attempt04 completed after the user approved all three access prompts. Its 21-event
  journal reached `terminal/pass`; input/output visible-text SHA-256 stayed
  `91fd67b8cae0b9da6f05a8e960e061c239f58979cdfe19d4aabb40a445571644`, input stayed unchanged,
  save/reopen/PDF/quit passed and Hwp residue was zero. Saved HWPX SHA-256 is
  `8b33d2353ebec9eccbcbbde0c0b31eb440390ddf9c38bad7c064f179b1ab2325`.
- The strict oracle preserves the exact D2 `SUM(A2:C2)` AST, value 52, 2x4 topology, all eight
  visible values, table/cell geometry, margins and content digest. Each cell has one exact one-line
  cache. Removing all ten renderer-owned section caches makes the saved section byte-identical to
  the target section; remaining package drift is limited to three exact heading fallbacks,
  modified-date/header-spine metadata, caret position, row-boundary preview text and regenerated
  preview image.
- PDF SHA-256 `e09e5a0d...0149f0` is a valid one-page A4 render; visual review confirms the 2x4
  table and all values with no clipping or overlap. V2 contract, migration, report, ignored-artifact
  validator and five tamper test groups pass. P06-06 is current-PC PASS; P06 remains in progress.
- Workspace all-target Rust tests, Clippy `-D warnings` and formatting pass; P06 Python tests pass
  62/62 and the 11 P05/P06 PowerShell static safety suites pass.
- Source v39 acceptance run `e159d3cf21df48b38bda3f9813d8a0d1` passed 11/11 at clean commit
  `103bbf5b0448076e3f95db939b4d186100b6a4f4`; receipt SHA-256 is
  `b3d0349d0e0b84900f7200938d8687cbe3b636ffecd62d2670c7197da77815c3`. Qualification contract
  SHA-256 `544c68cdea536e234139bd492f7e2812fe1b7ab02826af580f307284835f287c`
  binds the seven exact P06-06 closure sources over immutable v38. V39 focused tests pass 5/5,
  `verify` passes, and its generic source-only runtime/P06/product claims remain false.

## Latest P06-07 evidence

- Pure schemas `hwpx-agent.table-pagination/v1` and
  `hwpx-agent.table-pagination-observation/v1` bind one validated `TableGrid` to exact row heights,
  typed split eligibility, page capacities, ordered fragments, repeated header copies, and a
  renderer observation without predicting renderer output.
- `allow`, `avoid_row`, `avoid_table`, and `required_keep` are distinct. Avoid-row rejects a page
  boundary through a vertically merged cell; nested-table and unbreakable-object rows cannot be
  silently split; required keep rejects a detached caption policy.
- Repeat headers are a contiguous prefix and may not contain a master cell that crosses into the
  body. Top/bottom captions bind semantic content SHA-256, block height, gap and explicit keep.
- Rust P06-07 boundary tests pass 11/11, including one micrometer before/exactly at/after capacity,
  row fragments, header mismatch, merged/nested/unbreakable rows, caption order, malformed JSON,
  finite limits and stable public error codes. Full `domain-ir` tests and Clippy `-D warnings` pass.
- Contract validator and four tamper tests pass with six immutable source locks and four
  implementation files. This component does not claim current Hangul page counts, HWPX lowering,
  save/reopen/PDF, left/right captions, P06-07 completion, production or product completion.
- Static current-PC adapter profile `hwpx-agent.table-pagination-hwpx.hancom-2020/1` maps `CELL`,
  `TABLE`, and `NONE` exactly to allow, avoid-row, and avoid-table. `required_keep` rejects because
  no exact table-level native attribute is admitted.
- Repeated headers bind the table `repeatHeader` flag to a contiguous prefix of rows whose direct
  cells uniformly carry `header="1"`; mixed, non-contiguous and flag-inconsistent sources reject.
  Existing top/bottom caption attributes lower only when their semantic-content SHA-256 remains
  exact. Caption creation/removal and left/right flow remain outside V1.
- Adapter tests pass 10/10, full `hwpx-package --all-targets` passes, package Clippy
  `-D warnings`, formatting and diff checks pass. The HWPX adapter contract plus four tamper tests
  pass; the complete P06 Python suite passes 70/70.
- The pure/adapter PASS results do not establish renderer behavior. A predecessor target has
  diagnostic-only Hangul 2020 lifecycle evidence, while the corrected qualifying target v2 still
  has `NOT_RUN` boundary, repeated-header/caption and PDF geometry evidence; P06-07 and P06 remain
  in progress.
- Exact composite target v2 SHA-256 `98aab83f...d9eb33` passes the pre-runtime oracle with six
  typed tables (five top-level and one nested), five captions, one native equation and zero stale
  line caches. Its builder is deterministic, create-only and source-SHA locked. The predecessor
  target completed the full Hangul 2020 save/reopen/PDF lifecycle, but visual review found long-cell
  clipping, a blank continuation page, no useful before/exact/after separation, and no avoid-row
  page crossing. It is retained as failed diagnostic evidence. V2 removes the artificial long-cell
  height, forces the avoid-row case across pages and recalibrates the boundary fillers; its first
  launch timed out waiting for access before file open, so v2 renderer evidence remains `NOT_RUN`.

## Latest P06-08 evidence

- Exact commit `293053e2c756d145fea6caf899dd636a6978757b` implements schema
  `hwpx-agent.table-inspection/v1`: stable table/cell selectors bind revision, canonical graph SHA,
  typed structural path, logical ID and fingerprints; merged covered coordinates retain the
  requested coordinate while resolving to the canonical master.
- Top-level, cell/drawing-nested and note-root tables are recursively indexed. Snapshot output is
  metadata-only, deterministic and finite; cell bodies are omitted and fingerprinting streams into
  bounded SHA-256 state.
- Primary Rust boundary tests pass 11/11, P06 Python passes 74/74, contract/tamper passes 4/4,
  `domain-ir` all-targets, Clippy `-D warnings` and formatting pass. STRICT review closed three
  allocation/coverage findings with final blocker/major/minor `0/0/0`.
- Primary FULL lanes linux-core/windows-worker/widget and a separate security lane pass. Docs is
  not green because R-0008's historical P14 validator rereads a mutable successor file; FULL 5/5
  is not claimed. Clean checkout independently passes linux-core, P06-08 contract 4/4 and Rust
  11/11; its wider Windows/P06 runs stop on intentionally ignored current-PC evidence absence.
- Report: `implementation/p06/P06-08_REPORT.md`. P06-08 does not claim HWPX/Hangul cursor/readback,
  P06-07 renderer closure, P06-09 matrix, P06 or product completion.

## Open risks and holds

- R-0002: P16 actual registered-app and Hangul end-to-end evidence absent.
- R-0003: one historical independent worker timeout root cause remains unproven; retries passed.
- R-0005: P17 durable checkpoint exists, but atomic durable mirror role/head admission, persistent
  credential custody, production lifecycle and real pull/push do not.
- R-0006: P17 conflict resolver/widget are component evidence only.
- R-0007: P06-07 still requires the actual current Hangul 2020 boundary-page and exact page/PDF
  oracle; P06-09's
  61-capability target conformance matrix. P06-05's exact fixture PASS does not prove arbitrary
  documents or other PCs/versions.
- R-0008: bulk discovery of historical source-qualification tests reports forward-stability errors
  in v21-v30, v33-v34 and now direct v38 verification because those legacy verifiers reread mutable
  files after qualified successors change them. The authoritative latest v39 verifies and its five
  focused tests pass. Before the final Gate, make the legacy audit forward-stable against immutable
  commit blobs without rewriting its historical contracts or reclassifying old evidence.
- HOLD-0002: P10-05 path-security registration and P10-06 production COM execution.
- HOLD-0003: P10-08 production isolation and later-version PCs.

## Next actions

1. At `max`, rerun the exact composite P06-07 target v2 when the user can approve the visible
   Hangul 2020 access prompts, then collect repeat-header/caption save/reopen/PDF evidence for
   one-line-before, exact-boundary, one-line-after, merged-cell, nested-table and long-equation
   cases. Keep renderer/page claims unverified until visual and structural evidence both pass.
2. At `max`, implement P06-09's fail-closed 61-capability current-PC target conformance matrix.
   Bind every row to source contract, exact implementation and actual/static evidence; missing
   P06-07 renderer evidence must remain non-green.
3. At every card/phase closure run target tests, regressions, current and clean-checkout FULL plus
   applicable offline Linux/security/STRICT checks without weakening actual-evidence Gates.

## Context pack and archive pointers

- Read first: this file, `implementation/p06/P06-04_CELL_STYLE_POLICY.md`,
  `implementation/p06/P06-06_FORMULA_AST_POLICY.md`,
  `implementation/p06/P06-06_TARGET_READBACK_REPORT.md`, `implementation/p06/P06-03_REPORT.md`,
  `implementation/p06/P06-07_TABLE_PAGINATION_POLICY.md`,
  `implementation/p06/P06-07_TABLE_PAGINATION_HWPX_ADAPTER_REPORT.md`,
  `implementation/p06/P06-08_REPORT.md`, and
  `implementation/p05/P05_GATE_REPORT.md`.
- P06-04 source tool: `implementation/p06/tools/create-hancom-2020-table-source.ps1`.
- P06-05 metric qualification: commits `af3dbf0`, `42aba1c`, `742b3d2`.
- P17 source qualification: `implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V39.md`; other details
  are under `implementation/p17/`; detailed ledger history through
  P-0085 is recoverable from `fae5bc0:PLANS.md` and later Git history.
- Do not touch user originals, failed evidence, immutable predecessor locks or unrelated processes.

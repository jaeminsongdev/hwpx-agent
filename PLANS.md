# HWPX Agent implementation ledger

- Updated: 2026-09-03
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only
- Active phase/task: `P05 / P05-03 Paragraph styles`
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
| P05 | `in_progress_current_pc_local` | P05-01/02 pass; P05-03 active |
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
| P-0042 | P05-03 Paragraph styles | `in_progress` | exact 2020 paraProperties and border/fill profile discovery |

## P05-03 acceptance

- Lock a versioned bounded current-2020 `header.xml` paragraph-style profile from exact
  `paraProperties` and the border/fill structures it references, cross-checked against the locked
  official Appendix C/F records. Do not infer another Hangul release from a shared namespace.
- Model paragraph alignment, margin/indent, paragraph-before/after and line spacing, line-break word
  policy, condense/grid/font-line-height, widow/orphan, keep-with-next, keep-lines, page-break-before,
  heading/outline and typed border/fill references using exact units, enums, defaults and ranges.
- Lift only supported exact namespace shapes through P03 preserving XML. Validate counts, child
  cardinality/order, unique dense IDs, numeric/enum/bool/range syntax and every in-scope reference.
  Unknown content inside a typed record rejects or remains explicitly non-editable; none is dropped.
- Define semantic paragraph-style identity separately from allocated ID. Deduplicate in deterministic
  first-use order and atomically rewrite only typed P05-01 `paraPrIDRef` references after a complete
  validation pass. Opaque content and unrelated IDs must remain untouched.
- Lower deterministic escaped typed fragments, reparse for exact equality/reference closure, and emit
  stable digest/count receipts. No raw XML, CSS-like style string, arbitrary path, COM/HAction name or
  best-effort platform fallback enters the public contract.
- Test the exact generated 2020 header, alignment/margins/negative indent/spacing/line-spacing and
  keep/break variations, border/fill reference behavior, dedup/idempotence, malformed/count/ID/
  reference/range/namespace/limit failures and P05-01 paragraph-reference readback.
- Run Windows and offline read-only Linux unit/Clippy validation, current/clean-clone FULL 5/5 and
  security. This pure package/IR task requires no Hangul UI or user document; visual pagination and
  installed-runtime fidelity remain later layout-oracle evidence.

## P05-02 closure evidence

P05-02 added `hwpx-agent.character-style/1` with seven language-local font domains, bounded typed
font/style values, semantic dedup, atomic typed-reference rewrite and deterministic lower/readback
receipts. Its 11 tests, fixed 128-case corpus `5d2a03a1...91e6d`, package 74/74, Windows/Linux,
current/clean FULL 5/5 and security all passed at exact commit `a810aa7`; no Hangul runtime or user
document was used. Installed-font/render compatibility remains unverified.

## Validation policy

Every implementation task gets target tests plus format/Clippy, relevant regressions, current checkout
FULL, exact-commit clean clone FULL, offline network-disabled Linux core where applicable, security
checks, strict self-review and an authoritative report. A phase closes only after its separate
STRICT/`max` Gate audit updates the roadmap, status and this ledger.

## Exact next action

Inspect the exact current-2020 generated `header.xml` paraProperties/borderFills, the locked official
Appendix C/F records and P03 ID/preserving XML contracts. Freeze `P05-03` paragraph semantic identity,
units, ranges, reference domains, defaults and failure codes in a migration/policy, then implement the
smallest exact-profile lift/lower/readback slice. Continue at reasoning effort `max`.

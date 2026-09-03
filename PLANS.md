# HWPX Agent implementation ledger

- Updated: 2026-09-03
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only
- Active phase/task: `P05 / P05-02 Character styles`
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
| P05 | `in_progress_current_pc_local` | P05-01 pass; P05-02 active |
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
| P-0041 | P05-02 Character styles | `in_progress` | exact 2020 header profile and typed style contract discovery |

## P05-02 acceptance

- Lock a versioned bounded current-2020 `header.xml` character-style profile. Model all seven language
  slots (Hangul/Latin/Hanja/Japanese/Other/Symbol/User), font identities/references, HWPUNIT height,
  ratio, spacing, relative size, offset, font spacing/kerning, text/shade color and supported effects.
- Lift only exact `http://www.hancom.co.kr/hwpml/2011/head` fontface/charProperties structures through
  P03 preserving XML. Validate counts, unique dense IDs, references, ranges, enum/color syntax and
  child cardinality. Unknown or unsafe shapes remain opaque/non-editable or reject; none are dropped.
- Define semantic style identity separately from allocated ID. Deduplicate equal semantic styles in a
  deterministic first-use/canonical order, allocate checked collision-free IDs and rewrite only typed
  references. Repeated input order must produce byte-identical catalogs and receipts.
- Lower typed fontface/charPr fragments with deterministic attribute/child order and escaped values,
  then reparse and require exact semantic equality and reference closure. No raw XML, installed-font
  assumption, arbitrary path or platform font fallback enters the contract.
- Test the exact generated 2020 header (7 fontface groups, 7 charPr records), cross-language slot
  variation, size/ratio/spacing/effects/colors, dedup/idempotence, missing/dangling/duplicate IDs,
  malformed/limit/range/opaque cases and P05-01 run `charPrIDRef` readback.
- Run Windows and offline read-only Linux unit/Clippy validation, current/clean-clone FULL 5/5 and
  security. This task is a pure package/IR Gate and requires no Hangul UI or user document; actual
  installed-font rendering and visual fidelity remain later oracle evidence.

## P05-01 closure evidence

P05-01 added `hwpx-agent.text-flow/v1` with ordered run/text/tab/line-break/field boundaries, bounded
lift/lower/lift, conservative opaque semantics and redacted diagnostics. Its 12 tests, 128-case fixed
corpus, package 63/63, Windows/Linux workspace, current/clean FULL 5/5 and security all passed at exact
commit `08de88a`; no Hangul runtime or user document was used. Character references remain unresolved
numeric IDs until P05-02.

## Validation policy

Every implementation task gets target tests plus format/Clippy, relevant regressions, current checkout
FULL, exact-commit clean clone FULL, offline network-disabled Linux core where applicable, security
checks, strict self-review and an authoritative report. A phase closes only after its separate
STRICT/`max` Gate audit updates the roadmap, status and this ledger.

## Exact next action

Inspect the exact current-2020 generated `header.xml`, the locked official head-schema records and P03
ID/preserving XML contracts. Freeze `P05-02` char-style semantic identity, ranges, effects, dedup and
failure codes in a migration/policy, then implement the smallest exact-profile lift/lower/readback
slice. Continue at reasoning effort `max`.

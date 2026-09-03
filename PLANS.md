# HWPX Agent implementation ledger

- Updated: 2026-09-03
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only
- Active phase/task: `P05 / P05-01 Text flow reader/writer`
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
| P05 | `in_progress_current_pc_local` | P05-01 active |
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
| P-0040 | P05-01 Text flow reader/writer | `in_progress` | contract/source/failure model discovery |

## P05-01 acceptance

- Add a versioned bounded typed text-flow model that distinguishes text runs, tabs, line breaks,
  field begin/end boundaries and any required opaque non-editable token. Do not collapse adjacent runs
  when style/source boundaries differ, and do not infer unmatched field pairs.
- Lift only from P03 safe/preserving XML with explicit namespace/name and checked source spans. Unknown
  or unsafe constructs remain preserved/opaque or cause a stable typed rejection; they are never
  silently discarded or interpreted as executable markup.
- Lower deterministic XML through typed values only. Escape text correctly, preserve Unicode scalar
  content and semantic NFC policy without changing source run boundaries, and reparse/re-lift the
  result before publication. No raw caller XML fragments are accepted.
- Apply finite limits for bytes, elements, runs, text, field depth and nesting with checked arithmetic;
  duplicate/missing/misnested field boundaries, malformed XML, limit overflow and unsupported shapes
  fail without partial flow or output.
- Test Hangul/Latin/CJK/emoji/combining characters, tabs/line breaks, empty and adjacent runs, style
  transitions, nested/sequential field boundaries, XML escaping, malformed/limit cases, deterministic
  lift→lower→lift and untouched-byte preservation outside the targeted paragraph.
- Run Windows and offline read-only Linux unit/Clippy validation, current/clean-clone FULL 5/5 and
  security. This task is a pure package/IR Gate and requires no Hangul UI or user document.

## P04 closure evidence

P04 built typed immutable DocumentGraph, exact selectors, deterministic atomic plans, signed
capability routing, isolated workspace transactions, semantic diff, in-memory exactly-once/CAS and
the VS-0 vertical. Actual 2020 open/readback/close/Quit passed with input/save/network/settings change
and residual process all 0. The actual bundle is digest-correlated and independently checked; private
body/path/key data is untracked. Durable cross-process idempotency remains explicitly P14.

## Validation policy

Every implementation task gets target tests plus format/Clippy, relevant regressions, current checkout
FULL, exact-commit clean clone FULL, offline network-disabled Linux core where applicable, security
checks, strict self-review and an authoritative report. A phase closes only after its separate
STRICT/`max` Gate audit updates the roadmap, status and this ledger.

## Exact next action

Inspect the authoritative HWPX 2020 paragraph schema/source records and existing P03 preserving XML /
P04 paragraph IR. Freeze `P05-01` typed elements and failure codes in a migration/policy, then implement
the smallest safe lift/lower slice with Unicode/run-boundary tests. Next phase decision after P05-01:
P05-02 at `max` if the task Gate passes.

# P07-02 LaTeX adapter report

## Result

Result: `component_pass` / direct stage `unit_passed`.

`equation-engine` now parses a finite versioned LaTeX profile into normalized P07-01 `MathAst`
values. Unsupported source fails closed. Four ambiguity classes return two complete semantic
candidates with uncalibrated deterministic confidence instead of choosing one interpretation.

## Evidence

- Focused `equation-engine` all-target locked/offline tests: 11/11 PASS.
- Focused Clippy with `-D warnings`: PASS.
- `p07-focused` profile: MathAst 19/19, LaTeX adapter 11/11 and private-contract tests
  8/8 PASS.
- Final `rust-full` profile: workspace all-target/all-feature locked/offline tests PASS in 29.470s,
  workspace Clippy with `-D warnings` PASS in 9.439s and fmt check PASS in 1.581s. The existing
  explicitly isolated PostgreSQL and Windows credential side-effect cases remain ignored; this
  run does not substitute for P17's separate 397-test qualification.
- Development-runner regression tests: 12/12 PASS; `git diff --check` and final fmt check PASS.
- Explicit Tier A source corpus: 44/44 PASS with no ambiguity or approximation.
- Ambiguity cases: `2x`, `xy`, `f(x)` and `-x^2` return two semantically distinct candidates;
  multiple source sites remain distinct.
- Macro cases cover parameters, nested expansion, deterministic output, reserved/duplicate names,
  invalid references, direct recursion, depth and expansion limits.
- Negative/boundary cases cover empty/oversized source, token/parser-depth/output/ambiguity limits, unsupported
  commands/environments/comments/approach arrows, missing groups, chained relations, wrong schema,
  duplicate/unknown JSON fields and redacted Debug/error surfaces.

## Evidence boundary

This is component evidence for P07-02's finite explicit-source parser, not full P07 Tier
conformance. MathML, EqEdit, native HWPX equation writing, package preservation, EquationNode
integration, Hangul execution, save/reopen, semantic native readback, editor smoke, rendering,
automation and differential evidence are `false` / `not_run`. P07 remains in progress.

## Next exact task

Implement P07-03 as a namespace-strict, entity-safe finite MathML adapter into the same MathAst,
with presentation/content source profiles, exact ambiguity rejection and a round-trip corpus. The
next reasoning level remains `max`.

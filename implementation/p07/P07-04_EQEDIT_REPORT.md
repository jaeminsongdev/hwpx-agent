# P07-04 EqEdit parser/compiler report

## Result

Result: `component_pass` / direct stage `unit_passed`.

`equation-engine` now parses the finite current-PC Hangul 2020 EqEdit profile to normalized
P07-01 `MathAst` and compiles admitted ASTs to deterministic, fully grouped EqEdit. Every compiler
result is reparsed and compared semantically before it can be returned.

## Evidence

- Focused EqEdit adapter Rust tests: 12/12 PASS, including 256 deterministic generated
  AST/script semantic round trips.
- `equation-engine` all-target locked/offline tests: 33/33 PASS, retaining the LaTeX and MathML
  adapter suites.
- Focused `equation-engine` Clippy with `-D warnings`: PASS.
- P07 private-contract tests: 16/16 PASS, including four EqEdit contract/migration/source-lock/
  evidence/tamper groups.
- Final `rust-full` profile: workspace all-target/all-feature locked/offline tests PASS in 29.1s,
  workspace Clippy with `-D warnings` PASS in 0.8s and fmt check PASS in 1.6s. Strict diff/self-audit
  also passed. The established isolated PostgreSQL and two Windows credential side-effect cases
  remain explicitly ignored rather than promoted.
- Cross-adapter tests compile admitted LaTeX and MathML ASTs, reparse the emitted EqEdit and require
  normalized semantic equality. Dedicated cases cover current commands, precedence, distinct
  fraction/division and script/power forms, functions, symbols, accents, six integral tokens,
  matrices, cases, aligned rows, set-builder, binomial and the canonical derivative quotient.
- The exact P06-07 saved script is admitted as a source-profile fixture. Its prior licensed
  save/reopen success is not relabeled as execution evidence for this new engine.
- Boundary and negative cases cover strict JSON/version/profile admission; source/token/token-byte,
  parser/compiler depth, script/result limits; relation chains, ragged grids, removed commands,
  unsupported escapes/spacing; styles, named functions and other unrepresentable ASTs; deterministic
  receipts and redacted Debug/errors.

## Evidence boundary

Installed help and binaries qualify the finite dialect vocabulary, and the code/test/contract
evidence proves the local parser/compiler component. Actual HWPX mutation, EquationNode lowering,
native equation creation/readback, Hangul execution of this engine, save/reopen, editor smoke,
render, automation and differential remain `false` / `not_run`. This is not a P07, production or
product PASS.

## Next exact task

Implement P07-05 as a typed native equation lowerer/readback boundary that binds `MathAst`, EqEdit,
object properties and package state without raw XML or image fallback. First prove closed-package
HWPX preservation, then obtain separate licensed Hangul 2020 save/reopen/readback evidence. The
next reasoning level remains `max`.

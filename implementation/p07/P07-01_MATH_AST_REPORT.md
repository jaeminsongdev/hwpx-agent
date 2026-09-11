# P07-01 MathAst report

## Result

Result: `component_pass`.

`domain-ir` now contains a versioned MathAst with exact source spans, optional typed style hints,
the complete semantic node families required by the equation design, deterministic normalization,
bounded complete JSON and a separate semantic projection/hash. The projection ignores provenance
and visual style while preserving semantic operator, order, content and structure.

## Evidence

- Focused Rust `math_ast` tests: 19/19 PASS.
- Focused `domain-ir` all-target/all-feature Clippy with `-D warnings`: PASS.
- `domain-ir` all-target/all-feature tests: PASS.
- Workspace all-target/all-feature locked offline tests and Clippy with `-D warnings`: PASS; the
  three pre-existing environment/side-effect qualifications remain ignored.
- Property-style corpus: 128 generated spelling/grouping/style variants preserve semantic equality,
  hash stability and canonical JSON idempotence.
- Boundary/negative coverage includes versions, unknown JSON fields, source containment, exact
  arities, number/identifier/text grammar, script/delimiter/large-operator/derivative shape,
  rectangular and determinant matrices, aligned columns, all finite limit classes and redacted
  Debug.

## Evidence boundary

This is pure component evidence for `P07-01`. LaTeX, MathML and EqEdit adapters, `EquationNode`
binding, native HWPX emission, Hangul execution, save/reopen, semantic readback, editor smoke,
rendering, automation and differential evidence are `false` / `not_run`. No EQ matrix row is
release-green and P07 is still in progress.

## Next exact task

Implement P07-02 as a finite, versioned LaTeX subset adapter that produces this MathAst, returns
typed ambiguity candidates instead of guessing, bounds macro expansion depth/token count, and
passes a Tier A plus negative corpus without claiming native equation output.

# P07-03 MathML adapter report

## Result

Result: `component_pass` / direct stage `unit_passed`.

`equation-engine` now parses a finite namespace-strict presentation/content MathML profile into
normalized P07-01 `MathAst` values. Unsafe XML, profile mixing, semantic adjacency and unsupported
structures fail closed without a partial tree.

## Evidence

- Focused MathML adapter Rust tests: 10/10 PASS.
- `equation-engine` all-target locked/offline tests: 21/21 PASS, including the unchanged 11/11
  LaTeX adapter groups.
- Focused Clippy with `-D warnings`: PASS.
- P07 private-contract tests: 12/12 PASS, including four MathML contract/migration/tamper groups.
- Final `rust-full` profile: workspace all-target/all-feature locked/offline tests PASS in 30.930s,
  workspace Clippy with `-D warnings` PASS in 1.080s and fmt check PASS in 1.656s. The existing
  isolated PostgreSQL and two Windows credential side-effect cases remain explicitly ignored.
- Cross-profile semantic corpus: 17/17 presentation/content pairs normalize to equal MathAst.
- XML security cases cover DTD, custom entity, PI, CDATA, comment, XML 1.1/legacy declaration,
  wrong/unbound/foreign namespace, unused foreign namespace binding and safe numeric references.
- Boundary and negative cases cover input/XML/event/element/depth/text/attribute/namespace/child,
  presentation-parser and serialized-output limits; mixed profiles, adjacency, omitted function
  application, relation chains, unsupported elements/attributes, arity, qualifiers, ragged matrix,
  duplicate/unknown JSON fields and redacted Debug/error surfaces.

## Evidence boundary

This is component evidence for P07-03's finite source adapter and cross-profile semantic corpus.
It is not a full MathML, serializer, EqEdit, native HWPX, package-preservation, EquationNode,
Hangul, save/reopen, readback, editor-smoke, render, automation, differential, P07 or product PASS.
Those fields remain `false` / `not_run`.

## Next exact task

Implement P07-04 as an exact Hangul-2020-profile EqEdit parser/compiler with explicit precedence,
escaping and symbol lowering, then prove AST-to-script-to-AST properties without claiming native
object success. The next reasoning level remains `max`.

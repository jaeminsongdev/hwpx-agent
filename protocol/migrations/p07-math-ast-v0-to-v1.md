# P07 MathAst v0 to v1 migration

`hwpx-agent.math-ast/v1` and `hwpx-agent.math-ast-normalization/v1` replace the earlier design-only
`EquationNode/MathAst` placeholder with a private, typed and bounded semantic model.

Existing documents, `DocumentGraph`, equation source strings and public capability schemas are
unchanged. No stored v0 MathAst exists to rewrite. Later source adapters must construct a v1 draft
with one exact source length and a non-empty contained source span on every node. They must resolve
dialect ambiguity before admission; this model never guesses whether adjacency means
multiplication or function application, or whether a minus is unary or binary.

The complete normalized JSON retains spans and style hints. Semantic identity uses a separate
versioned projection that omits source length, spans and visual style, normalizes exact decimals and
Unicode NFC, removes unary positive, flattens associative grouping without operand reordering, and
equates square root with an explicit degree-two root. Unknown versions, fields, nodes, limits and
structural shapes fail closed without returning a partial AST.

LaTeX, MathML and EqEdit parsing/compilation, `EquationNode` integration, native HWPX objects,
licensed Hangul save/reopen, semantic readback, editor smoke, rendering and automation remain
separate P07 Gates. This migration does not promote component evidence into any target or product
PASS.

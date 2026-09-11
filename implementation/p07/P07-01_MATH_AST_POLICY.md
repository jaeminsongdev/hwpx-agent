# P07-01 MathAst policy

## Decision

Status: `component_only / unit_passed`.

P07-01 establishes `hwpx-agent.math-ast/v1` and
`hwpx-agent.math-ast-normalization/v1` inside `domain-ir`. It is the typed, bounded semantic
boundary shared by the later LaTeX, MathML and EqEdit adapters. It does not parse any source
dialect and does not emit or validate a native equation object.

## Model boundary

- Every `MathNode` carries one non-empty, end-exclusive byte span inside the exact source length
  and an optional typed visual style hint. Child spans must be contained by their parent span.
- Literals cover exact base-10 numbers, identifiers, text, Greek and fixed mathematical symbols.
  Operators distinguish arithmetic, relation, logic and set semantics with exact arity rules.
- The tree covers explicit functions, fractions, scripts, roots, accents, over/under annotations,
  limits, sums, products, single/multiple/contour integrals, multivariable derivatives,
  asymmetric delimiters, rectangular matrices and determinants, cases, aligned lines,
  combinatorics and set builders.
- Numbers remove redundant leading and fractional trailing zeroes. Identifier, text and named
  function content is Unicode NFC. Empty, control-bearing or whitespace-bearing identifiers and
  signed/exponent/non-decimal number spellings fail closed; sign is an operator, not a literal.
- Empty style hints normalize to absent. The complete canonical JSON retains normalized content,
  spans and style. The semantic projection excludes source length, spans and visual style, removes
  unary positive, flattens nested rows and associative operations without reordering operands, and
  treats an explicit degree-two root as a square root.
- Semantic equality and SHA-256 use that version-bound projection. Operator, operand order,
  function identity, literal content and every structural node remain identity-bearing.

## Limits and failure policy

All constructors require a validated `MathAstLimits`. Source bytes, node count, depth, children,
matrix dimensions, per-string bytes, aggregate string bytes and serialized bytes have finite
defaults and hard ceilings. JSON denies unknown fields. Invalid schema/normalization versions,
spans, arity, structure, literals, allocation arithmetic or output bounds return a typed error and
no partially admitted `MathAst`.

Parser ambiguity is outside this layer. A later adapter must return candidates/confidence and may
only create this AST after resolving implicit multiplication, unary minus, function application,
derivative notation and other dialect ambiguity.

## Gate boundary

This component pass does not claim a LaTeX, MathML or EqEdit parser/compiler, `EquationNode`
integration, direct HWPX lowering, package preservation, native object inspection, licensed
Hangul 2020 execution, save/reopen, editor smoke, render/baseline quality, automation parity,
P07 completion, production readiness or product completion. Those remain separate P07 Gates.

Reasoning level: `high` for this isolated pure model; `max` remains required for adapters,
preservation, target readback/render and phase Gates.

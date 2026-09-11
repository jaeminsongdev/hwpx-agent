# P07-03 MathML adapter policy

## Decision

Status: `component_only / unit_passed`.

P07-03 establishes `hwpx-agent.mathml-adapter/v1` and
`hwpx-agent.mathml-profile/finite-v1` in `equation-engine`. It converts one finite, documented
presentation or content MathML document into the P07-01 `MathAst`. It does not emit EqEdit, HWPX
or a native equation object.

## XML security and namespace boundary

- Input is bounded UTF-8 XML 1.0. The root is exactly `math`, and every element must resolve by URI
  to `http://www.w3.org/1998/Math/MathML`; literal prefixes are not trusted.
- The five predefined references and valid numeric XML scalar references are accepted. DTD,
  custom named entities, processing instructions, CDATA, comments, legacy encodings, unbound or
  foreign namespaces and foreign namespaced attributes fail closed. No filesystem, network,
  process or application resolver exists.
- Namespace declarations may bind only the exact MathML URI. Ordinary attributes are
  namespace-free, element-specific and allowlisted. Duplicate attributes and ignored semantic
  attributes fail closed.
- XML events, elements, depth, text, aggregate text, attributes, attribute bytes, active namespace
  bindings, children, presentation-parser depth, source and serialized output all have finite
  default and hard ceilings.

## Finite presentation profile

The adapter admits `mrow`, `mn`, `mi`, `mo`, `mtext`, fraction/root/script structures, exact
`mfenced` delimiters, explicitly attributed accents and fixed over/under annotations, `mstyle` with typed variant and
`#RRGGBB`, bounded rectangular `mtable`, and lower/upper-bound sum, product, limit and integral
heads. Arithmetic, relation, logic and set operators are an exact Unicode allowlist.

Multiplication and function application require U+2062 INVISIBLE TIMES and U+2061 FUNCTION
APPLICATION (or another explicit admitted operator). Adjacent operands, ordinary `f(x)` without
U+2061, relation chains, unknown operators and unsupported attributes are rejected as ambiguous or
unsupported; the adapter never guesses. Function parentheses are syntax grouping and do not enter
the semantic argument. Multi-letter `mi` remains one exact identifier.

## Finite content profile

The adapter admits exact `cn` decimals, `ci`, `cs`, Greek/fixed constants, bounded `apply`
operators and built-in functions, divide-to-fraction, power-to-script, root/degree, lower and upper
large-operator qualifiers, ordinary/partial derivatives with positive `bvar` degree, rectangular
matrix/matrixrow and set-builder bvar/condition. Operator arity, qualifier order/cardinality and
rectangularity are exact. Unknown content operators, `csymbol`, semantics/annotation payloads,
units, intervals, vectors, piecewise/aligned structures and arbitrary OpenMath/package extensions
remain unsupported.

The root is classified as presentation or content from its direct children. Mixing profiles is an
error. Content MathML has exactly one semantic root; presentation MathML may have a bounded row.

## Provenance and semantic round-trip

The deterministic result retains adapter/profile/MathAst versions, detected profile, exact source
SHA-256, source byte count, element and decoded-text counts, and the admitted complete `MathAst`.
Raw MathML is not retained as another receipt field. Debug and typed errors omit source text,
values, spans, hashes and AST payloads.

The cross-profile corpus pairs 17 presentation and content documents for arithmetic, unary minus,
explicit multiplication, fractions, powers, roots, relations, logic, functions, factorial,
symbols, bounded large operators and rectangular matrices. Every pair must normalize to the same
semantic `MathAst`; this is not a serializer or native EqEdit round-trip claim.

## Gate boundary

This finite component does not claim full MathML 3/4, full Content or Presentation MathML, Tier
A/B/C completion, a MathML serializer, EqEdit parsing/compilation, `EquationNode` integration,
direct HWPX mutation, package preservation, native object/readback, licensed Hangul 2020
execution, save/reopen, editor smoke, rendering, automation, differential, P07 completion,
production readiness or product completion. Those states remain `false` / `not_run`.

Reasoning level: `max` for this adapter and all later equation lowering/target Gates.

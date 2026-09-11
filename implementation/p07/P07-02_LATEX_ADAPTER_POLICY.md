# P07-02 LaTeX adapter policy

## Decision

Status: `component_only / unit_passed`.

P07-02 establishes `hwpx-agent.latex-adapter/v1` and
`hwpx-agent.latex-parser/tier-a-v1` in the `equation-engine` crate. It converts a finite,
documented LaTeX source profile into the P07-01 `MathAst`; it never emits EqEdit, HWPX or a native
equation object.

## Admitted source profile

- Exact decimals, Unicode alphabetic identifiers, groups, factorial, subscript and superscript.
- Explicit arithmetic, relation, logical and set operators. Multiplication can be written as `*`,
  `\cdot` or `\times`; no adjacency is silently treated as multiplication.
- `\frac`, `\sqrt`, fixed trigonometric/hyperbolic/log/exp/min/max functions, `\operatorname`,
  lower/upper Greek letters, the fixed P07-01 symbol set, accents and semantic-safe math variants.
- Parenthesis/bracket/bar and exact `\left ... \right` delimiter pairs.
- `\sum`, `\prod`, `\lim`, one/two/three-dimensional and contour integral nodes with explicit
  grouped bodies; `\dv`/`\pdv`, `\binom`, `\set` and non-nested `\text`.
- The adapter-specific `\dv[order]{expression}{variable}` and
  `\pdv[order]{expression}{variable}` forms are versioned source syntax, not claims about a
  third-party LaTeX package.

Unsupported commands, comments, display wrappers, `\to`, relation chains, nested text groups,
matrices/cases/aligned environments, arbitrary color/typography packages and other Tier B/C or
full-LaTeX constructs fail closed. P07-08 owns the later complete A/B/C corpus Gate.

## Ambiguity contract

Bare multi-letter identifiers, implicit adjacency, ordinary `f(x)` application and unary-minus
power precedence produce `Ambiguous`, never `Parsed`. Every distinct kind-and-source-span site is
retained up to a finite bound. Two deterministic whole-source candidates are returned:
`conventional_latex` and `literal_adjacency`. Their 600000/400000 confidence values use the explicit
basis `deterministic_syntax_preference_not_empirical_probability`; they are not calibrated
probabilities and neither candidate is selected by the adapter.

## Macro sandbox and limits

User macro names are 1-32 ASCII letters, cannot shadow any reserved built-in, and take zero to four
grouped parameters. Expansion substitutes `#1`-`#4` tokens, rejects missing arguments, duplicates,
invalid parameter references and direct or indirect recursion, and bounds definition count,
individual/aggregate replacement bytes, nesting depth, expansion count and expanded token count.

Source bytes, input/expanded tokens, parser recursion depth, ambiguity sites/candidates and
serialized output also have finite default and hard ceilings. All spans remain non-empty and inside the exact original source
length, including macro-produced tokens which bind to their invocation span. Canonical output keeps
only source SHA-256, counts, ambiguity metadata and admitted AST data; source and macro bodies are
not separate receipt fields. Public Debug and errors omit source, macro bodies, spans and hashes.

## Gate boundary

The 44-expression test corpus proves only this finite explicit-source profile. It is not the P07-08
full Tier A/B/C conformance corpus. No MathML, EqEdit parser/compiler, `EquationNode` binding, direct
HWPX mutation, package preservation, native object inspection, licensed Hangul 2020 execution,
save/reopen, editor smoke, render, automation, differential, P07 completion, production readiness
or product completion is claimed. Those states remain `false` / `not_run`.

Reasoning level: `max` for this adapter and all later equation lowering/target Gates.

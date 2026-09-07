# P06-06 FormulaAst pure component policy

- Model: `hwpx-agent.table-formula/v1`
- Contract: `protocol/private/p06-table-formula-v1.json`
- Implementation: `domain_ir::FormulaAst` and `domain_ir::FormulaCell`
- Scope: bounded pure formula/reference/cache/number-format component for current-PC local development

## Typed formula boundary

The first P06-06 increment implements the design-required `FormulaAst` before any HWPX or automation
binding. It accepts exact base-10 literals, A1 cell/range references, independent absolute/relative
axes, arithmetic, and the three functions required by the table model: `SUM`, `AVG`, and `PRODUCT`.
Parsing is ASCII and locale-neutral so comma/decimal interpretation cannot vary with the host locale.
The compiler emits uppercase references/functions, normalized decimal values, no whitespace, and
fully parenthesized arithmetic.

Typed JSON denies unknown fields and has finite input, node, depth, argument, coordinate, cache-text,
precision, and output limits. A complete `FormulaCell` can only be created or restored when its
owner and every formula reference fit caller-supplied exact table dimensions. Canonical JSON and
SHA-256 make semantic comparisons independent of the original spelling. Debug output redacts
formula literals and cached values.

## Reference semantics

Copy/rebase and structural table edits are distinct operations. Copying a formula to another owner
cell requires the exact current grid dimensions and shifts only relative axes; absolute axes remain
fixed. Every row/column structural edit carries the exact pre-edit dimensions and computes checked
post-edit dimensions. Both relative and absolute references then move so they continue to name the
same surviving cells. Interior range edits expand or contract through their endpoints. Deleting an
owner or referenced endpoint fails atomically instead of silently producing `#REF!` or a partial AST.

These pure transforms are the prerequisite for later integration with P06-02 row/column operations.
They do not yet mutate a `TableGrid` and do not claim that a particular Hangul formula string uses
the same syntax.

## Cache and number format

Formula source, cached value, and number format are separate fields. This pure component admits only
`absent` and `unverified` cache states. It deliberately cannot manufacture an oracle-qualified value
from caller-provided digest-shaped strings. A later adapter must parse and verify an actual Hangul
receipt before it can expose a separately versioned verified cache state.

`preserve` is rejected whenever a transform changes canonical formula bytes. `clear` accepts no
replacement. `update` requires a non-absent, explicitly unverified replacement.
The pure format subset is general, bounded fixed decimal/grouping, percent, and scientific. Target
format codes are deliberately deferred until exact HWPX and Hangul 2020 source evidence exists.

## Not complete

This component does not implement formula evaluation, dependency graphs/cycles, arbitrary functions,
currency/date/custom formats, HWPX formula lowering/readback, Hangul 2020 recalculation, pagination,
rendering, other PCs/versions, production, P06-06 completion, P06 completion, or product completion.
Those remain explicit gates rather than inferred support.

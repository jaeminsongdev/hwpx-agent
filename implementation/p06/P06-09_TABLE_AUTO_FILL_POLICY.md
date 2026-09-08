# P06-09 table auto-fill component policy v1

Status: pure bounded components implemented; no HWPX or Hangul 2020 oracle claim

## Scope

This policy covers `TABLE-057` / `table.auto_fill` and `TABLE-058` /
`table.auto_fill_series`. The series component defines a reusable scalar sequence. The fill
component binds one validated series to one exact logical table, canonical `TableGrid`, rectangular
merge-free region and complete pre-mutation cell snapshot. It produces a coordinate-canonical
mutation plan; it does not patch HWPX, invoke a documented native series index or automate Hangul.

## Series semantics

V1 admits exactly three deterministic definitions:

- an explicit non-empty cycle of typed blank, boolean, integer, fixed-decimal, date-day or text
  values;
- a linear number series with exact start and step values using scale-at-most-18 fixed decimal;
- a linear date-day series with signed whole-day steps.

Trailing-zero decimal representations are canonicalized. Numeric generation uses checked integer
arithmetic without floating point. Date, numeric and start-index overflow fail before a plan is
returned. A custom sequence is represented by its actual values and SHA-256 identity, not an
unqualified native UI index.

## Fill semantics

The caller explicitly selects row-major or column-major traversal and a starting series index. Each
selected coordinate carries its current scalar value plus full payload, optional formula and style
SHA-256 preconditions. The plan generates one value per coordinate, retains the style binding and
records whether a bound formula must be cleared.

Formula creation and relative-reference propagation are not part of V1. Existing formulas either
cause rejection or may be replaced only under explicit `replace_bound` policy with their exact
digest in the request and mutation. A later formula-capable version must use `FormulaAst` and a
separate migration; it may not reinterpret this scalar schema.

## Safety and determinism

- Series JSON is exactly `hwpx-agent.table-auto-fill-series/v1`; request JSON is exactly
  `hwpx-agent.table-auto-fill/v1`. Empty, oversized, malformed, duplicate and unknown input fails.
- The fill region must be ordered, inside the exact grid, merge-free and covered once by the
  supplied cell set.
- Series ID and canonical series SHA-256 must both match the exact validated series object.
- Payload, formula and preserved-style digests must be lowercase canonical SHA-256 values.
- Selected cells, series items, individual and aggregate text bytes, generation work and serialized
  bytes all have finite ceilings.
- The receipt binds table, grid, series, request, mutation set, formula policy and semantic change
  count.
- No partial plan or receipt is returned after validation, generation or output-limit failure.
- Debug output redacts logical IDs, cell and series values, sequence indices and every digest.

## Evidence promotion rule

Passing Rust and contract/tamper tests promotes only TABLE-057 and TABLE-058 to
`component_only / unit_passed` with `schema` evidence and happy, boundary, negative and
preservation fixtures. It cannot promote direct HWPX integration, formula creation/readback,
semantic/page readback, render diff, licensed Hangul 2020 target-build, native automation-series
mapping, differential exact match, P06-09/P06 PASS, production or product completion.

The next boundary is a preserving HWPX adapter that rewrites only bound cell content, proves style,
formula and pagination preservation on reopen, and rejects unsupported rich content. Recommended
reasoning remains `max`.

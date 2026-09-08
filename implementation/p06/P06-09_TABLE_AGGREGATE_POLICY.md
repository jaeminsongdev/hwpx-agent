# P06-09 table aggregate planner policy v1

Status: pure bounded component implemented; no HWPX or Hangul 2020 oracle claim

## Scope

This policy covers the locale-neutral formula-planning boundary shared by nine table calculations.
Eight were previously catalog-only and are admitted by this slice:

- `TABLE-022` / `table.block_sum`
- `TABLE-023` / `table.block_average`
- `TABLE-024` / `table.block_product`
- `TABLE-026` / `table.vertical_sum`
- `TABLE-027` / `table.horizontal_average`
- `TABLE-028` / `table.vertical_average`
- `TABLE-029` / `table.horizontal_product`
- `TABLE-030` / `table.vertical_product`

`TABLE-025` / `table.horizontal_sum` uses the same planner as a compatibility regression, but its
existing current-target oracle evidence remains authoritative and is not duplicated or downgraded.

## Semantics

Every request binds an exact nonzero table dimension, one ordered nonempty source rectangle and one
destination cell. Block calculations accept a rectangle outside the destination. Horizontal
calculations require one row strictly to the left of the destination. Vertical calculations require
one column strictly above it. A destination inside its source is rejected to avoid an immediate
self-reference.

The planner emits one relative A1 range under exactly one of `SUM`, `AVG` or `PRODUCT`. The result is
a validated `FormulaCell` with the requested destination, an absent cache and general number format.
It never evaluates the formula or invents a verified cached result.

## Safety and determinism

- Request JSON is exact `hwpx-agent.table-aggregate/v1`; unknown and duplicate keys fail closed.
- Dimensions, source endpoints and destination are checked against caller-supplied `FormulaLimits`.
- Axis mismatch, reversed range and self-reference return no partial plan.
- Canonical plan JSON and SHA-256 are deterministic and bounded by the formula serialization limit.
- Debug output redacts the compiled formula.

## Evidence promotion rule

Passing Rust and contract/tamper tests promotes only the eight listed catalog-only rows to
`component_only / unit_passed` with `schema` evidence. It cannot promote direct HWPX integration,
formula readback, page split, render diff, licensed Hangul 2020 target-build, automation,
differential exact match, release-enabled, P06-09/P06 PASS, production or product completion.

The next boundary is a preserving HWPX formula adapter for the exact native syntax variants proven
on the current licensed Hangul 2020 target. Recommended reasoning remains `max`.

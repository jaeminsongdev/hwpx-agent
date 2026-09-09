# P06-09 exact table number-format planner report

- Generated: 2026-09-10
- Model schema: `hwpx-agent.table-number-format/v1`
- Scope: current repository, pure exact-state formula-cell number-format planner
- Result: `component_pass`
- Direct stage: `unit_passed` (unchanged)
- Recommended next-step reasoning: `max`

## Result

`TABLE-049 table.number_format` now has an operation-level model rather than only a field on
`FormulaCell`. A complete master-cell state binds table identity, exact grid, table properties,
every cell's non-formula payload and properties, and full typed formula/cache/format state.

Requests canonicalize an exact formula-master selection and bind source state plus document flow.
The builder rechecks those bindings, then changes only the selected `number_format`. General,
number/grouping, percent and scientific typed variants are handled without narrowing the pure model.
Merged masters are selected only through their top-left owner; covered slots and non-formula cells
are rejected.

## Verification

| Check | Result |
|---|---:|
| Dedicated Rust tests | 12/12 PASS |
| All four typed format variants | PASS |
| Formula owner/AST/cache preservation | PASS |
| Complete cell/table/grid/flow binding | PASS |
| Request-time state/grid/flow drift | fail closed |
| Build-time state/grid/flow drift | fail closed |
| Empty/duplicate/non-formula/non-master selection | fail closed |
| State completeness/identity/owner negatives | fail closed |
| Strict JSON, precision and size limits | fail closed |
| Deterministic JSON/SHA-256 and idempotence | PASS |
| Debug sensitive state disclosure | redacted |

## Source decision

The archived official KS X 6101 machine-readable source was inspected without modification.
Section `10.7.3.5.2` supplies standard tokens for general, integer, and one through four decimals.
It does not close the exact Hangul 2020 mapping for the full typed model, including grouping,
percent and scientific formats. No guessed HWPX lowering was added.

## Conformance impact

The direct matrix remains cataloged 0, unit 4, integration 42, oracle 15, green 0/61. This
checkpoint strengthens the existing TABLE-049 unit evidence but does not change its stage.
`actual_hwpx`, `actual_hangul`, save/reopen, formula readback, page split, render, automation and
differential remain false or `not_run`. P06-09, P06, production and product completion remain open.

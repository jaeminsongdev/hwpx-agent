# P06-09 exact table number-format planner report

- Generated: 2026-09-10
- Model schema: `hwpx-agent.table-number-format/v1`
- Scope: current repository, pure exact-state formula-cell number-format planner
- Result: `integration_pass`
- Direct stage: `integration_passed`
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
| Source-qualifier static tests, PowerShell 7 | 24/24 PASS |
| Source-qualifier static tests, x86 Windows PowerShell 5.1 | 24/24 PASS |
| Source-qualifier PSScriptAnalyzer | 0 findings |

## Source and adapter decision

The archived official KS X 6101 source and Hancom help bounded the exact-target probe. Completed
attempt `20260913-05` then established the installed native tokens `%g,` and `%.0f,` through
`%.4f,`, including grouped `LastResult`, matching `Command` grammar and independent visible
grouping state. Percent, scientific and non-integer mappings remain excluded.

The new HWPX adapter binds section, selected formula/native-grouping state, grid, semantic flow and
domain plan at both request and build time. It owns only `Command`, `ResultFormat`, `LastResult` and
visible result, then requires typed reopen and unowned-byte equality before returning output.

## Exact-source qualifier status — 2026-09-13

A fail-closed worker created one 6-by-3 disposable table and Hangul-authored six formulas. The user
selected the six documented dialog choices; exact cell-block `TableDeleteComma` and
`TableInsertComma` actions produced ungrouped and grouped outputs. No user document, guessed token,
raw document/formula trace, Computer Use click/type, module registration, network or
registry/system-setting write was present.

Attempt 05 passed with 50 ordered progress events, six formula actions, six user-authored dialogs,
six grouping removals, six grouping additions, all three artifacts and zero remaining Hwp
processes. Attempts 01-04 remain failed/interrupted evidence and are not promoted.

Offline structural readback proves formula AST/cache and grid preservation. Five direct operations
produce the grouped native section exactly with 18 owned-text edits. With one independently counted
TABLE-033 general-grouping edit, five operations produce the ungrouped native section exactly with
19 owned-text edits. Raw `content.hpf` hashes remain distinct because Hangul updated save metadata
and one explicit/default spine attribute; their normalized semantic flow is equal.

## Conformance impact

The direct matrix is cataloged 0, unit 1, integration 35, oracle 25, green 0/61. TABLE-049 advances
only to `integration_passed`. Native source and direct section differential pass; direct-output
package save/reopen, render, rollback/retry, automation and release differential remain false or
`not_run`. P06-09, P06, production and product completion remain open.

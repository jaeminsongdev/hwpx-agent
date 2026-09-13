# P06-09 exact table number-format policy

- Feature: `TABLE-049`
- Capability: `table.number_format`
- Model: `hwpx-agent.table-number-format/v1`
- Contract: `protocol/private/p06-table-number-format-v1.json`
- Scope: pure exact-state planner for current-PC local development

## Exact state and selection

The operation is defined over one complete ordered master-cell snapshot, not a loose list of formula
objects. The snapshot binds the logical table identity, canonical `TableGrid` SHA-256, table-level
properties SHA-256, and every master cell. Each master cell binds its identity, top-left coordinate,
non-formula payload SHA-256 and properties SHA-256. Formula cells additionally carry the complete
validated owner, `FormulaAst`, absent or unverified display cache, and current number format.

Requests select a nonempty, bounded, sorted and unique set of exact formula master-cell coordinates.
Covered non-master slots and cells without formulas fail closed. A merged master cell is admissible
at its exact top-left owner because its grid identity remains unambiguous.

## Mutation and preservation

The target is one closed `FormulaNumberFormat` value: general, fixed number with grouping, percent,
or scientific. Decimal places remain bounded by the formula limits. The builder reconstructs each
selected `FormulaCell` with only `number_format` changed. Formula owner, AST and cache are exact;
unselected formulas and all cell/table digests remain byte-for-byte equal in the typed state.

The request binds the current source-state SHA-256 and document-flow SHA-256. Both request admission
and plan building independently recheck table identity, canonical grid digest, full source-state
digest and document-flow digest. Any intervening change fails before a plan is returned. Output is
deterministic bounded JSON with SHA-256; Debug output redacts identities, digests, formulas, caches
and the complete post-state.

## Official and exact-target format evidence

The archived machine-readable KS X 6101 source, section `10.7.3.5.2`, defines standard formula
`ResultFormat` values `%g`, `%.0f`, and `%.1f` through `%.4f`. Hancom's calculation-dialog help
exposes the corresponding six choices plus an independent thousands-grouping checkbox. Neither
source alone proves this installed build.

Completed attempt `20260913-05` now supplies exact Hangul 2020 source evidence. Its native fields use
`%g,`, `%.0f,`, `%.1f,`, `%.2f,`, `%.3f,` and `%.4f,`; `Command` repeats that token and grouped
`LastResult`, while the visible text independently records grouping off/on. Percent, scientific and
non-integer behavior remain outside the admitted native profile.

## Exact Hangul 2020 source qualification

The private source worker `tools/create-hancom-2020-table-number-format-source.ps1` creates only a
new 6-by-3 table with fixed, unique integer operands. Hangul authors six horizontal-sum formulas.
For each result cell the worker opens `ModifyCtrl` and stops at the visible dialog so the user can
choose, in order, general, integer and one through four decimal places. It then applies the
installed grouping actions and saves three immutable artifacts: baseline, ungrouped and grouped.
No native `ResultFormat`, packed command or field-control value is guessed or written by the
worker. The trace contains only bounded counters, booleans, phase state and SHA-256 digests.

The watchdog `tools/run-hancom-2020-table-number-format-source.ps1` pins x86 COM to build
`11.0.0.9136` and the locked executable digest, rejects pre-existing Hwp processes and existing,
colliding or out-of-boundary outputs, and bounds runtime, progress and artifact sizes. It can stop
only the exact same-session `-Automation -Embedding` process owned by the run. It never opens a
user document, registers a module, invokes network access, changes registry/system settings or
automates UI input. Computer Use may capture screens only; every format selection and access
`허용` click belongs to the user.

Attempt `20260913-05` satisfies admission: all three HWPX files and matching receipts exist; six
formula actions, six user-authored dialogs, six grouping removals and six grouping additions passed;
the 50-event journal ends in terminal `pass`; and zero Hwp processes remain. Attempts 01-04 remain
failed or interrupted evidence and are not relabeled.

The preserving adapter owns only selected `Command`, `ResultFormat`, `LastResult` and visible-result
text. It binds section, selected native/typed state, complete grid, semantic document flow and domain
plan at request and build time, then requires exact typed reopen plus equality of all unowned section
bytes. Direct grouped and ungrouped results match the corresponding native sections byte-for-byte.

## Gate boundary

`TABLE-049` advances to `direct_hwpx / integration_passed` for the bounded current-target profile.
The native source packages were created and the direct section differential passed. The direct
output was not repackaged or opened in Hangul; package save/reopen, PDF/render, rollback/retry,
product automation and release differential remain `not_run`. P06-09, P06, production and product
completion remain open.

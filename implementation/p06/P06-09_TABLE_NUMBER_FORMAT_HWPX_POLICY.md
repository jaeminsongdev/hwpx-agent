# P06-09 exact table number-format HWPX policy

- Feature: `TABLE-049`
- Capability: `table.number_format`
- Core model: `hwpx-agent.table-number-format/v1`
- Adapter: `hwpx-agent.table-number-format-hwpx/v1`
- Native profile: `hwpx-agent.table-number-format-hwpx.hancom-2020/1`
- Direct boundary: `direct_hwpx / integration_passed`

## Exact current-target source

Attempt `20260913-05` completed under licensed Hangul 2020 `11.0.0.9136` x86 `ko-KR`. The worker
created one disposable 6-by-3 table, asked Hangul to author six `SUM(LEFT)` fields, and stopped at
each calculation dialog for the user to select general, integer, and one through four decimal
places. It then used the installed `TableDeleteComma` and `TableInsertComma` actions on exact cell
blocks and saved baseline, ungrouped and grouped HWPX artifacts.

The run recorded 50 ordered progress events, six formula actions, six user-authored format dialogs,
six grouping removals and six grouping additions. It timed out nowhere, left zero Hwp processes,
opened no user document, invoked no Computer Use click/type, used no network and changed no registry
or system setting. Attempts 01-04 remain failed or interrupted evidence and are not promoted.

## Native profile and ownership

The exact source maps general to `%g,` and fixed zero through four decimal places to `%.0f,` through
`%.4f,`. `Command` repeats the exact native formula, result-format token and grouped `LastResult`.
Grouping is independently observed from the visible result. General preserves that observed mode;
fixed number uses the typed `use_grouping` value.

The adapter admits a complete unmerged grid, exact selected master-cell owners, native
`=SUM(LEFT)` fields, one of the six verified tokens and an unambiguous grouped integer cache.
Percent, scientific, non-integer values, merged grids, ambiguous grouping, unknown tokens and
malformed field envelopes fail closed.

Only four selected text spans are owned: `Command`, `ResultFormat`, `LastResult` and visible result.
Formula source, field IDs, all unselected formula fields, cell/table properties, grid topology and
every byte outside those spans remain exact.

## Bindings and return boundary

Request construction binds section SHA-256, selected formula/native-grouping state, grid,
semantic document flow and the complete domain plan. Lowering independently rechecks all five,
uses bounded non-overlapping edits, reparses the result and returns no bytes unless typed formula
readback, exact target format/grouping, grid equality and unowned-byte equality all pass.

The source oracle applies five number-format plans to the native baseline. Its grouped and
ungrouped results match the corresponding Hangul-authored sections byte-for-byte. The one general
grouping removal needed to construct the ungrouped baseline is performed through the separately
qualified TABLE-033 adapter and counted independently.

## Gate boundary

This exact current-target native-source HWPX integration passes only `TABLE-049` direct
`integration_passed`. The direct output was not repackaged, opened in Hangul, saved/reopened,
rendered or exercised through product automation. Rollback/retry and release differential remain
`not_run`. P06-09, P06, production and product completion remain open.

# P06 table number-format v1 to preserving HWPX v1

Before this profile, `hwpx-agent.table-number-format/v1` was a pure exact-state planner. It did not
read or modify a native HWPX formula field and therefore remained `unit_passed`.

The HWPX profile binds the exact section, selected native formula state, complete unmerged grid,
semantic document flow and domain plan at request time and rechecks every binding at build time.
It admits only current-target native `=SUM(LEFT)` fields whose cached value is an unambiguous
groupable integer and whose `ResultFormat` is `%g,` or `%.0f,` through `%.4f,`.

Change only the selected fields' `Command`, `ResultFormat`, `LastResult` and visible-result text.
Formula source, field identity, unselected formulas, table payload/properties, grid topology and all
other section bytes remain exact. General format preserves the observed grouping mode; fixed-number
format obtains grouping from the typed plan. Output is returned only after semantic readback and
unowned-byte equality pass.

Percent, scientific, non-integer formatting, arbitrary-document compatibility, package save/reopen,
render, product automation and release differential may not be inferred from this migration.

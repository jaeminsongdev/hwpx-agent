# P06 table auto-fill HWPX v0 to v1

Before this profile, `hwpx-agent.table-auto-fill/v1` and
`hwpx-agent.table-auto-fill-series/v1` produced a deterministic, complete cell mutation plan but no
native HWPX adapter materialized or reopened its result.

`hwpx-agent.table-auto-fill-hwpx.hancom-2020-single-run/1` adds an exact preserving adapter for one
explicitly bound current-Hangul-2020 table. It relifts every selected scalar from a merge-free
rectangle, independently rebuilds the domain fill plan, and rewrites only the selected native run
content. Existing nonempty payload identities are reused; blank or formula cells becoming nonempty
require caller-supplied distinct identities.

The request binds source header, section, table content, complete ruling state, grid, scalar state,
pagination, table count, series and current/target document flow. The lowerer repeats the complete
lift and rebuild before mutation. Publication occurs only after target state, grid, scalar values,
formula count, payload identities, page split, repeat headers, caption and table count reopen
exactly. A no-op keeps the original bytes and flow.

Selected exact native formulas may be rejected or replaced according to the bound domain policy.
The adapter does not recalculate formulas: if a changed selected cell is referenced by an
unselected formula, the operation fails closed so that its visible cache cannot become stale.
Merged cells, multiple paragraphs or runs, inline styles and opaque content have no reviewed exact
native fill mapping in v1. Existing documents are not rewritten in place.

Static synthetic HWPX/package success may not promote TABLE-057/058 to licensed Hangul 2020,
renderer, target-build, rollback/retry, automation, differential, release, production or product
PASS.

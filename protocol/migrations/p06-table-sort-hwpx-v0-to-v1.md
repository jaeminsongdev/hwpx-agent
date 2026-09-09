# P06 table sort HWPX v0 to v1

Before this profile, `hwpx-agent.table-sort/v1` produced a deterministic whole-cell relocation plan
but no native HWPX adapter materialized or reopened its result.

`hwpx-agent.table-sort-hwpx.hancom-2020-plain-unmerged/1` adds an exact preserving adapter for one
explicitly bound current-Hangul-2020 table. It relifts plain cell text into deterministic blank,
boolean, canonical integer, fixed-decimal or text values; rebuilds the domain sort independently;
and moves complete native cell identities, payloads and non-ruling properties within the selected
row or column region.

The request binds source header, section, table content, full ruling state, grid, text grid,
pagination policy, table count and current/target document flow. The lowerer repeats the full lift
and rebuild before mutation. No output is returned until target ruling state, grid, text grid,
formula absence, page policy, repeat header, caption and table count reopen exactly. A no-op keeps
both bytes and document flow unchanged.

Merged, formula-bearing, multi-paragraph, field/control and opaque cell content have no reviewed exact native sort mapping
in v1 and fail closed. Dates and locale-sensitive collation are not
inferred from visible text. The domain formula policies are not removed or weakened. Migration is
additive and existing documents are not rewritten in place.

Static synthetic HWPX/package success may not promote TABLE-056 to licensed Hangul 2020, renderer,
target-build, rollback/retry, automation, differential, release, production or product PASS.

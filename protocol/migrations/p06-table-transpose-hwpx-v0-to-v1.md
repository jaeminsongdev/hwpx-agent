# P06 table transpose HWPX v0 to v1

Before this profile, `hwpx-agent.table-transpose/v1` produced a complete semantic grid, relocation
and formula-transpose plan, but no native HWPX adapter materialized that target.

`hwpx-agent.table-transpose-hwpx.hancom-2020-wrapper/1` adds an exact preserving adapter for one
explicitly bound current-Hangul-2020 table. It swaps logical and physical row/column axes, merged
span axes, frame width/height and every unit-edge axis while moving each complete payload/property
state with the unchanged master identity.

The request binds source header, section, full ruling state, grid and current/target document flow.
The builder and lowerer relift source state and rebuild the domain plan independently. The output
binding is regenerated in target row-major order, and no parts are returned until exact semantic
reopen proves target grid/state, formula-free readback, page-split policy and caption preservation.

Formula-bearing input and nonzero repeat-header rows have no reviewed exact native transpose mapping
in v1 and fail closed. The domain formula-transpose model is not removed or weakened. Migration is
additive and existing documents are not rewritten in place.

Static synthetic HWPX/package success may not promote TABLE-021 to licensed Hangul 2020, renderer,
target-build, rollback/retry, automation, differential, release, production or product PASS.

# P06 table structure HWPX v0 to v1

Before this profile, row and column insertion/deletion existed only as component grid operations.
They did not bind complete ruling, payload, property, formula/cache, pagination, caption, wrapper,
document-flow or native HWPX readback state and therefore could not be direct-HWPX evidence.

`hwpx-agent.table-structure/v1` unifies TABLE-012 through TABLE-015 under one exact structural
transition. It reuses the authoritative grid edit, preserves every surviving master cell and all
complete state, inserts one empty formula-free 1x1 master per new slot, rebases surviving formula
owners/references and their explicit cache policy, and defines exact edge duplication/collapse.
Insertion through a merged span, partial-span deletion, final-dimension deletion, and unequal edges
that would collapse onto one survivor boundary all fail closed.

`hwpx-agent.table-structure-hwpx.hancom-2020-wrapper/1` adds a preserving adapter for one top-level
`hp:p/hp:run/hp:tbl` wrapper. The lowerer relifts the source and rebuilds the domain result, reuses
native cell/formula content, applies the exact formula and pagination transition, and semantically
reopens state, grid, page-split, repeat-header prefix, caption and native identities before returning.
Deleting a formula owner is explicit; deleting a referenced endpoint is unsupported. A repeat-header
zero/nonzero transition is also unsupported because the current exact table-property model requires
the native repeat-header flag to remain preserved.

Migration is additive and existing documents are not rewritten in place. Static synthetic XML and
closed in-memory package success may not promote these rows to saved-real-HWPX, licensed Hangul 2020,
renderer, target-build, automation, differential, rollback/retry, release, production or product PASS.

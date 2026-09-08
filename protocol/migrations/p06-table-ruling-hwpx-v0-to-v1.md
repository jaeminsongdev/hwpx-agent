# P06 table ruling HWPX v0 to v1

Before this profile, `hwpx-agent.table-ruling/v1` modeled TABLE-002 draw and TABLE-003 eraser as
one exact physical ruling/topology operation, but it had no native HWPX read/lower boundary.

`hwpx-agent.table-ruling-hwpx.hancom-2020/1` adds a preserving adapter for an explicitly selected
`hp:tbl`. A caller supplies logical table, master-cell and payload IDs plus every physical row and
column boundary because merged HWPX cells do not retain enough information to reconstruct all
internal physical boundaries without guessing. Every native cell extent and shared border is
verified against that binding.

Existing-table lowering relifts the exact source immediately before mutation and verifies the
domain plan's before/after state, grid and document-flow receipts. Outer-rectangle creation is a
separate path: it replaces one exact empty top-level paragraph whose full-section insertion-context
digest was bound by the domain request. A reviewed empty 1x1 native wrapper supplies unowned HWPX
shape properties; the adapter validates its table/cell properties, frame, formula/payload absence
and native table-ID uniqueness instead of synthesizing undocumented defaults.

Migration is additive. Existing documents are not rewritten in place. Structural formula changes
remain fail closed in this native profile because the current formula adapter cannot serialize the
domain model's general rebasing and cache-clear result. Line-only operations preserve the exact
formula AST/cache bytes. A caller must not reinterpret this limitation as a partial successful
mutation.

Static package success may not promote TABLE-002/003 to a licensed Hangul oracle, renderer,
automation, differential, rollback/retry, release, production or product PASS.

# P06 table style HWPX v0 to v1

Before this profile, `hwpx-agent.table-style-definition/v1` and
`hwpx-agent.table-style/v1` resolved complete table and per-master style identities, precedence and
merged-cell policy, but no native HWPX adapter materialized those identities.

`hwpx-agent.table-style-hwpx.hancom-2020/1` adds a preserving adapter for one explicitly bound
`hp:tbl`. A reusable visual cell-style identity covers typed non-border cell properties, four
directional borders, background and visible diagonal value. Exact each-cell versus unified
diagonal application provenance remains in the property binding because native HWPX does not store
that intent and a reusable style rule cannot truthfully encode a document-specific region.

At request time the adapter binds complete source style/property state, grid, package parts,
document flow, definition, request and plan hashes. At lowering time it relifts the source and
rebuilds the domain plan before any output exists. Every supplied catalog value and every declared
style rule is checked through typed native values; raw XML and unresolved digest fallbacks are not
accepted.

Truthful unified diagonal provenance is preserved only while every member keeps the same visible
diagonal. If one member changes, every remaining visible member is normalized to an explicit
each-cell binding before rendering. Payload, formula/cache, grid, geometry, pagination and
unselected package content remain exact and are checked by semantic reopen.

Migration is additive and existing documents are not rewritten in place. Static synthetic package
success may not promote TABLE-020 to licensed Hangul 2020, renderer, automation, differential,
rollback/retry, release, production or product PASS.

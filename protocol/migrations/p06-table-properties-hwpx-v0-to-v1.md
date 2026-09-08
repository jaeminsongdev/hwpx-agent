# P06 table properties HWPX v0 to v1

Before this profile, `hwpx-agent.table-properties/v1` modeled TABLE-007 table properties,
TABLE-008 cell properties, TABLE-009 directional borders/background and TABLE-047 diagonals as one
complete typed state, but it had no native HWPX read/lower boundary.

`hwpx-agent.table-properties-hwpx.hancom-2020/1` adds a preserving adapter for one explicitly
selected `hp:tbl`. It reuses the strict table grid and physical boundary binding, reads every
master cell through the current Hangul 2020 cell-style profile, and binds visible native diagonals
to explicit logical each-cell or unified intent because HWPX does not retain that provenance.

Lowering relifts the exact source immediately before mutation and verifies source parts, complete
state, grid, plan and document-flow identities. Opaque domain digests resolve only through typed
table, cell, line, background and border-fill values. Every supplied catalog value is checked
against the current header and finite limits even when the plan does not reference it. Raw XML is
never accepted as a property value.

Migration is additive. Existing documents are not rewritten in place. Native table cell spacing is
preserved as geometry-bound state rather than exposed as an independent table-property value;
changing only that attribute would conflict with the exact cell extents. The current formula
profile admits zero or one supported formula and otherwise remains fail closed.

Static package success may not promote these four rows to a licensed Hangul oracle, renderer,
automation, differential, rollback/retry, release, production or product PASS.
